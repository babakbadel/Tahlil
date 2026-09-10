"""Collect TSETMC market/options data through algotik-tse.

This is an independent provider path. It never fabricates data and writes a
provider envelope so BabiMind can compare it with other collectors.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import algotik_tse as att

OUT = Path(os.getenv("ALGOTIK_TSE_OUT", "data/raw/algotik_tse_snapshot.json"))
UNDERLYINGS = [x.strip() for x in os.getenv("OPTION_UNDERLYINGS", "فملی,ذوب,وبملت,شپنا,خساپا,فولاد,فغدیر,سرچشمه").split(",") if x.strip()]
FETCH_OI = os.getenv("ALGOTIK_FETCH_OI", "true").lower() == "true"


def frame_rows(df):
    if df is None:
        return []
    return json.loads(df.to_json(orient="records", force_ascii=False, date_format="iso"))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "source": "mohsenalipour/algotik_tse",
        "package": "algotik-tse",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "error",
        "underlyings": {},
    }
    try:
        market = att.get_market_snapshot()
        envelope["market_snapshot"] = {
            "market_time": market.get("market_time"),
            "index_value": market.get("index_value"),
            "stocks_rows": len(market.get("stocks", [])),
            "stocks": frame_rows(market.get("stocks")),
        }
        for underlying in UNDERLYINGS:
            try:
                chain = att.get_options_chain(underlying, fetch_oi=FETCH_OI, progress=False)
                envelope["underlyings"][underlying] = {
                    "status": "ok",
                    "underlying_name": chain.get("underlying_name"),
                    "underlying_price": chain.get("underlying_price"),
                    "expiry_dates": chain.get("expiry_dates", []),
                    "market_time": chain.get("market_time"),
                    "calls": frame_rows(chain.get("calls")),
                    "puts": frame_rows(chain.get("puts")),
                }
            except Exception as exc:
                envelope["underlyings"][underlying] = {
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
        ok = sum(v.get("status") == "ok" for v in envelope["underlyings"].values())
        envelope["successful_underlyings"] = ok
        envelope["status"] = "ok" if ok else "error"
    except Exception as exc:
        envelope["error"] = f"{type(exc).__name__}: {exc}"
    OUT.write_text(json.dumps(envelope, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"[ALGOTIK-TSE] {envelope['status']} successful_underlyings={envelope.get('successful_underlyings', 0)}")
    return 0 if envelope["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
