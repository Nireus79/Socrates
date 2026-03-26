# Deployment Guide for Socrates

Complete guide to deploying Socrates in development, staging, and production environments.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Setup](#development-setup)
3. [Staging Deployment](#staging-deployment)
4. [Production Deployment](#production-deployment)
5. [Database Migration](#database-migration)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Backup and Recovery](#backup-and-recovery)
8. [Scaling](#scaling)
9. [Troubleshooting](#troubleshooting)
10. [Deployment Checklist](#deployment-checklist)

---

## Quick Start

### Minimum Requirements

- Python 3.9+
- Node.js 16+ (for frontend)
- SQLite (included with Python)
- 2GB RAM
- 1GB disk space

### 5-Minute Setup

```bash
# 1. Clone repository
git clone https://github.com/anthropics/socrates.git
cd socrates

# 2. Set up environment
cp .env.example .env
python setup_env.py

# 3. Install dependencies
pip install -r requirements.txt
cd socrates-frontend && npm install && cd ..

# 4. Start system
python socrates.py

# 5. Access application
# Frontend: http://localhost:5173
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

## Development Setup

### Prerequisites

```bash
# Check Python version
python --version  # >= 3.9

# Check Node version
node --version    # >= 16
npm --version     # >= 8
```

### Installation

```bash
# Create project directory
mkdir socrates && cd socrates
git clone https://github.com/anthropics/socrates.git .

# Create virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate          # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd socrates-frontend
npm install
cd ..

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### Configuration

```bash
# Generate .env file
python setup_env.py

# Or manually create .env
cat > .env << 'EOF'
# API Configuration
SOCRATES_API_PORT=8000
SOCRATES_API_HOST=0.0.0.0
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Database
DATABASE_URL=sqlite:///~/.socrates/api_projects.db

# LLM Configuration
ANTHROPIC_API_KEY=sk-ant-...

# Frontend
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Features
ENABLE_CORS=true
ENABLE_RATE_LIMITING=false

# Logging
LOG_LEVEL=INFO
EOF
```

### Running Development Server

```bash
# Terminal 1: Start API
python socrates.py

# Terminal 2: Start Frontend
cd socrates-frontend
npm run dev

# Access:
# Frontend: http://localhost:5173
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Development Tips

```bash
# Run with debug logging
LOGLEVEL=DEBUG python socrates.py

# Watch for file changes (frontend)
cd socrates-frontend && npm run dev

# Run tests
pytest

# Format code
black backend/src socrates_api tests
ruff check backend/src --fix

# Type checking
mypy backend/src socrates_api
```

---

## Staging Deployment

### Server Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended)
- **CPU**: 2+ cores
- **RAM**: 4GB minimum
- **Storage**: 20GB
- **Network**: Static IP, firewall configured

### Infrastructure Setup

```bash
# 1. Provision server (AWS/GCP/Azure/DigitalOcean)
# 2. SSH into server
ssh ubuntu@your-server-ip

# 3. Install system dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.9 python3.9-venv python3-pip
sudo apt install -y nodejs npm
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y redis-server
sudo apt install -y nginx

# 4. Create application user
sudo useradd -m -s /bin/bash socrates
sudo su - socrates
```

### Application Deployment

```bash
# 1. Clone repository
cd /home/socrates
git clone https://github.com/anthropics/socrates.git
cd socrates

# 2. Set up Python environment
python3.9 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install gunicorn

# 4. Build frontend
cd socrates-frontend
npm install
npm run build
cd ..

# 5. Configure environment
cat > .env << 'EOF'
SOCRATES_API_PORT=8000
DATABASE_URL=postgresql://user:password@localhost:5432/socrates
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENABLE_CORS=true
ENABLE_RATE_LIMITING=true
LOG_LEVEL=INFO
EOF

# 6. Set permissions
sudo chown -R socrates:socrates /home/socrates/socrates
```

### Database Setup

```bash
# 1. Create PostgreSQL database
sudo -u postgres psql

postgres=# CREATE DATABASE socrates;
postgres=# CREATE USER socrates_user WITH PASSWORD 'strong_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE socrates TO socrates_user;
postgres=# \q

# 2. Run migrations
cd /home/socrates/socrates
python -c "from socrates_api.database import LocalDatabase; LocalDatabase().initialize()"

# 3. Create backup user (optional)
sudo -u postgres createuser -P socrates_backup
```

### Systemd Service

```bash
# Create service file
sudo tee /etc/systemd/system/socrates-api.service > /dev/null << 'EOF'
[Unit]
Description=Socrates API Server
After=network.target postgresql.service

[Service]
Type=notify
User=socrates
WorkingDirectory=/home/socrates/socrates
Environment="PATH=/home/socrates/socrates/venv/bin"
ExecStart=/home/socrates/socrates/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    socrates_api.main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable socrates-api
sudo systemctl start socrates-api
sudo systemctl status socrates-api
```

### Nginx Configuration

```bash
# Create nginx config
sudo tee /etc/nginx/sites-available/socrates > /dev/null << 'EOF'
upstream socrates_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        root /home/socrates/socrates/socrates-frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://socrates_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/socrates /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Verify Staging Deployment

```bash
# Check services
sudo systemctl status socrates-api
sudo systemctl status nginx
sudo systemctl status postgresql

# Check logs
sudo journalctl -u socrates-api -n 50 -f

# Test API
curl https://your-domain.com/api/health

# Test frontend
curl https://your-domain.com/
```

---

## Production Deployment

### High-Availability Setup

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │   (Nginx/HAProxy)│
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼──┐            ┌───▼──┐            ┌───▼──┐
    │API-1 │            │API-2 │            │API-N │
    └──────┘            └──────┘            └──────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼──────┐      ┌─────▼─────┐      ┌──────▼──┐
    │PostgreSQL│      │PostgreSQL │      │  Redis  │
    │ Primary  │      │ Standby   │      │ Cluster │
    └──────────┘      └───────────┘      └─────────┘
        │
        └──── Replication ────┘
```

### Kubernetes Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: socrates-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: socrates-api
  template:
    metadata:
      labels:
        app: socrates-api
    spec:
      containers:
      - name: api
        image: socrates:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: socrates-secrets
              key: database-url
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: socrates-secrets
              key: api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: socrates-api-service
spec:
  type: LoadBalancer
  selector:
    app: socrates-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt gunicorn

# Create non-root user
RUN useradd -m -u 1000 socrates
USER socrates

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["gunicorn", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "socrates_api.main:app"]
```

### Build and Push

```bash
# Build image
docker build -t socrates:latest .

# Tag for registry
docker tag socrates:latest your-registry.com/socrates:latest

# Push to registry
docker push your-registry.com/socrates:latest

# Deploy to Kubernetes
kubectl apply -f kubernetes/deployment.yaml
```

---

## Database Migration

### SQLite to PostgreSQL

```bash
# 1. Export SQLite data
sqlite3 ~/.socrates/api_projects.db ".dump" > backup.sql

# 2. Create PostgreSQL database
createdb socrates
psql socrates < backup.sql

# 3. Update DATABASE_URL
export DATABASE_URL=postgresql://user:password@localhost:5432/socrates

# 4. Run migrations
python -m alembic upgrade head

# 5. Verify data
psql socrates -c "SELECT count(*) FROM users;"
```

---

## Monitoring and Logging

### Application Logging

```bash
# Configure logging in .env
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/socrates/app.log

# View logs
tail -f /var/log/socrates/app.log
```

### System Monitoring

```bash
# CPU and Memory
top -p $(pgrep -f gunicorn | tr '\n' ',')

# Disk usage
df -h /home/socrates

# Network connections
netstat -an | grep :8000
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database connection
psql $DATABASE_URL -c "SELECT 1;"

# Redis connection
redis-cli ping
```

### Monitoring Tools

**Recommended**:
- Prometheus + Grafana (metrics)
- ELK Stack (logs)
- Sentry (error tracking)
- DataDog (APM)

---

## Backup and Recovery

### Automated Backups

```bash
# Create backup script
cat > /home/socrates/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/home/socrates/backups
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
pg_dump $DATABASE_URL > $BACKUP_DIR/postgres_$DATE.sql

# Backup application data
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /home/socrates/socrates

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /home/socrates/backup.sh

# Schedule with cron
crontab -e
# Add: 0 2 * * * /home/socrates/backup.sh
```

### Recovery

```bash
# Restore database
psql $DATABASE_URL < /home/socrates/backups/postgres_20260326.sql

# Restore application
tar -xzf /home/socrates/backups/app_20260326.tar.gz -C /

# Restart services
sudo systemctl restart socrates-api
```

---

## Scaling

### Vertical Scaling

```bash
# Increase server resources:
# - CPU: 2 cores → 4+ cores
# - RAM: 4GB → 8GB+
# - Storage: 20GB → 100GB+
```

### Horizontal Scaling

```bash
# 1. Deploy multiple API instances
# 2. Set up load balancer (Nginx/HAProxy)
# 3. Use shared PostgreSQL database
# 4. Configure Redis cluster
# 5. Use CDN for frontend
```

### Database Scaling

```bash
# Read replicas
ALTER SYSTEM SET max_wal_senders = 10;
SELECT pg_reload_conf();

# Connection pooling
# Use PgBouncer between app and database
```

---

## Troubleshooting

### Common Issues

**Port Already in Use**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

**Database Connection Failed**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection string
psql $DATABASE_URL -c "SELECT 1;"
```

**High Memory Usage**:
```bash
# Check memory
free -h

# Restart service
sudo systemctl restart socrates-api
```

**SSL Certificate Errors**:
```bash
# Renew certificate
sudo certbot renew --force-renewal

# Check certificate
sudo certbot certificates
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Code reviewed and tested
- [ ] Environment variables configured
- [ ] Database backups created
- [ ] SSL certificates valid
- [ ] Firewall rules configured
- [ ] Load balancer configured
- [ ] Monitoring setup complete
- [ ] Alert thresholds set

### Deployment

- [ ] Pull latest code
- [ ] Build application
- [ ] Run database migrations
- [ ] Deploy to staging first
- [ ] Run smoke tests
- [ ] Deploy to production
- [ ] Monitor for errors
- [ ] Verify all features working

### Post-Deployment

- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Verify backups working
- [ ] Document any issues
- [ ] Notify team of completion
- [ ] Schedule post-deployment review

---

**Last Updated**: 2026-03-26
**Version**: 1.0.0
