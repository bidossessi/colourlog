# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from colourlog.application.ports.activitywatch import WindowSnapshot
from colourlog.application.usecases.resolve_auto_switch import (
    NoOp,
    OverrideContext,
    OverrideSignals,
    StartAuto,
    resolve_auto_switch,
)
from colourlog.domain.entities import EntryEvent, Task
from colourlog.domain.value_objects import MatchSource, Mode, Source


def _ts(offset_min: int = 0) -> datetime:
    return datetime(2026, 5, 14, 10, 0, tzinfo=UTC) + timedelta(minutes=offset_min)


def _task(
    name: str,
    keywords: list[str] | None = None,
    archived: bool = False,
    created_offset: int = 0,
) -> Task:
    project_id = uuid4()
    return Task.create(
        id=uuid4(),
        name=name,
        project_id=project_id,
        created_at=_ts(created_offset),
        keywords=keywords,
        archived=archived,
    )


def _window(app: str = "Chrome", title: str = "", url: str | None = None) -> WindowSnapshot:
    return WindowSnapshot(ts=_ts(), app=app, title=title, url=url)


def _start_event(task_id: UUID) -> EntryEvent:
    return EntryEvent.create(id=uuid4(), ts=_ts(), task_id=task_id, source=Source.MANUAL)


class TestModeGating:
    def test_manual_mode_returns_noop_even_with_match(self):
        t = _task("T41622", keywords=["t41622"])
        w = _window(title="T41622 - Chrome")
        decision = resolve_auto_switch(mode=Mode.MANUAL, latest_event=None, window=w, tasks=[t])
        assert isinstance(decision, NoOp)


class TestWindowMatching:
    def test_match_starts_auto(self):
        t = _task("T41622", keywords=["t41622"])
        w = _window(app="Code", title="T41622 - main.py")
        decision = resolve_auto_switch(mode=Mode.AUTO, latest_event=None, window=w, tasks=[t])
        assert isinstance(decision, StartAuto)
        assert decision.task_id == t.id
        assert decision.match_source is MatchSource.WINDOW
        assert decision.matched_keyword == "t41622"

    def test_no_window_returns_noop(self):
        t = _task("T41622", keywords=["t41622"])
        decision = resolve_auto_switch(mode=Mode.AUTO, latest_event=None, window=None, tasks=[t])
        assert isinstance(decision, NoOp)

    def test_no_match_returns_noop(self):
        t = _task("T41622", keywords=["t41622"])
        w = _window(title="random other window")
        decision = resolve_auto_switch(mode=Mode.AUTO, latest_event=None, window=w, tasks=[t])
        assert isinstance(decision, NoOp)

    def test_case_insensitive_match(self):
        t = _task("T41622", keywords=["t41622"])
        w = _window(title="T41622 - main.py")  # uppercase in haystack, lowercase keyword
        decision = resolve_auto_switch(mode=Mode.AUTO, latest_event=None, window=w, tasks=[t])
        assert isinstance(decision, StartAuto)

    def test_url_considered_in_haystack(self):
        t = _task("D12345", keywords=["d12345"])
        w = _window(
            app="Chrome",
            title="Phabricator",
            url="https://example.com/D12345",
        )
        decision = resolve_auto_switch(mode=Mode.AUTO, latest_event=None, window=w, tasks=[t])
        assert isinstance(decision, StartAuto)
        assert decision.task_id == t.id

    def test_archived_task_skipped(self):
        t = _task("T41622", keywords=["t41622"], archived=True)
        w = _window(title="T41622 - main.py")
        decision = resolve_auto_switch(mode=Mode.AUTO, latest_event=None, window=w, tasks=[t])
        assert isinstance(decision, NoOp)

    def test_empty_keywords_skipped(self):
        # explicit empty list → task not auto-switchable per plan
        t = _task("T41622", keywords=[])
        w = _window(title="T41622 - main.py")
        decision = resolve_auto_switch(mode=Mode.AUTO, latest_event=None, window=w, tasks=[t])
        assert isinstance(decision, NoOp)


class TestTiebreak:
    def test_first_by_created_at(self):
        # both tasks would match; older one wins
        older = _task("T1", keywords=["foo"], created_offset=0)
        newer = _task("T2", keywords=["foo"], created_offset=5)
        w = _window(title="foo bar")
        decision = resolve_auto_switch(
            mode=Mode.AUTO,
            latest_event=None,
            window=w,
            tasks=[newer, older],  # order doesn't matter
        )
        assert isinstance(decision, StartAuto)
        assert decision.task_id == older.id


class TestAlreadyOnTask:
    def test_no_op_when_already_running_matched_task(self):
        t = _task("T41622", keywords=["t41622"])
        latest = _start_event(t.id)
        w = _window(title="T41622 - main.py")
        decision = resolve_auto_switch(mode=Mode.AUTO, latest_event=latest, window=w, tasks=[t])
        assert isinstance(decision, NoOp)

    def test_switch_when_running_different_task(self):
        t1 = _task("T1", keywords=["t1"], created_offset=0)
        t2 = _task("T2", keywords=["t2"], created_offset=5)
        latest = _start_event(t1.id)
        w = _window(title="working on t2 now")
        decision = resolve_auto_switch(
            mode=Mode.AUTO, latest_event=latest, window=w, tasks=[t1, t2]
        )
        assert isinstance(decision, StartAuto)
        assert decision.task_id == t2.id

    def test_start_when_latest_is_stop(self):
        t = _task("T41622", keywords=["t41622"])
        stop_event = EntryEvent.create(id=uuid4(), ts=_ts())  # task_id=None
        w = _window(title="T41622 - main.py")
        decision = resolve_auto_switch(mode=Mode.AUTO, latest_event=stop_event, window=w, tasks=[t])
        assert isinstance(decision, StartAuto)


class TestOverrideStickiness:
    def test_override_no_op_when_window_keyword_unchanged(self):
        t = _task("T1", keywords=["t1"])
        w = _window(title="working on t1")
        override = OverrideContext(signals=OverrideSignals(window_keyword="t1"))
        decision = resolve_auto_switch(
            mode=Mode.AUTO, latest_event=None, window=w, tasks=[t], override=override
        )
        assert isinstance(decision, NoOp)

    def test_override_releases_when_window_keyword_changes(self):
        t1 = _task("T1", keywords=["t1"], created_offset=0)
        t2 = _task("T2", keywords=["t2"], created_offset=5)
        w = _window(title="now on t2")
        override = OverrideContext(signals=OverrideSignals(window_keyword="t1"))
        decision = resolve_auto_switch(
            mode=Mode.AUTO,
            latest_event=None,
            window=w,
            tasks=[t1, t2],
            override=override,
        )
        assert isinstance(decision, StartAuto)
        assert decision.task_id == t2.id
        assert decision.matched_keyword == "t2"

    def test_override_no_op_when_blank_held_and_window_has_no_match(self):
        t = _task("T1", keywords=["t1"])
        w = _window(title="something unrelated")
        override = OverrideContext(signals=OverrideSignals(window_keyword=None))
        decision = resolve_auto_switch(
            mode=Mode.AUTO, latest_event=None, window=w, tasks=[t], override=override
        )
        assert isinstance(decision, NoOp)

    def test_override_releases_when_blank_held_but_window_now_matches(self):
        t = _task("T1", keywords=["t1"])
        w = _window(title="working on t1 now")
        override = OverrideContext(signals=OverrideSignals(window_keyword=None))
        decision = resolve_auto_switch(
            mode=Mode.AUTO, latest_event=None, window=w, tasks=[t], override=override
        )
        assert isinstance(decision, StartAuto)
        assert decision.task_id == t.id

    def test_manual_mode_ignores_override(self):
        t = _task("T1", keywords=["t1"])
        w = _window(title="working on t1")
        override = OverrideContext(signals=OverrideSignals(window_keyword="t1"))
        decision = resolve_auto_switch(
            mode=Mode.MANUAL,
            latest_event=None,
            window=w,
            tasks=[t],
            override=override,
        )
        assert isinstance(decision, NoOp)

    def test_override_release_still_respects_already_on_task(self):
        t = _task("T1", keywords=["t1"])
        w = _window(title="t1 window")
        latest = _start_event(t.id)
        override = OverrideContext(signals=OverrideSignals(window_keyword=None))
        decision = resolve_auto_switch(
            mode=Mode.AUTO,
            latest_event=latest,
            window=w,
            tasks=[t],
            override=override,
        )
        assert isinstance(decision, NoOp)
