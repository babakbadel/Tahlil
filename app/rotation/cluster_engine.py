"""Clustered capital-flow and relative-velocity engine for BabiMind.

The engine is intentionally dependency-free. It does not claim to identify
specific actors or hidden intent; it scores observable market behaviour:
direction, velocity, acceleration, flow, future-demand proxies, supply
constraints, attention gaps and lead/lag relationships.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from statistics import mean
from typing import Iterable, Sequence


@dataclass(frozen=True)
class AssetSignal:
    symbol: str
    cluster: str
    returns: Sequence[float] = field(default_factory=tuple)
    flow: float = 0.0
    future_demand: float = 0.0
    supply_constraint: float = 0.0
    attention: float = 0.0
    accumulation: float = 0.0


@dataclass(frozen=True)
class ClusterSignal:
    cluster: str
    members: int
    direction: float
    velocity: float
    acceleration: float
    flow: float
    future_demand: float
    supply_constraint: float
    attention_gap: float
    score: float
    leader: str | None
    followers: tuple[str, ...]


def _clamp(value: float, low: float = -100.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _last(values: Sequence[float]) -> float:
    return float(values[-1]) if values else 0.0


def _velocity(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(values[-1] - values[-2])


def _acceleration(values: Sequence[float]) -> float:
    if len(values) < 3:
        return 0.0
    return float((values[-1] - values[-2]) - (values[-2] - values[-3]))


def _safe(value: float) -> float:
    return float(value) if isfinite(float(value)) else 0.0


class RotationEngine:
    """Rank economic clusters and assets by direction and relative speed."""

    def __init__(self, velocity_weight: float = 1.0, acceleration_weight: float = 0.5):
        self.velocity_weight = velocity_weight
        self.acceleration_weight = acceleration_weight

    def rank_assets(self, assets: Iterable[AssetSignal]) -> list[dict]:
        rows: list[dict] = []
        for asset in assets:
            direction = _clamp(_last(asset.returns))
            velocity = _clamp(_velocity(asset.returns))
            acceleration = _clamp(_acceleration(asset.returns))
            attention_gap = _clamp(asset.future_demand - asset.attention)
            score = _clamp(
                0.20 * direction
                + 0.20 * velocity
                + 0.10 * acceleration
                + 0.15 * _safe(asset.flow)
                + 0.15 * _safe(asset.future_demand)
                + 0.10 * _safe(asset.supply_constraint)
                + 0.10 * attention_gap
                + 0.10 * _safe(asset.accumulation)
            )
            rows.append(
                {
                    "symbol": asset.symbol,
                    "cluster": asset.cluster,
                    "direction": direction,
                    "velocity": velocity,
                    "acceleration": acceleration,
                    "attention_gap": attention_gap,
                    "score": score,
                }
            )
        return sorted(rows, key=lambda row: row["score"], reverse=True)

    def rank_clusters(self, assets: Iterable[AssetSignal]) -> list[ClusterSignal]:
        grouped: dict[str, list[AssetSignal]] = {}
        for asset in assets:
            grouped.setdefault(asset.cluster, []).append(asset)

        result: list[ClusterSignal] = []
        for cluster, members in grouped.items():
            ranked = self.rank_assets(members)
            leader = ranked[0]["symbol"] if ranked else None
            followers = tuple(row["symbol"] for row in ranked[1:])
            result.append(
                ClusterSignal(
                    cluster=cluster,
                    members=len(members),
                    direction=_clamp(mean(_last(a.returns) for a in members)),
                    velocity=_clamp(mean(_velocity(a.returns) for a in members)),
                    acceleration=_clamp(mean(_acceleration(a.returns) for a in members)),
                    flow=_clamp(mean(_safe(a.flow) for a in members)),
                    future_demand=_clamp(mean(_safe(a.future_demand) for a in members)),
                    supply_constraint=_clamp(mean(_safe(a.supply_constraint) for a in members)),
                    attention_gap=_clamp(mean(_safe(a.future_demand - a.attention) for a in members)),
                    score=_clamp(mean(row["score"] for row in ranked)),
                    leader=leader,
                    followers=followers,
                )
            )
        return sorted(result, key=lambda row: row.score, reverse=True)


__all__ = ["AssetSignal", "ClusterSignal", "RotationEngine"]
