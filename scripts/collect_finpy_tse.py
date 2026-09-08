"""Collect a fail-safe, model-ready FinPy-TSE snapshot for BabiMind.

Important: FinPy-TSE calls run in killable child processes. We MUST read the
result queue while the child is running; joining first can deadlock when a
large pandas result fills multiprocessing.Queue's pipe buffer.
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
QUEUE_GRACE_SECONDS = 2


def _worker(func: Callable[[], Any], result_queue: Any) -> None:
    """Run the actual FinPy call in a killable child process."""
    try:
        result_queue.put(("ok", func()))
    except BaseException as exc:
        try:
            result_queue.put(("error", f"{type(exc).__name__}: {exc}"))
        except Exception:
            pass


def _call_bounded(label: str, func: Callable[[], Any]) -> tuple[Any, dict[str, Any]]:
    """Execute one upstream call with a hard wall-clock timeout.

    Do not call process.join() before reading Queue: a large serialized result
    can block the child in Queue.put(), which otherwise makes join hang forever.
    """
    started = time.monotonic()
    ctx = mp.get_context("fork") if "fork" in mp.get_all_start_methods() else mp.get_context()
    result_queue = ctx.Queue(maxsize=1)
    process = ctx.Process(target=_worker, args=(func, result_queue), name=f"finpy-{label[:40]}")
    process.daemon = True
    process.start()
    print(f"[FINPY] START {label}", flush=True)

    result: tuple[str, Any] | None = None
    deadline = started + TIMEOUT_SECONDS
    try:
        while time.monotonic() < deadline:
            try:
                result = result_queue.get(timeout=min(0.5, max(0.05, deadline - time.monotonic())))
                break
            except queue.Empty:
                if not process.is_alive():
                    break

        if result is None and process.is_alive():
            process.terminate()
            process.join(1)
            if process.is_alive() and hasattr(process, "kill"):
                process.kill()
                process.join(1)
            elapsed = round(time.monotonic() - started, 3)
            print(f"[FINPY] TIMEOUT {label} after {elapsed}s", flush=True)
            return None, {
                "status": "timeout",
                "elapsed_seconds": elapsed,
                "error": f"{label} timed out after {TIMEOUT_SECONDS}s; child process terminated",
            }

        # Child exited but may still be flushing the Queue feeder thread.
        if result is None:
            try:
                result = result_queue.get(timeout=QUEUE_GRACE_SECONDS)
            except queue.Empty:
                elapsed = round(time.monotonic() - started, 3)
                print(f"[FINPY] ERROR {label}: no result (exit={process.exitcode})", flush=True)
                return None, {
                    "status": "error",
                    "elapsed_seconds": elapsed,
                    "error": f"{label} exited without returning a result (exit_code={process.exitcode})",
                }

        status, value = result
        elapsed = round(time.monotonic() - started, 3)
        process.join(1)
        if status == "ok":
            print(f"[FINPY] OK {label} in {elapsed}s", flush=True)
            return value, {"status": "ok", "elapsed_seconds": elapsed}

        print(f"[FINPY] ERROR {label}: {value}", flush=True)
        return None, {"status": "error", "elapsed_seconds": elapsed, "error": f"{label}: {value}"}
    finally:
        if process.is_alive():
            process.terminate()
            process.join(1)
        try:
            result_queue.cancel_join_thread()
            result_queue.close()
        except Exception:
            pass


def main() -> int:
    end = date.today()
    lookback = max(1, int(os.getenv("FINPY_TSE_LOOKBACK_DAYS", "30")))
    start = end - timedelta(days=lookback)
    print(f"[FINPY] BEGIN symbols={','.join(SYMBOLS)} lookback={lookback}d timeout={TIMEOUT_SECONDS}s", flush=True)

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
    print(f"[FINPY] WROTE {OUTPUT} | status={payload['collection_status']} failures={len(failures)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
