"""Polling collector and normalized snapshots for Iran equity/options data."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from .client import BrsApiClient, BrsApiError
from .stream import RealtimeHub


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rows(payload: Any) -> list[dict[str, Any]]:
    rows = payload.get("data", payload.get("result", payload)) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise TypeError(f"Unexpected BRS response shape: {type(rows).__name__}")
    return [r for r in rows if isinstance(r, dict)]


def _is_option(row: dict[str, Any]) -> bool:
    return bool(row.get("base_l18") or row.get("underlying") or row.get("underlying_symbol"))


def normalize(rows: list[dict[str, Any]], source: str = "BRS_API") -> dict[str, Any]:
    received = _now()
    equities = [r for r in rows if not _is_option(r)]
    options = [r for r in rows if _is_option(r)]
    return {
        "schema_version": "1.0",
        "market": "IR",
        "source": source,
        "event_time": received,
        "received_at": received,
        "sequence": None,
        "data_quality": {
            "status": "live" if rows else "partial",
            "age_ms": 0,
            "record_count": len(rows),
        },
        "data": {
            "equities": equities,
            "options": options,
            "equity_count": len(equities),
            "option_count": len(options),
        },
    }


class RealtimeCollector:
    """Poll the upstream snapshot endpoint and publish normalized events."""

    def __init__(self, client: BrsApiClient | None = None, interval: float = 5.0, hub: RealtimeHub | None = None) -> None:
        self.client = client or BrsApiClient()
        self.interval = max(1.0, interval)
        self.hub = hub
        self.latest: dict[str, Any] | None = None
        self.last_error: str | None = None
        self._running = False

    def collect_once(self) -> dict[str, Any]:
        try:
            raw = self.client.get_all_symbols(security_type=1)
            snapshot = normalize(_rows(raw))
            self.latest = snapshot
            self.last_error = None
            if self.hub is not None:
                self.hub.publish(snapshot)
            return snapshot
        except Exception as exc:
            self.last_error = type(exc).__name__
            if self.latest is not None:
                self.latest["data_quality"]["status"] = "stale"
            raise

    async def run_forever(self) -> None:
        self._running = True
        while self._running:
            started = time.monotonic()
            try:
                self.collect_once()
            except (BrsApiError, TypeError, ValueError):
                pass
            await asyncio.sleep(max(0.0, self.interval - (time.monotonic() - started)))

    def stop(self) -> None:
        self._running = False
