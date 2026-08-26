#!/usr/bin/env python3
"""Build a confidence-weighted clustered factor rotation snapshot.

The factor catalog is intentionally data-driven. If a live factor feed is not
available yet, the script emits an empty-but-valid snapshot instead of
inventing market observations.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PIPE=ROOT/"reports"/"babimind_pipeline.json"
FACTORS=ROOT/"config"/"babimind_factors.json"
OUT=ROOT/"reports"/"babimind_factor_rotation.json"


def main():
    pipeline=json.loads(PIPE.read_text(encoding="utf-8"))
    catalog=json.loads(FACTORS.read_text(encoding="utf-8")) if FACTORS.exists() else {"factors":[]}
    source_weights={x["name"]:x.get("signal_weight",0.25) for x in pipeline.get("sources",[])}
    rows=[]
    for f in catalog.get("factors",[]):
        sources=f.get("sources",[])
        weights=[source_weights[s] for s in sources if s in source_weights]
        source_weight=sum(weights)/len(weights) if weights else 0.25
        # No market value is fabricated: velocity/acceleration stay null until a feed exists.
        rows.append({**f,"source_weight":round(source_weight,4),"velocity":None,"acceleration":None,"direction":None})
    clusters={}
    for r in rows: clusters.setdefault(r.get("cluster","unclassified"),[]).append(r)
    output={"model":"BabiMind","generated_at":datetime.now(timezone.utc).isoformat(),"factor_count":len(rows),"clusters":clusters,"note":"Market velocity, acceleration and direction require observed factor data; this layer does not fabricate them."}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"factor rotation snapshot: {len(rows)} factors, {len(clusters)} clusters")

if __name__=="__main__": main()
