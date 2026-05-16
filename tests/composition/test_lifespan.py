# SPDX-License-Identifier: GPL-3.0-or-later
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from colourlog.adapters.event_bus.in_memory import InMemoryEventBus
from colourlog.adapters.override.in_memory import InMemoryOverrideStore
from colourlog.application.ports.activitywatch import WindowSnapshot
from colourlog.composition.container import Container
from colourlog.composition.fastapi_app import create_app
from colourlog.domain.entities import Task
from colourlog.domain.value_objects import Mode, Source
from fastapi.testclient import TestClient

from tests.application.fakes import (
    AdvancingClock,
    InMemoryActivityWatchReader,
    InMemoryClientRepository,
    InMemoryEntryEventRepository,
    InMemoryModeRepository,
    InMemoryProjectRepository,
    InMemoryTaskRepository,
)


def _ts(offset_min: int = 0) -> datetime:
    return datetime(2026, 5, 14, 10, 0, tzinfo=UTC) + timedelta(minutes=offset_min)


def test_lifespan_starts_ticker_and_writes_auto_event():
    tasks_repo = InMemoryTaskRepository()
    t = Task.create(
        id=uuid4(),
        name="T1",
        project_id=uuid4(),
        created_at=_ts(),
        keywords=["t1"],
    )
    tasks_repo.add(t)
    events_repo = InMemoryEntryEventRepository()
    container = Container(
        clients_repo=InMemoryClientRepository(),
        projects_repo=InMemoryProjectRepository(),
        tasks_repo=tasks_repo,
        events_repo=events_repo,
        modes_repo=InMemoryModeRepository(initial=Mode.AUTO),
        event_bus=InMemoryEventBus(),
        clock=AdvancingClock(_ts(), step_seconds=1),
        aw_reader=InMemoryActivityWatchReader(
            window=WindowSnapshot(ts=_ts(), app="App", title="t1 here", url=None)
        ),
        override_store=InMemoryOverrideStore(),
        poll_interval=0.01,
    )
    app = create_app(container)
    with TestClient(app):
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            if events_repo.latest_event() is not None:
                break
            time.sleep(0.02)
    latest = events_repo.latest_event()
    assert latest is not None
    assert latest.task_id == t.id
    assert latest.source is Source.AUTO
