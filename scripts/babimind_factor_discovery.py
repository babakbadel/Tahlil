#!/usr/bin/env python3
"""BabiMind hidden-factor discovery scaffold.

This module deliberately refuses to manufacture observations. It consumes
real observations supplied by project pipelines and emits candidate metadata.
Statistical computation can be enabled when pandas/scipy/statsmodels are
available; missing dependencies or sources degrade gracefully.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "babimind_factor_discovery.yaml"
OUT = ROOT / "artifacts" / "factor_discovery_latest.json"


def load_csv_files() -> list[dict]:
    rows: list[dict] = []
    for path in sorted((ROOT / "data").rglob("*.csv")):
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row["__source_file"] = str(path.relative_to(ROOT))
                    rows.append(row)
        except (OSError, UnicodeError, csv.Error):
            continue
    return rows


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    mx, my = mean(xs), mean(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    den = math.sqrt(sum(v * v for v in dx) * sum(v * v for v in dy))
    return None if den == 0 else sum(a * b for a, b in zip(dx, dy)) / den


def main() -> int:
    rows = load_csv_files()
    result = {
        "schema_version": 1,
        "status": "insufficient_data" if not rows else "candidate_scan_ready",
        "synthetic_data_used": False,
        "observation_count": len(rows),
        "sources": sorted({r["__source_file"] for r in rows}),
        "candidates": [],
        "notes": [
            "Candidate factors require historical aligned series for statistical testing.",
            "No synthetic observations are created by this script.",
            "Promotion requires the gates documented in docs/babimind-factor-discovery.md.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
