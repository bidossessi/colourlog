# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass

from colourlog.application.ports.repositories import ModeRepository
from colourlog.domain.value_objects import Mode


@dataclass(frozen=True, slots=True)
class GetMode:
    modes: ModeRepository

    def execute(self) -> Mode:
        return self.modes.get()


@dataclass(frozen=True, slots=True)
class SetMode:
    modes: ModeRepository

    def execute(self, *, mode: Mode) -> Mode:
        self.modes.set(mode)
        return mode
