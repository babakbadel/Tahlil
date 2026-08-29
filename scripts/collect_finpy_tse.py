"""Collect a small, model-ready FinPy-TSE snapshot for BabiMind.

The collector is intentionally fail-soft: upstream outages should not block
other market-data sources in the unified pipeline.
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path

from app.data.finpy_tse_adapter import get_market_watch, get_price_history, get_ri_history, source_status

OUTPUT = Path(os.getenv("FINPY_TSE_OUTPUT", "data/raw/finpy_tse_snapshot.json"))
SYMBOLS = [s.strip() for s in os.getenv("FINPY_TSE_SYMBOLS", "فملی,وبملت,شپنا,خساپا").split(",") if s.strip()]


def main() -> int:
    end = date.today()
    start = end - timedelta(days=int(os.getenv("FINPY_TSE_LOOKBACK_DAYS", "30")))
    payload = {
        "source": "finpy-tse",
        "upstream": "https://github.com/ARahimiQuant/finpy-tse",
        "collected_at": end.isoformat(),
        "status": source_status(),
        "symbols": {},
    }

    for symbol in SYMBOLS:
        item = {"price_history": [], "ri_history": []}
        try:
            item["price_history"] = get_price_history(symbol, start.isoformat(), end.isoformat())
        except Exception as exc:
            item["price_error"] = str(exc)
        try:
            item["ri_history"] = get_ri_history(symbol, start.isoformat(), end.isoformat())
        except Exception as exc:
            item["ri_error"] = str(exc)
        payload["symbols"][symbol] = item

    try:
        payload["market_watch"] = get_market_watch()
    except Exception as exc:
        payload["market_watch_error"] = str(exc)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
