# Deployment Guide - Coffee-Berry Stores Management System

This guide covers the deployment of the Coffee-Berry Stores Management System on Hetzner VMs with Cloudflare Tunnel.

## Prerequisites

- Hetzner account with active VM
- Ubuntu 22.04 LTS on the VM
- Cloudflare account with domain
- SSH access to the Hetzner VM

## Phase 1: Initial VM Setup

### 1.1 Connect to Your Hetzner VM

```bash
ssh root@your-vm-ip
```

### 1.2 Run the Setup Script

```bash
# Upload the setup script to your VM
scp deploy/hetzner-setup.sh root@your-vm-ip:/tmp/

# On the VM, run:
chmod +x /tmp/hetzner-setup.sh
/tmp/hetzner-setup.sh
```

### 1.3 Log Out and Log Back In

This ensures Docker group permissions are applied:
```bash
exit
ssh root@your-vm-ip
```

## Phase 2: Cloudflare Tunnel Setup

### 2.1 Create Cloudflare Tunnel

1. Go to Cloudflare Dashboard → Zero Trust → Networks → Tunnels
2. Click "Create a tunnel"
3. Choose "Cloudflared" and give it a name (e.g., `coffee-berry-tunnel`)
4. Download the credentials file and save it to your VM at `/etc/cloudflared/credentials.json`

### 2.2 Configure Tunnel

```bash
# Create config directory
sudo mkdir -p /etc/cloudflared

# Copy credentials file to /etc/cloudflared/credentials.json
# (Upload it from your local machine)

# Copy tunnel configuration
sudo cp deploy/cloudflare-tunnel.yml /etc/cloudflared/config.yml

# Edit the configuration with your domains
sudo nano /etc/cloudflared/config.yml
```

**Important:** Update the hostnames in `cloudflare-tunnel.yml`:
- `stores.yourdomain.com` → Your frontend domain
- `api.stores.yourdomain.com` → Your API domain

### 2.3 Configure DNS

In Cloudflare DNS settings, add:
- **CNAME** record: `stores` → `your-tunnel-id.cfargotunnel.com`
- **CNAME** record: `api.stores` → `your-tunnel-id.cfargotunnel.com`

### 2.4 Install as Systemd Service

```bash
# Copy service file
sudo cp deploy/cloudflare-tunnel.service /etc/systemd/system/cloudflared.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Check status
sudo systemctl status cloudflared
```

## Phase 3: Deploy Application

### 3.1 Clone/Upload Application Code

```bash
# Create app directory
sudo mkdir -p /opt/coffee-berry/app
cd /opt/coffee-berry/app

# Either clone from git or upload files
# Example: Upload from local machine
# scp -r /path/to/app/* root@your-vm-ip:/opt/coffee-berry/app/
```

### 3.2 Configure Environment Variables

```bash
cd /opt/coffee-berry/app

# Create .env file
cat > .env << EOF
# Database
POSTGRES_DB=coffee_berry
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password-here

# Backend
SECRET_KEY=your-very-secure-secret-key-here
ENVIRONMENT=production
CORS_ORIGINS=https://stores.yourdomain.com

# Frontend
VITE_API_URL=https://api.stores.yourdomain.com
VITE_GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# Redis (optional)
REDIS_URL=redis://redis:6379/0
EOF

chmod 600 .env
```

### 3.3 Build and Start Services

```bash
cd /opt/coffee-berry/app

# Build images
docker-compose build

# Run database migrations
docker-compose run --rm backend alembic upgrade head

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 3.4 Verify Services

```bash
# Check service status
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:80
```

## Phase 4: SSL/TLS Configuration

Cloudflare Tunnel automatically handles SSL/TLS termination. Ensure:

1. **Cloudflare SSL/TLS Mode**: Set to "Full" or "Full (strict)" in Cloudflare Dashboard
2. **Automatic HTTPS Rewrites**: Enable in Cloudflare Dashboard → SSL/TLS → Edge Certificates
3. **Always Use HTTPS**: Enable redirect in Cloudflare Dashboard → SSL/TLS → Edge Certificates

## Maintenance

### Backup Database

```bash
# Create backup script
cat > /opt/coffee-berry/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/coffee-berry/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U postgres coffee_berry > $BACKUP_DIR/db_backup_$DATE.sql
# Keep only last 7 days
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +7 -delete
EOF

chmod +x /opt/coffee-berry/backup.sh

# Add to crontab for daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/coffee-berry/backup.sh") | crontab -
```

### Update Application

```bash
cd /opt/coffee-berry/app

# Pull latest changes (if using git)
git pull

# Rebuild and restart
docker-compose build
docker-compose run --rm backend alembic upgrade head
docker-compose up -d
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

## Security Notes

1. **Firewall**: Only ports 22 (SSH), 80, 443 are open. PostgreSQL (5432) and Redis (6379) are only accessible internally.
2. **Passwords**: Always change default passwords in `.env` file
3. **SSH Keys**: Use SSH key authentication instead of passwords
4. **Cloudflare Tunnel**: Provides secure access without exposing ports publicly
5. **Updates**: Regularly update system packages and Docker images

## Troubleshooting

### Cloudflare Tunnel Not Connecting

```bash
# Check tunnel status
sudo systemctl status cloudflared

# View tunnel logs
sudo journalctl -u cloudflared -f

# Test tunnel manually
sudo cloudflared tunnel --config /etc/cloudflared/config.yml run
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U postgres -d coffee_berry
```

### Backend Not Starting

```bash
# Check backend logs
docker-compose logs backend

# Verify environment variables
docker-compose exec backend env | grep DATABASE

# Check if migrations ran
docker-compose exec backend alembic current
```

## Support

For issues or questions, refer to the main documentation or contact the development team.
