import os
import csv
import json
import requests
from datetime import datetime, timezone
from pathlib import Path


API_URL = "https://api.brsapi.ir/Tsetmc/AllSymbols.php"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def fetch_all_symbols():
    api_key = os.getenv("BRS_API_KEY")

    if not api_key:
        raise RuntimeError("BRS_API_KEY تنظیم نشده است.")

    response = requests.get(
        API_URL,
        params={"key": api_key, "type": 1},
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    if isinstance(data, dict):
        rows = data.get("data", data.get("result", data))
    else:
        rows = data

    if not isinstance(rows, list):
        raise RuntimeError(f"ساختار پاسخ ناشناخته است: {type(rows)}")

    return rows


def save_json(rows):
    timestamp = datetime.now(timezone.utc).isoformat()
    output = {
        "source": "BRS API",
        "endpoint": "Tsetmc/AllSymbols.php",
        "type": 1,
        "fetched_at_utc": timestamp,
        "count": len(rows),
        "symbols": rows,
    }
    Path("data").mkdir(exist_ok=True)
    Path("data/all_symbols.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_csv(rows):
    if not rows:
        return
    Path("data").mkdir(exist_ok=True)
    fields = sorted({
        key for row in rows if isinstance(row, dict) for key in row.keys()
    })
    with open("data/all_symbols.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f=f,
            fieldnames=fields,
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def print_market_summary(rows):
    print("\n" + "=" * 70)
    print("BRS MARKET SCAN")
    print("=" * 70)
    print(f"تعداد کل رکوردها: {len(rows):,}")

    symbols = [r for r in rows if isinstance(r, dict) and r.get("l18")]
    print(f"تعداد دارای نماد: {len(symbols):,}")

    volume_rows = [
        r for r in symbols if isinstance(r.get("tvol"), (int, float))
    ]
    volume_rows.sort(key=lambda x: x.get("tvol", 0), reverse=True)
    print("\n10 نماد با بیشترین حجم:")
    for i, row in enumerate(volume_rows[:10], 1):
        print(
            f"{i:2}. {row.get('l18', ''):<15} "
            f"حجم={row.get('tvol', 0):,} "
            f"قیمت={row.get('pl', '')} "
            f"درصد={row.get('plp', '')}"
        )

    value_rows = [
        r for r in symbols if isinstance(r.get("tval"), (int, float))
    ]
    value_rows.sort(key=lambda x: x.get("tval", 0), reverse=True)
    print("\n10 نماد با بیشترین ارزش معاملات:")
    for i, row in enumerate(value_rows[:10], 1):
        print(
            f"{i:2}. {row.get('l18', ''):<15} "
            f"ارزش={row.get('tval', 0):,} "
            f"قیمت={row.get('pl', '')} "
            f"درصد={row.get('plp', '')}"
        )


def main():
    print("در حال دریافت کل بازار از BRS...")
    rows = fetch_all_symbols()
    print(f"دریافت شد: {len(rows):,} رکورد")
    save_json(rows)
    save_csv(rows)
    print_market_summary(rows)
    print("\nفایل‌ها:")
    print("data/all_symbols.json")
    print("data/all_symbols.csv")


if __name__ == "__main__":
    main()
