# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
from uuid import uuid4

from colourlog.composition.container import build_sqlite_container
from colourlog.domain.entities import Client


def test_build_sqlite_container_initializes_schema_and_repos(tmp_path: Path):
    db = tmp_path / "test.sqlite"
    container = build_sqlite_container(db)
    c = Client.create(id=uuid4(), name="EMSA")
    container.clients_repo.add(c)
    assert container.clients_repo.get(c.id) == c
    assert db.exists()
