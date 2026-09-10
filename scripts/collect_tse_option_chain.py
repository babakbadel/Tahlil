"""Collect a live option chain using sm-sokout/tse-option.

Designed for CI: the third-party call runs in a killable subprocess so an
upstream/network hang can never hang the GitHub Actions job indefinitely.
No fabricated values are written; failed collections are recorded explicitly.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SYMBOL = os.getenv("OPTION_SYMBOL", "فملی")
OUT = Path(os.getenv("TSE_OPTION_OUT", "data/raw/tse_option_chain.json"))
REPO = os.getenv("TSE_OPTION_REPO", "https://github.com/sm-sokout/tse-option.git")
REF = os.getenv("TSE_OPTION_REF", "master")
TIMEOUT = max(5, int(os.getenv("TSE_OPTION_TIMEOUT_SECONDS", "45")))
RUNTIME = Path(os.getenv("TSE_OPTION_RUNTIME_DIR", ".cache/tse-option"))


def _write(payload: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _ensure_runtime() -> None:
    """Use the workflow's existing checkout when available; otherwise bootstrap it."""
    if (RUNTIME / ".git").exists():
        return
    RUNTIME.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", REF, REPO, str(RUNTIME)],
        check=True,
        timeout=30,
    )
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(RUNTIME)],
        check=True,
        timeout=120,
    )


def main() -> int:
    collected_at = datetime.now(timezone.utc).isoformat()
    base = {
        "source": "sm-sokout/tse-option",
        "upstream": REPO,
        "ref": REF,
        "symbol": SYMBOL,
        "collected_at_utc": collected_at,
        "status": "error",
        "columns": [],
        "rows": [],
    }

    try:
        _ensure_runtime()
        code = r'''
import json, os
import tse_option as tso
symbol = os.environ["OPTION_SYMBOL"]
df = tso.option_chain(
    symbol=symbol,
    IV=os.environ.get("OPTION_INCLUDE_GREEKS", "true").lower() == "true",
    leverage=os.environ.get("OPTION_INCLUDE_GREEKS", "true").lower() == "true",
    P_BSM=os.environ.get("OPTION_INCLUDE_GREEKS", "true").lower() == "true",
    sort="Maturity",
)
payload = {
    "columns": list(df.columns),
    "rows": df.where(df.notna(), None).to_dict(orient="records"),
}
print("__TSE_OPTION_JSON__" + json.dumps(payload, ensure_ascii=False, default=str))
'''
        env = dict(os.environ)
        env["OPTION_SYMBOL"] = SYMBOL
        result = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )

        marker = "__TSE_OPTION_JSON__"
        json_lines = [line[len(marker):] for line in result.stdout.splitlines() if line.startswith(marker)]
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "upstream process failed").strip()[-4000:]
            base["error"] = f"tse-option exited {result.returncode}: {detail}"
            _write(base)
            print(f"[TSE-OPTION] ERROR {base['error']}", flush=True)
            return 0
        if not json_lines:
            base["error"] = "tse-option returned no machine-readable payload"
            base["stdout_tail"] = result.stdout[-2000:]
            _write(base)
            print(f"[TSE-OPTION] ERROR {base['error']}", flush=True)
            return 0

        payload = json.loads(json_lines[-1])
        base.update(payload)
        base["status"] = "ok"
        _write(base)
        print(f"[TSE-OPTION] OK rows={len(base['rows'])} symbol={SYMBOL}", flush=True)
        return 0

    except subprocess.TimeoutExpired:
        base["error"] = f"tse-option timed out after {TIMEOUT}s; child process was killed"
        _write(base)
        print(f"[TSE-OPTION] TIMEOUT {base['error']}", flush=True)
        return 0
    except Exception as exc:
        base["error"] = f"{type(exc).__name__}: {exc}"
        _write(base)
        print(f"[TSE-OPTION] ERROR {base['error']}", flush=True)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
