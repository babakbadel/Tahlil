# Realtime Market JSON API

## Run

```bash
pip install -r requirements-realtime.txt
export BRS_API_KEY='...'
uvicorn realtime_api:app --host 0.0.0.0 --port 8000
```

Optional polling interval:

```bash
export BRS_POLL_SECONDS=5
```

## Endpoints

- `GET /health`
- `GET /api/v1/market/realtime`
- `GET /api/v1/equity/market`
- `GET /api/v1/equity/symbol/{symbol}`
- `GET /api/v1/options/market`
- `GET /api/v1/options/chain/{underlying}`

The upstream BRS `AllSymbols` feed is snapshot/poll based. This service therefore provides near-real-time polling rather than claiming an exchange-native tick WebSocket. When an upstream streaming feed becomes available, the collector interface can be replaced without changing the JSON contract.

## Security

`BRS_API_KEY` is read from the environment and is never returned by the API or logged.

## Data quality

Every response includes `event_time`, `received_at`, and `data_quality`. If polling fails after a successful snapshot, the retained snapshot is marked `stale` rather than presented as a new event.
