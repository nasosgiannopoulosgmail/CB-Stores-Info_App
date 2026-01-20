# VM Installation Instructions

## Quick Start - One Command Installation

Connect to your VM and run this single command:

```bash
ssh nasos@192.168.88.75
```

Once connected, run:

```bash
curl -fsSL https://raw.githubusercontent.com/nasosgiannopoulosgmail/CB-Stores-Info_App/main/deploy/quick-install.sh | bash
```

OR if the above doesn't work, copy and paste this entire block:

```bash
# Complete installation script
sudo apt-get update && \
sudo apt-get install -y curl wget git && \
curl -fsSL https://get.docker.com | sudo sh && \
sudo usermod -aG docker $USER && \
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4) && \
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
sudo chmod +x /usr/local/bin/docker-compose && \
sudo ufw default deny incoming && \
sudo ufw default allow outgoing && \
sudo ufw allow 22/tcp && \
sudo ufw allow 80/tcp && \
sudo ufw allow 443/tcp && \
sudo ufw --force enable && \
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared && \
sudo mv /tmp/cloudflared /usr/local/bin/cloudflared && \
sudo chmod +x /usr/local/bin/cloudflared && \
sudo mkdir -p /opt/coffee-berry/{app,data/postgres,data/media,logs,backups} && \
sudo chown -R $USER:$USER /opt/coffee-berry && \
cd /opt/coffee-berry/app && \
git clone https://github.com/nasosgiannopoulosgmail/CB-Stores-Info_App.git . && \
echo "✓ Installation complete! Please log out and log back in, then continue with: cd /opt/coffee-berry/app"
```

## Step-by-Step Manual Installation

### 1. Connect to Your VM

```bash
ssh nasos@192.168.88.75
```

You'll be prompted for your password.

### 2. Run the Installation Script

Once connected, run:

```bash
cd ~
git clone https://github.com/nasosgiannopoulosgmail/CB-Stores-Info_App.git temp-setup
cd temp-setup
chmod +x deploy/install-vm.sh
sudo ./deploy/install-vm.sh
```

### 3. Reconnect After Installation

**IMPORTANT**: Log out and log back in to apply Docker group permissions:

```bash
exit
ssh nasos@192.168.88.75
```

### 4. Configure Environment

```bash
cd /opt/coffee-berry/app
cp .env.example .env
nano .env
```

Edit these essential variables:
- `POSTGRES_PASSWORD` - Set a strong password
- `SECRET_KEY` - Generate a random secret key
- `VITE_GOOGLE_MAPS_API_KEY` - Your Google Maps API key
- `DATABASE_URL` - Usually keep default unless you changed POSTGRES_PASSWORD

### 5. Build and Start Services

```bash
cd /opt/coffee-berry/app
docker-compose build
docker-compose run --rm backend alembic upgrade head
docker-compose up -d
```

### 6. Verify Installation

```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs -f

# Test backend health
curl http://localhost:8000/health
```

### 7. Setup Cloudflare Tunnel (Optional)

If you haven't already, configure Cloudflare Tunnel:

```bash
cd /opt/coffee-berry/app
sudo mkdir -p /etc/cloudflared
# Copy your credentials.json to /etc/cloudflared/
sudo cp deploy/cloudflare-tunnel.yml /etc/cloudflared/config.yml
# Edit config.yml with your domains
sudo nano /etc/cloudflared/config.yml
# Setup as systemd service
sudo cp deploy/cloudflare-tunnel.service /etc/systemd/system/cloudflared.service
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

## Troubleshooting

### Docker Permission Denied
If you get "permission denied" errors with Docker:
```bash
# Log out and log back in
exit
ssh nasos@192.168.88.75
```

### Port Already in Use
If ports are already in use:
```bash
# Check what's using the ports
sudo netstat -tulpn | grep -E ':(80|443|8000|3000)'
# Stop conflicting services or change ports in docker-compose.yml
```

### Git Not Found
If git is not installed:
```bash
sudo apt-get update
sudo apt-get install -y git
```

### Firewall Issues
If you can't connect after firewall setup:
```bash
# Allow your IP through firewall
sudo ufw allow from YOUR_IP_ADDRESS to any port 22
```

## Next Steps

After installation:
1. Import your existing data (see `scripts/README.md`)
2. Configure Cloudflare Tunnel
3. Set up automated backups (see `deploy/backup.sh`)
4. Configure monitoring and logging

## Support

For issues, check:
- `README.md` - General documentation
- `deploy/README.md` - Deployment guide
- `scripts/README.md` - Data import guide
