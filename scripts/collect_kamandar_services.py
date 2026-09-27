#!/usr/bin/env python3
"""Daily same-domain crawl of Kamandar market services and linked pages.

Starts at /services/market, follows links found on that page and subsequent
same-domain pages (bounded crawl), and stores each visited page, extracted text,
and outgoing links with timestamps. This is a source archive, not a guarantee
that every dynamically rendered or access-restricted page was captured.
"""
from __future__ import annotations
import json, re, time
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
START = "https://kamandar.ir/services/market"
DOMAIN = "kamandar.ir"
MAX_PAGES = 150
DELAY_SECONDS = 0.4
OUT = ROOT / "data/raw/kamandar_services_crawl.json"
REPORT = ROOT / "reports/kamandar_services_crawl.json"

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.text = [], []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            s = re.sub(r"\\s+", " ", data).strip()
            if s: self.text.append(s)

def canonical(url):
    url, _ = urldefrag(url)
    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.hostname not in (DOMAIN, "www."+DOMAIN):
        return None
    return p._replace(fragment="").geturl()

def main():
    queue = deque([START])
    seen, pages, errors = set(), [], []
    while queue and len(seen) < MAX_PAGES:
        url = canonical(queue.popleft())
        if not url or url in seen: continue
        seen.add(url)
        try:
            req = Request(url, headers={"User-Agent":"BabiMind-KamandarCrawler/1.0"})
            with urlopen(req, timeout=25) as response:
                body = response.read(5_000_000)
                final_url = canonical(response.geturl()) or url
                ctype = response.headers.get("Content-Type", "")
            if "html" not in ctype.lower():
                pages.append({"url":url,"final_url":final_url,"content_type":ctype,"status":"non_html"})
                continue
            html = body.decode("utf-8", errors="replace")
            parser = Parser(); parser.feed(html)
            links = []
            for href in parser.links:
                target = canonical(urljoin(final_url, href))
                if target and target not in seen and target not in queue:
                    links.append(target)
                    queue.append(target)
            pages.append({"url":url,"final_url":final_url,"status":"ok","title_text":parser.text[:30000],"links":sorted(set(links))})
        except Exception as exc:
            errors.append({"url":url,"error":repr(exc)})
            pages.append({"url":url,"status":"error","error":repr(exc)})
        time.sleep(DELAY_SECONDS)
    payload = {"source":"kamandar","start_url":START,"collected_at":datetime.now(timezone.utc).isoformat(),"pages_visited":len(seen),"pages":pages,"errors":errors,"crawl_limit":MAX_PAGES,"queue_remaining":len(queue)}
    OUT.parent.mkdir(parents=True,exist_ok=True); REPORT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    REPORT.write_text(json.dumps({"source":"kamandar","checked_at":payload["collected_at"],"pages_visited":len(seen),"pages_ok":sum(p.get("status")=="ok" for p in pages),"errors":len(errors),"queue_remaining":len(queue),"start_url":START},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"pages_visited":len(seen),"errors":len(errors),"queue_remaining":len(queue)}))
    return 0
if __name__ == "__main__": raise SystemExit(main())
