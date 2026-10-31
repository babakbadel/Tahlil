#!/usr/bin/env python3
"""BabiMind v3 fixed-capital scenario game; assumptions are not fitted probabilities."""
import json, math, argparse
from pathlib import Path
from datetime import datetime, timezone
MARKETS=['usd','gold','stocks','housing','auto','fixed_income','crypto']
INITIAL=[18.,20.,19.,18.,7.,15.,3.]
SCENARIOS={'stagflation':(.55,[.55,.68,.30,.12,.10,.40,.15]),'shock':(.30,[.86,.90,-.15,-.18,-.05,.48,-.12]),'relief':(.15,[.15,.20,.95,.55,.40,.32,.60])}
FACTORS={'us_real_yield':[-.2,-.7,-.35,-.1,-.1,.2,-.5],'us_unemployment_change':[.1,.2,-.6,-.3,-.3,.35,-.5],'us_yield_curve_10y_2y':[.1,-.1,.2,.1,.1,-.1,.2],'us_credit_stress':[.3,.5,-.7,-.35,-.3,.3,-.8],'global_oil_shock':[.45,.4,-.45,-.3,-.35,.1,-.3],'iran_inflation_acceleration':[.65,.8,-.4,.15,.05,-.6,.1],'iran_employment_change':[-.15,-.15,.6,.4,.35,.1,.2],'iran_participation_change':[-.1,-.1,.4,.2,.2,.1,.1],'iran_real_policy_rate':[-.45,-.55,-.1,-.2,-.25,.75,-.2],'iran_fx_access':[-.65,-.5,.85,.25,.25,.1,.35],'iran_energy_shortage':[.4,.4,-.65,-.3,-.4,.1,-.2],'iran_government_bond_supply':[.1,.1,-.4,-.2,-.15,.35,-.1],'iran_social_confidence':[-.4,-.4,.75,.3,.3,.1,.4]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--observations');p.add_argument('--output',default='reports/babimind_cycle_game_v3.json');a=p.parse_args()
 raw=json.loads(Path(a.observations).read_text()) if a.observations and Path(a.observations).exists() else {}
 valid={};rejected={}
 for k in FACTORS:
  v=raw.get('indicators',{}).get(k)
  if not isinstance(v,dict) or not isinstance(v.get('signal'),(float,int)) or not v.get('source') or not v.get('observed_at'):rejected[k]='missing_or_unverified';continue
  try:age=(datetime.now(timezone.utc).date()-datetime.fromisoformat(v['observed_at'].replace('Z','+00:00')).date()).days
  except (ValueError,TypeError):rejected[k]='bad_date';continue
  if not 0<=age<=100 or not -1<=v['signal']<=1:rejected[k]='stale_or_invalid';continue
  valid[k]=float(v['signal'])
 runs={}
 for name,(prob,base) in SCENARIOS.items():
  x=INITIAL[:];history=[x[:]]
  for t in range(12):
   score=[1.5*base[i]+.35*sum(FACTORS[k][i]*v for k,v in valid.items())+.2*math.log((x[i]+1)/15)-.35*x[i]/100 for i in range(7)]
   z=[math.exp((v-max(score))/.6) for v in score];target=[100*v/sum(z) for v in z]
   x=[.88*q+.12*w for q,w in zip(x,target)];history.append(x[:])
  runs[name]={'probability':prob,'final':x,'history':history}
 expected=[sum(r['probability']*r['final'][i] for r in runs.values()) for i in range(7)]
 out={'model':'babimind_cycle_game_v3','generated_at':datetime.now(timezone.utc).isoformat(),'status':'partial_observed' if valid else 'scenario_only','markets':MARKETS,'initial':INITIAL,'observed_factors':valid,'missing_or_rejected_factors':rejected,'scenarios':runs,'expected':expected,'capital_conservation':all(abs(sum(row)-100)<1e-8 for r in runs.values() for row in r['history']),'warning':'Subjective scenario probabilities; not calibrated, not Nash equilibrium; missing is not zero.'}
 dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(out,ensure_ascii=False,indent=2))
 print(json.dumps({'status':out['status'],'capital_conservation':out['capital_conservation'],'observed_count':len(valid)}))
if __name__=='__main__':main()
