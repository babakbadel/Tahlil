#!/usr/bin/env python3
"""Expose the Graphify knowledge index without a synthetic market signal.

Code relationships support retrieval. They do not establish economic direction;
market scenarios require dated price observations and explicit provenance.
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
    edges = []
    error = None
    if GRAPH.exists():
        try:
            edges = list(edge_iter(json.loads(GRAPH.read_text(encoding="utf-8"))))
        except (OSError, ValueError) as exc:
            error = type(exc).__name__
    payload = {
        "model": "BabiMind", "component": "Graphify knowledge index", "generated_at": now.isoformat(),
        "graph_available": GRAPH.exists() and error is None, "index_path": "graphify-out/graph.json",
        "index_edge_count": len(edges), "market_signal_eligible": False,
        "graph_score": None, "graph_confidence": None, "graph_regime": "not_applicable_code_index",
        "graph_top_drivers": [], "graph_risk_drivers": [], "edges_used": 0,
        "missing_data_policy": "MISSING_IS_NOT_ZERO", "error": error,
        "instruction": "Use the code graph for retrieval only. Its edges do not establish market direction or probabilities. Economic relationships require dated observations and provenance.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Graphify index: {len(edges)} edges; no synthetic market signal")


if __name__ == "__main__":
    main()
