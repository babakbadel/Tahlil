"""Daily economic news collector (Event Time layer).

Dependency-free RSS collector for Iran economy, bourse, FX, oil, policy and
Pezeshkian. Outputs JSON evidence log + markdown digest.
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

# (query, relevance, channels, hl, gl, ceid)
DEFAULT_QUERIES: list[tuple[str, str, list[str], str, str, str]] = [
    ("بورس تهران شاخص کل", "bourse", ["equity", "flow"], "fa", "IR", "IR:fa"),
    ("بورس ورود پول حقیقی", "bourse_flow", ["equity", "flow"], "fa", "IR", "IR:fa"),
    ("دلار آزاد بازار ارز", "fx", ["fx", "inflation_expectations"], "fa", "IR", "IR:fa"),
    ("نرخ تورم نقدینگی بانک مرکزی", "macro_monetary", ["monetary", "inflation"], "fa", "IR", "IR:fa"),
    ("نفت برنت صادرات نفت ایران", "oil", ["oil", "fx_monetization"], "fa", "IR", "IR:fa"),
    ("پزشکیان اقتصاد ارز بودجه", "pezeshkian", ["policy", "fx", "fiscal"], "fa", "IR", "IR:fa"),
    ("اختیار معامله بورس فملی", "options", ["options"], "fa", "IR", "IR:fa"),
    ("تحریم هرمز کشتیرانی ایران", "geopolitics", ["geopolitical_risk", "oil"], "fa", "IR", "IR:fa"),
    ("طلا سکه صندوق طلا", "gold", ["gold", "fx"], "fa", "IR", "IR:fa"),
    ("مدنی‌زاده همتی بانک مرکزی", "policy_actors", ["policy", "monetary"], "fa", "IR", "IR:fa"),
    ("Iran stock market Tehran exchange", "bourse", ["equity"], "en", "US", "US:en"),
    ("Iran rial free market dollar", "fx", ["fx"], "en", "US", "US:en"),
    ("Pezeshkian Iran economy oil", "pezeshkian", ["policy", "oil"], "en", "US", "US:en"),
    ("Iran Hormuz oil blockade exports", "geopolitics", ["oil", "geopolitical_risk"], "en", "US", "US:en"),
    ("Brent crude oil price", "oil", ["oil"], "en", "US", "US:en"),
    ("Iran inflation gasoline subsidy", "macro_monetary", ["inflation", "fiscal"], "en", "US", "US:en"),
]

MAX_ITEMS = 2500


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; BabiMind/1.2 news)"}
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


class DailyEconomicNewsCollector:
    """Collect and persist daily economic news evidence."""

    def __init__(self, root: Path | None = None, queries: list | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[2]
        self.queries = queries or DEFAULT_QUERIES
        self.out_json = self.root / "artifacts" / "babimind_daily_economic_news.json"
        self.out_md = self.root / "memory" / "news-daily-latest.md"

    def collect(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for q, relevance, channels, hl, gl, ceid in self.queries:
            params = urllib.parse.urlencode({"q": q, "hl": hl, "gl": gl, "ceid": ceid})
            url = "https://news.google.com/rss/search?" + params
            try:
                root = ET.fromstring(_fetch(url))
            except Exception as exc:
                rows.append(
                    {
                        "status": "SKIP",
                        "query": q,
                        "relevance": relevance,
                        "error": str(exc),
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
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
                        "query": q,
                        "relevance": relevance,
                        "confidence": "source_pending",
                        "market_channels": channels,
                        "decision_signal": "pending_extraction",
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
        return rows

    def merge(self, previous: list, fresh: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = {x.get("id") for x in previous if isinstance(x, dict) and x.get("id")}
        merged = [x for x in previous if isinstance(x, dict)]
        for row in fresh:
            if row.get("status") == "SKIP":
                continue
            rid = row.get("id")
            if rid and rid not in seen:
                merged.append(row)
                seen.add(rid)
        return merged[-MAX_ITEMS:]

    def write_digest(self, items: list[dict[str, Any]], new_count: int) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        news = [x for x in items if x.get("title") and x.get("id")]
        news = sorted(
            news,
            key=lambda x: x.get("collected_at") or x.get("published_at") or "",
            reverse=True,
        )[:40]
        lines = [
            f"# Daily Economic News Digest — {now}",
            "",
            "> Evidence only. Not ground truth prices or implemented policy.",
            f"> New items this run: **{new_count}** · Total stored: **{len(items)}**",
            "",
            "| Relevance | Title | Source | Published |",
            "|-----------|-------|--------|-----------|",
        ]
        for x in news:
            title = (x.get("title") or "").replace("|", "/")[:120]
            lines.append(
                f"| {x.get('relevance', '')} | {title} | {x.get('source', '')} | "
                f"{str(x.get('published_at', ''))[:22]} |"
            )
        lines += [
            "",
            "## Policy",
            "- Map events to factors with confidence/freshness before scoring.",
            "- Cross-check Tier-A sources for market-moving claims.",
            "- Options: never rank expired contracts from headlines.",
            "",
            f"NEWS_DIGEST | {now} | {new_count} new | {len(items)} total",
            "",
        ]
        self.out_md.parent.mkdir(parents=True, exist_ok=True)
        self.out_md.write_text("\n".join(lines), encoding="utf-8")

    def persist(self) -> dict[str, Any]:
        previous: list = []
        if self.out_json.exists():
            try:
                previous = json.loads(self.out_json.read_text(encoding="utf-8"))
                if not isinstance(previous, list):
                    previous = []
            except Exception:
                previous = []

        fresh = self.collect()
        prev_ids = {x.get("id") for x in previous if isinstance(x, dict)}
        new_count = sum(1 for x in fresh if x.get("id") and x.get("id") not in prev_ids)
        merged = self.merge(previous, fresh)

        self.out_json.parent.mkdir(parents=True, exist_ok=True)
        self.out_json.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        self.write_digest(merged, new_count)

        skips = sum(1 for x in fresh if x.get("status") == "SKIP")
        return {
            "status": "ok",
            "new_items": new_count,
            "fetched_rows": len(fresh),
            "skips": skips,
            "total": len(merged),
            "output_json": str(self.out_json),
            "output_md": str(self.out_md),
        }


def collect_and_persist(root: Path | None = None) -> dict[str, Any]:
    return DailyEconomicNewsCollector(root=root).persist()
