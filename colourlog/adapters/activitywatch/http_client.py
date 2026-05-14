# SPDX-License-Identifier: GPL-3.0-or-later
import socket
from datetime import datetime
from typing import Any, cast

import httpx
from colourlog.application.ports.activitywatch import (
    AfkSnapshot,
    AfkStatus,
    WindowSnapshot,
)


class AwHttpReader:
    """Reads aw-server-rust REST API for the current window + AFK state."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:5600",
        hostname: str | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._hostname = hostname if hostname is not None else socket.gethostname()
        self._client = httpx.Client(base_url=self._base_url, timeout=timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AwHttpReader":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @property
    def window_bucket(self) -> str:
        return f"aw-watcher-window_{self._hostname}"

    @property
    def afk_bucket(self) -> str:
        return f"aw-watcher-afk_{self._hostname}"

    def _latest_event(self, bucket: str) -> dict[str, Any] | None:
        try:
            response = self._client.get(f"/api/0/buckets/{bucket}/events", params={"limit": 1})
        except httpx.RequestError:
            return None
        if response.status_code != 200:
            return None
        items = cast("list[dict[str, Any]]", response.json())
        if not items:
            return None
        return items[0]

    def latest_window(self) -> WindowSnapshot | None:
        event = self._latest_event(self.window_bucket)
        if event is None:
            return None
        data = event["data"]
        return WindowSnapshot(
            ts=datetime.fromisoformat(event["timestamp"]),
            app=str(data.get("app", "")),
            title=str(data.get("title", "")),
            url=data.get("url"),
        )

    def latest_afk(self) -> AfkSnapshot | None:
        event = self._latest_event(self.afk_bucket)
        if event is None:
            return None
        status_raw = event["data"].get("status", "")
        if status_raw not in ("afk", "not-afk"):
            return None
        return AfkSnapshot(
            ts=datetime.fromisoformat(event["timestamp"]),
            status=cast("AfkStatus", status_raw),
            duration_seconds=float(event.get("duration", 0.0)),
        )
