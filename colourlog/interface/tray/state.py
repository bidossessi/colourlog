# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
from enum import StrEnum

from colourlog.interface.tray.client import CurrentTaskView


class IconState(StrEnum):
    RUNNING = "running"
    PAUSED = "paused"
    IDLE = "idle"
    OFFLINE = "offline"


_ICON_NAMES: dict[IconState, str] = {
    IconState.RUNNING: "media-playback-start",
    IconState.PAUSED: "media-playback-pause",
    IconState.IDLE: "media-playback-stop",
    IconState.OFFLINE: "network-offline",
}

_SOURCE_PREFIX: dict[str, str] = {
    "manual": "M",
    "auto": "A",  # placeholder until match_source-aware refinement
}

_LABEL_MAX_NAME_CHARS = 16


@dataclass(frozen=True, slots=True)
class TrayView:
    icon: IconState
    icon_name: str
    label: str


def _truncate(name: str) -> str:
    if len(name) <= _LABEL_MAX_NAME_CHARS:
        return name
    return name[: _LABEL_MAX_NAME_CHARS - 1] + "…"


def render(current: CurrentTaskView | None, *, daemon_online: bool) -> TrayView:
    if not daemon_online:
        return TrayView(
            icon=IconState.OFFLINE,
            icon_name=_ICON_NAMES[IconState.OFFLINE],
            label="—: daemon offline",
        )
    if current is None:
        return TrayView(
            icon=IconState.IDLE,
            icon_name=_ICON_NAMES[IconState.IDLE],
            label="—: idle",
        )
    prefix = _SOURCE_PREFIX.get(current.source, "?")
    return TrayView(
        icon=IconState.RUNNING,
        icon_name=_ICON_NAMES[IconState.RUNNING],
        label=f"{prefix}: {_truncate(current.task_name)}",
    )
