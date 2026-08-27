#!/usr/bin/env python3
"""Send BabiMind state to Gemini and persist structured model feedback."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUT = REPORTS / "babimind_gemini.json"
MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def compact_state() -> dict:
    pipeline = load_json(REPORTS / "babimind_pipeline.json", {})
    graph = load_json(REPORTS / "babimind_graph.json", {})
    previous = load_json(OUT, {})
    return {
        "pipeline_summary": pipeline.get("summary", {}),
        "routing": pipeline.get("routing", []),
        "graph_intelligence": graph,
        "active_sources": [
            {k: r.get(k) for k in ("name", "topic", "type", "state", "freshness", "confidence", "signal_weight")}
            for r in pipeline.get("sources", []) if r.get("eligible_for_aggregation")
        ],
        "previous_gemini_result": previous.get("analysis"),
    }


def main() -> None:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not configured")

    state = compact_state()
    prompt = """You are the strategic reasoning layer of BabiMind for Iran financial markets.\nAnalyze the supplied machine-readable state. Do not invent missing facts. Separate observed data from inference. Apply: (1) multi-player game theory, (2) dynamic-systems/feedback-loop reasoning, (3) political economy, and (4) scenario analysis. Produce ONLY valid JSON with keys: regime, scenarios, game_theory, dynamic_system, political_economy, market_implications, confidence, data_gaps.\nscenarios must be an array of objects with name, probability (0..1), horizon, triggers, expected_market_effect, invalidation_signals. Include separate implications for stocks, USD/IRR, gold and options. Rank the scenarios by probability. If evidence is insufficient, lower confidence instead of guessing.\n\nCURRENT BabiMind STATE:\n""" + json.dumps(state, ensure_ascii=False, separators=(",", ":"))

    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}}, ensure_ascii=False).encode()
    req = Request(API_URL, data=body, headers={"Content-Type": "application/json", "X-goog-api-key": key}, method="POST")
    now = datetime.now(timezone.utc).isoformat()
    try:
        with urlopen(req, timeout=90) as response:
            raw = json.loads(response.read().decode("utf-8"))
        text = raw["candidates"][0]["content"]["parts"][0]["text"]
        analysis = json.loads(text)
        payload = {"model": "BabiMind", "provider": "Gemini", "gemini_model": MODEL, "generated_at": now, "analysis": analysis, "input_state": state}
        REPORTS.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"BabiMind Gemini analysis saved: {OUT}")
    except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        OUT.write_text(json.dumps({"model":"BabiMind","provider":"Gemini","generated_at":now,"status":"error","error":str(exc)}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit(f"Gemini request failed: {exc}")


if __name__ == "__main__":
    main()
