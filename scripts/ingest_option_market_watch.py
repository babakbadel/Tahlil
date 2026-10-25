"""Normalize data/latest/OptionMarketWatch.csv for BabiMind.

The source is the repository's own OptionMarketWatch snapshot.  The CSV has
Persian headers and duplicated column names for the option and underlying
sides, so this loader splits the call, shared underlying, and put sections by header.  Missing IV/Greeks/timestamps are preserved as data gaps rather than
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

    # The export contains paired contracts: call columns, shared underlying/
    # dates, then put columns in reverse order. Match section headers instead
    # of assuming 43 columns or interpreting underlying prices as symbols.
    headers = [value.strip().strip("<>").strip() for value in rows[0]]
    try:
        underlying_index = headers.index("نماد پایه")
        end_index = headers.index("تاریخ پایان")
    except ValueError as exc:
        raise ValueError("Unsupported OptionMarketWatch headers") from exc

    def section(row, start, stop):
        result = {}
        for index in range(start, stop):
            if index < len(row):
                result.setdefault(headers[index], row[index].strip())
        return result

    records: list[dict[str, Any]] = []
    for row in rows[1:]:
        if not row:
            continue
        if len(row) != len(headers):
            raise ValueError(f"Malformed OptionMarketWatch row: {len(row)} columns, expected {len(headers)}")
        shared = section(row, underlying_index, end_index + 1)
        primary = section(row, 0, underlying_index)
        counterpart = section(row, end_index + 1, len(headers))
        for side in (primary, counterpart):
            symbol = side.get("نماد", "")
            if not symbol or symbol == "-":
                continue
            option_type = "call" if symbol.startswith("ض") else "put" if symbol.startswith("ط") else "unknown"
            if option_type == "unknown":
                continue
            records.append({
                "symbol": symbol,
                "option_type": option_type,
                "status": side.get("وضعیت در سود بودن نماد"),
                "volume": int_num(side.get("حجم")),
                "trade_count": int_num(side.get("تعداد")),
                "value": num(side.get("ارزش")),
                "notional_value": num(side.get("ارزش مفهومی")),
                "open_interest": int_num(side.get("موقعیت های باز")),
                "change_pct": num(side.get("درصد تغییر")),
                "close": num(side.get("قیمت پایانی")),
                "last": num(side.get("قیمت آخرین معامله")),
                "bid_volume": int_num(side.get("حجم خرید")),
                "bid": num(side.get("قیمت خرید")),
                "ask": num(side.get("قیمت فروش")),
                "ask_volume": int_num(side.get("حجم فروش")),
                "contract_size": int_num(primary.get("اندازه قرارداد")),
                "strike": num(primary.get("قیمت اعمال")),
                "days_to_expiry": int_num(primary.get("روز باقی مانده تا سررسید")),
                "underlying": shared.get("نماد پایه"),
                "underlying_close": num(shared.get("پایانی دارایی پایه")),
                "underlying_last": num(shared.get("آخرین معامله دارایی پایه")),
                "start_date": shared.get("تاریخ شروع"),
                "end_date": shared.get("تاریخ پایان"),
                "data_gaps": ["iv", "delta", "gamma", "theta", "vega", "quote_timestamp"],
            })
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
