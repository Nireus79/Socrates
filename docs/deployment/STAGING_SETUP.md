# Staging Environment Setup Guide

## Objective
Set up a production-like staging environment for final testing before production deployment.

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Staging Environment                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Frontend     │    │ API Backend  │    │ PostgreSQL   │  │
│  │ (React)      │───▶│ (FastAPI)    │───▶│ Database     │  │
│  │ Port 3000    │    │ Port 8000    │    │ Port 5432    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         △                                                    │
│         │                                                    │
│  ┌──────┴──────────────────────────────────────────────┐   │
│  │            Nginx Reverse Proxy (443)                │   │
│  │     HTTPS, SSL, Rate Limiting, Caching              │   │
│  └───────────────────────────────────────────────────────┐ │
│         │                                                │  │
│         ▼                                                │  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Redis Cache (Port 6379)                     │  │
│  │          Sessions & Caching                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Monitoring                                          │  │
│  │  - Application Logs: /var/log/socrates/             │  │
│  │  - Metrics: Port 9090                               │  │
│  │  - Health Checks: Automated                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Hardware Requirements

### Minimum
- CPU: 2 cores
- RAM: 4GB
- Storage: 50GB SSD
- Network: 100Mbps

### Recommended
- CPU: 4 cores
- RAM: 8GB
- Storage: 100GB SSD
- Network: 1Gbps

## Step 1: Server Setup

### 1.1 Create Linux Server
```bash
# Using Ubuntu 22.04 LTS (recommended)
# AWS EC2, DigitalOcean, Linode, etc.
# Key pair: socrates-staging.pem
# Security group: Allow 80, 443, 22 inbound
```

### 1.2 Initial Server Configuration
```bash
# Connect to server
ssh -i socrates-staging.pem ubuntu@your-staging-server.com

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    git \
    curl \
    wget \
    vim \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nodejs \
    npm \
    nginx \
    docker.io \
    docker-compose \
    certbot \
    python3-certbot-nginx

# Verify installations
python3.11 --version
node --version
npm --version
psql --version
redis-server --version
docker --version
```

### 1.3 Create Application User
```bash
# Create non-root user for application
sudo useradd -m -s /bin/bash socrates
sudo usermod -aG docker socrates
sudo usermod -aG sudo socrates

# Create application directory
sudo mkdir -p /opt/socrates
sudo mkdir -p /var/log/socrates
sudo mkdir -p /var/lib/socrates/data
sudo mkdir -p /etc/socrates

# Set permissions
sudo chown -R socrates:socrates /opt/socrates
sudo chown -R socrates:socrates /var/log/socrates
sudo chown -R socrates:socrates /var/lib/socrates
sudo chown socrates:socrates /etc/socrates
sudo chmod 700 /etc/socrates

# Switch to socrates user
sudo su - socrates
```

## Step 2: Database Setup

### 2.1 PostgreSQL Configuration
```bash
# Switch to postgres user
sudo su - postgres

# Create database and user
psql << EOF
CREATE USER socrates_user WITH PASSWORD 'staging_password_123';
CREATE DATABASE socrates_db OWNER socrates_user;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE socrates_db TO socrates_user;

-- Enable required extensions
\c socrates_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Verify
\du
\l
EOF

# Exit postgres user
exit
```

### 2.2 PostgreSQL Backup Configuration
```bash
# As socrates user
sudo su - socrates

# Create backup directory
mkdir -p ~/backups/db

# Set up automated backups (cron)
crontab -e
# Add line:
# 0 2 * * * pg_dump -U socrates_user socrates_db > ~/backups/db/socrates_db_$(date +\%Y\%m\%d_\%H\%M\%S).sql

# Verify cron job
crontab -l
```

## Step 3: Application Deployment

### 3.1 Clone Repository
```bash
# As socrates user
cd /opt/socrates
git clone https://github.com/yourusername/socrates.git .
git checkout staging  # or main branch

# Verify clone
ls -la
git status
```

### 3.2 Create Python Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt
pip install -e .
pip install -e ./socrates-cli
pip install -e ./socrates-api
pip install -e ".[dev]"

# Verify installation
python --version
pip list | grep socrates
```

### 3.3 Environment Configuration
```bash
# Copy example configuration
cp .env.example .env.staging

# Edit configuration
nano .env.staging

# Set critical variables:
# CLAUDE_API_KEY=sk-your-actual-key
# DATABASE_URL=postgresql://socrates_user:staging_password_123@localhost/socrates_db
# REDIS_URL=redis://localhost:6379/0
# SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
# ENVIRONMENT=staging
# DEBUG=false
# LOG_LEVEL=INFO
```

### 3.4 Database Migrations
```bash
# Run migrations
cd /opt/socrates
source venv/bin/activate

alembic upgrade head

# Verify migration
alembic current

# Create test data (optional)
python scripts/seed_test_data.py
```

## Step 4: Frontend Setup

### 4.1 Install Dependencies
```bash
cd /opt/socrates/socrates-frontend
npm ci  # Use ci instead of install for consistency

# Verify
npm list react
npm list typescript
```

### 4.2 Build Frontend
```bash
npm run build

# Verify build
ls -la build/
file build/index.html
```

### 4.3 Configure Environment
```bash
# Create .env for production build
cat > .env.production << EOF
REACT_APP_API_URL=https://your-staging-domain.com/api
REACT_APP_ENV=staging
REACT_APP_DEBUG=false
EOF
```

## Step 5: Systemd Services

### 5.1 Create API Service
```bash
# Create service file
sudo nano /etc/systemd/system/socrates-api.service

# Content should be similar to socrates-api.service in repo
# Edit paths to match your setup
```

### 5.2 Create Frontend Service (optional - nginx serves static)
```bash
sudo nano /etc/systemd/system/socrates-frontend.service

# Configure to serve static files via nginx
```

### 5.3 Enable Services
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services on boot
sudo systemctl enable socrates-api
sudo systemctl enable redis-server
sudo systemctl enable postgresql
sudo systemctl enable nginx

# Start services
sudo systemctl start socrates-api
sudo systemctl start redis-server
sudo systemctl start postgresql
sudo systemctl start nginx

# Verify services
sudo systemctl status socrates-api
sudo systemctl status redis-server
sudo systemctl status postgresql
```

## Step 6: Nginx Configuration

### 6.1 Copy Nginx Config
```bash
# Copy and customize nginx config
sudo cp nginx.conf /etc/nginx/sites-available/socrates
sudo ln -s /etc/nginx/sites-available/socrates /etc/nginx/sites-enabled/socrates

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 6.2 SSL Certificate Setup
```bash
# Using Let's Encrypt Certbot
sudo certbot certonly --nginx -d your-staging-domain.com

# Update nginx config to use certificate
sudo nano /etc/nginx/nginx.conf
# Update paths:
# ssl_certificate /etc/letsencrypt/live/your-staging-domain.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/your-staging-domain.com/privkey.pem;

# Reload nginx
sudo systemctl reload nginx

# Test HTTPS
curl -I https://your-staging-domain.com
```

### 6.3 Auto-Renewal Setup
```bash
# Verify certbot renewal works
sudo certbot renew --dry-run

# This should be in crontab already from certbot setup
sudo crontab -l | grep certbot
```

## Step 7: Monitoring & Logging

### 7.1 Configure Application Logs
```bash
# Verify log directory exists
ls -la /var/log/socrates/

# Check log rotation
sudo nano /etc/logrotate.d/socrates

# Content:
# /var/log/socrates/*.log {
#     daily
#     rotate 14
#     compress
#     delaycompress
#     notifempty
#     create 0640 socrates socrates
#     sharedscripts
#     postrotate
#         systemctl reload socrates-api > /dev/null 2>&1 || true
#     endscript
# }
```

### 7.2 Health Check Setup
```bash
# Test health endpoint
curl https://your-staging-domain.com/health

# Set up automated health checks
crontab -e
# Add:
# */5 * * * * curl -f https://your-staging-domain.com/health || \
#   systemctl restart socrates-api
```

### 7.3 Monitoring Dashboards
```bash
# Enable metrics endpoint
# Verify in .env:
# ENABLE_METRICS=true

# Access metrics
curl http://localhost:9090/metrics

# Set up monitoring tool (Prometheus, Grafana, etc.)
# Optional: Advanced monitoring setup
```

## Step 8: Testing

### 8.1 Smoke Tests
```bash
# Test API
curl -X GET https://your-staging-domain.com/api/health
curl -X GET https://your-staging-domain.com/api/status

# Test frontend
curl -I https://your-staging-domain.com/

# Test database
psql -U socrates_user -d socrates_db -c "SELECT 1;"

# Test Redis
redis-cli ping
```

### 8.2 Functional Tests
```bash
# Login test
curl -X POST https://your-staging-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'

# Project creation test
curl -X POST https://your-staging-domain.com/api/projects \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "description": "test"}'

# Export test
curl -X GET https://your-staging-domain.com/api/projects/{id}/export?format=zip \
  -H "Authorization: Bearer TOKEN"

# GitHub test (requires token)
curl -X POST https://your-staging-domain.com/api/projects/{id}/publish-to-github \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"repo_name": "test", "private": true}'
```

### 8.3 Load Testing (Optional)
```bash
# Install load testing tool
pip install locust

# Create load test script
cat > loadtest.py << 'EOF'
from locust import HttpUser, task, between

class SocratesUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health_check(self):
        self.client.get("/api/health")

    @task
    def project_list(self):
        self.client.get("/api/projects")
EOF

# Run load test
locust -f loadtest.py --host=https://your-staging-domain.com -u 10 -r 1
```

## Step 9: Backup & Disaster Recovery

### 9.1 Configure Backups
```bash
# Database backup
mkdir -p /backups/database
sudo chown socrates:socrates /backups/database

# Set up backup script
cat > ~/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U socrates_user socrates_db | gzip > $BACKUP_DIR/socrates_db_$DATE.sql.gz
# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete
EOF

chmod +x ~/backup.sh

# Add to crontab
crontab -e
# 0 2 * * * ~/backup.sh
```

### 9.2 Test Restore Procedure
```bash
# Create test database
psql -U postgres -c "CREATE DATABASE socrates_db_restore;"

# Restore from backup
gunzip < /backups/database/socrates_db_20240101_020000.sql.gz | \
  psql -U socrates_user -d socrates_db_restore

# Verify restore
psql -U socrates_user -d socrates_db_restore -c "SELECT COUNT(*) FROM users;"

# Drop test database
psql -U postgres -c "DROP DATABASE socrates_db_restore;"
```

## Step 10: Pre-Production Verification

### 10.1 Performance Baseline
```bash
# Record baseline metrics
echo "Performance Baseline - $(date)" >> /var/log/socrates/baseline.txt
ps aux | grep socrates-api >> /var/log/socrates/baseline.txt
free -h >> /var/log/socrates/baseline.txt
df -h >> /var/log/socrates/baseline.txt

# Repeat tests and compare
```

### 10.2 Security Verification
```bash
# Check security headers
curl -I https://your-staging-domain.com | grep X-

# Verify HTTPS
curl -v https://your-staging-domain.com 2>&1 | grep TLS

# Check firewall
sudo ufw status

# Verify SSH keys only (no password login)
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
```

### 10.3 Access Control
```bash
# Verify proper file permissions
ls -la /opt/socrates/
ls -la /etc/socrates/

# Verify user permissions
id socrates
groups socrates
```

## Checklist

- [ ] Server created and configured
- [ ] PostgreSQL database running
- [ ] Redis cache running
- [ ] Application user created
- [ ] Python environment set up
- [ ] Dependencies installed
- [ ] Database migrations completed
- [ ] Environment variables configured
- [ ] Frontend built successfully
- [ ] Systemd services created and enabled
- [ ] Nginx configured with SSL
- [ ] Health checks passing
- [ ] Smoke tests successful
- [ ] Functional tests successful
- [ ] Logging configured
- [ ] Backups configured
- [ ] Monitoring set up
- [ ] Performance baseline recorded
- [ ] Security verified
- [ ] Team access verified

## Troubleshooting

### Application won't start
```bash
# Check logs
sudo journalctl -u socrates-api -n 50
tail -f /var/log/socrates/api.log

# Check service status
sudo systemctl status socrates-api

# Manually start to see errors
cd /opt/socrates
source venv/bin/activate
python -m socrates_api.main
```

### Database connection error
```bash
# Test connection
psql -U socrates_user -d socrates_db -c "SELECT 1;"

# Check credentials in .env
grep DATABASE_URL /etc/socrates/.env.staging

# Check PostgreSQL is running
sudo systemctl status postgresql
```

### Nginx 502 error
```bash
# Check if API is running
curl http://localhost:8000/health

# Check nginx error log
sudo tail -f /var/log/nginx/error.log

# Reload nginx
sudo systemctl reload nginx
```

## Next Steps

1. **Run GitHub Testing Guide** (GITHUB_TESTING_GUIDE.md)
2. **Run Deployment Checklist** (DEPLOYMENT_CHECKLIST.md)
3. **Get team approval for production deployment**
4. **Schedule production deployment window**

---

**Setup Date:** [Date]
**Setup By:** [Name]
**Status:** ✅ Complete / ❌ Incomplete
