# AMAIMA Full-Stack Deployment Guide

Deploy the entire AMAIMA application (Next.js frontend + FastAPI backend + FHE engine) as a single unit.

---

## Table of Contents

1. [How It Works](#how-it-works)
2. [Resource Requirements](#resource-requirements)
3. [Environment Variables](#environment-variables)
4. [Deployment Options](#deployment-options)
   - [Railway (Recommended)](#1-railway-recommended)
   - [Fly.io (Best for Global Performance)](#2-flyio-best-for-global-performance)
   - [Hetzner VPS + Docker Compose (Best Value)](#3-hetzner-vps--docker-compose-best-value)
   - [DigitalOcean App Platform](#4-digitalocean-app-platform)
   - [Render (Standard Plan+)](#5-render-standard-plan)
   - [Replit Reserved VM](#6-replit-reserved-vm)
   - [Google Cloud Run](#7-google-cloud-run)
   - [AWS](#8-aws)
   - [Azure Container Apps](#9-azure-container-apps)
   - [Heroku](#10-heroku)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Security Checklist](#security-checklist)
7. [Troubleshooting](#troubleshooting)
8. [Platform Comparison](#platform-comparison)

---

## How It Works

```
┌──────────────────────────────────────────────────────────┐
│                      Your Server                          │
│                                                           │
│  ┌──────────────────────┐   ┌───────────────────────────┐ │
│  │  Next.js Frontend    │──▶│  FastAPI Backend           │ │
│  │  (Port 10000)        │   │  (Port 8000)               │ │
│  │                      │   │                            │ │
│  │  - Web UI            │   │  - 7-domain Smart Router   │ │
│  │  - FHE Dashboard     │   │  - NVIDIA NIM client       │ │
│  │  - Agent Builder     │   │  - Multi-agent crews       │ │
│  │  - Billing/Analytics │   │  - FHE engine (TenSEAL)    │ │
│  │  - API proxy routes  │   │  - Audio/Image/Video       │ │
│  │  - Stripe checkout   │   │  - Biology/Robotics/Vision │ │
│  └──────────────────────┘   └───────────────────────────┘ │
│           │                            │                   │
│           │  BACKEND_URL=              │                   │
│           │  http://localhost:8000     │                   │
│           ▼                            ▼                   │
│      Users see UI               Calls NVIDIA NIM API       │
│                                        │                   │
│                              ┌─────────▼──────────┐        │
│                              │    PostgreSQL        │        │
│                              │  (API keys, usage,  │        │
│                              │   conversations)    │        │
│                              └────────────────────┘        │
└──────────────────────────────────────────────────────────┘
```

- The **frontend** (Next.js) serves the web interface and proxies API requests to the backend via `localhost`
- The **backend** (FastAPI) handles 7-domain AI routing, multi-agent orchestration, FHE operations, and NVIDIA NIM calls
- The **FHE engine** (TenSEAL / Microsoft SEAL) runs homomorphic encryption — requires a native C++ extension
- **PostgreSQL** stores API keys, usage tracking, conversation history, and billing data

---

## Resource Requirements

> ⚠️ These are real-world minimums measured from AMAIMA's actual build and runtime. Platforms below these thresholds will fail with OOM errors during the Docker build or runtime.

| Component | Build RAM Peak | Runtime RAM |
|---|---|---|
| Next.js 16 `npm run build` | ~500MB | — |
| `next start` (frontend) | — | ~300MB |
| FastAPI + 4 uvicorn workers | — | ~400MB |
| FHE context pool (CKKS + BFV) | — | ~150MB |
| TenSEAL C++ extension load | ~200MB | included above |
| OS + buffers | — | ~200MB |
| **Total** | **~500MB build peak** | **~1.05GB runtime** |

**Minimum: 2GB RAM** (build environment and runtime)
**Recommended: 4GB RAM** for headroom during FHE operations and traffic spikes

**Build time:** 5-8 minutes (Next.js compilation + TenSEAL install)
**Platforms with build timeouts under 10 minutes will fail.**

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `NVIDIA_API_KEY` | ✅ Yes | Your NVIDIA NIM API key — get one at https://build.nvidia.com |
| `API_SECRET_KEY` | ✅ Yes | Protects API endpoints. Must be a strong random value in production |
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string: `postgresql://user:pass@host:5432/dbname` |
| `AMAIMA_EXECUTION_MODE` | ✅ Yes | Set to `execution-enabled` — no simulation fallback |
| `FHE_ENABLED` | ✅ Yes | Set to `true` to activate FHE subsystem (TenSEAL) |
| `STRIPE_SECRET_KEY` | Optional | Required for billing/subscription features |
| `STRIPE_WEBHOOK_SECRET` | Optional | Required for Stripe webhook verification |
| `BACKEND_URL` | No | Defaults to `http://localhost:8000` — correct for full-stack deployment |
| `PORT` | No | Frontend port — defaults to `10000` |
| `SEAL_THREADS` | No | SEAL NTT parallelism (default: 2 on 1-CPU, 4 on multi-CPU) |
| `NVIDIA_NIM_API_KEY` | No | Alias for `NVIDIA_API_KEY` — set both for compatibility |

---

## Deployment Options

---

### 1. Railway (Recommended)

Railway is the fastest path from GitHub to a working AMAIMA deployment. It has no build memory limits that affect AMAIMA, no build timeouts, and a one-click PostgreSQL plugin.

**Cost:** ~$10-20/month (usage-based — ~$0.000463/GB-hour of RAM)
**RAM available:** Uncapped during build; set instance size at deploy time (use 2GB+)
**Build timeout:** None
**TenSEAL:** ✅ Installs successfully

#### Steps

1. Sign up at [railway.app](https://railway.app) and connect your GitHub repo

2. Click **New Project → Deploy from GitHub repo** → select your AMAIMA repo

3. Add a PostgreSQL database: click **New → Database → PostgreSQL**

4. Railway auto-detects the root `Dockerfile` and starts building

5. Set environment variables in the Railway dashboard under your service → **Variables**:
   ```
   NVIDIA_API_KEY=nvapi-your-key
   NVIDIA_NIM_API_KEY=nvapi-your-key
   API_SECRET_KEY=your-strong-32-char-secret
   AMAIMA_EXECUTION_MODE=execution-enabled
   FHE_ENABLED=true
   SEAL_THREADS=2
   PORT=10000
   BACKEND_URL=http://localhost:8000
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ```
   Railway auto-fills `DATABASE_URL` from the Postgres plugin using the `${{Postgres.DATABASE_URL}}` reference.

6. Under **Settings → Deploy**, set the instance to at least **2GB RAM**

7. Railway builds and deploys — your URL will be `https://amaima-production.up.railway.app` or a custom domain

#### railway.json (add to repo root)

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "/app/start.sh",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 90,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

---

### 2. Fly.io (Best for Global Performance)

Fly.io runs your Docker container at edge locations worldwide. You control the exact VM size, so TenSEAL and the Next.js build both work without fighting memory limits.

**Cost:** ~$12-18/month for a 2GB shared-CPU machine + Postgres (~$3/mo)
**RAM available:** You choose — set `memory = "2gb"` minimum
**Build timeout:** None (builds run on Fly's infrastructure)
**TenSEAL:** ✅ Installs successfully

#### Steps

1. Install the Fly CLI and log in:
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. Create a Postgres database:
   ```bash
   fly postgres create --name amaima-db --region iad --vm-size shared-cpu-1x --volume-size 10
   ```

3. Create `fly.toml` in the repo root:
   ```toml
   app = "amaima"
   primary_region = "iad"

   [build]
     dockerfile = "Dockerfile"

   [env]
     BACKEND_URL = "http://localhost:8000"
     AMAIMA_EXECUTION_MODE = "execution-enabled"
     FHE_ENABLED = "true"
     SEAL_THREADS = "2"
     PORT = "10000"

   [http_service]
     internal_port = 10000
     force_https = true
     auto_stop_machines = false
     auto_start_machines = true
     min_machines_running = 1

   [[http_service.checks]]
     grace_period = "90s"
     interval = "30s"
     method = "GET"
     path = "/health"
     timeout = "10s"

   [[vm]]
     memory = "2gb"
     cpu_kind = "shared"
     cpus = 1
   ```

   Key settings:
   - `memory = "2gb"` — required; 1GB will OOM during Next.js build
   - `auto_stop_machines = false` and `min_machines_running = 1` — keeps the app always on; the FHE context pool and uvicorn workers must stay resident
   - `grace_period = "90s"` — gives the FHE pool time to warm up before health checks start

4. Attach the database and set secrets:
   ```bash
   fly postgres attach amaima-db
   fly secrets set NVIDIA_API_KEY=nvapi-your-key
   fly secrets set NVIDIA_NIM_API_KEY=nvapi-your-key
   fly secrets set API_SECRET_KEY=your-strong-secret
   ```

5. Deploy:
   ```bash
   fly deploy
   ```

6. Your URL: `https://amaima.fly.dev` (or your custom domain via `fly certs add amaima.live`)

#### Scaling to multiple regions later

```bash
fly regions add lhr syd  # Add London + Sydney
fly scale count 3        # 3 instances across regions
```

---

### 3. Hetzner VPS + Docker Compose (Best Value)

The highest RAM-per-dollar option. A Hetzner CX22 gives you 4GB RAM and 2 vCPUs for €4.51/month (~$5) — more resources than Railway's $20/mo plan. Your `docker-compose.yml` is already written.

**Cost:** €4.51/month (CX22: 4GB RAM, 2 vCPU, 40GB SSD)
**RAM available:** 4GB — comfortable for AMAIMA + FHE + headroom
**TenSEAL:** ✅ Installs successfully (full build environment available)
**Best for:** Production workloads, full control, lowest cost at scale

#### Server setup

```bash
# On your Hetzner VPS (Ubuntu 24.04)
apt update && apt upgrade -y
apt install -y docker.io docker-compose-plugin git
usermod -aG docker $USER
newgrp docker

# Clone your repo
git clone https://github.com/YOUR_ORG/AMAIMA.git
cd AMAIMA
```

#### Create `.env` (never commit this)

```bash
cat > .env << 'EOF'
NVIDIA_API_KEY=nvapi-your-key
NVIDIA_NIM_API_KEY=nvapi-your-key
API_SECRET_KEY=your-strong-32-char-secret
AMAIMA_EXECUTION_MODE=execution-enabled
FHE_ENABLED=true
SEAL_THREADS=4
DB_PASSWORD=your-strong-db-password
STRIPE_SECRET_KEY=sk_live_your-key
EOF
chmod 600 .env
```

#### docker-compose.yml (already in repo root)

```yaml
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: amaima
      POSTGRES_USER: amaima
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U amaima"]
      interval: 10s
      timeout: 5s
      retries: 5

  amaima:
    build: .
    ports:
      - "10000:10000"
    environment:
      - NVIDIA_API_KEY=${NVIDIA_API_KEY}
      - NVIDIA_NIM_API_KEY=${NVIDIA_NIM_API_KEY}
      - API_SECRET_KEY=${API_SECRET_KEY}
      - AMAIMA_EXECUTION_MODE=execution-enabled
      - FHE_ENABLED=true
      - SEAL_THREADS=4
      - DATABASE_URL=postgresql://amaima:${DB_PASSWORD}@db:5432/amaima
      - BACKEND_URL=http://localhost:8000
      - PORT=10000
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 90s

volumes:
  pgdata:
```

#### Deploy

```bash
docker compose up -d --build
```

#### SSL with Caddy (simpler than Nginx + Certbot)

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install caddy
```

Create `/etc/caddy/Caddyfile`:
```
amaima.live {
    reverse_proxy localhost:10000
}
```

```bash
systemctl enable --now caddy
# Caddy auto-provisions Let's Encrypt SSL — no certbot needed
```

#### Auto-deploy on git push (optional)

```bash
# On the VPS, add a cron or systemd timer:
cat > /etc/systemd/system/amaima-deploy.service << 'EOF'
[Unit]
Description=AMAIMA auto-deploy

[Service]
Type=oneshot
WorkingDirectory=/root/AMAIMA
ExecStart=/bin/bash -c 'git pull && docker compose up -d --build'
EOF
```

---

### 4. DigitalOcean App Platform

Clean GitHub integration, managed PostgreSQL, and straightforward pricing. Use the Professional tier (2GB) — the Basic tier (1GB) will OOM during build.

**Cost:** $25/month (Professional — 2GB RAM) + ~$15/month managed PostgreSQL
**TenSEAL:** ✅ Installs on Professional tier

#### Steps

1. Sign up at [digitalocean.com](https://www.digitalocean.com) and connect your GitHub repo

2. Create a **managed PostgreSQL database** from the Databases section

3. Create a new **App**, connect your repo, configure:
   - **Type:** Web Service
   - **Environment:** Dockerfile (root `Dockerfile`)
   - **HTTP Port:** `10000`
   - **Instance size:** Professional ($25/mo, 2GB RAM) — do NOT use Basic

4. Add environment variables (mark sensitive values as Encrypted):
   ```
   NVIDIA_API_KEY=nvapi-your-key
   NVIDIA_NIM_API_KEY=nvapi-your-key
   API_SECRET_KEY=your-strong-secret
   AMAIMA_EXECUTION_MODE=execution-enabled
   FHE_ENABLED=true
   SEAL_THREADS=2
   PORT=10000
   BACKEND_URL=http://localhost:8000
   DATABASE_URL=${db.DATABASE_URL}
   ```

5. Deploy — DigitalOcean builds and deploys automatically on every push to `main`

---

### 5. Render (Standard Plan+)

Render works well once you're on the Standard plan (2GB). The free and Starter tiers (both 512MB) will always fail — the Next.js build alone peaks at 500MB.

**Cost:** $25/month (Standard — 2GB RAM)
**TenSEAL:** ✅ Installs on Standard plan
**Note:** Render's build environment shares the same memory limit as the runtime on lower plans — this is what caused the `FATAL ERROR: JavaScript heap out of memory` during `npm run build`.

#### Steps

1. Sign up at [render.com](https://render.com), connect your GitHub repo

2. Create a **PostgreSQL database** in Render → copy the connection string

3. Create a **New Web Service**:
   - Environment: Docker
   - Dockerfile Path: `./Dockerfile`
   - Instance type: **Standard** ($25/mo, 2GB RAM)

4. Set environment variables:
   ```
   NVIDIA_API_KEY=nvapi-your-key
   NVIDIA_NIM_API_KEY=nvapi-your-key
   API_SECRET_KEY=your-strong-secret
   AMAIMA_EXECUTION_MODE=execution-enabled
   FHE_ENABLED=true
   SEAL_THREADS=2
   PORT=10000
   BACKEND_URL=http://localhost:8000
   DATABASE_URL=postgresql://user:pass@host:5432/amaima
   ```

5. Deploy — use **"Clear build cache & deploy"** on the first deploy after changing the Dockerfile

#### render.yaml (add to repo root for one-click deploys)

```yaml
services:
  - type: web
    name: amaima
    runtime: docker
    plan: standard
    dockerfilePath: ./Dockerfile
    dockerContext: .
    healthCheckPath: /health
    envVars:
      - key: NVIDIA_API_KEY
        sync: false
      - key: NVIDIA_NIM_API_KEY
        sync: false
      - key: API_SECRET_KEY
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: amaima-db
          property: connectionString
      - key: AMAIMA_EXECUTION_MODE
        value: execution-enabled
      - key: FHE_ENABLED
        value: "true"
      - key: SEAL_THREADS
        value: "2"
      - key: PORT
        value: "10000"
      - key: BACKEND_URL
        value: http://localhost:8000

databases:
  - name: amaima-db
    plan: starter
    databaseName: amaima
```

---

### 6. Replit Reserved VM

The development environment where AMAIMA was built. FHE works here because Replit installs TenSEAL directly and the Reserved VM has enough RAM.

**Cost:** ~$7-12/month (Reserved VM)
**TenSEAL:** ✅ Works — Replit has pip access to tenseal
**Best for:** Continued development, demos, prototyping

#### Publishing to Production

1. Click **Publish** in your Replit workspace
2. Choose **Reserved VM** (Autoscale doesn't support two persistent processes)
3. Set the run command:
   ```bash
   cd /home/runner/workspace/amaima/backend && \
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 &
   cd /home/runner/workspace/amaima/frontend && \
   npm run build && npx next start -p 10000 -H 0.0.0.0
   ```
4. Ensure Secrets are set: `NVIDIA_API_KEY`, `API_SECRET_KEY`, `AMAIMA_EXECUTION_MODE`, `FHE_ENABLED=true`
5. Replit provides a public URL at `https://your-project.replit.app`

---

### 7. Google Cloud Run

Cloud Run works for AMAIMA but requires `--memory 2Gi` minimum and `--no-cpu-throttling` to keep the FHE context pool and uvicorn workers alive between requests.

**Cost:** Pay-per-use + $0.10/hour for min-instances=1 (~$75/month always-on)
**TenSEAL:** ✅ Installs — Cloud Build has no memory constraints
**Best for:** Teams already in GCP

#### Steps

1. Store secrets in Secret Manager:
   ```bash
   echo -n "nvapi-your-key" | gcloud secrets create NVIDIA_API_KEY --data-file=-
   echo -n "your-strong-secret" | gcloud secrets create API_SECRET_KEY --data-file=-
   echo -n "postgresql://..." | gcloud secrets create DATABASE_URL --data-file=-
   ```

2. Build and push:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT/amaima
   ```

3. Deploy:
   ```bash
   gcloud run deploy amaima \
     --image gcr.io/YOUR_PROJECT/amaima \
     --platform managed \
     --region us-east1 \
     --allow-unauthenticated \
     --port 10000 \
     --memory 2Gi \
     --cpu 2 \
     --min-instances 1 \
     --no-cpu-throttling \
     --timeout 300 \
     --set-env-vars "BACKEND_URL=http://localhost:8000,AMAIMA_EXECUTION_MODE=execution-enabled,FHE_ENABLED=true,PORT=10000" \
     --set-secrets "NVIDIA_API_KEY=NVIDIA_API_KEY:latest,API_SECRET_KEY=API_SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest"
   ```

   Critical flags:
   - `--memory 2Gi` — minimum for AMAIMA (use 4Gi for FHE-heavy workloads)
   - `--min-instances 1` — keeps FHE pool warm; without this every cold start re-generates SEAL contexts (~600ms delay)
   - `--no-cpu-throttling` — keeps uvicorn workers alive between requests
   - `--timeout 300` — FHE operations can take up to 60s; default 60s timeout kills them

---

### 8. AWS

#### Option A: App Runner (Simplest)

1. Push to Amazon ECR:
   ```bash
   aws ecr create-repository --repository-name amaima
   docker build -t amaima .
   docker tag amaima:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/amaima:latest
   docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/amaima:latest
   ```

2. Create an App Runner service — set **CPU: 1 vCPU, Memory: 2GB minimum**, port 10000

3. Create RDS PostgreSQL and pass `DATABASE_URL` as an environment variable

#### Option B: ECS with Fargate (Production scale)

1. Define an ECS task with the full-stack image — set 2GB+ memory reservation
2. Expose port 10000 through an Application Load Balancer
3. Store secrets in AWS Secrets Manager
4. Set up RDS PostgreSQL

#### Option C: EC2 (Full control, lowest cost)

```bash
# t3.small (2GB RAM) is the minimum; t3.medium (4GB) recommended
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER
git clone https://github.com/YOUR_ORG/AMAIMA.git && cd AMAIMA
# Create .env, then:
docker compose up -d --build
```

---

### 9. Azure Container Apps

```bash
az login
az group create --name amaima-rg --location eastus
az containerapp env create --name amaima-env --resource-group amaima-rg --location eastus

az containerapp up \
  --name amaima \
  --resource-group amaima-rg \
  --environment amaima-env \
  --source . \
  --target-port 10000 \
  --ingress external \
  --min-replicas 1 \
  --cpu 1 \
  --memory 2.0Gi \
  --env-vars \
    "BACKEND_URL=http://localhost:8000" \
    "AMAIMA_EXECUTION_MODE=execution-enabled" \
    "FHE_ENABLED=true" \
    "PORT=10000" \
  --secrets \
    "nvidia-key=nvapi-your-key" \
    "api-secret=your-strong-secret" \
    "db-url=postgresql://..."
```

---

### 10. Heroku

```bash
heroku login
heroku create amaima-app
heroku addons:create heroku-postgresql:essential-0 -a amaima-app
heroku stack:set container -a amaima-app
```

Create `heroku.yml` in repo root:
```yaml
build:
  docker:
    web: Dockerfile
run:
  web: /app/start.sh
```

```bash
heroku config:set \
  NVIDIA_API_KEY=nvapi-your-key \
  NVIDIA_NIM_API_KEY=nvapi-your-key \
  API_SECRET_KEY=your-strong-secret \
  AMAIMA_EXECUTION_MODE=execution-enabled \
  FHE_ENABLED=true \
  PORT=10000 \
  BACKEND_URL=http://localhost:8000 \
  -a amaima-app

# Set dyno to at least Standard-2X (1GB RAM) — Eco/Basic dynos will OOM
heroku ps:resize web=standard-2x -a amaima-app

git push heroku main
```

---

## Post-Deployment Verification

Run these checks after deploying to any platform:

### 1. Backend health
```bash
curl https://YOUR_URL/health
# Expected: {"status": "healthy", ...}
```

### 2. FHE subsystem
```bash
curl https://YOUR_URL/v1/fhe/status
# Expected: {"available": true, "backend": "Microsoft SEAL via TenSEAL", ...}
# If available=false, check FHE_ENABLED=true and that tenseal installed in build log
```

### 3. AI query
```bash
curl -X POST https://YOUR_URL/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'
```

### 4. FHE demo (all 5 should return 200)
```bash
curl https://YOUR_URL/v1/fhe/demo
```

### 5. Models list
```bash
curl https://YOUR_URL/v1/models
# Should show nvidia_nim_configured: true
```

---

## Security Checklist

Before going public:

- [ ] `API_SECRET_KEY` is a strong random value (32+ characters) — the default is publicly known
- [ ] `NVIDIA_API_KEY` is stored as a secret, not in code or config files
- [ ] `DATABASE_URL` credentials are not exposed in logs
- [ ] HTTPS is enabled (all platforms above do this automatically)
- [ ] CORS is restricted — in `main.py` change `allow_origins=["*"]` to `allow_origins=["https://amaima.live"]`
- [ ] `--reload` flag is NOT in the uvicorn start command (development only)
- [ ] Stripe webhook secret is set if using billing features
- [ ] FHE dashboard is behind authentication if exposing sensitive key operations

---

## Troubleshooting

### `FATAL ERROR: JavaScript heap out of memory` during build

The Next.js build is OOM-killed. Your platform doesn't have enough RAM for the build environment.

- **Fix:** Upgrade to a plan with 2GB+ RAM. This error cannot be fixed with `NODE_OPTIONS` workarounds on platforms with hard memory limits — you need more RAM.
- **Affected plans:** Render free/Starter (512MB), Fly.io with `memory = "1gb"`, Heroku Eco/Basic dynos

### `TenSEAL not available — FHE operations will be disabled`

TenSEAL failed to install or import.

1. Check the **build log** (not runtime log) for `tenseal` — look for `Successfully installed tenseal-0.3.1x` or an error
2. If the build log shows a compilation error, your build environment is missing `cmake` and `g++` — both are in the updated `Dockerfile`
3. If tenseal doesn't appear in the build log at all, the `RUN pip install tenseal` step was skipped — verify the Dockerfile is the one from this repo (root `Dockerfile`, not `amaima/backend/Dockerfile`)
4. Ensure `FHE_ENABLED=true` is set as an environment variable on your platform

### Frontend SIGTERM every 5-15 minutes

`next start` is being OOM-killed by the OS.

- **Fix:** Upgrade to a plan with more RAM. This happens when the total runtime memory (backend + frontend + FHE pool) exceeds the instance limit.
- On a 2GB instance this should not occur under normal load.

### `Backend unavailable` on the web interface

1. Is the backend process running? Check logs for Python startup errors
2. Is `BACKEND_URL=http://localhost:8000`? (Correct for full-stack — do not change to a public URL)
3. Did the backend finish starting before the frontend tried to connect? The `start.sh` health-check loop waits up to 60s

### Database connection errors

1. Check `DATABASE_URL` is set and the PostgreSQL host is reachable from your container
2. The backend creates tables automatically on first connection (no Alembic migration needed for initial setup)
3. For managed databases, ensure your service's egress IP is allowlisted

### FHE context pool warm-up takes too long

Normal warm-up time on a 1-CPU instance: 15-30 seconds for all CKKS + BFV contexts.
The `grace_period = "90s"` in `fly.toml` and `start-period=90s` in the Dockerfile `HEALTHCHECK` accounts for this.
If health checks are failing before the pool warms, increase these values.

---

## Platform Comparison

> Based on actual AMAIMA deployment experience. "Build OK" means the Docker build completes without OOM. "FHE OK" means TenSEAL installs and the context pool warms successfully.

| Platform | Min Plan for AMAIMA | Monthly Cost | Build OK | FHE OK | Always On | Best For |
|---|---|---|---|---|---|---|
| **Railway** | Starter (usage-based) | ~$10-20 | ✅ | ✅ | ✅ | Fastest to get started |
| **Fly.io** | 2GB shared-CPU | ~$15 | ✅ | ✅ | ✅ | Global edge, full control |
| **Hetzner VPS** | CX22 (4GB) | ~$5 | ✅ | ✅ | ✅ | Best value, full control |
| **DigitalOcean** | Professional (2GB) | ~$25 | ✅ | ✅ | ✅ | Clean UI, managed PG |
| **Render** | Standard (2GB) | $25 | ✅ | ✅ | ✅ | Good if already on Render |
| **Replit** | Reserved VM | ~$7-12 | ✅ | ✅ | ✅ | Development + demos |
| **Cloud Run** | 2Gi + min-instances=1 | ~$75 | ✅ | ✅ | ✅ | GCP ecosystem |
| **AWS App Runner** | 2GB | ~$30 | ✅ | ✅ | ✅ | AWS ecosystem |
| **AWS EC2** | t3.small (2GB) | ~$17 | ✅ | ✅ | ✅ | Full control on AWS |
| **Azure** | 2Gi | ~$30 | ✅ | ✅ | ✅ | Azure ecosystem |
| **Heroku** | Standard-2X | ~$50 | ✅ | ✅ | ✅ | Easy deploys |
| **Render Free/Starter** | — | $0-7 | ❌ OOM | ❌ | ❌ | Not suitable |
| **Fly.io 1GB** | — | ~$7 | ❌ OOM | ❌ | ✅ | Not suitable |
| **Heroku Eco/Basic** | — | $5-7 | ❌ OOM | ❌ | ❌ | Not suitable |

### Recommended path

1. **Development & demos** → Replit (already working)
2. **Fastest production deploy** → Railway (connect GitHub, set env vars, done)
3. **Best long-term value** → Hetzner CX22 VPS (~$5/mo, 4GB RAM, `docker compose up`)
4. **Global scale** → Fly.io (2GB+ VM, multi-region with `fly regions add`)
