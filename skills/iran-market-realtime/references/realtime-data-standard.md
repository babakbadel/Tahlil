# Realtime Market Data Standard

## Goal
Define the operational standard used by `iran-market-realtime` for Bursa and listed-options data before it reaches Bobby Hosh.

## 1. Source hierarchy
1. TSETMC / official exchange data
2. SEO / TSE / IFB / official derivatives data
3. BRS API / approved secondary provider
4. Other secondary sources
5. Calculated analytics

Source facts must never be silently replaced by calculated values.

## 2. Identity
Use stable instrument/contract identifiers whenever available. TSETMC uses `insCode` as a primary instrument identifier; Persian display symbols are lookup/display fields, not reliable primary keys. citeturn0search1

For options always preserve:
- contract_id
- symbol
- underlying_id
- underlying_symbol
- option_type
- strike
- expiry

## 3. Event time
Store both:
- `event_time`: when the market/source says the event happened
- `received_at`: when our collector received it

For TSETMC, normalize source date/time fields such as `dEven` and `hEven` into `event_time`. citeturn0search13

Never use `received_at` as a substitute for a known source event time.

## 4. Freshness
Required fields:
- `status`
- `age_ms`
- `upstream_reachable`
- `field_completeness`
- `clock_skew_ms`

A polling snapshot pushed over WebSocket/SSE remains a snapshot stream. It is not exchange-native tick data. Native tick status requires a verified upstream streaming feed.

## 5. Event types
Use explicit event types:
- snapshot
- trade
- quote
- depth
- index
- flow
- option_quote
- option_oi

This prevents a full snapshot from being mistaken for a single trade event.

## 6. Streaming
When an upstream native WebSocket exists, prefer it to polling. Persistent connections must implement reconnect/backoff, heartbeat handling, subscription validation, duplicate suppression, and sequence handling. Existing market-data skills follow this pattern. citeturn0search3turn0search10

Our API layer provides:
- WebSocket `/ws/market`
- SSE `/api/v1/stream/market`

Both must preserve the same normalized event contract as REST.

## 7. Data quality
Never invent missing fields. Use `null` plus provenance/reason where necessary.

Quarantine events with impossible timestamps, backwards sequence numbers, invalid instrument identity, malformed market depth, or exact duplicate event IDs.

If the source is unavailable, preserve the last observation but mark it stale and retain its original event time.

## 8. Options
For every option:
- resolve the underlying;
- distinguish call vs put;
- preserve strike and expiry;
- separate exchange/provider OI from calculated OI change;
- label IV/Greeks as source-provided or model-derived;
- retain pricing-model assumptions for calculated Greeks.

## 9. Bobby Hosh handoff
Every downstream observation should carry enough provenance to answer:
- What instrument was observed?
- What source produced it?
- When did it occur?
- When did we receive it?
- Is it fresh?
- Was it calculated?
- What inputs/model produced the calculation?

Decision Engine must consume events only in event-time order and must not access future observations during replay/backtest.
