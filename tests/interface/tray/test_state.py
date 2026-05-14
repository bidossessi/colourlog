# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime
from uuid import uuid4

from colourlog.interface.tray.client import CurrentTaskView
from colourlog.interface.tray.state import IconState, render


def _current(name: str = "T41622", source: str = "manual") -> CurrentTaskView:
    return CurrentTaskView(
        task_id=uuid4(),
        task_name=name,
        source=source,
        started_at=datetime(2026, 5, 14, 10, 0, tzinfo=UTC),
    )


class TestRender:
    def test_offline(self):
        view = render(None, daemon_online=False)
        assert view.icon is IconState.OFFLINE
        assert view.label == "—: daemon offline"

    def test_idle(self):
        view = render(None, daemon_online=True)
        assert view.icon is IconState.IDLE
        assert view.label == "—: idle"

    def test_running_manual(self):
        view = render(_current(), daemon_online=True)
        assert view.icon is IconState.RUNNING
        assert view.label == "M: T41622"
        assert view.icon_name == "colourlog-running"

    def test_running_auto(self):
        view = render(_current(source="auto"), daemon_online=True)
        assert view.label == "A: T41622"

    def test_unknown_source_uses_question_mark(self):
        view = render(_current(source="weird"), daemon_online=True)
        assert view.label.startswith("?:")

    def test_truncates_long_task_name(self):
        view = render(
            _current(name="VERY-LONG-TASK-NAME-EXCEEDS-LIMIT"),
            daemon_online=True,
        )
        body = view.label.split(": ", 1)[1]
        assert len(body) <= 16
        assert body.endswith("…")

    def test_short_name_not_truncated(self):
        view = render(_current(name="T41622"), daemon_online=True)
        assert view.label.endswith("T41622")
