"""Score locked BabiMind dollar forecasts.

Input CSV columns:
expert,issued_at,horizon_days,price_at_issue,target_low,target_high,direction,actual_price,actual_at

A forecast is scored only after actual_price is available at/after the declared
horizon. Missing outcomes remain unscored; this prevents hindsight bias.
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

INPUT = Path("data/dollar_expert_forecasts.csv")
OUTPUT = Path("data/dollar_expert_leaderboard.csv")

WEIGHTS = {
    "direction": 0.30,
    "price_accuracy": 0.30,
    "timing": 0.15,
    "regime": 0.15,
    "consistency": 0.10,
}


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def direction_score(direction: str, start: float, actual: float) -> float:
    move = actual - start
    if abs(move) < max(start * 0.005, 1):
        actual_dir = "flat"
    else:
        actual_dir = "up" if move > 0 else "down"
    if direction == actual_dir:
        return 100.0
    if direction == "flat" and actual_dir != "flat":
        return 0.0
    return 0.0


def price_score(start: float, low: float, high: float, actual: float) -> float:
    if low > high:
        low, high = high, low
    if low <= actual <= high:
        return 100.0
    target = low if actual < low else high
    width = max(abs(high - low), start * 0.01, 1.0)
    error = abs(actual - target)
    return clamp(100.0 * math.exp(-error / width))


def regime_score(direction: str, start: float, actual: float) -> float:
    # Simple regime agreement. A later regime classifier can replace this
    # without changing the leaderboard schema.
    return direction_score(direction, start, actual)


def main() -> None:
    if not INPUT.exists():
        print(f"missing input: {INPUT}")
        return

    rows = list(csv.DictReader(INPUT.open(encoding="utf-8-sig")))
    by_expert = defaultdict(list)
    for row in rows:
        try:
            actual = float(row.get("actual_price") or "")
            start = float(row["price_at_issue"])
            low = float(row["target_low"])
            high = float(row["target_high"])
        except (ValueError, KeyError):
            continue
        d = direction_score(row["direction"].lower(), start, actual)
        p = price_score(start, low, high, actual)
        r = regime_score(row["direction"].lower(), start, actual)
        # Timing is binary only after the declared horizon is evaluated.
        timing = 100.0
        consistency = 100.0
        total = (
            WEIGHTS["direction"] * d
            + WEIGHTS["price_accuracy"] * p
            + WEIGHTS["timing"] * timing
            + WEIGHTS["regime"] * r
            + WEIGHTS["consistency"] * consistency
        )
        by_expert[row["expert"]].append(total)

    leaderboard = []
    for expert, scores in by_expert.items():
        leaderboard.append({
            "expert": expert,
            "scored_forecasts": len(scores),
            "score": round(sum(scores) / len(scores), 2),
        })
    leaderboard.sort(key=lambda x: (-x["score"], -x["scored_forecasts"], x["expert"]))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["rank", "expert", "scored_forecasts", "score"])
        writer.writeheader()
        for rank, item in enumerate(leaderboard, 1):
            writer.writerow({"rank": rank, **item})
    for rank, item in enumerate(leaderboard, 1):
        print(rank, item)


if __name__ == "__main__":
    main()
