# SPDX-License-Identifier: GPL-3.0-or-later
from uuid import UUID

from fastapi import APIRouter, status

from colourlog.application.usecases.crud_client import (
    CreateClient,
    DeleteClient,
    GetClient,
    ListClients,
    UpdateClient,
)
from colourlog.interface.http.dependencies import ClientsRepoDep
from colourlog.interface.http.schemas import ClientCreate, ClientOut, ClientPatch

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(body: ClientCreate, clients: ClientsRepoDep) -> ClientOut:
    client = CreateClient(clients=clients).execute(name=body.name)
    return ClientOut.model_validate(client)


@router.get("", response_model=list[ClientOut])
def list_clients(clients: ClientsRepoDep, include_archived: bool = False) -> list[ClientOut]:
    items = ListClients(clients=clients).execute(include_archived=include_archived)
    return [ClientOut.model_validate(c) for c in items]


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: UUID, clients: ClientsRepoDep) -> ClientOut:
    client = GetClient(clients=clients).execute(client_id)
    return ClientOut.model_validate(client)


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: UUID, body: ClientPatch, clients: ClientsRepoDep) -> ClientOut:
    client = UpdateClient(clients=clients).execute(
        client_id, name=body.name, archived=body.archived
    )
    return ClientOut.model_validate(client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: UUID, clients: ClientsRepoDep) -> None:
    DeleteClient(clients=clients).execute(client_id)
