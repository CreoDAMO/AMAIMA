#!/bin/bash
set -e

echo "================================================"
echo "  AMAIMA - Starting Full-Stack Application"
echo "================================================"

echo "[1/3] Starting FastAPI backend on port 8000..."
cd /app/amaima/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 &
BACKEND_PID=$!

echo "[2/3] Waiting for backend to be ready..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "  Backend is ready! (took ${i}s)"
    break
  fi
  if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "  ERROR: Backend process died. Check logs above."
    exit 1
  fi
  sleep 1
done

if ! curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  echo "  WARNING: Backend did not respond to health check within 30s."
  echo "  Continuing anyway (it may still be initializing)..."
fi

echo "[3/3] Starting Next.js frontend on port ${PORT:-5000}..."
cd /app/amaima/frontend
exec npx next start -p ${PORT:-5000} -H 0.0.0.0
