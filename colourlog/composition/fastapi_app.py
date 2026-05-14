# SPDX-License-Identifier: GPL-3.0-or-later
from fastapi import FastAPI

from colourlog.composition.container import Container
from colourlog.interface.http import dependencies
from colourlog.interface.http.errors import register_exception_handlers
from colourlog.interface.http.routers.clients import router as clients_router
from colourlog.interface.http.routers.entries import router as entries_router
from colourlog.interface.http.routers.health import router as health_router
from colourlog.interface.http.routers.projects import router as projects_router
from colourlog.interface.http.routers.tasks import router as tasks_router

API_PREFIX = "/api/v1"


def create_app(container: Container) -> FastAPI:
    app = FastAPI(title="colourlog", version="0.1.0")

    app.dependency_overrides[dependencies.get_clients_repo] = lambda: container.clients_repo
    app.dependency_overrides[dependencies.get_projects_repo] = lambda: container.projects_repo
    app.dependency_overrides[dependencies.get_tasks_repo] = lambda: container.tasks_repo
    app.dependency_overrides[dependencies.get_events_repo] = lambda: container.events_repo
    app.dependency_overrides[dependencies.get_clock] = lambda: container.clock

    app.include_router(health_router)
    app.include_router(clients_router, prefix=API_PREFIX)
    app.include_router(projects_router, prefix=API_PREFIX)
    app.include_router(tasks_router, prefix=API_PREFIX)
    app.include_router(entries_router, prefix=API_PREFIX)

    register_exception_handlers(app)

    return app
