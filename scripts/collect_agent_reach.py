#!/usr/bin/env python3
"""Collect research through Agent Reach without making it a primary data source.

The collector is deliberately fail-open: if Agent Reach or a channel is unavailable,
Tahlil records the failure and continues. Raw stdout is retained for provenance.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "agent_reach"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def run(cmd: list[str], timeout: int) -> dict:
    started = now()
    try:
        p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        return {
            "command": cmd,
            "started_at": started,
            "finished_at": now(),
            "returncode": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
        }
    except FileNotFoundError as exc:
        return {"command": cmd, "started_at": started, "finished_at": now(), "returncode": 127, "error": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "command": cmd,
            "started_at": started,
            "finished_at": now(),
            "returncode": 124,
            "error": f"timeout after {timeout}s",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", action="append", default=[], help="Research query; repeatable")
    ap.add_argument("--timeout", type=int, default=90)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    result = {
        "schema": "babimind.agent_reach.v1",
        "provider": "Panniantong/Agent-Reach",
        "collector": "scripts/collect_agent_reach.py",
        "collected_at": now(),
        "queries": args.query,
        "results": [],
    }

    agent_reach = shutil.which("agent-reach")
    if not agent_reach:
        result["status"] = "unavailable"
        result["results"].append({"error": "agent-reach CLI not installed"})
    else:
        doctor = run([agent_reach, "doctor"], args.timeout)
        result["doctor"] = doctor
        result["status"] = "ready" if doctor.get("returncode") == 0 else "degraded"

        # Agent Reach exposes platform-specific upstream tools. We only execute
        # explicitly supplied research commands through the installed CLI/skill.
        # The generic doctor result is always captured; query execution remains
        # opt-in so CI cannot unexpectedly hit external services.
        for q in args.query:
            result["results"].append({
                "query": q,
                "status": "queued",
                "note": "Use the Agent Reach skill/channel for the requested platform; raw command execution is opt-in.",
            })

    path = OUT / f"agent_reach_{stamp}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(path.relative_to(ROOT))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
