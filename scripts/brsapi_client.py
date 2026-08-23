import os
from typing import Any

import requests

BRS_API_KEY = os.environ["BRS_API_KEY"]
BRS_API_URL = os.getenv(
    "BRS_API_URL",
    "https://Api.BrsApi.ir/Tsetmc/AllSymbols.php",
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def fetch_symbols(symbol_type: int = 1) -> Any:
    response = requests.get(
        BRS_API_URL,
        params={"key": BRS_API_KEY, "type": symbol_type},
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    data = fetch_symbols()
    print(f"received={len(data) if isinstance(data, list) else 'object'}")
