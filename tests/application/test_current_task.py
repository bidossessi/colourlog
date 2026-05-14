# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from colourlog.application import exceptions
from colourlog.application.usecases import (
    crud_project,
    crud_task,
    current_task,
    start_entry,
    stop_entry,
)
from colourlog.domain import entities, value_objects
from colourlog.domain.entities import Task

from tests.application import fakes


def _now() -> datetime:
    return datetime(2026, 5, 14, 10, 0, tzinfo=UTC)


def _bootstrap() -> tuple[fakes.InMemoryTaskRepository, fakes.InMemoryEntryEventRepository, Task]:
    clients = fakes.InMemoryClientRepository()
    projects = fakes.InMemoryProjectRepository()
    tasks = fakes.InMemoryTaskRepository()
    events = fakes.InMemoryEntryEventRepository()
    p = crud_project.CreateProject(projects=projects, clients=clients).execute(name="Evvue")
    clock = fakes.FrozenClock(_now())
    t = crud_task.CreateTask(tasks=tasks, projects=projects, clock=clock).execute(
        name="T41622", project_id=p.id
    )
    return tasks, events, t


class TestGetCurrentTask:
    def test_none_when_no_events(self):
        tasks, events, _ = _bootstrap()
        assert current_task.GetCurrentTask(events=events, tasks=tasks).execute() is None

    def test_returns_entry_and_task_when_running(self):
        tasks, events, t = _bootstrap()
        clock = fakes.AdvancingClock(_now())
        start_entry.StartEntry(events=events, tasks=tasks, clock=clock).execute(task_id=t.id)
        result = current_task.GetCurrentTask(events=events, tasks=tasks).execute()
        assert result is not None
        entry, task = result
        assert entry.task_id == t.id
        assert task.id == t.id

    def test_none_after_stop(self):
        tasks, events, t = _bootstrap()
        clock = fakes.AdvancingClock(_now())
        start_entry.StartEntry(events=events, tasks=tasks, clock=clock).execute(task_id=t.id)
        stop_entry.StopEntry(events=events, clock=clock).execute()
        assert current_task.GetCurrentTask(events=events, tasks=tasks).execute() is None

    def test_orphan_event_raises(self):
        tasks = fakes.InMemoryTaskRepository()
        events = fakes.InMemoryEntryEventRepository()
        orphan = entities.EntryEvent.create(
            id=uuid4(),
            ts=_now(),
            task_id=uuid4(),
            source=value_objects.Source.MANUAL,
        )
        events.append(orphan)
        with pytest.raises(exceptions.EntityNotFoundError):
            current_task.GetCurrentTask(events=events, tasks=tasks).execute()
