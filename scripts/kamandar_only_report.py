#!/usr/bin/env python3
"""Independent Kamandar-only daily intelligence layer.

Collects Kamandar evidence without feeding or depending on the BabiMind pipeline.
The output is an auditable manifest plus the six market-section snapshots and
the market-report/services snapshots.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
FILES = [
    "kamandar_market_report.json",
    "kamandar_indices.json",
    "kamandar_stocks.json",
    "kamandar_funds.json",
    "kamandar_options.json",
    "kamandar_baskets.json",
    "kamandar_options_top_put.json",
    "kamandar_services_crawl.json",
]

def main():
    now = datetime.now(timezone.utc).isoformat()
    sections = []
    for name in FILES:
        p = RAW / name
        item = {"file": str(p.relative_to(ROOT)), "exists": p.exists()}
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                item.update({
                    "status": data.get("status"),
                    "source": data.get("source", "kamandar"),
                    "section": data.get("section"),
                    "collected_at": data.get("collected_at"),
                    "pages_fetched": data.get("crawl", {}).get("pages_fetched"),
                    "errors_count": data.get("crawl", {}).get("errors_count"),
                    "records": len(data.get("records", [])) if isinstance(data.get("records"), list) else None,
                })
            except Exception as exc:
                item["parse_error"] = repr(exc)
        sections.append(item)

    payload = {
        "layer": "KAMANDAR_ONLY",
        "source": "kamandar",
        "generated_at": now,
        "independent_from_babimind": True,
        "evidence_files": sections,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "kamandar_only_manifest.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
