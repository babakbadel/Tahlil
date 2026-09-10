import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="BabiMind TSETMC Relay", version="1.0.0")

TIMEOUT = float(os.getenv("TSETMC_TIMEOUT", "20"))
CACHE_TTL = int(os.getenv("TSETMC_CACHE_TTL", "20"))
USER_AGENT = os.getenv(
    "TSETMC_USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36",
)

_cache: dict[str, tuple[float, Any]] = {}


def _cached(key: str):
    item = _cache.get(key)
    if item and time.time() - item[0] < CACHE_TTL:
        return item[1]
    return None


async def _get(url: str) -> Any:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/plain, */*"}
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers=headers) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()


async def _fetch(name: str, urls: list[str]) -> dict[str, Any]:
    cached = _cached(name)
    if cached is not None:
        return {"status": "ok", "cached": True, "data": cached}
    last_error = None
    for url in urls:
        try:
            data = await _get(url)
            _cache[name] = (time.time(), data)
            return {"status": "ok", "cached": False, "source": url, "data": data}
        except Exception as exc:
            last_error = repr(exc)
    return {"status": "error", "error": last_error}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "babimind-tsetmc-relay",
        "utc": datetime.now(timezone.utc).isoformat(),
        "cache_ttl_seconds": CACHE_TTL,
    }


@app.get("/market/watch")
async def market_watch():
    result = await _fetch(
        "market_watch",
        [
            "https://webgw.tse.ir/InstrumentProvider/api/v1/MarketWatch/MarketWatchCash/fa",
            "https://cdn.tsetmc.com/api/ClosingPrice/GetMarketWatch?market=0&paperTypes[0]=1&paperTypes[1]=2&paperTypes[2]=3&paperTypes[3]=4&paperTypes[4]=5&paperTypes[5]=6&paperTypes[6]=7&paperTypes[7]=8&paperTypes[8]=9&withBestLimits=true&hEven=0&RefID=0",
        ],
    )
    if result["status"] != "ok":
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/market/client-type")
async def client_type():
    result = await _fetch(
        "client_type_all",
        ["https://cdn.tsetmc.com/api/ClientType/GetClientTypeAll"],
    )
    if result["status"] != "ok":
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/options/watch")
async def options_watch():
    result = await _fetch(
        "options_watch",
        [
            "https://webgw.tse.ir/InstrumentProvider/api/v1/MarketWatch/MarketWatchOption/fa",
            "https://webgw.tse.ir/InstrumentProvider/api/v1/MarketWatch/MarketWatchTradeOption/fa",
        ],
    )
    if result["status"] != "ok":
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/instrument/{isin}")
async def instrument(isin: str):
    if len(isin) < 8 or len(isin) > 32:
        raise HTTPException(status_code=400, detail="invalid ISIN")
    result = await _fetch(
        f"instrument:{isin}",
        [f"https://webgw.tse.ir/InstrumentProvider/api/v1/Instrument/LiveInstrumentByIdQuery/fa?InstrumentId={isin}"],
    )
    if result["status"] != "ok":
        raise HTTPException(status_code=502, detail=result)
    return result


@app.get("/")
async def root():
    return {"service": "babimind-tsetmc-relay", "endpoints": ["/health", "/market/watch", "/market/client-type", "/options/watch", "/instrument/{isin}"]}
