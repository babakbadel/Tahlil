"""Ingest the collected sm-sokout/tse-option snapshot without overwriting it.

The collector writes data/raw/tse_option_chain.json. This step fetches and
records upstream provenance, then copies the collector payload into the
canonical snapshot consumed by downstream BabiMind option stages.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

COLLECTED = Path(os.getenv("TSE_OPTION_COLLECTED", "data/raw/tse_option_chain.json"))
OUT = Path("data/raw/tse_option_snapshot.json")
META = Path("reports/tse_option_source_status.json")
UPSTREAM = os.getenv("TSE_OPTION_REPO", "https://github.com/sm-sokout/tse-option.git")
REF = os.getenv("TSE_OPTION_REF", "master")


def main() -> int:
    work = Path(".cache/tse-option")
    if not (work / ".git").exists():
        work.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", REF, UPSTREAM, str(work)],
            check=True,
            timeout=30,
        )
    commit = subprocess.check_output(
        ["git", "-C", str(work), "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()

    if COLLECTED.exists():
        try:
            collected = json.loads(COLLECTED.read_text(encoding="utf-8"))
        except Exception as exc:
            collected = {
                "source": "sm-sokout/tse-option",
                "status": "error",
                "data": [],
                "error": f"invalid collector JSON: {type(exc).__name__}: {exc}",
            }
    else:
        collected = {
            "source": "sm-sokout/tse-option",
            "status": "error",
            "data": [],
            "error": "collector output is missing",
        }

    collected["upstream"] = UPSTREAM
    collected["ref"] = REF
    collected["commit"] = commit
    collected["provenance"] = {
        "source": "sm-sokout/tse-option",
        "upstream": UPSTREAM,
        "ref": REF,
        "commit": commit,
    }

    # Keep both the collector schema (rows) and a generic data alias so older
    # downstream consumers can migrate without losing the real snapshot.
    if "rows" in collected and "data" not in collected:
        collected["data"] = collected["rows"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(collected, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(collected["provenance"] | {"status": collected.get("status")}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"TSE Option snapshot preserved: status={collected.get('status')} commit={commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
