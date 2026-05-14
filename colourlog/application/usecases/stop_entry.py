# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
from uuid import uuid4

from colourlog.application.ports.clock import Clock
from colourlog.application.ports.repositories import EntryEventRepository
from colourlog.domain.entities import EntryEvent


@dataclass(frozen=True, slots=True)
class StopEntry:
    events: EntryEventRepository
    clock: Clock

    def execute(self) -> EntryEvent:
        event = EntryEvent.create(id=uuid4(), ts=self.clock.now())
        self.events.append(event)
        return event
