#!/usr/bin/env python3
"""Collect Kamandar market overview plus every linked daily report page."""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
URL="https://kamandar.ir/market-report"
OUT=ROOT/"data/raw/kamandar_market_report.json"
REPORT=ROOT/"reports/kamandar_market_report.json"
USER_AGENT="BabiMind-KamandarCollector/2.0 (+https://github.com/babakbadel/Tahlil)"
MAX_REPORTS=60


class TextParser(HTMLParser):
    def __init__(self)->None:
        super().__init__(); self.parts=[]; self.links=[]; self._href=""; self._in_a=False; self._link_text=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            self._in_a=True; self._link_text=[]; self._href=dict(attrs).get("href") or ""
    def handle_endtag(self,tag):
        if tag=="a" and self._in_a:
            text=clean(" ".join(self._link_text))
            if text and self._href:self.links.append({"text":text,"href":self._href})
            self._in_a=False; self._href=""
    def handle_data(self,data):
        value=clean(data)
        if value:
            self.parts.append(value)
            if self._in_a:self._link_text.append(value)


def clean(value:str)->str:
    return re.sub(r"\s+"," ",value or "").strip()


def fetch(url:str)->str:
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT})
    with urllib.request.urlopen(req,timeout=25) as response:
        return response.read().decode("utf-8",errors="replace")


def parse_page(html:str)->tuple[str,list[dict[str,str]]]:
    p=TextParser(); p.feed(html)
    return " ".join(p.parts),p.links


def normalize_url(href:str)->str:
    return urllib.parse.urljoin(URL,href)


def extract_metrics(text:str)->dict[str,Any]:
    patterns={
        "index":r"شاخص کل\s*([\d٬,\.]+)",
        "change_pct":r"(?:شاخص کل.*?)([+−-]\s*[\d٫.,]+\s*%)",
        "equal_weight":r"(?:هم.?وزن|شاخص هم.?وزن)\s*([\d٬,\.]+)",
        "positive":r"(?:نمادهای مثبت|مثبت)\s*[:：]?\s*([\d٬,]+)",
        "negative":r"(?:نمادهای منفی|منفی)\s*[:：]?\s*([\d٬,]+)",
        "buy_queue":r"(?:صف خرید)\s*[:：]?\s*([\d٬,]+)",
        "sell_queue":r"(?:صف فروش)\s*[:：]?\s*([\d٬,]+)",
        "retail_flow":r"(?:پول حقیقی|حقیقی)\s*[:：]?\s*([+−-]?\s*[\d٬,\.]+)",
    }
    out={}
    for key,pat in patterns.items():
        m=re.search(pat,text,re.I)
        if m: out[key]=m.group(1).replace("٬","").replace(",","").replace("٫",".").replace(" ","")
    return out


def parse_overview(html:str)->dict[str,Any]:
    text,links=parse_page(html)
    rows=re.findall(r"(\d{1,2} [^ ]+ ۱۴۰۵|\d{1,2} [^ ]+ 1405).*?شاخص کل\s*([\d٬,]+).*?([+−-]\s*[\d٫.,]+\s*%)",text)
    daily=[{"date":clean(d),"index":i.replace("٬","").replace(",",""),"change_pct":c.replace("٫",".").replace(" ","")} for d,i,c in rows]
    report_links=[]
    seen=set()
    for x in links:
        u=normalize_url(x["href"])
        if "/market-report/" in urllib.parse.urlparse(u).path and u not in seen:
            seen.add(u); report_links.append({"text":x["text"],"href":x["href"],"url":u})
    return {
        "source":"kamandar","url":URL,"collected_at":datetime.now(timezone.utc).isoformat(),
        "title":"گزارش روزانهٔ بازار بورس",
        "description":"شاخص کل، عرض بازار، صف‌های خرید و فروش، ارزش معاملات خرد و جریان پول حقیقی",
        "unit_note":"ارقام پولی صفحه به ریال گزارش می‌شوند.",
        "daily_index_history":daily,
        "report_links":report_links[:MAX_REPORTS],
        "raw_text":text,
        "raw_text_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "parser_version":2,
    }


def collect_reports(links:list[dict[str,str]])->list[dict[str,Any]]:
    reports=[]
    for item in links:
        url=item["url"]
        try:
            html=fetch(url)
            text,links2=parse_page(html)
            reports.append({
                "url":url,"link_text":item.get("text",""),"status":"ok",
                "collected_at":datetime.now(timezone.utc).isoformat(),
                "title":next((x["text"] for x in links2 if x["text"]),item.get("text","")),
                "metrics":extract_metrics(text),
                "text":text,
                "text_sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
            })
        except Exception as exc:
            reports.append({"url":url,"link_text":item.get("text",""),"status":"error","error":repr(exc)})
    return reports


def main()->int:
    try:
        overview=parse_overview(fetch(URL))
        overview["daily_reports"]=collect_reports(overview["report_links"])
        overview["status"]="ok"
    except Exception as exc:
        overview={"source":"kamandar","url":URL,"collected_at":datetime.now(timezone.utc).isoformat(),"status":"error","error":repr(exc),"parser_version":2}
    OUT.parent.mkdir(parents=True,exist_ok=True); REPORT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(overview,ensure_ascii=False,indent=2),encoding="utf-8")
    REPORT.write_text(json.dumps({
        "source":"kamandar","status":overview.get("status"),"checked_at":overview.get("collected_at"),
        "overview_url":URL,"history_records":len(overview.get("daily_index_history",[])),
        "report_links":len(overview.get("report_links",[])),
        "daily_reports":len(overview.get("daily_reports",[])),
        "successful_reports":sum(1 for x in overview.get("daily_reports",[]) if x.get("status")=="ok"),
        "parser_version":overview.get("parser_version")
    },ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":overview.get("status"),"daily_reports":len(overview.get("daily_reports",[]))},ensure_ascii=False))
    return 0 if overview.get("status")=="ok" else 1


if __name__=="__main__":
    raise SystemExit(main())
