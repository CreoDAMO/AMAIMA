#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# AMAIMA — deploy.sh
#
# Run this script on the VPS to pull latest code and redeploy.
# Zero-downtime: builds new image before stopping the old container.
#
# Usage:
#   ./deploy.sh              # deploy latest from current branch
#   ./deploy.sh --no-cache   # force full rebuild (clears Docker layer cache)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NO_CACHE=""

if [[ "${1:-}" == "--no-cache" ]]; then
    NO_CACHE="--no-cache"
    echo "[deploy] Full rebuild requested (--no-cache)"
fi

echo "[deploy] Starting deployment — $(date)"
echo "[deploy] Directory: ${INSTALL_DIR}"

cd "$INSTALL_DIR"

# ── Pull latest code ──────────────────────────────────────────────────────────
echo "[deploy] Pulling latest code..."
git fetch origin
git pull origin "$(git rev-parse --abbrev-ref HEAD)"
echo "[deploy] Current commit: $(git rev-parse --short HEAD)"

# ── Build new image ───────────────────────────────────────────────────────────
echo "[deploy] Building new Docker image..."
docker compose build $NO_CACHE

# ── Restart with new image ────────────────────────────────────────────────────
echo "[deploy] Restarting services..."
docker compose up -d

# ── Wait for health check ─────────────────────────────────────────────────────
echo "[deploy] Waiting for health check..."
WAITED=0
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    if [ $WAITED -ge 120 ]; then
        echo "[deploy] ERROR: Service did not become healthy after 120s"
        echo "[deploy] Check logs: docker compose logs --tail=50"
        exit 1
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    echo "[deploy] Waiting... (${WAITED}s)"
done

echo "[deploy] Deployment successful — service healthy after ${WAITED}s"

# ── Prune old images ──────────────────────────────────────────────────────────
echo "[deploy] Pruning old images..."
docker image prune -f

echo "[deploy] Done — $(date)"
