# SPDX-License-Identifier: GPL-3.0-or-later
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import cast
from uuid import UUID

from colourlog.domain.exceptions import (
    EndBeforeStartError,
    IncoherentStopEventError,
    InvalidKeywordError,
    InvalidNameError,
    InvalidTextFieldError,
    NaiveDatetimeError,
    SourceMatchSourceMismatchError,
    SubtaskWithoutTaskError,
)
from colourlog.domain.value_objects import MatchSource, Source


def _normalize_name(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise InvalidNameError(value)
    return stripped


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


@dataclass(frozen=True, slots=True, kw_only=True)
class Client:
    id: UUID
    name: str
    archived: bool = False

    def __post_init__(self) -> None:
        if not self.name or self.name != self.name.strip():
            raise InvalidNameError(self.name)

    @classmethod
    def create(cls, *, id: UUID, name: str, archived: bool = False) -> "Client":
        return cls(id=id, name=_normalize_name(name), archived=archived)


@dataclass(frozen=True, slots=True, kw_only=True)
class Project:
    id: UUID
    name: str
    client_id: UUID | None = None
    archived: bool = False

    def __post_init__(self) -> None:
        if not self.name or self.name != self.name.strip():
            raise InvalidNameError(self.name)

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        name: str,
        client_id: UUID | None = None,
        archived: bool = False,
    ) -> "Project":
        return cls(
            id=id,
            name=_normalize_name(name),
            client_id=client_id,
            archived=archived,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Task:
    id: UUID
    name: str
    project_id: UUID
    created_at: datetime
    code: str | None = None
    tags: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    archived: bool = False

    def __post_init__(self) -> None:
        if not self.name or self.name != self.name.strip():
            raise InvalidNameError(self.name)
        for k in self.keywords:
            if not k or k != k.strip() or k != k.lower():
                raise InvalidKeywordError(k)

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        name: str,
        project_id: UUID,
        created_at: datetime,
        code: str | None = None,
        tags: Iterable[str] = (),
        keywords: Iterable[str] | None = None,
        archived: bool = False,
    ) -> "Task":
        name_n = _normalize_name(name)
        tags_n = tuple(t.strip() for t in tags if t.strip())
        if keywords is None:
            kw_n: tuple[str, ...] = (name_n.lower(),)
        else:
            kw_n = tuple(k.strip().lower() for k in keywords if k.strip())
        return cls(
            id=id,
            name=name_n,
            project_id=project_id,
            created_at=created_at,
            code=_normalize_optional_text(code),
            tags=tags_n,
            keywords=kw_n,
            archived=archived,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class EntryEvent:
    id: UUID
    ts: datetime
    task_id: UUID | None = None
    subtask_id: UUID | None = None
    source: Source | None = None
    match_source: MatchSource | None = None
    matched_keyword: str | None = None
    calendar_event_id: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if self.ts.tzinfo is None:
            raise NaiveDatetimeError("ts", self.ts)
        if (self.task_id is None) != (self.source is None):
            raise IncoherentStopEventError(self.task_id, self.source)
        if self.subtask_id is not None and self.task_id is None:
            raise SubtaskWithoutTaskError(self.subtask_id)
        if self.source is Source.MANUAL and self.match_source is not None:
            raise SourceMatchSourceMismatchError(self.source, self.match_source)
        if self.source is Source.AUTO and self.match_source is None:
            raise SourceMatchSourceMismatchError(self.source, self.match_source)
        for field, value in (
            ("matched_keyword", self.matched_keyword),
            ("calendar_event_id", self.calendar_event_id),
            ("note", self.note),
        ):
            if value is not None and (value != value.strip() or value == ""):
                raise InvalidTextFieldError(field, value)

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        ts: datetime,
        task_id: UUID | None = None,
        subtask_id: UUID | None = None,
        source: Source | None = None,
        match_source: MatchSource | None = None,
        matched_keyword: str | None = None,
        calendar_event_id: str | None = None,
        note: str | None = None,
    ) -> "EntryEvent":
        return cls(
            id=id,
            ts=ts,
            task_id=task_id,
            subtask_id=subtask_id,
            source=source,
            match_source=match_source,
            matched_keyword=_normalize_optional_text(matched_keyword),
            calendar_event_id=_normalize_optional_text(calendar_event_id),
            note=_normalize_optional_text(note),
        )

    @property
    def is_stop(self) -> bool:
        return self.task_id is None

    @property
    def is_start(self) -> bool:
        return self.task_id is not None


@dataclass(frozen=True, slots=True, kw_only=True)
class Entry:
    """Projection of a start-event with derived end from the next event's ts.

    Read-only view; never persisted. Constructed by repo projection methods.
    """

    id: UUID
    task_id: UUID
    start: datetime
    source: Source
    subtask_id: UUID | None = None
    end: datetime | None = None
    match_source: MatchSource | None = None
    matched_keyword: str | None = None
    calendar_event_id: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if self.start.tzinfo is None:
            raise NaiveDatetimeError("start", self.start)
        if self.end is not None:
            if self.end.tzinfo is None:
                raise NaiveDatetimeError("end", self.end)
            if self.end < self.start:
                raise EndBeforeStartError(self.start, self.end)
        if self.source is Source.MANUAL and self.match_source is not None:
            raise SourceMatchSourceMismatchError(self.source, self.match_source)
        if self.source is Source.AUTO and self.match_source is None:
            raise SourceMatchSourceMismatchError(self.source, self.match_source)

    @property
    def is_running(self) -> bool:
        return self.end is None

    @classmethod
    def from_event(cls, event: EntryEvent, end: datetime | None) -> "Entry":
        if event.is_stop:
            raise ValueError("cannot project a stop event as an Entry")
        return cls(
            id=event.id,
            task_id=cast("UUID", event.task_id),
            subtask_id=event.subtask_id,
            start=event.ts,
            end=end,
            source=cast("Source", event.source),
            match_source=event.match_source,
            matched_keyword=event.matched_keyword,
            calendar_event_id=event.calendar_event_id,
            note=event.note,
        )
