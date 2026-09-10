import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = os.environ.get("TSETMC_RELAY_URL", "").rstrip("/")
OUT = Path(os.environ.get("TSETMC_RELAY_OUT", "data/raw/tsetmc_relay_snapshot.json"))
TIMEOUT = int(os.environ.get("TSETMC_RELAY_TIMEOUT", "20"))


def fetch(path: str):
    if not BASE:
        raise RuntimeError("TSETMC_RELAY_URL is not configured")
    r = requests.get(BASE + path, timeout=TIMEOUT, headers={"Accept": "application/json"})
    r.raise_for_status()
    return r.json()


def main():
    payload = {
        "source": "babimind-tsetmc-relay",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "error",
        "market_watch": [],
        "client_type": [],
        "options": [],
        "errors": [],
    }
    try:
        market = fetch("/market/watch")
        data = market.get("data") if isinstance(market, dict) else market
        payload["market_watch"] = data if isinstance(data, list) else (data.get("marketwatch", []) if isinstance(data, dict) else [])
    except Exception as exc:
        payload["errors"].append(f"market_watch: {exc!r}")
    try:
        clients = fetch("/market/client-type")
        data = clients.get("data") if isinstance(clients, dict) else clients
        payload["client_type"] = data if isinstance(data, list) else (data.get("clientTypeAllDto", []) if isinstance(data, dict) else [])
    except Exception as exc:
        payload["errors"].append(f"client_type: {exc!r}")
    try:
        options = fetch("/options/watch")
        payload["options"] = options.get("data", options) if isinstance(options, dict) else options
    except Exception as exc:
        payload["errors"].append(f"options: {exc!r}")
    if payload["market_watch"] or payload["client_type"] or payload["options"]:
        payload["status"] = "ok"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "market_rows": len(payload["market_watch"]), "client_rows": len(payload["client_type"]), "errors": payload["errors"]}, ensure_ascii=False))
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
