"""In-process fan-out hub for WebSocket and Server-Sent Events clients."""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator


class RealtimeHub:
    """Broadcast immutable-ish snapshots to connected clients with bounded queues."""

    def __init__(self, max_queue: int = 2) -> None:
        self.max_queue = max(1, max_queue)
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.max_queue)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    def publish(self, snapshot: dict[str, Any]) -> None:
        """Schedule non-blocking delivery; slow clients never block market polling."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        loop.create_task(self._fanout(snapshot))

    async def _fanout(self, snapshot: dict[str, Any]) -> None:
        async with self._lock:
            subscribers = tuple(self._subscribers)
        for queue in subscribers:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(snapshot)
            except asyncio.QueueFull:
                pass

    async def events(self, initial: dict[str, Any] | None = None) -> AsyncIterator[dict[str, Any]]:
        queue = await self.subscribe()
        try:
            if initial is not None:
                yield initial
            while True:
                yield await queue.get()
        finally:
            await self.unsubscribe(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
