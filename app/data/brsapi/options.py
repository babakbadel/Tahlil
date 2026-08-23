"""BRS option scanner for live/near-realtime option snapshots.

BRS is the primary upstream. This module deliberately does not fabricate
missing fields; unavailable fields remain None and can be enriched by a
provider-specific adapter later.
"""

from __future__ import annotations

from typing import Any, Iterable

from .client import BrsApiClient

OPTION_PREFIXES = ("ضملی",)
DEFAULT_TARGETS = {"ضملی7069", "ضملی7070"}


def _rows(payload: Any) -> list[dict[str, Any]]:
    rows = payload.get("data", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise TypeError("Unexpected BRS API response shape")
    return [row for row in rows if isinstance(row, dict)]


def _name(row: dict[str, Any]) -> str | None:
    for key in ("l18", "symbol", "ticker", "name"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def find_zmli(rows: Iterable[dict[str, Any]], targets: set[str] | None = None) -> list[dict[str, Any]]:
    """Return all active ZMLI rows, optionally narrowed to exact contracts."""
    target_set = targets
    result: list[dict[str, Any]] = []
    for row in rows:
        names = {_name(row), row.get("base_l18")}
        names = {n for n in names if isinstance(n, str)}
        if target_set and names & target_set:
            result.append(row)
        elif not target_set and any(n.startswith(OPTION_PREFIXES) for n in names):
            result.append(row)
    return result


def find_targets(rows: list[dict[str, Any]], names: set[str] = DEFAULT_TARGETS) -> list[dict[str, Any]]:
    return find_zmli(rows, names)


def snapshot(client: BrsApiClient, targets: set[str] | None = None) -> list[dict[str, Any]]:
    """Fetch the dedicated BRS live option feed and return ZMLI contracts."""
    return find_zmli(_rows(client.get_options()), targets)
