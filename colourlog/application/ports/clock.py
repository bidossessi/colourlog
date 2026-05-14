# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...
