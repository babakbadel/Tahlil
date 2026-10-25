"""Option ranking pipeline with hard anti-hindsight and expiry gates.

Implements the mandatory validation order from graph/option-ranking-pipeline.md.
Does NOT invent missing IV/Greeks or synchronized quotes.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from math import isfinite
from typing import Any, Sequence


@dataclass
class OptionContract:
    symbol: str
    underlying: str
    option_type: str          # call|put
    strike: float
    expiry: date              # Gregorian
    last_price: float | None = None
    bid: float | None = None
    ask: float | None = None
    volume: float | None = None
    open_interest: float | None = None
    event_time: str | None = None   # ISO timestamp of quote
    underlying_price: float | None = None
    underlying_event_time: str | None = None
    source: str = "unknown"

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["expiry"] = self.expiry.isoformat()
        return d


@dataclass
class RankedOption:
    contract: OptionContract
    rank: int | None
    score: float | None
    moneyness: float | None
    intrinsic: float | None
    time_value: float | None
    break_even: float | None
    data_gaps: list[str] = field(default_factory=list)
    confidence: float = 0.0
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract.as_dict(),
            "rank": self.rank,
            "score": self.score,
            "moneyness": self.moneyness,
            "intrinsic": self.intrinsic,
            "time_value": self.time_value,
            "break_even": self.break_even,
            "data_gaps": self.data_gaps,
            "confidence": self.confidence,
            "notes": self.notes,
        }


def _parse_date(value: str | date) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])


def filter_active(contracts: Sequence[OptionContract], as_of: date) -> list[OptionContract]:
    """Hard rule: exclude any contract with expiry <= as_of."""
    return [c for c in contracts if c.expiry > as_of]


def compute_basic_metrics(c: OptionContract) -> tuple[float | None, float | None, float | None, float | None, list[str]]:
    gaps: list[str] = []
    if (c.option_type not in {"call", "put"} or not isfinite(c.strike) or c.strike <= 0
            or any(v is not None and (not isfinite(v) or v < 0)
                   for v in (c.last_price, c.bid, c.ask, c.volume, c.open_interest, c.underlying_price))):
        return None, None, None, None, ["invalid_contract", "blocked_for_final_rank"]
    if c.bid is not None and c.ask is not None and c.bid > c.ask:
        gaps.append("crossed_bid_ask")
    if c.underlying_price is None or c.underlying_price <= 0:
        gaps.append("missing_underlying_price")
        return None, None, None, None, gaps
    if c.last_price is None:
        gaps.append("missing_last_price")

    spot = c.underlying_price
    k = c.strike
    if c.option_type == "call":
        moneyness = spot / k
        intrinsic = max(0.0, spot - k)
        break_even = k + c.last_price if c.last_price is not None else None
    else:
        moneyness = k / spot if spot else None
        intrinsic = max(0.0, k - spot)
        break_even = k - c.last_price if c.last_price is not None else None

    time_value = None
    if c.last_price is not None:
        time_value = c.last_price - intrinsic
        if time_value < 0:
            gaps.append("negative_time_value")

    if c.event_time and c.underlying_event_time:
        try:
            quote = datetime.fromisoformat(c.event_time.replace("Z", "+00:00"))
            underlying_quote = datetime.fromisoformat(c.underlying_event_time.replace("Z", "+00:00"))
            synchronized = (quote.tzinfo is not None and underlying_quote.tzinfo is not None
                            and abs((quote - underlying_quote).total_seconds()) <= 60)
        except (ValueError, TypeError):
            synchronized = False
        if not synchronized:
            gaps.append("timestamp_mismatch")
    else:
        gaps.append("missing_synchronized_timestamps")

    if c.volume is None:
        gaps.append("missing_volume")
    if c.open_interest is None:
        gaps.append("missing_oi")
    if c.bid is None or c.ask is None:
        gaps.append("missing_bid_ask")

    return moneyness, intrinsic, time_value, break_even, gaps


def rank_options(
    contracts: Sequence[OptionContract],
    as_of: date | str,
    require_synchronized: bool = True,
) -> list[RankedOption]:
    """Run ranking pipeline.

    If require_synchronized=True and timestamps are missing/mismatched,
    rank stays None. No final 'best' without synchronized live data.
    """
    as_of_d = _parse_date(as_of)
    active = filter_active(contracts, as_of_d)

    ranked: list[RankedOption] = []
    for c in active:
        mon, intr, tv, be, gaps = compute_basic_metrics(c)

        score = None
        conf = 0.0
        if c.event_time:
            try:
                if date.fromisoformat(c.event_time[:10]) > as_of_d:
                    gaps.append("future_quote")
            except ValueError:
                gaps.append("timestamp_mismatch")
        invalid = any(g in gaps for g in ("invalid_contract", "missing_underlying_price", "missing_last_price", "negative_time_value", "crossed_bid_ask", "future_quote"))
        unsynchronized = any(g in gaps for g in ("timestamp_mismatch", "missing_synchronized_timestamps"))
        if invalid or (require_synchronized and unsynchronized):
            if "blocked_for_final_rank" not in gaps:
                gaps.append("blocked_for_final_rank")
        else:
            vol = c.volume or 0.0
            oi = c.open_interest or 0.0
            mon_penalty = abs((mon or 1.0) - 1.0)
            score = (vol ** 0.5) * (1.0 + (oi ** 0.3)) / (1.0 + 5.0 * mon_penalty)
            conf = max(0.1, 1.0 - 0.15 * len(gaps))

        ranked.append(
            RankedOption(
                contract=c,
                rank=None,
                score=score,
                moneyness=mon,
                intrinsic=intr,
                time_value=tv,
                break_even=be,
                data_gaps=gaps,
                confidence=conf,
                notes="",
            )
        )

    scorable = [r for r in ranked if r.score is not None and "blocked_for_final_rank" not in r.data_gaps]
    scorable.sort(key=lambda r: r.score or 0.0, reverse=True)
    for i, r in enumerate(scorable, 1):
        r.rank = i

    return ranked


def summarize_ranking(ranked: Sequence[RankedOption]) -> dict[str, Any]:
    with_rank = [r for r in ranked if r.rank is not None]
    blocked = [r for r in ranked if "blocked_for_final_rank" in r.data_gaps]
    return {
        "active_count": len(ranked),
        "ranked_count": len(with_rank),
        "blocked_count": len(blocked),
        "top": [r.as_dict() for r in sorted(with_rank, key=lambda x: x.rank or 999)[:5]],
        "can_declare_best": len(with_rank) > 0 and len(blocked) == 0,
    }
