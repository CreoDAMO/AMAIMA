#!/bin/bash
# =============================================================================
# AMAIMA — Full-Stack Startup Script
# Starts FastAPI backend (port 8000) then Next.js frontend (port 10000)
# =============================================================================

set -e

echo "================================================"
echo "  AMAIMA - Starting Full-Stack Application"
echo "================================================"

# ── Backend ───────────────────────────────────────────────────────────────────
echo "[1/3] Starting FastAPI backend on port 8000..."

# Render sets WEB_CONCURRENCY=1 on starter instances (1 CPU).
# On larger plans increase UVICORN_WORKERS in environment variables.
WORKERS=${UVICORN_WORKERS:-${WEB_CONCURRENCY:-1}}

cd /app/amaima/backend
python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "$WORKERS" \
    --loop uvloop \
    --log-level info &

BACKEND_PID=$!

# ── Wait for backend ──────────────────────────────────────────────────────────
echo "[2/3] Waiting for backend to be ready..."
MAX_WAIT=60
WAITED=0
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "ERROR: Backend failed to start within ${MAX_WAIT}s"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done
echo "  Backend is ready! (took ${WAITED}s)"

# ── Frontend ──────────────────────────────────────────────────────────────────
echo "[3/3] Starting Next.js frontend on port ${PORT:-10000}..."

cd /app/amaima/frontend

# Limit Next.js heap to 400MB to prevent OOM kills on Render's 512MB instance.
# The remaining ~112MB covers the OS, uvicorn workers, and FHE context pool.
# Increase to 600+ if you upgrade to a Standard (1GB) plan.
export NODE_OPTIONS="--max-old-space-size=400"

npm start -- -p "${PORT:-10000}" -H 0.0.0.0 &
FRONTEND_PID=$!

# ── Process supervision ───────────────────────────────────────────────────────
# If either process dies, kill the other and exit so Render restarts the container.
wait_and_supervise() {
    while true; do
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            echo "ERROR: Backend process died — restarting container"
            kill $FRONTEND_PID 2>/dev/null
            exit 1
        fi
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "ERROR: Frontend process died — restarting container"
            kill $BACKEND_PID 2>/dev/null
            exit 1
        fi
        sleep 5
    done
}

# Trap signals so both processes are stopped cleanly on container shutdown
trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' SIGTERM SIGINT

wait_and_supervise
