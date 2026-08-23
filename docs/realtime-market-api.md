# Realtime Market JSON API

## Run

```bash
pip install -r requirements-realtime.txt
export BRS_API_KEY='...'
uvicorn realtime_api:app --host 0.0.0.0 --port 8000
```

Optional polling interval and stream queue size:

```bash
export BRS_POLL_SECONDS=5
export BRS_STREAM_QUEUE=2
```

## REST endpoints

- `GET /health`
- `GET /api/v1/market/realtime`
- `GET /api/v1/equity/market`
- `GET /api/v1/equity/symbol/{symbol}`
- `GET /api/v1/options/market`
- `GET /api/v1/options/chain/{underlying}`

## Streaming endpoints

### WebSocket

```text
ws://HOST:8000/ws/market
```

The server sends the latest snapshot immediately when available, then every newly collected snapshot. A bounded per-client queue prevents a slow client from blocking the collector; the oldest pending event is dropped when the queue is full.

### Server-Sent Events

```text
GET http://HOST:8000/api/v1/stream/market
```

The SSE stream sends the latest snapshot first, then `market` events. A 20-second heartbeat keeps intermediaries from closing an idle connection.

## Important data-source limitation

The upstream BRS `AllSymbols` endpoint is snapshot/poll based. Therefore WebSocket/SSE here is **application-level streaming of newly collected snapshots**, not an exchange-native tick feed. With the current adapter, `BRS_POLL_SECONDS` controls the upstream polling cadence. When a true exchange/provider streaming source is available, only the collector/source adapter needs to change; the JSON, WebSocket and SSE contracts remain stable.

## Architecture

`BRS snapshot -> Collector -> Normalizer -> RealtimeHub -> REST / WebSocket / SSE -> Bobby Hosh`

The `RealtimeHub` uses bounded in-memory queues and fan-out. For multi-process or multi-instance deployment, replace the in-process hub with Redis Pub/Sub or Streams while keeping the external API contract unchanged.

## Security

`BRS_API_KEY` is read from the environment and is never returned by the API or logged.

## Data quality

Every response includes `event_time`, `received_at`, and `data_quality`. If polling fails after a successful snapshot, the retained snapshot is marked `stale` rather than presented as a new event.
