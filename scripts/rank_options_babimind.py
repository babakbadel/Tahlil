#!/usr/bin/env python3
"""BabiMind option ranking.
Uses realtime option snapshot, infers spot from call/put parity when the
snapshot has no underlying price, then calculates BS IV/Greeks and ranking.
Never fabricates an IV when the inputs are insufficient.
"""
from __future__ import annotations
import json, math, re
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/latest/options_realtime.json'; OUT_JSON=ROOT/'reports/options_babimind_ranked.json'; OUT_MD=ROOT/'reports/options_babimind_ranked.md'; R=0.25
ALIASES={'underlying':['underlying','underlying_symbol','base_symbol','stock','stock_symbol','asset','نماد_پایه','نمادپایه','سهم_پایه'],'symbol':['symbol','option_symbol','contract','ticker','نماد','نماد_اختیار','نام_نماد'],'strike':['strike','strike_price','exercise_price','قیمت_اعمال','قیمتاعمال','استرایک'],'price':['price','last','last_price','close','close_price','option_price','قیمت','آخرین','آخرین_قیمت'],'bid':['bid','best_bid','buy_price','قیمت_خرید'],'ask':['ask','best_ask','sell_price','قیمت_فروش'],'iv':['iv','implied_volatility','implied_vol','نوسان_ضمنی','نوسانضمنی'],'delta':['delta','دلتا'],'gamma':['gamma','گاما'],'theta':['theta','تتا'],'vega':['vega','وگا'],'expiry':['expiry','expiration','expiry_date','maturity','سررسید','تاریخ_سررسید'],'volume':['volume','trade_volume','حجم'],'open_interest':['open_interest','oi','موقعیت_باز'],'underlying_price':['underlying_price','spot','last_underlying','base_price','قیمت_پایه','قیمت_سهم']}
def norm(s):return str(s).strip().replace('ي','ی').replace('ك','ک').replace('\u200c','').upper()
def num(v):
 if v is None or v=='':return None
 if isinstance(v,(int,float)):return float(v)
 s=str(v).replace(',','').replace('٬','').replace('٪','%').strip()
 try:return float(s[:-1])/100 if s.endswith('%') else float(s)
 except:return None
def get(d,aliases):
 if not isinstance(d,dict):return None
 nd={norm(k):v for k,v in d.items()}
 for a in aliases:
  if norm(a) in nd:return nd[norm(a)]
 return None
def flatten(x):
 if isinstance(x,list):
  for v in x:yield from flatten(v)
 elif isinstance(x,dict):
  keys={norm(k) for k in x}
  if any(norm(a) in keys for a in ALIASES['symbol']) or any(norm(a) in keys for a in ALIASES['strike']):yield x
  for v in x.values():
   if isinstance(v,(dict,list)):yield from flatten(v)
def target(r):
 s=norm(' '.join(str(get(r,a) or '') for a in [ALIASES['underlying'],ALIASES['symbol']]))
 for name,parts in {'فملی':['فملی','FEMLI','ضملی','طملی'],'وبملت':['وبملت','WEMELAT','ضملت','طملت'],'شپنا':['شپنا','SHAPNA','ضشنا','طشنا'],'خساپا':['خساپا','KHODRO','ضسپا','طسپا']}.items():
  if any(x in s for x in parts):return name
 return None
def opt_type(r):
 t=norm(get(r,['type','option_type','side','نوع']) or '');s=norm(get(r,ALIASES['symbol']) or '')
 if 'PUT' in t or 'پوت' in t or t=='P':return 'PUT'
 if 'CALL' in t or 'کال' in t or t=='C':return 'CALL'
 if s.startswith('ض') or any(x in s for x in ['ضملی','ضملت','ضشنا','ضسپا']):return 'CALL'
 if s.startswith('ط') or any(x in s for x in ['طملی','طملت','طشنا','طسپا']):return 'PUT'
 return None
def jalali_to_gregorian(jy,jm,jd):
 jy-=979;jm-=1;jd-=1;j=365*jy+jy//33*8+((jy%33)+3)//4+(31*jm if jm<6 else 186+30*(jm-6))+jd;g=j+79;gy=1600+400*(g//146097);g%=146097;leap=True
 if g>=36525:
  g-=1;gy+=100*(g//36524);g%=36524
  if g>=365:g+=1
  else:leap=False
 gy+=4*(g//1461);g%=1461
 if g>=366:leap=False;g-=1;gy+=g//365;g%=365
 gd=g+1;md=[31,29 if leap else 28,31,30,31,30,31,31,30,31,30,31];gm=1
 while gd>md[gm-1]:gd-=md[gm-1];gm+=1
 return gy,gm,gd
def parse_date(v):
 if v is None:return None
 s=str(v).strip().replace('/','-');m=re.search(r'(1[34]\d{2})[-]?(\d{1,2})[-]?(\d{1,2})',s)
 if m:
  y,mo,d=map(int,m.groups())
  if 1300<=y<=1499:y,mo,d=jalali_to_gregorian(y,mo,d)
  try:return datetime(y,mo,d,tzinfo=timezone.utc)
  except:return None
 for f in ('%Y-%m-%d','%Y-%m-%dT%H:%M:%S','%Y-%m-%dT%H:%M:%S.%f'):
  try:return datetime.strptime(s[:26],f).replace(tzinfo=timezone.utc)
  except:pass
 return None
def cdf(x):return .5*(1+math.erf(x/math.sqrt(2)))
def pdf(x):return math.exp(-x*x/2)/math.sqrt(2*math.pi)
def bs_price(S,K,T,sig,typ,r=R):
 if min(S,K,T,sig)<=0:return None
 d1=(math.log(S/K)+(r+.5*sig*sig)*T)/(sig*math.sqrt(T));d2=d1-sig*math.sqrt(T)
 return S*cdf(d1)-K*math.exp(-r*T)*cdf(d2) if typ=='CALL' else K*math.exp(-r*T)*cdf(-d2)-S*cdf(-d1)
def implied_vol(S,K,T,P,typ):
 if not all(x is not None for x in [S,K,T,P]) or min(S,K,T,P)<=0:return None
 intrinsic=max(0,S-K) if typ=='CALL' else max(0,K-S)
 if P<intrinsic*.999:return None
 lo,hi=1e-5,5
 if bs_price(S,K,T,hi,typ)<P:return None
 for _ in range(80):
  mid=(lo+hi)/2
  if bs_price(S,K,T,mid,typ)<P:lo=mid
  else:hi=mid
 return (lo+hi)/2
def greeks(S,K,T,sig,typ,r=R):
 if not all(x is not None for x in [S,K,T,sig]) or min(S,K,T,sig)<=0:return (None,)*4
 d1=(math.log(S/K)+(r+.5*sig*sig)*T)/(sig*math.sqrt(T));d2=d1-sig*math.sqrt(T);gamma=pdf(d1)/(S*sig*math.sqrt(T));vega=S*pdf(d1)*math.sqrt(T)/100
 if typ=='CALL':delta=cdf(d1);theta=(-S*pdf(d1)*sig/(2*math.sqrt(T))-r*K*math.exp(-r*T)*cdf(d2))/365
 else:delta=cdf(d1)-1;theta=(-S*pdf(d1)*sig/(2*math.sqrt(T))+r*K*math.exp(-r*T)*cdf(-d2))/365
 return delta,gamma,theta,vega
def infer_spots(rows):
 groups={}
 for r in rows:groups.setdefault((r['underlying'],r['expiry_key']),[]).append(r)
 spots={}
 for key,rs in groups.items():
  cs={r['strike']:r['price'] for r in rs if r['option_type']=='CALL' and r['price'] is not None};ps={r['strike']:r['price'] for r in rs if r['option_type']=='PUT' and r['price'] is not None};vals=[]
  T=max([(r['days_to_expiry'] or 0)/365 for r in rs],default=0)
  for k,c in cs.items():
   if k in ps:vals.append(c-ps[k]+k*math.exp(-R*T))
  if vals:vals.sort();spots[key]=vals[len(vals)//2]
 return spots
def score(r):
 s=35
 if r['underlying_price'] is not None:s+=8
 if r['iv'] is not None:s+=12
 if r['delta'] is not None:s+=5
 if r['gamma'] is not None:s+=3
 if r['theta'] is not None:s+=3
 if r['vega'] is not None:s+=3
 if r['volume'] is not None:s+=min(8,2*math.log1p(max(0,r['volume'])))
 if r['open_interest'] is not None:s+=min(8,2*math.log1p(max(0,r['open_interest'])))
 d=r['days_to_expiry'] or 0
 if 20<=d<=120:s+=8
 elif d>0:s+=4
 if r['underlying_price'] and r['strike']:
  m=abs(r['strike']-r['underlying_price'])/r['underlying_price']
  if m<=.10:s+=7
  elif m<=.20:s+=3
 return round(min(100,s),2)
def main():
 raw=json.loads(SRC.read_text(encoding='utf-8'));rows=[]
 for rec in flatten(raw):
  u=target(rec);typ=opt_type(rec);dt=parse_date(get(rec,ALIASES['expiry']))
  if not u or not typ or not dt:continue
  r={'underlying':u,'symbol':get(rec,ALIASES['symbol']),'option_type':typ,'strike':num(get(rec,ALIASES['strike'])),'price':num(get(rec,ALIASES['price'])),'bid':num(get(rec,ALIASES['bid'])),'ask':num(get(rec,ALIASES['ask'])),'iv':num(get(rec,ALIASES['iv'])),'delta':num(get(rec,ALIASES['delta'])),'gamma':num(get(rec,ALIASES['gamma'])),'theta':num(get(rec,ALIASES['theta'])),'vega':num(get(rec,ALIASES['vega'])),'volume':num(get(rec,ALIASES['volume'])),'open_interest':num(get(rec,ALIASES['open_interest'])),'underlying_price':num(get(rec,ALIASES['underlying_price'])),'expiry':get(rec,ALIASES['expiry'])}
  r['days_to_expiry']=round((dt-datetime.now(timezone.utc)).total_seconds()/86400,2)
  if r['days_to_expiry']<0 or not r['strike'] or not r['price'] or r['price']<=0:continue
  r['expiry_key']=dt.date().isoformat();rows.append(r)
 spots=infer_spots(rows)
 for r in rows:
  if r['underlying_price'] is None:r['underlying_price']=spots.get((r['underlying'],r['expiry_key']))
  S,K,T,P=r['underlying_price'],r['strike'],max(r['days_to_expiry']/365,1e-8),r['price']
  if r['iv'] is None:r['iv']=implied_vol(S,K,T,P,r['option_type'])
  if r['iv'] is not None and r['iv']>5:r['iv']=None
  if r['delta'] is None or r['gamma'] is None or r['theta'] is None or r['vega'] is None:
   g=greeks(S,K,T,r['iv'],r['option_type']) if r['iv'] else (None,)*4
   for k,v in zip(('delta','gamma','theta','vega'),g):
    if r[k] is None:r[k]=v
  if S is not None:
   intrinsic=max(0,S-K) if r['option_type']=='CALL' else max(0,K-S);r['intrinsic_value']=round(intrinsic,4);r['time_value']=round(P-intrinsic,4);r['breakeven']=round(K+P,4) if r['option_type']=='CALL' else round(K-P,4)
  else:r['intrinsic_value']=r['time_value']=r['breakeven']=None
  r.pop('expiry_key');r['babimind_score']=score(r);r['decision']='BUY' if r['babimind_score']>=80 else 'HOLD' if r['babimind_score']>=60 else 'AVOID'
 best={}
 for r in rows:
  k=r['symbol'] or f"{r['underlying']}|{r['option_type']}|{r['strike']}|{r['expiry']}"
  if k not in best or r['babimind_score']>best[k]['babimind_score']:best[k]=r
 rows=sorted(best.values(),key=lambda r:(-r['babimind_score'],r['underlying'],r['option_type'],r['strike']))
 for i,r in enumerate(rows,1):r['rank']=i
 generated=datetime.now(timezone.utc).isoformat();OUT_JSON.parent.mkdir(parents=True,exist_ok=True);OUT_JSON.write_text(json.dumps({'generated_at_utc':generated,'record_count':len(rows),'records':rows},ensure_ascii=False,indent=2),encoding='utf-8')
 lines=['# BabiMind Option Ranking','',f'Generated: {generated}',f'Contracts ranked: {len(rows)}','', '| Rank | Underlying | Contract | Type | Score | Decision | Strike | Price | IV | Delta | Gamma | Theta | Vega | Days | BE |','|---:|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for r in rows:
  f=lambda x:'-' if x is None else (f'{x:.6f}' if isinstance(x,float) else str(x));lines.append(f"| {r['rank']} | {r['underlying']} | {r.get('symbol') or '-'} | {r['option_type']} | {r['babimind_score']:.1f} | {r['decision']} | {f(r['strike'])} | {f(r['price'])} | {f(r['iv'])} | {f(r['delta'])} | {f(r['gamma'])} | {f(r['theta'])} | {f(r['vega'])} | {f(r['days_to_expiry'])} | {f(r['breakeven'])} |")
 OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8');print(f'ranked {len(rows)} contracts')
if __name__=='__main__':main()
