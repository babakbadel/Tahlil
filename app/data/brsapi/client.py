"""BRS API client for Tahlil.

Credentials are read only from the BRS_API_KEY environment variable.
Never hard-code or log the API key.
"""

from __future__ import annotations

import os
from typing import Any

import requests

BASE_URL = "https://api.brsapi.ir/Tsetmc"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


class BrsApiError(RuntimeError):
    pass


class BrsApiClient:
    def __init__(self, api_key: str | None = None, timeout: int = 20) -> None:
        self.api_key = api_key or os.getenv("BRS_API_KEY")
        if not self.api_key:
            raise BrsApiError("BRS_API_KEY is not configured")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": USER_AGENT, "Accept": "application/json, text/plain, */*"}
        )

    def get_all_symbols(self, security_type: int = 1) -> Any:
        response = self.session.get(
            f"{BASE_URL}/AllSymbols.php",
            params={"key": self.api_key, "type": security_type},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise BrsApiError(f"BRS API HTTP {response.status_code}")
        return response.json()
