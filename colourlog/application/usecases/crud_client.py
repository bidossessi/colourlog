# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
from uuid import UUID, uuid4

from colourlog.application.exceptions import EntityNotFoundError
from colourlog.application.ports.repositories import ClientRepository
from colourlog.domain.entities import Client


@dataclass(frozen=True, slots=True)
class CreateClient:
    clients: ClientRepository

    def execute(self, *, name: str) -> Client:
        client = Client.create(id=uuid4(), name=name)
        self.clients.add(client)
        return client


@dataclass(frozen=True, slots=True)
class GetClient:
    clients: ClientRepository

    def execute(self, client_id: UUID) -> Client:
        existing = self.clients.get(client_id)
        if existing is None:
            raise EntityNotFoundError(Client, client_id)
        return existing


@dataclass(frozen=True, slots=True)
class ListClients:
    clients: ClientRepository

    def execute(self, *, include_archived: bool = False) -> list[Client]:
        return self.clients.list(include_archived=include_archived)


@dataclass(frozen=True, slots=True)
class UpdateClient:
    clients: ClientRepository

    def execute(
        self,
        client_id: UUID,
        *,
        name: str | None = None,
        archived: bool | None = None,
    ) -> Client:
        existing = self.clients.get(client_id)
        if existing is None:
            raise EntityNotFoundError(Client, client_id)
        updated = Client.create(
            id=existing.id,
            name=name if name is not None else existing.name,
            archived=archived if archived is not None else existing.archived,
        )
        self.clients.update(updated)
        return updated


@dataclass(frozen=True, slots=True)
class DeleteClient:
    clients: ClientRepository

    def execute(self, client_id: UUID) -> None:
        if self.clients.get(client_id) is None:
            raise EntityNotFoundError(Client, client_id)
        self.clients.delete(client_id)
