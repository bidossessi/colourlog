# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime

from colourlog.application.usecases import (
    crud_project,
    crud_task,
    start_entry,
    stop_entry,
)

from tests.application import fakes


def _now() -> datetime:
    return datetime(2026, 5, 14, 10, 0, tzinfo=UTC)


def _seed_running() -> tuple[fakes.InMemoryEntryEventRepository, fakes.AdvancingClock]:
    clients = fakes.InMemoryClientRepository()
    projects = fakes.InMemoryProjectRepository()
    tasks = fakes.InMemoryTaskRepository()
    events = fakes.InMemoryEntryEventRepository()
    clock = fakes.AdvancingClock(_now(), step_seconds=60)
    p = crud_project.CreateProject(projects=projects, clients=clients).execute(name="Evvue")
    t = crud_task.CreateTask(tasks=tasks, projects=projects, clock=clock).execute(
        name="T41622", project_id=p.id
    )
    start_entry.StartEntry(events=events, tasks=tasks, clock=clock).execute(task_id=t.id)
    return events, clock


class TestStopEntry:
    def test_appends_stop_event(self):
        events, clock = _seed_running()
        ev = stop_entry.StopEntry(events=events, clock=clock).execute()
        assert ev.is_stop
        assert ev.task_id is None
        assert events.latest_event() == ev

    def test_stop_when_nothing_running_still_appends(self):
        events = fakes.InMemoryEntryEventRepository()
        clock = fakes.FrozenClock(_now())
        ev = stop_entry.StopEntry(events=events, clock=clock).execute()
        assert ev.is_stop
        # ledger remains append-only; redundant stop is just another event.
        assert len(events.events_in_range()) == 1

    def test_current_entry_is_none_after_stop(self):
        events, clock = _seed_running()
        stop_entry.StopEntry(events=events, clock=clock).execute()
        assert events.current_entry() is None
