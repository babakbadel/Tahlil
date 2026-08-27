#!/usr/bin/env python3
"""Persistent, auditable BabiMind memory.

Stores compact run summaries so future OpenRouter prompts can use prior model
state without sending the entire historical report every time.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "reports" / "babimind_memory.json"
CONTEXT = ROOT / "reports" / "babimind_memory_context.json"
LLM = ROOT / "reports" / "babimind_llm.json"
MAX_RUNS = 100


def load():
    if not MEMORY.exists():
        return {"model": "BabiMind", "version": 1, "runs": []}
    try:
        d = json.loads(MEMORY.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {"model": "BabiMind", "version": 1, "runs": []}
    except Exception:
        return {"model": "BabiMind", "version": 1, "runs": []}


def compact(d):
    a = d.get("analysis") or {}
    scenarios = a.get("scenarios") or {}
    return {
        "timestamp": d.get("generated_at") or datetime.now(timezone.utc).isoformat(),
        "provider": d.get("provider"), "model": d.get("model"),
        "regime": a.get("regime"),
        "scenarios": scenarios,
        "market_implications": a.get("market_implications"),
        "confidence": a.get("confidence"),
        "data_gaps": a.get("data_gaps", []),
    }


def prepare():
    d = load(); runs = d.get("runs", [])[-20:]
    context = {
        "memory_version": d.get("version", 1),
        "historical_runs_available": len(d.get("runs", [])),
        "recent_runs": runs,
        "instruction": "Use history for regime changes, recurring errors and calibration. Never treat old data as current evidence."
    }
    CONTEXT.parent.mkdir(parents=True, exist_ok=True)
    CONTEXT.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[BabiMind Memory] prepared {len(runs)} recent runs")


def ingest():
    if not LLM.exists():
        print("[BabiMind Memory] no LLM result; nothing to ingest")
        return
    try: d = json.loads(LLM.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[BabiMind Memory] invalid LLM output: {e}"); return
    if d.get("status") != "ok":
        print("[BabiMind Memory] non-success result not added")
        return
    row = compact(d)
    fingerprint = hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    row["fingerprint"] = fingerprint
    mem = load(); runs = mem.setdefault("runs", [])
    if any(x.get("fingerprint") == fingerprint for x in runs):
        print("[BabiMind Memory] duplicate run skipped"); return
    runs.append(row); mem["runs"] = runs[-MAX_RUNS:]
    mem["updated_at"] = datetime.now(timezone.utc).isoformat()
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    MEMORY.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[BabiMind Memory] ingested run; total={len(mem['runs'])}")


def main():
    p = argparse.ArgumentParser(); p.add_argument("--prepare", action="store_true"); p.add_argument("--ingest", action="store_true")
    a = p.parse_args()
    if a.prepare: prepare()
    if a.ingest: ingest()
    if not a.prepare and not a.ingest: prepare()

if __name__ == "__main__": main()
