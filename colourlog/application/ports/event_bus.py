# SPDX-License-Identifier: GPL-3.0-or-later
from collections.abc import AsyncGenerator
from typing import Protocol

from colourlog.domain.entities import EntryEvent


class EventBus(Protocol):
    async def publish(self, event: EntryEvent) -> None: ...

    def subscribe(self) -> AsyncGenerator[EntryEvent, None]: ...
