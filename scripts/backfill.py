"""Self-healing data backfill for Tahlil.

Backfill policy:
- During the market session, refresh missing or stale latest snapshots.
- After 12:30 Tehran, if today's final snapshot is missing, create an
  emergency final snapshot from the latest BRS feed and explicitly mark it
  as backfilled. Never pretend it represents the exact 12:30 observation.
- Safe to run repeatedly; no Artifact is required.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timedelta, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LATEST = DATA / "latest"
FINAL = DATA / "final"
ARTIFACTS = ROOT / "artifacts"
STALE_AFTER = timedelta(minutes=35)


def now_tehran() -> datetime:
    return datetime.now(TEHRAN)


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(TEHRAN)


def snapshot_time(path: Path) -> datetime | None:
    payload = read_json(path)
    if not payload:
        return None
    for key in ("event_time", "received_at", "fetched_at_utc"):
        parsed = parse_timestamp(payload.get(key))
        if parsed:
            return parsed
    return None


def is_stale(path: Path, now: datetime) -> bool:
    captured = snapshot_time(path)
    return captured is None or (now - captured) > STALE_AFTER


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def refresh_options() -> Path:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    output = ARTIFACTS / "options_realtime_backfill.json"
    run(["python3", "scripts/fetch_options_realtime.py", "--output", str(output)])
    LATEST.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output, LATEST / "options_realtime.json")
    return output


def refresh_market() -> Path:
    run(["python3", "scan_market.py"])
    LATEST.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DATA / "all_symbols.json", LATEST / "all_symbols.json")
    if (DATA / "all_symbols.csv").exists():
        shutil.copy2(DATA / "all_symbols.csv", LATEST / "all_symbols.csv")
    return DATA / "all_symbols.json"


def mark_backfilled(path: Path, reason: str) -> None:
    payload = read_json(path)
    if not payload:
        return
    payload.setdefault("data_quality", {})
    payload["data_quality"]["backfill"] = True
    payload["data_quality"]["backfill_reason"] = reason
    payload["data_quality"]["backfilled_at"] = datetime.now(timezone.utc).isoformat()
    write_json(path, payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--options-only", action="store_true")
    parser.add_argument("--market-only", action="store_true")
    args = parser.parse_args()

    now = now_tehran()
    today = now.date().isoformat()
    market_open = time(8, 0)
    market_close = time(12, 30)
    in_session = market_open <= now.time() <= market_close
    final_dir = FINAL / today
    final_options = final_dir / "options_realtime.json"
    final_market = final_dir / "all_symbols.json"

    latest_options = LATEST / "options_realtime.json"
    latest_market = LATEST / "all_symbols.json"

    if args.force or not latest_options.exists() or (in_session and is_stale(latest_options, now)):
        refresh_options()

    if not args.options_only and (
        args.force or not latest_market.exists() or (in_session and is_stale(latest_market, now))
    ):
        refresh_market()

    if not in_session and now.time() > market_close:
        final_dir.mkdir(parents=True, exist_ok=True)

        if args.force or not final_options.exists():
            src = LATEST / "options_realtime.json"
            if not src.exists():
                refresh_options()
                src = LATEST / "options_realtime.json"
            shutil.copy2(src, final_options)
            mark_backfilled(
                final_options,
                "No verified 12:30 scheduled snapshot; emergency final created from latest available feed",
            )

        if not args.options_only and (args.force or not final_market.exists()):
            src = LATEST / "all_symbols.json"
            if not src.exists():
                refresh_market()
                src = LATEST / "all_symbols.json"
            shutil.copy2(src, final_market)
            mark_backfilled(
                final_market,
                "No verified 12:30 scheduled snapshot; emergency final created from latest available feed",
            )

    print(
        f"Backfill OK | Tehran={now.isoformat()} | in_session={in_session} | "
        f"final={final_dir}"
    )


if __name__ == "__main__":
    main()
