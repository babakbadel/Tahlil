"""Core data models for Decision Engine.

All timestamps are ISO-8601 strings (UTC preferred for storage).
as_of / observed_at / source_published_at are deliberately separate
to prevent look-ahead bias.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import json


@dataclass
class Evidence:
    evidence_id: str
    source_url: str | None = None
    source_published_at: str | None = None  # when the source was published
    observed_at: str | None = None          # when we recorded it
    summary: str = ""
    confidence: float = 0.5                 # 0..1
    tags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Person:
    person_id: str
    name: str
    aliases: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RoleEvent:
    """A time-bounded role for a person. status is active|ended|uncertain."""

    person_id: str
    role: str
    organization: str = ""
    role_type: str = ""          # advisor|deputy|minister|other
    start_at: str | None = None
    end_at: str | None = None
    status: str = "active"
    source_url: str | None = None
    source_published_at: str | None = None
    observed_at: str | None = None
    confidence: float = 0.5
    influence_domain: list[str] = field(default_factory=list)  # economy|policy|...
    influence_score: float | None = None  # 0..1 provisional

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_active_as_of(self, as_of: str) -> bool:
        """True if role is valid at as_of (inclusive start, exclusive end if set)."""
        if self.start_at and as_of < self.start_at:
            return False
        if self.end_at and as_of >= self.end_at:
            return False
        return self.status in ("active", "uncertain")


@dataclass
class InfluenceEdge:
    from_person_id: str
    to_person_id: str
    relation_type: str           # advisor_to|deputy_of|collaborates|...
    domain: str = ""
    weight: float = 0.5          # 0..1
    valid_from: str | None = None
    valid_to: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.5

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_valid_as_of(self, as_of: str) -> bool:
        if self.valid_from and as_of < self.valid_from:
            return False
        if self.valid_to and as_of >= self.valid_to:
            return False
        return True


@dataclass
class NetworkSnapshot:
    """Point-in-time view of the influence network (as_of only)."""

    snapshot_id: str
    as_of: str
    persons: list[Person] = field(default_factory=list)
    roles: list[RoleEvent] = field(default_factory=list)
    edges: list[InfluenceEdge] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "as_of": self.as_of,
            "persons": [p.as_dict() for p in self.persons],
            "roles": [r.as_dict() for r in self.roles],
            "edges": [e.as_dict() for e in self.edges],
            "evidence_ids": self.evidence_ids,
            "notes": self.notes,
        }


@dataclass
class DecisionPrediction:
    """One predicted scenario inside a DecisionRecord."""

    scenario_id: str
    label: str
    probability: float           # 0..1
    rationale: str = ""
    impact_domains: list[str] = field(default_factory=list)  # market|fx|policy|...
    expected_market_effect: str | None = None  # bullish|bearish|neutral|mixed

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionRecord:
    """Immutable historical decision prediction + later outcome.

    Rules:
    - prediction fields are frozen after creation.
    - actual_outcome and error_metric may be filled later; never overwrite prediction.
    - as_of defines the information set available at prediction time.
    """

    decision_id: str
    as_of: str
    title: str
    decision_target: str         # what is being predicted
    input_evidence_ids: list[str] = field(default_factory=list)
    network_snapshot_id: str | None = None
    predictions: list[DecisionPrediction] = field(default_factory=list)
    actual_outcome: str | None = None
    outcome_observed_at: str | None = None
    error_metric: float | None = None   # e.g. Brier or custom
    tags: list[str] = field(default_factory=list)
    created_at: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["predictions"] = [p.as_dict() if hasattr(p, "as_dict") else p for p in self.predictions]
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False, indent=indent)
