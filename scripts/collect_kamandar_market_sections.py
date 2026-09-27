#!/usr/bin/env python3
"""Recursively collect Kamandar market sections for BabiMind.

Starts from the six canonical Kamandar pages, follows same-domain HTML links
to a bounded depth, deduplicates URLs, and stores every fetched page as raw
evidence. The section JSON remains the single input consumed by BabiMind.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "BabiMind-KamandarMarketCollector/2.0 (+https://github.com/babakbadel/Tahlil)"
HOST = "kamandar.ir"
MAX_DEPTH = 2
MAX_PAGES_PER_SECTION = 60
TIMEOUT = 20
MAX_BODY_BYTES = 2_000_000
MAX_TEXT_CHARS_PER_PAGE = 120_000
SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".pdf",
    ".zip", ".rar", ".7z", ".mp4", ".mp3", ".wav", ".avi", ".mov",
    ".css", ".js", ".map", ".woff", ".woff2", ".ttf", ".eot",
}

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
        self.parts = []
        self.links = []
        self._a = False
        self._href = ""
        self._txt = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._a = True
            self._href = dict(attrs).get("href") or ""
            self._txt = []

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._a:
            text = clean(" ".join(self._txt))
            if text and self._href:
                self.links.append({"text": text, "href": self._href})
            self._a = False
            self._href = ""
            self._txt = []

    def handle_data(self, data):
        value = clean(data)
        if value:
            self.parts.append(value)
            if self._a:
                self._txt.append(value)


def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_url(base, href):
    if not href:
        return None
    href = href.strip()
    if href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    url = urllib.parse.urljoin(base, href)
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {HOST, "www." + HOST}:
        return None
    path = parsed.path or "/"
    if any(path.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
        return None
    # Fragments never change server content. Keep query parameters because
    # some Kamandar pages use them to identify a symbol/list.
    return urllib.parse.urlunsplit(("https", HOST, path.rstrip("/") or "/", parsed.query, ""))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        status = getattr(response, "status", 200)
        ctype = response.headers.get("Content-Type", "")
        body = response.read(MAX_BODY_BYTES + 1)
        if len(body) > MAX_BODY_BYTES:
            raise ValueError("response exceeds MAX_BODY_BYTES")
        return body.decode("utf-8", errors="replace"), status, ctype


def parse_page(html, url):
    parser = Parser()
    parser.feed(html)
    text = " ".join(parser.parts)
    links = []
    seen = set()
    for item in parser.links:
        absolute = normalize_url(url, item["href"])
        if absolute and absolute not in seen:
            seen.add(absolute)
            links.append({"text": item["text"], "href": item["href"], "url": absolute})
    return text[:MAX_TEXT_CHARS_PER_PAGE], links


def crawl(root_url):
    queue = deque([(root_url, 0)])
    seen = set()
    pages = []
    errors = []
    discovered = set([root_url])

    while queue and len(pages) + len(errors) < MAX_PAGES_PER_SECTION:
        url, depth = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            html, status, ctype = fetch(url)
            text, links = parse_page(html, url)
            record = {
                "url": url,
                "depth": depth,
                "status": "ok",
                "http_status": status,
                "content_type": ctype,
                "text_length": len(text),
                "links_count": len(links),
                "links": links,
                "raw_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "raw_text": text,
            }
            pages.append(record)
            if depth < MAX_DEPTH:
                for link in links:
                    child = link["url"]
                    if child not in discovered and len(pages) + len(queue) < MAX_PAGES_PER_SECTION:
                        discovered.add(child)
                        queue.append((child, depth + 1))
        except Exception as exc:
            errors.append({"url": url, "depth": depth, "status": "error", "error": repr(exc)})

    return {
        "pages": pages,
        "errors": errors,
        "pages_fetched": len(pages),
        "errors_count": len(errors),
        "max_depth_reached": max((p["depth"] for p in pages), default=0),
        "urls_discovered": len(discovered),
    }


def collect(name, url):
    now = datetime.now(timezone.utc).isoformat()
    out = ROOT / "data" / "raw" / f"kamandar_{name}.json"
    report = ROOT / "reports" / f"kamandar_{name}.json"

    try:
        crawl_result = crawl(url)
        root = next((p for p in crawl_result["pages"] if p["url"] == url), None)
        if root is None:
            raise RuntimeError("root page was not fetched")

        # Keep the root fields compatible with the old collector while adding
        # the complete bounded recursive crawl as evidence.
        payload = {
            "source": "kamandar",
            "section": name,
            "url": url,
            "collected_at": now,
            "status": "ok",
            "crawl": {
                "recursive": True,
                "same_domain_only": True,
                "max_depth": MAX_DEPTH,
                "max_pages": MAX_PAGES_PER_SECTION,
                "timeout_seconds": TIMEOUT,
                **{k: v for k, v in crawl_result.items() if k != "pages"},
            },
            "http_status": root["http_status"],
            "content_type": root["content_type"],
            "text_length": root["text_length"],
            "links_count": root["links_count"],
            "links": root["links"],
            "raw_text_sha256": root["raw_text_sha256"],
            "raw_text": root["raw_text"],
            "pages": crawl_result["pages"],
            "errors": crawl_result["errors"],
        }
    except Exception as exc:
        payload = {
            "source": "kamandar",
            "section": name,
            "url": url,
            "collected_at": now,
            "status": "error",
            "crawl": {
                "recursive": True,
                "same_domain_only": True,
                "max_depth": MAX_DEPTH,
                "max_pages": MAX_PAGES_PER_SECTION,
            },
            "error": repr(exc),
        }

    out.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report.write_text(
        json.dumps({
            "source": "kamandar",
            "section": name,
            "url": url,
            "collected_at": now,
            "status": payload.get("status"),
            "pages_fetched": payload.get("crawl", {}).get("pages_fetched", 0),
            "errors_count": payload.get("crawl", {}).get("errors_count", 0),
            "max_depth_reached": payload.get("crawl", {}).get("max_depth_reached", 0),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({
        "section": name,
        "status": payload.get("status"),
        "pages": payload.get("crawl", {}).get("pages_fetched", 0),
        "errors": payload.get("crawl", {}).get("errors_count", 0),
    }, ensure_ascii=False))
    return payload.get("status") == "ok"


def main():
    results = [collect(name, url) for name, url in PAGES.items()]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
