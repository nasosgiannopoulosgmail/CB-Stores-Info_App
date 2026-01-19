#!/bin/bash
# Hetzner VM Setup Script for Coffee-Berry Stores Management System
# This script should be run on a fresh Ubuntu 22.04 LTS Hetzner VM

set -e

echo "=========================================="
echo "Coffee-Berry Stores System - VM Setup"
echo "=========================================="

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install essential packages
echo "Installing essential packages..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    vim \
    ufw \
    fail2ban \
    htop \
    net-tools

# Install Docker
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed successfully"
else
    echo "Docker is already installed"
fi

# Install Docker Compose
echo "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed successfully"
else
    echo "Docker Compose is already installed"
fi

# Configure firewall
echo "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (for internal testing)
sudo ufw allow 443/tcp   # HTTPS (for internal testing)
sudo ufw --force enable
echo "Firewall configured"

# Install Cloudflare Tunnel (cloudflared)
echo "Installing Cloudflare Tunnel..."
if ! command -v cloudflared &> /dev/null; then
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
    sudo chmod +x /usr/local/bin/cloudflared
    echo "Cloudflare Tunnel installed successfully"
else
    echo "Cloudflare Tunnel is already installed"
fi

# Create application directory structure
echo "Creating application directory structure..."
sudo mkdir -p /opt/coffee-berry/{app,data/postgres,data/media,logs}
sudo chown -R $USER:$USER /opt/coffee-berry

# Create systemd service directory if needed
sudo mkdir -p /etc/systemd/system

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Log out and log back in to apply Docker group changes"
echo "2. Configure Cloudflare Tunnel (see deploy/cloudflare-tunnel.yml)"
echo "3. Copy application files to /opt/coffee-berry/app"
echo "4. Run 'docker-compose up -d' to start services"
echo ""
echo "Note: PostgreSQL port 5432 is not exposed externally."
echo "Access is only through Cloudflare Tunnel."
echo ""
