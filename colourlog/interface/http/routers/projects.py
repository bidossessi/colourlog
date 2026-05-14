# SPDX-License-Identifier: GPL-3.0-or-later
from uuid import UUID

from fastapi import APIRouter, status

from colourlog.application.usecases.crud_project import (
    CreateProject,
    DeleteProject,
    GetProject,
    ListProjects,
    UpdateProject,
)
from colourlog.interface.http.dependencies import ClientsRepoDep, ProjectsRepoDep
from colourlog.interface.http.schemas import ProjectCreate, ProjectOut, ProjectPatch

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate, projects: ProjectsRepoDep, clients: ClientsRepoDep
) -> ProjectOut:
    project = CreateProject(projects=projects, clients=clients).execute(
        name=body.name, client_id=body.client_id
    )
    return ProjectOut.model_validate(project)


@router.get("", response_model=list[ProjectOut])
def list_projects(
    projects: ProjectsRepoDep,
    client_id: UUID | None = None,
    include_archived: bool = False,
) -> list[ProjectOut]:
    items = ListProjects(projects=projects).execute(
        client_id=client_id, include_archived=include_archived
    )
    return [ProjectOut.model_validate(p) for p in items]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: UUID, projects: ProjectsRepoDep) -> ProjectOut:
    project = GetProject(projects=projects).execute(project_id)
    return ProjectOut.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: UUID,
    body: ProjectPatch,
    projects: ProjectsRepoDep,
    clients: ClientsRepoDep,
) -> ProjectOut:
    project = UpdateProject(projects=projects, clients=clients).execute(
        project_id,
        name=body.name,
        client_id=body.client_id,
        clear_client=body.clear_client,
        archived=body.archived,
    )
    return ProjectOut.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, projects: ProjectsRepoDep) -> None:
    DeleteProject(projects=projects).execute(project_id)
