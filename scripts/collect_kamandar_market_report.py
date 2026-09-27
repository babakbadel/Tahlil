#!/usr/bin/env python3
"""Collect Kamandar daily Tehran Stock Exchange market reports.

Kamandar's public report exposes daily market-level aggregates such as:
index level/change, market breadth, buy/sell queues, retail trading value
and real-person money flow. The collector keeps the source as evidence and
does not treat it as ground truth when it conflicts with official TSE/TSETMC.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
URL = "https://kamandar.ir/market-report"
OUT = ROOT / "data" / "raw" / "kamandar_market_report.json"
REPORT = ROOT / "reports" / "kamandar_market_report.json"
USER_AGENT = "BabiMind-KamandarCollector/1.0 (+https://github.com/babakbadel/Tahlil)"


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self._href = ""
        self._in_a = False
        self._link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._in_a = True
            self._link_text = []
            self._href = dict(attrs).get("href") or ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_a:
            text = clean(" ".join(self._link_text))
            if text and self._href:
                self.links.append({"text": text, "href": self._href})
            self._in_a = False
            self._href = ""

    def handle_data(self, data: str) -> None:
        value = clean(data)
        if value:
            self.parts.append(value)
            if self._in_a:
                self._link_text.append(value)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def fetch() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read().decode("utf-8", errors="replace")


def parse(html: str) -> dict[str, Any]:
    parser = TextParser()
    parser.feed(html)
    text = " ".join(parser.parts)
    rows = re.findall(
        r"(\d{1,2} [^ ]+ ۱۴۰۵|\d{1,2} [^ ]+ 1405).*?"
        r"شاخص کل\s*([\d٬,]+).*?([+−-]\s*[\d٫.,]+\s*%)",
        text,
    )
    daily = []
    for date, index, change in rows:
        daily.append(
            {
                "date": clean(date),
                "index": index.replace("٬", "").replace(",", ""),
                "change_pct": change.replace("٫", ".").replace(" ", ""),
            }
        )
    return {
        "source": "kamandar",
        "url": URL,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "title": "گزارش روزانهٔ بازار بورس",
        "description": "شاخص کل، عرض بازار، صف‌های خرید و فروش، ارزش معاملات خرد و جریان پول حقیقی",
        "unit_note": "ارقام پولی صفحه به ریال گزارش می‌شوند.",
        "daily_index_history": daily,
        "report_links": [x for x in parser.links if "/market-report/" in x["href"]],
        "raw_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "parser_version": 1,
    }


def main() -> int:
    try:
        payload = parse(fetch())
        payload["status"] = "ok"
    except Exception as exc:
        payload = {
            "source": "kamandar",
            "url": URL,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "error": repr(exc),
            "parser_version": 1,
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.write_text(
        json.dumps(
            {
                "source": "kamandar",
                "status": payload.get("status"),
                "checked_at": payload.get("collected_at"),
                "url": URL,
                "records": len(payload.get("daily_index_history", [])),
                "report_links": len(payload.get("report_links", [])),
                "parser_version": payload.get("parser_version"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"status": payload.get("status"), "records": len(payload.get("daily_index_history", []))}, ensure_ascii=False))
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
