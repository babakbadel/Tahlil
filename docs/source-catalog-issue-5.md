# Source Catalog: issue #5 implementation and remaining work

The canonical executable catalog for coverage is `config/babimind_factors.json`.
Its declared count now matches its 490 unique entries. These are catalog definitions,
not 490 validated economic series. The YAML registry remains a design backlog;
`config/babimind_factor_source_mapping.json` remains a legacy group mapping and no
longer determines factor availability. The >500 target is explicitly unmet.

## Observation contract

Collectors may publish `reports/babimind_factor_observations.json` with an
`observations` array, one consolidated observation per canonical `factor_id`:

```json
{
  "observations": [
    {
      "factor_id": "ai_price",
      "source": "IMF",
      "timestamp": "2026-10-25T08:00:00Z",
      "raw_value": 0,
      "normalized_score": 0,
      "confidence": 0.8,
      "max_age_seconds": 86400,
      "state": "ok"
    }
  ]
}
```

This is a contract example, not a real observation. The factor/source names are
existing catalog entries; their economic definition, actual series and normalization
must be validated before a collector publishes them. Do not copy example data into
production. `timestamp` is the economic observation timestamp, not HTTP check time.
`max_age_seconds` must reflect that series' publication cadence. Units and score
normalization need series-specific definitions in the next catalog migration.

- Available: numeric, finite raw value and score, mapped source, timezone-aware
  non-future timestamp, positive TTL and positive confidence in [0,1], within TTL.
- Partial: incomplete or invalid observation, or explicitly partial input.
- Stale: otherwise valid observation older than its allowed age.
- Unavailable: no observation or upstream error/timeout/unavailable.

All non-Available records have zero signal weight, are excluded from aggregation
and retain `retry_next_run=true`. Raw zero remains a real value. Error reasons are
separate from the four reporting states. Duplicate/unknown factor observations,
duplicate catalog IDs and count mismatches fail validation rather than inflate coverage.

Coverage is `Available / actual_catalog_count`; Partial is reported separately.
Every record retains source, timestamp, raw value, normalized score, confidence,
freshness, state, eligibility and retry metadata, with null for missing evidence.
There is no dependency on endpoint health in this computation.

## Verification and limitations

`python -m pytest -q tests/test_factor_coverage.py`

`python scripts/babimind_factor_coverage.py --output-dir /tmp/factor-coverage`

No collector currently writes this observation contract. Consequently the initial
honest report is 490 Unavailable, not evidence that all upstream APIs are down.
The old 100% coverage claim measured group endpoint health and is removed.
Source confidence and signal weights no longer give failed sources nonzero weight,
failed groups cannot select a primary, and unmatched rotation sources receive zero.
Coverage validation is mandatory in unified/research workflows and CI.

## Prioritized follow-up (issue remains open)

1. Define series, units, transforms and release cadence for curated Iranian factors;
   reconcile YAML definitions with the JSON catalog. Add >500 meaningful definitions
   only after reviewing duplicates and economically meaningless generated entries.
2. Migrate human source names to stable source IDs with aliases. Unify health and
   pipeline loaders; separate official numerical series from news corroboration.
3. Adapt existing TSETMC/options observations to this contract, with captured fixtures;
   then implement CBI/SCI/Codal/IME, followed by energy/global sources in issue #5.
4. Add release/published/retrieved timestamps, revision metadata, run IDs, catalog
   hashes and immutable as-of history. Enforce no-look-ahead using both observation
   and publication time before any backtest or decision consumption.
5. Require coverage/schema checks before report publishing; retain degraded reports
   with explicit status when upstream providers fail, without carrying old availability.

## Evidence relationships

- EXTRACTED: JSON catalog -> coverage factor IDs (`scripts/babimind_factor_coverage.py`).
- EXTRACTED: validated observation -> coverage state (same script).
- EXTRACTED: failed source -> zero legacy signal weight (`babimind_signal_weight.py`).
- INFERRED: explicit unavailable reporting reduces false confidence in downstream
  analysis; trading improvement has not been measured.

Observed at 2026-10-25. These are code relationships, not market observations.
