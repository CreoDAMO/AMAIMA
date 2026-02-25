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

FROM python:3.11-slim-bookworm AS base

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        # Required for psycopg2-binary
        libpq-dev \
        # Required for httpx / cryptography native extensions
        gcc \
        # Required if Pillow is used for image format conversion
        libjpeg-dev \
        libpng-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Copy source ───────────────────────────────────────────────────────────────
# Copy before any ARG/ENV declarations so layer is cache-busted on code changes
COPY . .

# ── Python dependencies ───────────────────────────────────────────────────────
RUN cd amaima/backend && pip install --no-cache-dir -r requirements.txt

# ── TenSEAL for FHE subsystem ────────────────────────────────────────────────
# Installed unconditionally — FHE is a primary platform feature.
# The generic pip wheel has no AVX-512 acceleration; for full performance
# use the 3-stage backend Dockerfile which compiles against Intel HEXL + SEAL.
RUN pip install --no-cache-dir tenseal

# ── Build-time secrets (not baked into the image layer) ──────────────────────
# These are only used during `npm run build` for SSR/static generation.
# Runtime secrets should be injected via `docker run -e` or your platform's
# secret manager — not hard-coded here.
ARG DATABASE_URL=""
ARG STRIPE_SECRET_KEY=""
ARG NVIDIA_API_KEY=""

ENV DATABASE_URL=${DATABASE_URL}
ENV STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
ENV NVIDIA_API_KEY=${NVIDIA_API_KEY}
# Alias — audio_service.py and image_service.py check both names
ENV NVIDIA_NIM_API_KEY=${NVIDIA_API_KEY}

# ── Frontend build ────────────────────────────────────────────────────────────
RUN cd amaima/frontend && npm install && npm run build

# ── Runtime environment ───────────────────────────────────────────────────────
# PORT: frontend listens on 10000 (matches Render's default and Next.js config)
# BACKEND_URL: internal backend address for Next.js API proxy
# AMAIMA_EXECUTION_MODE: MUST be execution-enabled — no simulation fallback
# FHE_ENABLED: controls whether fhe_startup() attempts TenSEAL pool warm-up
# SEAL_THREADS / OMP_NUM_THREADS: SEAL NTT parallelism (no-op if TenSEAL absent)
ENV PORT=10000
ENV BACKEND_URL=http://localhost:8000
ENV AMAIMA_EXECUTION_MODE=execution-enabled
ENV FHE_ENABLED=true
ENV SEAL_THREADS=4
ENV OMP_NUM_THREADS=4

# ── start.sh ─────────────────────────────────────────────────────────────────
# Already copied with COPY . . above, but chmod must happen after COPY
RUN chmod +x /app/start.sh

# ── Ports ─────────────────────────────────────────────────────────────────────
# 10000 — Next.js frontend
#  8000 — FastAPI backend
EXPOSE 10000 8000

# ── Healthcheck ───────────────────────────────────────────────────────────────
# start-period=60s: gives FHE pool warm-up and DB init time before Render/
# Docker considers the container unhealthy and restarts it.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["/app/start.sh"]
