#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
API_PORT="${GODMODE_API_PORT_HOST:-5051}"
API_BASE="${GODMODE_API_URL:-http://127.0.0.1:${API_PORT}}"

echo "=== Docker containers ==="
docker ps --format '  - {{.Names}} ({{.Status}})'

echo
echo "=== API health ==="
if curl -fsS "${API_BASE}/health" >/tmp/ascentrix_health.json 2>/tmp/ascentrix_health.err; then
  cat /tmp/ascentrix_health.json
  echo
  echo "✅ Ascentrix API responding."
else
  echo "❌ API health check failed:"
  cat /tmp/ascentrix_health.err || true
  echo
fi
