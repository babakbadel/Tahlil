"""Collect a bounded, model-ready FinPy-TSE snapshot for BabiMind.

The collector is fail-soft and time-bounded: an upstream FinPy-TSE/TSETMC
request must never block the Daily Brain indefinitely. Each network call is
run in a worker thread with a configurable timeout. Partial results are still
written so downstream source-health logic can see exactly what failed.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.data.finpy_tse_adapter import (
    get_market_watch,
    get_price_history,
    get_ri_history,
    source_status,
)

OUTPUT = Path(os.getenv("FINPY_TSE_OUTPUT", "data/raw/finpy_tse_snapshot.json"))
SYMBOLS = [
    s.strip()
    for s in os.getenv("FINPY_TSE_SYMBOLS", "فملی,وبملت,شپنا,خساپا").split(",")
    if s.strip()
]
TIMEOUT_SECONDS = max(5, int(os.getenv("FINPY_TSE_REQUEST_TIMEOUT_SECONDS", "30")))


def _call_bounded(label: str, func: Callable[[], Any]) -> tuple[Any, dict[str, Any]]:
    started = time.monotonic()
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="finpy")
    future = executor.submit(func)
    try:
        value = future.result(timeout=TIMEOUT_SECONDS)
        return value, {
            "status": "ok",
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    except FuturesTimeoutError:
        future.cancel()
        return None, {
            "status": "timeout",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "error": f"{label} timed out after {TIMEOUT_SECONDS}s",
        }
    except Exception as exc:
        return None, {
            "status": "error",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        # Do not wait for a stuck network worker. The worker is daemon-like for
        # the purpose of this collector; the main process remains fail-soft.
        executor.shutdown(wait=False, cancel_futures=True)


def main() -> int:
    end = date.today()
    start = end - timedelta(days=int(os.getenv("FINPY_TSE_LOOKBACK_DAYS", "30")))
    payload: dict[str, Any] = {
        "source": "finpy-tse",
        "upstream": "https://github.com/ARahimiQuant/finpy-tse",
        "collected_at": end.isoformat(),
        "status": source_status(),
        "request_timeout_seconds": TIMEOUT_SECONDS,
        "symbols": {},
    }

    for symbol in SYMBOLS:
        item: dict[str, Any] = {"price_history": [], "ri_history": []}
        price, meta = _call_bounded(
            f"{symbol} price history",
            lambda s=symbol: get_price_history(s, start.isoformat(), end.isoformat()),
        )
        item["price_history"] = price or []
        item["price_request"] = meta

        ri, meta = _call_bounded(
            f"{symbol} RI history",
            lambda s=symbol: get_ri_history(s, start.isoformat(), end.isoformat()),
        )
        item["ri_history"] = ri or []
        item["ri_request"] = meta
        payload["symbols"][symbol] = item

    market_watch, meta = _call_bounded("market watch", get_market_watch)
    payload["market_watch"] = market_watch or []
    payload["market_watch_request"] = meta

    failures = []
    for symbol, item in payload["symbols"].items():
        for key in ("price_request", "ri_request"):
            if item[key]["status"] != "ok":
                failures.append({"scope": f"{symbol}.{key}", **item[key]})
    if meta["status"] != "ok":
        failures.append({"scope": "market_watch", **meta})

    payload["collection_status"] = "ok" if not failures else "degraded"
    payload["failures"] = failures

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(
        f"wrote {OUTPUT} | status={payload['collection_status']} "
        f"failures={len(failures)} timeout={TIMEOUT_SECONDS}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
