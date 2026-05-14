# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from colourlog.domain.value_objects import MatchSource, Mode, Source


class ClientCreate(BaseModel):
    name: str = Field(min_length=1)


class ClientPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    archived: bool | None = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    archived: bool


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    client_id: UUID | None = None


class ProjectPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    client_id: UUID | None = None
    clear_client: bool = False
    archived: bool | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    client_id: UUID | None
    archived: bool


class TaskCreate(BaseModel):
    name: str = Field(min_length=1)
    project_id: UUID
    code: str | None = None
    tags: list[str] = Field(default_factory=list)
    keywords: list[str] | None = None


class TaskPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    project_id: UUID | None = None
    code: str | None = None
    clear_code: bool = False
    tags: list[str] | None = None
    keywords: list[str] | None = None
    archived: bool | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    project_id: UUID
    code: str | None
    tags: tuple[str, ...]
    keywords: tuple[str, ...]
    created_at: datetime
    archived: bool


class EntryStartIn(BaseModel):
    task_id: UUID
    subtask_id: UUID | None = None
    note: str | None = None


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: UUID
    subtask_id: UUID | None
    start: datetime
    end: datetime | None
    source: Source
    match_source: MatchSource | None
    matched_keyword: str | None
    calendar_event_id: str | None
    note: str | None


class EntryEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    ts: datetime
    task_id: UUID | None
    subtask_id: UUID | None
    source: Source | None
    match_source: MatchSource | None
    matched_keyword: str | None
    calendar_event_id: str | None
    note: str | None


class CurrentTaskOut(BaseModel):
    entry: EntryOut
    task: TaskOut


class ModeOut(BaseModel):
    mode: Mode


class ModeIn(BaseModel):
    mode: Mode
