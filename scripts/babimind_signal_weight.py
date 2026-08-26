#!/usr/bin/env python3
"""Apply source confidence to normalized BabiMind signals.

Input: reports/babimind_source_confidence.json
Output: reports/babimind_signal_weights.json

The score is a reliability weight, not a probability that the underlying claim is true.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "reports" / "babimind_source_confidence.json"
OUT = ROOT / "reports" / "babimind_signal_weights.json"


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    rows = []
    for s in data.get("sources", []):
        c = float(s.get("confidence", 0.0))
        # Keep weak sources visible but prevent them from dominating aggregate signals.
        weight = round(0.25 + 0.75 * c, 4)
        rows.append({
            "source": s.get("name"),
            "topic": s.get("topic", s.get("type")),
            "confidence": c,
            "signal_weight": weight,
            "tier": s.get("tier"),
            "status": s.get("status"),
        })
    OUT.write_text(json.dumps({"model":"BabiMind", "weights":rows, "formula":"0.25 + 0.75*confidence"}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__": main()
