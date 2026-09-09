#!/usr/bin/env python3
"""CLI entry: daily economic news → app.news.DailyEconomicNewsCollector."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.news.collector import collect_and_persist  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="BabiMind daily economic news collector")
    ap.add_argument("--hours", type=int, default=36, help="compat only")
    args = ap.parse_args()
    _ = args.hours
    result = collect_and_persist(root=ROOT)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
