# SPDX-License-Identifier: GPL-3.0-or-later
import sqlite3
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from colourlog.adapters.persistence.sqlite.client_repository import (
    SqliteClientRepository,
)
from colourlog.adapters.persistence.sqlite.project_repository import (
    SqliteProjectRepository,
)
from colourlog.domain.entities import Client, Project


def _project(
    name: str = "Evvue",
    client_id: UUID | None = None,
    archived: bool = False,
) -> Project:
    return Project.create(id=uuid4(), name=name, client_id=client_id, archived=archived)


class TestSqliteProjectRepository:
    def test_add_get_without_client(self, db_path: Path):
        repo = SqliteProjectRepository(db_path)
        p = _project()
        repo.add(p)
        assert repo.get(p.id) == p

    def test_add_get_with_client(self, db_path: Path):
        clients = SqliteClientRepository(db_path)
        c = Client.create(id=uuid4(), name="EMSA")
        clients.add(c)
        repo = SqliteProjectRepository(db_path)
        p = _project(client_id=c.id)
        repo.add(p)
        fetched = repo.get(p.id)
        assert fetched is not None
        assert fetched.client_id == c.id

    def test_add_unknown_client_violates_fk(self, db_path: Path):
        repo = SqliteProjectRepository(db_path)
        p = _project(client_id=uuid4())
        with pytest.raises(sqlite3.IntegrityError):
            repo.add(p)

    def test_get_missing_returns_none(self, db_path: Path):
        assert SqliteProjectRepository(db_path).get(uuid4()) is None

    def test_list_default_excludes_archived(self, db_path: Path):
        repo = SqliteProjectRepository(db_path)
        a = _project("A")
        b = _project("B")
        repo.add(a)
        repo.add(b)
        repo.update(Project.create(id=a.id, name=a.name, archived=True))
        assert repo.list() == [b]

    def test_list_filter_by_client(self, db_path: Path):
        clients = SqliteClientRepository(db_path)
        c1 = Client.create(id=uuid4(), name="C1")
        c2 = Client.create(id=uuid4(), name="C2")
        clients.add(c1)
        clients.add(c2)
        repo = SqliteProjectRepository(db_path)
        p1 = _project("P1", client_id=c1.id)
        p2 = _project("P2", client_id=c2.id)
        repo.add(p1)
        repo.add(p2)
        listed = repo.list(client_id=c1.id)
        assert listed == [p1]

    def test_list_include_archived(self, db_path: Path):
        repo = SqliteProjectRepository(db_path)
        a = _project("A")
        b = _project("B")
        repo.add(a)
        repo.add(b)
        repo.update(Project.create(id=a.id, name=a.name, archived=True))
        listed = repo.list(include_archived=True)
        assert {p.id for p in listed} == {a.id, b.id}

    def test_update_mutates(self, db_path: Path):
        repo = SqliteProjectRepository(db_path)
        p = _project()
        repo.add(p)
        repo.update(Project.create(id=p.id, name="Evvue2", archived=True))
        fetched = repo.get(p.id)
        assert fetched is not None
        assert fetched.name == "Evvue2"
        assert fetched.archived is True

    def test_delete_removes(self, db_path: Path):
        repo = SqliteProjectRepository(db_path)
        p = _project()
        repo.add(p)
        repo.delete(p.id)
        assert repo.get(p.id) is None
