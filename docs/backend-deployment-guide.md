# AMAIMA Backend Deployment Guide

A comprehensive guide for deploying the AMAIMA FastAPI backend to various platforms. The backend is a Python FastAPI application that provides intelligent AI query routing via the Smart Router engine, powered by NVIDIA NIM for real model inference.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Deployment Options](#deployment-options)
   - [Replit](#1-replit)
   - [Railway](#2-railway)
   - [Render](#3-render)
   - [Fly.io](#4-flyio)
   - [Google Cloud Run](#5-google-cloud-run)
   - [AWS (ECS / App Runner / EC2)](#6-aws)
   - [Azure Container Apps](#7-azure-container-apps)
   - [DigitalOcean App Platform](#8-digitalocean-app-platform)
   - [Docker (Self-Hosted / VPS)](#9-docker-self-hosted--vps)
   - [Heroku](#10-heroku)
4. [Post-Deployment](#post-deployment)
5. [Connecting the Frontend](#connecting-the-frontend)
6. [Security Checklist](#security-checklist)

---

## Prerequisites

- **Python 3.10+** (3.11 recommended)
- **NVIDIA API Key** for NIM inference (get one at https://build.nvidia.com)
- The backend source code is located at `amaima/backend/` in the repository

### Backend File Structure

```
amaima/backend/
├── main.py                          # FastAPI entry point
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker container config
├── amaima_config.yaml               # Application configuration
├── app/
│   ├── core/
│   │   └── unified_smart_router.py  # Smart Router logic
│   ├── modules/
│   │   ├── nvidia_nim_client.py     # NVIDIA NIM API client
│   │   ├── execution_engine.py      # Model execution engine
│   │   └── smart_router_engine.py   # Query routing engine
│   ├── security.py                  # API key authentication
│   └── database.py                  # Database initialization
└── openapi.yaml                     # OpenAPI spec
```

---

## Environment Variables

Set these as secrets/environment variables in your chosen platform.

| Variable | Required | Description | Example |
|---|---|---|---|
| `NVIDIA_API_KEY` | Yes | NVIDIA NIM API key for AI inference | `nvapi-xxxxxxxxxxxx` |
| `API_SECRET_KEY` | Recommended | Secret key for authenticating `/v1/query` requests. If not set, defaults to a known development value — **always set this in production** | `your-strong-random-key-here` |
| `AMAIMA_EXECUTION_MODE` | Yes | Must be `execution-enabled` for real AI inference | `execution-enabled` |
| `PORT` | No | Port to listen on (default: 8000) | `8000` |
| `DATABASE_URL` | No | PostgreSQL connection string (optional) | `postgresql://user:pass@host/db` |
| `REDIS_URL` | No | Redis connection string (optional) | `redis://host:6379/0` |
| `AMAIMA_ENV` | No | Environment name | `production` |

**Security Warning:** `API_SECRET_KEY` protects the `/v1/query` endpoint. If you do not set it, it defaults to `default_secret_key_for_development`, which is publicly known. Anyone could call your query endpoint and consume your NVIDIA API credits. **Always set a strong, unique value in production.**

**Note:** Endpoints like `/health`, `/v1/models`, `/v1/stats`, and `/v1/capabilities` are public and do not require the API key. Only `/v1/query` requires the `X-API-Key` header.

**Note on CORS:** CORS is currently hardcoded in `main.py` to allow all origins (`allow_origins=["*"]`). To restrict it in production, edit `main.py` directly and replace `"*"` with your frontend domain (e.g., `["https://your-frontend.vercel.app"]`).

---

## Deployment Options

---

### 1. Replit

Replit is the simplest option since the project is already configured to run here. Replit handles infrastructure, SSL, and provides a public URL automatically.

**Deployment Type:** Autoscale (recommended) or Reserved VM

#### Steps

1. **The backend is already running** in Replit at port 8000 with the workflow:
   ```
   cd amaima/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Set your secrets** in the Replit Secrets tab:
   - `NVIDIA_API_KEY` = your NVIDIA NIM API key
   - `API_SECRET_KEY` = a strong random key for production
   - `AMAIMA_EXECUTION_MODE` = `execution-enabled`

3. **Publish the backend** using Replit's Publish feature:
   - Click the **Publish** button in your workspace
   - Choose **Autoscale** deployment (recommended for APIs with variable traffic)
   - Set the run command to:
     ```
     cd amaima/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000
     ```
     (Remove `--reload` for production)
   - Replit will assign a public URL like `https://your-project.replit.app`

4. **Note the public URL** — you'll need this as the `BACKEND_URL` for your frontend deployment on Vercel.

#### Replit-Specific Notes

- Autoscale deployments spin down when idle and spin up on incoming requests. First request after idle may take a few seconds.
- If you need the backend to stay always-on (for WebSocket connections or background tasks), choose **Reserved VM** instead of Autoscale.
- Secrets set in the Secrets tab are automatically available in deployed instances.
- Replit provides free SSL/TLS certificates on all deployed URLs.

---

### 2. Railway

Railway provides simple Git-based deployments with automatic builds, free SSL, and pay-per-use pricing.

**Estimated cost:** ~$5/month for light usage

#### Steps

1. **Sign up** at [railway.app](https://railway.app)

2. **Create a new project** and connect your GitHub repository

3. **Set the root directory** to `amaima/backend`

4. **Configure environment variables** in Railway's dashboard:
   ```
   NVIDIA_API_KEY=nvapi-your-key
   API_SECRET_KEY=your-strong-secret
   AMAIMA_EXECUTION_MODE=execution-enabled
   PORT=8000
   ```

5. **Set the start command** in settings:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

6. **Deploy** — Railway auto-detects Python, installs from `requirements.txt`, and deploys

7. **Get your public URL** from Railway's dashboard (e.g., `https://amaima-backend-production.up.railway.app`)

#### Railway `railway.json` (optional, place in `amaima/backend/`)

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 5
  }
}
```

---

### 3. Render

Render offers straightforward deployment with free tier availability, auto-deploy from Git, and managed infrastructure.

**Estimated cost:** Free tier available, paid starts at $7/month

#### Steps

1. **Sign up** at [render.com](https://render.com)

2. **Create a New Web Service** and connect your GitHub repository

3. **Configure the service:**
   - **Root Directory:** `amaima/backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add environment variables** in the Render dashboard:
   ```
   NVIDIA_API_KEY=nvapi-your-key
   API_SECRET_KEY=your-strong-secret
   AMAIMA_EXECUTION_MODE=execution-enabled
   ```

5. **Deploy** — Render handles the rest and provides a URL like `https://amaima-backend.onrender.com`

#### Render `render.yaml` (optional, place in repo root)

```yaml
services:
  - type: web
    name: amaima-backend
    runtime: python
    rootDir: amaima/backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: NVIDIA_API_KEY
        sync: false
      - key: API_SECRET_KEY
        sync: false
      - key: AMAIMA_EXECUTION_MODE
        value: execution-enabled
      - key: PYTHON_VERSION
        value: 3.11.0
```

#### Render Notes

- Free tier instances spin down after 15 minutes of inactivity. First request after idle takes ~30 seconds.
- For production use, select a paid plan to avoid cold starts.

---

### 4. Fly.io

Fly.io deploys containers close to users worldwide with great performance, and supports persistent storage and WebSockets.

**Estimated cost:** ~$3-7/month for light usage

#### Steps

1. **Install the Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Navigate to the backend directory and launch:**
   ```bash
   cd amaima/backend
   fly launch
   ```

3. **Set secrets:**
   ```bash
   fly secrets set NVIDIA_API_KEY=nvapi-your-key
   fly secrets set API_SECRET_KEY=your-strong-secret
   fly secrets set AMAIMA_EXECUTION_MODE=execution-enabled
   ```

4. **Create a `fly.toml`** in `amaima/backend/`:

   ```toml
   app = "amaima-backend"
   primary_region = "iad"

   [build]
     dockerfile = "Dockerfile"

   [env]
     PORT = "8000"

   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0

   [[http_service.checks]]
     grace_period = "15s"
     interval = "30s"
     method = "GET"
     path = "/health"
     timeout = "10s"

   [[vm]]
     memory = "512mb"
     cpu_kind = "shared"
     cpus = 1
   ```

5. **Deploy:**
   ```bash
   fly deploy
   ```

6. **Get your URL:** `https://amaima-backend.fly.dev`

---

### 5. Google Cloud Run

Cloud Run is a fully managed serverless platform. You only pay for what you use, and it scales to zero when there's no traffic.

**Estimated cost:** Pay-per-request, free tier includes 2 million requests/month

#### Steps

1. **Install the Google Cloud CLI** and authenticate:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Build and push the Docker image:**
   ```bash
   cd amaima/backend
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/amaima-backend
   ```

3. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy amaima-backend \
     --image gcr.io/YOUR_PROJECT_ID/amaima-backend \
     --platform managed \
     --region us-east1 \
     --allow-unauthenticated \
     --port 8000 \
     --memory 512Mi \
     --cpu 1 \
     --min-instances 0 \
     --max-instances 10 \
     --set-env-vars "AMAIMA_EXECUTION_MODE=execution-enabled" \
     --set-secrets "NVIDIA_API_KEY=NVIDIA_API_KEY:latest,API_SECRET_KEY=API_SECRET_KEY:latest"
   ```

4. **Store secrets in Google Secret Manager first:**
   ```bash
   echo -n "nvapi-your-key" | gcloud secrets create NVIDIA_API_KEY --data-file=-
   echo -n "your-strong-secret" | gcloud secrets create API_SECRET_KEY --data-file=-
   ```

5. **Get your URL** from the deployment output (e.g., `https://amaima-backend-xxxxx-ue.a.run.app`)

---

### 6. AWS

AWS offers multiple deployment options. Here are the most practical ones:

#### Option A: AWS App Runner (Simplest)

App Runner is AWS's simplest container deployment service — similar to Cloud Run.

1. **Push your Docker image** to Amazon ECR:
   ```bash
   cd amaima/backend
   aws ecr create-repository --repository-name amaima-backend
   docker build -t amaima-backend .
   docker tag amaima-backend:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/amaima-backend:latest
   docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/amaima-backend:latest
   ```

2. **Create an App Runner service** in the AWS Console:
   - Source: Container registry (ECR)
   - Port: 8000
   - CPU: 1 vCPU, Memory: 2 GB
   - Add environment variables for `NVIDIA_API_KEY`, `API_SECRET_KEY`, `AMAIMA_EXECUTION_MODE`

#### Option B: AWS ECS with Fargate (Production-Grade)

1. **Create an ECS Cluster** and define a task using the existing `Dockerfile`
2. **Set up an Application Load Balancer** pointing to the ECS service
3. **Store secrets** in AWS Secrets Manager and reference them in the task definition
4. **Configure auto-scaling** based on CPU/memory utilization

#### Option C: AWS EC2 (Full Control)

1. **Launch an EC2 instance** (t3.small or larger recommended)
2. **SSH in and set up the environment:**
   ```bash
   sudo apt update && sudo apt install -y python3.11 python3.11-venv
   git clone https://github.com/CreoDAMO/AMAIMA.git
   cd AMAIMA/amaima/backend
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Set environment variables** in `/etc/environment` or use a `.env` file
4. **Run with a process manager** (systemd or supervisor):
   ```bash
   # /etc/systemd/system/amaima.service
   [Unit]
   Description=AMAIMA Backend
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/AMAIMA/amaima/backend
   Environment="NVIDIA_API_KEY=nvapi-your-key"
   Environment="API_SECRET_KEY=your-strong-secret"
   Environment="AMAIMA_EXECUTION_MODE=execution-enabled"
   ExecStart=/home/ubuntu/AMAIMA/amaima/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
5. **Enable and start:**
   ```bash
   sudo systemctl enable amaima
   sudo systemctl start amaima
   ```
6. **Set up Nginx** as a reverse proxy with SSL (use Certbot for free certificates)

---

### 7. Azure Container Apps

Azure Container Apps is Microsoft's serverless container platform.

#### Steps

1. **Install Azure CLI** and log in:
   ```bash
   az login
   ```

2. **Create a resource group and container app environment:**
   ```bash
   az group create --name amaima-rg --location eastus
   az containerapp env create --name amaima-env --resource-group amaima-rg --location eastus
   ```

3. **Build and deploy:**
   ```bash
   cd amaima/backend
   az containerapp up \
     --name amaima-backend \
     --resource-group amaima-rg \
     --environment amaima-env \
     --source . \
     --target-port 8000 \
     --ingress external \
     --env-vars \
       "AMAIMA_EXECUTION_MODE=execution-enabled" \
     --secrets \
       "nvidia-key=nvapi-your-key" \
       "api-secret=your-strong-secret"
   ```

4. **Get your URL** from the output (e.g., `https://amaima-backend.bluesky-xxxxx.eastus.azurecontainerapps.io`)

---

### 8. DigitalOcean App Platform

DigitalOcean's App Platform provides simple deployment from GitHub with affordable pricing.

**Estimated cost:** Starting at $5/month

#### Steps

1. **Sign up** at [digitalocean.com](https://www.digitalocean.com)

2. **Create a new App** and connect your GitHub repository

3. **Configure the app:**
   - **Source Directory:** `amaima/backend`
   - **Type:** Web Service
   - **Run Command:** `uvicorn main:app --host 0.0.0.0 --port 8080`
   - **HTTP Port:** 8080 (DigitalOcean expects 8080 by default; the `--port 8080` flag in the run command matches this)
   - **Instance Size:** Basic ($5/month) or Professional ($12/month)

4. **Add environment variables** in the App settings:
   - Mark `NVIDIA_API_KEY` and `API_SECRET_KEY` as "Encrypted"

5. **Deploy** — DigitalOcean auto-detects Python and installs dependencies

---

### 9. Docker (Self-Hosted / VPS)

Use this method if you have your own server, VPS, or want to run it on any machine with Docker installed.

#### Steps

1. **Build the Docker image:**
   ```bash
   cd amaima/backend
   docker build -t amaima-backend:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name amaima-backend \
     -p 8000:8000 \
     -e NVIDIA_API_KEY=nvapi-your-key \
     -e API_SECRET_KEY=your-strong-secret \
     -e AMAIMA_EXECUTION_MODE=execution-enabled \
     --restart unless-stopped \
     amaima-backend:latest
   ```

3. **Verify it's running:**
   ```bash
   curl http://localhost:8000/health
   ```

#### Docker Compose (recommended for production)

Create a `docker-compose.yml` in `amaima/backend/`:

```yaml
version: "3.9"

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NVIDIA_API_KEY=${NVIDIA_API_KEY}
      - API_SECRET_KEY=${API_SECRET_KEY}
      - AMAIMA_EXECUTION_MODE=execution-enabled
      - PORT=8000
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
```

Run with:
```bash
docker compose up -d
```

#### Production with Nginx Reverse Proxy

For SSL termination, create an Nginx config:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

### 10. Heroku

Heroku provides simple Git-based deployment with a generous free-to-start tier.

#### Steps

1. **Install the Heroku CLI** and log in:
   ```bash
   heroku login
   ```

2. **Create a `Procfile`** in `amaima/backend/`:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. **Create a `runtime.txt`** in `amaima/backend/`:
   ```
   python-3.11.9
   ```

4. **Create the app and deploy:**
   ```bash
   heroku create amaima-backend
   heroku config:set NVIDIA_API_KEY=nvapi-your-key
   heroku config:set API_SECRET_KEY=your-strong-secret
   heroku config:set AMAIMA_EXECUTION_MODE=execution-enabled

   # Deploy using subtree push (since backend is in a subdirectory)
   git subtree push --prefix amaima/backend heroku main
   ```

5. **Get your URL:** `https://amaima-backend-xxxxx.herokuapp.com`

---

## Post-Deployment

After deploying to any platform, verify everything works:

### 1. Health Check

```bash
curl https://YOUR_BACKEND_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "5.0.0",
  "components": {
    "router": {"status": "healthy", "type": "smart_router"},
    "api": {"status": "healthy", "uptime_seconds": 12.5, "query_count": 0}
  }
}
```

### 2. Test AI Inference

```bash
curl -X POST https://YOUR_BACKEND_URL/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_SECRET_KEY" \
  -d '{"query": "What is machine learning?"}'
```

You should get a real AI response with routing metadata.

### 3. Check Available Models

```bash
curl https://YOUR_BACKEND_URL/v1/models
```

### 4. View System Stats

```bash
curl https://YOUR_BACKEND_URL/v1/stats
```

---

## Connecting the Frontend

Once your backend is deployed and you have the public URL, configure your Vercel-hosted frontend to connect to it:

1. **Go to your Vercel project** at [vercel.com](https://vercel.com)
2. **Navigate to Settings > Environment Variables**
3. **Add `BACKEND_URL`** with the value of your deployed backend URL:
   ```
   BACKEND_URL=https://your-backend-url.example.com
   ```
4. **Redeploy** the frontend for the change to take effect

The frontend's API routes (in `src/app/api/`) proxy all requests to the backend using this `BACKEND_URL` variable.

---

## Security Checklist

Before going to production, verify these items:

- [ ] **Changed `API_SECRET_KEY`** from the default development value to a strong, random key (32+ characters)
- [ ] **NVIDIA API key stored as a secret** (not in code or config files)
- [ ] **HTTPS enabled** on your deployment URL (most platforms do this automatically)
- [ ] **CORS origins restricted** in `main.py` — change `allow_origins=["*"]` to only allow your frontend domain (e.g., `allow_origins=["https://your-frontend.vercel.app"]`)
- [ ] **Rate limiting enabled** to prevent abuse
- [ ] **Health check endpoint accessible** for monitoring
- [ ] **No debug mode** in production (`--reload` flag removed from uvicorn command)
- [ ] **Logs monitored** for errors and unusual activity

---

## Platform Comparison

| Platform | Ease of Setup | Free Tier | Auto-Scale | WebSocket Support | Cold Start | Best For |
|---|---|---|---|---|---|---|
| **Replit** | Easiest | Dev only | Yes (Autoscale) | Yes (VM mode) | ~2-5s | Prototyping, small projects |
| **Railway** | Easy | Trial credits | Yes | Yes | ~1-3s | Small to medium projects |
| **Render** | Easy | Yes (limited) | Yes | Yes | ~30s (free) | Budget-friendly production |
| **Fly.io** | Moderate | Yes | Yes | Yes | ~1-2s | Global low-latency APIs |
| **Cloud Run** | Moderate | 2M req/month | Yes | Limited | ~2-5s | Google Cloud users |
| **AWS App Runner** | Moderate | No | Yes | No | ~3-5s | AWS ecosystem users |
| **AWS ECS** | Complex | No | Yes | Yes | None | Enterprise production |
| **Azure Container Apps** | Moderate | Yes | Yes | Yes | ~2-4s | Azure ecosystem users |
| **DigitalOcean** | Easy | No | Yes | Yes | None (paid) | Affordable always-on |
| **Docker/VPS** | Complex | N/A | Manual | Yes | None | Full control needed |
| **Heroku** | Easy | Eco ($5/mo) | Yes | Yes | ~5-10s | Quick deploys |

---

## Recommended Deployment Strategy

For most users, we recommend:

1. **Development:** Replit (already set up and running)
2. **Production Backend:** Railway or Render (simple, affordable, auto-deploy from GitHub)
3. **Production Frontend:** Vercel (already configured with `vercel.json`)

This gives you a fully deployed system for under $10/month with automatic deploys on every GitHub push.
