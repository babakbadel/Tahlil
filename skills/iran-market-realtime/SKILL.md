---
name: iran-market-realtime
description: Production-grade real-time and event-time market-data skill for Iran equities and listed options, feeding the Babak Analysis / Bobby Hosh engine.
version: 1.1.0
---

# Iran Market Realtime Skill

## Purpose
Provide a production-grade, provider-neutral contract for real-time and near-real-time data from Iran's equity and listed-options markets. The skill separates source facts from derived analytics and makes freshness, event ordering, provenance, and data quality first-class fields.

## Reference standard
This skill follows the strongest applicable patterns from:
- the project TSETMC skill: instrument identifiers, source timestamps, order-book/client-type semantics, and authoritative-source priority;
- established market-data WebSocket skills: persistent streaming, reconnect/backoff, heartbeat, subscription validation, and explicit stream/event types;
- the project's existing BRS adapter: normalized JSON, polling fallback, and Secret-based credentials.

The TSETMC skill documents CDN JSON, legacy endpoints, instrument-code semantics, and market/asset classification; use those references rather than inventing endpoint or field meanings. citeturn0search1turn0search13

## Scope
### Equity
- instrument identity and market classification
- last/reference/close/open/high/low
- volume, value, trade count
- best bid/ask and depth
- queue pressure
- market breadth and indices
- حقیقی/حقوقی flow when supplied by the source

### Listed options
- contract identity
- underlying identity
- call/put
- strike and expiry
- last/bid/ask
- volume/value
- open interest and OI change when available
- IV and Greeks when supplied or calculated
- intrinsic/time value and moneyness when calculable
- contract-to-underlying linkage

## Source hierarchy
Use the strongest available source for each field:
1. TSETMC / official exchange market data
2. SEO / TSE / IFB / official derivatives data
3. BRS or another approved market-data provider
4. Other secondary providers
5. Derived/calculated values only when inputs are sufficient

Do not silently substitute a secondary source for an authoritative source. Record `source`, `source_type`, and `source_field` where practical.

## Critical realtime rule
A polling API is **not** an exchange-native tick feed. If the upstream is snapshot/poll based, expose the service as `near_realtime`/`snapshot_stream`, not `tick_realtime`. WebSocket/SSE at our API layer only pushes newly observed upstream snapshots. This distinction must remain visible to Bobby Hosh.

## Canonical event envelope
```json
{
  "schema_version": "1.1",
  "event_id": "provider:instrument:event_time:sequence",
  "event_type": "snapshot|trade|quote|depth|index|flow|option_quote|option_oi",
  "market": "IR",
  "asset_class": "equity|option|index",
  "source": "TSETMC|BRS_API|SEO|TSE|IFB|other",
  "source_type": "authoritative|secondary|derived",
  "instrument_id": null,
  "symbol": null,
  "event_time": "ISO-8601",
  "received_at": "ISO-8601",
  "sequence": null,
  "data_quality": {
    "status": "live|near_realtime|delayed|stale|partial|error",
    "age_ms": 0,
    "upstream_reachable": true,
    "field_completeness": 1.0,
    "clock_skew_ms": null
  },
  "data": {}
}
```

### Timestamp rules
- Preserve source/event timestamp whenever available; never replace it with receive time.
- Keep `received_at` separately.
- If TSETMC supplies event date/time fields such as `dEven`/`hEven`, normalize them to an ISO-8601 `event_time` while retaining the raw values in provenance. citeturn0search13
- Use UTC internally for storage/transport; render Asia/Tehran only at presentation boundaries.
- `age_ms = received_at - event_time` after clock normalization.
- A newer `received_at` does not make an old event new.

## Identity rules
- Prefer stable provider instrument/contract identifiers over Persian display names.
- Keep both `instrument_id` and `symbol` when available.
- Options must contain `underlying_id` and `underlying_symbol` whenever the provider exposes them.
- Never join option chains by display name alone when a stable identifier exists.
- Preserve provider identifiers verbatim in provenance.

## Equity record
```json
{
  "instrument_id": "...",
  "symbol": "...",
  "last_price": null,
  "close_price": null,
  "reference_price": null,
  "open": null,
  "high": null,
  "low": null,
  "volume": null,
  "value": null,
  "trade_count": null,
  "best_bid": null,
  "best_ask": null,
  "bid_depth": [],
  "ask_depth": [],
  "buy_queue": null,
  "sell_queue": null,
  "real_buy_volume": null,
  "real_sell_volume": null,
  "legal_buy_volume": null,
  "legal_sell_volume": null
}
```

## Option record
```json
{
  "contract_id": "...",
  "symbol": "...",
  "underlying_id": "...",
  "underlying_symbol": "...",
  "option_type": "call|put",
  "strike": null,
  "expiry": null,
  "last_price": null,
  "bid": null,
  "ask": null,
  "volume": null,
  "value": null,
  "open_interest": null,
  "oi_change": null,
  "implied_volatility": null,
  "delta": null,
  "gamma": null,
  "theta": null,
  "vega": null,
  "rho": null
}
```

## Source vs derived data
Every calculated field must carry provenance such as:
```json
{
  "calculated": true,
  "model": "black_scholes",
  "inputs": ["underlying_price", "strike", "expiry", "rate", "iv"]
}
```

Never label calculated IV/Greeks as exchange-provided facts. If IV cannot be solved reliably, return `null` with a reason instead of forcing a value.

## Realtime stream contract
The service exposes:
- `WS /ws/market`
- `GET /api/v1/stream/market` (SSE)

Streaming requirements:
- send a current snapshot immediately after connection when available;
- then send only new event IDs/snapshots;
- bounded per-client queues;
- drop oldest queued snapshot for a slow client rather than blocking the collector;
- heartbeat/keepalive for SSE and WebSocket;
- reconnect with exponential backoff and jitter at the upstream adapter;
- never duplicate an event after reconnect when `event_id` is known;
- expose connection/feed health separately from market-data values.

These are standard streaming patterns: live feeds should use persistent WebSockets rather than a tight quote-poll loop where the upstream supports it. citeturn0search3turn0search10

## Subscription contract
When a true upstream WebSocket becomes available, subscriptions must be typed and validated:
- `trade`
- `quote`
- `depth`
- `ticker`
- `option_quote`
- `option_oi`
- `index`

Validate symbol/contract identifiers against known instrument metadata before subscribing. Do not copy arbitrary user strings into upstream subscription messages.

## Quality gate
Reject or quarantine events when:
- event timestamp is impossible/outside configured clock-skew bounds;
- sequence goes backwards for a source stream;
- instrument identity is unknown;
- bid/ask is structurally invalid;
- negative volume/value appears without an explicit provider convention;
- an event is an exact duplicate;
- upstream is unreachable and only an old snapshot exists.

For stale data:
1. preserve the last observation;
2. mark `data_quality.status=stale`;
3. preserve the original `event_time`;
4. never emit it as a fresh event;
5. keep the failure reason in telemetry, not inside secret-bearing errors.

## Collector architecture
```text
Source Adapter
   -> Instrument Registry
   -> Collector
   -> Normalizer
   -> Quality Gate
   -> Deduplicator / Sequencer
   -> RealtimeHub
      -> REST
      -> WebSocket
      -> SSE
      -> Redis Streams
      -> Historical Recorder
   -> Bobby Hosh
```

Current BRS `AllSymbols` is a snapshot/poll adapter. It must remain the fallback adapter until a verified exchange-native stream is available.

## Redis and persistence standard
For multi-process/multi-instance deployment:
- Redis Streams is the canonical internal event bus;
- use a stable stream key per market/asset class where useful;
- retain event IDs and source sequence;
- consumers must be idempotent;
- persist normalized events/snapshots for replay and backtesting;
- partition historical storage by trading date and asset class.

Do not change the public REST/WebSocket/SSE schema when replacing the in-process hub with Redis.

## Bobby Hosh integration
Realtime data is evidence, not an automatic trade instruction. Downstream signals must include:
- event time
- freshness
- source confidence
- field completeness
- calculation provenance
- regime context when available

Decision Engine must never use a future event relative to the decision timestamp. Historical replay must reproduce the same event ordering available at that time.

## Decision-facing realtime signals
- market breadth/index regime
- volume/value acceleration
- money-flow direction
- order-book imbalance
- queue pressure
- equity/option divergence
- OI accumulation/unwinding
- IV expansion/compression
- abnormal call/put activity
- underlying momentum vs option premium response
- spread/liquidity deterioration
- stale-feed and source-disagreement alerts

## API contract
REST:
- `GET /api/v1/market/realtime`
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

Streaming:
- `WS /ws/market`
- `GET /api/v1/stream/market`

## Security
- Never hard-code API keys, tokens, cookies, or credentials.
- Read credentials from environment variables or the project's secret manager.
- Never print secrets in logs, JSON, exceptions, commits, or telemetry.

## Testing standard
At minimum:
- schema validation
- event-time ordering
- duplicate suppression
- sequence handling
- stale detection
- clock skew
- reconnect/backoff
- heartbeat
- missing-field handling
- option/underlying mapping
- IV/Greeks fixtures
- WebSocket/SSE fan-out
- slow-client backpressure
- Redis idempotency
- historical replay
- no-look-ahead bias
- source disagreement

## Implementation roadmap
Phase 1: normalized REST JSON + source adapters. **Complete.**
Phase 2: bounded WebSocket/SSE + quality gate. **Complete.**
Phase 3: Redis Streams + historical recorder + replay/backtest. **Next.**
Phase 4: verified upstream native streaming adapters + anomaly detection + Decision Engine integration.
