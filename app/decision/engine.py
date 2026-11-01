"""Decision Engine — produces timestamped predictions from network + evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
import uuid
import math

from .models import (
    DecisionRecord,
    DecisionPrediction,
    Evidence,
    NetworkSnapshot,
)
from .history import DecisionHistory
from .network import InfluenceNetwork


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class DecisionEngine:
    """Minimal decision engine.

    Current version is rule/heuristic based so it can be used immediately
    while richer models (LLM, game-theory solvers, historical calibration)
    are added later. Every output is a DecisionRecord that can be
    persisted and later scored.
    """

    def __init__(
        self,
        network: InfluenceNetwork | None = None,
        history: DecisionHistory | None = None,
    ) -> None:
        self.network = network or InfluenceNetwork()
        self.history = history or DecisionHistory()

    def predict(
        self,
        *,
        title: str,
        decision_target: str,
        as_of: str,
        evidence: Sequence[Evidence] = (),
        scenarios: Sequence[dict] | None = None,
        tags: Sequence[str] = (),
        notes: str = "",
        decision_id: str | None = None,
    ) -> DecisionRecord:
        """Create a DecisionRecord at as_of.

        If scenarios is not provided, a neutral placeholder is used.
        Callers should supply explicit scenarios for real analysis.
        """
        timestamp = datetime.fromisoformat(as_of.replace('Z', '+00:00'))
        timestamp = timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
        for item in evidence:
            if not math.isfinite(item.confidence) or not 0 <= item.confidence <= 1:
                raise ValueError('invalid evidence confidence')
            for stamp in (item.observed_at, item.source_published_at):
                if stamp:
                    observed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
                    observed = observed.replace(tzinfo=timezone.utc) if observed.tzinfo is None else observed
                    if observed > timestamp:
                        raise ValueError('future evidence is not available as_of')
        if decision_id:
            existing = self.history.latest_prediction(decision_id)
            if existing:
                return existing
        snapshot = self.network.snapshot(as_of=as_of)
        evidence_ids = [e.evidence_id for e in evidence]
        for e in evidence:
            self.network.add_evidence(e)

        if scenarios:
            preds = [
                DecisionPrediction(
                    scenario_id=s.get("scenario_id", f"s-{i}"),
                    label=s["label"],
                    probability=float(s["probability"]),
                    rationale=s.get("rationale", ""),
                    impact_domains=list(s.get("impact_domains", [])),
                    expected_market_effect=s.get("expected_market_effect"),
                )
                for i, s in enumerate(scenarios)
            ]
            total = sum(p.probability for p in preds)
            if any(not math.isfinite(p.probability) or not 0 <= p.probability <= 1 for p in preds) or abs(total - 1.0) > 1e-6:
                raise ValueError('scenario probabilities must be finite, nonnegative and sum to one')
        else:
            preds = [
                DecisionPrediction(
                    scenario_id="s-neutral",
                    label="insufficient_evidence",
                    probability=1.0,
                    rationale="No explicit scenarios supplied; network snapshot only.",
                    impact_domains=[],
                    expected_market_effect="neutral",
                )
            ]

        record = DecisionRecord(
            decision_id=decision_id or f"dec-{uuid.uuid4().hex[:12]}",
            as_of=as_of,
            title=title,
            decision_target=decision_target,
            input_evidence_ids=evidence_ids,
            network_snapshot_id=snapshot.snapshot_id,
            predictions=preds,
            tags=list(tags),
            created_at=_now_iso(),
            notes=notes,
        )
        self.history.append(record)
        return record

    def network_summary(self, as_of: str) -> dict:
        snap = self.network.snapshot(as_of=as_of)
        return {
            "as_of": snap.as_of,
            "person_count": len(snap.persons),
            "active_roles": len(snap.roles),
            "active_edges": len(snap.edges),
            "roles": [
                {
                    "name": next(
                        (p.name for p in snap.persons if p.person_id == r.person_id),
                        r.person_id,
                    ),
                    "role": r.role,
                    "organization": r.organization,
                    "influence_score": r.influence_score,
                    "domains": r.influence_domain,
                }
                for r in snap.roles
            ],
        }
