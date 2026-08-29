"""Normalize data/latest/OptionMarketWatch.csv for BabiMind.

The source is the repository's own OptionMarketWatch snapshot.  The CSV has
Persian headers and duplicated column names for the option and underlying
sides, so this loader intentionally uses column positions instead of a dict
reader.  Missing IV/Greeks/timestamps are preserved as data gaps rather than
invented.
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/latest/OptionMarketWatch.csv"
OUTPUT = ROOT / "data/raw/option_market_watch_snapshot.json"
REPORT = ROOT / "reports/option_market_watch_summary.json"


def num(value: str) -> float | None:
    if value is None:
        return None
    value = value.strip().replace(",", "")
    if not value or value in {"-", "null", "None"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def int_num(value: str) -> int | None:
    n = num(value)
    return int(n) if n is not None else None


def parse_rows() -> list[dict[str, Any]]:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    if len(rows) < 2:
        return []

    # Current OptionMarketWatch schema: 43 columns, option side first,
    # underlying side after the option expiry/date fields.
    records: list[dict[str, Any]] = []
    for row in rows[1:]:
        if not row or not row[0].strip() or len(row) < 43:
            continue
        symbol = row[0].strip()
        underlying = row[20].strip()
        option_type = "put" if symbol.startswith("ض") else "call" if symbol.startswith("ط") else "unknown"
        records.append(
            {
                "symbol": symbol,
                "option_type": option_type,
                "status": row[1].strip(),
                "volume": int_num(row[2]),
                "trade_count": int_num(row[3]),
                "value": num(row[4]),
                "notional_value": num(row[5]),
                "open_interest": int_num(row[6]),
                "change_pct": num(row[7]),
                "close": num(row[8]),
                "last": num(row[10]),
                "bid_volume": int_num(row[12]),
                "bid": num(row[13]),
                "ask": num(row[14]),
                "ask_volume": int_num(row[15]),
                "contract_size": int_num(row[16]),
                "strike": num(row[17]),
                "days_to_expiry": int_num(row[18]),
                "underlying": underlying,
                "underlying_close": num(row[21]),
                "underlying_change_pct": num(row[22]),
                "underlying_last": num(row[23]),
                "start_date": row[25].strip(),
                "end_date": row[26].strip(),
                "underlying_ask_volume": int_num(row[27]),
                "underlying_ask": num(row[28]),
                "underlying_bid": num(row[29]),
                "underlying_bid_volume": int_num(row[30]),
                "underlying_change_pct_2": num(row[31]),
                "underlying_last_2": num(row[32]),
                "underlying_change_pct_3": num(row[33]),
                "underlying_close_2": num(row[34]),
                "underlying_change_pct_4": num(row[35]),
                "underlying_open_interest": int_num(row[36]),
                "underlying_notional_value": num(row[37]),
                "underlying_value": num(row[38]),
                "underlying_trade_count": int_num(row[39]),
                "underlying_volume": int_num(row[40]),
                "underlying_status": row[41].strip(),
                "underlying_symbol": row[42].strip(),
                "data_gaps": ["iv", "delta", "gamma", "theta", "vega", "quote_timestamp"],
            }
        )
    return records


def build_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_underlying: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "contracts": 0, "calls": 0, "puts": 0, "volume": 0,
        "open_interest": 0, "value": 0.0, "notional_value": 0.0,
        "max_oi_symbol": None, "max_oi": 0,
    })
    for r in records:
        s = by_underlying[r["underlying"]]
        s["contracts"] += 1
        s["calls"] += int(r["option_type"] == "call")
        s["puts"] += int(r["option_type"] == "put")
        s["volume"] += r["volume"] or 0
        s["open_interest"] += r["open_interest"] or 0
        s["value"] += r["value"] or 0.0
        s["notional_value"] += r["notional_value"] or 0.0
        if (r["open_interest"] or 0) > s["max_oi"]:
            s["max_oi"] = r["open_interest"] or 0
            s["max_oi_symbol"] = r["symbol"]

    liquid = sorted(records, key=lambda r: ((r["volume"] or 0), (r["open_interest"] or 0)), reverse=True)[:20]
    return {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_type": "repository_snapshot",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "underlying_count": len(by_underlying),
        "underlyings": dict(sorted(by_underlying.items())),
        "top_liquidity": [
            {
                "symbol": r["symbol"],
                "underlying": r["underlying"],
                "option_type": r["option_type"],
                "strike": r["strike"],
                "days_to_expiry": r["days_to_expiry"],
                "last": r["last"],
                "volume": r["volume"],
                "open_interest": r["open_interest"],
                "bid": r["bid"],
                "ask": r["ask"],
                "status": r["status"],
            }
            for r in liquid
        ],
        "data_quality": {
            "iv_available": False,
            "greeks_available": False,
            "quote_timestamp_available": False,
            "warning": "This snapshot is suitable for option-chain structure, liquidity and OI analysis; final Greek/IV ranking requires a synchronized Greek source.",
        },
    }


def main() -> None:
    records = parse_rows()
    summary = build_summary(records)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"records": records, "summary": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OptionMarketWatch: {len(records)} contracts -> {OUTPUT}")


if __name__ == "__main__":
    main()
