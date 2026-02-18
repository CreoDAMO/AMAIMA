# AMAIMA Full-Stack Deployment Guide

Deploy the entire AMAIMA application (Next.js frontend + FastAPI backend) as a **single unit** — no need to split them across different services.

---

## Table of Contents

1. [How It Works](#how-it-works)
2. [Environment Variables](#environment-variables)
3. [Deployment Options](#deployment-options)
   - [Replit (Recommended for Getting Started)](#1-replit)
   - [Railway](#2-railway)
   - [Render](#3-render)
   - [Fly.io](#4-flyio)
   - [Docker / VPS (Self-Hosted)](#5-docker--vps-self-hosted)
   - [Google Cloud Run](#6-google-cloud-run)
   - [AWS (App Runner / ECS / EC2)](#7-aws)
   - [Azure Container Apps](#8-azure-container-apps)
   - [DigitalOcean App Platform](#9-digitalocean-app-platform)
   - [Heroku](#10-heroku)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Security Checklist](#security-checklist)
6. [Troubleshooting](#troubleshooting)

---

## How It Works

AMAIMA has two components that work together:

```
┌──────────────────────────────────────────────────────┐
│                   Your Server                        │
│                                                      │
│  ┌─────────────────────┐   ┌──────────────────────┐  │
│  │   Next.js Frontend  │──▶│   FastAPI Backend     │  │
│  │   (Port 5000)       │   │   (Port 8000)         │  │
│  │                     │   │                       │  │
│  │  - Web UI           │   │  - Smart Router       │  │
│  │  - Agent Builder    │   │  - NVIDIA NIM client  │  │
│  │  - Billing/Analytics│   │  - NIM Prompt Cache    │  │
│  │  - API proxy routes │   │  - MAU Rate Limiting   │  │
│  │  - Stripe checkout  │   │  - Multi-agent crews  │  │
│  └─────────────────────┘   └──────────────────────┘  │
│          │                          │                 │
│          │  BACKEND_URL=            │                 │
│          │  http://localhost:8000   │                 │
│          ▼                          ▼                 │
│     Users see the UI          Calls NVIDIA NIM API   │
│                                     │                │
│                              ┌──────▼──────┐         │
│                              │ PostgreSQL   │         │
│                              │ (API keys,   │         │
│                              │  usage, etc) │         │
│                              └─────────────┘         │
└──────────────────────────────────────────────────────┘
```

- The **frontend** (Next.js) serves the web interface including the Agent Builder, Billing & Analytics dashboard, and API proxy routes that forward requests to the backend
- The **backend** (FastAPI) handles AI query routing, NIM prompt caching, MAU rate limiting, multi-agent orchestration, and calls NVIDIA NIM for inference
- **PostgreSQL** stores API keys, usage tracking, monthly usage, conversation history, and billing data
- When deployed together, the frontend connects to the backend via `localhost` — no public backend URL needed
- Users only interact with the frontend; the backend stays internal

### Project Structure

```
amaima/
├── frontend/                    # Next.js frontend (port 5000)
│   ├── src/app/                 # Pages and components
│   │   ├── agent-builder/       # React Flow visual workflow builder
│   │   ├── billing/             # Billing page with analytics dashboard
│   │   ├── conversations/       # Conversation history
│   │   ├── benchmarks/          # Model benchmarking
│   │   └── api/                 # API proxy routes → backend
│   │       ├── v1/              # Backend API proxies
│   │       └── stripe/          # Stripe checkout/webhook routes
│   ├── src/lib/                 # Stripe client, utilities
│   ├── next.config.js
│   └── package.json
├── backend/                     # FastAPI backend (port 8000)
│   ├── main.py                  # Entry point + MAU middleware
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Standalone backend container
│   └── app/
│       ├── modules/
│       │   ├── nvidia_nim_client.py  # NIM client + prompt cache
│       │   ├── execution_engine.py
│       │   └── smart_router_engine.py
│       ├── agents/              # Multi-agent crew system
│       │   ├── crew_manager.py
│       │   ├── biology_crew.py
│       │   └── robotics_crew.py
│       ├── routers/             # Domain-specific API routers
│       ├── billing.py           # API key + usage tracking
│       ├── webhooks.py          # Webhook notifications
│       └── security.py          # API key authentication
│   └── tests/
│       ├── agents/              # Unit tests (55 tests)
│       └── integration/         # Integration tests (8 tests)
├── Dockerfile                   # Full-stack container (frontend + backend)
├── start.sh                     # Full-stack startup script
└── docker-compose.yml           # Docker Compose config
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `NVIDIA_API_KEY` | Yes | Your NVIDIA NIM API key (get one at https://build.nvidia.com) |
| `API_SECRET_KEY` | Yes (production) | Protects API endpoints. **Must be changed from default in production** — the default value is publicly known and would let anyone use your NVIDIA credits |
| `DATABASE_URL` | Yes (production) | PostgreSQL connection string (e.g., `postgresql://user:pass@host:5432/dbname`). Required for API key management, usage tracking, billing, and conversation history |
| `AMAIMA_EXECUTION_MODE` | Yes | Set to `execution-enabled` for real AI responses |
| `STRIPE_SECRET_KEY` | Optional | Stripe secret key for payment processing. Required if enabling the billing subscription flow |
| `STRIPE_WEBHOOK_SECRET` | Optional | Stripe webhook signing secret for verifying webhook events |
| `BACKEND_URL` | No | How the frontend finds the backend. Defaults to `http://localhost:8000` — correct for full-stack deployment, no need to change |
| `PORT` | No | Frontend port (default: 5000 for dev, varies by platform) |

---

## Deployment Options

---

### 1. Replit

The simplest option. Everything is already configured and running.

**Cost:** Free for development; Autoscale or Reserved VM for production (starts at ~$0.06/hr)

#### How It Works on Replit

Two workflows run simultaneously:
- **AMAIMA Backend:** Starts the FastAPI server on port 8000
- **AMAIMA Frontend:** Starts the Next.js dev server on port 5000

The frontend automatically proxies API requests to the backend at `http://localhost:8000`. PostgreSQL is provided by Replit's built-in database, and Stripe is managed via Replit's Stripe integration.

#### Development (Already Working)

Your app is already running in development mode. You can use it right now in the webview.

#### Publishing to Production

1. Click the **Publish** button in your Replit workspace
2. Choose **Reserved VM** (recommended for full-stack since you need both processes running)
3. Set the **run command** to start both services:
   ```bash
   cd /home/runner/workspace/amaima/backend && uvicorn main:app --host 0.0.0.0 --port 8000 &
   cd /home/runner/workspace/amaima/frontend && npm run build && npx next start -p 5000 -H 0.0.0.0
   ```
4. Make sure your secrets are set in the Secrets tab:
   - `NVIDIA_API_KEY`
   - `API_SECRET_KEY` (set a strong production value)
   - `AMAIMA_EXECUTION_MODE` = `execution-enabled`
   - `DATABASE_URL` (automatically set by Replit's PostgreSQL)
5. Replit will give you a public URL like `https://your-project.replit.app`

#### Why Reserved VM Instead of Autoscale?

Autoscale is great for single-process apps, but AMAIMA runs two processes (frontend + backend). Reserved VM keeps both running continuously and handles this better. It also supports WebSocket connections which AMAIMA uses for real-time system monitoring.

---

### 2. Railway

Railway can deploy multiple services from one repo, or you can run both in a single service.

**Cost:** ~$5-10/month for light usage

#### Option A: Single Service (Simplest)

1. **Sign up** at [railway.app](https://railway.app) and connect your GitHub repo

2. **Add a PostgreSQL database** from Railway's plugin marketplace

3. Railway detects the root `Dockerfile` and builds automatically

4. **Set environment variables** in Railway dashboard:
   ```
   NVIDIA_API_KEY=nvapi-your-key
   API_SECRET_KEY=your-strong-secret
   AMAIMA_EXECUTION_MODE=execution-enabled
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   PORT=5000
   ```

5. **Deploy** — Railway builds the Docker image and starts both services

#### Option B: Two Linked Services

1. Create two services from the same repo:
   - **Backend:** Root directory `amaima/backend`, Dockerfile `amaima/backend/Dockerfile`
   - **Frontend:** Root directory `amaima/frontend`, Dockerfile `amaima/frontend/Dockerfile`
2. Add a PostgreSQL plugin and link it to the backend
3. Railway gives each service an internal hostname
4. Set the frontend's `BACKEND_URL` to the backend's internal Railway URL (e.g., `http://backend.railway.internal:8000`)

---

### 3. Render

Render can run both as a single service using a Docker container.

**Cost:** Free tier available (with cold starts), paid starts at $7/month

#### Steps

1. **Sign up** at [render.com](https://render.com)

2. **Create a PostgreSQL database** in Render and copy the connection string

3. **Create a New Web Service** on Render:
   - Connect your GitHub repository
   - **Environment:** Docker
   - **Docker Context:** `.` (repo root)
   - **Dockerfile Path:** `./Dockerfile` (the full-stack one in repo root)

4. **Add environment variables:**
   ```
   NVIDIA_API_KEY=nvapi-your-key
   API_SECRET_KEY=your-strong-secret
   AMAIMA_EXECUTION_MODE=execution-enabled
   DATABASE_URL=postgresql://user:pass@host:5432/amaima
   PORT=5000
   ```

5. **Deploy** — Render builds the Docker image and starts both services

#### Render Blueprint (`render.yaml` in repo root)

```yaml
services:
  - type: web
    name: amaima
    runtime: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    healthCheckPath: /api/health
    envVars:
      - key: NVIDIA_API_KEY
        sync: false
      - key: API_SECRET_KEY
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: amaima-db
          property: connectionString
      - key: AMAIMA_EXECUTION_MODE
        value: execution-enabled
      - key: PORT
        value: "5000"
      - key: BACKEND_URL
        value: http://localhost:8000

databases:
  - name: amaima-db
    plan: free
    databaseName: amaima
```

---

### 4. Fly.io

Fly.io runs Docker containers at edge locations worldwide for low latency.

**Cost:** ~$3-7/month for light usage

#### Steps

1. **Install the Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. **Create a Postgres database:**
   ```bash
   fly postgres create --name amaima-db
   ```

3. **Create `fly.toml`** in the repo root:
   ```toml
   app = "amaima"
   primary_region = "iad"

   [build]
     dockerfile = "Dockerfile"

   [env]
     BACKEND_URL = "http://localhost:8000"
     AMAIMA_EXECUTION_MODE = "execution-enabled"
     PORT = "5000"

   [http_service]
     internal_port = 5000
     force_https = true
     auto_stop_machines = false
     auto_start_machines = true
     min_machines_running = 1

   [[http_service.checks]]
     grace_period = "30s"
     interval = "30s"
     method = "GET"
     path = "/api/health"
     timeout = "10s"

   [[vm]]
     memory = "1gb"
     cpu_kind = "shared"
     cpus = 1
   ```

   **Note:** `auto_stop_machines = false` and `min_machines_running = 1` keep the app always on, which is important since the backend needs to stay running.

4. **Attach the database and set secrets:**
   ```bash
   fly postgres attach amaima-db
   fly secrets set NVIDIA_API_KEY=nvapi-your-key
   fly secrets set API_SECRET_KEY=your-strong-secret
   ```

5. **Deploy:**
   ```bash
   fly deploy
   ```

6. **Your URL:** `https://amaima.fly.dev`

---

### 5. Docker / VPS (Self-Hosted)

Run everything on your own server — a VPS from any provider (Hetzner, Linode, Vultr, etc.) or your own hardware.

**Cost:** VPS from ~$4/month

#### Full-Stack Dockerfile

The `Dockerfile` in the repo root builds both frontend and backend into a single image:

```dockerfile
FROM python:3.11-slim-bookworm AS base

RUN apt-get update && apt-get install -y \
    curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN cd amaima/backend && pip install --no-cache-dir -r requirements.txt

ARG DATABASE_URL=""
ARG STRIPE_SECRET_KEY=""
ARG NVIDIA_API_KEY=""
ENV DATABASE_URL=${DATABASE_URL}
ENV STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
ENV NVIDIA_API_KEY=${NVIDIA_API_KEY}

RUN cd amaima/frontend && npm install && npm run build

ENV BACKEND_URL=http://localhost:8000
ENV PORT=5000

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 5000 8000

CMD ["/app/start.sh"]
```

#### Start Script (`start.sh` in repo root)

```bash
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
```

#### Docker Compose (`docker-compose.yml` in repo root)

```yaml
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: amaima
      POSTGRES_USER: amaima
      POSTGRES_PASSWORD: ${DB_PASSWORD:-amaima_dev_password}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U amaima"]
      interval: 10s
      timeout: 5s
      retries: 5

  amaima:
    build: .
    ports:
      - "5000:5000"
    environment:
      - NVIDIA_API_KEY=${NVIDIA_API_KEY}
      - API_SECRET_KEY=${API_SECRET_KEY}
      - AMAIMA_EXECUTION_MODE=execution-enabled
      - DATABASE_URL=postgresql://amaima:${DB_PASSWORD:-amaima_dev_password}@db:5432/amaima
      - BACKEND_URL=http://localhost:8000
      - PORT=5000
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

volumes:
  pgdata:
```

Create a `.env` file (never commit this):
```
NVIDIA_API_KEY=nvapi-your-key
API_SECRET_KEY=your-strong-secret
DB_PASSWORD=your-strong-db-password
```

#### Run It

```bash
docker compose up -d
```

Your app is now at `http://your-server-ip:5000`

#### Adding SSL with Nginx

For HTTPS, put Nginx in front:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support for real-time features
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Get a free SSL certificate:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

### 6. Google Cloud Run

Cloud Run can run the full-stack Docker container. Use `--no-cpu-throttling` to keep the backend alive between requests.

**Cost:** Pay-per-use, generous free tier (2 million requests/month)

#### Steps

1. **Create a Cloud SQL PostgreSQL instance** or use a managed provider

2. **Build and push the Docker image:**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT/amaima
   ```

3. **Deploy:**
   ```bash
   gcloud run deploy amaima \
     --image gcr.io/YOUR_PROJECT/amaima \
     --platform managed \
     --region us-east1 \
     --allow-unauthenticated \
     --port 5000 \
     --memory 1Gi \
     --cpu 1 \
     --min-instances 1 \
     --max-instances 5 \
     --no-cpu-throttling \
     --set-env-vars "BACKEND_URL=http://localhost:8000,AMAIMA_EXECUTION_MODE=execution-enabled" \
     --set-secrets "NVIDIA_API_KEY=NVIDIA_API_KEY:latest,API_SECRET_KEY=API_SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest"
   ```

   **Important flags:**
   - `--min-instances 1` keeps at least one instance warm (no cold starts)
   - `--no-cpu-throttling` keeps the backend process running between requests
   - `--port 5000` tells Cloud Run the container listens on port 5000 (the frontend)

4. **Store secrets first:**
   ```bash
   echo -n "nvapi-your-key" | gcloud secrets create NVIDIA_API_KEY --data-file=-
   echo -n "your-strong-secret" | gcloud secrets create API_SECRET_KEY --data-file=-
   echo -n "postgresql://..." | gcloud secrets create DATABASE_URL --data-file=-
   ```

---

### 7. AWS

#### Option A: AWS App Runner (Simplest)

1. Push your Docker image to Amazon ECR:
   ```bash
   aws ecr create-repository --repository-name amaima
   docker build -t amaima .
   docker tag amaima:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/amaima:latest
   docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/amaima:latest
   ```

2. Create an RDS PostgreSQL instance or use Amazon Aurora Serverless

3. Create an App Runner service:
   - Source: ECR image
   - Port: 5000
   - CPU: 1 vCPU, Memory: 2 GB
   - Add environment variables including `DATABASE_URL`

#### Option B: AWS ECS with Fargate (Production)

1. Create an ECS cluster
2. Define a task using the full-stack Docker image
3. Expose port 5000 through an Application Load Balancer
4. Store secrets in AWS Secrets Manager
5. Set up RDS PostgreSQL and pass `DATABASE_URL` as a secret
6. Set up auto-scaling based on CPU/memory

#### Option C: AWS EC2 (Full Control)

1. Launch an EC2 instance (t3.small minimum)
2. Install Docker:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose
   sudo usermod -aG docker $USER
   ```
3. Clone the repo and run:
   ```bash
   git clone https://github.com/CreoDAMO/AMAIMA.git
   cd AMAIMA
   # Create .env with your secrets (including DATABASE_URL)
   docker compose up -d
   ```
4. Set up Nginx + Certbot for SSL (see Docker/VPS section above)

---

### 8. Azure Container Apps

1. **Create resources:**
   ```bash
   az login
   az group create --name amaima-rg --location eastus
   az containerapp env create --name amaima-env --resource-group amaima-rg --location eastus
   ```

2. **Create an Azure Database for PostgreSQL** and get the connection string

3. **Deploy:**
   ```bash
   az containerapp up \
     --name amaima \
     --resource-group amaima-rg \
     --environment amaima-env \
     --source . \
     --target-port 5000 \
     --ingress external \
     --min-replicas 1 \
     --env-vars \
       "BACKEND_URL=http://localhost:8000" \
       "AMAIMA_EXECUTION_MODE=execution-enabled" \
     --secrets \
       "nvidia-key=nvapi-your-key" \
       "api-secret=your-strong-secret" \
       "db-url=postgresql://..."
   ```

   `--min-replicas 1` keeps the app always running so the backend doesn't shut down.

---

### 9. DigitalOcean App Platform

1. **Sign up** at [digitalocean.com](https://www.digitalocean.com)

2. **Create a managed PostgreSQL database** from the DigitalOcean dashboard

3. **Create a new App**, connect your GitHub repo

4. **Configure:**
   - **Type:** Web Service
   - **Environment:** Dockerfile (point to the full-stack Dockerfile in repo root)
   - **HTTP Port:** 5000

5. **Add environment variables** (mark API keys as "Encrypted"):
   ```
   NVIDIA_API_KEY=nvapi-your-key
   API_SECRET_KEY=your-strong-secret
   AMAIMA_EXECUTION_MODE=execution-enabled
   DATABASE_URL=${db.DATABASE_URL}
   BACKEND_URL=http://localhost:8000
   PORT=5000
   ```

6. **Deploy**

**Cost:** Starting at $5/month

---

### 10. Heroku

Heroku supports Docker deployments for multi-process apps.

#### Steps

1. **Install Heroku CLI** and log in:
   ```bash
   heroku login
   heroku create amaima-app
   ```

2. **Add Heroku Postgres:**
   ```bash
   heroku addons:create heroku-postgresql:essential-0 -a amaima-app
   ```

3. **Create `heroku.yml`** in repo root:
   ```yaml
   build:
     docker:
       web: Dockerfile
   run:
     web: /app/start.sh
   ```

4. **Set the stack to container:**
   ```bash
   heroku stack:set container -a amaima-app
   ```

5. **Set environment variables:**
   ```bash
   heroku config:set NVIDIA_API_KEY=nvapi-your-key -a amaima-app
   heroku config:set API_SECRET_KEY=your-strong-secret -a amaima-app
   heroku config:set AMAIMA_EXECUTION_MODE=execution-enabled -a amaima-app
   heroku config:set BACKEND_URL=http://localhost:8000 -a amaima-app
   ```
   (Heroku automatically sets `DATABASE_URL` when you add Postgres)

6. **Deploy:**
   ```bash
   git push heroku main
   ```

**Cost:** Eco dynos start at $5/month

---

## Post-Deployment Verification

After deploying to any platform, run these checks to make sure everything works:

### 1. Check the Web Interface

Open your deployment URL in a browser. You should see the AMAIMA dashboard with the navigation bar showing Home, Agent Builder, Conversations, Benchmarks, Settings, and Billing.

### 2. Check API Health

```bash
curl https://YOUR_URL/api/health
```

Expected:
```json
{
  "status": "healthy",
  "version": "5.0.0",
  "components": {
    "router": {"status": "healthy"},
    "api": {"status": "healthy"}
  }
}
```

### 3. Test AI Query

Type a question in the web interface and click "Process Query." You should get a real AI response within a few seconds.

Or test via command line:
```bash
curl -X POST https://YOUR_URL/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_SECRET_KEY" \
  -d '{"query": "What is machine learning?"}'
```

### 4. Check Available Models

```bash
curl https://YOUR_URL/api/v1/models
```

You should see NVIDIA NIM models listed with `nvidia_nim_configured: true`.

### 5. Check Cache Stats

```bash
curl https://YOUR_URL/api/v1/cache/stats
```

### 6. Test Agent Builder

Navigate to `/agent-builder` in the browser. You should see the visual workflow builder with template options (Research Pipeline, Drug Discovery, Navigation Crew).

### 7. Test Billing Page

Navigate to `/billing`. You should see:
- API key management with the generate key form
- Three pricing tiers (Community: Free, Production: $49/mo, Enterprise: $299/mo)
- Analytics tab with usage charts

---

## Security Checklist

Before sharing your deployment publicly:

- [ ] **Set `API_SECRET_KEY`** to a strong random value (32+ characters). The default is publicly known and would let anyone use your NVIDIA credits
- [ ] **Store `NVIDIA_API_KEY` as a secret**, not in code or config files
- [ ] **Set `DATABASE_URL` securely** — never expose database credentials in logs or config files
- [ ] **HTTPS is enabled** (most platforms do this automatically)
- [ ] **Restrict CORS** — edit `amaima/backend/main.py` and change `allow_origins=["*"]` to your actual domain (e.g., `allow_origins=["https://amaima-app.fly.dev"]`)
- [ ] **Remove `--reload` flag** from the backend start command (it's for development only)
- [ ] **Set Stripe webhook secret** if using payment features, to verify webhook events are authentic
- [ ] **Monitor logs** for errors and unusual activity

---

## Troubleshooting

### "Backend unavailable" on the web interface

The frontend can't reach the backend. Check:
1. Is the backend process actually running? Check logs for Python errors
2. Is `BACKEND_URL` set correctly? For full-stack, it should be `http://localhost:8000`
3. Did the backend finish starting before the frontend tried to connect?

### AI queries return errors

1. Check that `NVIDIA_API_KEY` is set correctly
2. Check that `AMAIMA_EXECUTION_MODE` is set to `execution-enabled`
3. Verify your NVIDIA API key is valid at https://build.nvidia.com

### Database connection errors

1. Check that `DATABASE_URL` is set and the PostgreSQL server is reachable
2. The backend creates tables automatically on first connection
3. For managed databases, make sure your service's IP is allowlisted

### Container won't build

1. Make sure `start.sh` has Unix line endings (LF, not CRLF). If editing on Windows, use `dos2unix start.sh`
2. Check that both `amaima/backend/requirements.txt` and `amaima/frontend/package.json` exist
3. The frontend build needs `npm install` to succeed — check for missing dependencies in build logs

### Billing/Stripe not working

1. Ensure `STRIPE_SECRET_KEY` is set in environment variables
2. For webhook events, configure Stripe to send to `https://YOUR_URL/api/stripe/webhook`
3. Set `STRIPE_WEBHOOK_SECRET` to the webhook signing secret from the Stripe dashboard

### Cold starts take too long

For platforms that scale to zero (Cloud Run, Render free tier, Fly.io):
- Set minimum instances to 1 to keep the app warm
- Or accept ~10-30 second cold starts on first request after idle

---

## Platform Comparison (Full-Stack)

| Platform | Setup Difficulty | Monthly Cost | Always On | Database | Auto-Deploy | Best For |
|---|---|---|---|---|---|---|
| **Replit** | Easiest | ~$7+ | Yes (VM) | Built-in | N/A | Prototyping, small projects |
| **Railway** | Easy | ~$5-10 | Yes | Plugin | Yes (GitHub) | Small-medium projects |
| **Render** | Easy | $7+ (free w/ limits) | Paid only | Managed | Yes (GitHub) | Budget production |
| **Fly.io** | Moderate | ~$5-10 | Yes | fly postgres | Yes (CLI) | Global low-latency |
| **Docker/VPS** | Moderate | ~$4+ (VPS) | Yes | Self-hosted | Manual | Full control |
| **Cloud Run** | Moderate | Pay-per-use | With min=1 | Cloud SQL | Yes (CLI) | Google Cloud users |
| **AWS App Runner** | Moderate | ~$10+ | Yes | RDS | Yes | AWS users |
| **AWS ECS** | Complex | ~$15+ | Yes | RDS/Aurora | Yes | Enterprise |
| **Azure** | Moderate | ~$10+ | With min=1 | Managed PG | Yes | Azure users |
| **DigitalOcean** | Easy | $5+ | Yes | Managed PG | Yes (GitHub) | Affordable always-on |
| **Heroku** | Easy | $5+ | Eco dynos | Heroku PG | Yes (GitHub) | Quick deploys |

---

## Recommended Setup

For most users, the simplest production path is:

1. **Start with Replit** (already working, zero setup)
2. **When ready for production**, pick one:
   - **Railway or Render** if you want the easiest GitHub-connected deployment
   - **Fly.io** if you want global edge performance
   - **Docker on a VPS** if you want full control at the lowest cost
   - **Cloud Run / AWS / Azure** if you're already in that ecosystem
