#!/usr/bin/env python3
"""BabiMind LLM router.

OpenRouter Free is the only active LLM provider. Gemini and all other
providers are intentionally disabled in this stage. Secrets are never
printed or written to reports.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

PROVIDER = "openrouter"
KEY_VAR = "OPENROUTER_API_KEY"
MODEL_VAR = "OPENROUTER_MODEL"
DEFAULT_MODEL = "openrouter/free"
URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_ATTEMPTS = 3
REQUEST_TIMEOUT = 75
RETRY_DELAYS = (3, 8)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "babimind_provider_status.json"
LLM_OUT = ROOT / "reports" / "babimind_llm.json"


def is_retryable(code: int, text: str) -> bool:
    t = text.lower()
    return code in (408, 409, 429, 500, 502, 503, 504) or any(x in t for x in (
        "quota", "rate limit", "rate_limit", "resource_exhausted", "credits", "temporarily unavailable"
    ))


def call_openrouter(key: str, model: str, prompt: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + key,
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://github.com/babakbadel/Tahlil"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME", "BabiMind"),
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    req = Request(URL, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        raw = json.loads(response.read().decode("utf-8"))
    text = raw["choices"][0]["message"]["content"]
    if isinstance(text, list):
        text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("OpenRouter returned JSON that is not an object")
    return result


def run(prompt: str) -> tuple[dict | None, dict]:
    key = os.getenv(KEY_VAR)
    model = os.getenv(MODEL_VAR, DEFAULT_MODEL)
    statuses = []

    if not key:
        statuses.append({"provider": PROVIDER, "status": "not_configured", "model": model})
        return None, {"selected": None, "model": model, "statuses": statuses}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = call_openrouter(key, model, prompt)
            statuses.append({"provider": PROVIDER, "status": "ok", "model": model, "attempt": attempt})
            return result, {"selected": PROVIDER, "model": model, "statuses": statuses}
        except HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:2000]
            retryable = is_retryable(exc.code, body)
            status = "quota_exhausted" if exc.code == 429 or "quota" in body.lower() else "http_error"
            statuses.append({"provider": PROVIDER, "status": status, "http_status": exc.code, "model": model, "attempt": attempt})
            print(f"[BabiMind OpenRouter] attempt={attempt} status={status} http={exc.code}", flush=True)
            if not retryable or attempt == MAX_ATTEMPTS:
                break
            time.sleep(RETRY_DELAYS[attempt - 1])
        except (URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError, ValueError) as exc:
            statuses.append({"provider": PROVIDER, "status": "error", "error": str(exc)[:500], "model": model, "attempt": attempt})
            print(f"[BabiMind OpenRouter] attempt={attempt} error={type(exc).__name__}", flush=True)
            if attempt == MAX_ATTEMPTS:
                break
            time.sleep(RETRY_DELAYS[attempt - 1])

    return None, {"selected": None, "model": model, "statuses": statuses}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--output", type=Path, default=LLM_OUT)
    args = parser.parse_args()

    default_prompt = (
        "Analyze the supplied BabiMind market intelligence. Return JSON with exactly these top-level keys: "
        "regime, scenarios, game_theory, dynamic_system, political_economy, market_implications, confidence, data_gaps. "
        "Be explicit about uncertainty and do not invent unavailable data.\n"
    )
    prompt = args.prompt_file.read_text(encoding="utf-8") if args.prompt_file else default_prompt
    result, meta = run(prompt)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if result is None:
        payload = {
            "status": "unavailable",
            "provider": PROVIDER,
            "model": meta.get("model"),
            "analysis": None,
            "provider_status": meta,
        }
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[BabiMind OpenRouter] unavailable after bounded retries", flush=True)
        return 2

    payload = {
        "status": "ok",
        "provider": PROVIDER,
        "model": meta.get("model"),
        "analysis": result,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[BabiMind OpenRouter] selected={PROVIDER} model={meta['model']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
