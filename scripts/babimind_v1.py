#!/usr/bin/env python3
"""Lightweight, deterministic BabiMind v1 core.

This module intentionally works without an LLM. It consumes a small set of
normalized numeric features and produces a transparent probability estimate.
OpenRouter is optional and belongs only to the text/event layer.
"""
from __future__ import annotations
import json, math, os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "babimind_v1_signal.json"

FEATURES = {
    "usd_1d": 0.22,
    "usd_5d": 0.16,
    "copper_1d": 0.12,
    "copper_usd_1d": 0.12,
    "fml_stock_1d": 0.10,
    "fml_stock_5d": 0.08,
    "real_money_flow": 0.08,
    "market_liquidity": 0.05,
    "metal_sector_return": 0.04,
    "political_risk": 0.03,
}

def clamp(x: float, lo: float = -3.0, hi: float = 3.0) -> float:
    return max(lo, min(hi, float(x)))

def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def predict(features: dict[str, float]) -> dict:
    score = sum(w * clamp(features.get(k, 0.0)) for k, w in FEATURES.items())
    # Conservative prior: do not manufacture high confidence from missing data.
    available = sum(k in features for k in FEATURES)
    coverage = available / len(FEATURES)
    raw = sigmoid(score * 2.4)
    probability = 0.5 + (raw - 0.5) * min(1.0, coverage)
    confidence = abs(probability - 0.5) * 2.0 * coverage
    return {
        "asset": "FMLI",
        "horizon": "until_option_expiry",
        "prob_up": round(probability, 4),
        "prob_down": round(1.0 - probability, 4),
        "confidence": round(confidence, 4),
        "coverage": round(coverage, 4),
        "score": round(score, 6),
        "features_used": {k: features[k] for k in FEATURES if k in features},
    }

def main() -> None:
    raw = os.getenv("BABIMIND_FEATURES", "{}")
    try:
        features = json.loads(raw)
        if not isinstance(features, dict):
            raise ValueError("BABIMIND_FEATURES must be a JSON object")
    except Exception as exc:
        raise SystemExit(f"invalid BABIMIND_FEATURES: {exc}")
    result = predict({k: float(v) for k, v in features.items()})
    result.update({
        "model": "BabiMind-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "llm_dependency": False,
        "decision_policy": "no_trade_when_confidence_below_threshold",
        "threshold": 0.60,
    })
    result["action"] = "signal" if result["confidence"] >= result["threshold"] else "wait"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
