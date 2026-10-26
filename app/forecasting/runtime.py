"""Daily, evidence-backed model runtime. No network access and no LLM dependency."""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import jdatetime
import numpy as np
import pandas as pd

from app.decision import DecisionEngine, DecisionHistory, Evidence
from .historical_forecaster import HistoricalAnalogForecaster, add_forward_targets
from .walk_forward import walk_forward_backtest

VERSION = '1.0'
FEATURES = ['return_1', 'return_5', 'return_20', 'volatility_20']
HORIZONS = (1, 5, 20)
TEHRAN = ZoneInfo('Asia/Tehran')
MIN_ROWS = 120


def read(path, default=None):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else (default or {})
    except (OSError, ValueError):
        return default or {}


def clean(value):
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    return value


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(payload), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def parse_date(value):
    text = str(value).strip().translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')).replace('/', '-')
    if len(text) == 8 and text.isdigit():
        text = f'{text[:4]}-{text[4:6]}-{text[6:]}'
    parts = text[:10].split('-')
    if len(parts) != 3:
        raise ValueError('missing candle date')
    year, month, day = map(int, parts)
    if 1300 <= year <= 1499:
        return jdatetime.date(year, month, day).togregorian()
    return datetime(year, month, day).date()


def normalize_history(records, as_of):
    """Validate one adjusted price series before computing any features."""
    by_date = {}
    if not isinstance(records, list):
        raise ValueError('history must be a list of candles')
    local = as_of.astimezone(TEHRAN)
    for row in records:
        if not isinstance(row, dict):
            raise ValueError('invalid candle record')
        observed = parse_date(row.get('date') or row.get('Date') or row.get('J-Date'))
        if observed > local.date() or (observed == local.date() and local.time() < time(12, 40)):
            continue  # A partial current session is not a completed daily candle.
        price = row.get('close', row.get('Adj Close'))
        if price is None or isinstance(price, bool):
            raise ValueError('missing adjusted close')
        price = float(price)
        if not math.isfinite(price) or price <= 0:
            raise ValueError('invalid adjusted close')
        if observed in by_date and by_date[observed] != price:
            raise ValueError('conflicting prices for the same date')
        by_date[observed] = price
    if not by_date:
        raise ValueError('no completed daily observations')
    frame = pd.DataFrame(sorted(by_date.items()), columns=['date', 'close']).tail(1260).reset_index(drop=True)
    return frame


def feature_panel(frame):
    out = frame.copy()
    returns = out['close'].pct_change(fill_method=None)
    for horizon in (1, 5, 20):
        out[f'return_{horizon}'] = out['close'].pct_change(horizon, fill_method=None)
    out['volatility_20'] = returns.rolling(20).std(ddof=0)
    return out.dropna(subset=FEATURES).reset_index(drop=True)


def forecast_series(frame, as_of):
    last_date = frame.iloc[-1]['date']
    age = (as_of.astimezone(TEHRAN).date() - last_date).days
    if age > 7:
        return {'status': 'stale', 'observation_date': last_date.isoformat(), 'age_days': age, 'reason': 'last completed price is older than seven calendar days', 'horizons': []}
    if len(frame) < MIN_ROWS:
        return {'status': 'insufficient_history', 'observation_date': last_date.isoformat(), 'row_count': len(frame), 'required_rows': MIN_ROWS, 'horizons': []}
    features = feature_panel(frame)
    current = features.iloc[-1]
    targets = add_forward_targets(features, HORIZONS)
    results = []
    for horizon in HORIZONS:
        # Labels must have finished strictly before the latest observation.
        train = targets.iloc[:len(targets) - 1 - horizon].copy()
        model = HistoricalAnalogForecaster(top_k=40).fit(train, FEATURES)
        result = model.predict(current, (horizon,), neutral_band=.005)[0]
        _, summary = walk_forward_backtest(features, FEATURES, horizon=horizon,
                                          train_window=min(252, max(60, len(features) // 2)), step=10)
        item = result.as_dict()
        item['status'] = 'ok' if result.sample_count >= 15 else 'insufficient_analogs'
        item['backtest'] = summary.as_dict()
        item['price_interval_q10_q90'] = [float(current['close']) * (1 + result.q10_return), float(current['close']) * (1 + result.q90_return)]
        item['scenarios'] = [
            {'scenario_id': 'bullish', 'label': 'بازده بیشتر از مثبت نیم درصد', 'probability': result.probability_up, 'expected_market_effect': 'bullish'},
            {'scenario_id': 'neutral', 'label': 'بازده بین منفی و مثبت نیم درصد', 'probability': result.probability_flat, 'expected_market_effect': 'neutral'},
            {'scenario_id': 'bearish', 'label': 'بازده کمتر از منفی نیم درصد', 'probability': result.probability_down, 'expected_market_effect': 'bearish'},
        ]
        results.append(item)
    return {'status': 'ok' if all(r['status'] == 'ok' for r in results) else 'partial',
            'observation_date': last_date.isoformat(), 'age_days': age, 'row_count': len(frame), 'feature_rows': len(features),
            'spot_adjusted': float(current['close']), 'horizon_unit': 'observed_trading_sessions',
            'price_basis': 'adjusted', 'neutral_band': .005, 'horizons': results}


def run(root: Path, as_of: datetime, symbols=None):
    if as_of.tzinfo is None:
        raise ValueError('as_of must include a timezone')
    brs = read(root / 'data/raw/brs_history_snapshot.json')
    finpy = read(root / 'data/raw/finpy_tse_snapshot.json')
    brs_symbols = brs.get('symbols') if isinstance(brs.get('symbols'), dict) else {}
    finpy_symbols = finpy.get('symbols') if isinstance(finpy.get('symbols'), dict) else {}
    symbols = symbols or sorted(set(brs_symbols) | set(finpy_symbols)) or ['فملی', 'وبملت', 'شپنا', 'خساپا', 'خودرو', 'فولاد', 'ذوب']
    history = DecisionHistory(root / 'data/model_decision_history.jsonl')
    engine = DecisionEngine(history=history)
    forecasts, decisions = {}, {}
    for symbol in symbols:
        if not isinstance(symbol, str) or not re.fullmatch(r'[\w\u200c .-]{1,60}', symbol) or symbol in {'.', '..'}:
            raise ValueError('invalid symbol identifier')
        cache_path = root / 'data/history' / f'{symbol}.json'
        cached = read(cache_path)
        brs_item = brs_symbols.get(symbol, {})
        brs_item = brs_item if isinstance(brs_item, dict) else {}
        finpy_item = finpy_symbols.get(symbol, {})
        finpy_rows = finpy_item.get('price_history') if isinstance(finpy_item, dict) else []
        finpy_rows = finpy_rows if isinstance(finpy_rows, list) and all(isinstance(row, dict) for row in finpy_rows) else []
        candidates = []
        if brs_item.get('status') == 'ok' and brs_item.get('adjusted') is True:
            candidates.append(('BRS', brs_item.get('records', []), brs.get('collected_at'), False))
        if finpy_rows and any('Adj Close' in row for row in finpy_rows):
            # FinPy rows explicitly use Adj Close, never a raw Close alias.
            candidates.append(('FinPy-TSE', [{'date': row.get('Date') or row.get('J-Date'), 'close': row.get('Adj Close')} for row in finpy_rows], finpy.get('collected_at'), False))
        if cached.get('price_basis') == 'adjusted':
            candidates.append((cached.get('source', 'cache'), cached.get('records', []), cached.get('collected_at'), True))
        valid, errors = [], []
        for source, records, collected_at, is_cached in candidates:
            try:
                collected = datetime.fromisoformat(str(collected_at).replace('Z', '+00:00'))
                if collected.tzinfo is None:
                    collected = collected.replace(tzinfo=TEHRAN)
                if collected > as_of:
                    raise ValueError('future source collection')
                frame = normalize_history(records, as_of)
                valid.append((frame.iloc[-1]['date'], len(frame), source, frame, collected.isoformat(), is_cached))
            except (ValueError, TypeError, KeyError, OverflowError) as exc:
                errors.append({'source': source, 'reason': str(exc)})
        if not valid:
            forecasts[symbol] = {'status': 'unavailable', 'reason': 'no validated adjusted price history', 'errors': errors, 'horizons': []}
            decisions[symbol] = {'action': 'WAIT', 'status': 'blocked', 'reason': forecasts[symbol]['reason'], 'scenarios': None}
            continue
        _, _, source, frame, collected_at, is_cached = max(valid, key=lambda item: (item[0], item[1], not item[5]))
        forecast = forecast_series(frame, as_of)
        forecast.update(source=source, source_collected_at=collected_at, cached=is_cached, input_errors=errors)
        forecasts[symbol] = forecast
        if not is_cached:
            write(cache_path, {'source': source, 'collected_at': collected_at, 'price_basis': 'adjusted',
                              'records': [{'date': row.date.isoformat(), 'close': row.close} for row in frame.itertuples()]})
        decision_rows = []
        for item in forecast['horizons']:
            if item['status'] != 'ok':
                continue
            fingerprint = hashlib.sha256((VERSION + symbol + frame.to_csv(index=False) + str(item['horizon'])).encode()).hexdigest()[:24]
            evidence = Evidence(evidence_id='prices-' + fingerprint, source_url='data/history/' + symbol + '.json',
                                observed_at=collected_at, confidence=item['confidence'], summary='Validated adjusted daily prices; ' + forecast['observation_date'])
            record = engine.predict(decision_id='model-' + fingerprint, title=symbol + ' historical analog forecast',
                                    decision_target=symbol + ':' + str(item['horizon']), as_of=as_of.isoformat(), evidence=[evidence],
                                    scenarios=item['scenarios'], tags=['production', 'historical_analog'],
                                    notes='Empirical historical scenarios; backtest is diagnostic, not a validated trading strategy.')
            best = max(item['scenarios'], key=lambda row: row['probability'])
            action = 'WAIT' if best['scenario_id'] == 'neutral' or best['probability'] < .6 else 'REVIEW_' + best['scenario_id'].upper()
            decision_rows.append({'decision_id': record.decision_id, 'horizon': item['horizon'], 'action': action,
                                  'scenarios': [row.as_dict() for row in record.predictions], 'confidence': item['confidence'], 'backtest': item['backtest']})
        decisions[symbol] = {'status': 'ok' if decision_rows else 'blocked', 'action': 'REVIEW_ONLY' if decision_rows else 'WAIT',
                             'reason': None if decision_rows else forecast.get('reason', 'insufficient historical analogs'), 'horizons': decision_rows}
    common = {'model': 'BabiMind', 'runtime_version': VERSION, 'generated_at': as_of.isoformat(), 'missing_data_policy': 'MISSING_IS_NOT_ZERO'}
    successful = sum(row['status'] == 'ok' for row in forecasts.values())
    status = 'ok' if successful == len(forecasts) else 'partial' if successful else 'unavailable'
    forecast_report = {**common, 'status': status, 'symbols': forecasts}
    decision_report = {**common, 'status': status, 'policy': 'review_only_no_automatic_orders', 'symbols': decisions}
    write(root / 'reports/babimind_forecast.json', forecast_report)
    write(root / 'reports/babimind_decision.json', decision_report)
    lines = ['# خروجی مدل BabiMind', '', 'سناریوها از مشابه‌های تاریخی استخراج می‌شوند. این خروجی دستور معامله نیست.', '',
             '| نماد | افق | صعود | خنثی | نزول | وضعیت / اقدام | تاریخ داده |',
             '|---|---:|---:|---:|---:|---|---|']
    for symbol, item in forecasts.items():
        if not item['horizons']:
            lines.append(f"| {symbol} | — | — | — | — | WAIT: {item.get('reason', item['status'])} | {item.get('observation_date', '—')} |")
        for horizon in item['horizons']:
            probabilities = [horizon.get(key) for key in ('probability_up', 'probability_flat', 'probability_down')]
            formatted = ['—' if value is None or not math.isfinite(value) else f'{value:.1%}' for value in probabilities]
            lines.append(f"| {symbol} | {horizon['horizon']} | {' | '.join(formatted)} | {horizon['status']} / REVIEW_ONLY | {item['observation_date']} |")
    (root / 'reports/babimind_decision.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    write(root / 'reports/babimind_model_stage_status.json', {**common, 'status': status,
          'forecasting': {'connected': True, 'status': status, 'available_symbols': successful, 'symbol_count': len(forecasts)},
          'decision': {'connected': True, 'status': status, 'history': 'data/model_decision_history.jsonl'}})
    return forecast_report, decision_report
