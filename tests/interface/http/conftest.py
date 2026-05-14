# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime

import pytest
from colourlog.composition.container import Container
from colourlog.composition.fastapi_app import create_app
from fastapi.testclient import TestClient

from tests.application.fakes import (
    AdvancingClock,
    InMemoryClientRepository,
    InMemoryEntryEventRepository,
    InMemoryProjectRepository,
    InMemoryTaskRepository,
)


@pytest.fixture
def container() -> Container:
    return Container(
        clients_repo=InMemoryClientRepository(),
        projects_repo=InMemoryProjectRepository(),
        tasks_repo=InMemoryTaskRepository(),
        events_repo=InMemoryEntryEventRepository(),
        clock=AdvancingClock(datetime(2026, 5, 14, 10, 0, tzinfo=UTC), step_seconds=1),
    )


@pytest.fixture
def client(container: Container) -> TestClient:
    return TestClient(create_app(container))
