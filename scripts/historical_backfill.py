"""Backfill TSETMC daily history for BabiMind forecasting.

Acquisition is fail-soft: one unavailable endpoint must not abort the whole
historical pipeline. Successful data is always written as an artifact.
"""
from __future__ import annotations

import argparse
import gzip
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
}
INDEX_CODES = {"tedpix": "32097828820363860", "equal_weighted": "67130298613737946"}


def make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=1, connect=1, read=1, status=1, backoff_factor=0.8,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset({"GET"}),
                  respect_retry_after_header=True)
    adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=4)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update(HEADERS)
    return s

SESSION = make_session()


def get_json(url: str, attempts: int = 2) -> dict[str, Any]:
    last: Exception | None = None
    for n in range(attempts):
        try:
            r = SESSION.get(url, timeout=(8, 25))
            r.raise_for_status()
            text = r.text.lstrip("\ufeff \t\r\n")
            if not text.startswith("{"):
                raise RuntimeError("non-JSON response from TSETMC")
            return r.json()
        except Exception as exc:
            last = exc
            if n + 1 < attempts:
                delay = min(6.0, 2.0 ** n) + random.uniform(0.1, 0.5)
                print(f"RETRY {n + 1}/{attempts - 1}: {type(exc).__name__}; sleep={delay:.1f}s", flush=True)
                time.sleep(delay)
    raise RuntimeError(f"TSETMC request failed: {url}: {last}")


def index_history_old(code: str) -> pd.DataFrame:
    url = f"{OLD_BASE}/IndexFinancial.aspx?i={code}&t=ph"
    r = SESSION.get(url, timeout=(8, 30), headers={**HEADERS, "Accept": "text/plain,*/*"})
    r.raise_for_status()
    rows = []
    for raw in r.text.lstrip("\ufeff \t\r\n").replace("\r", "").replace("\n", "").split(";"):
        p = raw.strip().split(",")
        if len(p) >= 7:
            rows.append((p[0], p[6]))
    if not rows:
        raise RuntimeError(f"old TSETMC endpoint returned no rows for {code}")
    out = pd.DataFrame(rows, columns=["date", "close"])
    out["date"] = pd.to_datetime(out["date"].astype(str), format="%Y%m%d", errors="coerce")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    return out.dropna().drop_duplicates("date").sort_values("date").reset_index(drop=True)


def index_history(code: str) -> pd.DataFrame:
    try:
        payload = get_json(f"{BASE}/Index/GetIndexB2History/{code}")
        rows = payload.get("indexB2", [])
        if rows:
            df = pd.DataFrame(rows)
            dc = next((c for c in ("dEven", "date") if c in df.columns), None)
            vc = next((c for c in ("xValue", "indexLast", "last") if c in df.columns), None)
            if dc and vc:
                out = pd.DataFrame({"date": pd.to_datetime(df[dc].astype(str), format="%Y%m%d", errors="coerce"),
                                    "close": pd.to_numeric(df[vc], errors="coerce")}).dropna()
                if not out.empty:
                    return out.drop_duplicates("date").sort_values("date").reset_index(drop=True)
    except Exception as exc:
        print(f"CDN failed: {exc}", flush=True)
    print(f"Using old TSETMC endpoint for index {code}", flush=True)
    return index_history_old(code)


def market_symbols() -> pd.DataFrame:
    payload = get_json(f"{BASE}/ClosingPrice/GetMarketWatch?market=0&paperTypes[0]=1&paperTypes[1]=2&paperTypes[2]=3&paperTypes[3]=4&paperTypes[4]=5&paperTypes[5]=6&paperTypes[6]=7&paperTypes[7]=8&paperTypes[8]=9&withBestLimits=false&hEven=0&RefID=0")
    df = pd.DataFrame(payload.get("marketwatch", []))
    if df.empty or "insCode" not in df:
        raise RuntimeError("marketwatch returned no usable rows")
    sc = next((c for c in ("lVal18AFC", "lVal18") if c in df), None)
    return pd.DataFrame({"ins_code": df["insCode"].astype(str), "symbol": df[sc].astype(str) if sc else ""}).drop_duplicates("ins_code")


def symbol_history(ins_code: str) -> pd.DataFrame:
    payload = get_json(f"{BASE}/ClosingPrice/GetClosingPriceDailyList/{ins_code}/0")
    rows = payload.get("closingPriceDaily", [])
    if not rows:
        return pd.DataFrame(columns=["date", "close"])
    df = pd.DataFrame(rows)
    dc = "dEven" if "dEven" in df else "date"
    vc = "pClosing" if "pClosing" in df else "pc"
    out = pd.DataFrame({"date": pd.to_datetime(df[dc].astype(str), format="%Y%m%d", errors="coerce"),
                        "close": pd.to_numeric(df[vc], errors="coerce")})
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
        failures = 0
        for name, code in INDEX_CODES.items():
            try:
                df = index_history(code)
                print(f"{name}: rows={len(df)} from={df.date.min().date()} to={df.date.max().date()}", flush=True)
                write_gz(df, out / f"index_{name}.csv.gz")
            except Exception as exc:
                failures += 1
                print(f"ERROR {name}: {exc}", flush=True)
                write_gz(pd.DataFrame(columns=["date", "close"]), out / f"index_{name}.csv.gz")
        print(f"index_backfill_failures={failures}", flush=True)
        return

    try:
        symbols = market_symbols()
    except Exception as exc:
        print(f"ERROR marketwatch: {exc}", flush=True)
        write_gz(pd.DataFrame(columns=["date", "close", "ins_code", "symbol"]), out / f"symbols_shard_{args.shard:02d}.csv.gz")
        return
    symbols = symbols.iloc[args.shard :: args.shards].copy()
    if args.limit:
        symbols = symbols.head(args.limit)
    records = []
    for n, row in enumerate(symbols.itertuples(index=False), 1):
        try:
            h = symbol_history(row.ins_code)
            if len(h) >= 250:
                h["ins_code"], h["symbol"] = row.ins_code, row.symbol
                records.append(h)
        except Exception as exc:
            print(f"WARN {row.symbol} {row.ins_code}: {exc}", flush=True)
        if n % 25 == 0:
            print(f"processed={n}/{len(symbols)} kept={len(records)}", flush=True)
    result = pd.concat(records, ignore_index=True) if records else pd.DataFrame(columns=["date", "close", "ins_code", "symbol"])
    write_gz(result, out / f"symbols_shard_{args.shard:02d}.csv.gz")
    print(f"shard={args.shard}: rows={len(result)} symbols={result.symbol.nunique() if not result.empty else 0}", flush=True)


if __name__ == "__main__":
    main()
