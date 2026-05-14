# SPDX-License-Identifier: GPL-3.0-or-later
import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from colourlog.adapters.event_bus.in_memory import InMemoryEventBus
from colourlog.domain import entities, value_objects
from colourlog.interface.sse.stream import sse_stream


def _start_event() -> entities.EntryEvent:
    return entities.EntryEvent.create(
        id=uuid4(),
        ts=datetime(2026, 5, 14, 10, 0, tzinfo=UTC),
        task_id=uuid4(),
        source=value_objects.Source.MANUAL,
    )


def _stop_event() -> entities.EntryEvent:
    return entities.EntryEvent.create(
        id=uuid4(),
        ts=datetime(2026, 5, 14, 10, 1, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_emits_entry_started_event_name():
    bus = InMemoryEventBus()
    stream = sse_stream(bus)
    chunks: list[bytes] = []

    async def reader() -> None:
        async for chunk in stream:
            chunks.append(chunk)
            break

    task = asyncio.create_task(reader())
    await asyncio.sleep(0)
    await bus.publish(_start_event())
    await task
    chunk = chunks[0].decode()
    assert chunk.startswith("event: entry_started\n")
    assert "data: " in chunk
    assert chunk.endswith("\n\n")


@pytest.mark.asyncio
async def test_emits_entry_stopped_event_name():
    bus = InMemoryEventBus()
    stream = sse_stream(bus)
    chunks: list[bytes] = []

    async def reader() -> None:
        async for chunk in stream:
            chunks.append(chunk)
            break

    task = asyncio.create_task(reader())
    await asyncio.sleep(0)
    await bus.publish(_stop_event())
    await task
    assert chunks[0].decode().startswith("event: entry_stopped\n")


@pytest.mark.asyncio
async def test_stream_exits_cleanly_when_bus_yields_nothing():
    """sse_stream's `async for` exit path (loop terminates without break)."""

    class _EmptyBus:
        async def publish(self, _event: object) -> None:
            pass

        async def subscribe(self):
            return
            yield  # makes this an async generator

    chunks: list[bytes] = []
    async for chunk in sse_stream(_EmptyBus()):
        chunks.append(chunk)
    assert chunks == []
