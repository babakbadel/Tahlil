"""BabiMind historical-pattern forecasting engine.

The engine deliberately forecasts conditionally rather than assuming that history
repeats exactly. It searches historical observations for regimes similar to the
current state, estimates forward return distributions, and exposes confidence
and sample-size diagnostics. It is designed for walk-forward use: callers must
fit only on observations available before each forecast date.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ForecastResult:
    horizon: int
    probability_up: float
    probability_down: float
    expected_return: float
    median_return: float
    q10_return: float
    q90_return: float
    max_drawdown_proxy: float
    sample_count: int
    similarity: float
    confidence: float

    def as_dict(self) -> dict:
        return {
            "horizon": self.horizon,
            "probability_up": self.probability_up,
            "probability_down": self.probability_down,
            "expected_return": self.expected_return,
            "median_return": self.median_return,
            "q10_return": self.q10_return,
            "q90_return": self.q90_return,
            "max_drawdown_proxy": self.max_drawdown_proxy,
            "sample_count": self.sample_count,
            "similarity": self.similarity,
            "confidence": self.confidence,
        }


class HistoricalAnalogForecaster:
    """Nearest-regime historical analog forecaster.

    Parameters
    ----------
    feature_weights:
        Optional mapping of feature name to importance. Weights are normalized.
    top_k:
        Number of nearest historical observations used for the conditional
        distribution. A larger value is more stable but less regime-specific.
    min_similarity:
        Minimum normalized similarity required for an observation to be used.
    """

    def __init__(
        self,
        feature_weights: dict[str, float] | None = None,
        top_k: int = 40,
        min_similarity: float = 0.55,
    ) -> None:
        if top_k < 5:
            raise ValueError("top_k must be >= 5")
        self.feature_weights = feature_weights or {}
        self.top_k = top_k
        self.min_similarity = min_similarity
        self._feature_mean: pd.Series | None = None
        self._feature_std: pd.Series | None = None
        self._train: pd.DataFrame | None = None

    def fit(self, history: pd.DataFrame, feature_columns: Sequence[str]) -> "HistoricalAnalogForecaster":
        if history.empty:
            raise ValueError("history is empty")
        missing = [c for c in feature_columns if c not in history.columns]
        if missing:
            raise ValueError(f"missing feature columns: {missing}")
        if "close" not in history.columns:
            raise ValueError("history must contain close")

        x = history.loc[:, feature_columns].astype(float).replace([np.inf, -np.inf], np.nan)
        valid = x.notna().all(axis=1) & history["close"].notna()
        self._train = history.loc[valid].copy().reset_index(drop=True)
        x = self._train.loc[:, feature_columns].astype(float)
        self._feature_mean = x.mean()
        self._feature_std = x.std(ddof=0).replace(0, 1.0)
        self._features = list(feature_columns)
        return self

    def _distance(self, current: pd.Series) -> np.ndarray:
        assert self._train is not None
        assert self._feature_mean is not None
        assert self._feature_std is not None

        cur = current[self._features].astype(float)
        z_cur = (cur - self._feature_mean) / self._feature_std
        z_hist = (self._train[self._features] - self._feature_mean) / self._feature_std

        weights = np.array([self.feature_weights.get(c, 1.0) for c in self._features], dtype=float)
        weights = weights / weights.sum()
        dist = np.sqrt(((z_hist.to_numpy() - z_cur.to_numpy()) ** 2 * weights).sum(axis=1))
        return dist

    @staticmethod
    def _similarity(distance: np.ndarray) -> np.ndarray:
        # Maps distance to (0, 1], with smooth decay and no arbitrary hard cutoff.
        return np.exp(-distance / 2.0)

    def predict(self, current: pd.Series, horizons: Iterable[int] = (1, 5, 20, 60)) -> list[ForecastResult]:
        if self._train is None:
            raise RuntimeError("fit() must be called before predict()")
        if any(c not in current.index for c in self._features):
            missing = [c for c in self._features if c not in current.index]
            raise ValueError(f"current observation missing features: {missing}")

        distances = self._distance(current)
        similarities = self._similarity(distances)
        order = np.argsort(distances)
        selected = [i for i in order[: self.top_k] if similarities[i] >= self.min_similarity]
        if len(selected) < 5:
            selected = list(order[: min(self.top_k, len(order))])

        weights = similarities[selected]
        weights = weights / weights.sum()
        spot = float(current["close"])
        results: list[ForecastResult] = []

        for horizon in horizons:
            future = []
            drawdowns = []
            valid_weights = []
            for i, w in zip(selected, weights):
                row = self._train.iloc[i]
                # The historical frame may already contain precomputed forward
                # columns. If absent, the observation is skipped rather than
                # leaking future data through a re-computation at prediction time.
                ret_col = f"fwd_return_{horizon}"
                dd_col = f"fwd_drawdown_{horizon}"
                if ret_col not in self._train.columns:
                    continue
                r = row[ret_col]
                if pd.isna(r):
                    continue
                future.append(float(r))
                valid_weights.append(float(w))
                if dd_col in self._train.columns and not pd.isna(row[dd_col]):
                    drawdowns.append(float(row[dd_col]))

            if not future:
                results.append(ForecastResult(horizon, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 0, float(similarities[selected].mean()), 0.0))
                continue

            w = np.asarray(valid_weights)
            w = w / w.sum()
            r = np.asarray(future)
            order_r = np.argsort(r)
            r_sorted = r[order_r]
            w_sorted = w[order_r]
            cdf = np.cumsum(w_sorted)

            def weighted_quantile(q: float) -> float:
                return float(r_sorted[np.searchsorted(cdf, q, side="left")])

            p_up = float(w[r > 0].sum())
            sim = float(np.average(similarities[selected], weights=np.asarray(valid_weights)))
            sample_factor = min(1.0, len(r) / 30.0)
            confidence = float(np.clip(sim * sample_factor, 0.0, 1.0))
            dd_proxy = float(np.average(drawdowns, weights=w[: len(drawdowns)])) if drawdowns else np.nan

            results.append(
                ForecastResult(
                    horizon=horizon,
                    probability_up=p_up,
                    probability_down=1.0 - p_up,
                    expected_return=float(np.average(r, weights=w)),
                    median_return=weighted_quantile(0.5),
                    q10_return=weighted_quantile(0.1),
                    q90_return=weighted_quantile(0.9),
                    max_drawdown_proxy=dd_proxy,
                    sample_count=len(r),
                    similarity=sim,
                    confidence=confidence,
                )
            )
        return results


def add_forward_targets(df: pd.DataFrame, horizons: Iterable[int] = (1, 5, 20, 60)) -> pd.DataFrame:
    """Add leakage-safe forward return and drawdown targets.

    This function should be run on the full historical timeline *before* each
    walk-forward split. The forecaster itself must be fitted only on rows whose
    forecast date is earlier than the evaluation date.
    """
    out = df.copy()
    close = out["close"].astype(float)
    for h in horizons:
        out[f"fwd_return_{h}"] = close.shift(-h) / close - 1.0
        # Minimum future close relative to current close is a conservative
        # horizon drawdown proxy; it does not use any data after the horizon.
        out[f"fwd_drawdown_{h}"] = close.rolling(h + 1).min().shift(-h) / close - 1.0
    return out
