#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${MINDBRIDGE_BASE_URL:-http://localhost:8000}"
FRONTEND_URL="${MINDBRIDGE_FRONTEND_URL:-http://localhost:3000}"
wait_for() {
  local url="$1"; local attempts="${2:-30}"
  for _ in $(seq 1 "$attempts"); do curl -fsS "$url" >/dev/null 2>&1 && return 0; sleep 2; done
  echo "Timed out waiting for $url" >&2; return 1
}
wait_for "$BASE_URL/livez"
health="$(curl -fsS "$BASE_URL/health")"
echo "$health" | grep -q '"database":"ok"'
echo "$health" | grep -q '"redis":"ok"'
wait_for "$FRONTEND_URL/"
curl -fsS "$BASE_URL/v1/system/readiness" >/tmp/mindbridge-readiness.json || true
printf 'MindBridge V11 staging smoke checks passed
'
