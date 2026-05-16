# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class OverrideSignals:
    window_keyword: str | None = None


@dataclass(frozen=True, slots=True)
class OverrideContext:
    signals: OverrideSignals


class OverrideStore(Protocol):
    def get(self) -> OverrideContext | None: ...

    def set(self, context: OverrideContext) -> None: ...

    def clear(self) -> None: ...
