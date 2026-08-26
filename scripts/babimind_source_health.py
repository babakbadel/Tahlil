#!/usr/bin/env python3
"""Health-check BabiMind data and news source endpoints."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "babimind_source_health.json"
NEWS_CONFIG = ROOT / "config" / "babimind_news_sources.json"
REPORT_DIR = ROOT / "reports"
REPORT_JSON = REPORT_DIR / "babimind_source_health.json"
REPORT_MD = REPORT_DIR / "babimind_source_health.md"


def check(url: str, timeout: int = 15) -> dict:
    started = time.monotonic()
    headers = {"User-Agent": "BabiMind-SourceHealth/1.1 (+https://github.com/babakbadel/Tahlil)"}
    try:
        req = Request(url, headers=headers, method="GET")
        with urlopen(req, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            sample = response.read(512)
        return {
            "status": "ok" if 200 <= status < 400 else "error",
            "http_status": status,
            "latency_ms": round((time.monotonic() - started) * 1000, 1),
            "bytes_sampled": len(sample),
        }
    except HTTPError as exc:
        return {"status": "error", "http_status": exc.code, "error": str(exc), "latency_ms": round((time.monotonic() - started) * 1000, 1)}
    except (URLError, TimeoutError, OSError) as exc:
        return {"status": "unavailable", "error": str(exc), "latency_ms": round((time.monotonic() - started) * 1000, 1)}
    except Exception as exc:
        return {"status": "error", "error": repr(exc), "latency_ms": round((time.monotonic() - started) * 1000, 1)}


def load_sources() -> list[dict]:
    if not CONFIG.exists():
        raise FileNotFoundError(CONFIG)
    catalog = json.loads(CONFIG.read_text(encoding="utf-8"))
    sources = [{**s, "source_class": "data"} for s in catalog.get("sources", [])]

    if NEWS_CONFIG.exists():
        news = json.loads(NEWS_CONFIG.read_text(encoding="utf-8"))
        for region_key, region in (("iran_sources", "iran"), ("international_sources", "international")):
            for s in news.get(region_key, []):
                sources.append({
                    "name": s["name"],
                    "type": "news",
                    "topic": "news_events",
                    "url": s["url"],
                    "tier": s.get("tier", "C"),
                    "source_class": "news",
                    "region": region,
                })
    return sources


def main() -> int:
    try:
        sources = load_sources()
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        print(f"invalid source catalog: {exc}", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc).isoformat()
    results = []
    for source in sources:
        result = check(source["url"], int(source.get("timeout_seconds", 15)))
        results.append({**source, **result, "checked_at": now})

    ok = sum(r["status"] == "ok" for r in results)
    unavailable = sum(r["status"] == "unavailable" for r in results)
    errors = len(results) - ok - unavailable
    data_results = [r for r in results if r["source_class"] == "data"]
    news_results = [r for r in results if r["source_class"] == "news"]
    summary = {
        "checked": len(results),
        "ok": ok,
        "unavailable": unavailable,
        "error": errors,
        "data_sources": len(data_results),
        "news_sources": len(news_results),
        "news_iran": sum(r.get("region") == "iran" for r in news_results),
        "news_international": sum(r.get("region") == "international" for r in news_results),
    }
    payload = {"model": "BabiMind", "checked_at": now, "summary": summary, "sources": results}

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# BabiMind Source Health", "", f"Checked: `{now}`", "",
        f"**Total:** {len(results)} | **Data:** {len(data_results)} | **News:** {len(news_results)}",
        f"**OK:** {ok} | **Unavailable:** {unavailable} | **Error:** {errors}",
        "", "| Source | Class | Region | Tier | Status | HTTP | Latency ms |",
        "|---|---|---|---|---|---:|---:|",
    ]
    for r in results:
        lines.append(f"| {r['name']} | {r['source_class']} | {r.get('region','-')} | {r.get('tier','-')} | {r['status']} | {r.get('http_status','-')} | {r.get('latency_ms','-')} |")
    lines += [
        "", "Health status is operational metadata, not evidence that a source is correct or suitable as Ground Truth.",
        "News sources are evidence for events, narratives, sentiment and geopolitical risk; they are not automatically economic ground truth.",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
