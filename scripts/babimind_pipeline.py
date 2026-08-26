#!/usr/bin/env python3
"""Unified BabiMind source -> signal pipeline.

Stages:
source health -> schema/content checks -> freshness -> confidence -> fallback
-> signal weight -> optional cluster scoring.

This pipeline intentionally treats source confidence as operational trust,
not truth probability.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "babimind_source_health.json"
OUT = ROOT / "reports" / "babimind_pipeline.json"


def endpoint_check(url: str, timeout: int = 15) -> dict:
    started = time.monotonic()
    try:
        req = Request(url, headers={"User-Agent": "BabiMind-Pipeline/1.0"})
        with urlopen(req, timeout=timeout) as response:
            body = response.read(8192)
            status = getattr(response, "status", 200)
            ctype = response.headers.get("Content-Type", "")
        return {"status": "ok" if 200 <= status < 400 else "error", "http_status": status,
                "content_type": ctype, "bytes": len(body),
                "latency_ms": round((time.monotonic()-started)*1000, 1),
                "content_check": "nonempty" if body else "empty"}
    except HTTPError as e:
        return {"status":"error", "http_status":e.code, "error":str(e), "content_check":"failed"}
    except (URLError, TimeoutError, OSError) as e:
        return {"status":"unavailable", "error":str(e), "content_check":"failed"}


def freshness(source: dict, now: datetime) -> float:
    """Freshness based on declared release/observation timestamp when present.
    If absent, return neutral rather than pretending latency means freshness.
    """
    stamp = source.get("release_timestamp") or source.get("observation_timestamp")
    if not stamp:
        return 0.75
    try:
        dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        age_days = max(0.0, (now - dt).total_seconds()/86400)
        half_life = float(source.get("freshness_half_life_days", 7))
        return round(2 ** (-age_days / max(half_life, 0.1)), 4)
    except (ValueError, TypeError):
        return 0.5


def confidence(source: dict, availability: float, fresh: float) -> float:
    authority = float(source.get("authority_score", 0.75))
    independence = float(source.get("independence_score", 0.75))
    coverage = float(source.get("coverage_score", 0.75))
    reproducibility = float(source.get("reproducibility_score", 0.75))
    reliability = float(source.get("api_reliability_score", 0.75))
    revision = 1.0 - float(source.get("revision_risk", 0.10))
    # Weights sum to 1.0 before availability/freshness adjustments.
    structural = (0.20*authority + 0.15*independence + 0.15*coverage +
                  0.15*reproducibility + 0.15*reliability + 0.20*revision)
    return round(max(0.0, min(1.0, structural * availability * fresh)), 4)


def main() -> None:
    catalog = json.loads(CONFIG.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    rows = []
    for src in catalog.get("sources", []):
        result = endpoint_check(src["url"], int(src.get("timeout_seconds", 15)))
        availability = 1.0 if result.get("status") == "ok" and result.get("content_check") == "nonempty" else 0.25 if result.get("status") == "unavailable" else 0.10
        fresh = freshness(src, now)
        conf = confidence(src, availability, fresh)
        weight = round(0.25 + 0.75*conf, 4)
        rows.append({**src, **result, "freshness":fresh, "confidence":conf,
                     "signal_weight":weight, "primary_eligible":conf >= 0.70,
                     "checked_at":now.isoformat()})

    groups = {}
    for r in rows:
        key = r.get("topic", r.get("type", "unknown"))
        groups.setdefault(key, []).append(r)
    routing=[]
    for key, items in groups.items():
        ranked=sorted(items, key=lambda x:x["confidence"], reverse=True)
        primary=next((x for x in ranked if x["primary_eligible"]), ranked[0] if ranked else None)
        routing.append({"group":key, "primary":primary["name"] if primary else None,
                        "fallbacks":[x["name"] for x in ranked if primary and x["name"] != primary["name"]][:3]})

    payload={"model":"BabiMind", "pipeline_version":"1.0", "generated_at":now.isoformat(),
             "stages":["health","content","freshness","confidence","fallback","signal_weight"],
             "sources":rows, "routing":routing}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"BabiMind pipeline: {len(rows)} sources, {len(routing)} routing groups")

if __name__ == "__main__": main()
