#!/usr/bin/env python3
"""Second-pass BabiMind option scoring.
Scores contracts using IV, delta, theta, time value, liquidity and expiry P/L
at -20/-10/-5/0/+5/+10/+20% moves of the inferred underlying.
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'reports/options_babimind_ranked.json'
OUTJ=ROOT/'reports/options_babimind_scenario_ranked.json'
OUTM=ROOT/'reports/options_babimind_scenario_ranked.md'
MOVES=(-.20,-.10,-.05,.05,.10,.20)

def n(v):
    try:return float(v)
    except:return None

def expiry_pnl(r, move):
    s=n(r.get('underlying_price')); k=n(r.get('strike')); p=n(r.get('price'))
    if None in (s,k,p) or s<=0:return None
    st=s*(1+move)
    intrinsic=max(0,st-k) if r.get('option_type')=='CALL' else max(0,k-st)
    return intrinsic-p

def liquidity_score(r):
    v=n(r.get('volume')) or 0; oi=n(r.get('open_interest')) or 0
    return min(10, 2*math.log1p(max(0,v))+2*math.log1p(max(0,oi)))

def score(r):
    s=50.0
    iv=n(r.get('iv')); d=n(r.get('delta')); tv=n(r.get('time_value')); p=n(r.get('price')); days=n(r.get('days_to_expiry'))
    if iv is not None:
        # Prefer moderate IV relative to the set; raw IV alone is not a buy signal.
        s += 8 if .20 <= iv <= .70 else 3
    if d is not None:
        ad=abs(d); s += 8 if .35 <= ad <= .85 else 3
    if tv is not None and p:
        ratio=tv/p if p else 1
        s += 7 if 0.15 <= ratio <= .75 else 2
    if days is not None:
        s += 6 if 20 <= days <= 120 else 2
    s += liquidity_score(r)
    pnls={m:expiry_pnl(r,m) for m in MOVES}
    if r.get('option_type')=='CALL':
        if pnls[.10] is not None and pnls[.10] > 0:s+=5
        if pnls[.20] is not None and pnls[.20] > 0:s+=5
    else:
        if pnls[-.10] is not None and pnls[-.10] > 0:s+=5
        if pnls[-.20] is not None and pnls[-.20] > 0:s+=5
    # Penalize contracts that only win in the far tail.
    near=pnls.get(.05) if r.get('option_type')=='CALL' else pnls.get(-.05)
    if near is not None and near>0:s+=3
    return round(min(100,max(0,s)),2),pnls

def main():
    data=json.loads(SRC.read_text(encoding='utf-8'))
    rows=data.get('records',[])
    out=[]
    for r in rows:
        r=dict(r); s,pnls=score(r); r['scenario_pnl_pct']={f'{int(m*100):+d}%':pnls[m] for m in MOVES}; r['scenario_pnl_roi_pct']={f'{int(m*100):+d}%':(pnls[m]/r['price']*100 if pnls[m] is not None and r.get('price') else None) for m in MOVES}; r['babimind_scenario_score']=s; r['decision']='BUY' if s>=82 else 'HOLD' if s>=65 else 'AVOID'; out.append(r)
    out.sort(key=lambda x:(-x['babimind_scenario_score'],x.get('underlying',''),x.get('option_type',''),x.get('strike',0)))
    for i,r in enumerate(out,1):r['scenario_rank']=i
    generated=datetime.now(timezone.utc).isoformat()
    OUTJ.write_text(json.dumps({'generated_at_utc':generated,'record_count':len(out),'moves':MOVES,'records':out},ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# BabiMind Option Scenario Ranking','',f'Generated: {generated}',f'Contracts ranked: {len(out)}','', '| Rank | Underlying | Contract | Type | Score | Decision | Price | Strike | IV | Delta | Days | P/L -20% | P/L -10% | P/L +10% | P/L +20% |','|---:|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in out:
        def f(x): return '-' if x is None else f'{x:.2f}'
        p=r['scenario_pnl_pct']; lines.append(f"| {r['scenario_rank']} | {r.get('underlying','-')} | {r.get('symbol','-')} | {r.get('option_type','-')} | {r['babimind_scenario_score']:.2f} | {r['decision']} | {f(n(r.get('price')))} | {f(n(r.get('strike')))} | {f(n(r.get('iv')))} | {f(n(r.get('delta')))} | {f(n(r.get('days_to_expiry')))} | {f(p['-20%'])} | {f(p['-10%'])} | {f(p['+10%'])} | {f(p['+20%'])} |")
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'scenario-ranked {len(out)} contracts')

if __name__=='__main__':main()
