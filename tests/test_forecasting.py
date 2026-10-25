import numpy as np
import pandas as pd
import pytest

from app.forecasting.historical_forecaster import HistoricalAnalogForecaster, add_forward_targets
from app.forecasting.walk_forward import walk_forward_backtest


def test_missing_forward_labels_do_not_crash_prediction():
    frame = pd.DataFrame({'close': range(100, 120), 'feature': np.linspace(0, 1, 20)})
    frame = add_forward_targets(frame, (5,))
    frame.loc[2:4, 'fwd_drawdown_5'] = np.nan
    result = HistoricalAnalogForecaster(top_k=20, min_similarity=0).fit(frame, ['feature']).predict(frame.iloc[10], (5,))[0]
    assert result.sample_count == 15
    assert np.isfinite(result.similarity)
    assert np.isfinite(result.max_drawdown_proxy)


def test_walk_forward_never_exposes_unmatured_labels(monkeypatch):
    frame = pd.DataFrame({'date': range(100), 'close': np.arange(100, 200), 'feature': np.arange(100)})
    original_predict = HistoricalAnalogForecaster.predict

    def checked_predict(self, current, horizons):
        horizon = horizons[0]
        assert (self._train['date'] + horizon < current['date']).all()
        return original_predict(self, current, horizons)

    monkeypatch.setattr(HistoricalAnalogForecaster, 'predict', checked_predict)
    _, summary = walk_forward_backtest(frame, ['feature'], horizon=5, train_window=50)
    assert summary.observations > 0
    assert np.isfinite(summary.brier_score)
