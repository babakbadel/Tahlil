#!/usr/bin/env python3
"""Unified BabiMind source -> signal pipeline with Graph Intelligence.

Source checks are concurrent so one slow/unavailable endpoint cannot stall the
entire pipeline for many minutes.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "babimind_source_health.json"
OUT = ROOT / "reports" / "babimind_pipeline.json"
GRAPH_OUT = ROOT / "reports" / "babimind_graph.json"
MAX_WORKERS = 12
DEFAULT_TIMEOUT = 8


def endpoint_check(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    started = time.monotonic()
    try:
        req = Request(url, headers={"User-Agent": "BabiMind-Pipeline/1.3"})
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
    structural = (0.20*authority + 0.15*independence + 0.15*coverage +
                  0.15*reproducibility + 0.15*reliability + 0.20*revision)
    return round(max(0.0, min(1.0, structural * availability * fresh)), 4)


def operational_state(result: dict, fresh: float) -> str:
    status = result.get("status")
    if status == "unavailable": return "unavailable"
    if status == "error": return "error"
    if result.get("content_check") != "nonempty": return "partial"
    if fresh < 0.25: return "stale"
    return "available"


def load_graph() -> dict:
    if not GRAPH_OUT.exists():
        return {"available": False, "graph_score": None, "graph_confidence": 0.0,
                "graph_regime": "unavailable", "reason": "graph_score_not_generated"}
    try:
        return json.loads(GRAPH_OUT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"available": False, "graph_score": None, "graph_confidence": 0.0,
                "graph_regime": "error", "reason": str(exc)}


def check_source(src: dict) -> dict:
    timeout = min(max(int(src.get("timeout_seconds", DEFAULT_TIMEOUT)), 2), DEFAULT_TIMEOUT)
    result = endpoint_check(src["url"], timeout)
    now = datetime.now(timezone.utc)
    fresh = freshness(src, now)
    state = operational_state(result, fresh)
    availability = 1.0 if state == "available" else 0.0
    conf = confidence(src, availability, fresh)
    weight = 0.0 if state in {"unavailable", "error", "partial"} else round(0.25 + 0.75*conf, 4)
    return {**src, **result, "state":state, "freshness":fresh,
            "confidence":conf, "signal_weight":weight,
            "eligible_for_aggregation":weight > 0.0,
            "retry_next_run":state != "available", "checked_at":now.isoformat()}


def main() -> None:
    started = time.monotonic()
    catalog = json.loads(CONFIG.read_text(encoding="utf-8"))
    sources = catalog.get("sources", [])
    rows = [None] * len(sources)

    # Concurrent health checks: 68 sources now take roughly the slowest batch,
    # rather than 68 * timeout_seconds when endpoints are unavailable.
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, max(1, len(sources)))) as pool:
        futures = {pool.submit(check_source, src): i for i, src in enumerate(sources)}
        for future in as_completed(futures):
            i = futures[future]
            try:
                rows[i] = future.result()
            except Exception as exc:
                src = sources[i]
                rows[i] = {**src, "state":"error", "confidence":0.0,
                           "signal_weight":0.0, "eligible_for_aggregation":False,
                           "retry_next_run":True, "error":repr(exc),
                           "checked_at":datetime.now(timezone.utc).isoformat()}

    groups = {}
    for r in rows:
        key = r.get("topic", r.get("type", "unknown"))
        groups.setdefault(key, []).append(r)
    routing=[]
    for key, items in groups.items():
        ranked=sorted(items, key=lambda x:(x["signal_weight"], x["confidence"]), reverse=True)
        primary=next((x for x in ranked if x["eligible_for_aggregation"]), None)
        routing.append({"group":key, "primary":primary["name"] if primary else None,
                        "fallbacks":[x["name"] for x in ranked if not primary or x["name"] != primary["name"]][:3]})

    active = sum(r["eligible_for_aggregation"] for r in rows)
    unavailable = sum(r["state"] == "unavailable" for r in rows)
    graph = load_graph()
    elapsed = round(time.monotonic() - started, 2)
    payload={"model":"BabiMind", "pipeline_version":"1.3", "generated_at":datetime.now(timezone.utc).isoformat(),
             "stages":["health","content","freshness","confidence","fallback","signal_weight","graph_intelligence"],
             "missing_data_policy":"SKIP_CURRENT_RUN_AND_RETRY_NEXT_RUN",
             "execution":{"max_workers":MAX_WORKERS,"default_timeout_seconds":DEFAULT_TIMEOUT,"elapsed_seconds":elapsed},
             "summary":{"total_sources":len(rows),"active_sources":active,"unavailable_sources":unavailable},
             "graph_intelligence":graph, "sources":rows, "routing":routing}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"BabiMind pipeline: {len(rows)} sources, {active} active, {unavailable} unavailable; graph={graph.get('graph_regime')}; elapsed={elapsed}s")

if __name__ == "__main__": main()
