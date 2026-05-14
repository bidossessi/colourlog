# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol


@dataclass(frozen=True, slots=True)
class WindowSnapshot:
    ts: datetime
    app: str
    title: str
    url: str | None = None


AfkStatus = Literal["afk", "not-afk"]


@dataclass(frozen=True, slots=True)
class AfkSnapshot:
    ts: datetime
    status: AfkStatus
    duration_seconds: float


class ActivityWatchReader(Protocol):
    def latest_window(self) -> WindowSnapshot | None: ...

    def latest_afk(self) -> AfkSnapshot | None: ...
