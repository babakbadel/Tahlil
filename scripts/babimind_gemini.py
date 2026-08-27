#!/usr/bin/env python3
"""Gemini reasoning layer for BabiMind with quota-aware graceful fallback."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT=Path(__file__).resolve().parents[1]
REPORTS=ROOT/"reports"; OUT=REPORTS/"babimind_gemini.json"
MODEL=os.getenv("GEMINI_MODEL","gemini-flash-latest")
API_URL=f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def load_json(path, default):
    try:return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError,json.JSONDecodeError):return default

def compact_state():
    pipeline=load_json(REPORTS/"babimind_pipeline.json",{}); graph=load_json(REPORTS/"babimind_graph.json",{}); previous=load_json(OUT,{})
    return {"pipeline_summary":pipeline.get("summary",{}),"routing":pipeline.get("routing",[]),"graph_intelligence":graph,"active_sources":[{k:r.get(k) for k in ("name","topic","type","state","freshness","confidence","signal_weight")} for r in pipeline.get("sources",[]) if r.get("eligible_for_aggregation")],"previous_gemini_result":previous.get("analysis")}

def write(payload):
    REPORTS.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")

def main():
    key=os.getenv("GEMINI_API_KEY"); now=datetime.now(timezone.utc).isoformat()
    if not key:
        write({"model":"BabiMind","provider":"Gemini","gemini_model":MODEL,"generated_at":now,"status":"skipped","reason":"missing_api_key","quota_exhausted":False})
        print("BabiMind Gemini: SKIPPED (missing API key)"); return
    state=compact_state()
    prompt="""You are the strategic reasoning layer of BabiMind for Iran financial markets. Analyze only the supplied machine-readable state; never invent missing facts. Separate observed data from inference. Apply multi-player game theory, dynamic-systems/feedback-loop reasoning, political economy, and scenario analysis. Return ONLY valid JSON with keys: regime, scenarios, game_theory, dynamic_system, political_economy, market_implications, confidence, data_gaps. scenarios is an array with name, probability (0..1), horizon, triggers, expected_market_effect, invalidation_signals. Include separate implications for stocks, USD/IRR, gold and options. Rank scenarios by probability and lower confidence when evidence is insufficient.\n\nCURRENT STATE:\n"""+json.dumps(state,ensure_ascii=False,separators=(",",":"))
    body=json.dumps({"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.2,"responseMimeType":"application/json"}},ensure_ascii=False).encode()
    req=Request(API_URL,data=body,headers={"Content-Type":"application/json","X-goog-api-key":key},method="POST")
    try:
        with urlopen(req,timeout=90) as response: raw=json.loads(response.read().decode())
        text=raw["candidates"][0]["content"]["parts"][0]["text"]; analysis=json.loads(text)
        write({"model":"BabiMind","provider":"Gemini","gemini_model":MODEL,"generated_at":now,"status":"ok","quota_exhausted":False,"analysis":analysis,"input_state":state}); print("BabiMind Gemini analysis saved")
    except HTTPError as exc:
        details=exc.read().decode("utf-8","replace")[:4000]
        quota=exc.code==429 or "RESOURCE_EXHAUSTED" in details or "quota" in details.lower()
        status="quota_exhausted" if quota else "error"
        write({"model":"BabiMind","provider":"Gemini","gemini_model":MODEL,"generated_at":now,"status":status,"quota_exhausted":quota,"http_status":exc.code,"error":details,"action":"skip_gemini_and_use_cached_or_local_outputs"})
        if quota:
            print("🚨 BabiMind Gemini Quota Alert: API quota exhausted (HTTP 429). Gemini reasoning skipped; cached/local outputs remain usable.")
            return
        raise SystemExit(f"Gemini request failed: HTTP {exc.code}")
    except (URLError,TimeoutError,KeyError,json.JSONDecodeError) as exc:
        write({"model":"BabiMind","provider":"Gemini","gemini_model":MODEL,"generated_at":now,"status":"error","quota_exhausted":False,"error":str(exc),"action":"retry_next_run"})
        raise SystemExit(f"Gemini request failed: {exc}")

if __name__=="__main__":main()
