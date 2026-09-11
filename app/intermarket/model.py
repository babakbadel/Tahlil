from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import json

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "babimind_intermarket_marks.yml"

@dataclass(frozen=True)
class IntermarketSignal:
    name: str
    score: float
    confidence: float = 1.0
    direction: str = "neutral"

@dataclass(frozen=True)
class IntermarketResult:
    score: float
    confidence: float
    regime: str
    rotation_score: float
    divergence: bool
    signals_used: int


def _clamp(x: float) -> float:
    return max(-1.0, min(1.0, float(x)))


def weighted_signal_score(signals: list[IntermarketSignal]) -> tuple[float, float]:
    """Combine independent cross-market signals without treating missing data as zero."""
    usable = [s for s in signals if math.isfinite(s.score) and s.confidence > 0]
    if not usable:
        return 0.0, 0.0
    weights = [max(0.0, min(1.0, s.confidence)) for s in usable]
    total = sum(weights)
    score = sum(_clamp(s.score) * w for s, w in zip(usable, weights)) / total
    confidence = min(1.0, total / max(3.0, len(usable)))
    return round(score, 4), round(confidence, 4)


def detect_divergence(price_score: float, confirmation_score: float, threshold: float = 0.45) -> bool:
    """Flag price/confirmation disagreement rather than blindly following price."""
    return price_score * confirmation_score < 0 and abs(price_score - confirmation_score) >= threshold


def classify_regime(score: float) -> str:
    if score >= 0.45:
        return "risk_on"
    if score <= -0.45:
        return "risk_off"
    return "mixed"


def marks_second_level_gate(expected_return: float, priced_in: float, risk: float) -> float:
    """Second-level thinking: reward edge over expectations and penalize downside risk."""
    edge = float(expected_return) - float(priced_in)
    return round(_clamp(edge) * max(0.0, 1.0 - min(1.0, float(risk))), 4)


def rotation_score(relative_strength: float, flow: float, macro_fit: float,
                   valuation_gap: float, cycle_fit: float, catalyst: float,
                   positioning: float) -> float:
    """Version-1 prior weights from the BabiMind Intermarket + Marks framework."""
    value = (
        0.25 * relative_strength + 0.20 * flow + 0.15 * macro_fit +
        0.15 * valuation_gap + 0.10 * cycle_fit + 0.10 * catalyst +
        0.05 * positioning
    )
    return round(_clamp(value), 4)


def evaluate(price_score: float, signals: list[IntermarketSignal], **rotation_inputs: float) -> IntermarketResult:
    confirmation, confidence = weighted_signal_score(signals)
    divergence = detect_divergence(price_score, confirmation)
    score = 0.5 * _clamp(price_score) + 0.5 * confirmation
    if divergence:
        confidence *= 0.65
    rscore = rotation_score(**rotation_inputs) if rotation_inputs else 0.0
    return IntermarketResult(
        score=round(score, 4),
        confidence=round(confidence, 4),
        regime=classify_regime(score),
        rotation_score=rscore,
        divergence=divergence,
        signals_used=len([s for s in signals if s.confidence > 0]),
    )
