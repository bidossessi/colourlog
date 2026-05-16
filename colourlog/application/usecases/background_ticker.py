# SPDX-License-Identifier: GPL-3.0-or-later
import asyncio
import contextlib
from dataclasses import dataclass
from uuid import uuid4

from colourlog.application.ports.activitywatch import ActivityWatchReader
from colourlog.application.ports.clock import Clock
from colourlog.application.ports.event_bus import EventBus
from colourlog.application.ports.override import OverrideContext, OverrideStore
from colourlog.application.ports.repositories import (
    EntryEventRepository,
    ModeRepository,
    TaskRepository,
)
from colourlog.application.usecases.resolve_auto_switch import (
    StartAuto,
    compute_current_signals,
    resolve_auto_switch,
)
from colourlog.domain.entities import EntryEvent
from colourlog.domain.value_objects import Source


@dataclass(frozen=True, slots=True, kw_only=True)
class BackgroundTicker:
    modes: ModeRepository
    tasks: TaskRepository
    events: EntryEventRepository
    aw: ActivityWatchReader
    override_store: OverrideStore
    event_bus: EventBus
    clock: Clock
    poll_interval: float = 3.0

    async def tick_once(self) -> None:
        decision = resolve_auto_switch(
            mode=self.modes.get(),
            latest_event=self.events.latest_event(),
            window=self.aw.latest_window(),
            tasks=self.tasks.list(),
            override=self.override_store.get(),
        )
        if isinstance(decision, StartAuto):
            event = EntryEvent.create(
                id=uuid4(),
                ts=self.clock.now(),
                task_id=decision.task_id,
                source=Source.AUTO,
                match_source=decision.match_source,
                matched_keyword=decision.matched_keyword,
                calendar_event_id=decision.calendar_event_id,
            )
            self.events.append(event)
            await self.event_bus.publish(event)

    async def handle_event(self, event: EntryEvent) -> None:
        if event.is_stop:
            self.override_store.clear()
            return
        if event.source is Source.AUTO:
            self.override_store.clear()
            return
        signals = compute_current_signals(self.aw.latest_window(), self.tasks.list())
        self.override_store.set(OverrideContext(signals=signals))

    async def run(self, stop_event: asyncio.Event) -> None:
        poll_task = asyncio.create_task(self._poll_loop(stop_event))
        subscribe_task = asyncio.create_task(self._subscribe_loop())
        try:
            await stop_event.wait()
        finally:
            poll_task.cancel()
            subscribe_task.cancel()
            await asyncio.gather(poll_task, subscribe_task, return_exceptions=True)

    async def _poll_loop(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            await self.tick_once()
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop_event.wait(), timeout=self.poll_interval)

    async def _subscribe_loop(self) -> None:
        async for event in self.event_bus.subscribe():
            await self.handle_event(event)
