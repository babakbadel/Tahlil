#!/usr/bin/env python3
"""Collect Kamandar market indices and breadth snapshot for BabiMind."""
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
URL = "https://kamandar.ir/app/market"
OUT = ROOT / "data" / "raw" / "kamandar_indices.json"
REPORT = ROOT / "reports" / "kamandar_indices.json"
UA = "BabiMind-KamandarIndicesCollector/1.0 (+https://github.com/babakbadel/Tahlil)"

DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹٬٫", "0123456789,.")


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self._a = False
        self._href = ""
        self._link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._a = True
            self._href = dict(attrs).get("href") or ""
            self._link_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._a:
            text = clean(" ".join(self._link_text))
            if text and self._href:
                self.links.append({"text": text, "href": self._href})
            self._a = False
            self._href = ""

    def handle_data(self, data: str) -> None:
        value = clean(data)
        if value:
            self.parts.append(value)
            if self._a:
                self._link_text.append(value)


def clean(v: str) -> str:
    return re.sub(r"\s+", " ", v or "").strip()


def norm(v: str) -> str:
    return v.translate(DIGIT_MAP)


def fetch() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read().decode("utf-8", errors="replace")


def number(v: str) -> float | int | None:
    try:
        s = norm(v).replace(",", "").replace(" ", "")
        return float(s) if "." in s else int(s)
    except (ValueError, TypeError):
        return None


def extract(text: str) -> dict[str, Any]:
    t = norm(text)
    key_patterns = {
        "tse_total": r"شاخص کل بورس\s*([0-9,]+)\s*\(?([+-][0-9.]+)%\)?",
        "ifx_total": r"شاخص کل فرابورس\s*([0-9,]+)\s*\(?([+-][0-9.]+)%\)?",
        "equal_weight": r"شاخص کل \(هم وزن\)\s*([0-9,]+)\s*\(?([+-][0-9.]+)%\)?",
        "large30": r"شاخص 30 شرکت بزرگ\s*([0-9,]+)\s*\(?([+-][0-9.]+)%\)?",
        "price_weighted": r"شاخص قيمت\(وزني-ارزشي\)\s*([0-9,]+)\s*\(?([+-][0-9.]+)%\)?",
        "price_equal": r"شاخص قيمت \(هم وزن\)\s*([0-9,]+)\s*\(?([+-][0-9.]+)%\)?",
    }
    indices: dict[str, Any] = {}
    for key, pattern in key_patterns.items():
        m = re.search(pattern, t)
        if m:
            indices[key] = {"value": number(m.group(1)), "change_pct": number(m.group(2))}

    breadth: dict[str, Any] = {}
    m = re.search(r"مجموع:\s*([0-9]+).*?منفی‌ها:\s*([0-9]+).*?بدون تغییر:\s*([0-9]+).*?مثبت‌ها:\s*([0-9]+)", t)
    if m:
        breadth = {"total": number(m.group(1)), "negative": number(m.group(2)), "unchanged": number(m.group(3)), "positive": number(m.group(4))}

    industry_rows = []
    start = t.find("شاخص صنعت")
    end = t.find("در مورد شاخص‌های بازار", start if start >= 0 else 0)
    if start >= 0:
        section = t[start:end if end > start else len(t)]
        # Keep the raw section because names and ordering can change.
        industry_rows = re.findall(r"([^\d]{2,80}?)([0-9]{3,}(?:,[0-9]{3})*)\s*\(([+-][0-9.]+)%\)", section)[:60]

    return {
        "indices": indices,
        "breadth": breadth,
        "industry_section_raw": section if start >= 0 else "",
        "industry_rows": [
            {"name": clean(name), "value": number(value), "change_pct": number(change)}
            for name, value, change in industry_rows
        ],
    }


def main() -> int:
    collected_at = datetime.now(timezone.utc).isoformat()
    try:
        html = fetch()
        parser = Parser()
        parser.feed(html)
        text = " ".join(parser.parts)
        extracted = extract(text)
        payload = {
            "source": "kamandar",
            "url": URL,
            "collected_at": collected_at,
            "status": "ok",
            "parser_version": 1,
            "indices_count": len(extracted["indices"]),
            "industry_count": len(extracted["industry_rows"]),
            **extracted,
            "links": [x for x in parser.links if "/app/market/indices" in x["href"] or "/app/market/" in x["href"]],
            "raw_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "raw_text": text[:120000],
        }
    except Exception as exc:
        payload = {"source": "kamandar", "url": URL, "collected_at": collected_at, "status": "error", "parser_version": 1, "error": repr(exc)}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.write_text(json.dumps({
        "source": "kamandar",
        "url": URL,
        "status": payload.get("status"),
        "checked_at": collected_at,
        "indices_count": payload.get("indices_count", 0),
        "industry_count": payload.get("industry_count", 0),
        "parser_version": payload.get("parser_version"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload.get("status"), "indices": payload.get("indices_count", 0), "industries": payload.get("industry_count", 0)}, ensure_ascii=False))
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
