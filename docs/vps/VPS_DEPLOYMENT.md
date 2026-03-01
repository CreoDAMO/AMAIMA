# AMAIMA — VPS Deployment Guide

Deploy AMAIMA on your own VPS for full control, lowest cost, and zero platform memory limits.

**Recommended:** Hetzner CX22 — €4.51/month, 4GB RAM, 2 vCPU, 40GB SSD.
That's 4× more RAM than Render Starter for 1/5 the price.

---

## Contents

1. [Why VPS](#why-vps)
2. [Server Requirements](#server-requirements)
3. [Quick Start (5 minutes)](#quick-start)
4. [Manual Setup](#manual-setup)
5. [Files in this Package](#files-in-this-package)
6. [Environment Variables](#environment-variables)
7. [Deploying Updates](#deploying-updates)
8. [SSL / HTTPS](#ssl--https)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)
11. [VPS Provider Comparison](#vps-provider-comparison)

---

## Why VPS

| Issue on PaaS | On a VPS |
|---|---|
| Next.js OOM during build (512MB limit) | 4GB available — build completes in ~5 min |
| TenSEAL install fails (no build-time env vars) | Docker build runs with full root access |
| Frontend SIGTERM every 7 min (memory pressure) | 4GB keeps all processes resident |
| `tenseal==0.3.14` yanked — CI breaks | You control the build environment entirely |
| Platform costs $25-75/mo for 2GB | Hetzner CX22: ~$5/mo for 4GB |

---

## Server Requirements

| Spec | Minimum | Recommended |
|---|---|---|
| RAM | 2GB | 4GB |
| vCPU | 1 | 2 |
| Disk | 20GB | 40GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| Open ports | 22, 80, 443 | 22, 80, 443 |

**Why 4GB?**

| Component | RAM at Runtime |
|---|---|
| Next.js (`next start`) | ~300MB |
| FastAPI (2 uvicorn workers) | ~400MB |
| FHE context pool (CKKS + BFV) | ~150MB |
| TenSEAL C++ extension | included above |
| PostgreSQL | ~100MB |
| OS + Docker overhead | ~200MB |
| **Total** | **~1.15GB steady state** |
| **Build peak** (Next.js compile) | **~500MB** |

4GB gives comfortable headroom for FHE operations, traffic spikes, and future growth.

---

## Quick Start

### 1. Provision a VPS

Get a Hetzner CX22 at [hetzner.com/cloud](https://www.hetzner.com/cloud):
- Image: Ubuntu 24.04
- Location: closest to your users
- Add your SSH key during provisioning

Point your domain's **A record** to the VPS IP before proceeding (DNS propagation takes ~5 min on Cloudflare, up to 24h on other providers).

### 2. Run the setup script

```bash
ssh root@YOUR_VPS_IP

# Option A: One-shot automated setup
curl -fsSL https://raw.githubusercontent.com/CreoDAMO/AMAIMA/main/setup.sh | bash

# Option B: Manual (copy setup.sh to the server first)
chmod +x setup.sh && ./setup.sh
```

The setup script:
- Installs Docker, Caddy, Git
- Clones the AMAIMA repo
- Auto-generates strong secrets for `API_SECRET_KEY`, `JWT_SECRET_KEY`, `DB_PASSWORD`
- Writes `.env` (you only need to add your NVIDIA key)
- Configures Caddy for automatic HTTPS
- Sets up a firewall (SSH + HTTP + HTTPS only)
- Creates a systemd service so AMAIMA starts on boot

### 3. Add your NVIDIA key

```bash
nano /root/AMAIMA/.env
# Replace: nvapi-REPLACE-WITH-YOUR-KEY
# With:    nvapi-your-actual-key
```

Get a key at [build.nvidia.com](https://build.nvidia.com) → API Keys.

### 4. Build and start

```bash
cd /root/AMAIMA
docker compose up -d --build
```

First build takes 5-8 minutes (Next.js compilation + TenSEAL C++ install). Watch progress:

```bash
docker compose logs -f
```

### 5. Verify

```bash
# Backend health
curl https://YOUR_DOMAIN/health

# FHE status (should show available: true)
curl https://YOUR_DOMAIN/v1/fhe/status

# Run all FHE demos
curl https://YOUR_DOMAIN/v1/fhe/demo
```

---

## Manual Setup

If you prefer to set up each component individually:

### Install Docker

```bash
apt-get update
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker
```

### Install Caddy

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
    gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
    tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install caddy
```

### Clone and configure

```bash
git clone https://github.com/CreoDAMO/AMAIMA.git /root/AMAIMA
cd /root/AMAIMA
cp .env.example .env
chmod 600 .env
nano .env   # Set NVIDIA_API_KEY and verify other values
```

### Configure Caddy

Copy `Caddyfile` from this package to `/etc/caddy/Caddyfile` and edit the domain:

```bash
cp Caddyfile /etc/caddy/Caddyfile
nano /etc/caddy/Caddyfile   # Replace amaima.live with your domain
systemctl reload caddy
```

### Firewall

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable
```

### Build and start

```bash
cd /root/AMAIMA
docker compose up -d --build
```

---

## Files in This Package

| File | Purpose |
|---|---|
| `Dockerfile` | Production image — python:3.10, unconditional tenseal, OOM-safe Next.js build |
| `docker-compose.yml` | App + PostgreSQL stack with healthchecks and resource limits |
| `.env.example` | Template for all environment variables — copy to `.env` |
| `start.sh` | Process supervisor — starts backend, waits for health, starts frontend, monitors both |
| `next.config.js` | Memory-safe Next.js config — API proxy rewrites, security headers |
| `Caddyfile` | Automatic HTTPS reverse proxy — replace domain name and copy to `/etc/caddy/Caddyfile` |
| `setup.sh` | One-shot VPS provisioning script |
| `deploy.sh` | Pull latest code + rebuild + health-check verification |

All files go in the root of your AMAIMA repo. `start.sh` and `next.config.js` also need to be placed at their respective paths inside the repo structure.

---

## Environment Variables

The `.env` file lives in the repo root alongside `docker-compose.yml`.

| Variable | Required | How to Set |
|---|---|---|
| `NVIDIA_API_KEY` | **Yes** | Get at [build.nvidia.com](https://build.nvidia.com) |
| `API_SECRET_KEY` | **Yes** | `openssl rand -hex 32` |
| `JWT_SECRET_KEY` | **Yes** | `openssl rand -hex 32` |
| `DB_PASSWORD` | **Yes** | `openssl rand -hex 16` |
| `SEAL_THREADS` | No | Number of vCPUs (CX22=2, CX32=4) |
| `FHE_MAX_PAYLOADS` | No | LRU store cap, default 512 |
| `STRIPE_SECRET_KEY` | No | Only needed for billing features |
| `STRIPE_WEBHOOK_SECRET` | No | Only needed for Stripe webhooks |

The following are set automatically in `docker-compose.yml` and do not need to be in `.env`:
- `DATABASE_URL` — constructed from `DB_PASSWORD`
- `AMAIMA_EXECUTION_MODE` — always `execution-enabled`
- `FHE_ENABLED` — always `true`
- `BACKEND_URL` — always `http://localhost:8000`
- `PORT` — always `10000`
- `NODE_OPTIONS` — set in `start.sh`

---

## Deploying Updates

### Routine update (new code)

```bash
cd /root/AMAIMA
./deploy.sh
```

This pulls the latest code, builds a new Docker image, restarts the stack, and verifies health.

### Force full rebuild (after Dockerfile changes)

```bash
./deploy.sh --no-cache
```

### Manual update steps

```bash
cd /root/AMAIMA
git pull
docker compose down
docker compose up -d --build
docker compose logs -f
```

### Rollback to previous commit

```bash
cd /root/AMAIMA
git log --oneline -10   # find the commit to roll back to
git checkout <commit-hash>
docker compose up -d --build
```

---

## SSL / HTTPS

Caddy handles TLS automatically — no certbot, no cron jobs, no manual renewal.

**Requirements:**
- Your domain's A record must point to the VPS IP
- Ports 80 and 443 must be open (UFW config above does this)
- Caddy must be running: `systemctl status caddy`

**Verify certificate:**
```bash
curl -I https://YOUR_DOMAIN/health
# Should show: HTTP/2 200
```

**Check Caddy logs:**
```bash
journalctl -u caddy -f
tail -f /var/log/caddy/amaima.access.log
```

**Reload Caddy after config changes:**
```bash
caddy fmt --overwrite /etc/caddy/Caddyfile
systemctl reload caddy
```

---

## Monitoring

### Check all container status

```bash
docker compose ps
```

### Follow all logs

```bash
docker compose logs -f
```

### Backend logs only

```bash
docker compose logs -f amaima | grep -v "GET /health"
```

### Resource usage

```bash
docker stats
```

### FHE pool health

```bash
curl -s http://localhost:8000/v1/fhe/status | python3 -m json.tool
```

### Platform metrics

```bash
curl -s http://localhost:8000/v1/stats | python3 -m json.tool
```

### Disk usage

```bash
df -h
docker system df
```

### Cleanup old Docker images

```bash
docker image prune -f
docker system prune -f  # WARNING: removes stopped containers and unused networks too
```

---

## Troubleshooting

### Build fails with "JavaScript heap out of memory"

This should not happen on a 2GB+ VPS, but if it does:

```bash
# Check available memory during build
free -h

# The Dockerfile sets NODE_OPTIONS=--max-old-space-size=256 for the build stage
# If still failing, temporarily increase swap:
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
docker compose up -d --build
```

### TenSEAL not loading

```bash
# Check build log
docker compose logs amaima | grep -i tenseal

# Should see: TenSEAL loaded — SEAL_THREADS=X
# If not, check:
docker compose exec amaima python3 -c "import tenseal; print(tenseal.__version__)"
```

### Backend not starting

```bash
docker compose logs amaima | tail -50
# Look for Python import errors or missing env vars
```

### FHE endpoints returning 503

```bash
curl http://localhost:8000/v1/fhe/status
# Check: "available": true
# If false: FHE_ENABLED is not set or TenSEAL failed to import
```

### Database connection refused

```bash
docker compose ps db
# Should be "healthy"
# If not: docker compose logs db
```

### Caddy not issuing certificate

```bash
journalctl -u caddy -n 50
# Common causes:
# - DNS A record not pointing to this IP yet (wait for propagation)
# - Port 80/443 not open in firewall: ufw status
# - Domain typo in Caddyfile
```

### Container restarts in a loop

```bash
docker compose ps
# Check RESTARTS column

docker compose logs amaima --tail=100
# Find the crash reason
```

---

## VPS Provider Comparison

| Provider | Plan | RAM | vCPU | Disk | Cost/mo | Notes |
|---|---|---|---|---|---|---|
| **Hetzner** | CX22 | 4GB | 2 | 40GB SSD | ~$5 | Best value. EU + US data centers |
| **Hetzner** | CX32 | 8GB | 4 | 80GB SSD | ~$12 | Recommended for FHE-heavy workloads |
| **Vultr** | Regular 4GB | 4GB | 2 | 80GB SSD | $24 | Global locations |
| **DigitalOcean** | Basic 4GB | 4GB | 2 | 80GB SSD | $24 | Managed PG addon available |
| **Linode/Akamai** | Linode 4GB | 4GB | 2 | 80GB SSD | $24 | Good support |
| **OVH** | B2-7 | 7GB | 2 | 50GB | $19 | EU-based |

**Hetzner CX22 is the recommended default** — 4× the RAM of Render Starter for $5/mo vs $7/mo, full Docker access, and a clean Ubuntu 24.04 image.

### Selecting a data center location

Choose the region closest to the majority of your users:
- **US East coast** → Hetzner Ashburn (ASH) or DigitalOcean NYC
- **US West coast** → Hetzner Hillsboro (HIL) or DigitalOcean SFO
- **Europe** → Hetzner Nuremberg (NBG) or Falkenstein (FSN)
- **Asia-Pacific** → Hetzner Singapore (SIN) or Vultr Tokyo
