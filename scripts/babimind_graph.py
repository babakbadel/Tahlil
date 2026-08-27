#!/usr/bin/env python3
"""Turn Graphify's generated graph into an auditable BabiMind feature.

The adapter is deliberately schema-tolerant because Graphify output can evolve.
Missing data is never converted to a negative signal. Inferred/ambiguous edges
are discounted and repeated/correlated paths are penalized.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "graphify-out" / "graph.json"
OUT = ROOT / "reports" / "babimind_graph.json"

TARGETS = {"FMLI", "فملی", "وبملت", "شپنا", "خساپا", "USD", "دلار", "GOLD", "طلا", "MARKET", "بورس"}


def clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def num(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def edge_iter(data: Any):
    if isinstance(data, dict):
        for key in ("edges", "relationships", "links"):
            value = data.get(key)
            if isinstance(value, list):
                yield from value
        graph = data.get("graph")
        if graph is not None:
            yield from edge_iter(graph)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item


def endpoint(edge: dict, side: str) -> str:
    keys = ("source", "from", "src") if side == "source" else ("target", "to", "dst")
    for k in keys:
        if edge.get(k) is not None:
            value = edge[k]
            if isinstance(value, dict):
                return str(value.get("id") or value.get("name") or value.get("label") or "")
            return str(value)
    return ""


def status_factor(edge: dict) -> float:
    status = str(edge.get("status") or edge.get("relationship_status") or "EXTRACTED").upper()
    return {"EXTRACTED": 1.0, "INFERRED": 0.70, "AMBIGUOUS": 0.35}.get(status, 0.60)


def main() -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "model": "BabiMind",
        "component": "Graph Intelligence",
        "generated_at": now.isoformat(),
        "graph_available": GRAPH.exists(),
        "graph_snapshot_id": now.strftime("%Y%m%dT%H%M%SZ"),
        "graph_score": 0.0,
        "graph_confidence": 0.0,
        "graph_regime": "unavailable",
        "graph_top_drivers": [],
        "graph_risk_drivers": [],
        "edges_used": 0,
        "correlation_penalty": 0.0,
        "missing_data_policy": "MISSING_IS_NOT_ZERO",
    }
    if not GRAPH.exists():
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Graphify output unavailable; Graph contribution skipped")
        return

    data = json.loads(GRAPH.read_text(encoding="utf-8"))
    edges = list(edge_iter(data))
    scored = []
    for e in edges:
        src, dst = endpoint(e, "source"), endpoint(e, "target")
        text = f"{src} {dst}".lower()
        if not any(t.lower() in text for t in TARGETS):
            continue
        direction = num(e.get("direction"), 1.0)
        weight = clamp(num(e.get("weight"), num(e.get("strength"), 0.5)), 0.0, 1.0)
        conf = clamp(num(e.get("confidence"), 0.75), 0.0, 1.0)
        freshness = clamp(num(e.get("freshness"), 1.0), 0.0, 1.0)
        value = direction * weight * conf * freshness * status_factor(e)
        scored.append((value, src, dst, e))

    # Conservative aggregation: duplicate source/target pairs are counted once
    # and repeated sources receive diminishing marginal contribution.
    seen_pairs: set[tuple[str, str]] = set()
    source_count: dict[str, int] = {}
    values = []
    for value, src, dst, e in sorted(scored, key=lambda x: abs(x[0]), reverse=True):
        pair = (src.lower(), dst.lower())
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        n = source_count.get(src.lower(), 0)
        adjusted = value * (0.70 ** n)
        source_count[src.lower()] = n + 1
        values.append((adjusted, src, dst, e))

    raw = sum(v[0] for v in values)
    denom = max(1.0, sum(abs(v[0]) for v in values))
    score = clamp(raw / denom if values else 0.0)
    confidence = sum(num(v[3].get("confidence"), 0.75) for v in values) / len(values) if values else 0.0
    top = sorted(values, key=lambda x: x[0], reverse=True)[:8]
    risk = sorted(values, key=lambda x: x[0])[:8]

    payload.update({
        "graph_score": round(score, 4),
        "graph_confidence": round(confidence, 4),
        "graph_regime": "bullish" if score >= 0.20 else "bearish" if score <= -0.20 else "neutral",
        "graph_top_drivers": [{"source": s, "target": d, "contribution": round(v, 4)} for v, s, d, _ in top],
        "graph_risk_drivers": [{"source": s, "target": d, "contribution": round(v, 4)} for v, s, d, _ in risk],
        "edges_used": len(values),
        "correlation_penalty": round(max(0.0, 1.0 - sum(abs(v[0]) for v in values) / max(1.0, sum(abs(v[0]) for v in scored))), 4) if scored else 0.0,
    })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Graph Intelligence: {len(values)} edges used, score={score:.4f}, confidence={confidence:.4f}")


if __name__ == "__main__":
    main()
