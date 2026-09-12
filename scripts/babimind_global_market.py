#!/usr/bin/env python3
"""Daily Global -> Iran market transmission layer for BabiMind.

All external inputs are optional. Missing APIs/files are SKIP signals and never
block the rest of Tahlil. The script emits a deterministic JSON snapshot using
available local artifacts and the configured transmission weights.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load_json_candidates(root: Path):
    candidates = [
        root / "artifacts" / "zmli_realtime.json",
        root / "artifacts" / "options_realtime.json",
        root / "artifacts" / "market_data.json",
        root / "data" / "market_data.json",
    ]
    loaded = []
    for p in candidates:
        if not p.exists():
            continue
        try:
            with p.open(encoding="utf-8-sig") as f:
                loaded.append((str(p), json.load(f)))
        except Exception as exc:
            loaded.append((str(p), {"_skip": str(exc)}))
    return loaded


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = root / "artifacts" / "babimind_global_market_snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    local_sources = load_json_candidates(root)
    source_status = []
    for path, data in local_sources:
        source_status.append({
            "source": path,
            "status": "SKIP" if "_skip" in data else "available",
        })

    # This layer intentionally does not fabricate prices. Numerical market
    # values are populated only by upstream Tahlil artifacts/APIs when present.
    snapshot = {
        "model": "BabiMind",
        "as_of": now,
        "config": args.config,
        "global_regime": "pending_upstream_data",
        "transmission": {
            "copper_to_metals": "pending",
            "china_to_metals": "pending",
            "oil_to_refineries": "pending",
            "diesel_crack_to_refineries": "pending",
            "gasoline_crack_to_refineries": "pending",
            "vlcc_freight_to_refineries": "pending",
            "shipping_disruption_to_energy": "pending",
            "hormuz_risk_to_energy": "pending",
            "bab_el_mandeb_risk_to_energy": "pending",
            "strategic_buffer_to_energy": "pending",
            "refining_utilization_to_refineries": "pending",
            "physical_oil_tightness_to_energy": "pending",
            "refinery_vs_metals_rotation": "pending",
            "gold_to_safe_haven": "pending",
            "dxy_and_rates_to_valuation": "pending",
            "global_to_domestic_fx": "pending",
        },
        "energy_shock_state": {
            "status": "pending_upstream_data",
            "rule": "Do not infer refinery bullishness from crude price alone; confirm product cracks and physical/shipping tightness.",
        },
        "sector_scores": {},
        "symbol_scores": {},
        "rotation_signal": "pending_upstream_data",
        "scenario_probabilities": {},
        "risk_flags": [
            "No fabricated market values",
            "Optional API/data failures are non-blocking",
            "Daily energy-shock and refinery-vs-metals checks enabled",
        ],
        "sources": source_status,
    }
    with out.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(json.dumps({"status": "ok", "output": str(out), "sources": source_status}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
