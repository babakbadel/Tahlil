"""FastAPI JSON service for the live equity/options snapshot collector."""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException

from app.data.brsapi.realtime import RealtimeCollector

collector = RealtimeCollector(interval=float(os.getenv("BRS_POLL_SECONDS", "5")))
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


app = FastAPI(title="Tahlil Iran Market Realtime API", version="1.0.0", lifespan=lifespan)


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
