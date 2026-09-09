"""EconomicGraphStore — append-oriented, as_of-queryable economic knowledge graph.

Storage layout (default under data/economic_graph/):
  nodes.jsonl      append-only node observations / structural defs
  edges.jsonl      append-only edge claims (new line supersedes by edge_id+as_of)
  evidence.jsonl   append-only evidence records
  snapshots/       optional materialised snapshot JSON files

Rules:
- Never overwrite a historical line in place.
- snapshot(as_of) only sees nodes/edges valid at that information set.
- Missing value on a node is not a zero signal.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    EconomicEdge,
    EconomicNode,
    GraphEvidence,
    GraphScoreResult,
    GraphSnapshot,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


class EconomicGraphStore:
    def __init__(self, root: str | Path = "data/economic_graph") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.nodes_path = self.root / "nodes.jsonl"
        self.edges_path = self.root / "edges.jsonl"
        self.evidence_path = self.root / "evidence.jsonl"
        self.snapshots_dir = self.root / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        for p in (self.nodes_path, self.edges_path, self.evidence_path):
            if not p.exists():
                p.touch()

        self._nodes: list[EconomicNode] = []
        self._edges: list[EconomicEdge] = []
        self._evidence: dict[str, GraphEvidence] = {}
        self._loaded = False

    def _append_jsonl(self, path: Path, row: dict) -> None:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _read_jsonl(self, path: Path) -> list[dict]:
        rows: list[dict] = []
        if not path.exists() or path.stat().st_size == 0:
            return rows
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    def load(self) -> None:
        self._nodes = [EconomicNode(**r) for r in self._read_jsonl(self.nodes_path)]
        self._edges = [EconomicEdge(**r) for r in self._read_jsonl(self.edges_path)]
        self._evidence = {
            r["evidence_id"]: GraphEvidence(**r)
            for r in self._read_jsonl(self.evidence_path)
            if "evidence_id" in r
        }
        self._loaded = True

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def add_evidence(self, evidence: GraphEvidence, persist: bool = True) -> None:
        self.ensure_loaded()
        self._evidence[evidence.evidence_id] = evidence
        if persist:
            self._append_jsonl(self.evidence_path, evidence.as_dict())

    def upsert_node(self, node: EconomicNode, persist: bool = True) -> None:
        self.ensure_loaded()
        if not node.timestamp:
            node.timestamp = _now()
        self._nodes.append(node)
        if persist:
            self._append_jsonl(self.nodes_path, node.as_dict())

    def upsert_edge(self, edge: EconomicEdge, persist: bool = True) -> None:
        self.ensure_loaded()
        if not edge.timestamp:
            edge.timestamp = _now()
        if edge.evidence_count <= 0 and edge.evidence_ids:
            edge.evidence_count = len(edge.evidence_ids)
        self._edges.append(edge)
        if persist:
            self._append_jsonl(self.edges_path, edge.as_dict())

    def _latest_nodes_as_of(self, as_of: str) -> dict[str, EconomicNode]:
        best: dict[str, EconomicNode] = {}
        for n in self._nodes:
            t = n.as_of or n.timestamp
            if t and t > as_of:
                continue
            prev = best.get(n.node_id)
            prev_t = (prev.as_of or prev.timestamp or "") if prev else ""
            cur_t = t or ""
            if prev is None or cur_t >= prev_t:
                best[n.node_id] = n
        return best

    def _edges_as_of(self, as_of: str) -> list[EconomicEdge]:
        by_id: dict[str, EconomicEdge] = {}
        for e in self._edges:
            claim_t = e.as_of or e.timestamp or ""
            if claim_t and claim_t > as_of:
                continue
            if not e.is_valid_as_of(as_of):
                continue
            prev = by_id.get(e.edge_id)
            prev_t = (prev.as_of or prev.timestamp or "") if prev else ""
            if prev is None or claim_t >= prev_t:
                by_id[e.edge_id] = e
        return list(by_id.values())

    def snapshot(
        self,
        as_of: str,
        snapshot_id: str | None = None,
        analysis_date: str | None = None,
        persist: bool = False,
    ) -> GraphSnapshot:
        self.ensure_loaded()
        nodes_map = self._latest_nodes_as_of(as_of)
        for e in self._edges_as_of(as_of):
            for nid in (e.source_id, e.target_id):
                if nid not in nodes_map:
                    nodes_map[nid] = EconomicNode(
                        node_id=nid,
                        type="factor",
                        name=nid,
                        state="unavailable",
                        confidence=0.0,
                        freshness=0.0,
                        as_of=as_of,
                    )
        edges = [
            e
            for e in self._edges_as_of(as_of)
            if e.source_id in nodes_map and e.target_id in nodes_map
        ]
        evidence_ids = sorted(
            {
                *{eid for n in nodes_map.values() for eid in n.evidence_ids},
                *{eid for e in edges for eid in e.evidence_ids},
            }
        )
        snap = GraphSnapshot(
            snapshot_id=snapshot_id or f"econ-{as_of}",
            as_of=as_of,
            nodes=list(nodes_map.values()),
            edges=edges,
            evidence_ids=evidence_ids,
            analysis_date=analysis_date,
        )
        if persist:
            out = self.snapshots_dir / f"{snap.snapshot_id}.json"
            out.write_text(snap.to_json(), encoding="utf-8")
        return snap

    def score_target(
        self,
        as_of: str,
        target_id: str,
        snapshot: GraphSnapshot | None = None,
    ) -> GraphScoreResult:
        snap = snapshot or self.snapshot(as_of)
        node_map = {n.node_id: n for n in snap.nodes}
        incoming = [e for e in snap.edges if e.target_id == target_id]

        scored: list[tuple[float, EconomicEdge]] = []
        for e in incoming:
            src = node_map.get(e.source_id)
            if src is None or src.state == "unavailable":
                continue
            nf = src.freshness if src.freshness is not None else 1.0
            if src.confidence is not None and src.confidence <= 0:
                continue
            val = e.effective_weight(freshness=nf)
            if val == 0.0 and e.direction in ("mixed", "neutral"):
                continue
            scored.append((val, e))

        scored.sort(key=lambda x: abs(x[0]), reverse=True)
        seen_pairs: set[tuple[str, str]] = set()
        source_count: dict[str, int] = defaultdict(int)
        values: list[tuple[float, EconomicEdge]] = []
        for val, e in scored:
            pair = (e.source_id.lower(), e.target_id.lower())
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            n = source_count[e.source_id.lower()]
            adjusted = val * (0.70 ** n)
            source_count[e.source_id.lower()] = n + 1
            values.append((adjusted, e))

        if not values:
            return GraphScoreResult(
                as_of=as_of,
                target_id=target_id,
                graph_score=0.0,
                graph_confidence=0.0,
                graph_regime="unavailable",
                edges_used=0,
                generated_at=_now(),
            )

        raw = sum(v for v, _ in values)
        denom = max(1.0, sum(abs(v) for v, _ in values))
        score = _clamp(raw / denom)
        conf = sum(e.confidence for _, e in values) / len(values)
        raw_abs = sum(abs(v) for v, _ in scored)
        used_abs = sum(abs(v) for v, _ in values)
        penalty = max(0.0, 1.0 - used_abs / max(1.0, raw_abs)) if scored else 0.0

        top = sorted(values, key=lambda x: x[0], reverse=True)[:8]
        risk = sorted(values, key=lambda x: x[0])[:8]
        regime = (
            "bullish" if score >= 0.20 else "bearish" if score <= -0.20 else "neutral"
        )
        return GraphScoreResult(
            as_of=as_of,
            target_id=target_id,
            graph_score=round(score, 4),
            graph_confidence=round(conf, 4),
            graph_regime=regime,
            edges_used=len(values),
            correlation_penalty=round(penalty, 4),
            top_drivers=[
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "relation": e.relation,
                    "contribution": round(v, 4),
                }
                for v, e in top
            ],
            risk_drivers=[
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "relation": e.relation,
                    "contribution": round(v, 4),
                }
                for v, e in risk
            ],
            generated_at=_now(),
        )

    def summary(self) -> dict:
        self.ensure_loaded()
        return {
            "nodes_lines": len(self._nodes),
            "unique_nodes": len({n.node_id for n in self._nodes}),
            "edges_lines": len(self._edges),
            "unique_edges": len({e.edge_id for e in self._edges}),
            "evidence": len(self._evidence),
        }
