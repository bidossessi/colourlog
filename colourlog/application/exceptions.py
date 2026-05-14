# SPDX-License-Identifier: GPL-3.0-or-later
from uuid import UUID


class ApplicationError(Exception):
    pass


class EntityNotFoundError(ApplicationError):
    def __init__(self, entity_type: type, entity_id: UUID) -> None:
        super().__init__(f"{entity_type.__name__} not found: {entity_id}")
        self.entity_type = entity_type
        self.entity_id = entity_id
