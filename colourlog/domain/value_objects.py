# SPDX-License-Identifier: GPL-3.0-or-later
from enum import StrEnum


class Source(StrEnum):
    MANUAL = "manual"
    AUTO = "auto"


class MatchSource(StrEnum):
    WINDOW = "window"
    CALENDAR = "calendar"
    AFK_RESUME = "afk_resume"
