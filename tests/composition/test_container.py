# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
from uuid import uuid4

from colourlog.adapters.activitywatch.http_client import AwHttpReader
from colourlog.adapters.override.in_memory import InMemoryOverrideStore
from colourlog.composition.container import build_sqlite_container
from colourlog.domain.entities import Client


def test_build_sqlite_container_initializes_schema_and_repos(tmp_path: Path):
    db = tmp_path / "test.sqlite"
    container = build_sqlite_container(db)
    c = Client.create(id=uuid4(), name="EMSA")
    container.clients_repo.add(c)
    assert container.clients_repo.get(c.id) == c
    assert db.exists()


def test_build_sqlite_container_wires_ticker_collaborators(tmp_path: Path):
    db = tmp_path / "ticker.sqlite"
    container = build_sqlite_container(
        db,
        aw_base_url="http://example.test:9999",
        poll_interval=1.5,
    )
    assert isinstance(container.aw_reader, AwHttpReader)
    assert isinstance(container.override_store, InMemoryOverrideStore)
    assert container.poll_interval == 1.5
