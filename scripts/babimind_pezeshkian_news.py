#!/usr/bin/env python3
"""CLI entry: Pezeshkian news → app.news.PezeshkianNewsCollector."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.news.pezeshkian import collect_pezeshkian_and_persist  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=36)
    args = ap.parse_args()
    result = collect_pezeshkian_and_persist(root=ROOT, hours=args.hours)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
