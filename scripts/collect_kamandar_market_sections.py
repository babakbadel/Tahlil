#!/usr/bin/env python3
"""Collect daily Kamandar market section snapshots for BabiMind.

The pages are stored as raw evidence plus a compact parsed metadata summary.
This intentionally keeps the source text even when Kamandar changes its HTML.
"""
from __future__ import annotations
import hashlib, json, re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "BabiMind-KamandarMarketCollector/1.0 (+https://github.com/babakbadel/Tahlil)"
PAGES = {
    "indices": "https://kamandar.ir/app/market/indices",
    "stocks": "https://kamandar.ir/app/market/stocks",
    "funds": "https://kamandar.ir/app/market/funds",
    "options": "https://kamandar.ir/app/market/options",
    "baskets": "https://kamandar.ir/app/market/baskets",
    "options_top_put": "https://kamandar.ir/app/market/list/options-top-put",
}

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]; self.links=[]; self._a=False; self._href=""; self._txt=[]
    def handle_starttag(self, tag, attrs):
        if tag=="a":
            self._a=True; self._href=dict(attrs).get("href") or ""; self._txt=[]
    def handle_endtag(self, tag):
        if tag=="a" and self._a:
            t=clean(" ".join(self._txt))
            if t and self._href: self.links.append({"text":t,"href":self._href})
            self._a=False; self._href=""; self._txt=[]
    def handle_data(self, data):
        t=clean(data)
        if t:
            self.parts.append(t)
            if self._a: self._txt.append(t)

def clean(v): return re.sub(r"\s+"," ",v or "").strip()

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read().decode("utf-8",errors="replace"), getattr(r,"status",200), r.headers.get("Content-Type","")

def collect(name,url):
    now=datetime.now(timezone.utc).isoformat()
    out=ROOT/"data"/"raw"/f"kamandar_{name}.json"
    report=ROOT/"reports"/f"kamandar_{name}.json"
    try:
        html,status,ctype=fetch(url)
        p=Parser(); p.feed(html)
        text=" ".join(p.parts)
        payload={
            "source":"kamandar","section":name,"url":url,"collected_at":now,"status":"ok",
            "http_status":status,"content_type":ctype,"text_length":len(text),
            "links_count":len(p.links),"links":p.links,
            "raw_text_sha256":hashlib.sha256(text.encode()).hexdigest(),
            "raw_text":text[:150000],
        }
    except Exception as exc:
        payload={"source":"kamandar","section":name,"url":url,"collected_at":now,"status":"error","error":repr(exc)}
    out.parent.mkdir(parents=True,exist_ok=True); report.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    report.write_text(json.dumps({k:payload.get(k) for k in ["source","section","url","collected_at","status","http_status","text_length","links_count","raw_text_sha256"]},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"section":name,"status":payload.get("status"),"links":payload.get("links_count",0)},ensure_ascii=False))
    return payload.get("status")=="ok"

def main():
    ok=[collect(n,u) for n,u in PAGES.items()]
    return 0 if all(ok) else 1

if __name__=="__main__": raise SystemExit(main())
