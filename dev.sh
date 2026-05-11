#!/usr/bin/env bash
# EdgarWolf local dev launcher
# Usage: ./dev.sh [standard|pro|pro_plus]
# Starts the FastAPI server on :8000 and opens the browser with the specified tier.

set -e

TIER="${1:-pro}"
PORT=8000
URL="http://127.0.0.1:${PORT}/?dev_tier=${TIER}"

# Kill anything already on the port
lsof -ti:${PORT} | xargs kill -9 2>/dev/null && echo "Cleared port ${PORT}" || true

# Start server in background
cd "$(dirname "$0")/edgar-api"
.venv/bin/uvicorn main:app --reload --port ${PORT} &>/tmp/edgarwolf-dev.log &
SERVER_PID=$!
echo "Server PID: ${SERVER_PID} (logs: /tmp/edgarwolf-dev.log)"

# Wait until healthy
echo -n "Waiting for server"
for i in $(seq 1 15); do
  sleep 1
  if curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    echo " ready."
    break
  fi
  echo -n "."
done

echo "Opening ${URL}"
open "${URL}"
