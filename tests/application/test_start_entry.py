# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from colourlog.application import exceptions
from colourlog.application.usecases import crud_project, crud_task, start_entry
from colourlog.domain import value_objects
from colourlog.domain.entities import Task

from tests.application import fakes


def _now() -> datetime:
    return datetime(2026, 5, 14, 10, 0, tzinfo=UTC)


def _seed_task() -> tuple[fakes.InMemoryTaskRepository, fakes.InMemoryEntryEventRepository, Task]:
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


class TestStartEntry:
    def test_appends_event_with_task(self):
        tasks, events, t = _seed_task()
        uc = start_entry.StartEntry(events=events, tasks=tasks, clock=fakes.FrozenClock(_now()))
        ev = uc.execute(task_id=t.id)
        assert ev.task_id == t.id
        assert ev.source is value_objects.Source.MANUAL
        assert ev.is_start
        assert events.latest_event() == ev

    def test_unknown_task_raises(self):
        tasks, events, _ = _seed_task()
        uc = start_entry.StartEntry(events=events, tasks=tasks, clock=fakes.FrozenClock(_now()))
        with pytest.raises(exceptions.EntityNotFoundError):
            uc.execute(task_id=uuid4())

    def test_with_subtask(self):
        tasks, events, t = _seed_task()
        sub = Task.create(id=uuid4(), name="D12345", project_id=t.project_id, created_at=_now())
        tasks.add(sub)
        uc = start_entry.StartEntry(events=events, tasks=tasks, clock=fakes.FrozenClock(_now()))
        ev = uc.execute(task_id=t.id, subtask_id=sub.id)
        assert ev.subtask_id == sub.id

    def test_unknown_subtask_raises(self):
        tasks, events, t = _seed_task()
        uc = start_entry.StartEntry(events=events, tasks=tasks, clock=fakes.FrozenClock(_now()))
        with pytest.raises(exceptions.EntityNotFoundError):
            uc.execute(task_id=t.id, subtask_id=uuid4())

    def test_auto_source_with_match_source(self):
        tasks, events, t = _seed_task()
        uc = start_entry.StartEntry(events=events, tasks=tasks, clock=fakes.FrozenClock(_now()))
        ev = uc.execute(
            task_id=t.id,
            source=value_objects.Source.AUTO,
            match_source=value_objects.MatchSource.WINDOW,
            matched_keyword="t41622",
        )
        assert ev.source is value_objects.Source.AUTO
        assert ev.match_source is value_objects.MatchSource.WINDOW
        assert ev.matched_keyword == "t41622"

    def test_note_normalized(self):
        tasks, events, t = _seed_task()
        uc = start_entry.StartEntry(events=events, tasks=tasks, clock=fakes.FrozenClock(_now()))
        ev = uc.execute(task_id=t.id, note="  focus  ")
        assert ev.note == "focus"
