#!/usr/bin/env python3
"""BabiMind LLM router.

OpenRouter Free is the active primary provider. Other providers remain as
future fallbacks and are only used when their secrets are explicitly present.
No provider secret is printed or written to reports.
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ORDER = [
    ("openrouter", "OPENROUTER_API_KEY", "OPENROUTER_MODEL", "openrouter/free", "https://openrouter.ai/api/v1/chat/completions"),
    ("deepseek", "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "deepseek-chat", "https://api.deepseek.com/chat/completions"),
    ("groq", "GROQ_API_KEY", "GROQ_MODEL", "openai/gpt-oss-120b", "https://api.groq.com/openai/v1/chat/completions"),
    ("cerebras", "CEREBRAS_API_KEY", "CEREBRAS_MODEL", "llama-4-scout-17b-16e-instruct", "https://api.cerebras.ai/v1/chat/completions"),
    ("gemini", "GEMINI_API_KEY", "GEMINI_MODEL", "gemini-flash-latest", "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"),
    ("openai", "OPENAI_API_KEY", "OPENAI_MODEL", "gpt-5-mini", "https://api.openai.com/v1/chat/completions"),
    ("anthropic", "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "claude-sonnet-4-5", "https://api.anthropic.com/v1/messages"),
    ("kimi", "MOONSHOT_API_KEY", "MOONSHOT_MODEL", "kimi-k2.5", "https://api.moonshot.ai/v1/chat/completions"),
]
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "babimind_provider_status.json"
LLM_OUT = ROOT / "reports" / "babimind_llm.json"


def quota_error(code: int, text: str) -> bool:
    t = text.lower()
    return code in (402, 408, 409, 429, 500, 502, 503, 504) or any(x in t for x in (
        "quota", "rate limit", "rate_limit", "resource_exhausted", "insufficient_quota", "credits", "billing"
    ))


def call(name: str, key: str, model: str, url: str, prompt: str) -> dict:
    headers = {"Content-Type": "application/json"}
    if name == "gemini":
        headers["X-goog-api-key"] = key
        url = url.format(model=model)
        body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2}}
    elif name == "anthropic":
        headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
        body = {"model": model, "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]}
    else:
        headers["Authorization"] = "Bearer " + key
        body = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
        if name == "openrouter":
            headers["HTTP-Referer"] = os.getenv("OPENROUTER_SITE_URL", "https://github.com/babakbadel/Tahlil")
            headers["X-Title"] = os.getenv("OPENROUTER_APP_NAME", "BabiMind")
            body["response_format"] = {"type": "json_object"}
    req = Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urlopen(req, timeout=75) as response:
        raw = json.loads(response.read().decode())
    if name == "gemini":
        text = raw["candidates"][0]["content"]["parts"][0]["text"]
    elif name == "anthropic":
        text = "".join(x.get("text", "") for x in raw.get("content", []))
    else:
        text = raw["choices"][0]["message"]["content"]
    return json.loads(text)


def run(prompt: str) -> tuple[dict | None, dict]:
    statuses = []
    for name, keyvar, modelvar, default, url in ORDER:
        key = os.getenv(keyvar)
        if not key:
            statuses.append({"provider": name, "status": "not_configured"})
            continue
        model = os.getenv(modelvar, default)
        try:
            result = call(name, key, model, url, prompt)
            statuses.append({"provider": name, "status": "ok", "model": model})
            return result, {"selected": name, "model": model, "statuses": statuses}
        except HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:2000]
            status = "quota_exhausted" if quota_error(exc.code, body) else "http_error"
            statuses.append({"provider": name, "status": status, "http_status": exc.code, "model": model})
            print(f"[BabiMind Router] {name}: {status}; trying next configured provider", flush=True)
        except (URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError) as exc:
            statuses.append({"provider": name, "status": "error", "error": str(exc), "model": model})
            print(f"[BabiMind Router] {name}: error; trying next configured provider", flush=True)
    return None, {"selected": None, "statuses": statuses}


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
    payload = {"status": "ok", "provider": meta.get("selected"), "model": meta.get("model"), "analysis": result} if result is not None else {"status": "unavailable", "provider": None, "analysis": None, "provider_status": meta}
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if result is None:
        print("[BabiMind Router] no configured provider available", flush=True)
        return 2
    print(f"[BabiMind Router] selected={meta['selected']} model={meta['model']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
