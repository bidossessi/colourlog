# SPDX-License-Identifier: GPL-3.0-or-later
from colourlog.application.ports.override import OverrideContext


class InMemoryOverrideStore:
    def __init__(self) -> None:
        self._current: OverrideContext | None = None

    def get(self) -> OverrideContext | None:
        return self._current

    def set(self, context: OverrideContext) -> None:
        self._current = context

    def clear(self) -> None:
        self._current = None
