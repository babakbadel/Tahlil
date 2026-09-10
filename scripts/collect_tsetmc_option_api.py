"""Collect the full TSETMC option market from the endpoint used by TSETMC_OPTION.

This provider is intentionally independent of the Flask wrapper in
amirkazem/TSETMC_OPTION: we use its underlying public TSETMC API directly,
which avoids starting a second web server in CI while preserving the source
and schema lineage.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

OUT = Path(os.getenv("TSETMC_OPTION_API_OUT", "data/raw/tsetmc_option_api_snapshot.json"))
TIMEOUT = max(5, int(os.getenv("TSETMC_OPTION_API_TIMEOUT", "20")))
URLS = {
    "bourse": "https://cdn.tsetmc.com/api/Instrument/GetInstrumentOptionMarketWatch/1",
    "farabourse": "https://cdn.tsetmc.com/api/Instrument/GetInstrumentOptionMarketWatch/2",
}


def fetch(url: str):
    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 BabiMind/Tahlil"},
        timeout=(5, TIMEOUT),
    )
    r.raise_for_status()
    body = r.json()
    return body.get("instrumentOptMarketWatch", [])


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "source": "amirkazem/TSETMC_OPTION -> TSETMC GetInstrumentOptionMarketWatch",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "error",
        "markets": {},
    }
    total = 0
    try:
        for market, url in URLS.items():
            try:
                data = fetch(url)
                df = pd.DataFrame(data)
                records = json.loads(df.to_json(orient="records", force_ascii=False))
                envelope["markets"][market] = {
                    "status": "ok",
                    "url": url,
                    "rows": len(records),
                    "data": records,
                }
                total += len(records)
            except Exception as exc:
                envelope["markets"][market] = {
                    "status": "error",
                    "url": url,
                    "error": f"{type(exc).__name__}: {exc}",
                }
        envelope["total_rows"] = total
        envelope["status"] = "ok" if total else "error"
    except Exception as exc:
        envelope["error"] = f"{type(exc).__name__}: {exc}"
    OUT.write_text(json.dumps(envelope, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"[TSETMC-OPTION-API] {envelope['status']} total_rows={total}")
    return 0 if envelope["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
