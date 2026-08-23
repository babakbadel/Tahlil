---
name: iran-market-realtime
description: Real-time and event-time data acquisition and analysis contract for Iran equity and options markets, designed for the Babak Analysis / Bobby Hosh engine.
---

# Iran Market Realtime Skill

## Purpose
Provide a unified, timestamped data contract for Iran's equity (بورس) and listed options markets. The skill is an analytical/data-ingestion specification, not a substitute for an upstream market-data provider.

## Scope
- Equity market: symbols, last/close prices, OHLC, volume, value, trade count, bid/ask and order-book levels, queues, market breadth, real-person/legal-person flow when available.
- Options market: contracts, underlying, call/put, strike, expiry, last/bid/ask, volume, value, open interest, implied volatility, and Greeks when derivable.
- Cross-market linkage: every option contract must resolve to its underlying instrument.
- Event-time intelligence: preserve source timestamp, receive timestamp, sequence when available, and source/provider identity.
- Snapshot history for backtesting and regime/event analysis.

## Data hierarchy
Prefer authoritative Iranian market sources and existing project skills in this order when applicable:
1. TSETMC / exchange market data
2. SEO / TSE / IFB / official derivatives sources
3. Codal for company disclosures and fundamentals
4. Other approved market-data providers only as secondary sources

Do not fabricate missing real-time fields. Mark unavailable fields as `null` and attach data-quality metadata.

## Security
- Never hard-code API keys, tokens, cookies, or credentials.
- Read credentials from environment variables or the project's secret manager.
- Never print secrets in logs, JSON responses, commits, or error messages.

## Canonical JSON envelope
```json
{
  "schema_version": "1.0",
  "market": "IR",
  "asset_class": "equity|option",
  "source": "provider",
  "event_time": "ISO-8601",
  "received_at": "ISO-8601",
  "sequence": null,
  "data_quality": {
    "status": "live|delayed|stale|partial|error",
    "age_ms": 0
  },
  "data": {}
}
```

## Equity record
Required when available:
- symbol, instrument_id
- last_price, close_price, reference_price
- open, high, low
- volume, value, trade_count
- best_bid, best_ask
- bid/ask depth
- buy/sell queue indicators
- real/legal-person flow fields when the source provides them

## Option record
Required when available:
- contract_id, symbol
- underlying_symbol, underlying_id
- option_type: `call|put`
- strike
- expiry
- last_price, bid, ask
- volume, value, open_interest
- implied_volatility
- delta, gamma, theta, vega, rho
- intrinsic_value, time_value when calculable

## Derived analytics
Derived values must be explicitly marked as calculated and must retain their inputs/model assumptions.

Useful calculations include:
- IV from market price
- Black-Scholes or appropriate option-pricing model Greeks
- moneyness and distance to strike
- put/call volume and OI ratios
- OI change and abnormal volume/OI
- option premium relative to underlying movement
- implied move
- underlying-option flow divergence

Never treat model-derived Greeks or IV as exchange-provided facts unless the source explicitly supplies them.

## API contract
Recommended service endpoints:
- `GET /api/v1/equity/market`
- `GET /api/v1/equity/symbol/{symbol}`
- `GET /api/v1/equity/trades/{symbol}`
- `GET /api/v1/equity/orderbook/{symbol}`
- `GET /api/v1/options/market`
- `GET /api/v1/options/contracts`
- `GET /api/v1/options/{contract}`
- `GET /api/v1/options/{contract}/orderbook`
- `GET /api/v1/options/chain/{underlying}`
- `GET /api/v1/options/greeks/{contract}`
- `GET /api/v1/derivatives/underlying/{symbol}`

For streaming, prefer WebSocket or SSE over client-side polling when the upstream source permits it.

## Collector architecture
`Source Adapter -> Collector -> Normalizer -> Quality Gate -> Cache/Stream -> JSON API -> Bobby Hosh`

The collector should support reconnect/backoff, rate-limit handling, stale-data detection, duplicate-event suppression, and structured logging.

Redis/cache is recommended for the latest snapshot and short-lived stream state. Persistent storage should be used for historical snapshots required by backtests.

## Integration with Bobby Hosh
The skill feeds, but does not replace, the existing analysis engines:
- TSETMC skill
- Codal skill
- technical-analysis skill
- Game Theory / behavioral layer
- macroeconomic factors
- Decision Engine

The model must preserve event ordering and avoid look-ahead bias. Real-time observations become eligible for decisions only after their recorded `event_time`.

## Decision-facing signals
Expose normalized observations for:
- market breadth and index regime
- volume/value acceleration
- money-flow direction
- liquidity/order-book imbalance
- queue pressure
- equity-to-option divergence
- option OI accumulation/unwinding
- IV expansion/compression
- abnormal call/put activity
- underlying momentum versus option premium response

Signals are evidence, not automatic buy/sell instructions. Confidence and data quality must accompany downstream model outputs.

## Failure policy
If the upstream feed is unavailable:
1. Do not invent values.
2. Mark the feed stale/error.
3. Preserve the last known timestamp separately from current receive time.
4. Prevent stale data from being interpreted as a new event.
5. Log the failure with provider-neutral diagnostics.

## Testing requirements
At minimum test:
- JSON schema validation
- timestamp ordering
- duplicate events
- stale feed detection
- reconnect behavior
- missing fields
- option/underlying mapping
- IV/Greeks calculation against known fixtures
- no-look-ahead behavior in historical replay

## Implementation roadmap
Phase 1: schema + adapters + normalized REST JSON.
Phase 2: live collector + cache + streaming.
Phase 3: historical recorder + replay/backtest.
Phase 4: anomaly detection and Decision Engine integration.
