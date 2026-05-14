# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest
from colourlog.adapters.event_bus.in_memory import InMemoryEventBus
from colourlog.adapters.persistence.sqlite.client_repository import (
    SqliteClientRepository,
)
from colourlog.adapters.persistence.sqlite.engine import connect, init_schema
from colourlog.adapters.persistence.sqlite.entry_event_repository import (
    SqliteEntryEventRepository,
)
from colourlog.adapters.persistence.sqlite.mode_repository import (
    SqliteModeRepository,
)
from colourlog.adapters.persistence.sqlite.project_repository import (
    SqliteProjectRepository,
)
from colourlog.adapters.persistence.sqlite.task_repository import SqliteTaskRepository
from colourlog.composition.container import Container
from colourlog.composition.fastapi_app import create_app
from fastapi.testclient import TestClient

from tests.application.fakes import AdvancingClock


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "functional.sqlite"
    with closing(connect(path)) as conn:
        init_schema(conn)
    return path


@pytest.fixture
def container(db_path: Path) -> Container:
    return Container(
        clients_repo=SqliteClientRepository(db_path),
        projects_repo=SqliteProjectRepository(db_path),
        tasks_repo=SqliteTaskRepository(db_path),
        events_repo=SqliteEntryEventRepository(db_path),
        modes_repo=SqliteModeRepository(db_path),
        event_bus=InMemoryEventBus(),
        clock=AdvancingClock(datetime(2026, 5, 14, 10, 0, tzinfo=UTC), step_seconds=1),
    )


@pytest.fixture
def client(container: Container) -> TestClient:
    return TestClient(create_app(container))
