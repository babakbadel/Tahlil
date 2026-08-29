"""Ingest sm-sokout/tse-option outputs as a validated auxiliary option source.

The upstream project is fetched at CI time. This adapter intentionally uses a
CLI/API contract rather than importing unknown upstream internals, so upstream
changes cannot silently corrupt BabiMind.
"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

OUT = Path("data/raw/tse_option_snapshot.json")
META = Path("reports/tse_option_source_status.json")
UPSTREAM = os.getenv("TSE_OPTION_REPO", "https://github.com/sm-sokout/tse-option.git")
REF = os.getenv("TSE_OPTION_REF", "master")


def main() -> int:
    work = Path(".cache/tse-option")
    if not (work / ".git").exists():
        work.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", "--branch", REF, UPSTREAM, str(work)], check=True)
    else:
        subprocess.run(["git", "-C", str(work), "fetch", "--depth", "1", "origin", REF], check=True)
        subprocess.run(["git", "-C", str(work), "reset", "--hard", "FETCH_HEAD"], check=True)

    commit = subprocess.check_output(["git", "-C", str(work), "rev-parse", "HEAD"], text=True).strip()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "sm-sokout/tse-option",
        "upstream": UPSTREAM,
        "ref": REF,
        "commit": commit,
        "status": "source-fetched",
        "data": [],
        "note": "Upstream source fetched and provenance recorded. Runtime extraction must be explicitly enabled by a compatible upstream CLI/API contract; no undocumented internals are imported.",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"TSE Option source fetched: {commit}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
