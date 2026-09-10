"""Collect a live TSE/IFB option chain safely for BabiMind.

The upstream package is treated as an unreliable network boundary. We first
try the requested Greeks, then automatically fall back to the raw option chain
without IV/BSM/leverage if the enhanced calculation fails. The subprocess is
killable, so a hung upstream call cannot hang the GitHub Actions job.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SYMBOL = os.getenv("OPTION_SYMBOL", "فملی")
OUT = Path(os.getenv("TSE_OPTION_OUT", "data/raw/tse_option_chain.json"))
REPO = os.getenv("TSE_OPTION_REPO", "https://github.com/sm-sokout/tse-option.git")
REF = os.getenv("TSE_OPTION_REF", "master")
TIMEOUT = max(10, int(os.getenv("TSE_OPTION_TIMEOUT_SECONDS", "60")))
TRADING_DAYS = max(1, int(os.getenv("OPTION_TRADING_DAYS", "100")))
INCLUDE_GREEKS = os.getenv("OPTION_INCLUDE_GREEKS", "true").lower() == "true"
RUNTIME = Path(os.getenv("TSE_OPTION_RUNTIME_DIR", ".cache/tse-option"))


def _write(payload: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _ensure_runtime() -> None:
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


def _run_child(with_greeks: bool) -> tuple[int, str, str]:
    """Run one isolated tse-option call; kill the whole process group on timeout."""
    flags = "True" if with_greeks else "False"
    code = f'''
import json, os
import tse_option as tso
symbol = os.environ["OPTION_SYMBOL"]
df = tso.option_chain(
    symbol=symbol,
    trading_days=int(os.environ.get("OPTION_TRADING_DAYS", "100")),
    IV={flags},
    leverage={flags},
    P_BSM={flags},
    sort="Maturity",
)
payload = {{"columns": list(df.columns), "rows": df.where(df.notna(), None).to_dict(orient="records")}}
print("__TSE_OPTION_JSON__" + json.dumps(payload, ensure_ascii=False, default=str), flush=True)
'''
    env = dict(os.environ)
    env["OPTION_SYMBOL"] = SYMBOL
    env["OPTION_TRADING_DAYS"] = str(TRADING_DAYS)
    proc = subprocess.Popen(
        [sys.executable, "-c", code],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = proc.communicate()
        return 124, stdout, f"timeout after {TIMEOUT}s\n{stderr}"
    return proc.returncode, stdout, stderr


def _parse(stdout: str) -> dict | None:
    marker = "__TSE_OPTION_JSON__"
    lines = [line[len(marker):] for line in stdout.splitlines() if line.startswith(marker)]
    if not lines:
        return None
    return json.loads(lines[-1])


def main() -> int:
    collected_at = datetime.now(timezone.utc).isoformat()
    base = {
        "source": "sm-sokout/tse-option",
        "upstream": REPO,
        "ref": REF,
        "symbol": SYMBOL,
        "trading_days": TRADING_DAYS,
        "collected_at_utc": collected_at,
        "status": "error",
        "mode": "none",
        "columns": [],
        "rows": [],
    }
    try:
        _ensure_runtime()
        attempts = [True, False] if INCLUDE_GREEKS else [False]
        errors: list[str] = []
        for greeks in attempts:
            rc, stdout, stderr = _run_child(greeks)
            payload = _parse(stdout) if rc == 0 else None
            if payload and payload.get("rows"):
                base.update(payload)
                base["status"] = "ok"
                base["mode"] = "greeks" if greeks else "raw_fallback"
                if errors:
                    base["fallback_from_error"] = errors[-1][-4000:]
                _write(base)
                print(f"[TSE-OPTION] OK mode={base['mode']} rows={len(base['rows'])} symbol={SYMBOL}", flush=True)
                return 0
            detail = (stderr or stdout or f"exit={rc}").strip()[-4000:]
            errors.append(f"mode={'greeks' if greeks else 'raw'} exit={rc}: {detail}")
        base["error"] = " | ".join(errors)[-8000:]
        _write(base)
        print(f"[TSE-OPTION] ERROR {base['error']}", flush=True)
        return 1
    except Exception as exc:
        base["error"] = f"{type(exc).__name__}: {exc}"
        _write(base)
        print(f"[TSE-OPTION] ERROR {base['error']}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
