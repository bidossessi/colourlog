# SPDX-License-Identifier: GPL-3.0-or-later
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from colourlog.application.usecases.background_ticker import BackgroundTicker
from colourlog.composition.container import Container
from colourlog.interface.http import dependencies
from colourlog.interface.http.errors import register_exception_handlers
from colourlog.interface.http.routers.clients import router as clients_router
from colourlog.interface.http.routers.entries import router as entries_router
from colourlog.interface.http.routers.events import router as events_router
from colourlog.interface.http.routers.health import router as health_router
from colourlog.interface.http.routers.mode import router as mode_router
from colourlog.interface.http.routers.projects import router as projects_router
from colourlog.interface.http.routers.tasks import router as tasks_router

API_PREFIX = "/api/v1"


def create_app(container: Container) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        ticker = BackgroundTicker(
            modes=container.modes_repo,
            tasks=container.tasks_repo,
            events=container.events_repo,
            aw=container.aw_reader,
            override_store=container.override_store,
            event_bus=container.event_bus,
            clock=container.clock,
            poll_interval=container.poll_interval,
        )
        stop = asyncio.Event()
        run_task = asyncio.create_task(ticker.run(stop))
        try:
            yield
        finally:
            stop.set()
            await run_task

    app = FastAPI(title="colourlog", version="0.1.0", lifespan=lifespan)

    app.dependency_overrides[dependencies.get_clients_repo] = lambda: container.clients_repo
    app.dependency_overrides[dependencies.get_projects_repo] = lambda: container.projects_repo
    app.dependency_overrides[dependencies.get_tasks_repo] = lambda: container.tasks_repo
    app.dependency_overrides[dependencies.get_events_repo] = lambda: container.events_repo
    app.dependency_overrides[dependencies.get_event_bus] = lambda: container.event_bus
    app.dependency_overrides[dependencies.get_modes_repo] = lambda: container.modes_repo
    app.dependency_overrides[dependencies.get_clock] = lambda: container.clock

    app.include_router(health_router)
    app.include_router(clients_router, prefix=API_PREFIX)
    app.include_router(projects_router, prefix=API_PREFIX)
    app.include_router(tasks_router, prefix=API_PREFIX)
    app.include_router(entries_router, prefix=API_PREFIX)
    app.include_router(events_router, prefix=API_PREFIX)
    app.include_router(mode_router, prefix=API_PREFIX)

    register_exception_handlers(app)

    return app
