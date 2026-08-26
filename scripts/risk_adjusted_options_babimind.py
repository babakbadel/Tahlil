#!/usr/bin/env python3
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'reports/options_babimind_scenario_ranked.json'
OUTJ=ROOT/'reports/options_babimind_risk_adjusted.json'
OUTM=ROOT/'reports/options_babimind_risk_adjusted.md'
def n(x):
    try:return float(x)
    except:return None
def calc(r):
    base=n(r.get('score')) or 0
    ups=[x for x in (n(r.get('pl_plus_5')),n(r.get('pl_plus_10')),n(r.get('pl_plus_20'))) if x is not None]
    downs=[abs(x) for x in (n(r.get('pl_minus_5')),n(r.get('pl_minus_10')),n(r.get('pl_minus_20'))) if x is not None]
    rr=max(ups)/max(downs) if ups and downs and max(downs)>0 else None
    parts=[base]
    iv=n(r.get('iv')); theta=n(r.get('theta')); delta=n(r.get('delta')); days=n(r.get('days')); price=n(r.get('price'))
    if rr is not None: parts.append(100*(rr/(1+rr)))
    if iv is not None: parts.append(max(0,100-min(100,iv*100)))
    if theta is not None and price: parts.append(max(0,100-min(100,abs(theta)/price*36500)))
    if delta is not None: parts.append(max(0,100-abs(abs(delta)-.55)*100))
    if days is not None: parts.append(max(0,100-abs(days-45)*1.2))
    return round(.65*sum(parts)/len(parts)+.35*base,2),rr

data=json.loads(SRC.read_text()); rows=data if isinstance(data,list) else data.get('contracts',data.get('results',[])); out=[]
for r in rows:
    x=dict(r); s,rr=calc(r); x['risk_adjusted_score']=s; x['risk_reward_ratio']=round(rr,3) if rr is not None else None; out.append(x)
out.sort(key=lambda x:x['risk_adjusted_score'],reverse=True)
for i,x in enumerate(out,1):x['risk_adjusted_rank']=i
OUTJ.write_text(json.dumps({'contracts':out},ensure_ascii=False,indent=2))
cols=['risk_adjusted_rank','underlying','contract','type','risk_adjusted_score','price','strike','iv','delta','theta','days','risk_reward_ratio','pl_minus_10','pl_minus_20','pl_plus_10','pl_plus_20']
md=['# BabiMind Risk-Adjusted Option Ranking','',f'Contracts ranked: {len(out)}','', '| '+' | '.join(c for c in cols)+' |','|'+'---:|'*len(cols)]
for x in out:md.append('| '+' | '.join('' if x.get(c) is None else str(x.get(c)) for c in cols)+' |')
OUTM.write_text('\n'.join(md)+'\n')
print(len(out))
