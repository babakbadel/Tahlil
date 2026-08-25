"""Decision Engine — produces timestamped predictions from network + evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
import uuid

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
    ) -> DecisionRecord:
        """Create a DecisionRecord at as_of.

        If scenarios is not provided, a neutral placeholder is used.
        Callers should supply explicit scenarios for real analysis.
        """
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
            total = sum(p.probability for p in preds) or 1.0
            for p in preds:
                p.probability = round(p.probability / total, 4)
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
            decision_id=f"dec-{uuid.uuid4().hex[:12]}",
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
