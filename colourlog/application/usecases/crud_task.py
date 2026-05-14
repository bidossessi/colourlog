# SPDX-License-Identifier: GPL-3.0-or-later
from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID, uuid4

from colourlog.application.exceptions import EntityNotFoundError
from colourlog.application.ports.clock import Clock
from colourlog.application.ports.repositories import ProjectRepository, TaskRepository
from colourlog.domain.entities import Project, Task


@dataclass(frozen=True, slots=True)
class CreateTask:
    tasks: TaskRepository
    projects: ProjectRepository
    clock: Clock

    def execute(
        self,
        *,
        name: str,
        project_id: UUID,
        code: str | None = None,
        tags: Iterable[str] = (),
        keywords: Iterable[str] | None = None,
    ) -> Task:
        if self.projects.get(project_id) is None:
            raise EntityNotFoundError(Project, project_id)
        task = Task.create(
            id=uuid4(),
            name=name,
            project_id=project_id,
            created_at=self.clock.now(),
            code=code,
            tags=tags,
            keywords=keywords,
        )
        self.tasks.add(task)
        return task


@dataclass(frozen=True, slots=True)
class GetTask:
    tasks: TaskRepository

    def execute(self, task_id: UUID) -> Task:
        existing = self.tasks.get(task_id)
        if existing is None:
            raise EntityNotFoundError(Task, task_id)
        return existing


@dataclass(frozen=True, slots=True)
class ListTasks:
    tasks: TaskRepository

    def execute(
        self,
        *,
        project_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[Task]:
        return self.tasks.list(
            project_id=project_id,
            include_archived=include_archived,
        )


@dataclass(frozen=True, slots=True)
class UpdateTask:
    tasks: TaskRepository
    projects: ProjectRepository

    def execute(
        self,
        task_id: UUID,
        *,
        name: str | None = None,
        project_id: UUID | None = None,
        code: str | None = None,
        clear_code: bool = False,
        tags: Iterable[str] | None = None,
        keywords: Iterable[str] | None = None,
        archived: bool | None = None,
    ) -> Task:
        existing = self.tasks.get(task_id)
        if existing is None:
            raise EntityNotFoundError(Task, task_id)
        if project_id is not None and self.projects.get(project_id) is None:
            raise EntityNotFoundError(Project, project_id)
        new_code: str | None
        if clear_code:
            new_code = None
        elif code is not None:
            new_code = code
        else:
            new_code = existing.code
        updated = Task.create(
            id=existing.id,
            name=name if name is not None else existing.name,
            project_id=project_id if project_id is not None else existing.project_id,
            created_at=existing.created_at,
            code=new_code,
            tags=tuple(tags) if tags is not None else existing.tags,
            keywords=tuple(keywords) if keywords is not None else existing.keywords,
            archived=archived if archived is not None else existing.archived,
        )
        self.tasks.update(updated)
        return updated


@dataclass(frozen=True, slots=True)
class DeleteTask:
    tasks: TaskRepository

    def execute(self, task_id: UUID) -> None:
        if self.tasks.get(task_id) is None:
            raise EntityNotFoundError(Task, task_id)
        self.tasks.delete(task_id)
