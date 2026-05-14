# SPDX-License-Identifier: GPL-3.0-or-later
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from colourlog.interface.http.dependencies import EventBusDep
from colourlog.interface.sse.stream import sse_stream

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
async def events(bus: EventBusDep) -> StreamingResponse:
    return StreamingResponse(sse_stream(bus), media_type="text/event-stream")
