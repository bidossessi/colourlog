# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from colourlog.adapters.clock.system import SystemClock
from colourlog.adapters.event_bus.in_memory import InMemoryEventBus
from colourlog.adapters.persistence.sqlite.client_repository import (
    SqliteClientRepository,
)
from colourlog.adapters.persistence.sqlite.engine import connect, init_schema
from colourlog.adapters.persistence.sqlite.entry_event_repository import (
    SqliteEntryEventRepository,
)
from colourlog.adapters.persistence.sqlite.project_repository import (
    SqliteProjectRepository,
)
from colourlog.adapters.persistence.sqlite.task_repository import SqliteTaskRepository
from colourlog.application.ports.clock import Clock
from colourlog.application.ports.event_bus import EventBus
from colourlog.application.ports.repositories import (
    ClientRepository,
    EntryEventRepository,
    ProjectRepository,
    TaskRepository,
)


@dataclass(frozen=True, slots=True)
class Container:
    clients_repo: ClientRepository
    projects_repo: ProjectRepository
    tasks_repo: TaskRepository
    events_repo: EntryEventRepository
    event_bus: EventBus
    clock: Clock


def build_sqlite_container(database_path: Path | str) -> Container:
    with closing(connect(database_path)) as conn:
        init_schema(conn)
    return Container(
        clients_repo=SqliteClientRepository(database_path),
        projects_repo=SqliteProjectRepository(database_path),
        tasks_repo=SqliteTaskRepository(database_path),
        events_repo=SqliteEntryEventRepository(database_path),
        event_bus=InMemoryEventBus(),
        clock=SystemClock(),
    )
