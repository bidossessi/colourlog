# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import datetime
from uuid import UUID

from colourlog.domain.entities import Client, Entry, EntryEvent, Project, Task
from colourlog.domain.value_objects import Mode


class InMemoryClientRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Client] = {}

    def add(self, client: Client) -> None:
        self._store[client.id] = client

    def get(self, id: UUID) -> Client | None:
        return self._store.get(id)

    def list(self, *, include_archived: bool = False) -> list[Client]:
        items = list(self._store.values())
        if not include_archived:
            items = [c for c in items if not c.archived]
        return items

    def update(self, client: Client) -> None:
        self._store[client.id] = client

    def delete(self, id: UUID) -> None:
        self._store.pop(id, None)


class InMemoryProjectRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Project] = {}

    def add(self, project: Project) -> None:
        self._store[project.id] = project

    def get(self, id: UUID) -> Project | None:
        return self._store.get(id)

    def list(
        self,
        *,
        client_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[Project]:
        items = list(self._store.values())
        if client_id is not None:
            items = [p for p in items if p.client_id == client_id]
        if not include_archived:
            items = [p for p in items if not p.archived]
        return items

    def update(self, project: Project) -> None:
        self._store[project.id] = project

    def delete(self, id: UUID) -> None:
        self._store.pop(id, None)


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Task] = {}

    def add(self, task: Task) -> None:
        self._store[task.id] = task

    def get(self, id: UUID) -> Task | None:
        return self._store.get(id)

    def list(
        self,
        *,
        project_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[Task]:
        items = list(self._store.values())
        if project_id is not None:
            items = [t for t in items if t.project_id == project_id]
        if not include_archived:
            items = [t for t in items if not t.archived]
        return items

    def update(self, task: Task) -> None:
        self._store[task.id] = task

    def delete(self, id: UUID) -> None:
        self._store.pop(id, None)


class InMemoryEntryEventRepository:
    def __init__(self) -> None:
        self._events: list[EntryEvent] = []

    def append(self, event: EntryEvent) -> None:
        self._events.append(event)

    def get_event(self, id: UUID) -> EntryEvent | None:
        for e in self._events:
            if e.id == id:
                return e
        return None

    def latest_event(self) -> EntryEvent | None:
        if not self._events:
            return None
        return max(self._events, key=lambda e: e.ts)

    def events_in_range(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ) -> list[EntryEvent]:
        items = sorted(self._events, key=lambda e: e.ts)
        if from_ts is not None:
            items = [e for e in items if e.ts >= from_ts]
        if to_ts is not None:
            items = [e for e in items if e.ts <= to_ts]
        return items

    def current_entry(self) -> Entry | None:
        latest = self.latest_event()
        if latest is None or latest.is_stop:
            return None
        return Entry.from_event(latest, end=None)

    def entries_in_range(
        self,
        *,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        task_id: UUID | None = None,
    ) -> list[Entry]:
        sorted_events = sorted(self._events, key=lambda e: e.ts)
        result: list[Entry] = []
        for i, ev in enumerate(sorted_events):
            if not ev.is_start:
                continue
            if task_id is not None and ev.task_id != task_id:
                continue
            if from_ts is not None and ev.ts < from_ts:
                continue
            if to_ts is not None and ev.ts > to_ts:
                continue
            end = sorted_events[i + 1].ts if i + 1 < len(sorted_events) else None
            result.append(Entry.from_event(ev, end=end))
        return result


class AdvancingClock:
    def __init__(self, start: datetime, step_seconds: int = 60) -> None:
        self._now = start
        self._step = step_seconds

    def now(self) -> datetime:
        from datetime import timedelta

        current = self._now
        self._now = current + timedelta(seconds=self._step)
        return current


class FrozenClock:
    def __init__(self, ts: datetime) -> None:
        self._ts = ts

    def now(self) -> datetime:
        return self._ts


class InMemoryModeRepository:
    def __init__(self, initial: Mode = Mode.MANUAL) -> None:
        self._mode = initial

    def get(self) -> Mode:
        return self._mode

    def set(self, mode: Mode) -> None:
        self._mode = mode
