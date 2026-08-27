#!/usr/bin/env python3
"""Unified BabiMind source -> signal pipeline with Graph Intelligence.

Fast, bounded source checks. Network failures never block the model indefinitely.
"""
from __future__ import annotations
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "babimind_source_health.json"
OUT = ROOT / "reports" / "babimind_pipeline.json"
GRAPH_OUT = ROOT / "reports" / "babimind_graph.json"
MAX_WORKERS = 24
DEFAULT_TIMEOUT = 4
TOTAL_DEADLINE = 45

def endpoint_check(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    started = time.monotonic()
    try:
        req = Request(url, headers={"User-Agent": "BabiMind-Pipeline/1.4"})
        with urlopen(req, timeout=timeout) as response:
            body = response.read(4096)
            status = getattr(response, "status", 200)
            return {"status": "ok" if 200 <= status < 400 else "error", "http_status": status,
                    "content_type": response.headers.get("Content-Type", ""), "bytes": len(body),
                    "latency_ms": round((time.monotonic()-started)*1000, 1),
                    "content_check": "nonempty" if body else "empty"}
    except HTTPError as e:
        return {"status":"error", "http_status":e.code, "error":str(e), "content_check":"failed"}
    except (URLError, TimeoutError, OSError) as e:
        return {"status":"unavailable", "error":str(e), "content_check":"failed"}

def freshness(source: dict, now: datetime) -> float:
    stamp = source.get("release_timestamp") or source.get("observation_timestamp")
    if not stamp: return 0.75
    try:
        dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        age_days = max(0.0, (now-dt).total_seconds()/86400)
        half_life = float(source.get("freshness_half_life_days", 7))
        return round(2 ** (-age_days/max(half_life,0.1)), 4)
    except (ValueError, TypeError): return 0.5

def confidence(source: dict, availability: float, fresh: float) -> float:
    authority=float(source.get("authority_score",.75)); independence=float(source.get("independence_score",.75))
    coverage=float(source.get("coverage_score",.75)); reproducibility=float(source.get("reproducibility_score",.75))
    reliability=float(source.get("api_reliability_score",.75)); revision=1-float(source.get("revision_risk",.10))
    structural=.20*authority+.15*independence+.15*coverage+.15*reproducibility+.15*reliability+.20*revision
    return round(max(0,min(1,structural*availability*fresh)),4)

def check_source(src: dict) -> dict:
    result=endpoint_check(src["url"])
    now=datetime.now(timezone.utc); fresh=freshness(src,now); state=result.get("status","error")
    if state=="ok" and result.get("content_check")!="nonempty": state="partial"
    if state=="ok" and fresh<.25: state="stale"
    availability=1.0 if state=="ok" else 0.0
    conf=confidence(src,availability,fresh)
    weight=round(.25+.75*conf,4) if state=="ok" else 0.0
    return {**src,**result,"state":state,"freshness":fresh,"confidence":conf,"signal_weight":weight,
            "eligible_for_aggregation":weight>0,"retry_next_run":state!="ok","checked_at":now.isoformat()}

def load_graph() -> dict:
    if not GRAPH_OUT.exists(): return {"available":False,"graph_score":None,"graph_confidence":0.0,"graph_regime":"unavailable"}
    try: return json.loads(GRAPH_OUT.read_text(encoding="utf-8"))
    except Exception as exc: return {"available":False,"graph_score":None,"graph_confidence":0.0,"graph_regime":"error","reason":str(exc)}

def main() -> None:
    started=time.monotonic(); catalog=json.loads(CONFIG.read_text(encoding="utf-8")); sources=catalog.get("sources",[]); rows=[None]*len(sources)
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS,max(1,len(sources)))) as pool:
        futures={pool.submit(check_source,s):i for i,s in enumerate(sources)}
        for future in as_completed(futures,timeout=TOTAL_DEADLINE):
            i=futures[future]
            try: rows[i]=future.result()
            except Exception as exc:
                rows[i]={**sources[i],"state":"timeout","confidence":0,"signal_weight":0,"eligible_for_aggregation":False,"retry_next_run":True,"error":repr(exc),"checked_at":datetime.now(timezone.utc).isoformat()}
    for i,r in enumerate(rows):
        if r is None: rows[i]={**sources[i],"state":"timeout","confidence":0,"signal_weight":0,"eligible_for_aggregation":False,"retry_next_run":True,"error":"global deadline exceeded"}
    groups={}
    for r in rows: groups.setdefault(r.get("topic",r.get("type","unknown")),[]).append(r)
    routing=[]
    for key,items in groups.items():
        ranked=sorted(items,key=lambda x:(x["signal_weight"],x["confidence"]),reverse=True)
        primary=next((x for x in ranked if x["eligible_for_aggregation"]),None)
        routing.append({"group":key,"primary":primary["name"] if primary else None,"fallbacks":[x["name"] for x in ranked if not primary or x["name"]!=primary["name"]][:3]})
    active=sum(bool(r["eligible_for_aggregation"]) for r in rows); unavailable=sum(r["state"] in {"unavailable","timeout"} for r in rows)
    graph=load_graph(); elapsed=round(time.monotonic()-started,2)
    payload={"model":"BabiMind","pipeline_version":"1.4","generated_at":datetime.now(timezone.utc).isoformat(),"stages":["health","content","freshness","confidence","fallback","signal_weight","graph_intelligence"],"missing_data_policy":"SKIP_CURRENT_RUN_AND_RETRY_NEXT_RUN","execution":{"max_workers":MAX_WORKERS,"default_timeout_seconds":DEFAULT_TIMEOUT,"total_deadline_seconds":TOTAL_DEADLINE,"elapsed_seconds":elapsed},"summary":{"total_sources":len(rows),"active_sources":active,"unavailable_sources":unavailable},"graph_intelligence":graph,"sources":rows,"routing":routing}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"BabiMind pipeline: {len(rows)} sources, {active} active, {unavailable} unavailable; elapsed={elapsed}s")

if __name__=="__main__": main()
