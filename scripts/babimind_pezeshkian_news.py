#!/usr/bin/env python3
"""Collect fresh public news for the BabiMind Pezeshkian decision layer.

The collector is intentionally dependency-free and non-blocking. It stores a
rolling, deduplicated evidence log; it does not infer that an announcement is
an implemented policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

QUERIES = [
    "پزشکیان دولت اقتصاد",
    "پزشکیان تیم اقتصادی",
    "پزشکیان دلار ارز بودجه تورم",
    "پزشکیان بورس بانک مرکزی نرخ بهره",
    "پزشکیان تحریم مذاکره تجارت نفت",
]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "BabiMind/1.0 news-monitor"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def text(node, names):
    for name in names:
        x = node.find(name)
        if x is not None and x.text:
            return x.text.strip()
    return ""


def clean(s: str) -> str:
    return re.sub(r"\\s+", " ", s).strip()


def collect(hours: int):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = []
    for q in QUERIES:
        params = urllib.parse.urlencode({"q": q, "hl": "fa", "gl": "IR", "ceid": "IR:fa"})
        url = "https://news.google.com/rss/search?" + params
        try:
            root = ET.fromstring(fetch(url))
        except Exception as exc:
            rows.append({"status": "SKIP", "query": q, "error": str(exc)})
            continue
        for item in root.findall(".//item"):
            title = clean(text(item, ["title"]))
            link = clean(text(item, ["link"]))
            source = clean(text(item, ["source"])) or "unknown"
            published = clean(text(item, ["pubDate"]))
            # Keep feed items even when date parsing is unavailable; provenance
            # is more useful than silently dropping evidence.
            if not title or not link:
                continue
            key = hashlib.sha256((title + "|" + link).encode("utf-8")).hexdigest()
            rows.append({
                "id": key,
                "published_at": published,
                "title": title,
                "source": source,
                "url": link,
                "relevance": "pezeshkian",
                "confidence": "source_pending",
                "entities": ["مسعود پزشکیان"],
                "decision_signal": "pending_extraction",
                "market_channels": [],
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=36)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = root / "artifacts" / "babimind_pezeshkian_news.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    previous = []
    if out.exists():
        try:
            previous = json.loads(out.read_text(encoding="utf-8"))
            if not isinstance(previous, list):
                previous = []
        except Exception:
            previous = []

    fresh = collect(args.hours)
    seen = {x.get("id") for x in previous if isinstance(x, dict)}
    merged = previous[:]
    for row in fresh:
        if row.get("id") not in seen:
            merged.append(row)
            seen.add(row.get("id"))

    # Keep a bounded evidence history while preserving the newest material.
    merged = merged[-2000:]
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "new_items": sum(1 for x in fresh if x.get("id") not in {y.get("id") for y in previous if isinstance(y, dict)}), "total": len(merged), "output": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
