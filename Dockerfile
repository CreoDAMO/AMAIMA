# =============================================================================
# AMAIMA — Production Dockerfile
#
# Single-stage build for standard deployment (no FHE hardware acceleration).
# For the 3-stage AVX-512 build with Intel HEXL + Microsoft SEAL compiled from
# source, see docs/fhe-dockerfile.md (in progress).
#
# Build:
#   docker build \
#     --build-arg NVIDIA_API_KEY=nvapi-... \
#     --build-arg DATABASE_URL=postgresql://... \
#     -t amaima:latest .
#
# Run:
#   docker run -p 10000:10000 -p 8000:8000 \
#     -e AMAIMA_EXECUTION_MODE=execution-enabled \
#     amaima:latest
# =============================================================================

# ── Python 3.10 — required for TenSEAL pre-built wheels ─────────────────────
# TenSEAL 0.3.14 ships cp310 wheels for linux/amd64 on PyPI.
# Python 3.11+ has no pre-built wheel — pip falls back to source compilation
# which requires a full C++ toolchain and takes 10-15 min, exceeding Render's
# build timeout. Pinning to 3.10 guarantees a fast wheel install (~30 seconds).
# FastAPI, uvicorn, SQLAlchemy, httpx and all other deps support Python 3.10.
FROM python:3.10-slim-bookworm AS base

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        libpq-dev \
        gcc \
        g++ \
        cmake \
        libjpeg-dev \
        libpng-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Copy source ───────────────────────────────────────────────────────────────
COPY . .

# ── Python dependencies (all except tenseal) ──────────────────────────────────
# tenseal installed separately so failures are isolated and visible in build log
RUN cd amaima/backend && grep -v "tenseal" requirements.txt | pip install --no-cache-dir -r /dev/stdin

# ── TenSEAL — FHE is a primary platform feature ───────────────────────────────
# Pinned to 0.3.14 which has a cp310-cp310-manylinux_x86_64 wheel on PyPI.
# With Python 3.10 this resolves and installs in ~30s with no source compilation.
RUN pip install --no-cache-dir -v "tenseal==0.3.14"

# ── Build-time secrets ────────────────────────────────────────────────────────
ARG DATABASE_URL=""
ARG STRIPE_SECRET_KEY=""
ARG NVIDIA_API_KEY=""

ENV DATABASE_URL=${DATABASE_URL}
ENV STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
ENV NVIDIA_API_KEY=${NVIDIA_API_KEY}
ENV NVIDIA_NIM_API_KEY=${NVIDIA_API_KEY}

# ── Frontend build ────────────────────────────────────────────────────────────
# Limit heap to 384MB during build to avoid OOM on Render's 512MB starter instance
ENV NODE_OPTIONS="--max-old-space-size=384"
RUN cd amaima/frontend && npm install && npm run build

# ── Runtime environment ───────────────────────────────────────────────────────
ENV PORT=10000
ENV BACKEND_URL=http://localhost:8000
ENV AMAIMA_EXECUTION_MODE=execution-enabled
ENV FHE_ENABLED=true
ENV SEAL_THREADS=2
ENV OMP_NUM_THREADS=2
# Reset NODE_OPTIONS — start.sh sets the correct runtime heap limit
ENV NODE_OPTIONS=""

# ── start.sh ──────────────────────────────────────────────────────────────────
RUN chmod +x /app/start.sh

# ── Ports ─────────────────────────────────────────────────────────────────────
EXPOSE 10000 8000

# ── Healthcheck ───────────────────────────────────────────────────────────────
# 90s start-period: FHE pool warm + uvicorn startup + DB init on 1 CPU
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["/app/start.sh"]
