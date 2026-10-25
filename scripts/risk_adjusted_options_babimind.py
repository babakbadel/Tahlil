#!/usr/bin/env python3
"""Heuristic stress-scenario ranking; never a calibrated trade signal."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'reports/options_babimind_scenario_ranked.json'
OUTJ = ROOT / 'reports/options_babimind_risk_adjusted.json'
OUTM = ROOT / 'reports/options_babimind_risk_adjusted.md'


def n(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None


def calc(row):
    base = n(row.get('babimind_scenario_score', row.get('score'))) or 0
    scenario = row.get('scenario_pnl_pct')
    if isinstance(scenario, dict):
        pnl = [n(value) for value in scenario.values()]
    else:
        pnl = [n(row.get(f'pl_{direction}_{move}')) for direction in ('minus', 'plus') for move in (5, 10, 20)]
    gains = [value for value in pnl if value is not None and value > 0]
    losses = [-value for value in pnl if value is not None and value < 0]
    rr = max(gains) / max(losses) if gains and losses else None
    parts = [base]
    iv, theta, delta, days, price = [n(row.get(key)) for key in ('iv', 'theta', 'delta', 'days_to_expiry', 'price')]
    if days is None:
        days = n(row.get('days'))
    if rr is not None:
        parts.append(100 * rr / (1 + rr))
    if iv is not None:
        parts.append(max(0, 100 - min(100, iv * 100)))
    if theta is not None and price is not None and price > 0:
        parts.append(max(0, 100 - min(100, abs(theta) / price * 36500)))
    if delta is not None:
        parts.append(max(0, 100 - abs(abs(delta) - .55) * 100))
    if days is not None:
        parts.append(max(0, 100 - abs(days - 45) * 1.2))
    return round(.65 * sum(parts) / len(parts) + .35 * base, 2), rr


def main():
    data = json.loads(SRC.read_text(encoding='utf-8'))
    rows = data if isinstance(data, list) else data.get('records', data.get('contracts', data.get('results', [])))
    out = []
    for row in rows:
        score, rr = calc(row)
        out.append({**row, 'risk_adjusted_score': score, 'risk_reward_ratio': round(rr, 3) if rr is not None else None,
                    'decision': 'REVIEW_REQUIRED', 'ranking_policy': 'scenario_stress_test_not_a_trade_signal'})
    out.sort(key=lambda row: row['risk_adjusted_score'], reverse=True)
    for rank, row in enumerate(out, 1):
        row['risk_adjusted_rank'] = rank
    metadata = data if isinstance(data, dict) else {}
    payload = {'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'status': metadata.get('status', 'partial'),
               'source_event_time': metadata.get('source_event_time'), 'record_count': len(out),
               'ranking_policy': 'scenario_stress_test_not_a_trade_signal', 'contracts': out}
    OUTJ.parent.mkdir(parents=True, exist_ok=True)
    OUTJ.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    columns = ['risk_adjusted_rank', 'underlying', 'symbol', 'option_type', 'risk_adjusted_score', 'price', 'strike', 'iv', 'delta', 'theta', 'days_to_expiry', 'risk_reward_ratio']
    lines = ['# BabiMind Risk-Adjusted Option Ranking', '', 'Stress scenarios only; not expected returns or a trade recommendation.', '',
             f'Contracts ranked: {len(out)}', '', '| ' + ' | '.join(columns) + ' |', '|' + '---|' * len(columns)]
    for row in out:
        lines.append('| ' + ' | '.join('-' if row.get(key) is None else str(row[key]) for key in columns) + ' |')
    OUTM.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'risk-ranked {len(out)} contracts')


if __name__ == '__main__':
    main()
