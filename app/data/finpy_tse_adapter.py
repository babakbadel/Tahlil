"""FinPy-TSE adapter for BabiMind.

This module keeps the third-party package behind a small, fail-soft interface.
FinPy-TSE returns pandas DataFrames; BabiMind consumes normalized records.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

try:
    import finpy_tse as fpy
except Exception as exc:  # pragma: no cover - exercised in source-health jobs
    fpy = None
    _IMPORT_ERROR = str(exc)
else:
    _IMPORT_ERROR = None


def source_status() -> dict[str, Any]:
    return {
        "source": "finpy-tse",
        "upstream": "https://github.com/ARahimiQuant/finpy-tse",
        "available": fpy is not None,
        "import_error": _IMPORT_ERROR,
    }


def _records(frame: pd.DataFrame | None) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    out = frame.copy()
    out = out.where(pd.notna(out), None)
    return out.to_dict(orient="records")


def get_price_history(
    stock: str,
    start_date: str,
    end_date: str,
    *,
    adjust_price: bool = True,
) -> list[dict[str, Any]]:
    """Return normalized daily price history for a Tehran Stock Exchange symbol."""
    if fpy is None:
        raise RuntimeError(f"finpy-tse unavailable: {_IMPORT_ERROR}")
    frame = fpy.Get_Price_History(
        stock=stock,
        start_date=start_date,
        end_date=end_date,
        ignore_date=False,
        adjust_price=adjust_price,
        show_weekday=False,
        double_date=False,
    )
    return _records(frame)


def get_ri_history(
    stock: str,
    start_date: str,
    end_date: str,
) -> list[dict[str, Any]]:
    """Return daily real/legal-person flow history."""
    if fpy is None:
        raise RuntimeError(f"finpy-tse unavailable: {_IMPORT_ERROR}")
    frame = fpy.Get_RI_History(
        stock=stock,
        start_date=start_date,
        end_date=end_date,
        ignore_date=False,
        show_weekday=False,
        double_date=False,
        alt=False,
    )
    return _records(frame)


def get_market_watch() -> list[dict[str, Any]]:
    """Return the latest market-watch snapshot when the upstream endpoint is available."""
    if fpy is None:
        raise RuntimeError(f"finpy-tse unavailable: {_IMPORT_ERROR}")
    return _records(fpy.Get_MarketWatch())


def get_usd_rial(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Return FinPy-TSE's historical USD/IRR series."""
    if fpy is None:
        raise RuntimeError(f"finpy-tse unavailable: {_IMPORT_ERROR}")
    return _records(
        fpy.Get_USD_RIAL(
            start_date=start_date,
            end_date=end_date,
            ignore_date=False,
            show_weekday=False,
            double_date=False,
        )
    )
