# SPDX-License-Identifier: GPL-3.0-or-later
from uuid import UUID

from fastapi import APIRouter, status

from colourlog.application.usecases.crud_task import (
    CreateTask,
    DeleteTask,
    GetTask,
    ListTasks,
    UpdateTask,
)
from colourlog.application.usecases.current_task import GetCurrentTask
from colourlog.interface.http.dependencies import (
    ClockDep,
    EventsRepoDep,
    ProjectsRepoDep,
    TasksRepoDep,
)
from colourlog.interface.http.schemas import (
    CurrentTaskOut,
    EntryOut,
    TaskCreate,
    TaskOut,
    TaskPatch,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    body: TaskCreate,
    tasks: TasksRepoDep,
    projects: ProjectsRepoDep,
    clock: ClockDep,
) -> TaskOut:
    task = CreateTask(tasks=tasks, projects=projects, clock=clock).execute(
        name=body.name,
        project_id=body.project_id,
        code=body.code,
        tags=body.tags,
        keywords=body.keywords,
    )
    return TaskOut.model_validate(task)


@router.get("", response_model=list[TaskOut])
def list_tasks(
    tasks: TasksRepoDep,
    project_id: UUID | None = None,
    include_archived: bool = False,
) -> list[TaskOut]:
    items = ListTasks(tasks=tasks).execute(project_id=project_id, include_archived=include_archived)
    return [TaskOut.model_validate(t) for t in items]


@router.get("/current", response_model=CurrentTaskOut | None)
def get_current_task(events: EventsRepoDep, tasks: TasksRepoDep) -> CurrentTaskOut | None:
    result = GetCurrentTask(events=events, tasks=tasks).execute()
    if result is None:
        return None
    entry, task = result
    return CurrentTaskOut(
        entry=EntryOut.model_validate(entry),
        task=TaskOut.model_validate(task),
    )


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: UUID, tasks: TasksRepoDep) -> TaskOut:
    task = GetTask(tasks=tasks).execute(task_id)
    return TaskOut.model_validate(task)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: UUID,
    body: TaskPatch,
    tasks: TasksRepoDep,
    projects: ProjectsRepoDep,
) -> TaskOut:
    task = UpdateTask(tasks=tasks, projects=projects).execute(
        task_id,
        name=body.name,
        project_id=body.project_id,
        code=body.code,
        clear_code=body.clear_code,
        tags=body.tags,
        keywords=body.keywords,
        archived=body.archived,
    )
    return TaskOut.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID, tasks: TasksRepoDep) -> None:
    DeleteTask(tasks=tasks).execute(task_id)
