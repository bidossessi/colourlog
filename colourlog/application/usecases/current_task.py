# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass

from colourlog.application.exceptions import EntityNotFoundError
from colourlog.application.ports.repositories import (
    EntryEventRepository,
    TaskRepository,
)
from colourlog.domain.entities import Entry, Task


@dataclass(frozen=True, slots=True)
class GetCurrentTask:
    events: EntryEventRepository
    tasks: TaskRepository

    def execute(self) -> tuple[Entry, Task] | None:
        entry = self.events.current_entry()
        if entry is None:
            return None
        task = self.tasks.get(entry.task_id)
        if task is None:
            raise EntityNotFoundError(Task, entry.task_id)
        return (entry, task)
