# BabiMind production forecast and decision runtime

The daily workflow and focused `model-runtime.yml` now execute actual inference instead of a demonstration decision or a fixed `not_connected` marker.

## Data path

1. Collect adjusted daily candles from BRS `Candlestick.php`, `type=3`, per symbol. Credentials come from the existing `BRS_API_KEY` GitHub secret. Official API contract: https://brsapi.ir/bourse-api-candlestick-webservice/ .
2. Validate Jalali/Gregorian dates, finite positive adjusted closes, duplicate observations, source collection time, and completed daily sessions. Before 12:40 Tehran, exclude today's still-incomplete candle. No future observations enter features.
3. Prefer the freshest validated series from BRS, FinPy adjusted prices, or the last known good cache. Never substitute an unadjusted series or erase a good cache because a provider timed out. Inputs retain source and collection time.
4. Build lagged 1/5/20-observation returns and 20-observation volatility. These are price-only features; missing flow, macro or options factors are not silently invented.
5. Forecast 1/5/20 observed trading sessions using the historical analog engine. At least 120 completed daily observations and 15 valid analogs are required. A series older than seven calendar days cannot produce a current forecast.
6. Train only on targets that finished strictly before each inference/backtest observation. Bullish means return >0.5%, neutral means within ±0.5%, bearish means below −0.5%. Probabilities come from weighted historical outcomes, sum to one, and are not assigned by an LLM.
7. Export expected return, adjusted price interval, sample count, similarity/confidence, walk-forward directional accuracy and Brier diagnostics. These diagnostics do not certify a tradable strategy; execution costs, liquidity, corporate-action revisions and overlapping samples still matter.
8. Pass sourced scenarios into DecisionEngine. Evidence after `as_of`, invalid probabilities and repeated decision IDs are rejected or deduplicated. Forecast history is immutable, append-only. Missing/stale/insufficient history produces WAIT and null probabilities, never a synthetic neutral prediction.

## Outputs

- `data/raw/brs_history_snapshot.json`: per-provider/per-symbol acquisition status.
- `data/history/<symbol>.json`: last validated adjusted price history, with provenance.
- `reports/babimind_forecast.json`: forecasts and diagnostics per symbol/horizon.
- `reports/babimind_decision.json` and `.md`: review-only decisions and a Persian table.
- `data/model_decision_history.jsonl`: immutable prediction records.
- `reports/babimind_model_stage_status.json`: connected layers with current availability, not a hard-coded readiness claim.
- `reports/babimind_pipeline.json`: includes forecast and decision layers; the daily LLM prompt receives both directly.
- `data/model_llm_history.jsonl`: lossless successful LLM results, deduplicated by analysis hash. Bounded context memory remains separate from this archive.

Forecast outputs can be `ok`, `partial`, `unavailable`, `stale`, or `insufficient_history`. `connected=true` describes integration, not data availability. Production does not place orders. `REVIEW_BULLISH`, `REVIEW_BEARISH`, and `WAIT` are evidence-review states.

Graphify remains a code/knowledge index. Its nodes and edges cannot manufacture a bullish/bearish market regime. Economic relationships require dated observations; the old structural-graph market score is excluded even if an old report is loaded.

## Execution

```bash
python -m pip install -r requirements-test.txt
python -m scripts.collect_brs_history
python -m scripts.run_model_runtime
python scripts/babimind_graph.py
python scripts/babimind_pipeline.py
python -m pytest -q
```

For reproducible historical runs, use `python -m scripts.run_model_runtime --as-of 2030-01-02T13:00:00Z` with a matching input fixture. The runtime rejects future source collection timestamps. Do not run that illustrative future date with live data for financial analysis.

Direct TSETMC connectivity can remain unavailable from a hosted runner; successful code execution is not proof of healthy upstream data. Per-source status and WAIT states are intentional operational outputs.
