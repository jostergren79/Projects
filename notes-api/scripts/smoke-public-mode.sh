#!/usr/bin/env bash

set -euo pipefail

PORT="${PORT:-3001}"
BASE_URL="http://127.0.0.1:${PORT}"

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  echo "PASS: $1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  echo "FAIL: $1"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

http_code() {
  curl -s -o /dev/null -w "%{http_code}" "$1"
}

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

PORT="$PORT" PUBLIC_MODE=true npm run dev >/tmp/notes-public-smoke.log 2>&1 &
SERVER_PID=$!

for _ in {1..30}; do
  if [[ "$(http_code "${BASE_URL}/edgar")" == "200" ]]; then
    break
  fi
  sleep 1
done

[[ "$(http_code "${BASE_URL}/edgar")" == "200" ]] && pass "/edgar reachable" || fail "/edgar should return 200"
[[ "$(http_code "${BASE_URL}/sop")" == "404" ]] && pass "/sop blocked" || fail "/sop should return 404 in PUBLIC_MODE"
[[ "$(http_code "${BASE_URL}/query")" == "404" ]] && pass "/query blocked" || fail "/query should return 404 in PUBLIC_MODE"
[[ "$(http_code "${BASE_URL}/api/sop/forecast")" == "404" ]] && pass "/api/sop/forecast blocked" || fail "/api/sop/forecast should return 404 in PUBLIC_MODE"

POST_NOTES_CODE="$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/notes" -H "Content-Type: application/json" -d '{"title":"x","content":"y"}')"
[[ "$POST_NOTES_CODE" == "404" ]] && pass "notes write disabled" || fail "POST /notes should return 404 in PUBLIC_MODE"

POST_SQL_CODE="$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/sop/query" -H "Content-Type: application/json" -d '{"sql":"select 1"}')"
[[ "$POST_SQL_CODE" == "404" ]] && pass "SQL runner disabled" || fail "POST /api/sop/query should return 404 in PUBLIC_MODE"

echo
if [[ "$FAIL_COUNT" -eq 0 ]]; then
  echo "All checks passed (${PASS_COUNT} PASS, ${FAIL_COUNT} FAIL)"
  exit 0
else
  echo "Smoke checks completed with failures (${PASS_COUNT} PASS, ${FAIL_COUNT} FAIL)"
  echo "Logs: /tmp/notes-public-smoke.log"
  exit 1
fi
