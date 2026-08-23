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

    # Use canonical normalized field names here. The previous version
    # incorrectly looked for raw BRS keys (base_l18/l18) inside the normalized
    # records, which produced 0 contracts and 0 underlyings despite receiving
    # 1,144 valid option rows.
    underlyings = sorted({
        row.get("underlying")
        for row in normalized
        if isinstance(row.get("underlying"), str) and row.get("underlying")
    })
    symbols = sorted({
        row.get("symbol")
        for row in normalized
        if isinstance(row.get("symbol"), str) and row.get("symbol")
    })

    return {
        "schema_version": "2.2",
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

    print(
        f"BRS returned {count} option records, "
        f"{symbol_count} contracts, across {underlying_count} underlyings"
    )
    print("Underlyings:", ", ".join(quality["underlyings"]))
    print(f"Wrote {args.output} with {count} option records")

    if underlying_count < 2:
        raise RuntimeError(
            "Options feed appears incomplete: fewer than 2 distinct underlyings "
            "were returned. Refusing to publish a ZMLI-only/single-underlying snapshot."
        )


if __name__ == "__main__":
    main()
