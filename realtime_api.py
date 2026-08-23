"""FastAPI JSON + WebSocket + SSE service for Iran equity/options snapshots."""
from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.data.brsapi.realtime import RealtimeCollector
from app.data.brsapi.stream import RealtimeHub

hub = RealtimeHub(max_queue=int(os.getenv("BRS_STREAM_QUEUE", "2")))
collector = RealtimeCollector(interval=float(os.getenv("BRS_POLL_SECONDS", "5")), hub=hub)
_task: asyncio.Task[Any] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _task
    _task = asyncio.create_task(collector.run_forever())
    try:
        yield
    finally:
        collector.stop()
        if _task:
            _task.cancel()
            try:
                await _task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="Tahlil Iran Market Realtime API", version="1.1.0", lifespan=lifespan)


def snapshot() -> dict[str, Any]:
    if collector.latest is None:
        try:
            return collector.collect_once()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="market feed unavailable") from exc
    return collector.latest


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok" if collector.latest else "starting",
        "source": "BRS_API",
        "last_error": collector.last_error,
        "stream_subscribers": hub.subscriber_count,
    }


@app.get("/api/v1/equity/market")
def equity_market() -> dict[str, Any]:
    s = snapshot()
    return {**s, "asset_class": "equity", "data": s["data"]["equities"]}


@app.get("/api/v1/equity/symbol/{symbol}")
def equity_symbol(symbol: str) -> dict[str, Any]:
    s = snapshot()
    rows = [r for r in s["data"]["equities"] if r.get("l18") == symbol]
    if not rows:
        raise HTTPException(status_code=404, detail="symbol not found")
    return {**s, "asset_class": "equity", "data": rows[0]}


@app.get("/api/v1/options/market")
def options_market() -> dict[str, Any]:
    s = snapshot()
    return {**s, "asset_class": "option", "data": s["data"]["options"]}


@app.get("/api/v1/options/chain/{underlying}")
def option_chain(underlying: str) -> dict[str, Any]:
    s = snapshot()
    rows = [
        r for r in s["data"]["options"]
        if r.get("base_l18") == underlying
        or r.get("underlying") == underlying
        or r.get("underlying_symbol") == underlying
    ]
    return {**s, "asset_class": "option", "data": rows}


@app.get("/api/v1/market/realtime")
def realtime() -> dict[str, Any]:
    return snapshot()


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = await hub.subscribe()
    try:
        if collector.latest is not None:
            await websocket.send_json(collector.latest)
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        await hub.unsubscribe(queue)


async def _sse_events() -> AsyncIterator[bytes]:
    queue = await hub.subscribe()
    try:
        if collector.latest is not None:
            yield f"data: {json.dumps(collector.latest, ensure_ascii=False)}\n\n".encode()
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=20.0)
                payload = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
                yield f"event: market\ndata: {payload}\n\n".encode()
            except asyncio.TimeoutError:
                yield b": heartbeat\n\n"
    finally:
        await hub.unsubscribe(queue)


@app.get("/api/v1/stream/market")
async def sse_market() -> StreamingResponse:
    return StreamingResponse(
        _sse_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
