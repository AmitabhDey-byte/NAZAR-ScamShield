from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.realtime import broker


router = APIRouter(prefix="/api/realtime", tags=["realtime"])


@router.get("/events")
async def events():
    async def stream():
        yield "retry: 3000\n\n"
        async for message in broker.subscribe():
            if message is None:
                yield ": keepalive\n\n"
            else:
                yield f"event: {message['type']}\ndata: {json.dumps(message, default=str)}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
