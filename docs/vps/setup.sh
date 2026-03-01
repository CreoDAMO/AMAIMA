#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# AMAIMA — VPS Setup Script
#
# Tested on: Ubuntu 24.04 LTS (Hetzner CX22, CX32, DigitalOcean, Vultr)
# Minimum: 2GB RAM, 20GB disk
# Recommended: Hetzner CX22 — 4GB RAM, 2 vCPU, 40GB SSD (~$5/mo)
#
# What this script does:
#   1. Updates system packages
#   2. Installs Docker + Docker Compose plugin
#   3. Installs Caddy (automatic HTTPS)
#   4. Clones AMAIMA from GitHub
#   5. Generates strong secrets and writes .env
#   6. Builds and starts the Docker stack
#   7. Configures Caddy to proxy traffic with automatic TLS
#   8. Sets up automatic security updates
#   9. Configures a firewall (UFW)
#
# Usage (run as root on a fresh VPS):
#   curl -fsSL https://raw.githubusercontent.com/CreoDAMO/AMAIMA/main/setup.sh | bash
#
# Or manually:
#   chmod +x setup.sh
#   ./setup.sh
#
# After running, set your environment secrets:
#   nano /root/AMAIMA/.env
#   docker compose up -d --build
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Config — edit these before running ────────────────────────────────────────
DOMAIN="amaima.live"              # Your domain — must point to this VPS IP
REPO="https://github.com/CreoDAMO/AMAIMA.git"
INSTALL_DIR="/root/AMAIMA"
# ─────────────────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; exit 1; }
info()  { echo -e "${BLUE}[→]${NC} $*"; }

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         AMAIMA VPS Setup — $(date +%Y-%m-%d)                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Check root ────────────────────────────────────────────────────────────────
[[ $EUID -ne 0 ]] && error "This script must be run as root. Use: sudo bash setup.sh"

# ── Check RAM ─────────────────────────────────────────────────────────────────
TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM_MB" -lt 1800 ]; then
    error "Insufficient RAM: ${TOTAL_RAM_MB}MB detected. AMAIMA requires minimum 2GB RAM."
fi
log "RAM check passed: ${TOTAL_RAM_MB}MB available"

# ── Step 1: System update ─────────────────────────────────────────────────────
info "Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw \
    unattended-upgrades \
    apt-transport-https \
    debian-keyring \
    debian-archive-keyring
log "System packages updated"

# ── Step 2: Docker ────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    info "Installing Docker..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable --now docker
    log "Docker installed"
else
    log "Docker already installed"
fi

# ── Step 3: Caddy ─────────────────────────────────────────────────────────────
if ! command -v caddy &>/dev/null; then
    info "Installing Caddy..."
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
        gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
        tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null
    apt-get update -qq
    apt-get install -y -qq caddy
    log "Caddy installed"
else
    log "Caddy already installed"
fi

# ── Step 4: Clone repo ────────────────────────────────────────────────────────
if [ -d "$INSTALL_DIR" ]; then
    warn "Directory $INSTALL_DIR exists — pulling latest changes"
    cd "$INSTALL_DIR" && git pull
else
    info "Cloning AMAIMA from $REPO..."
    git clone "$REPO" "$INSTALL_DIR"
    log "Repository cloned to $INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# ── Step 5: Generate secrets and write .env ───────────────────────────────────
if [ ! -f .env ]; then
    info "Generating secrets and writing .env..."

    API_SECRET=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -hex 16)
    WEBHOOK_SECRET=$(openssl rand -hex 16)

    cat > .env << EOF
# ── NVIDIA NIM (REQUIRED — fill this in) ──────────────────────────────────────
NVIDIA_API_KEY=nvapi-REPLACE-WITH-YOUR-KEY

# ── Security (auto-generated) ─────────────────────────────────────────────────
API_SECRET_KEY=${API_SECRET}
JWT_SECRET_KEY=${JWT_SECRET}

# ── Database (auto-generated) ─────────────────────────────────────────────────
DB_PASSWORD=${DB_PASSWORD}

# ── FHE ───────────────────────────────────────────────────────────────────────
SEAL_THREADS=4
FHE_MAX_PAYLOADS=512

# ── Stripe Billing (optional) ─────────────────────────────────────────────────
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
WEBHOOK_INTERNAL_SECRET=${WEBHOOK_SECRET}
EOF

    chmod 600 .env
    log ".env written with auto-generated secrets"
    warn "ACTION REQUIRED: Edit .env and set NVIDIA_API_KEY before starting"
    warn "  nano ${INSTALL_DIR}/.env"
else
    log ".env already exists — skipping secret generation"
fi

# ── Step 6: Configure Caddy ───────────────────────────────────────────────────
info "Configuring Caddy for $DOMAIN..."
mkdir -p /var/log/caddy

cat > /etc/caddy/Caddyfile << EOF
${DOMAIN} {
    reverse_proxy localhost:10000 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
        health_uri /health
        health_interval 30s
        transport http {
            response_header_timeout 300s
        }
    }

    encode gzip

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        -Server
    }

    log {
        output file /var/log/caddy/amaima.access.log {
            roll_size 100mb
            roll_keep 5
        }
    }
}

www.${DOMAIN} {
    redir https://${DOMAIN}{uri} permanent
}
EOF

systemctl enable --now caddy
caddy fmt --overwrite /etc/caddy/Caddyfile
log "Caddy configured"

# ── Step 7: Firewall ──────────────────────────────────────────────────────────
info "Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh          # Port 22
ufw allow http         # Port 80  (Caddy HTTP→HTTPS redirect)
ufw allow https        # Port 443 (Caddy TLS)
ufw --force enable
log "Firewall configured (SSH + HTTP + HTTPS only)"

# ── Step 8: Automatic security updates ───────────────────────────────────────
info "Configuring automatic security updates..."
cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
log "Automatic security updates enabled"

# ── Step 9: Systemd service for auto-restart ─────────────────────────────────
info "Creating systemd service for AMAIMA..."
cat > /etc/systemd/system/amaima.service << EOF
[Unit]
Description=AMAIMA AI Platform
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable amaima.service
log "AMAIMA systemd service created (starts on boot)"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete!                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo ""
echo "  1. Set your NVIDIA API key:"
echo "     nano ${INSTALL_DIR}/.env"
echo "     # Replace 'nvapi-REPLACE-WITH-YOUR-KEY' with your real key"
echo ""
echo "  2. Make sure your domain's DNS A record points to this VPS IP:"
echo "     $(curl -s ifconfig.me 2>/dev/null || echo "YOUR_VPS_IP")"
echo ""
echo "  3. Build and start AMAIMA:"
echo "     cd ${INSTALL_DIR}"
echo "     docker compose up -d --build"
echo ""
echo "  4. Watch the build logs (takes 5-8 minutes first time):"
echo "     docker compose logs -f"
echo ""
echo "  5. Verify everything is working:"
echo "     curl https://${DOMAIN}/health"
echo "     curl https://${DOMAIN}/v1/fhe/status"
echo ""
echo -e "${GREEN}Your site will be live at: https://${DOMAIN}${NC}"
echo -e "${GREEN}Caddy will automatically provision SSL from Let's Encrypt.${NC}"
echo ""
