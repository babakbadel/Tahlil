"""Observation-backed factor coverage. Endpoint health is not factor evidence."""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = ('Available', 'Partial', 'Stale', 'Unavailable')
REQUIRED = ('source', 'timestamp', 'raw_value', 'normalized_score', 'confidence', 'max_age_seconds')


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be an ISO timestamp with timezone')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timestamp requires timezone')
    return result


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_catalog(catalog):
    factors = catalog['factors']
    ids = [f['id'] for f in factors]
    if not ids or any(not isinstance(i, str) or not i.strip() for i in ids):
        raise ValueError('factor IDs must be nonempty strings')
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate factor IDs')
    if catalog.get('factor_count') != len(ids):
        raise ValueError('factor_count does not match catalog')
    return factors


def evaluate(factor, observation, now):
    row = {
        'factor_id': factor['id'], 'name': factor['name'],
        'group': factor.get('cluster', 'unclassified'),
        'candidate_sources': factor.get('sources', []),
        'source': None, 'timestamp': None, 'raw_value': None,
        'normalized_score': None, 'freshness': None, 'confidence': None,
        'state': 'Unavailable', 'status': 'Unavailable',
        'signal_weight': 0.0, 'eligible_for_aggregation': False,
        'retry_next_run': True, 'error_reason': 'no_observation',
    }
    if observation is None:
        return row
    for key in REQUIRED:
        row[key] = observation.get(key)
    for key in REQUIRED:
        if isinstance(row.get(key), float) and not math.isfinite(row[key]):
            row[key] = None
    # Transport/parse failures never become observations, even if cached values exist.
    if observation.get('state', '').lower() in {'error', 'unavailable', 'timeout'}:
        row['error_reason'] = observation.get('error_reason') or 'upstream_failure'
        return row
    if observation.get('state', 'ok').lower() not in {'ok', 'available', 'partial'}:
        row.update(state='Partial', status='Partial', error_reason='unknown_upstream_state')
        return row
    missing = [k for k in REQUIRED if row.get(k) is None]
    if missing:
        row.update(state='Partial', status='Partial', error_reason='missing_fields:' + ','.join(missing))
        return row
    try:
        stamp = timestamp(row['timestamp'])
        age = (now - stamp).total_seconds()
        max_age = observation['max_age_seconds']
        if not isinstance(row['source'], str) or row['source'] not in factor.get('sources', []):
            raise ValueError('source_not_mapped_to_factor')
        if not finite(max_age) or max_age <= 0:
            raise ValueError('invalid_max_age_seconds')
        if not finite(row['raw_value']) or not finite(row['normalized_score']):
            raise ValueError('invalid_numeric_value')
        if not finite(row['confidence']) or not 0 <= row['confidence'] <= 1:
            raise ValueError('invalid_confidence')
        if age < 0:
            raise ValueError('future_observation')
        row['freshness'] = round(2 ** (-age / max_age), 6)
        if age > max_age:
            row.update(state='Stale', status='Stale', error_reason='observation_expired')
        elif observation.get('state', '').lower() == 'partial':
            row.update(state='Partial', status='Partial', error_reason='upstream_partial')
        elif row['confidence'] == 0:
            row.update(state='Partial', status='Partial', error_reason='zero_confidence')
        else:
            row.update(state='Available', status='Available', error_reason=None,
                       signal_weight=row['confidence'] * row['freshness'],
                       eligible_for_aggregation=True, retry_next_run=False)
    except (ValueError, TypeError, OverflowError) as exc:
        row.update(state='Partial', status='Partial', error_reason=str(exc))
    # JSON null preserves unusable numerical observations without emitting NaN/Infinity.
    for key in ('raw_value', 'normalized_score', 'confidence', 'max_age_seconds'):
        if isinstance(row.get(key), float) and not math.isfinite(row[key]):
            row[key] = None
    return row


def build_report(catalog, observations, now):
    factors = validate_catalog(catalog)
    if now.tzinfo is None:
        raise ValueError('as_of requires timezone')
    indexed = {}
    known = {f['id'] for f in factors}
    for item in observations:
        fid = item['factor_id']
        if fid not in known:
            raise ValueError('unknown factor_id: ' + str(fid))
        if fid in indexed:
            raise ValueError('duplicate observation for factor: ' + fid)
        indexed[fid] = item
    records = [evaluate(f, indexed.get(f['id']), now) for f in factors]
    counts = {s: sum(r['state'] == s for r in records) for s in STATES}
    available = counts['Available']
    return {
        'schema_version': 2, 'generated_at': now.isoformat(), 'as_of': now.isoformat(),
        'catalog_version': catalog.get('version'), 'missing_data_policy': 'MISSING_IS_NOT_ZERO',
        'method': 'validated_factor_observations', 'factor_count': len(factors),
        'target_factor_count_minimum': 501, 'target_met': len(factors) > 500,
        'counts': counts, 'covered': available,
        'coverage_percent': round(100 * available / len(factors), 2), 'records': records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'config/babimind_factors.json')
    parser.add_argument('--observations', type=Path, default=ROOT / 'reports/babimind_factor_observations.json')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'reports')
    parser.add_argument('--as-of', type=timestamp)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding='utf-8'))
    observations = json.loads(args.observations.read_text(encoding='utf-8'))['observations'] if args.observations.exists() else []
    result = build_report(catalog, observations, args.as_of or datetime.now(timezone.utc))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'babimind_factor_coverage.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    lines = ['# BabiMind Factor Coverage', '', f"As of: {result['as_of']}",
             f"Catalog factors: {result['factor_count']}; target >500 met: {result['target_met']}",
             f"Counts: {result['counts']}", '',
             'Only validated, fresh observations count as Available. Endpoint health is not factor coverage.', '',
             '| Factor | State | Source | Timestamp | Reason |', '|---|---|---|---|---|']
    def cell(value):
        return str(value if value is not None else '-').replace('|', '\\|').replace('\n', ' ')
    lines.extend('| ' + ' | '.join(cell(r[k]) for k in ('factor_id','state','source','timestamp','error_reason')) + ' |' for r in result['records'])
    (args.output_dir / 'babimind_factor_coverage.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('factor_count','counts','coverage_percent','target_met')}))


if __name__ == '__main__':
    main()
