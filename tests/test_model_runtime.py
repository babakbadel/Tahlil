import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.forecasting.runtime import run, normalize_history, parse_date, write
from app.forecasting.historical_forecaster import HistoricalAnalogForecaster
from app.decision import DecisionEngine, DecisionHistory, Evidence

AS_OF = datetime(2030, 1, 2, 13, tzinfo=timezone.utc)


def candles(count=180, end='2030-01-01'):
    rng = np.random.default_rng(17)
    prices = 100 * np.exp(np.cumsum(rng.normal(.0005, .01, count)))
    return [{'date': stamp.date().isoformat(), 'close': float(price)} for stamp, price in zip(pd.bdate_range(end=end, periods=count), prices)]


def supply(root, records, collected=None):
    write(root / 'data/raw/brs_history_snapshot.json', {'collected_at': collected or AS_OF.isoformat(),
          'symbols': {'فملی': {'status': 'ok', 'adjusted': True, 'records': records}}})


def test_complete_history_to_forecast_decision_and_idempotent_memory(tmp_path):
    supply(tmp_path, candles())
    forecast, decision = run(tmp_path, AS_OF, ['فملی'])
    assert forecast['status'] == 'ok'
    horizons = forecast['symbols']['فملی']['horizons']
    assert [row['horizon'] for row in horizons] == [1, 5, 20]
    for row in horizons:
        assert sum(s['probability'] for s in row['scenarios']) == pytest.approx(1)
        assert row['sample_count'] >= 15
        assert row['backtest']['observations'] > 0
    assert len(decision['symbols']['فملی']['horizons']) == 3
    history = tmp_path / 'data/model_decision_history.jsonl'
    original = history.read_text()
    run(tmp_path, AS_OF, ['فملی'])
    assert history.read_text() == original
    assert len(original.splitlines()) == 3
    assert (tmp_path / 'reports/babimind_decision.md').exists()
    assert 'NaN' not in (tmp_path / 'reports/babimind_forecast.json').read_text()


@pytest.mark.parametrize('records,status', [(candles(20), 'insufficient_history'), (candles(end='2029-01-01'), 'stale')])
def test_missing_or_stale_data_never_produces_probabilities(tmp_path, records, status):
    supply(tmp_path, records)
    forecast, decision = run(tmp_path, AS_OF, ['فملی'])
    assert forecast['symbols']['فملی']['status'] == status
    assert forecast['symbols']['فملی']['horizons'] == []
    assert decision['symbols']['فملی']['action'] == 'WAIT'
    assert (tmp_path / 'data/model_decision_history.jsonl').read_text() == ''


def test_missing_source_is_connected_but_explicitly_unavailable(tmp_path):
    forecast, decision = run(tmp_path, AS_OF, ['فملی'])
    assert forecast['status'] == 'unavailable'
    assert decision['symbols']['فملی']['scenarios'] is None
    stage = json.loads((tmp_path / 'reports/babimind_model_stage_status.json').read_text())
    assert stage['forecasting']['connected'] is True
    assert stage['forecasting']['status'] == 'unavailable'


def test_last_known_good_history_survives_provider_outage(tmp_path):
    supply(tmp_path, candles())
    run(tmp_path, AS_OF, ['فملی'])
    (tmp_path / 'data/raw/brs_history_snapshot.json').write_text('{}')
    forecast, _ = run(tmp_path, AS_OF, ['فملی'])
    assert forecast['symbols']['فملی']['cached'] is True
    assert forecast['symbols']['فملی']['status'] == 'ok'


def test_future_and_incomplete_candles_are_excluded():
    as_of = datetime(2030, 1, 2, 6, tzinfo=timezone.utc)
    frame = normalize_history([{'date': '2030-01-01', 'close': 10}, {'date': '2030-01-02', 'close': 20}, {'date': '2030-01-03', 'close': 30}], as_of)
    assert len(frame) == 1
    assert frame.iloc[0]['close'] == 10


def test_jalali_dates_are_validated():
    assert parse_date('۱۴۰۴/۰۱/۰۱').isoformat() == '2025-03-21'
    with pytest.raises(ValueError):
        parse_date('1404-13-01')


def test_conflicting_prices_and_nan_are_rejected():
    for rows in ([{'date': '2030-01-01', 'close': float('nan')}], [{'date': '2030-01-01', 'close': 10}, {'date': '2030-01-01', 'close': 20}]):
        with pytest.raises(ValueError):
            normalize_history(rows, AS_OF)


def test_runtime_labels_have_matured_at_each_forecast(tmp_path, monkeypatch):
    records = candles()
    positions = {pd.Timestamp(row['date']).date(): i for i, row in enumerate(records)}
    original = HistoricalAnalogForecaster.predict

    def checked(self, current, horizons, **kwargs):
        for horizon in horizons:
            assert all(positions[date] + horizon < positions[current['date']] for date in self._train['date'])
        return original(self, current, horizons, **kwargs)

    monkeypatch.setattr(HistoricalAnalogForecaster, 'predict', checked)
    supply(tmp_path, records)
    run(tmp_path, AS_OF, ['فملی'])


def test_decisions_reject_future_evidence_and_invalid_probabilities(tmp_path):
    engine = DecisionEngine(history=DecisionHistory(tmp_path / 'history.jsonl'))
    with pytest.raises(ValueError, match='future evidence'):
        engine.predict(title='test', decision_target='test', as_of=AS_OF.isoformat(), evidence=[Evidence('future', observed_at='2031-01-01')])
    for probability in (-1, float('nan'), 0, .5):
        with pytest.raises(ValueError, match='probabilities'):
            engine.predict(title='test', decision_target='test', as_of=AS_OF.isoformat(), scenarios=[{'label': 'invalid', 'probability': probability}])


@pytest.mark.parametrize('records', [None, 'not a series', [1], [{'date': '2030-01-01', 'close': True}]])
def test_malformed_candle_shapes_do_not_enter_forecasts(records):
    with pytest.raises(ValueError):
        normalize_history(records, AS_OF)


def test_malformed_provider_container_is_reported_as_unavailable(tmp_path):
    write(tmp_path / 'data/raw/brs_history_snapshot.json', {'symbols': None})
    forecast, _ = run(tmp_path, AS_OF, ['فملی'])
    assert forecast['status'] == 'unavailable'
