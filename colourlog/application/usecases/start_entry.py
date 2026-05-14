# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
from uuid import UUID, uuid4

from colourlog.application.exceptions import EntityNotFoundError
from colourlog.application.ports.clock import Clock
from colourlog.application.ports.repositories import (
    EntryEventRepository,
    TaskRepository,
)
from colourlog.domain.entities import EntryEvent, Task
from colourlog.domain.value_objects import MatchSource, Source


@dataclass(frozen=True, slots=True)
class StartEntry:
    events: EntryEventRepository
    tasks: TaskRepository
    clock: Clock

    def execute(
        self,
        *,
        task_id: UUID,
        source: Source = Source.MANUAL,
        subtask_id: UUID | None = None,
        match_source: MatchSource | None = None,
        matched_keyword: str | None = None,
        calendar_event_id: str | None = None,
        note: str | None = None,
    ) -> EntryEvent:
        if self.tasks.get(task_id) is None:
            raise EntityNotFoundError(Task, task_id)
        if subtask_id is not None and self.tasks.get(subtask_id) is None:
            raise EntityNotFoundError(Task, subtask_id)
        event = EntryEvent.create(
            id=uuid4(),
            ts=self.clock.now(),
            task_id=task_id,
            subtask_id=subtask_id,
            source=source,
            match_source=match_source,
            matched_keyword=matched_keyword,
            calendar_event_id=calendar_event_id,
            note=note,
        )
        self.events.append(event)
        return event
