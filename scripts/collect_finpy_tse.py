"""Collect a fail-safe, model-ready FinPy-TSE snapshot for BabiMind.

Every upstream request runs in an isolated child process. This is deliberate:
FinPy-TSE may block inside third-party/network code where a Python thread
cannot be forcibly stopped. A timed-out child is terminated so the Daily
Brain can always continue with partial data.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import queue
import sys
import time
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
SYMBOLS = [s.strip() for s in os.getenv("FINPY_TSE_SYMBOLS", "فملی,وبملت,شپنا,خساپا").split(",") if s.strip()]
TIMEOUT_SECONDS = max(5, int(os.getenv("FINPY_TSE_REQUEST_TIMEOUT_SECONDS", "20")))


def _worker(func: Callable[[], Any], result_queue: Any) -> None:
    """Run the actual FinPy call in a killable child process."""
    try:
        result_queue.put(("ok", func()))
    except BaseException as exc:  # child must report every failure cleanly
        result_queue.put(("error", f"{type(exc).__name__}: {exc}"))


def _call_bounded(label: str, func: Callable[[], Any]) -> tuple[Any, dict[str, Any]]:
    started = time.monotonic()
    ctx = mp.get_context("fork") if "fork" in mp.get_all_start_methods() else mp.get_context()
    result_queue = ctx.Queue(maxsize=1)
    process = ctx.Process(target=_worker, args=(func, result_queue), name=f"finpy-{label[:40]}")
    process.start()

    try:
        process.join(TIMEOUT_SECONDS)
        if process.is_alive():
            process.terminate()
            process.join(3)
            if process.is_alive() and hasattr(process, "kill"):
                process.kill()
                process.join(2)
            return None, {
                "status": "timeout",
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "error": f"{label} timed out after {TIMEOUT_SECONDS}s; child process terminated",
            }

        try:
            status, value = result_queue.get(timeout=2)
        except queue.Empty:
            return None, {
                "status": "error",
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "error": f"{label} exited without returning a result (exit_code={process.exitcode})",
            }

        if status == "ok":
            return value, {
                "status": "ok",
                "elapsed_seconds": round(time.monotonic() - started, 3),
            }
        return None, {
            "status": "error",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "error": f"{label}: {value}",
        }
    finally:
        try:
            result_queue.close()
            result_queue.join_thread()
        except Exception:
            pass


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
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"wrote {OUTPUT} | status={payload['collection_status']} failures={len(failures)} timeout={TIMEOUT_SECONDS}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
