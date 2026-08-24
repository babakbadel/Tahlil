"""Backfill TSETMC daily history for BabiMind forecasting.

Phase 1 focuses on the total/equal-weighted indices. Symbol backfill is sharded
so GitHub Actions can safely build the multi-year panel without one oversized job.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import random
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = "https://cdn.tsetmc.com/api"
OLD_BASE = "http://old.tsetmc.com/tsev2/chart/data"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36 Tahlil-BabiMind/1.0",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.tsetmc.com/",
    "Connection": "keep-alive",
}
INDEX_CODES = {
    "tedpix": "32097828820363860",
    "equal_weighted": "67130298613737946",
}


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=4)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(HEADERS)
    return session


SESSION = make_session()


def get_json(url: str, attempts: int = 4) -> dict[str, Any]:
    last: Exception | None = None
    for n in range(attempts):
        try:
            r = SESSION.get(url, timeout=(12, 45))
            r.raise_for_status()
            text = r.text.lstrip("\ufeff \t\r\n")
            if not text.startswith("{"):
                raise RuntimeError("non-JSON response from TSETMC")
            return r.json()
        except Exception as exc:
            last = exc
            if n + 1 < attempts:
                delay = min(20.0, 2.0 ** n) + random.uniform(0.2, 1.0)
                print(f"RETRY {n + 1}/{attempts - 1} after {type(exc).__name__}: sleep={delay:.1f}s url={url}", flush=True)
                time.sleep(delay)
    raise RuntimeError(f"TSETMC request failed after {attempts} attempts: {url}: {last}")


def index_history_old(code: str) -> pd.DataFrame:
    """Fallback index history via the older CSV chart endpoint.

    The CDN JSON endpoint can be unreachable from GitHub-hosted runners. The
    older IndexFinancial endpoint is a documented TSETMC fallback and returns
    semicolon-separated rows: date,pmax,pmin,pf,pl,tvol,pc.
    """
    url = f"{OLD_BASE}/IndexFinancial.aspx?i={code}&t=ph"
    r = SESSION.get(url, timeout=(12, 60), headers={**HEADERS, "Accept": "text/csv,text/plain,*/*"})
    r.raise_for_status()
    text = r.text.lstrip("\ufeff \t\r\n")
    rows = []
    for raw in text.replace("\r", "").replace("\n", "").split(";"):
        parts = raw.strip().split(",")
        if len(parts) < 7:
            continue
        rows.append((parts[0], parts[6]))
    if not rows:
        raise RuntimeError(f"old TSETMC index endpoint returned no rows for {code}")
    out = pd.DataFrame(rows, columns=["date", "close"])
    out["date"] = pd.to_datetime(out["date"].astype(str), format="%Y%m%d", errors="coerce")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    return out.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)


def index_history(code: str) -> pd.DataFrame:
    try:
        payload = get_json(f"{BASE}/Index/GetIndexB2History/{code}", attempts=2)
        rows = payload.get("indexB2", [])
        if rows:
            df = pd.DataFrame(rows)
            date_col = next((c for c in ("dEven", "date") if c in df.columns), None)
            value_col = next((c for c in ("xValue", "indexLast", "last") if c in df.columns), None)
            if date_col and value_col:
                out = pd.DataFrame({"date": pd.to_datetime(df[date_col].astype(str), format="%Y%m%d", errors="coerce"), "close": pd.to_numeric(df[value_col], errors="coerce")})
                out = out.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)
                if not out.empty:
                    return out
        print(f"CDN index history empty for {code}; switching to old TSETMC endpoint", flush=True)
    except Exception as exc:
        print(f"CDN index history failed for {code}: {exc}; switching to old TSETMC endpoint", flush=True)
    return index_history_old(code)


def market_symbols() -> pd.DataFrame:
    payload = get_json(f"{BASE}/ClosingPrice/GetMarketWatch?market=0&paperTypes[0]=1&paperTypes[1]=2&paperTypes[2]=3&paperTypes[3]=4&paperTypes[4]=5&paperTypes[5]=6&paperTypes[6]=7&paperTypes[7]=8&paperTypes[8]=9&withBestLimits=false&hEven=0&RefID=0")
    rows = payload.get("marketwatch", [])
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("marketwatch returned no rows")
    code = "insCode" if "insCode" in df.columns else None
    symbol = next((c for c in ("lVal18AFC", "lVal18") if c in df.columns), None)
    if not code:
        raise RuntimeError(f"marketwatch schema missing insCode: {df.columns.tolist()}")
    out = pd.DataFrame({"ins_code": df[code].astype(str), "symbol": df[symbol].astype(str) if symbol else ""})
    return out.drop_duplicates("ins_code").reset_index(drop=True)


def symbol_history(ins_code: str) -> pd.DataFrame:
    payload = get_json(f"{BASE}/ClosingPrice/GetClosingPriceDailyList/{ins_code}/0")
    rows = payload.get("closingPriceDaily", [])
    if not rows:
        return pd.DataFrame(columns=["date", "close"])
    df = pd.DataFrame(rows)
    date_col = "dEven" if "dEven" in df.columns else "date"
    value_col = "pClosing" if "pClosing" in df.columns else "pc"
    out = pd.DataFrame({"date": pd.to_datetime(df[date_col].astype(str), format="%Y%m%d", errors="coerce"), "close": pd.to_numeric(df[value_col], errors="coerce")})
    return out.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)


def write_gz(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as f:
        df.to_csv(f, index=False)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--kind", choices=["indices", "symbols"], default="indices")
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--shards", type=int, default=1)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--out", default="data/historical")
    args = p.parse_args()
    out = Path(args.out)

    if args.kind == "indices":
        for name, code in INDEX_CODES.items():
            df = index_history(code)
            print(f"{name}: rows={len(df)} from={df.date.min().date()} to={df.date.max().date()}", flush=True)
            write_gz(df, out / f"index_{name}.csv.gz")
        return

    symbols = market_symbols()
    symbols = symbols.iloc[args.shard :: args.shards].copy()
    if args.limit:
        symbols = symbols.head(args.limit)
    records = []
    for n, row in enumerate(symbols.itertuples(index=False), 1):
        try:
            h = symbol_history(row.ins_code)
            if len(h) >= 250:
                h["ins_code"] = row.ins_code
                h["symbol"] = row.symbol
                records.append(h)
        except Exception as exc:
            print(f"WARN {row.symbol} {row.ins_code}: {exc}", flush=True)
        if n % 25 == 0:
            print(f"processed={n}/{len(symbols)} kept={len(records)}", flush=True)
    if records:
        write_gz(pd.concat(records, ignore_index=True), out / f"symbols_shard_{args.shard:02d}.csv.gz")
    else:
        write_gz(pd.DataFrame(columns=["date", "close", "ins_code", "symbol"]), out / f"symbols_shard_{args.shard:02d}.csv.gz")


if __name__ == "__main__":
    main()
