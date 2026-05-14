# SPDX-License-Identifier: GPL-3.0-or-later
import asyncio
from collections.abc import AsyncGenerator

from colourlog.domain.entities import EntryEvent


class InMemoryEventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[EntryEvent]] = set()

    async def publish(self, event: EntryEvent) -> None:
        for queue in list(self._subscribers):
            await queue.put(event)

    async def subscribe(self) -> AsyncGenerator[EntryEvent, None]:
        queue: asyncio.Queue[EntryEvent] = asyncio.Queue()
        self._subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.discard(queue)
