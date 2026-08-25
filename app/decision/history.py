"""Decision History store — append-only, no hindsight overwrite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import DecisionRecord, DecisionPrediction


class DecisionHistory:
    """Persist and query DecisionRecords.

    Storage is a simple JSONL file so every record remains immutable.
    Updating an outcome creates a *new* line that references the same
    decision_id but carries actual_outcome / error_metric; the original
    prediction line is never modified.
    """

    def __init__(self, path: str | Path = "data/decision_history.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def append(self, record: DecisionRecord) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.as_dict(), ensure_ascii=False) + "\n")

    def load_all(self) -> list[DecisionRecord]:
        records: list[DecisionRecord] = []
        if not self.path.exists() or self.path.stat().st_size == 0:
            return records
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                preds = [
                    DecisionPrediction(**p) if isinstance(p, dict) else p
                    for p in data.get("predictions", [])
                ]
                data["predictions"] = preds
                records.append(DecisionRecord(**{
                    k: data.get(k) for k in DecisionRecord.__dataclass_fields__
                }))
        return records

    def by_id(self, decision_id: str) -> list[DecisionRecord]:
        return [r for r in self.load_all() if r.decision_id == decision_id]

    def latest_prediction(self, decision_id: str) -> DecisionRecord | None:
        """Return the earliest (original) prediction for a decision_id."""
        matches = self.by_id(decision_id)
        if not matches:
            return None
        # Prefer the first record that has no actual_outcome (the pure prediction)
        for r in matches:
            if r.actual_outcome is None:
                return r
        return matches[0]

    def record_outcome(
        self,
        decision_id: str,
        actual_outcome: str,
        outcome_observed_at: str,
        error_metric: float | None = None,
        notes: str = "",
    ) -> DecisionRecord | None:
        """Append an outcome update without mutating the original prediction."""
        original = self.latest_prediction(decision_id)
        if original is None:
            return None
        updated = DecisionRecord(
            decision_id=original.decision_id,
            as_of=original.as_of,
            title=original.title,
            decision_target=original.decision_target,
            input_evidence_ids=list(original.input_evidence_ids),
            network_snapshot_id=original.network_snapshot_id,
            predictions=list(original.predictions),
            actual_outcome=actual_outcome,
            outcome_observed_at=outcome_observed_at,
            error_metric=error_metric,
            tags=list(original.tags),
            created_at=outcome_observed_at,
            notes=notes or "outcome update",
        )
        self.append(updated)
        return updated

    def summary(self) -> dict:
        records = self.load_all()
        with_outcome = [r for r in records if r.actual_outcome is not None]
        errors = [r.error_metric for r in with_outcome if r.error_metric is not None]
        return {
            "total_lines": len(records),
            "unique_decisions": len({r.decision_id for r in records}),
            "with_outcome": len(with_outcome),
            "mean_error_metric": sum(errors) / len(errors) if errors else None,
        }
