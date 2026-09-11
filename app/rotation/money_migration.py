"""BabiMind seven-market capital migration scoring.

This is an estimation layer, not a claim about the complete wealth stock of Iran.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Optional

MARKETS = ("usd", "gold", "housing", "auto", "fixed_income", "stocks", "crypto")
WEIGHTS = {
    "price_relative_return": .30,
    "volume_flow": .20,
    "liquidity": .15,
    "inflation_real_rate": .15,
    "macro_political_risk": .10,
    "positioning_behavior": .10,
}

@dataclass
class MarketEvidence:
    price_relative_return: Optional[float] = None
    volume_flow: Optional[float] = None
    liquidity: Optional[float] = None
    inflation_real_rate: Optional[float] = None
    macro_political_risk: Optional[float] = None
    positioning_behavior: Optional[float] = None


def weighted_score(evidence: MarketEvidence) -> Optional[float]:
    vals = asdict(evidence)
    usable = [(WEIGHTS[k], float(v)) for k, v in vals.items() if v is not None]
    if not usable:
        return None
    denom = sum(w for w, _ in usable)
    return round(sum(w * v for w, v in usable) / denom, 2)


def normalize_capital(scores: Dict[str, Optional[float]]) -> Dict[str, float]:
    """Convert non-negative attractiveness scores into a 100-unit estimate."""
    usable = {k: max(0.0, float(v)) for k, v in scores.items() if v is not None}
    total = sum(usable.values())
    if not total:
        return {k: 0.0 for k in MARKETS}
    result = {k: round(usable.get(k, 0.0) / total * 100, 2) for k in MARKETS}
    # Make rounding sum exactly 100.
    result[MARKETS[-1]] = round(result[MARKETS[-1]] + (100 - sum(result.values())), 2)
    return result


def migration(today: Dict[str, float], yesterday: Dict[str, float]) -> Dict[str, float]:
    return {k: round(today.get(k, 0.0) - yesterday.get(k, 0.0), 2) for k in MARKETS}
