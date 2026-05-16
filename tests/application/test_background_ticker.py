# SPDX-License-Identifier: GPL-3.0-or-later
import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from colourlog.adapters.event_bus.in_memory import InMemoryEventBus
from colourlog.adapters.override.in_memory import InMemoryOverrideStore
from colourlog.application.ports.activitywatch import WindowSnapshot
from colourlog.application.ports.override import OverrideContext, OverrideSignals
from colourlog.application.usecases.background_ticker import BackgroundTicker
from colourlog.domain.entities import EntryEvent, Task
from colourlog.domain.value_objects import MatchSource, Mode, Source

from tests.application.fakes import (
    AdvancingClock,
    InMemoryActivityWatchReader,
    InMemoryEntryEventRepository,
    InMemoryModeRepository,
    InMemoryTaskRepository,
)


def _ts(offset_min: int = 0) -> datetime:
    return datetime(2026, 5, 14, 10, 0, tzinfo=UTC) + timedelta(minutes=offset_min)


def _task(name: str, keywords: list[str] | None = None) -> Task:
    return Task.create(
        id=uuid4(),
        name=name,
        project_id=uuid4(),
        created_at=_ts(),
        keywords=keywords,
    )


def _window(title: str = "") -> WindowSnapshot:
    return WindowSnapshot(ts=_ts(), app="App", title=title, url=None)


def _build_ticker(
    *,
    mode: Mode = Mode.AUTO,
    tasks: list[Task] | None = None,
    window: WindowSnapshot | None = None,
    override: OverrideContext | None = None,
    poll_interval: float = 3.0,
) -> tuple[BackgroundTicker, dict[str, Any]]:
    modes = InMemoryModeRepository(initial=mode)
    tasks_repo = InMemoryTaskRepository()
    for t in tasks or []:
        tasks_repo.add(t)
    events_repo = InMemoryEntryEventRepository()
    aw = InMemoryActivityWatchReader(window=window)
    override_store = InMemoryOverrideStore()
    if override is not None:
        override_store.set(override)
    event_bus = InMemoryEventBus()
    clock = AdvancingClock(_ts(), step_seconds=1)
    ticker = BackgroundTicker(
        modes=modes,
        tasks=tasks_repo,
        events=events_repo,
        aw=aw,
        override_store=override_store,
        event_bus=event_bus,
        clock=clock,
        poll_interval=poll_interval,
    )
    deps: dict[str, Any] = {
        "events": events_repo,
        "override": override_store,
        "bus": event_bus,
    }
    return ticker, deps


class TestTickOnce:
    @pytest.mark.asyncio
    async def test_manual_mode_writes_nothing(self):
        t = _task("T1", keywords=["t1"])
        ticker, deps = _build_ticker(mode=Mode.MANUAL, tasks=[t], window=_window("t1 thing"))
        await ticker.tick_once()
        assert deps["events"].latest_event() is None

    @pytest.mark.asyncio
    async def test_no_window_writes_nothing(self):
        t = _task("T1", keywords=["t1"])
        ticker, deps = _build_ticker(tasks=[t], window=None)
        await ticker.tick_once()
        assert deps["events"].latest_event() is None

    @pytest.mark.asyncio
    async def test_auto_match_writes_auto_event(self):
        t = _task("T1", keywords=["t1"])
        ticker, deps = _build_ticker(tasks=[t], window=_window("t1 thing"))
        await ticker.tick_once()
        latest = deps["events"].latest_event()
        assert latest is not None
        assert latest.task_id == t.id
        assert latest.source is Source.AUTO
        assert latest.match_source is MatchSource.WINDOW
        assert latest.matched_keyword == "t1"

    @pytest.mark.asyncio
    async def test_auto_match_publishes_to_bus(self):
        t = _task("T1", keywords=["t1"])
        ticker, deps = _build_ticker(tasks=[t], window=_window("t1 thing"))
        received: list[EntryEvent] = []

        async def consume() -> None:
            async for ev in deps["bus"].subscribe():
                received.append(ev)
                return

        consumer = asyncio.create_task(consume())
        await asyncio.sleep(0.01)
        await ticker.tick_once()
        await asyncio.wait_for(consumer, timeout=1.0)
        assert len(received) == 1
        assert received[0].task_id == t.id

    @pytest.mark.asyncio
    async def test_sticky_override_blocks_write(self):
        t = _task("T1", keywords=["t1"])
        override = OverrideContext(signals=OverrideSignals(window_keyword="t1"))
        ticker, deps = _build_ticker(tasks=[t], window=_window("t1 window"), override=override)
        await ticker.tick_once()
        assert deps["events"].latest_event() is None

    @pytest.mark.asyncio
    async def test_stale_override_lets_write(self):
        t1 = _task("T1", keywords=["t1"])
        t2 = _task("T2", keywords=["t2"])
        override = OverrideContext(signals=OverrideSignals(window_keyword="t1"))
        ticker, deps = _build_ticker(tasks=[t1, t2], window=_window("t2 thing"), override=override)
        await ticker.tick_once()
        latest = deps["events"].latest_event()
        assert latest is not None
        assert latest.task_id == t2.id


class TestHandleEvent:
    @pytest.mark.asyncio
    async def test_manual_start_with_window_match_captures_keyword(self):
        t = _task("T1", keywords=["t1"])
        ticker, deps = _build_ticker(tasks=[t], window=_window("t1 here"))
        event = EntryEvent.create(id=uuid4(), ts=_ts(), task_id=t.id, source=Source.MANUAL)
        await ticker.handle_event(event)
        stored = deps["override"].get()
        assert stored is not None
        assert stored.signals.window_keyword == "t1"

    @pytest.mark.asyncio
    async def test_manual_start_with_no_window_match_captures_blank(self):
        t = _task("T1", keywords=["t1"])
        ticker, deps = _build_ticker(tasks=[t], window=_window("unrelated"))
        event = EntryEvent.create(id=uuid4(), ts=_ts(), task_id=t.id, source=Source.MANUAL)
        await ticker.handle_event(event)
        stored = deps["override"].get()
        assert stored is not None
        assert stored.signals.window_keyword is None

    @pytest.mark.asyncio
    async def test_manual_start_with_no_window_at_all_captures_blank(self):
        t = _task("T1", keywords=["t1"])
        ticker, deps = _build_ticker(tasks=[t], window=None)
        event = EntryEvent.create(id=uuid4(), ts=_ts(), task_id=t.id, source=Source.MANUAL)
        await ticker.handle_event(event)
        stored = deps["override"].get()
        assert stored is not None
        assert stored.signals.window_keyword is None

    @pytest.mark.asyncio
    async def test_auto_start_clears_override(self):
        t = _task("T1", keywords=["t1"])
        existing = OverrideContext(signals=OverrideSignals(window_keyword="t41875"))
        ticker, deps = _build_ticker(tasks=[t], window=_window("t1 here"), override=existing)
        event = EntryEvent.create(
            id=uuid4(),
            ts=_ts(),
            task_id=t.id,
            source=Source.AUTO,
            match_source=MatchSource.WINDOW,
            matched_keyword="t1",
        )
        await ticker.handle_event(event)
        assert deps["override"].get() is None

    @pytest.mark.asyncio
    async def test_stop_event_clears_override(self):
        t = _task("T1", keywords=["t1"])
        existing = OverrideContext(signals=OverrideSignals(window_keyword="t41875"))
        ticker, deps = _build_ticker(tasks=[t], override=existing)
        event = EntryEvent.create(id=uuid4(), ts=_ts())
        await ticker.handle_event(event)
        assert deps["override"].get() is None


class TestRun:
    @pytest.mark.asyncio
    async def test_poll_loop_writes_events(self):
        t = _task("T1", keywords=["t1"])
        ticker, deps = _build_ticker(tasks=[t], window=_window("t1 thing"), poll_interval=0.01)
        stop = asyncio.Event()
        run_task = asyncio.create_task(ticker.run(stop))
        await asyncio.sleep(0.05)
        stop.set()
        await asyncio.wait_for(run_task, timeout=1.0)
        assert deps["events"].latest_event() is not None

    @pytest.mark.asyncio
    async def test_subscribe_loop_captures_override(self):
        t = _task("T1", keywords=["t1"])
        ticker, deps = _build_ticker(tasks=[t], window=_window("t1 here"), poll_interval=10.0)
        stop = asyncio.Event()
        run_task = asyncio.create_task(ticker.run(stop))
        await asyncio.sleep(0.05)
        manual = EntryEvent.create(id=uuid4(), ts=_ts(), task_id=t.id, source=Source.MANUAL)
        await deps["bus"].publish(manual)
        await asyncio.sleep(0.05)
        stop.set()
        await asyncio.wait_for(run_task, timeout=1.0)
        stored = deps["override"].get()
        assert stored is not None
        assert stored.signals.window_keyword == "t1"
