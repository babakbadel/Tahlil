"""Print a normalized JSON snapshot for ZMLI option contracts.

Usage:
    BRS_API_KEY=... python scripts/fetch_zmli_realtime.py

No credential is printed or persisted by this script.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from app.data.brsapi.client import BrsApiClient
from app.data.brsapi.option_fields import normalize_option_row
from app.data.brsapi.options import snapshot


def main() -> None:
    received_at = datetime.now(timezone.utc).isoformat()
    rows = snapshot(BrsApiClient(), targets=None)
    normalized = [normalize_option_row(row) | {"raw": row} for row in rows]
    payload = {
        "schema_version": "1.2",
        "market": "IR",
        "asset_class": "option",
        "source": "BRS",
        "event_time": received_at,
        "received_at": received_at,
        "data_quality": {
            "status": "live" if rows else "partial",
            "age_ms": 0,
            "record_count": len(rows),
            "truth_policy": "missing_fields_are_null",
        },
        "data": normalized,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
