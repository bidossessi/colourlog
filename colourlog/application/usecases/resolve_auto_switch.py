# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
from uuid import UUID

from colourlog.application.ports.activitywatch import WindowSnapshot
from colourlog.application.ports.override import OverrideContext, OverrideSignals
from colourlog.domain.entities import EntryEvent, Task
from colourlog.domain.value_objects import MatchSource, Mode


@dataclass(frozen=True, slots=True)
class NoOp:
    pass


@dataclass(frozen=True, slots=True)
class StartAuto:
    task_id: UUID
    match_source: MatchSource
    matched_keyword: str | None = None
    calendar_event_id: str | None = None


@dataclass(frozen=True, slots=True)
class Stop:
    pass


Decision = NoOp | StartAuto | Stop


def _haystack(window: WindowSnapshot) -> str:
    parts = [window.app, window.title]
    if window.url is not None:
        parts.append(window.url)
    return " ".join(parts).lower()


def _match_window(window: WindowSnapshot, tasks: list[Task]) -> tuple[Task, str] | None:
    """First task (by created_at ASC) whose keyword is a substring of the window haystack."""
    haystack = _haystack(window)
    candidates = sorted(
        (t for t in tasks if not t.archived and t.keywords),
        key=lambda t: t.created_at,
    )
    for task in candidates:
        for keyword in task.keywords:
            if keyword in haystack:
                return task, keyword
    return None


def resolve_auto_switch(
    *,
    mode: Mode,
    latest_event: EntryEvent | None,
    window: WindowSnapshot | None,
    tasks: list[Task],
    override: OverrideContext | None = None,
) -> Decision:
    if mode is not Mode.AUTO:
        return NoOp()
    match = _match_window(window, tasks) if window is not None else None
    current_signals = OverrideSignals(window_keyword=match[1] if match else None)
    if override is not None and current_signals == override.signals:
        return NoOp()
    if match is None:
        return NoOp()
    task, keyword = match
    if latest_event is not None and latest_event.is_start and latest_event.task_id == task.id:
        return NoOp()
    return StartAuto(
        task_id=task.id,
        match_source=MatchSource.WINDOW,
        matched_keyword=keyword,
    )
