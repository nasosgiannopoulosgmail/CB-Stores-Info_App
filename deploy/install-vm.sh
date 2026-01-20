#!/bin/bash
# Comprehensive VM Setup Script for Coffee-Berry Stores Management System
# Run this on your Hetzner VM (Ubuntu 22.04 LTS)

set -e

echo "=========================================="
echo "Coffee-Berry Stores System - VM Setup"
echo "=========================================="
echo ""

# Update system
echo "[1/8] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install essential packages
echo "[2/8] Installing essential packages..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    vim \
    ufw \
    fail2ban \
    htop \
    net-tools \
    postgresql-client

# Install Docker
echo "[3/8] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    sudo usermod -aG docker $USER
    rm /tmp/get-docker.sh
    echo "✓ Docker installed successfully"
else
    echo "✓ Docker is already installed"
fi

# Install Docker Compose
echo "[4/8] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✓ Docker Compose installed successfully"
else
    echo "✓ Docker Compose is already installed"
fi

# Configure firewall
echo "[5/8] Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (for internal testing)
sudo ufw allow 443/tcp   # HTTPS (for internal testing)
sudo ufw --force enable
echo "✓ Firewall configured"

# Install Cloudflare Tunnel
echo "[6/8] Installing Cloudflare Tunnel..."
if ! command -v cloudflared &> /dev/null; then
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
    sudo chmod +x /usr/local/bin/cloudflared
    echo "✓ Cloudflare Tunnel installed successfully"
else
    echo "✓ Cloudflare Tunnel is already installed"
fi

# Create application directory structure
echo "[7/8] Creating application directory structure..."
sudo mkdir -p /opt/coffee-berry/{app,data/postgres,data/media,logs,backups}
sudo chown -R $USER:$USER /opt/coffee-berry
echo "✓ Directories created"

# Clone repository
echo "[8/8] Cloning repository..."
if [ ! -d "/opt/coffee-berry/app/.git" ]; then
    cd /opt/coffee-berry/app
    git clone https://github.com/nasosgiannopoulosgmail/CB-Stores-Info_App.git .
    echo "✓ Repository cloned"
else
    echo "✓ Repository already exists, updating..."
    cd /opt/coffee-berry/app
    git pull
fi

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Log out and log back in to apply Docker group changes:"
echo "   exit"
echo "   ssh nasos@192.168.88.75"
echo ""
echo "2. Configure environment variables:"
echo "   cd /opt/coffee-berry/app"
echo "   cp .env.example .env"
echo "   nano .env  # Edit with your settings"
echo ""
echo "3. Start the application:"
echo "   docker-compose build"
echo "   docker-compose run --rm backend alembic upgrade head"
echo "   docker-compose up -d"
echo ""
echo "4. Check logs:"
echo "   docker-compose logs -f"
echo ""
