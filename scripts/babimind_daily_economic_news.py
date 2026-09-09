#!/usr/bin/env python3
"""Daily economic news collector for BabiMind Event/Decision layers.

Collects public RSS evidence for Iran economy, bourse, FX, oil, policy and
Pezeshkian. Dependency-free. News is evidence, not ground truth.
Does not invent prices, flows or implemented policy from headlines.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

# (query, relevance, channels, hl, gl, ceid)
QUERIES: list[tuple[str, str, list[str], str, str, str]] = [
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
    # English fallbacks (more reliable from non-IR runners)
    ("Iran stock market Tehran exchange", "bourse", ["equity"], "en", "US", "US:en"),
    ("Iran rial free market dollar", "fx", ["fx"], "en", "US", "US:en"),
    ("Pezeshkian Iran economy oil", "pezeshkian", ["policy", "oil"], "en", "US", "US:en"),
    ("Iran Hormuz oil blockade exports", "geopolitics", ["oil", "geopolitical_risk"], "en", "US", "US:en"),
    ("Brent crude oil price", "oil", ["oil"], "en", "US", "US:en"),
    ("Iran inflation gasoline subsidy", "macro_monetary", ["inflation", "fiscal"], "en", "US", "US:en"),
]

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "artifacts" / "babimind_daily_economic_news.json"
OUT_MD = ROOT / "memory" / "news-daily-latest.md"
MAX_ITEMS = 2500


def fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; BabiMind/1.2 daily-econ-news)"}
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def text(node, names: list[str]) -> str:
    for name in names:
        x = node.find(name)
        if x is not None and (x.text or "").strip():
            return x.text.strip()
    return ""


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def collect() -> list[dict]:
    rows: list[dict] = []
    for q, relevance, channels, hl, gl, ceid in QUERIES:
        params = urllib.parse.urlencode({"q": q, "hl": hl, "gl": gl, "ceid": ceid})
        url = "https://news.google.com/rss/search?" + params
        try:
            root = ET.fromstring(fetch(url))
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
            title = clean(text(item, ["title"]))
            link = clean(text(item, ["link"]))
            source = clean(text(item, ["source"])) or "unknown"
            published = clean(text(item, ["pubDate"]))
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


def merge(previous: list, fresh: list[dict]) -> list[dict]:
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


def write_digest(items: list[dict], new_count: int) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    news = [x for x in items if x.get("title") and x.get("id")]
    news = sorted(
        news, key=lambda x: x.get("collected_at") or x.get("published_at") or "", reverse=True
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
            f"| {x.get('relevance','')} | {title} | {x.get('source','')} | {x.get('published_at','')[:22]} |"
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
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=36, help="kept for CLI compatibility")
    args = ap.parse_args()
    _ = args.hours

    previous: list = []
    if OUT_JSON.exists():
        try:
            previous = json.loads(OUT_JSON.read_text(encoding="utf-8"))
            if not isinstance(previous, list):
                previous = []
        except Exception:
            previous = []

    fresh = collect()
    prev_ids = {x.get("id") for x in previous if isinstance(x, dict)}
    new_count = sum(1 for x in fresh if x.get("id") and x.get("id") not in prev_ids)
    merged = merge(previous, fresh)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    write_digest(merged, new_count)

    skips = sum(1 for x in fresh if x.get("status") == "SKIP")
    print(
        json.dumps(
            {
                "status": "ok",
                "new_items": new_count,
                "fetched_rows": len(fresh),
                "skips": skips,
                "total": len(merged),
                "output_json": str(OUT_JSON),
                "output_md": str(OUT_MD),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
