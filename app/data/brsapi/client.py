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

    def _get_json(self, endpoint: str, **params: Any) -> Any:
        response = self.session.get(
            f"{BASE_URL}/{endpoint}",
            params={"key": self.api_key, **params},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise BrsApiError(f"BRS API HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise BrsApiError("BRS API returned invalid JSON") from exc

    def get_all_symbols(self, security_type: int = 1) -> Any:
        return self._get_json("AllSymbols.php", type=security_type)

    def get_options(self) -> Any:
        """Fetch the dedicated live TSETMC options dataset.

        BRS documents Option.php as the endpoint for live option-board data.
        It already returns option-specific fields such as l18, base_l18,
        price_strike, interest_open and date_end, so options must not be
        discovered by filtering the generic AllSymbols endpoint.
        """
        return self._get_json("Option.php")
