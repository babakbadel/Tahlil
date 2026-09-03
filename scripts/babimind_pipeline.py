#!/usr/bin/env python3
"""Unified BabiMind source -> signal pipeline.

Network checks are bounded and never allowed to block the model indefinitely.
"""
from __future__ import annotations
import json, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"config"/"babimind_source_health.json"
THESIS_CONFIG=ROOT/"config"/"babimind_symbol_theses.json"
OUT=ROOT/"reports"/"babimind_pipeline.json"
GRAPH_OUT=ROOT/"reports"/"babimind_graph.json"
MAX_WORKERS=24
DEFAULT_TIMEOUT=3
TOTAL_DEADLINE=30

def endpoint_check(url, timeout=DEFAULT_TIMEOUT):
    started=time.monotonic()
    try:
        req=Request(url,headers={"User-Agent":"BabiMind-Pipeline/1.6"})
        with urlopen(req,timeout=timeout) as r:
            body=r.read(4096)
            status=getattr(r,"status",200)
            return {"status":"ok" if 200<=status<400 else "error","http_status":status,"content_type":r.headers.get("Content-Type",""),"bytes":len(body),"latency_ms":round((time.monotonic()-started)*1000,1),"content_check":"nonempty" if body else "empty"}
    except HTTPError as e: return {"status":"error","http_status":e.code,"error":str(e),"content_check":"failed"}
    except (URLError,TimeoutError,OSError) as e: return {"status":"unavailable","error":str(e),"content_check":"failed"}
    except Exception as e: return {"status":"error","error":repr(e),"content_check":"failed"}

def freshness(s,now):
    stamp=s.get("release_timestamp") or s.get("observation_timestamp")
    if not stamp:return .75
    try:
        age=max(0,(now-datetime.fromisoformat(stamp.replace("Z","+00:00"))).total_seconds()/86400)
        return round(2**(-age/max(float(s.get("freshness_half_life_days",7)),.1)),4)
    except (ValueError,TypeError):return .5

def confidence(s,availability,fresh):
    vals=[float(s.get(k,d)) for k,d in [("authority_score",.75),("independence_score",.75),("coverage_score",.75),("reproducibility_score",.75),("api_reliability_score",.75)]]
    revision=1-float(s.get("revision_risk",.1))
    structural=.20*vals[0]+.15*vals[1]+.15*vals[2]+.15*vals[3]+.15*vals[4]+.20*revision
    return round(max(0,min(1,structural*availability*fresh)),4)

def check_source(src):
    result=endpoint_check(src["url"]); now=datetime.now(timezone.utc); fresh=freshness(src,now); state=result.get("status","error")
    if state=="ok" and result.get("content_check")!="nonempty":state="partial"
    if state=="ok" and fresh<.25:state="stale"
    avail=1.0 if state=="ok" else 0.0; conf=confidence(src,avail,fresh); weight=round(.25+.75*conf,4) if state=="ok" else 0
    return {**src,**result,"state":state,"freshness":fresh,"confidence":conf,"signal_weight":weight,"eligible_for_aggregation":weight>0,"retry_next_run":state!="ok","checked_at":now.isoformat()}

def load_graph():
    if not GRAPH_OUT.exists():return {"available":False,"graph_score":None,"graph_confidence":0.0,"graph_regime":"unavailable"}
    try:return json.loads(GRAPH_OUT.read_text(encoding="utf-8"))
    except Exception as e:return {"available":False,"graph_score":None,"graph_confidence":0.0,"graph_regime":"error","reason":repr(e)}

def load_symbol_theses():
    if not THESIS_CONFIG.exists():
        return {"version":0,"symbols":{},"available":False}
    try:
        payload=json.loads(THESIS_CONFIG.read_text(encoding="utf-8"))
        return {"version":payload.get("version",0),"updated_at":payload.get("updated_at"),"symbols":payload.get("symbols",{}),"available":True}
    except Exception as e:
        return {"version":0,"symbols":{},"available":False,"error":repr(e)}

def main():
    started=time.monotonic(); catalog=json.loads(CONFIG.read_text(encoding="utf-8")); sources=catalog.get("sources",[]); rows=[None]*len(sources)
    print(f"[BabiMind] checking {len(sources)} sources; workers={MAX_WORKERS}; timeout={DEFAULT_TIMEOUT}s; deadline={TOTAL_DEADLINE}s",flush=True)
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS,max(1,len(sources)))) as pool:
        futures={pool.submit(check_source,s):i for i,s in enumerate(sources)}
        try:
            for n,f in enumerate(as_completed(futures,timeout=TOTAL_DEADLINE),1):
                i=futures[f]
                try:rows[i]=f.result()
                except Exception as e:rows[i]={**sources[i],"state":"error","confidence":0,"signal_weight":0,"eligible_for_aggregation":False,"retry_next_run":True,"error":repr(e)}
                print(f"[BabiMind] progress {n}/{len(sources)}",flush=True)
        except TimeoutError:
            print("[BabiMind] global deadline reached; marking unfinished sources for retry",flush=True)
    for i,r in enumerate(rows):
        if r is None:rows[i]={**sources[i],"state":"timeout","confidence":0,"signal_weight":0,"eligible_for_aggregation":False,"retry_next_run":True,"error":"global deadline exceeded"}
    groups={}
    for r in rows:groups.setdefault(r.get("topic",r.get("type","unknown")),[]).append(r)
    routing=[]
    for key,items in groups.items():
        ranked=sorted(items,key=lambda x:(x.get("signal_weight",0),x.get("confidence",0)),reverse=True); primary=next((x for x in ranked if x.get("eligible_for_aggregation")),None)
        routing.append({"group":key,"primary":primary.get("name") if primary else None,"fallbacks":[x.get("name") for x in ranked if not primary or x.get("name")!=primary.get("name")][:3]})
    active=sum(bool(r.get("eligible_for_aggregation")) for r in rows); unavailable=sum(r.get("state") in {"unavailable","timeout"} for r in rows); elapsed=round(time.monotonic()-started,2)
    theses=load_symbol_theses()
    payload={"model":"BabiMind","pipeline_version":"1.6","generated_at":datetime.now(timezone.utc).isoformat(),"stages":["health","content","freshness","confidence","fallback","signal_weight","graph_intelligence","symbol_thesis"],"missing_data_policy":"SKIP_CURRENT_RUN_AND_RETRY_NEXT_RUN","execution":{"max_workers":MAX_WORKERS,"default_timeout_seconds":DEFAULT_TIMEOUT,"total_deadline_seconds":TOTAL_DEADLINE,"elapsed_seconds":elapsed},"summary":{"total_sources":len(rows),"active_sources":active,"unavailable_sources":unavailable,"symbol_theses":len(theses.get("symbols",{}))},"graph_intelligence":load_graph(),"symbol_theses":theses,"sources":rows,"routing":routing}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8"); print(f"[BabiMind] DONE sources={len(rows)} active={active} unavailable={unavailable} theses={len(theses.get('symbols',{}))} elapsed={elapsed}s",flush=True)

if __name__=="__main__":main()
