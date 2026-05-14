# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from colourlog.application.ports.repositories import EntryEventRepository
from colourlog.domain.entities import Entry


@dataclass(frozen=True, slots=True)
class ListEntries:
    events: EntryEventRepository

    def execute(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        task_id: UUID | None = None,
    ) -> list[Entry]:
        return self.events.entries_in_range(from_ts=from_ts, to_ts=to_ts, task_id=task_id)
