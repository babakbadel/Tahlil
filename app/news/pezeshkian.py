"""Pezeshkian-focused news evidence for Decision layer.

Stores a rolling, deduplicated evidence log. Does not treat announcements as
implemented policy.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

QUERIES = [
    "پزشکیان دولت اقتصاد",
    "پزشکیان تیم اقتصادی",
    "پزشکیان دلار ارز بودجه تورم",
    "پزشکیان بورس بانک مرکزی نرخ بهره",
    "پزشکیان تحریم مذاکره تجارت نفت",
    "Pezeshkian Iran economy",
]


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; BabiMind/1.2 pez-news)"}
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def _text(node: ET.Element, names: list[str]) -> str:
    for name in names:
        x = node.find(name)
        if x is not None and (x.text or "").strip():
            return x.text.strip()
    return ""


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


class PezeshkianNewsCollector:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[2]
        self.out = self.root / "artifacts" / "babimind_pezeshkian_news.json"

    def collect(self, hours: int = 36) -> list[dict[str, Any]]:
        _ = hours  # window kept for API compatibility; RSS is rolling
        rows: list[dict[str, Any]] = []
        for q in QUERIES:
            is_en = q.isascii()
            params = urllib.parse.urlencode(
                {
                    "q": q,
                    "hl": "en" if is_en else "fa",
                    "gl": "US" if is_en else "IR",
                    "ceid": "US:en" if is_en else "IR:fa",
                }
            )
            url = "https://news.google.com/rss/search?" + params
            try:
                root = ET.fromstring(_fetch(url))
            except Exception as exc:
                rows.append({"status": "SKIP", "query": q, "error": str(exc)})
                continue
            for item in root.findall(".//item"):
                title = _clean(_text(item, ["title"]))
                link = _clean(_text(item, ["link"]))
                source = _clean(_text(item, ["source"])) or "unknown"
                published = _clean(_text(item, ["pubDate"]))
                if not title or not link:
                    continue
                key = hashlib.sha256(f"{title}|{link}".encode("utf-8")).hexdigest()
                rows.append(
                    {
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
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
        return rows

    def persist(self, hours: int = 36) -> dict[str, Any]:
        previous: list = []
        if self.out.exists():
            try:
                previous = json.loads(self.out.read_text(encoding="utf-8"))
                if not isinstance(previous, list):
                    previous = []
            except Exception:
                previous = []

        fresh = self.collect(hours=hours)
        seen = {x.get("id") for x in previous if isinstance(x, dict)}
        merged = previous[:]
        for row in fresh:
            if row.get("status") == "SKIP":
                continue
            if row.get("id") not in seen:
                merged.append(row)
                seen.add(row.get("id"))
        merged = merged[-2000:]
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        new_items = sum(
            1
            for x in fresh
            if x.get("id") and x.get("id") not in {y.get("id") for y in previous if isinstance(y, dict)}
        )
        return {
            "status": "ok",
            "new_items": new_items,
            "total": len(merged),
            "output": str(self.out),
        }


def collect_pezeshkian_and_persist(root: Path | None = None, hours: int = 36) -> dict[str, Any]:
    return PezeshkianNewsCollector(root=root).persist(hours=hours)
