#!/usr/bin/env python3
"""Bounded, deduplicated and auditable historical memory for BabiMind."""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MEMORY=ROOT/'reports'/'babimind_memory.json'
CONTEXT=ROOT/'reports'/'babimind_memory_context.json'
LLM=ROOT/'reports'/'babimind_llm.json'
MAX_RUNS=100
CONTEXT_RUNS=20
MAX_MEMORY_BYTES=2_000_000

def now(): return datetime.now(timezone.utc).isoformat()
def empty(): return {'model':'BabiMind','version':2,'policy':'historical_context_only','runs':[]}

def load():
    if not MEMORY.exists(): return empty()
    try:
        d=json.loads(MEMORY.read_text(encoding='utf-8'))
        if not isinstance(d,dict) or not isinstance(d.get('runs',[]),list): raise ValueError('invalid schema')
        d.setdefault('model','BabiMind'); d.setdefault('version',2); d.setdefault('policy','historical_context_only')
        return d
    except Exception as e:
        print(f'[BabiMind Memory] unreadable memory; starting clean: {e}')
        return empty()

def compact(d):
    a=d.get('analysis') or {}
    return {'timestamp':d.get('generated_at') or now(),'provider':d.get('provider'),'model':d.get('model'),'regime':a.get('regime'),'scenarios':a.get('scenarios') or {},'market_implications':a.get('market_implications'),'confidence':a.get('confidence'),'data_gaps':a.get('data_gaps',[])}

def fp(row):
    basis={k:v for k,v in row.items() if k!='timestamp'}
    return hashlib.sha256(json.dumps(basis,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:20]

def normalize(runs):
    seen=set(); clean=[]
    for r in runs:
        if not isinstance(r,dict): continue
        r.setdefault('fingerprint',fp(r))
        if r['fingerprint'] in seen: continue
        seen.add(r['fingerprint']); clean.append(r)
    clean=clean[-MAX_RUNS:]
    while clean and len(json.dumps(clean,ensure_ascii=False,separators=(',',':')).encode())>MAX_MEMORY_BYTES: clean.pop(0)
    return clean

def save(mem):
    mem['runs']=normalize(mem.get('runs',[])); mem['updated_at']=now()
    MEMORY.parent.mkdir(parents=True,exist_ok=True)
    MEMORY.write_text(json.dumps(mem,ensure_ascii=False,indent=2),encoding='utf-8')

def maintenance():
    mem=load(); before=len(mem.get('runs',[])); save(mem); size=MEMORY.stat().st_size if MEMORY.exists() else 0
    print(f'[BabiMind Memory] maintenance before={before} after={len(mem["runs"])} bytes={size}')

def prepare():
    maintenance(); d=load(); runs=d.get('runs',[])[-CONTEXT_RUNS:]
    context={'memory_version':d.get('version',2),'historical_runs_available':len(d.get('runs',[])),'context_runs':len(runs),'recent_runs':runs,'instruction':'Historical context only. Never treat memory as current market data. Prefer current source evidence. Use memory for regime changes, recurring errors, calibration and confidence evolution.'}
    CONTEXT.parent.mkdir(parents=True,exist_ok=True); CONTEXT.write_text(json.dumps(context,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'[BabiMind Memory] prepared {len(runs)} recent runs')

def ingest():
    if not LLM.exists(): print('[BabiMind Memory] no LLM result; nothing to ingest'); return
    try: d=json.loads(LLM.read_text(encoding='utf-8'))
    except Exception as e: print(f'[BabiMind Memory] invalid LLM output: {e}'); return
    if d.get('status')!='ok': print('[BabiMind Memory] non-success result not added'); return
    row=compact(d); row['fingerprint']=fp(row); mem=load(); runs=normalize(mem.get('runs',[]))
    if any(x.get('fingerprint')==row['fingerprint'] for x in runs): print('[BabiMind Memory] duplicate run skipped'); return
    runs.append(row); mem['runs']=runs; save(mem)
    print(f'[BabiMind Memory] ingested run total={len(mem["runs"])} bytes={MEMORY.stat().st_size}')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--prepare',action='store_true'); p.add_argument('--ingest',action='store_true'); p.add_argument('--maintenance',action='store_true'); a=p.parse_args()
    if a.maintenance: maintenance()
    if a.prepare: prepare()
    if a.ingest: ingest()
    if not (a.prepare or a.ingest or a.maintenance): prepare()
if __name__=='__main__': main()
