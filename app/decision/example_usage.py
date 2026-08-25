"""Minimal example: load network, take snapshot, make a decision record."""

from __future__ import annotations

from pathlib import Path

from app.decision import (
    DecisionEngine,
    DecisionHistory,
    InfluenceNetwork,
    Evidence,
)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    net_path = root / "people" / "pezeshkian_network.json"
    history_path = root / "data" / "decision_history.jsonl"

    network = InfluenceNetwork()
    network.load_from_json(net_path)

    history = DecisionHistory(history_path)
    engine = DecisionEngine(network=network, history=history)

    as_of = "2026-08-25"
    print("Network summary @", as_of)
    print(engine.network_summary(as_of))

    evidence = [
        Evidence(
            evidence_id="ev-placeholder-1",
            summary="Placeholder evidence — replace with real source",
            observed_at=as_of,
            confidence=0.3,
            tags=["economy"],
        )
    ]

    record = engine.predict(
        title="نمونه — رژیم سیاست اقتصادی کوتاه‌مدت",
        decision_target="direction_of_macro_policy_bias",
        as_of=as_of,
        evidence=evidence,
        scenarios=[
            {
                "scenario_id": "s-ease",
                "label": "سیاست انبساطی‌تر / حمایت از بازار",
                "probability": 0.35,
                "rationale": "شبکه مشاوران اقتصادی فعال؛ نیاز به شواهد بیشتر",
                "impact_domains": ["market", "economy"],
                "expected_market_effect": "bullish",
            },
            {
                "scenario_id": "s-hold",
                "label": "ادامه وضعیت فعلی",
                "probability": 0.45,
                "rationale": "عدم تغییر واضح در سیگنال‌های عمومی",
                "impact_domains": ["policy"],
                "expected_market_effect": "neutral",
            },
            {
                "scenario_id": "s-tighten",
                "label": "انقباض یا محدودیت بیشتر",
                "probability": 0.20,
                "rationale": "سناریوی کم‌احتمال بدون شوک جدید",
                "impact_domains": ["market", "fx"],
                "expected_market_effect": "bearish",
            },
        ],
        tags=["bootstrap", "macro"],
        notes="رکورد نمونه برای راه‌اندازی Decision History — احتمالات موقتی هستند.",
    )

    print("\nCreated decision:", record.decision_id)
    print(record.to_json())
    print("\nHistory summary:", history.summary())


if __name__ == "__main__":
    main()
