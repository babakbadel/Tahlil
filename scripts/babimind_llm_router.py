#!/usr/bin/env python3
"""Multi-provider BabiMind router. DeepSeek first; then OpenAI, Anthropic, Gemini, Kimi."""
from __future__ import annotations
import json, os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ORDER=[
("deepseek","DEEPSEEK_API_KEY","DEEPSEEK_MODEL","deepseek-chat","https://api.deepseek.com/chat/completions"),
("openai","OPENAI_API_KEY","OPENAI_MODEL","gpt-5-mini","https://api.openai.com/v1/chat/completions"),
("anthropic","ANTHROPIC_API_KEY","ANTHROPIC_MODEL","claude-sonnet-4-5","https://api.anthropic.com/v1/messages"),
("gemini","GEMINI_API_KEY","GEMINI_MODEL","gemini-flash-latest","https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"),
("kimi","MOONSHOT_API_KEY","MOONSHOT_MODEL","kimi-k2.5","https://api.moonshot.ai/v1/chat/completions")]
OUT=Path(__file__).resolve().parents[1]/"reports"/"babimind_provider_status.json"

def limited(code,text):
 t=text.lower(); return code in (401,402,403,408,409,429,500,502,503,504) or any(x in t for x in ("quota","rate limit","rate_limit","resource_exhausted","insufficient_quota","credits","billing"))

def call(name,key,model,url,prompt):
 h={"Content-Type":"application/json"}
 if name=="gemini":
  h["X-goog-api-key"]=key; url=url.format(model=model); body={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.2,"responseMimeType":"application/json"}}
 elif name=="anthropic":
  h.update({"x-api-key":key,"anthropic-version":"2023-06-01"}); body={"model":model,"max_tokens":4096,"messages":[{"role":"user","content":prompt}]}
 else:
  h["Authorization"]="Bearer "+key; body={"model":model,"messages":[{"role":"user","content":prompt}],"temperature":0.2,"response_format":{"type":"json_object"}}
 req=Request(url,data=json.dumps(body).encode(),headers=h,method="POST")
 with urlopen(req,timeout=60) as r: raw=json.loads(r.read().decode())
 if name=="gemini": text=raw["candidates"][0]["content"]["parts"][0]["text"]
 elif name=="anthropic": text="".join(x.get("text","") for x in raw.get("content",[]))
 else: text=raw["choices"][0]["message"]["content"]
 return json.loads(text)

def run(prompt):
 statuses=[]
 for name,keyvar,modelvar,default,url in ORDER:
  key=os.getenv(keyvar)
  if not key: statuses.append({"provider":name,"status":"not_configured"}); continue
  model=os.getenv(modelvar,default)
  try:
   result=call(name,key,model,url,prompt); statuses.append({"provider":name,"status":"ok","model":model}); return result,{"selected":name,"statuses":statuses}
  except HTTPError as e:
   body=e.read().decode("utf-8","replace")[:2000]; statuses.append({"provider":name,"status":"quota_or_http_error" if limited(e.code,body) else "http_error","http_status":e.code,"model":model}); print(f"[BabiMind Router] {name}: fallback",flush=True)
  except (URLError,TimeoutError,OSError,KeyError,json.JSONDecodeError) as e:
   statuses.append({"provider":name,"status":"error","error":str(e),"model":model}); print(f"[BabiMind Router] {name}: error -> fallback",flush=True)
 return None,{"selected":None,"statuses":statuses}

if __name__=="__main__":
 result,meta=run(os.environ.get("BABIMIND_PROMPT","Return JSON with regime, scenarios, game_theory, dynamic_system, political_economy, market_implications, confidence, data_gaps.")); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
 if result is None: raise SystemExit("No configured/available BabiMind LLM provider")
 print(json.dumps(result,ensure_ascii=False))
