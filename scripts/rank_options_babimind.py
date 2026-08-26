#!/usr/bin/env python3
"""Robust BabiMind option ranking for the realtime option snapshot.

Important: never fabricate IV/Greeks. Supports Persian Jalali expiry dates and
Iranian option-symbol conventions (ض=CALL, ط=PUT) when explicit fields are absent.
"""
from __future__ import annotations
import json, math, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/latest/options_realtime.json'
OUT_JSON=ROOT/'reports/options_babimind_ranked.json'
OUT_MD=ROOT/'reports/options_babimind_ranked.md'

ALIASES={
'underlying':['underlying','underlying_symbol','base_symbol','stock','stock_symbol','asset','نماد_پایه','نمادپایه','سهم_پایه'],
'symbol':['symbol','option_symbol','contract','ticker','نماد','نماد_اختیار','نام_نماد'],
'strike':['strike','strike_price','exercise_price','قیمت_اعمال','قیمتاعمال','استرایک'],
'price':['price','last','last_price','close','close_price','option_price','قیمت','آخرین','آخرین_قیمت'],
'bid':['bid','best_bid','buy_price','قیمت_خرید'],'ask':['ask','best_ask','sell_price','قیمت_فروش'],
'iv':['iv','implied_volatility','implied_vol','نوسان_ضمنی','نوسانضمنی'],
'delta':['delta','دلتا'],'gamma':['gamma','گاما'],'theta':['theta','تتا'],'vega':['vega','وگا'],
'expiry':['expiry','expiration','expiry_date','maturity','سررسید','تاریخ_سررسید'],
'volume':['volume','trade_volume','حجم'],'open_interest':['open_interest','oi','موقعیت_باز'],
'underlying_price':['underlying_price','spot','last_underlying','base_price','قیمت_پایه','قیمت_سهم'],
}

def norm(s): return str(s).strip().replace('ي','ی').replace('ك','ک').replace('\u200c','').upper()
def num(v):
    if v is None or v=='': return None
    if isinstance(v,(int,float)): return float(v)
    s=str(v).replace(',','').replace('٬','').replace('٪','%').strip()
    try: return float(s[:-1])/100 if s.endswith('%') else float(s)
    except: return None

def get(d,aliases):
    if not isinstance(d,dict): return None
    nd={norm(k):v for k,v in d.items()}
    for a in aliases:
        if norm(a) in nd:return nd[norm(a)]
    return None

def flatten(x):
    if isinstance(x,list):
        for v in x: yield from flatten(v)
    elif isinstance(x,dict):
        keys={norm(k) for k in x}
        if any(norm(a) in keys for a in ALIASES['symbol']) or any(norm(a) in keys for a in ALIASES['strike']): yield x
        for v in x.values():
            if isinstance(v,(dict,list)): yield from flatten(v)

def target_from(r):
    text=' '.join(str(get(r,a) or '') for a in [ALIASES['underlying'],ALIASES['symbol']])
    s=norm(text)
    # Explicit and common Iranian option symbol fragments.
    if any(x in s for x in ['فملی','FEMLI','ضملی','طملی']): return 'فملی'
    if any(x in s for x in ['وبملت','WEMELAT','ضملت','طملت']): return 'وبملت'
    if any(x in s for x in ['شپنا','SHAPNA','ضشنا','طشنا']): return 'شپنا'
    if any(x in s for x in ['خساپا','KHODRO','ضسپا','طسپا']): return 'خساپا'
    return None

def option_type(r):
    t=norm(get(r,['type','option_type','side','نوع']) or '')
    s=norm(get(r,ALIASES['symbol']) or '')
    if any(x in t for x in ['PUT','P','فروش','پوت']): return 'PUT'
    if any(x in t for x in ['CALL','C','خرید','کال']): return 'CALL'
    # Iranian option naming convention: ض call, ط put.
    if s.startswith('ض') or 'ضملی' in s or 'ضملت' in s or 'ضشنا' in s or 'ضسپا' in s:return 'CALL'
    if s.startswith('ط') or 'طملی' in s or 'طملت' in s or 'طشنا' in s or 'طسپا' in s:return 'PUT'
    return None

# Jalali -> Gregorian conversion (integer algorithm; no external dependency).
def jalali_to_gregorian(jy,jm,jd):
    jy-=979; jm-=1; jd-=1
    j_day=365*jy + jy//33*8 + ((jy%33)+3)//4
    j_day += (31*jm if jm<6 else 186+30*(jm-6)) + jd
    g_day=j_day+79
    gy=1600+400*(g_day//146097); g_day%=146097
    leap=True
    if g_day>=36525:
        g_day-=1; gy+=100*(g_day//36524); g_day%=36524
        if g_day>=365: g_day+=1
        else: leap=False
    gy+=4*(g_day//1461); g_day%=1461
    if g_day>=366:
        leap=False; g_day-=1; gy+=g_day//365; g_day%=365
    gd=g_day+1
    month_days=[31,29 if leap else 28,31,30,31,30,31,31,30,31,30,31]
    gm=1
    while gd>month_days[gm-1]: gd-=month_days[gm-1]; gm+=1
    return gy,gm,gd

def parse_date(v):
    if v is None:return None
    s=str(v).strip().replace('/','-').replace('٫','.')
    # numeric YYYYMMDD, including Jalali 1405xxxx
    m=re.search(r'(1[34]\d{2})[-]?(\d{1,2})[-]?(\d{1,2})',s)
    if m:
        y,mo,d=map(int,m.groups())
        if 1300<=y<=1499:
            try:y,mo,d=jalali_to_gregorian(y,mo,d)
            except:return None
        try:return datetime(y,mo,d,tzinfo=timezone.utc)
        except:return None
    for fmt in ('%Y-%m-%d','%Y-%m-%dT%H:%M:%S','%Y-%m-%dT%H:%M:%S.%f'):
        try:return datetime.strptime(s[:26],fmt).replace(tzinfo=timezone.utc)
        except:pass
    return None

def clamp(x,a=0,b=100):return max(a,min(b,x))

def calc_score(r):
    quality=0
    for k in ('price','strike','expiry_dt','underlying_price'):
        if r.get(k) is not None:quality+=5
    liq=0
    if r.get('volume') is not None:liq+=min(10,2+2*math.log1p(max(0,r['volume'])))
    if r.get('open_interest') is not None:liq+=min(10,2+2*math.log1p(max(0,r['open_interest'])))
    pricing=10
    spot,strike,px=r.get('underlying_price'),r.get('strike'),r.get('price')
    if spot and strike:
        m=abs(spot-strike)/max(abs(spot),1)
        pricing=clamp(18-40*m,0,20)
    if px is not None and px>0:pricing+=3
    greek=5
    for k in ('iv','delta','gamma','theta','vega'):
        if r.get(k) is not None:greek+=3
    greek=clamp(greek,0,20)
    days=r.get('days_to_expiry')
    maturity=15 if days is not None and 20<=days<=120 else 10 if days is not None and days>120 else 6 if days is not None and days>0 else 0
    return round(clamp(quality+liq+pricing+greek+maturity),2)

def main():
    if not SRC.exists():raise SystemExit(f'missing {SRC}')
    raw=json.loads(SRC.read_text(encoding='utf-8'))
    records=[]
    for rec in flatten(raw):
        target=target_from(rec)
        if not target:continue
        expiry=get(rec,ALIASES['expiry']); dt=parse_date(expiry)
        r={'underlying':target,'symbol':get(rec,ALIASES['symbol']),'strike':num(get(rec,ALIASES['strike'])),'price':num(get(rec,ALIASES['price'])),'bid':num(get(rec,ALIASES['bid'])),'ask':num(get(rec,ALIASES['ask'])),'iv':num(get(rec,ALIASES['iv'])),'delta':num(get(rec,ALIASES['delta'])),'gamma':num(get(rec,ALIASES['gamma'])),'theta':num(get(rec,ALIASES['theta'])),'vega':num(get(rec,ALIASES['vega'])),'expiry':expiry,'expiry_dt':dt,'volume':num(get(rec,ALIASES['volume'])),'open_interest':num(get(rec,ALIASES['open_interest'])),'underlying_price':num(get(rec,ALIASES['underlying_price']))}
        r['option_type']=option_type(rec)
        r['days_to_expiry']=round((dt-datetime.now(timezone.utc)).total_seconds()/86400,2) if dt else None
        if r['days_to_expiry'] is not None and r['days_to_expiry']<0:continue
        if r['price'] is not None and r['strike'] is not None and r['underlying_price'] is not None:
            intrinsic=max(0,r['underlying_price']-r['strike']) if r['option_type']=='CALL' else max(0,r['strike']-r['underlying_price']) if r['option_type']=='PUT' else None
            r['intrinsic_value']=intrinsic
            r['time_value']=round(r['price']-intrinsic,6) if intrinsic is not None else None
            r['breakeven']=round(r['strike']+r['price'],6) if r['option_type']=='CALL' else round(r['strike']-r['price'],6) if r['option_type']=='PUT' else None
        else:r['intrinsic_value']=r['time_value']=r['breakeven']=None
        r['babimind_score']=calc_score(r)
        r['decision']='BUY' if r['babimind_score']>=80 else 'HOLD' if r['babimind_score']>=60 else 'AVOID'
        r.pop('expiry_dt')
        records.append(r)
    # Deduplicate exact contract symbol; retain the richest/highest score observation.
    best={}
    for r in records:
        k=str(r.get('symbol') or '')
        if k and (k not in best or r['babimind_score']>best[k]['babimind_score']):best[k]=r
    records=sorted(best.values(),key=lambda r:(-r['babimind_score'],r['underlying'],str(r['symbol'])))
    for i,r in enumerate(records,1):r['rank']=i
    generated=datetime.now(timezone.utc).isoformat()
    payload={'generated_at_utc':generated,'source':str(SRC),'record_count':len(records),'records':records[:1000]}
    OUT_JSON.parent.mkdir(parents=True,exist_ok=True);OUT_JSON.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# BabiMind Option Ranking','',f'Generated: {generated}',f'Contracts ranked: {len(records)}','', '| Rank | Underlying | Contract | Type | Score | Decision | Strike | Price | IV | Delta | Days | BE |','|---:|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|']
    for r in records[:300]:
        lines.append(f"| {r['rank']} | {r['underlying']} | {r.get('symbol') or '-'} | {r.get('option_type') or '-'} | {r['babimind_score']:.1f} | {r['decision']} | {r.get('strike') if r.get('strike') is not None else '-'} | {r.get('price') if r.get('price') is not None else '-'} | {r.get('iv') if r.get('iv') is not None else '-'} | {r.get('delta') if r.get('delta') is not None else '-'} | {r.get('days_to_expiry') if r.get('days_to_expiry') is not None else '-'} | {r.get('breakeven') if r.get('breakeven') is not None else '-'} |")
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'ranked {len(records)} contracts')

if __name__=='__main__':main()
