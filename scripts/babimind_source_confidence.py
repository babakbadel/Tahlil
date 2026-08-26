#!/usr/bin/env python3
"""Convert source-health results into confidence and fallback decisions."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEALTH = ROOT / "reports" / "babimind_source_health.json"
OUT_JSON = ROOT / "reports" / "babimind_source_confidence.json"
OUT_MD = ROOT / "reports" / "babimind_source_confidence.md"


def score(r: dict) -> float:
    base = float(r.get("authority_score", 0.75))
    independence = float(r.get("independence_score", 0.75))
    coverage = float(r.get("coverage_score", 0.75))
    reproducibility = float(r.get("reproducibility_score", 0.75))
    reliability = float(r.get("api_reliability_score", 0.75))
    s = 0.20*base + 0.15*independence + 0.15*coverage + 0.15*reproducibility + 0.15*reliability
    status = r.get("status")
    if status == "ok":
        availability = 1.0
    elif status == "unavailable":
        availability = 0.25
    else:
        availability = 0.10
    latency = float(r.get("latency_ms", 0) or 0)
    freshness = 1.0 if latency <= 1000 else 0.9 if latency <= 3000 else 0.75
    return round(max(0.0, min(1.0, s * availability * freshness)), 4)


def tier(conf: float) -> str:
    if conf >= 0.85: return "A"
    if conf >= 0.70: return "B"
    if conf >= 0.50: return "C"
    return "D"


def main() -> None:
    data = json.loads(HEALTH.read_text(encoding="utf-8"))
    rows = []
    for r in data["sources"]:
        c = score(r)
        rows.append({**r, "confidence": c, "tier": tier(c), "eligible_primary": c >= 0.70})
    # Prefer healthy high-confidence sources; fallback is selected by the same topic/type only.
    groups = {}
    for r in rows:
        key = r.get("topic", r.get("type", "unknown"))
        groups.setdefault(key, []).append(r)
    decisions = []
    for key, items in groups.items():
        ranked = sorted(items, key=lambda x: x["confidence"], reverse=True)
        primary = next((x for x in ranked if x["eligible_primary"]), ranked[0] if ranked else None)
        fallbacks = [x["name"] for x in ranked if primary and x["name"] != primary["name"]]
        decisions.append({"group": key, "primary": primary["name"] if primary else None, "fallbacks": fallbacks[:3]})
    payload = {"model":"BabiMind", "source_count":len(rows), "sources":rows, "routing":decisions}
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines=["# BabiMind Source Confidence", "", "Confidence is operational trust, not truth probability.", "", "| Source | Status | Confidence | Tier | Primary Eligible |", "|---|---|---:|---|---|"]
    for r in sorted(rows, key=lambda x:x["confidence"], reverse=True):
        lines.append(f"| {r['name']} | {r['status']} | {r['confidence']:.3f} | {r['tier']} | {'yes' if r['eligible_primary'] else 'no'} |")
    lines += ["", "## Routing", "", "Primary selection uses the highest-confidence healthy source in each topic/type group; lower-confidence sources remain fallbacks."]
    for d in decisions:
        lines.append(f"- **{d['group']}** → primary: `{d['primary']}`; fallback: {', '.join(d['fallbacks']) or '-'}")
    OUT_MD.write_text("\n".join(lines)+"\n", encoding="utf-8")


if __name__ == "__main__": main()
