# ─────────────────────────────────────────────────────────────────────────────
# AMAIMA — Production Dockerfile (VPS / self-hosted)
# Base: python:3.10-slim-bookworm
#   • python:3.10 required for the TenSEAL cp310 pre-built wheel on PyPI
#   • tenseal 0.3.14 was yanked; pin to >=0.3.15
#   • g++ and cmake are required to compile TenSEAL C++ extensions
#   • Next.js 16 peaks at ~500MB during npm run build — NODE_OPTIONS caps GC
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Python dependency builder ───────────────────────────────────────
FROM python:3.10-slim-bookworm AS python-builder

WORKDIR /build

# System deps: g++ + cmake for TenSEAL; curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    cmake \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY amaima/backend/requirements.txt .

# Install standard deps first, then tenseal separately for visible failure output
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user -v tenseal>=0.3.15

# ── Stage 2: Node.js frontend builder ────────────────────────────────────────
FROM node:20-slim AS node-builder

WORKDIR /frontend

COPY amaima/frontend/package*.json ./
RUN npm ci --prefer-offline

COPY amaima/frontend/ ./

# Limit GC pressure during the build — Next.js 16 peaks at ~500MB
ENV NODE_OPTIONS="--max-old-space-size=256"

RUN npm run build

# ── Stage 3: Production runtime ───────────────────────────────────────────────
FROM python:3.10-slim-bookworm AS runtime

WORKDIR /app

# Runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    cmake \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=python-builder /root/.local /root/.local
ENV PATH="/root/.local/bin:$PATH"

# Copy backend
COPY amaima/backend/ ./backend/

# Copy built frontend + node_modules for next start
COPY --from=node-builder /frontend/.next ./frontend/.next
COPY --from=node-builder /frontend/node_modules ./frontend/node_modules
COPY --from=node-builder /frontend/package.json ./frontend/package.json
COPY --from=node-builder /frontend/next.config.js ./frontend/next.config.js
COPY --from=node-builder /frontend/public ./frontend/public

# Copy start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# ── Environment defaults ──────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AMAIMA_EXECUTION_MODE=execution-enabled \
    FHE_ENABLED=true \
    SEAL_THREADS=4 \
    PORT=10000 \
    BACKEND_URL=http://localhost:8000 \
    # TenSEAL alias for NVIDIA key
    NVIDIA_NIM_API_KEY=${NVIDIA_API_KEY}

# Cap Next.js runtime heap — keeps total memory under 1GB on a 2GB VPS
ENV NODE_OPTIONS="--max-old-space-size=400"

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["/app/start.sh"]
