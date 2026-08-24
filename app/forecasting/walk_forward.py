"""Walk-forward evaluation utilities for BabiMind forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd

from .historical_forecaster import HistoricalAnalogForecaster, add_forward_targets


@dataclass(frozen=True)
class BacktestSummary:
    observations: int
    directional_accuracy: float
    brier_score: float
    mean_expected_return: float
    mean_realized_return: float
    mean_confidence: float

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def walk_forward_backtest(
    history: pd.DataFrame,
    feature_columns: Sequence[str],
    horizon: int = 20,
    train_window: int = 1000,
    step: int = 5,
    top_k: int = 40,
    min_similarity: float = 0.55,
) -> tuple[pd.DataFrame, BacktestSummary]:
    """Evaluate historical forecasting without look-ahead leakage.

    For every evaluation date, only observations strictly before that date are
    used for fitting. Forward targets are generated once from the original
    timeline, so the target at date t is never exposed to the model as a
    feature.
    """
    if horizon <= 0 or train_window < 50 or step <= 0:
        raise ValueError("invalid horizon, train_window, or step")
    if "date" not in history.columns:
        raise ValueError("history must contain date")

    df = history.sort_values("date").reset_index(drop=True)
    df = add_forward_targets(df, horizons=(horizon,))
    rows = []

    for i in range(train_window, len(df) - horizon, step):
        train = df.iloc[max(0, i - train_window):i].copy()
        current = df.iloc[i]
        model = HistoricalAnalogForecaster(top_k=top_k, min_similarity=min_similarity)
        model.fit(train, feature_columns)
        forecast = model.predict(current, horizons=(horizon,))[0]
        actual = current[f"fwd_return_{horizon}"]
        if pd.isna(actual) or forecast.sample_count == 0:
            continue
        rows.append(
            {
                "date": current["date"],
                "horizon": horizon,
                "probability_up": forecast.probability_up,
                "expected_return": forecast.expected_return,
                "actual_return": float(actual),
                "correct_direction": int((forecast.probability_up >= 0.5) == (float(actual) > 0)),
                "confidence": forecast.confidence,
                "similarity": forecast.similarity,
                "sample_count": forecast.sample_count,
            }
        )

    result = pd.DataFrame(rows)
    if result.empty:
        return result, BacktestSummary(0, float("nan"), float("nan"), float("nan"), float("nan"), float("nan"))

    y = (result["actual_return"] > 0).astype(float)
    p = result["probability_up"]
    summary = BacktestSummary(
        observations=len(result),
        directional_accuracy=float(result["correct_direction"].mean()),
        brier_score=float(((p - y) ** 2).mean()),
        mean_expected_return=float(result["expected_return"].mean()),
        mean_realized_return=float(result["actual_return"].mean()),
        mean_confidence=float(result["confidence"].mean()),
    )
    return result, summary
