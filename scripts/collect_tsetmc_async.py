"""Collect direct TSETMC MarketWatch data using 5j9/tsetmc."""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path


OUT = Path(os.getenv("TSETMC_ASYNC_OUT", "data/raw/tsetmc_async_snapshot.json"))


def rows(df):
    if df is None:
        return []
    return df.collect().to_dicts() if hasattr(df, "collect") else df.to_dicts()


async def collect():
    from tsetmc.market_watch import get_market_watch, client_type_all, closing_price_all

    results = await asyncio.gather(
        asyncio.wait_for(get_market_watch(with_best_limits=True, show_traded=True), timeout=45),
        asyncio.wait_for(client_type_all(), timeout=45),
        asyncio.wait_for(closing_price_all(), timeout=45),
        return_exceptions=True,
    )
    errors = {name: type(value).__name__ for name, value in zip(('market_watch', 'client_type_all', 'closing_price_all'), results) if isinstance(value, Exception)}
    market, clients, closing = [None if isinstance(value, Exception) else value for value in results]
    market_rows = rows(market)
    return {
        "source": "5j9/tsetmc",
        "package": "tsetmc",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok" if market_rows else "error",
        "errors": errors,
        "market_watch": market_rows,
        "client_type_all": rows(clients),
        "closing_price_all": rows(closing),
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = asyncio.run(collect())
    except Exception as exc:
        payload = {
            "source": "5j9/tsetmc",
            "package": "tsetmc",
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"[TSETMC-ASYNC] {payload['status']}")
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
