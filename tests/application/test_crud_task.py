# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from colourlog.application.exceptions import EntityNotFoundError
from colourlog.application.usecases.crud_project import CreateProject
from colourlog.application.usecases.crud_task import (
    CreateTask,
    DeleteTask,
    GetTask,
    ListTasks,
    UpdateTask,
)
from colourlog.domain.entities import Project

from tests.application.fakes import (
    FrozenClock,
    InMemoryClientRepository,
    InMemoryProjectRepository,
    InMemoryTaskRepository,
)


def _now() -> datetime:
    return datetime(2026, 5, 13, 18, 0, tzinfo=UTC)


def _bootstrap_project() -> tuple[InMemoryClientRepository, InMemoryProjectRepository, Project]:
    clients = InMemoryClientRepository()
    projects = InMemoryProjectRepository()
    p = CreateProject(projects=projects, clients=clients).execute(name="Evvue")
    return clients, projects, p


class TestCreateTask:
    def test_persists_and_returns(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        clock = FrozenClock(_now())
        t = CreateTask(tasks=tasks, projects=projects, clock=clock).execute(
            name="T41622", project_id=p.id
        )
        assert t.created_at == _now()
        assert t.project_id == p.id
        assert t.keywords == ("t41622",)
        assert tasks.get(t.id) == t

    def test_unknown_project_raises(self):
        with pytest.raises(EntityNotFoundError):
            CreateTask(
                tasks=InMemoryTaskRepository(),
                projects=InMemoryProjectRepository(),
                clock=FrozenClock(_now()),
            ).execute(name="T41622", project_id=uuid4())

    def test_explicit_keywords_preserved(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        t = CreateTask(tasks=tasks, projects=projects, clock=FrozenClock(_now())).execute(
            name="T41622", project_id=p.id, keywords=["FOO", "  bar  "]
        )
        assert t.keywords == ("foo", "bar")


class TestGetTask:
    def test_found(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        t = CreateTask(tasks=tasks, projects=projects, clock=FrozenClock(_now())).execute(
            name="T41622", project_id=p.id
        )
        assert GetTask(tasks=tasks).execute(t.id) == t

    def test_missing_raises(self):
        with pytest.raises(EntityNotFoundError):
            GetTask(tasks=InMemoryTaskRepository()).execute(uuid4())


class TestListTasks:
    def test_filter_by_project(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        p1 = CreateProject(projects=projects, clients=clients).execute(name="A")
        p2 = CreateProject(projects=projects, clients=clients).execute(name="B")
        tasks = InMemoryTaskRepository()
        clock = FrozenClock(_now())
        create = CreateTask(tasks=tasks, projects=projects, clock=clock)
        t1 = create.execute(name="X1", project_id=p1.id)
        create.execute(name="Y1", project_id=p2.id)
        listed = ListTasks(tasks=tasks).execute(project_id=p1.id)
        assert listed == [t1]

    def test_excludes_archived_by_default(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        clock = FrozenClock(_now())
        create = CreateTask(tasks=tasks, projects=projects, clock=clock)
        update = UpdateTask(tasks=tasks, projects=projects)
        a = create.execute(name="A", project_id=p.id)
        b = create.execute(name="B", project_id=p.id)
        update.execute(a.id, archived=True)
        listed = ListTasks(tasks=tasks).execute()
        assert listed == [b]

    def test_includes_archived_when_asked(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        clock = FrozenClock(_now())
        create = CreateTask(tasks=tasks, projects=projects, clock=clock)
        update = UpdateTask(tasks=tasks, projects=projects)
        a = create.execute(name="A", project_id=p.id)
        b = create.execute(name="B", project_id=p.id)
        update.execute(a.id, archived=True)
        listed = ListTasks(tasks=tasks).execute(include_archived=True)
        assert {t.id for t in listed} == {a.id, b.id}


class TestUpdateTask:
    def test_patch_name(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        t = CreateTask(tasks=tasks, projects=projects, clock=FrozenClock(_now())).execute(
            name="T41622", project_id=p.id
        )
        updated = UpdateTask(tasks=tasks, projects=projects).execute(t.id, name="T41622-r")
        assert updated.name == "T41622-r"
        assert updated.created_at == t.created_at
        assert updated.id == t.id

    def test_patch_project_id(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        p1 = CreateProject(projects=projects, clients=clients).execute(name="A")
        p2 = CreateProject(projects=projects, clients=clients).execute(name="B")
        tasks = InMemoryTaskRepository()
        t = CreateTask(tasks=tasks, projects=projects, clock=FrozenClock(_now())).execute(
            name="T", project_id=p1.id
        )
        updated = UpdateTask(tasks=tasks, projects=projects).execute(t.id, project_id=p2.id)
        assert updated.project_id == p2.id

    def test_patch_code(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        t = CreateTask(tasks=tasks, projects=projects, clock=FrozenClock(_now())).execute(
            name="T", project_id=p.id, code="OLD"
        )
        updated = UpdateTask(tasks=tasks, projects=projects).execute(t.id, code="NEW")
        assert updated.code == "NEW"

    def test_clear_code(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        t = CreateTask(tasks=tasks, projects=projects, clock=FrozenClock(_now())).execute(
            name="T", project_id=p.id, code="OLD"
        )
        updated = UpdateTask(tasks=tasks, projects=projects).execute(t.id, clear_code=True)
        assert updated.code is None

    def test_patch_tags_keywords_archived(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        t = CreateTask(tasks=tasks, projects=projects, clock=FrozenClock(_now())).execute(
            name="T", project_id=p.id
        )
        updated = UpdateTask(tasks=tasks, projects=projects).execute(
            t.id, tags=["meetings"], keywords=["foo", "bar"], archived=True
        )
        assert updated.tags == ("meetings",)
        assert updated.keywords == ("foo", "bar")
        assert updated.archived is True

    def test_no_fields_returns_existing(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        t = CreateTask(tasks=tasks, projects=projects, clock=FrozenClock(_now())).execute(
            name="T", project_id=p.id
        )
        updated = UpdateTask(tasks=tasks, projects=projects).execute(t.id)
        assert updated == t

    def test_unknown_task_raises(self):
        with pytest.raises(EntityNotFoundError):
            UpdateTask(
                tasks=InMemoryTaskRepository(),
                projects=InMemoryProjectRepository(),
            ).execute(uuid4(), name="X")

    def test_unknown_new_project_raises(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        t = CreateTask(tasks=tasks, projects=projects, clock=FrozenClock(_now())).execute(
            name="T", project_id=p.id
        )
        with pytest.raises(EntityNotFoundError):
            UpdateTask(tasks=tasks, projects=projects).execute(t.id, project_id=uuid4())


class TestDeleteTask:
    def test_removes(self):
        _, projects, p = _bootstrap_project()
        tasks = InMemoryTaskRepository()
        t = CreateTask(tasks=tasks, projects=projects, clock=FrozenClock(_now())).execute(
            name="T", project_id=p.id
        )
        DeleteTask(tasks=tasks).execute(t.id)
        assert tasks.get(t.id) is None

    def test_missing_raises(self):
        with pytest.raises(EntityNotFoundError):
            DeleteTask(tasks=InMemoryTaskRepository()).execute(uuid4())
