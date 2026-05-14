# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime

from colourlog.adapters.clock.system import SystemClock


def test_system_clock_returns_utc_aware_now_within_bounds():
    before = datetime.now(UTC)
    got = SystemClock().now()
    after = datetime.now(UTC)
    assert got.tzinfo is UTC
    assert before <= got <= after
