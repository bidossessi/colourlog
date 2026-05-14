# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)
