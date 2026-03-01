# Deploying AMAIMA On It's Own VPS

## The key facts from the docs:
- Python 3.10 (tenseal cp310 wheel)
- Frontend port 10000, backend port 8000
- 2GB minimum, 4GB recommended (Hetzner CX22 = 4GB for ~$5/mo)
- Unconditional tenseal install with g++ and cmake
- NODE_OPTIONS heap management
- Process supervision in start.sh
- Caddy for SSL (simpler than nginx+certbot)

Nine files — here's what each one does and how they fit together:

**`setup.sh`** — Run this once on a fresh Ubuntu 24.04 VPS as root. It installs Docker, installs Caddy, clones the repo, auto-generates strong secrets for `API_SECRET_KEY`, `JWT_SECRET_KEY`, and `DB_PASSWORD`, writes `.env`, configures the firewall, and creates a systemd service so AMAIMA restarts on reboot. After it finishes you only need to add your `NVIDIA_API_KEY` and run `docker compose up -d --build`.

**`Dockerfile`** — Three-stage build: Python deps builder → Node.js builder → slim runtime. Uses `python:3.10-slim-bookworm` (required for the pre-built TenSEAL cp310 wheel), installs `g++` and `cmake` for the C++ extension, separates `pip install tenseal` into its own `RUN` step so any failure is visible rather than silently skipped, and caps `NODE_OPTIONS=--max-old-space-size=256` during the Next.js build stage to prevent OOM.

**`docker-compose.yml`** — PostgreSQL + AMAIMA stack. Postgres stays on the internal network only (port 5432 never exposed to host). `DATABASE_URL` is constructed from `DB_PASSWORD` automatically. Memory limits are set (`3G` limit, `1G` reservation) to keep the container within VPS budget. The `start_period: 90s` healthcheck gives the FHE context pool time to warm before Docker considers the container unhealthy.

**`.env.example`** — Copy to `.env`, set `NVIDIA_API_KEY`. Every other secret has generation instructions (`openssl rand -hex 32`). Stripe keys are marked optional.

**`start.sh`** — Starts FastAPI first, polls `localhost:8000/health` up to 60s before launching Next.js, then runs a supervision loop that kills the other process and exits cleanly if either one dies. Docker's `restart: unless-stopped` then handles bringing it back up.

**`next.config.js`** — `swcMinify: false` (Terser is lighter on heap), `productionBrowserSourceMaps: false`, webpack `parallelism: 1`, API proxy rewrites for all `/v1/*` and WebSocket `/ws/*` traffic, security headers, and `outputFileTracingRoot` to silence the duplicate lockfile warning.

**`Caddyfile`** — Copy to `/etc/caddy/Caddyfile`, replace `amaima.live` with your domain. Caddy provisions and auto-renews a Let's Encrypt cert with zero config. The `response_header_timeout: 300s` handles Cosmos Predict video generation which can hold connections for up to 4 minutes.

**`deploy.sh`** — For ongoing updates: `git pull` → `docker compose build` → `docker compose up -d` → health-check verification → `docker image prune`. Pass `--no-cache` for a full rebuild after Dockerfile changes.

**`VPS_DEPLOYMENT.md`** — Complete reference covering provider comparison (Hetzner CX22 at $5/mo is the recommendation), manual setup steps, all env vars, SSL verification, monitoring commands, and a full troubleshooting section for every failure mode encountered across the 6 sessions.
