# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Annotated

from fastapi import Depends

from colourlog.application.ports.clock import Clock
from colourlog.application.ports.event_bus import EventBus
from colourlog.application.ports.repositories import (
    ClientRepository,
    EntryEventRepository,
    ProjectRepository,
    TaskRepository,
)


def get_clients_repo() -> ClientRepository:
    raise NotImplementedError("composition root must override get_clients_repo")


def get_projects_repo() -> ProjectRepository:
    raise NotImplementedError("composition root must override get_projects_repo")


def get_tasks_repo() -> TaskRepository:
    raise NotImplementedError("composition root must override get_tasks_repo")


def get_events_repo() -> EntryEventRepository:
    raise NotImplementedError("composition root must override get_events_repo")


def get_event_bus() -> EventBus:
    raise NotImplementedError("composition root must override get_event_bus")


def get_clock() -> Clock:
    raise NotImplementedError("composition root must override get_clock")


ClientsRepoDep = Annotated[ClientRepository, Depends(get_clients_repo)]
ProjectsRepoDep = Annotated[ProjectRepository, Depends(get_projects_repo)]
TasksRepoDep = Annotated[TaskRepository, Depends(get_tasks_repo)]
EventsRepoDep = Annotated[EntryEventRepository, Depends(get_events_repo)]
EventBusDep = Annotated[EventBus, Depends(get_event_bus)]
ClockDep = Annotated[Clock, Depends(get_clock)]
