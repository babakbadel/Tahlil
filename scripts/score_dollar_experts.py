"""Score locked BabiMind dollar forecasts without hindsight leakage.

A row is scored only when actual_at is at or after issued_at + horizon_days.
The outcome timestamp is required so an early/late observation cannot silently
be treated as the declared horizon.
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

INPUT = Path("data/dollar_expert_forecasts.csv")
OUTPUT = Path("data/dollar_expert_leaderboard.csv")

WEIGHTS = {"direction": 0.30, "price_accuracy": 0.30, "timing": 0.15, "regime": 0.15, "consistency": 0.10}


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def direction_score(direction: str, start: float, actual: float) -> float:
    move = actual - start
    threshold = max(start * 0.005, 1.0)
    actual_dir = "flat" if abs(move) < threshold else ("up" if move > 0 else "down")
    return 100.0 if direction == actual_dir else 0.0


def price_score(start: float, low: float, high: float, actual: float) -> float:
    if low > high:
        low, high = high, low
    if low <= actual <= high:
        return 100.0
    target = low if actual < low else high
    width = max(abs(high - low), start * 0.01, 1.0)
    return clamp(100.0 * math.exp(-abs(actual - target) / width))


def timing_score(issued_at: datetime, horizon_days: int, actual_at: datetime) -> float:
    expected = issued_at + timedelta(days=horizon_days)
    error_days = abs((actual_at - expected).total_seconds()) / 86400.0
    tolerance = max(1.0, horizon_days * 0.10)
    return clamp(100.0 * math.exp(-error_days / tolerance))


def consistency_score(history: list[float]) -> float:
    if len(history) < 2:
        return 100.0
    # Stable performance gets full credit; highly erratic forecasts are penalized.
    mean = sum(history) / len(history)
    variance = sum((x - mean) ** 2 for x in history) / len(history)
    return clamp(100.0 - math.sqrt(variance))


def main() -> None:
    if not INPUT.exists():
        print(f"missing input: {INPUT}")
        return

    rows = list(csv.DictReader(INPUT.open(encoding="utf-8-sig")))
    by_expert: dict[str, list[float]] = defaultdict(list)

    for row in rows:
        try:
            if str(row.get("locked", "")).strip().lower() not in {"true", "1", "yes"}:
                continue
            if not row.get("actual_price") or not row.get("actual_at"):
                continue
            issued = parse_dt(row["issued_at"])
            actual_at = parse_dt(row["actual_at"])
            horizon = int(row["horizon_days"])
            if actual_at < issued + timedelta(days=horizon):
                continue
            start = float(row["price_at_issue"])
            low = float(row["target_low"])
            high = float(row["target_high"])
            actual = float(row["actual_price"])
        except (ValueError, KeyError):
            continue

        d = direction_score(row["direction"].strip().lower(), start, actual)
        p = price_score(start, low, high, actual)
        t = timing_score(issued, horizon, actual_at)
        r = d  # Replace with explicit regime labels when the regime classifier is wired in.
        by_expert[row["expert"]].append(
            WEIGHTS["direction"] * d + WEIGHTS["price_accuracy"] * p + WEIGHTS["timing"] * t + WEIGHTS["regime"] * r
        )

    leaderboard = []
    for expert, scores in by_expert.items():
        consistency = consistency_score(scores)
        base = sum(scores) / len(scores)
        total = base + WEIGHTS["consistency"] * (consistency - 50.0)
        leaderboard.append({"expert": expert, "scored_forecasts": len(scores), "score": round(total, 2)})

    leaderboard.sort(key=lambda x: (-x["score"], -x["scored_forecasts"], x["expert"]))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["rank", "expert", "scored_forecasts", "score"])
        writer.writeheader()
        for rank, item in enumerate(leaderboard, 1):
            writer.writerow({"rank": rank, **item})
    print(f"Scored forecasts: {sum(len(v) for v in by_expert.values())}")
    for rank, item in enumerate(leaderboard, 1):
        print(rank, item)


if __name__ == "__main__":
    main()
