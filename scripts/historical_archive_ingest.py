"""Download and normalize an open historical TSE archive for BabiMind.

This is a historical-only acquisition path. It is intentionally independent of
TSETMC live/CDN access so the forecasting backtest can be populated even when
TSETMC is unreachable from GitHub Actions.
"""
from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

SOURCE_URL = "https://raw.githubusercontent.com/HdHamid/irx-usd-data/main/irx-usd-data.zip"


def download_source(url: str) -> bytes:
    r = requests.get(url, timeout=(10, 120), headers={"User-Agent": "BabiMind-Historical-Ingest/1.0"})
    r.raise_for_status()
    return r.content


def normalize_csv(raw: bytes, filename: str) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw))
    cols = {c.lower().strip(): c for c in df.columns}
    date_col = next((cols[c] for c in ("endt", "date", "prsndte") if c in cols), None)
    symbol_col = next((cols[c] for c in ("nmdnam", "symbol", "ticker") if c in cols), None)
    close_col = next((cols[c] for c in ("closeprc", "close", "closingprice") if c in cols), None)
    if not date_col or not close_col:
        raise ValueError(f"unsupported archive schema in {filename}: {list(df.columns)}")
    out = pd.DataFrame({
        "date": pd.to_datetime(df[date_col], errors="coerce"),
        "symbol": df[symbol_col].astype(str) if symbol_col else Path(filename).stem,
        "close": pd.to_numeric(df[close_col], errors="coerce"),
        "source": "HdHamid/irx-usd-data",
    })
    for src, dst in (("open", "open"), ("high", "high"), ("low", "low"), ("volume", "volume"), ("vol", "volume")):
        if src in cols:
            out[dst] = pd.to_numeric(df[cols[src]], errors="coerce")
    return out.dropna(subset=["date", "close"]).drop_duplicates(["symbol", "date"]).sort_values(["symbol", "date"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/historical/archive_1396.csv.gz")
    ap.add_argument("--url", default=SOURCE_URL)
    args = ap.parse_args()

    payload = download_source(args.url)
    frames = []
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            try:
                frame = normalize_csv(zf.read(name), name)
                frames.append(frame)
            except Exception as exc:
                print(f"SKIP {name}: {exc}", flush=True)

    if not frames:
        raise RuntimeError("historical archive contained no usable CSV files")
    out = pd.concat(frames, ignore_index=True)
    out = out[(out.date >= "2017-03-21") & (out.date < "2018-03-21")]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, compression="gzip")
    print(f"archive_1396 rows={len(out)} symbols={out.symbol.nunique()} from={out.date.min()} to={out.date.max()}", flush=True)


if __name__ == "__main__":
    main()
