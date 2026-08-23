"""Option scanner built on top of the BRS all-symbols feed."""

from __future__ import annotations

from typing import Any

from .client import BrsApiClient

TARGETS = {"ضملی7070", "ضملی7071", "ضخود8059", "فملی", "خودرو"}


def find_targets(rows: list[dict[str, Any]], names: set[str] = TARGETS) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("l18") in names or row.get("base_l18") in names]


def snapshot(client: BrsApiClient) -> list[dict[str, Any]]:
    data = client.get_all_symbols(security_type=1)
    rows = data.get("data", data) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise TypeError("Unexpected BRS API response shape")
    return find_targets(rows)
