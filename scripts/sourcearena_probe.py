#!/usr/bin/env python3
"""
SourceArena API probe for Tahlil.

Usage:
  SOURCEARENA_TOKEN=... python scripts/sourcearena_probe.py --name شستا

The token is read only from the environment and is never printed.
"""
import argparse
import json
import os
import sys

import requests

BASE_URL = "https://apis.sourcearena.ir/api/"


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe SourceArena symbol API")
    parser.add_argument("--name", default="شستا", help="Iranian symbol name")
    args = parser.parse_args()

    token = os.getenv("SOURCEARENA_TOKEN")
    if not token:
        print("ERROR: SOURCEARENA_TOKEN is not set.", file=sys.stderr)
        return 2

    try:
        response = requests.get(
            BASE_URL,
            params={"token": token, "name": args.name},
            headers={
                "User-Agent": "Tahlil-SourceArena-Probe/1.0",
                "Accept": "application/json, text/plain, */*",
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        print(f"ERROR: request failed: {exc}", file=sys.stderr)
        return 1

    print(f"HTTP_STATUS={response.status_code}")
    print(f"CONTENT_TYPE={response.headers.get('content-type', '')}")

    try:
        payload = response.json()
    except ValueError:
        print(response.text)
        return 1 if response.status_code >= 400 else 0

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if response.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
