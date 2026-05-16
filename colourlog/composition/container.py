# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from colourlog.adapters.activitywatch.http_client import AwHttpReader
from colourlog.adapters.clock.system import SystemClock
from colourlog.adapters.event_bus.in_memory import InMemoryEventBus
from colourlog.adapters.override.in_memory import InMemoryOverrideStore
from colourlog.adapters.persistence.sqlite.client_repository import (
    SqliteClientRepository,
)
from colourlog.adapters.persistence.sqlite.engine import connect, init_schema
from colourlog.adapters.persistence.sqlite.entry_event_repository import (
    SqliteEntryEventRepository,
)
from colourlog.adapters.persistence.sqlite.mode_repository import (
    SqliteModeRepository,
)
from colourlog.adapters.persistence.sqlite.project_repository import (
    SqliteProjectRepository,
)
from colourlog.adapters.persistence.sqlite.task_repository import SqliteTaskRepository
from colourlog.application.ports.activitywatch import ActivityWatchReader
from colourlog.application.ports.clock import Clock
from colourlog.application.ports.event_bus import EventBus
from colourlog.application.ports.override import OverrideStore
from colourlog.application.ports.repositories import (
    ClientRepository,
    EntryEventRepository,
    ModeRepository,
    ProjectRepository,
    TaskRepository,
)


@dataclass(frozen=True, slots=True)
class Container:
    clients_repo: ClientRepository
    projects_repo: ProjectRepository
    tasks_repo: TaskRepository
    events_repo: EntryEventRepository
    modes_repo: ModeRepository
    event_bus: EventBus
    clock: Clock
    aw_reader: ActivityWatchReader
    override_store: OverrideStore
    poll_interval: float = 3.0


def build_sqlite_container(
    database_path: Path | str,
    *,
    aw_base_url: str = "http://127.0.0.1:5600",
    poll_interval: float = 3.0,
) -> Container:
    with closing(connect(database_path)) as conn:
        init_schema(conn)
    return Container(
        clients_repo=SqliteClientRepository(database_path),
        projects_repo=SqliteProjectRepository(database_path),
        tasks_repo=SqliteTaskRepository(database_path),
        events_repo=SqliteEntryEventRepository(database_path),
        modes_repo=SqliteModeRepository(database_path),
        event_bus=InMemoryEventBus(),
        clock=SystemClock(),
        aw_reader=AwHttpReader(base_url=aw_base_url),
        override_store=InMemoryOverrideStore(),
        poll_interval=poll_interval,
    )
