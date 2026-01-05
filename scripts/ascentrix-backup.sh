#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
STAMP="$(date +'%Y%m%d_%H%M%S')"
DEST="backups/$STAMP"
mkdir -p "$DEST"
API_PORT="${GODMODE_API_PORT_HOST:-5051}"
API_BASE="${GODMODE_API_URL:-http://127.0.0.1:${API_PORT}}"

echo "=== Creating Ascentrix backup: $DEST ==="

# API state
curl -fsS "${API_BASE}/health" > "$DEST/api_health.json" || true

# Events snapshot
curl -fsS "${API_BASE}/events" > "$DEST/events.json" || true

# HUD snapshot
cp hud/index.html "$DEST/index.html" || true

# Container list
docker ps --format '{{.Names}} ({{.Status}})' > "$DEST/containers.txt"

# Save docker-compose config
cp docker-compose.yml "$DEST/docker-compose.yml" || true

echo "=== Backup complete ==="
echo "Backup saved to: $DEST"
