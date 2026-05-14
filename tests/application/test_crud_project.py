# SPDX-License-Identifier: GPL-3.0-or-later
from uuid import uuid4

import pytest
from colourlog.application.exceptions import EntityNotFoundError
from colourlog.application.usecases.crud_client import CreateClient
from colourlog.application.usecases.crud_project import (
    CreateProject,
    DeleteProject,
    GetProject,
    ListProjects,
    UpdateProject,
)

from tests.application.fakes import InMemoryClientRepository, InMemoryProjectRepository


class TestCreateProject:
    def test_without_client(self):
        repo = InMemoryProjectRepository()
        clients = InMemoryClientRepository()
        p = CreateProject(projects=repo, clients=clients).execute(name="Evvue")
        assert p.client_id is None
        assert repo.get(p.id) == p

    def test_with_existing_client(self):
        clients = InMemoryClientRepository()
        c = CreateClient(clients=clients).execute(name="EMSA")
        projects = InMemoryProjectRepository()
        p = CreateProject(projects=projects, clients=clients).execute(name="Evvue", client_id=c.id)
        assert p.client_id == c.id

    def test_unknown_client_raises(self):
        with pytest.raises(EntityNotFoundError):
            CreateProject(
                projects=InMemoryProjectRepository(),
                clients=InMemoryClientRepository(),
            ).execute(name="Evvue", client_id=uuid4())


class TestGetProject:
    def test_found(self):
        repo = InMemoryProjectRepository()
        clients = InMemoryClientRepository()
        p = CreateProject(projects=repo, clients=clients).execute(name="Evvue")
        assert GetProject(projects=repo).execute(p.id) == p

    def test_missing_raises(self):
        with pytest.raises(EntityNotFoundError):
            GetProject(projects=InMemoryProjectRepository()).execute(uuid4())


class TestListProjects:
    def test_filter_by_client(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        c1 = CreateClient(clients=clients).execute(name="EMSA")
        c2 = CreateClient(clients=clients).execute(name="ACME")
        cp = CreateProject(projects=projects, clients=clients)
        p1 = cp.execute(name="Evvue", client_id=c1.id)
        cp.execute(name="Other", client_id=c2.id)
        listed = ListProjects(projects=projects).execute(client_id=c1.id)
        assert listed == [p1]

    def test_excludes_archived_by_default(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        create = CreateProject(projects=projects, clients=clients)
        update = UpdateProject(projects=projects, clients=clients)
        a = create.execute(name="A")
        b = create.execute(name="B")
        update.execute(a.id, archived=True)
        listed = ListProjects(projects=projects).execute()
        assert listed == [b]

    def test_includes_archived_when_asked(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        create = CreateProject(projects=projects, clients=clients)
        update = UpdateProject(projects=projects, clients=clients)
        a = create.execute(name="A")
        b = create.execute(name="B")
        update.execute(a.id, archived=True)
        listed = ListProjects(projects=projects).execute(include_archived=True)
        assert {p.id for p in listed} == {a.id, b.id}


class TestUpdateProject:
    def test_patch_name(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        p = CreateProject(projects=projects, clients=clients).execute(name="Evvue")
        updated = UpdateProject(projects=projects, clients=clients).execute(p.id, name="Evvue2")
        assert updated.name == "Evvue2"
        assert updated.id == p.id

    def test_patch_client_id(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        c = CreateClient(clients=clients).execute(name="EMSA")
        p = CreateProject(projects=projects, clients=clients).execute(name="Evvue")
        updated = UpdateProject(projects=projects, clients=clients).execute(p.id, client_id=c.id)
        assert updated.client_id == c.id

    def test_clear_client(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        c = CreateClient(clients=clients).execute(name="EMSA")
        p = CreateProject(projects=projects, clients=clients).execute(name="Evvue", client_id=c.id)
        updated = UpdateProject(projects=projects, clients=clients).execute(p.id, clear_client=True)
        assert updated.client_id is None

    def test_patch_archived(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        p = CreateProject(projects=projects, clients=clients).execute(name="Evvue")
        updated = UpdateProject(projects=projects, clients=clients).execute(p.id, archived=True)
        assert updated.archived is True

    def test_no_fields_returns_existing(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        p = CreateProject(projects=projects, clients=clients).execute(name="Evvue")
        updated = UpdateProject(projects=projects, clients=clients).execute(p.id)
        assert updated == p

    def test_unknown_project_raises(self):
        with pytest.raises(EntityNotFoundError):
            UpdateProject(
                projects=InMemoryProjectRepository(),
                clients=InMemoryClientRepository(),
            ).execute(uuid4(), name="X")

    def test_unknown_new_client_raises(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        p = CreateProject(projects=projects, clients=clients).execute(name="Evvue")
        with pytest.raises(EntityNotFoundError):
            UpdateProject(projects=projects, clients=clients).execute(p.id, client_id=uuid4())


class TestDeleteProject:
    def test_removes(self):
        clients = InMemoryClientRepository()
        projects = InMemoryProjectRepository()
        p = CreateProject(projects=projects, clients=clients).execute(name="Evvue")
        DeleteProject(projects=projects).execute(p.id)
        assert projects.get(p.id) is None

    def test_missing_raises(self):
        with pytest.raises(EntityNotFoundError):
            DeleteProject(projects=InMemoryProjectRepository()).execute(uuid4())
