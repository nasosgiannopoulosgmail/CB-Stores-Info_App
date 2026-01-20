#!/bin/bash
# One-command installation script
# Run this directly on your VM via SSH

set -e

echo "=========================================="
echo "Coffee-Berry Stores System - Quick Install"
echo "=========================================="
echo ""

# Step 1: Update and install essentials
echo "[Step 1/6] Updating system..."
sudo apt-get update
sudo apt-get install -y curl wget git

# Step 2: Install Docker
echo "[Step 2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    sudo usermod -aG docker $USER
    rm /tmp/get-docker.sh
    echo "✓ Docker installed"
fi

# Step 3: Install Docker Compose
echo "[Step 3/6] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✓ Docker Compose installed"
fi

# Step 4: Setup firewall
echo "[Step 4/6] Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
echo "✓ Firewall configured"

# Step 5: Install Cloudflare Tunnel
echo "[Step 5/6] Installing Cloudflare Tunnel..."
if ! command -v cloudflared &> /dev/null; then
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
    sudo chmod +x /usr/local/bin/cloudflared
    echo "✓ Cloudflare Tunnel installed"
fi

# Step 6: Clone repository and setup
echo "[Step 6/6] Setting up application..."
sudo mkdir -p /opt/coffee-berry/{app,data/postgres,data/media,logs,backups}
sudo chown -R $USER:$USER /opt/coffee-berry

if [ ! -d "/opt/coffee-berry/app/.git" ]; then
    cd /opt/coffee-berry/app
    git clone https://github.com/nasosgiannopoulosgmail/CB-Stores-Info_App.git .
    echo "✓ Repository cloned"
else
    cd /opt/coffee-berry/app
    git pull
    echo "✓ Repository updated"
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "IMPORTANT: Please log out and log back in for Docker group to take effect!"
echo ""
echo "Next steps after reconnecting:"
echo "  cd /opt/coffee-berry/app"
echo "  cp .env.example .env"
echo "  nano .env"
echo "  docker-compose build"
echo "  docker-compose run --rm backend alembic upgrade head"
echo "  docker-compose up -d"
echo ""
