# SPDX-License-Identifier: GPL-3.0-or-later
import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from colourlog.adapters.event_bus.in_memory import InMemoryEventBus
from colourlog.domain import entities, value_objects


def _start_event() -> entities.EntryEvent:
    return entities.EntryEvent.create(
        id=uuid4(),
        ts=datetime(2026, 5, 14, 10, 0, tzinfo=UTC),
        task_id=uuid4(),
        source=value_objects.Source.MANUAL,
    )


@pytest.mark.asyncio
async def test_subscribe_receives_published_event():
    bus = InMemoryEventBus()
    received: list[entities.EntryEvent] = []
    stream = bus.subscribe()

    async def reader() -> None:
        async for e in stream:
            received.append(e)
            break

    task = asyncio.create_task(reader())
    await asyncio.sleep(0)  # let reader register
    ev = _start_event()
    await bus.publish(ev)
    await task
    assert received == [ev]


@pytest.mark.asyncio
async def test_fans_out_to_multiple_subscribers():
    bus = InMemoryEventBus()
    received_a: list[entities.EntryEvent] = []
    received_b: list[entities.EntryEvent] = []

    async def reader(target: list[entities.EntryEvent]) -> None:
        async for e in bus.subscribe():
            target.append(e)
            break

    t1 = asyncio.create_task(reader(received_a))
    t2 = asyncio.create_task(reader(received_b))
    await asyncio.sleep(0)
    ev = _start_event()
    await bus.publish(ev)
    await asyncio.gather(t1, t2)
    assert received_a == [ev]
    assert received_b == [ev]


@pytest.mark.asyncio
async def test_unsubscribe_on_iterator_close():
    bus = InMemoryEventBus()
    stream = bus.subscribe()

    async def reader() -> None:
        async for _ in stream:
            return

    task = asyncio.create_task(reader())
    await asyncio.sleep(0)
    await bus.publish(_start_event())
    await task
    await stream.aclose()
    assert bus._subscribers == set()
