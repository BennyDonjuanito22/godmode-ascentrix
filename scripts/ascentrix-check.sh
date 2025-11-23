#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo "=== Docker containers ==="
docker ps --format '  - {{.Names}} ({{.Status}})'

echo
echo "=== API health ==="
if curl -fsS http://127.0.0.1:5051/health >/tmp/ascentrix_health.json 2>/tmp/ascentrix_health.err; then
  cat /tmp/ascentrix_health.json
  echo
  echo "✅ Ascentrix API responding."
else
  echo "❌ API health check failed:"
  cat /tmp/ascentrix_health.err || true
  echo
fi
