# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import closing
from pathlib import Path
from uuid import uuid4

from colourlog.adapters.persistence.sqlite.client_repository import (
    SqliteClientRepository,
)
from colourlog.adapters.persistence.sqlite.engine import connect, init_schema
from colourlog.domain.entities import Client


def _new_client(name: str = "EMSA", archived: bool = False) -> Client:
    return Client.create(id=uuid4(), name=name, archived=archived)


class TestSqliteClientRepository:
    def test_add_then_get(self, db_path: Path):
        repo = SqliteClientRepository(db_path)
        c = _new_client()
        repo.add(c)
        assert repo.get(c.id) == c

    def test_get_missing_returns_none(self, db_path: Path):
        assert SqliteClientRepository(db_path).get(uuid4()) is None

    def test_list_default_excludes_archived(self, db_path: Path):
        repo = SqliteClientRepository(db_path)
        a = _new_client("A")
        b = _new_client("B")
        repo.add(a)
        repo.add(b)
        repo.update(Client.create(id=a.id, name=a.name, archived=True))
        assert repo.list() == [b]

    def test_list_include_archived(self, db_path: Path):
        repo = SqliteClientRepository(db_path)
        a = _new_client("A")
        b = _new_client("B")
        repo.add(a)
        repo.add(b)
        repo.update(Client.create(id=a.id, name=a.name, archived=True))
        listed = repo.list(include_archived=True)
        assert {c.id for c in listed} == {a.id, b.id}

    def test_update_mutates(self, db_path: Path):
        repo = SqliteClientRepository(db_path)
        c = _new_client("EMSA")
        repo.add(c)
        repo.update(Client.create(id=c.id, name="EMSA-2", archived=True))
        fetched = repo.get(c.id)
        assert fetched is not None
        assert fetched.name == "EMSA-2"
        assert fetched.archived is True

    def test_delete_removes(self, db_path: Path):
        repo = SqliteClientRepository(db_path)
        c = _new_client()
        repo.add(c)
        repo.delete(c.id)
        assert repo.get(c.id) is None

    def test_delete_missing_is_noop(self, db_path: Path):
        SqliteClientRepository(db_path).delete(uuid4())

    def test_init_schema_idempotent(self, db_path: Path):
        with closing(connect(db_path)) as conn:
            init_schema(conn)
            init_schema(conn)
