#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# AMAIMA start.sh — Process supervisor
#
# 1. Starts FastAPI backend (uvicorn) on port 8000
# 2. Waits up to 60s for backend to be healthy before starting frontend
# 3. Starts Next.js frontend on port 10000
# 4. Monitors both processes — if either exits, kills the other and exits
#    the container so Docker/compose restart policy can take effect
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Memory limits ─────────────────────────────────────────────────────────────
# Cap Next.js runtime heap to keep total memory under 2GB on a 2GB VPS.
# Raise to 600 if you're on a 4GB+ instance.
export NODE_OPTIONS="--max-old-space-size=400"

# ── Startup log ──────────────────────────────────────────────────────────────
echo "[start.sh] AMAIMA starting — $(date)"
echo "[start.sh] FHE_ENABLED=${FHE_ENABLED:-false}"
echo "[start.sh] AMAIMA_EXECUTION_MODE=${AMAIMA_EXECUTION_MODE:-not set}"
echo "[start.sh] SEAL_THREADS=${SEAL_THREADS:-4}"

# ── Start FastAPI backend ─────────────────────────────────────────────────────
echo "[start.sh] Starting FastAPI backend on port 8000..."
cd /app/backend

python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level info \
    --no-access-log &

BACKEND_PID=$!
echo "[start.sh] Backend PID: ${BACKEND_PID}"

# ── Wait for backend to be healthy ───────────────────────────────────────────
echo "[start.sh] Waiting for backend health check..."
WAITED=0
MAX_WAIT=60

until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "[start.sh] ERROR: Backend did not become healthy within ${MAX_WAIT}s"
        echo "[start.sh] Check logs above for Python/TenSEAL startup errors"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo "[start.sh] Still waiting... (${WAITED}s/${MAX_WAIT}s)"
done

echo "[start.sh] Backend healthy after ${WAITED}s"

# ── Start Next.js frontend ────────────────────────────────────────────────────
echo "[start.sh] Starting Next.js frontend on port ${PORT:-10000}..."
cd /app/frontend

npx next start \
    --port "${PORT:-10000}" \
    --hostname "0.0.0.0" &

FRONTEND_PID=$!
echo "[start.sh] Frontend PID: ${FRONTEND_PID}"

# ── Process supervision ───────────────────────────────────────────────────────
# If either process exits, kill the other and exit the container.
# Docker's restart policy will handle restarting the container.

cleanup() {
    echo "[start.sh] Shutting down..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
    wait $FRONTEND_PID 2>/dev/null || true
    echo "[start.sh] Shutdown complete"
    exit 0
}

trap cleanup SIGTERM SIGINT

# Wait for either process to exit
while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "[start.sh] ERROR: Backend process died (PID ${BACKEND_PID})"
        kill $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "[start.sh] ERROR: Frontend process died (PID ${FRONTEND_PID})"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 5
done
