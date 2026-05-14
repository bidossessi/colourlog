# SPDX-License-Identifier: GPL-3.0-or-later
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from uuid import UUID

from colourlog.adapters.persistence.sqlite.engine import connect
from colourlog.domain.entities import Entry, EntryEvent
from colourlog.domain.value_objects import MatchSource, Source

_EVENT_COLS = (
    "id, ts, task_id, subtask_id, source, match_source, matched_keyword, calendar_event_id, note"
)
_INSERT_SQL = (
    "INSERT INTO entry_events ("
    "id, ts, task_id, subtask_id, source, match_source, "
    "matched_keyword, calendar_event_id, note"
    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
_SELECT_BY_ID = (
    "SELECT id, ts, task_id, subtask_id, source, match_source, "
    "matched_keyword, calendar_event_id, note "
    "FROM entry_events WHERE id = ?"
)
_SELECT_LATEST = (
    "SELECT id, ts, task_id, subtask_id, source, match_source, "
    "matched_keyword, calendar_event_id, note "
    "FROM entry_events ORDER BY ts DESC LIMIT 1"
)
_SELECT_EVENTS_BASE = (
    "SELECT id, ts, task_id, subtask_id, source, match_source, "
    "matched_keyword, calendar_event_id, note "
    "FROM entry_events"
)
_PROJECTION_BASE = (
    "WITH paired AS ("
    "SELECT id, ts, task_id, subtask_id, source, match_source, "
    "matched_keyword, calendar_event_id, note, "
    "LEAD(ts) OVER (ORDER BY ts) AS next_ts "
    "FROM entry_events"
    ") "
    "SELECT id, ts, task_id, subtask_id, source, match_source, "
    "matched_keyword, calendar_event_id, note, next_ts FROM paired "
    "WHERE task_id IS NOT NULL"
)


def _row_to_event(row: sqlite3.Row) -> EntryEvent:
    task_id_raw = row["task_id"]
    subtask_id_raw = row["subtask_id"]
    source_raw = row["source"]
    ms_raw = row["match_source"]
    return EntryEvent(
        id=UUID(row["id"]),
        ts=datetime.fromisoformat(row["ts"]),
        task_id=UUID(task_id_raw) if task_id_raw is not None else None,
        subtask_id=UUID(subtask_id_raw) if subtask_id_raw is not None else None,
        source=Source(source_raw) if source_raw is not None else None,
        match_source=MatchSource(ms_raw) if ms_raw is not None else None,
        matched_keyword=row["matched_keyword"],
        calendar_event_id=row["calendar_event_id"],
        note=row["note"],
    )


def _event_to_params(event: EntryEvent) -> tuple[object, ...]:
    return (
        str(event.id),
        event.ts.isoformat(),
        str(event.task_id) if event.task_id is not None else None,
        str(event.subtask_id) if event.subtask_id is not None else None,
        event.source.value if event.source is not None else None,
        event.match_source.value if event.match_source is not None else None,
        event.matched_keyword,
        event.calendar_event_id,
        event.note,
    )


def _projection_row_to_entry(row: sqlite3.Row) -> Entry:
    event = _row_to_event(row)
    next_ts_raw = row["next_ts"]
    end = datetime.fromisoformat(next_ts_raw) if next_ts_raw is not None else None
    return Entry.from_event(event, end=end)


class SqliteEntryEventRepository:
    def __init__(self, database_path: Path | str) -> None:
        self._path = database_path

    def append(self, event: EntryEvent) -> None:
        with closing(connect(self._path)) as conn, conn:
            conn.execute(_INSERT_SQL, _event_to_params(event))

    def get_event(self, id: UUID) -> EntryEvent | None:
        with closing(connect(self._path)) as conn:
            row = conn.execute(_SELECT_BY_ID, (str(id),)).fetchone()
        return _row_to_event(row) if row is not None else None

    def latest_event(self) -> EntryEvent | None:
        with closing(connect(self._path)) as conn:
            row = conn.execute(_SELECT_LATEST).fetchone()
        return _row_to_event(row) if row is not None else None

    def events_in_range(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ) -> list[EntryEvent]:
        sql = _SELECT_EVENTS_BASE
        params: list[object] = []
        conditions: list[str] = []
        if from_ts is not None:
            conditions.append("ts >= ?")
            params.append(from_ts.isoformat())
        if to_ts is not None:
            conditions.append("ts <= ?")
            params.append(to_ts.isoformat())
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY ts"
        with closing(connect(self._path)) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_row_to_event(r) for r in rows]

    def current_entry(self) -> Entry | None:
        latest = self.latest_event()
        if latest is None or latest.is_stop:
            return None
        return Entry.from_event(latest, end=None)

    def entries_in_range(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        task_id: UUID | None = None,
    ) -> list[Entry]:
        sql = _PROJECTION_BASE
        params: list[object] = []
        if task_id is not None:
            sql += " AND task_id = ?"
            params.append(str(task_id))
        if from_ts is not None:
            sql += " AND ts >= ?"
            params.append(from_ts.isoformat())
        if to_ts is not None:
            sql += " AND ts <= ?"
            params.append(to_ts.isoformat())
        sql += " ORDER BY ts"
        with closing(connect(self._path)) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_projection_row_to_entry(r) for r in rows]
