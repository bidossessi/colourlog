# SPDX-License-Identifier: GPL-3.0-or-later
import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from colourlog.composition.container import Container
from colourlog.composition.fastapi_app import create_app
from colourlog.domain import entities, value_objects
from colourlog.interface.http.routers.events import events as events_route
from httpx import ASGITransport, AsyncClient


def _start_event() -> entities.EntryEvent:
    return entities.EntryEvent.create(
        id=uuid4(),
        ts=datetime(2026, 5, 14, 10, 0, tzinfo=UTC),
        task_id=uuid4(),
        source=value_objects.Source.MANUAL,
    )


@pytest.mark.asyncio
async def test_events_route_returns_text_event_stream(container: Container):
    response = await events_route(bus=container.event_bus)
    assert response.media_type == "text/event-stream"


@pytest.mark.asyncio
async def test_events_body_iterator_emits_sse_chunk_on_publish(container: Container):
    response = await events_route(bus=container.event_bus)
    body_iter = response.body_iterator

    async def trigger() -> None:
        for _ in range(50):
            if container.event_bus._subscribers:  # type: ignore[attr-defined]
                break
            await asyncio.sleep(0.01)
        await container.event_bus.publish(_start_event())

    trigger_task = asyncio.create_task(trigger())
    iterator = aiter(body_iter)
    first_chunk = await asyncio.wait_for(anext(iterator), timeout=2.0)
    await trigger_task
    if isinstance(first_chunk, bytes):
        text = first_chunk.decode()
    elif isinstance(first_chunk, memoryview):
        text = bytes(first_chunk).decode()
    else:
        text = first_chunk
    assert text.startswith("event: entry_started\n")
    assert "data: " in text
    assert text.endswith("\n\n")


@pytest.mark.asyncio
async def test_start_endpoint_publishes_to_bus(container: Container):
    app = create_app(container)
    transport = ASGITransport(app=app)

    received: list[entities.EntryEvent] = []
    stream = container.event_bus.subscribe()

    async def reader() -> None:
        async for e in stream:
            received.append(e)
            return

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        p = (await ac.post("/api/v1/projects", json={"name": "P"})).json()
        t = (await ac.post("/api/v1/tasks", json={"name": "T", "project_id": p["id"]})).json()

        reader_task = asyncio.create_task(reader())
        await asyncio.sleep(0)
        await ac.post("/api/v1/entries/start", json={"task_id": t["id"]})
        await asyncio.wait_for(reader_task, timeout=2.0)

    assert len(received) == 1
    assert received[0].is_start
    assert str(received[0].task_id) == t["id"]
    await stream.aclose()
