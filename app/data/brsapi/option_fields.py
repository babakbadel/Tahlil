"""Canonical option-field extraction from heterogeneous BRS rows.

The adapter is intentionally conservative: it maps only fields that are
actually present in the upstream row and never invents market values.
"""
from __future__ import annotations

from typing import Any

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "symbol": ("l18", "symbol", "ticker", "name"),
    "underlying": ("base_l18", "underlying", "underlying_symbol"),
    "instrument_id": ("id", "insCode", "inscode", "instrument_id"),
    "last": ("pl", "last", "last_price", "pLast"),
    "close": ("pc", "close", "close_price", "pClosing"),
    "bid": ("pd1", "bid", "best_bid", "buy_price"),
    "ask": ("po1", "ask", "best_ask", "sell_price"),
    "volume": ("tvol", "volume", "vol", "qTotTran5J"),
    "value": ("tval", "value", "trade_value", "value_traded"),
    "trade_count": ("tno", "trade_count", "count"),
    "open_interest": ("interest_open", "open_interest", "oi", "openInterest"),
    "strike": ("price_strike", "strike", "strike_price", "exercise_price"),
    "expiry": ("date_end", "expiry", "expiration", "expiration_date", "maturity"),
    "option_type": ("type", "option_type", "contract_type"),
}


def first(row: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for key in aliases:
        if key in row and row[key] is not None:
            return row[key]
    return None


def normalize_option_row(row: dict[str, Any]) -> dict[str, Any]:
    return {canonical: first(row, aliases) for canonical, aliases in FIELD_ALIASES.items()}
