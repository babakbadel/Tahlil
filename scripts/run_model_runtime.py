#!/usr/bin/env python3
"""Run the production forecast -> decision -> immutable-history path."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
from app.forecasting.runtime import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--as-of')
    args = parser.parse_args()
    as_of = datetime.fromisoformat(args.as_of.replace('Z', '+00:00')) if args.as_of else datetime.now(timezone.utc)
    forecast, _ = run(Path(__file__).resolve().parents[1], as_of)
    print('BabiMind forecast/decision runtime:', forecast['status'])
    for symbol, item in forecast['symbols'].items():
        print(symbol, item['status'], 'rows=', item.get('row_count', 0), 'observation=', item.get('observation_date'), 'source=', item.get('source'))


if __name__ == '__main__':
    main()
