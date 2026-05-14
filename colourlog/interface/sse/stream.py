# SPDX-License-Identifier: GPL-3.0-or-later
from collections.abc import AsyncIterator

from colourlog.application.ports.event_bus import EventBus
from colourlog.domain.entities import EntryEvent
from colourlog.interface.http.schemas import EntryEventOut


def _format(event: EntryEvent) -> bytes:
    kind = "entry_started" if event.is_start else "entry_stopped"
    payload = EntryEventOut.model_validate(event).model_dump_json()
    return f"event: {kind}\ndata: {payload}\n\n".encode()


async def sse_stream(bus: EventBus) -> AsyncIterator[bytes]:
    async for event in bus.subscribe():
        yield _format(event)
