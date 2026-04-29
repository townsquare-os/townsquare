#!/usr/bin/env bash
set -euo pipefail

# townsquare container entrypoint.
# 1. Waits for the database to be ready.
# 2. Runs init-db (idempotent — creates tables on first run, no-op after).
# 3. Starts uvicorn.

echo "[townsquare] initialising database..."
townsquare init-db || {
    echo "[townsquare] init-db failed — see error above. Likely DB not ready or DB_URL misconfigured."
    exit 1
}

echo "[townsquare] starting server on 0.0.0.0:8000"
exec uvicorn townsquare.web.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --proxy-headers \
    --forwarded-allow-ips='*'
