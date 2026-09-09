"""Economic Graph models for BabiMind EconomicGraphStore.

Design principles (aligned with Decision Engine):
- as_of / observed_at / source_published_at are separate (anti look-ahead)
- predictions and historical edges are never overwritten in place
- missing data is never coerced to zero signal
- every node/edge carries confidence, freshness, and provenance
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal
import json


NodeType = Literal[
    "factor",
    "asset",
    "sector",
    "macro",
    "commodity",
    "fx",
    "option",
    "news",
    "policy",
    "actor",
    "flow",
    "regime",
]

RelationType = Literal[
    "causes",
    "correlates_with",
    "transmits_to",
    "depends_on",
    "reacts_to",
    "influences",
    "hedges",
    "substitutes",
    "leads",
    "lags",
]

Direction = Literal["positive", "negative", "mixed", "neutral"]

EdgeState = Literal["active", "stale", "deprecated", "hypothesis"]

NodeState = Literal["active", "stale", "unavailable", "hypothesis"]


@dataclass
class GraphEvidence:
    """Provenance for a node value or edge claim."""

    evidence_id: str
    source: str
    source_url: str | None = None
    source_published_at: str | None = None
    observed_at: str | None = None
    summary: str = ""
    confidence: float = 0.5
    tags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EconomicNode:
    """Time-aware economic/market entity.

    value is optional: structural nodes may exist without a numeric value.
    When value is missing, state should not be treated as a zero signal.
    """

    node_id: str
    type: NodeType
    name: str
    value: float | None = None
    unit: str | None = None
    timestamp: str | None = None
    as_of: str | None = None
    source: str | None = None
    confidence: float = 0.5
    freshness: float = 1.0
    state: NodeState = "active"
    evidence_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EconomicEdge:
    """Directed relationship between two economic nodes."""

    edge_id: str
    source_id: str
    target_id: str
    relation: RelationType
    direction: Direction = "mixed"
    weight: float = 0.5
    confidence: float = 0.5
    lag_days: float | None = None
    independence_factor: float = 1.0
    valid_from: str | None = None
    valid_to: str | None = None
    state: EdgeState = "active"
    evidence_ids: list[str] = field(default_factory=list)
    evidence_count: int = 0
    timestamp: str | None = None
    as_of: str | None = None
    tags: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_valid_as_of(self, as_of: str) -> bool:
        if self.state == "deprecated":
            return False
        if self.valid_from and as_of < self.valid_from:
            return False
        if self.valid_to and as_of >= self.valid_to:
            return False
        return True

    def effective_weight(self, freshness: float = 1.0) -> float:
        f = max(0.0, min(1.0, freshness))
        ind = max(0.0, min(1.0, self.independence_factor))
        conf = max(0.0, min(1.0, self.confidence))
        w = max(0.0, min(1.0, self.weight))
        sign = {"positive": 1.0, "negative": -1.0, "mixed": 0.0, "neutral": 0.0}.get(
            self.direction, 0.0
        )
        return sign * w * conf * f * ind


@dataclass
class GraphSnapshot:
    """Point-in-time view of the economic graph (as_of only)."""

    snapshot_id: str
    as_of: str
    nodes: list[EconomicNode] = field(default_factory=list)
    edges: list[EconomicEdge] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    analysis_date: str | None = None
    notes: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "as_of": self.as_of,
            "analysis_date": self.analysis_date,
            "nodes": [n.as_dict() for n in self.nodes],
            "edges": [e.as_dict() for e in self.edges],
            "evidence_ids": self.evidence_ids,
            "notes": self.notes,
            "meta": self.meta,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False, indent=indent)


@dataclass
class GraphScoreResult:
    """Output of scoring a snapshot for one or more target assets."""

    as_of: str
    target_id: str
    graph_score: float
    graph_confidence: float
    graph_regime: str
    edges_used: int = 0
    correlation_penalty: float = 0.0
    top_drivers: list[dict[str, Any]] = field(default_factory=list)
    risk_drivers: list[dict[str, Any]] = field(default_factory=list)
    missing_policy: str = "MISSING_IS_NOT_ZERO"
    generated_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
