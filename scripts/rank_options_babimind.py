#!/usr/bin/env python3
"""Create a compact, deterministic BabiMind ranking from the realtime option snapshot.

The parser is intentionally schema-tolerant because the upstream option API can change
field names. Missing Greeks/IV are left null and are never fabricated.
"""
from __future__ import annotations

import json, math, os, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/latest/options_realtime.json"
OUT_JSON = ROOT / "reports/options_babimind_ranked.json"
OUT_MD = ROOT / "reports/options_babimind_ranked.md"
TARGETS = {"فملی": "فملی", "فملی": "فملی", "وبملت": "وبملت", "شپنا": "شپنا", "خساپا": "خساپا", "FEMLI": "فملی", "وبملت": "وبملت", "SHAPNA": "شپنا", "KHODRO": "خساپا"}

ALIASES = {
    "underlying": ["underlying", "underlying_symbol", "base_symbol", "stock", "stock_symbol", "asset", "نماد_پایه", "نمادپایه", "سهم_پایه"],
    "symbol": ["symbol", "option_symbol", "contract", "ticker", "نماد", "نماد_اختیار", "نام_نماد"],
    "strike": ["strike", "strike_price", "exercise_price", "قیمت_اعمال", "قیمتاعمال", "استرایک"],
    "price": ["price", "last", "last_price", "close", "close_price", "option_price", "قیمت", "آخرین", "آخرین_قیمت"],
    "bid": ["bid", "best_bid", "buy_price", "قیمت_خرید"],
    "ask": ["ask", "best_ask", "sell_price", "قیمت_فروش"],
    "iv": ["iv", "implied_volatility", "implied_vol", "نوسان_ضمنی", "نوسانضمنی"],
    "delta": ["delta", "دلتا"], "gamma": ["gamma", "گاما"], "theta": ["theta", "تتا"], "vega": ["vega", "وگا"],
    "expiry": ["expiry", "expiration", "expiry_date", "maturity", "سررسید", "تاریخ_سررسید"],
    "volume": ["volume", "trade_volume", "حجم"], "open_interest": ["open_interest", "oi", "موقعیت_باز"],
    "underlying_price": ["underlying_price", "spot", "last_underlying", "قیمت_پایه", "قیمت_سهم"],
}

def norm(s):
    return str(s).strip().replace("ي", "ی").replace("ك", "ک").replace("‌", "").upper()

def num(v):
    if v is None or v == "": return None
    if isinstance(v, (int,float)): return float(v)
    s = str(v).replace(",", "").replace("٪", "%").strip()
    try: return float(s[:-1]) / 100 if s.endswith("%") else float(s)
    except Exception: return None

def get(d, aliases):
    if not isinstance(d, dict): return None
    nd = {norm(k): v for k,v in d.items()}
    for a in aliases:
        if norm(a) in nd: return nd[norm(a)]
    return None

def flatten(x):
    if isinstance(x, list):
        for v in x: yield from flatten(v)
    elif isinstance(x, dict):
        # A dict with at least a few option-like fields is a candidate record.
        keys = {norm(k) for k in x}
        if any(norm(a) in keys for a in ALIASES["symbol"]) or any(norm(a) in keys for a in ALIASES["strike"]):
            yield x
        for v in x.values():
            if isinstance(v, (dict,list)): yield from flatten(v)

def target_from(rec):
    u = get(rec, ALIASES["underlying"])
    if u:
        s = norm(u)
        for k,v in TARGETS.items():
            if norm(k) in s: return v
    s = norm(get(rec, ALIASES["symbol"]) or "")
    # Also recognize the Persian/Latin underlying name embedded in option symbols.
    for k,v in TARGETS.items():
        if norm(k) in s: return v
    return None

def option_type(rec):
    s = norm(get(rec, ALIASES["symbol"]) or "")
    t = norm(get(rec, ["type", "option_type", "side", "نوع"]) or "")
    if any(z in t for z in ["CALL", "C", "خرید"]): return "CALL"
    if any(z in t for z in ["PUT", "P", "فروش"]): return "PUT"
    if "CALL" in s or "کال" in s: return "CALL"
    if "PUT" in s or "پوت" in s: return "PUT"
    return None

def parse_date(v):
    if not v: return None
    s=str(v).strip().replace("/","-")
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try: return datetime.strptime(s[:26],fmt).replace(tzinfo=timezone.utc)
        except Exception: pass
    return None

def clamp(x,a=0,b=100): return max(a,min(b,x))

def score(r):
    # Transparent score: data quality 20, liquidity 20, pricing 25, Greeks/IV 20, maturity 15.
    fields=[r.get(k) for k in ("price","strike","expiry","underlying_price")]
    quality=20*sum(v is not None for v in fields)/4
    vol=math.log1p(r.get("volume") or 0); oi=math.log1p(r.get("open_interest") or 0)
    liquidity=clamp(10 + 3.5*vol + 3.5*oi,0,20) if (vol or oi) else 0
    spot, strike, px = r.get("underlying_price"), r.get("strike"), r.get("price")
    pricing=12.5
    if spot and strike:
        m=abs(spot-strike)/max(abs(spot),1)
        pricing += clamp((0.20-m)*25, -12.5, 12.5)
    if px is not None and px>0: pricing += 4
    pricing=clamp(pricing,0,25)
    greek=10
    iv=r.get("iv")
    if iv is not None:
        ivpct=iv*100 if iv<3 else iv
        greek += clamp(10-abs(ivpct-45)/8, -5, 10)
    for g in ("delta","gamma","theta","vega"):
        if r.get(g) is not None: greek += 1.25
    greek=clamp(greek,0,20)
    days=None
    if r.get("expiry_dt"):
        days=max(0,(r["expiry_dt"]-datetime.now(timezone.utc)).total_seconds()/86400)
    maturity=clamp(15 if days is None else (15 if 20<=days<=90 else 10 if days>90 else 6),0,15)
    return round(clamp(quality+liquidity+pricing+greek+maturity),2)

def main():
    if not SRC.exists(): raise SystemExit(f"missing {SRC}")
    raw=json.loads(SRC.read_text(encoding="utf-8"))
    records=[]
    for rec in flatten(raw):
        target=target_from(rec)
        if not target: continue
        r={"underlying":target,"symbol":get(rec,ALIASES["symbol"]),"strike":num(get(rec,ALIASES["strike"])),"price":num(get(rec,ALIASES["price"])),"bid":num(get(rec,ALIASES["bid"])),"ask":num(get(rec,ALIASES["ask"])),"iv":num(get(rec,ALIASES["iv"])),"delta":num(get(rec,ALIASES["delta"])),"gamma":num(get(rec,ALIASES["gamma"])),"theta":num(get(rec,ALIASES["theta"])),"vega":num(get(rec,ALIASES["vega"])),"expiry":get(rec,ALIASES["expiry"]),"volume":num(get(rec,ALIASES["volume"])),"open_interest":num(get(rec,ALIASES["open_interest"])),"underlying_price":num(get(rec,ALIASES["underlying_price"])),"option_type":option_type(rec)}
        r["expiry_dt"]=parse_date(r["expiry"])
        r["days_to_expiry"]=round((r["expiry_dt"]-datetime.now(timezone.utc)).total_seconds()/86400,2) if r["expiry_dt"] else None
        if r["price"] is not None and r["strike"] is not None and r["underlying_price"] is not None:
            intrinsic=max(0,r["underlying_price"]-r["strike"]) if r["option_type"]=="CALL" else max(0,r["strike"]-r["underlying_price"]) if r["option_type"]=="PUT" else None
            r["intrinsic_value"]=intrinsic
            r["time_value"]=round(r["price"]-intrinsic,6) if intrinsic is not None else None
            r["breakeven"]=round(r["strike"]+r["price"],6) if r["option_type"]=="CALL" else round(r["strike"]-r["price"],6) if r["option_type"]=="PUT" else None
        else: r["intrinsic_value"]=r["time_value"]=r["breakeven"]=None
        r.pop("expiry_dt",None)
        r["babimind_score"]=score({**r,"expiry_dt":parse_date(r["expiry"])})
        r["decision"]="BUY" if r["babimind_score"]>=80 else "HOLD" if r["babimind_score"]>=60 else "AVOID"
        records.append(r)
    # Deduplicate by symbol, keeping highest score.
    best={str(r.get("symbol")):r for r in records if r.get("symbol")}
    records=sorted(best.values(), key=lambda x:x["babimind_score"], reverse=True)
    for i,r in enumerate(records,1): r["rank"]=i
    payload={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"source":str(SRC),"targets":list(TARGETS.values()),"record_count":len(records),"records":records[:1000]}
    OUT_JSON.parent.mkdir(parents=True,exist_ok=True); OUT_JSON.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# BabiMind Option Ranking","",f"Generated: {payload['generated_at_utc']}",f"Contracts ranked: {len(records)}","","| Rank | Underlying | Contract | Type | Score | Decision | Strike | Price | IV | Delta | Days | BE |","|---:|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for r in records[:200]:
        lines.append(f"| {r['rank']} | {r['underlying']} | {r['symbol']} | {r.get('option_type') or '-'} | {r['babimind_score']:.1f} | {r['decision']} | {r.get('strike') or '-'} | {r.get('price') or '-'} | {r.get('iv') if r.get('iv') is not None else '-'} | {r.get('delta') if r.get('delta') is not None else '-'} | {r.get('days_to_expiry') if r.get('days_to_expiry') is not None else '-'} | {r.get('breakeven') or '-'} |")
    OUT_MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"ranked {len(records)} contracts -> {OUT_JSON} and {OUT_MD}")

if __name__ == "__main__": main()
