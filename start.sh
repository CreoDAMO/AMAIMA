#!/bin/bash
set -e

echo "Starting AMAIMA Backend..."
cd /app/amaima/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 &
BACKEND_PID=$!

echo "Waiting for backend to start..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend is ready!"
    break
  fi
  sleep 1
done

echo "Starting AMAIMA Frontend..."
cd /app/amaima/frontend
exec npx next start -p ${PORT:-5000} -H 0.0.0.0
