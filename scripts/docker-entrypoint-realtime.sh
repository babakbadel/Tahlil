#!/bin/sh
set -eu

: "${BRS_API_KEY:?BRS_API_KEY is required}"

exec python scripts/run_realtime_api.py
