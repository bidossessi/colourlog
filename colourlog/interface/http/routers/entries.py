# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from colourlog.application.usecases.list_entries import ListEntries
from colourlog.application.usecases.start_entry import StartEntry
from colourlog.application.usecases.stop_entry import StopEntry
from colourlog.interface.http.dependencies import (
    ClockDep,
    EventBusDep,
    EventsRepoDep,
    TasksRepoDep,
)
from colourlog.interface.http.schemas import EntryEventOut, EntryOut, EntryStartIn

router = APIRouter(prefix="/entries", tags=["entries"])


@router.post("/start", response_model=EntryEventOut, status_code=status.HTTP_201_CREATED)
async def start_entry(
    body: EntryStartIn,
    events: EventsRepoDep,
    tasks: TasksRepoDep,
    clock: ClockDep,
    bus: EventBusDep,
) -> EntryEventOut:
    ev = StartEntry(events=events, tasks=tasks, clock=clock).execute(
        task_id=body.task_id,
        subtask_id=body.subtask_id,
        note=body.note,
    )
    await bus.publish(ev)
    return EntryEventOut.model_validate(ev)


@router.post("/stop", response_model=EntryEventOut, status_code=status.HTTP_201_CREATED)
async def stop_entry(events: EventsRepoDep, clock: ClockDep, bus: EventBusDep) -> EntryEventOut:
    ev = StopEntry(events=events, clock=clock).execute()
    await bus.publish(ev)
    return EntryEventOut.model_validate(ev)


@router.get("", response_model=list[EntryOut])
def list_entries(
    events: EventsRepoDep,
    from_ts: Annotated[datetime | None, Query(alias="from")] = None,
    to_ts: Annotated[datetime | None, Query(alias="to")] = None,
    task_id: UUID | None = None,
) -> list[EntryOut]:
    items = ListEntries(events=events).execute(from_ts=from_ts, to_ts=to_ts, task_id=task_id)
    return [EntryOut.model_validate(e) for e in items]
