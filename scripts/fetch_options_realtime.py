"""Collect and write a normalized JSON snapshot for all Iranian option contracts."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.data.brsapi.client import BrsApiClient
from app.data.brsapi.option_fields import normalize_option_row
from app.data.brsapi.options import snapshot_all


def build_payload() -> dict:
    received_at = datetime.now(timezone.utc).isoformat()
    rows = snapshot_all(BrsApiClient())
    normalized = [normalize_option_row(row) | {"raw": row} for row in rows]
    underlyings = sorted({
        row.get("base_l18")
        for row in normalized
        if isinstance(row.get("base_l18"), str) and row.get("base_l18")
    })
    symbols = sorted({
        row.get("l18")
        for row in normalized
        if isinstance(row.get("l18"), str) and row.get("l18")
    })
    return {
        "schema_version": "2.1",
        "market": "IR",
        "asset_class": "option",
        "source": "BRS",
        "event_time": received_at,
        "received_at": received_at,
        "data_quality": {
            "status": "live" if rows else "partial",
            "age_ms": 0,
            "record_count": len(rows),
            "symbol_count": len(symbols),
            "underlying_count": len(underlyings),
            "underlyings": underlyings,
            "symbols": symbols,
            "truth_policy": "missing_fields_are_null",
        },
        "data": normalized,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = build_payload()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    quality = payload["data_quality"]
    count = quality["record_count"]
    symbol_count = quality["symbol_count"]
    underlying_count = quality["underlying_count"]
    print(f"BRS returned {count} option records, {symbol_count} contracts, across {underlying_count} underlyings")
    print("Underlyings:", ", ".join(quality["underlyings"]))
    print(f"Wrote {args.output} with {count} option records")

    if not rows_have_multiple_underlyings(quality):
        raise RuntimeError(
            "Options feed appears incomplete: fewer than 2 distinct underlyings were returned. "
            "Refusing to publish a ZMLI-only/single-underlying snapshot."
        )


def rows_have_multiple_underlyings(quality: dict) -> bool:
    return quality.get("underlying_count", 0) >= 2


if __name__ == "__main__":
    main()
