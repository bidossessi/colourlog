# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
from uuid import UUID, uuid4

from colourlog.application.exceptions import EntityNotFoundError
from colourlog.application.ports.repositories import ClientRepository, ProjectRepository
from colourlog.domain.entities import Client, Project


@dataclass(frozen=True, slots=True)
class CreateProject:
    projects: ProjectRepository
    clients: ClientRepository

    def execute(self, *, name: str, client_id: UUID | None = None) -> Project:
        if client_id is not None and self.clients.get(client_id) is None:
            raise EntityNotFoundError(Client, client_id)
        project = Project.create(id=uuid4(), name=name, client_id=client_id)
        self.projects.add(project)
        return project


@dataclass(frozen=True, slots=True)
class GetProject:
    projects: ProjectRepository

    def execute(self, project_id: UUID) -> Project:
        existing = self.projects.get(project_id)
        if existing is None:
            raise EntityNotFoundError(Project, project_id)
        return existing


@dataclass(frozen=True, slots=True)
class ListProjects:
    projects: ProjectRepository

    def execute(
        self,
        *,
        client_id: UUID | None = None,
        include_archived: bool = False,
    ) -> list[Project]:
        return self.projects.list(
            client_id=client_id,
            include_archived=include_archived,
        )


@dataclass(frozen=True, slots=True)
class UpdateProject:
    projects: ProjectRepository
    clients: ClientRepository

    def execute(
        self,
        project_id: UUID,
        *,
        name: str | None = None,
        client_id: UUID | None = None,
        clear_client: bool = False,
        archived: bool | None = None,
    ) -> Project:
        existing = self.projects.get(project_id)
        if existing is None:
            raise EntityNotFoundError(Project, project_id)
        if client_id is not None and self.clients.get(client_id) is None:
            raise EntityNotFoundError(Client, client_id)
        new_client_id: UUID | None
        if clear_client:
            new_client_id = None
        elif client_id is not None:
            new_client_id = client_id
        else:
            new_client_id = existing.client_id
        updated = Project.create(
            id=existing.id,
            name=name if name is not None else existing.name,
            client_id=new_client_id,
            archived=archived if archived is not None else existing.archived,
        )
        self.projects.update(updated)
        return updated


@dataclass(frozen=True, slots=True)
class DeleteProject:
    projects: ProjectRepository

    def execute(self, project_id: UUID) -> None:
        if self.projects.get(project_id) is None:
            raise EntityNotFoundError(Project, project_id)
        self.projects.delete(project_id)
