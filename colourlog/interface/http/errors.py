# SPDX-License-Identifier: GPL-3.0-or-later
from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from colourlog.application.exceptions import EntityNotFoundError
from colourlog.domain.exceptions import InvalidNameError


async def _entity_not_found(_: Request, exc: Exception) -> JSONResponse:
    e = cast("EntityNotFoundError", exc)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": f"{e.entity_type.__name__.lower()}_not_found",
                "message": str(e),
                "details": {"id": str(e.entity_id)},
            }
        },
    )


async def _invalid_name(_: Request, exc: Exception) -> JSONResponse:
    e = cast("InvalidNameError", exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "invalid_name",
                "message": str(e),
                "details": {"value": e.value},
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(EntityNotFoundError, _entity_not_found)
    app.add_exception_handler(InvalidNameError, _invalid_name)
