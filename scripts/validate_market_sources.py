#!/usr/bin/env python3
"""Validate provider collection freshness, schema and nonempty rows.

Collection time is not quote event time and does not establish live pricing.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

CHECKS = {
    'data/raw/brs_options_snapshot.json': 'BRS options',
    'data/raw/pypihat_tsetmc_snapshot.json': 'pypiHat/tsetmc-api',
    'data/raw/algotik_tse_snapshot.json': 'algotik_tse',
    'data/raw/tsetmc_async_snapshot.json': '5j9/tsetmc',
    'data/raw/pytsetmc_market_snapshot.json': 'pytsetmc-api',
    'data/raw/tsetmc_option_api_snapshot.json': 'TSETMC_OPTION API',
}


def row_count(payload):
    for key in ('rows', 'data', 'market_watch', 'price_data', 'stats_data', 'traders_type_data', 'calls', 'puts'):
        value = payload.get(key)
        if isinstance(value, (list, dict)) and value:
            return len(value)
    for key in ('markets', 'underlyings'):
        value = payload.get(key)
        if isinstance(value, dict):
            count = sum(row_count(child) for child in value.values()
                        if isinstance(child, dict) and child.get('status') == 'ok')
            if count:
                return count
    return 0


def validate(payload, now):
    if not isinstance(payload, dict):
        return {'ok': False, 'reason': 'invalid_schema'}
    stamp = payload.get('collected_at_utc') or payload.get('collected_at') or payload.get('generated_at') or payload.get('received_at')
    try:
        collected = datetime.fromisoformat(str(stamp).replace('Z', '+00:00'))
        age = (now - collected).total_seconds()
    except (TypeError, ValueError):
        return {'ok': False, 'reason': 'missing_or_invalid_collection_time'}
    if age < -60 or age > 7200:
        return {'ok': False, 'reason': 'stale_or_future_collection', 'age_seconds': age}
    count = row_count(payload)
    status = payload.get('status') or payload.get('data_quality', {}).get('status')
    ok = status in {'ok', 'live'} and count > 0
    return {'ok': ok, 'reason': 'ok' if ok else 'provider_failed_or_empty', 'row_count': count, 'age_seconds': age}


def main():
    now = datetime.now(timezone.utc)
    report = []
    for filename, provider in CHECKS.items():
        try:
            result = validate(json.loads(Path(filename).read_text(encoding='utf-8')), now)
        except (OSError, ValueError):
            result = {'ok': False, 'reason': 'missing_or_invalid_json'}
        report.append({'provider': provider, **result})
    count = sum(r['ok'] for r in report)
    payload = {'generated_at': now.isoformat(), 'status': 'ok' if count == len(CHECKS) else 'partial_ok' if count else 'all_providers_failed', 'ok_count': count, 'provider_count': len(CHECKS), 'report': report}
    out = Path('reports/tse_option_source_status.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if count else 1


if __name__ == '__main__':
    raise SystemExit(main())
