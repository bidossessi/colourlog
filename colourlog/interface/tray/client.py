# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast
from uuid import UUID

import httpx


class TrayClientError(Exception):
    pass


class DaemonUnreachableError(TrayClientError):
    pass


@dataclass(frozen=True, slots=True)
class TaskSummary:
    id: UUID
    name: str
    archived: bool


@dataclass(frozen=True, slots=True)
class CurrentTaskView:
    task_id: UUID
    task_name: str
    source: str
    started_at: datetime


class TrayClient:
    """Sync HTTP client for the tray to drive daemon CRUD + entry actions."""

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self._base_url, timeout=timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TrayClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def list_tasks(self, *, include_archived: bool = False) -> list[TaskSummary]:
        try:
            response = self._client.get(
                "/api/v1/tasks", params={"include_archived": include_archived}
            )
        except httpx.RequestError as exc:
            raise DaemonUnreachableError(str(exc)) from exc
        response.raise_for_status()
        payload = cast("list[dict[str, Any]]", response.json())
        return [
            TaskSummary(
                id=UUID(item["id"]),
                name=item["name"],
                archived=bool(item["archived"]),
            )
            for item in payload
        ]

    def current_task(self) -> CurrentTaskView | None:
        try:
            response = self._client.get("/api/v1/tasks/current")
        except httpx.RequestError as exc:
            raise DaemonUnreachableError(str(exc)) from exc
        response.raise_for_status()
        body = cast("dict[str, Any] | None", response.json())
        if body is None:
            return None
        entry = body["entry"]
        task = body["task"]
        return CurrentTaskView(
            task_id=UUID(task["id"]),
            task_name=task["name"],
            source=entry["source"],
            started_at=datetime.fromisoformat(entry["start"]),
        )

    def start_entry(
        self, *, task_id: UUID, subtask_id: UUID | None = None, note: str | None = None
    ) -> None:
        body: dict[str, Any] = {"task_id": str(task_id)}
        if subtask_id is not None:
            body["subtask_id"] = str(subtask_id)
        if note is not None:
            body["note"] = note
        try:
            response = self._client.post("/api/v1/entries/start", json=body)
        except httpx.RequestError as exc:
            raise DaemonUnreachableError(str(exc)) from exc
        response.raise_for_status()

    def stop_entry(self) -> None:
        try:
            response = self._client.post("/api/v1/entries/stop")
        except httpx.RequestError as exc:
            raise DaemonUnreachableError(str(exc)) from exc
        response.raise_for_status()
