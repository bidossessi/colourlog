# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from colourlog.application.usecases import list_entries
from colourlog.domain import entities, value_objects

from tests.application import fakes


def _ts(offset_minutes: int = 0) -> datetime:
    return datetime(2026, 5, 14, 10, 0, tzinfo=UTC) + timedelta(minutes=offset_minutes)


def _start(task_id: UUID, ts: datetime) -> entities.EntryEvent:
    return entities.EntryEvent.create(
        id=uuid4(),
        ts=ts,
        task_id=task_id,
        source=value_objects.Source.MANUAL,
    )


class TestListEntries:
    def test_empty(self):
        events = fakes.InMemoryEntryEventRepository()
        assert list_entries.ListEntries(events=events).execute() == []

    def test_pairs_consecutive_events(self):
        events = fakes.InMemoryEntryEventRepository()
        t = uuid4()
        events.append(_start(t, _ts(0)))
        events.append(_start(t, _ts(30)))
        items = list_entries.ListEntries(events=events).execute()
        assert len(items) == 2
        assert items[0].end == items[1].start

    def test_filter_by_task(self):
        events = fakes.InMemoryEntryEventRepository()
        t1, t2 = uuid4(), uuid4()
        events.append(_start(t1, _ts(0)))
        events.append(_start(t2, _ts(30)))
        items = list_entries.ListEntries(events=events).execute(task_id=t1)
        assert len(items) == 1
        assert items[0].task_id == t1

    def test_filter_by_range(self):
        events = fakes.InMemoryEntryEventRepository()
        t = uuid4()
        events.append(_start(t, _ts(0)))
        events.append(_start(t, _ts(60)))
        items = list_entries.ListEntries(events=events).execute(from_ts=_ts(30), to_ts=_ts(120))
        assert len(items) == 1
        assert items[0].start == _ts(60)
