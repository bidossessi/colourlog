# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from colourlog.domain import entities, exceptions, value_objects


def _ts(offset_minutes: int = 0) -> datetime:
    return datetime(2026, 5, 14, 10, 0, tzinfo=UTC) + timedelta(minutes=offset_minutes)


def _start_event(task_id: object = None, subtask_id: object = None) -> entities.EntryEvent:
    from uuid import UUID

    tid: UUID = task_id if isinstance(task_id, UUID) else uuid4()
    stid: UUID | None = subtask_id if isinstance(subtask_id, UUID) else None
    return entities.EntryEvent.create(
        id=uuid4(),
        ts=_ts(),
        task_id=tid,
        subtask_id=stid,
        source=value_objects.Source.MANUAL,
        note="focus",
    )


class TestFromEvent:
    def test_running_entry_no_end(self):
        ev = _start_event()
        entry = entities.Entry.from_event(ev, end=None)
        assert entry.id == ev.id
        assert entry.task_id == ev.task_id
        assert entry.start == ev.ts
        assert entry.end is None
        assert entry.is_running
        assert entry.note == "focus"

    def test_closed_entry_with_end(self):
        ev = _start_event()
        entry = entities.Entry.from_event(ev, end=_ts(30))
        assert entry.end == _ts(30)
        assert not entry.is_running

    def test_stop_event_cannot_project(self):
        ev = entities.EntryEvent.create(id=uuid4(), ts=_ts())
        with pytest.raises(ValueError, match="stop event"):
            entities.Entry.from_event(ev, end=None)

    def test_subtask_carried(self):
        st = uuid4()
        ev = _start_event(subtask_id=st)
        entry = entities.Entry.from_event(ev, end=None)
        assert entry.subtask_id == st


class TestInvariants:
    def test_naive_start_raises(self):
        with pytest.raises(exceptions.NaiveDatetimeError):
            entities.Entry(
                id=uuid4(),
                task_id=uuid4(),
                start=datetime(2026, 5, 14, 10, 0),
                source=value_objects.Source.MANUAL,
            )

    def test_naive_end_raises(self):
        with pytest.raises(exceptions.NaiveDatetimeError):
            entities.Entry(
                id=uuid4(),
                task_id=uuid4(),
                start=_ts(),
                end=datetime(2026, 5, 14, 11, 0),
                source=value_objects.Source.MANUAL,
            )

    def test_end_before_start_raises(self):
        with pytest.raises(exceptions.EndBeforeStartError):
            entities.Entry(
                id=uuid4(),
                task_id=uuid4(),
                start=_ts(),
                end=_ts(-5),
                source=value_objects.Source.MANUAL,
            )

    def test_manual_with_match_source_raises(self):
        with pytest.raises(exceptions.SourceMatchSourceMismatchError):
            entities.Entry(
                id=uuid4(),
                task_id=uuid4(),
                start=_ts(),
                source=value_objects.Source.MANUAL,
                match_source=value_objects.MatchSource.WINDOW,
            )

    def test_auto_without_match_source_raises(self):
        with pytest.raises(exceptions.SourceMatchSourceMismatchError):
            entities.Entry(
                id=uuid4(),
                task_id=uuid4(),
                start=_ts(),
                source=value_objects.Source.AUTO,
            )
