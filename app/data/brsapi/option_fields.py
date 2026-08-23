"""Canonical option-field extraction from heterogeneous BRS rows.

The adapter is intentionally conservative: it maps only fields that are
actually present in the upstream row and never invents market values.
"""
from __future__ import annotations

from typing import Any

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "symbol": ("l18", "symbol", "ticker", "name"),
    "underlying": ("base_l18", "underlying", "underlying_symbol"),
    "instrument_id": ("insCode", "inscode", "instrument_id", "id"),
    "last": ("last", "last_price", "pl", "pLast"),
    "close": ("close", "close_price", "pc", "pClosing"),
    "bid": ("bid", "best_bid", "buy_price", "pd1"),
    "ask": ("ask", "best_ask", "sell_price", "po1"),
    "volume": ("volume", "vol", "qTotTran5J"),
    "value": ("value", "trade_value", "value_traded"),
    "trade_count": ("trade_count", "count", "tno"),
    "open_interest": ("open_interest", "oi", "openInterest"),
    "strike": ("strike", "strike_price", "exercise_price"),
    "expiry": ("expiry", "expiration", "expiration_date", "maturity"),
    "option_type": ("option_type", "type", "contract_type"),
}


def first(row: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for key in aliases:
        if key in row and row[key] is not None:
            return row[key]
    return None


def normalize_option_row(row: dict[str, Any]) -> dict[str, Any]:
    return {canonical: first(row, aliases) for canonical, aliases in FIELD_ALIASES.items()}
