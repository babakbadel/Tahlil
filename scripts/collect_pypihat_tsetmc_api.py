"""TSETMC market collector using the pypiHat/tsetmc-api implementation."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(os.getenv("PYPIHAT_TSETMC_OUT", "data/raw/pypihat_tsetmc_snapshot.json"))


def _safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    if hasattr(value, "to_dict"):
        try:
            return _safe(value.to_dict())
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        try:
            return {str(k): _safe(v) for k, v in vars(value).items() if not str(k).startswith("_")}
        except Exception:
            pass
    return str(value)


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    collected_at = datetime.now(timezone.utc).isoformat()
    try:
        from tsetmc_api.market_watch import MarketWatch

        market = MarketWatch()
        price = _safe(market.get_price_data())
        stats = _safe(market.get_stats_data())
        traders = _safe(market.get_traders_type_data())
        history = _safe(market.get_daily_history_data())

        row_count = 0
        for value in (price, stats, traders):
            if isinstance(value, (list, dict)):
                row_count = max(row_count, len(value))

        payload = {
            "source": "pypiHat/tsetmc-api",
            "package": "tsetmc-api",
            "collected_at_utc": collected_at,
            "status": "ok" if row_count else "empty",
            "row_count": row_count,
            "price_data": price,
            "stats_data": stats,
            "traders_type_data": traders,
            "daily_history_data": history,
        }
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"[PYPIHAT-TSETMC] {payload['status']} rows={row_count}")
        return 0 if row_count else 1
    except Exception as exc:
        payload = {
            "source": "pypiHat/tsetmc-api",
            "package": "tsetmc-api",
            "collected_at_utc": collected_at,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[PYPIHAT-TSETMC] error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

# Workflow trigger test: 2026-09-10
