# SPDX-License-Identifier: GPL-3.0-or-later
from uuid import uuid4

import pytest
from colourlog.application.exceptions import EntityNotFoundError
from colourlog.application.usecases.crud_client import (
    CreateClient,
    DeleteClient,
    GetClient,
    ListClients,
    UpdateClient,
)

from tests.application.fakes import InMemoryClientRepository


class TestCreateClient:
    def test_persists_and_returns(self):
        repo = InMemoryClientRepository()
        client = CreateClient(clients=repo).execute(name="  EMSA  ")
        assert client.name == "EMSA"
        assert repo.get(client.id) == client

    def test_archived_defaults_false(self):
        repo = InMemoryClientRepository()
        client = CreateClient(clients=repo).execute(name="EMSA")
        assert client.archived is False


class TestGetClient:
    def test_found(self):
        repo = InMemoryClientRepository()
        c = CreateClient(clients=repo).execute(name="EMSA")
        assert GetClient(clients=repo).execute(c.id) == c

    def test_missing_raises(self):
        repo = InMemoryClientRepository()
        with pytest.raises(EntityNotFoundError):
            GetClient(clients=repo).execute(uuid4())


class TestListClients:
    def test_excludes_archived_by_default(self):
        repo = InMemoryClientRepository()
        create = CreateClient(clients=repo)
        update = UpdateClient(clients=repo)
        a = create.execute(name="A")
        b = create.execute(name="B")
        update.execute(a.id, archived=True)
        listed = ListClients(clients=repo).execute()
        assert listed == [b]

    def test_includes_archived_when_asked(self):
        repo = InMemoryClientRepository()
        create = CreateClient(clients=repo)
        update = UpdateClient(clients=repo)
        a = create.execute(name="A")
        b = create.execute(name="B")
        update.execute(a.id, archived=True)
        listed = ListClients(clients=repo).execute(include_archived=True)
        assert {c.id for c in listed} == {a.id, b.id}


class TestUpdateClient:
    def test_patch_name_preserves_archived(self):
        repo = InMemoryClientRepository()
        c = CreateClient(clients=repo).execute(name="EMSA")
        updated = UpdateClient(clients=repo).execute(c.id, name="EMSA-2")
        assert updated.name == "EMSA-2"
        assert updated.archived is False
        assert updated.id == c.id

    def test_patch_archived_only(self):
        repo = InMemoryClientRepository()
        c = CreateClient(clients=repo).execute(name="EMSA")
        updated = UpdateClient(clients=repo).execute(c.id, archived=True)
        assert updated.name == "EMSA"
        assert updated.archived is True

    def test_no_fields_returns_existing(self):
        repo = InMemoryClientRepository()
        c = CreateClient(clients=repo).execute(name="EMSA")
        updated = UpdateClient(clients=repo).execute(c.id)
        assert updated == c

    def test_missing_raises(self):
        repo = InMemoryClientRepository()
        with pytest.raises(EntityNotFoundError):
            UpdateClient(clients=repo).execute(uuid4(), name="X")


class TestDeleteClient:
    def test_removes(self):
        repo = InMemoryClientRepository()
        c = CreateClient(clients=repo).execute(name="EMSA")
        DeleteClient(clients=repo).execute(c.id)
        assert repo.get(c.id) is None

    def test_missing_raises(self):
        repo = InMemoryClientRepository()
        with pytest.raises(EntityNotFoundError):
            DeleteClient(clients=repo).execute(uuid4())
