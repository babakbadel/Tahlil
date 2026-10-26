#!/usr/bin/env python3
"""Fetch adjusted daily BRS candles with bounded retries and per-symbol status.

Official contract: https://brsapi.ir/bourse-api-candlestick-webservice/
Keys are supplied only by the host environment. No sample API keys are used.
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from app.data.brsapi.client import BrsApiClient

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/raw/brs_history_snapshot.json'


def collect(symbol):
    try:
        payload = BrsApiClient(timeout=20).get_daily_history(symbol)
        if not isinstance(payload, dict) or payload.get('l18') != symbol or int(payload.get('type', 0)) != 3:
            raise ValueError('unexpected adjusted-history envelope')
        rows = payload.get('candle_daily_adjusted')
        if not isinstance(rows, list) or not rows:
            raise ValueError('empty adjusted-history response')
        json.dumps(rows, allow_nan=False)
        return symbol, {'status': 'ok', 'adjusted': True, 'records': rows, 'record_count': len(rows)}
    except Exception as exc:
        # Do not print upstream exception messages/URLs; they may contain keys.
        return symbol, {'status': 'unavailable', 'adjusted': True, 'records': [], 'error_type': type(exc).__name__}


def main():
    symbols = list(dict.fromkeys(s.strip() for s in os.getenv('BRS_HISTORY_SYMBOLS', 'فملی,وبملت,شپنا,خساپا,خودرو,فولاد,ذوب').split(',') if s.strip()))[:20]
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = dict(pool.map(collect, symbols))
    count = sum(value['status'] == 'ok' for value in results.values())
    payload = {'source': 'BRS', 'source_url': 'https://brsapi.ir/bourse-api-candlestick-webservice/',
               'collected_at': datetime.now(timezone.utc).isoformat(), 'price_basis': 'adjusted',
               'status': 'ok' if count == len(symbols) and count else 'partial' if count else 'unavailable', 'symbols': results}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(f'BRS history: {count}/{len(symbols)} symbols available')
    return 0  # Availability is model state; an upstream outage is not a crash.


if __name__ == '__main__':
    raise SystemExit(main())
