#!/usr/bin/env python3
"""Collect public US macro observations; never fabricate unavailable Iranian series."""
import csv,io,json,urllib.request
from pathlib import Path
from datetime import datetime,timezone
SERIES={'us_treasury_10y':'DGS10','us_treasury_2y':'DGS2','us_unemployment':'UNRATE','us_policy_upper':'DFEDTARU','us_cpi':'CPIAUCSL','us_payrolls':'PAYEMS','us_real_yield_10y':'DFII10','us_oil_wti':'DCOILWTICO'}
def get_series(series):
 url='https://fred.stlouisfed.org/graph/fredgraph.csv?id='+series
 req=urllib.request.Request(url,headers={'User-Agent':'BabiMind/3.0 economic-research'})
 with urllib.request.urlopen(req,timeout=18) as res:body=res.read().decode('utf-8-sig')
 rows=[]
 for row in csv.DictReader(io.StringIO(body)):
  try:rows.append((row.get('DATE') or row.get('observation_date'),float(row[series])))
  except (TypeError,ValueError,KeyError):pass
 if not rows:raise ValueError('no valid observations')
 return rows
def main():
 now=datetime.now(timezone.utc)
 out={'as_of':now.isoformat(),'source':'Federal Reserve Bank of St. Louis FRED public CSV','series':{},'indicators':{},'iran_reference':{'unemployment_rate':{'value':9.1,'unit':'percent','period':'1405-Q1','source':'https://www.tasnimnews.ir/fa/news/1405/05/07/3659367/'},'participation_rate':{'value':40.7,'unit':'percent','period':'1405-Q1','source':'https://www.tasnimnews.ir/fa/news/1405/05/07/3659367/'},'employment_yoy_change':{'value':-450000,'unit':'people','period':'1405-Q1','source':'https://www.tasnimnews.ir/fa/news/1405/05/07/3659367/'}}}
 for name,series in SERIES.items():
  try:
   rows=get_series(series)
   out['series'][name]={'status':'available','value':rows[-1][1],'observed_at':rows[-1][0],'previous_value':rows[-2][1] if len(rows)>1 else None,'source':'https://fred.stlouisfed.org/series/'+series}
  except Exception as e:out['series'][name]={'status':'unavailable','error':str(e)[:160]}
 for name,base,sign in [('us_unemployment_change','us_unemployment',1),('us_real_yield','us_real_yield_10y',1)]:
  s=out['series'].get(base,{})
  if s.get('status')!='available' or s.get('previous_value') is None:continue
  observed=datetime.fromisoformat(s['observed_at']).replace(tzinfo=timezone.utc)
  if (now-observed).days>60:continue
  delta=s['value']-s['previous_value']
  out['indicators'][name]={'signal':max(-1,min(1,delta*sign)),'observed_at':s['observed_at'],'source':s['source'],'method':'last_observation_change_clipped_to_unit_range'}
 for name,series in [('us_yield_curve_10y_2y','us_treasury_10y')]:
  a=out['series'].get('us_treasury_10y',{});b=out['series'].get('us_treasury_2y',{})
  if a.get('status')=='available' and b.get('status')=='available' and a['observed_at']==b['observed_at']:
   out['indicators'][name]={'signal':max(-1,min(1,(a['value']-b['value'])/2)),'observed_at':a['observed_at'],'source':a['source']+'; '+b['source'],'method':'spread_percentage_points_divided_by_two_clipped'}
 path=Path('data/latest/babimind_cycle_observations.json');path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'available':sum(s['status']=='available' for s in out['series'].values()),'indicators':list(out['indicators'])}))
if __name__=='__main__':main()
