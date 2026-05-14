# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import datetime
from typing import Protocol
from uuid import UUID

from colourlog.domain.entities import Client, Entry, EntryEvent, Project, Task
from colourlog.domain.value_objects import Mode


class ClientRepository(Protocol):
    def add(self, client: Client) -> None: ...

    def get(self, id: UUID) -> Client | None: ...

    def list(self, *, include_archived: bool = False) -> list[Client]: ...

    def update(self, client: Client) -> None: ...

    def delete(self, id: UUID) -> None: ...


class ProjectRepository(Protocol):
    def add(self, project: Project) -> None: ...

    def get(self, id: UUID) -> Project | None: ...

    def list(
        self,
        *,
        client_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[Project]: ...

    def update(self, project: Project) -> None: ...

    def delete(self, id: UUID) -> None: ...


class TaskRepository(Protocol):
    def add(self, task: Task) -> None: ...

    def get(self, id: UUID) -> Task | None: ...

    def list(
        self,
        *,
        project_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[Task]: ...

    def update(self, task: Task) -> None: ...

    def delete(self, id: UUID) -> None: ...


class EntryEventRepository(Protocol):
    def append(self, event: EntryEvent) -> None: ...

    def get_event(self, id: UUID) -> EntryEvent | None: ...

    def latest_event(self) -> EntryEvent | None: ...

    def events_in_range(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ) -> list[EntryEvent]: ...

    def current_entry(self) -> Entry | None: ...

    def entries_in_range(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        task_id: UUID | None = None,
    ) -> list[Entry]: ...


class ModeRepository(Protocol):
    def get(self) -> Mode: ...

    def set(self, mode: Mode) -> None: ...
