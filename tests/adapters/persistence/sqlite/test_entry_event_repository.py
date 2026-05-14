# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from colourlog.adapters.persistence.sqlite import (
    entry_event_repository,
    project_repository,
    task_repository,
)
from colourlog.domain import entities, value_objects


def _ts(offset_minutes: int = 0) -> datetime:
    return datetime(2026, 5, 14, 10, 0, tzinfo=UTC) + timedelta(minutes=offset_minutes)


def _seed_task(db_path: Path, name: str = "T41622") -> UUID:
    projects = project_repository.SqliteProjectRepository(db_path)
    tasks = task_repository.SqliteTaskRepository(db_path)
    p = entities.Project.create(id=uuid4(), name=f"P-{name}")
    projects.add(p)
    t = entities.Task.create(id=uuid4(), name=name, project_id=p.id, created_at=_ts())
    tasks.add(t)
    return t.id


def _start(task_id: UUID, ts: datetime, **kwargs: object) -> entities.EntryEvent:
    return entities.EntryEvent.create(
        id=uuid4(),
        ts=ts,
        task_id=task_id,
        source=value_objects.Source.MANUAL,
        **kwargs,  # type: ignore[arg-type]
    )


def _stop(ts: datetime) -> entities.EntryEvent:
    return entities.EntryEvent.create(id=uuid4(), ts=ts)


class TestAppendAndFetch:
    def test_append_then_get(self, db_path: Path):
        task_id = _seed_task(db_path)
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        ev = _start(task_id, _ts())
        repo.append(ev)
        assert repo.get_event(ev.id) == ev

    def test_get_missing_returns_none(self, db_path: Path):
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        assert repo.get_event(uuid4()) is None

    def test_append_stop_event(self, db_path: Path):
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        ev = _stop(_ts())
        repo.append(ev)
        fetched = repo.get_event(ev.id)
        assert fetched is not None
        assert fetched.is_stop

    def test_append_event_with_subtask(self, db_path: Path):
        task_id = _seed_task(db_path, "T41622")
        sub_id = _seed_task(db_path, "D12345")
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        ev = _start(task_id, _ts(), subtask_id=sub_id)
        repo.append(ev)
        assert repo.get_event(ev.id) == ev


class TestLatestEvent:
    def test_returns_none_when_empty(self, db_path: Path):
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        assert repo.latest_event() is None

    def test_returns_most_recent_by_ts(self, db_path: Path):
        task_id = _seed_task(db_path)
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        first = _start(task_id, _ts(0))
        second = _start(task_id, _ts(30))
        repo.append(first)
        repo.append(second)
        assert repo.latest_event() == second


class TestEventsInRange:
    def test_no_filter_returns_all_sorted_by_ts(self, db_path: Path):
        task_id = _seed_task(db_path)
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        b = _start(task_id, _ts(60))
        a = _start(task_id, _ts(0))
        repo.append(b)
        repo.append(a)
        result = repo.events_in_range()
        assert [e.id for e in result] == [a.id, b.id]

    def test_from_ts_filter(self, db_path: Path):
        task_id = _seed_task(db_path)
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        early = _start(task_id, _ts(0))
        late = _start(task_id, _ts(60))
        repo.append(early)
        repo.append(late)
        result = repo.events_in_range(from_ts=_ts(30))
        assert [e.id for e in result] == [late.id]

    def test_to_ts_filter(self, db_path: Path):
        task_id = _seed_task(db_path)
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        early = _start(task_id, _ts(0))
        late = _start(task_id, _ts(60))
        repo.append(early)
        repo.append(late)
        result = repo.events_in_range(to_ts=_ts(30))
        assert [e.id for e in result] == [early.id]


class TestCurrentEntry:
    def test_none_when_empty(self, db_path: Path):
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        assert repo.current_entry() is None

    def test_none_after_stop(self, db_path: Path):
        task_id = _seed_task(db_path)
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        repo.append(_start(task_id, _ts(0)))
        repo.append(_stop(_ts(30)))
        assert repo.current_entry() is None

    def test_returns_entry_for_latest_start(self, db_path: Path):
        task_id = _seed_task(db_path)
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        ev = _start(task_id, _ts(0), note="focus")
        repo.append(ev)
        entry = repo.current_entry()
        assert entry is not None
        assert entry.id == ev.id
        assert entry.task_id == task_id
        assert entry.end is None
        assert entry.note == "focus"


class TestEntriesInRange:
    def test_pairs_consecutive_events_into_entries(self, db_path: Path):
        task_id = _seed_task(db_path)
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        a = _start(task_id, _ts(0))
        b = _start(task_id, _ts(30))
        c = _stop(_ts(45))
        repo.append(a)
        repo.append(b)
        repo.append(c)
        entries = repo.entries_in_range()
        # 2 start events → 2 entries; stop event is excluded.
        assert len(entries) == 2
        first, second = entries
        assert first.id == a.id
        assert first.start == _ts(0)
        assert first.end == _ts(30)
        assert second.id == b.id
        assert second.start == _ts(30)
        assert second.end == _ts(45)

    def test_latest_start_with_no_following_event_has_no_end(self, db_path: Path):
        task_id = _seed_task(db_path)
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        ev = _start(task_id, _ts(0))
        repo.append(ev)
        entries = repo.entries_in_range()
        assert len(entries) == 1
        assert entries[0].end is None

    def test_filter_by_task(self, db_path: Path):
        t1 = _seed_task(db_path, "A")
        t2 = _seed_task(db_path, "B")
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        repo.append(_start(t1, _ts(0)))
        repo.append(_start(t2, _ts(30)))
        entries = repo.entries_in_range(task_id=t1)
        assert len(entries) == 1
        assert entries[0].task_id == t1

    def test_filter_by_range(self, db_path: Path):
        task_id = _seed_task(db_path)
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        repo.append(_start(task_id, _ts(0)))
        repo.append(_start(task_id, _ts(60)))
        entries = repo.entries_in_range(from_ts=_ts(30), to_ts=_ts(120))
        assert len(entries) == 1
        assert entries[0].start == _ts(60)

    def test_stop_event_not_projected(self, db_path: Path):
        task_id = _seed_task(db_path)
        repo = entry_event_repository.SqliteEntryEventRepository(db_path)
        repo.append(_start(task_id, _ts(0)))
        repo.append(_stop(_ts(30)))
        entries = repo.entries_in_range()
        assert len(entries) == 1  # the start; stop excluded
