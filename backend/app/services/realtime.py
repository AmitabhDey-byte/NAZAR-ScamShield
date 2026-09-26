from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone


class RealtimeBroker:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict]] = set()

    async def publish(self, event_type: str, payload: dict) -> None:
        message = {
            "type": event_type,
            "payload": payload,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
        for queue in tuple(self._subscribers):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(message)

    async def subscribe(self) -> AsyncIterator[dict | None]:
        queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        try:
            while True:
                try:
                    yield await asyncio.wait_for(queue.get(), timeout=15)
                except TimeoutError:
                    yield None
        finally:
            self._subscribers.discard(queue)


broker = RealtimeBroker()
