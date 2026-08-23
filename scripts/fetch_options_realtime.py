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
    return {
        "schema_version": "2.0",
        "market": "IR",
        "asset_class": "option",
        "source": "BRS",
        "event_time": received_at,
        "received_at": received_at,
        "data_quality": {
            "status": "live" if rows else "partial",
            "age_ms": 0,
            "record_count": len(rows),
            "underlying_count": len(underlyings),
            "underlyings": underlyings,
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
    count = payload["data_quality"]["record_count"]
    underlying_count = payload["data_quality"]["underlying_count"]
    print(f"BRS returned {count} option records across {underlying_count} underlyings")
    print(f"Wrote {args.output} with {count} option records")


if __name__ == "__main__":
    main()
