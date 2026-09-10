"""Fallback TSETMC market collector using mshojaei77/pytsetmc-api."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(os.getenv("PYTSETMC_OUT", "data/raw/pytsetmc_market_snapshot.json"))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        from pytsetmc_api import TSETMCClient

        client = TSETMCClient(
            timeout=int(os.getenv("PYTSETMC_TIMEOUT", "20")),
            max_retries=int(os.getenv("PYTSETMC_RETRIES", "2")),
            enable_logging=False,
        )
        market, order_book = client.get_market_watch()
        payload = {
            "source": "mshojaei77/pytsetmc-api",
            "package": "pytsetmc-api",
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "ok" if market is not None and not market.empty else "empty",
            "market_watch": market.to_dict(orient="records") if market is not None else [],
            "order_book": order_book.to_dict(orient="records") if order_book is not None else [],
        }
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"[PYTSETMC] {payload['status']} market={len(payload['market_watch'])} order_book={len(payload['order_book'])}")
        return 0 if payload["status"] == "ok" else 1
    except Exception as exc:
        payload = {
            "source": "mshojaei77/pytsetmc-api",
            "package": "pytsetmc-api",
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[PYTSETMC] error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
