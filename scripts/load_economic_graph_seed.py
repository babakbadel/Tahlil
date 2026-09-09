#!/usr/bin/env python3
"""Load config/economic_graph_seed.json into EconomicGraphStore."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "config" / "economic_graph_seed.json"
STORE_ROOT = ROOT / "data" / "economic_graph"


def main() -> None:
    from app.economic_graph import EconomicEdge, EconomicGraphStore, EconomicNode

    data = json.loads(SEED.read_text(encoding="utf-8"))
    as_of = datetime.now(timezone.utc).isoformat()
    store = EconomicGraphStore(STORE_ROOT)
    n = e = 0
    for row in data.get("nodes", []):
        store.upsert_node(
            EconomicNode(
                node_id=row["node_id"],
                type=row.get("type", "factor"),
                name=row.get("name", row["node_id"]),
                confidence=float(row.get("confidence", 0.5)),
                freshness=1.0,
                state="active",
                as_of=as_of,
                source="seed",
            )
        )
        n += 1
    for row in data.get("edges", []):
        store.upsert_edge(
            EconomicEdge(
                edge_id=row["edge_id"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                relation=row.get("relation", "influences"),
                direction=row.get("direction", "mixed"),
                weight=float(row.get("weight", 0.5)),
                confidence=float(row.get("confidence", 0.5)),
                lag_days=row.get("lag_days"),
                independence_factor=float(row.get("independence_factor", 1.0)),
                state="active",
                as_of=as_of,
            )
        )
        e += 1
    snap = store.snapshot(as_of=as_of, persist=True)
    femli = store.score_target(as_of=as_of, target_id="femli", snapshot=snap)
    market = store.score_target(as_of=as_of, target_id="market_index", snapshot=snap)
    out = {
        "loaded_nodes": n,
        "loaded_edges": e,
        "store": store.summary(),
        "femli": femli.as_dict(),
        "market_index": market.as_dict(),
    }
    report = ROOT / "reports" / "economic_graph_seed_load.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
