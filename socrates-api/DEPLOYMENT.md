# Socrates API Deployment Guide

## Overview

This guide covers deploying the Socrates API to production environments. Includes Docker setup, environment configuration, database migration, and operational procedures.

---

## Prerequisites

- Docker & Docker Compose
- Python 3.12+
- PostgreSQL 13+ or SQLite
- Redis 6+ (optional, for caching and rate limiting)
- Claude API key (for LLM features)

---

## Environment Configuration

### Required Environment Variables

Create a `.env.production` file in the project root:

```bash
# Application
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8008
WORKERS=4
RELOAD=False

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/socrates_prod
SOCRATES_DATA_DIR=/data/socrates
PROJECT_DB_PATH=/data/socrates/projects.db

# Authentication
SECRET_KEY=your-secret-key-generate-with-secrets.token_hex(32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["https://app.socrates.dev", "https://www.socrates.dev"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE"]
CORS_ALLOW_HEADERS=["Content-Type", "Authorization"]

# LLM / Claude API
ANTHROPIC_API_KEY=your-api-key
CLAUDE_MODEL=claude-opus-4.5
LLM_TIMEOUT_SECONDS=30

# Redis (optional)
REDIS_URL=redis://redis:6379/0
CACHE_ENABLED=true
RATE_LIMIT_ENABLED=true

# Email (for notifications)
SMTP_HOST=smtp.sendgrid.com
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-key
NOTIFICATION_EMAIL_FROM=api@socrates.dev

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
DATADOG_API_KEY=your-datadog-key
ENABLE_METRICS=true
METRICS_EXPORT_INTERVAL_SECONDS=60

# Feature Flags
ENABLE_GITHUB_SYNC=true
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_WEBHOOKS=true
TESTING_MODE=false
```

### Optional Features

```bash
# GitHub Integration
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-signing-secret
```

---

## Docker Deployment

### Docker Compose (Recommended for Quick Deployment)

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: socrates_prod
      POSTGRES_USER: socrates
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U socrates"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ./socrates-api
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://socrates:${DB_PASSWORD}@postgres:5432/socrates_prod
      REDIS_URL: redis://redis:6379/0
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      SECRET_KEY: ${SECRET_KEY}
      ENV: production
    ports:
      - "8008:8008"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always
    volumes:
      - ./data:/data
      - ./logs:/logs

volumes:
  postgres_data:

networks:
  default:
    name: socrates-network
```

### Dockerfile

Create `socrates-api/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src .
COPY src/socrates_api /app/socrates_api

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs /data && \
    chown -R appuser:appuser /app /data

USER appuser

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8008/health')"

# Run application
CMD ["uvicorn", "socrates_api.main:app", "--host", "0.0.0.0", "--port", "8008", "--workers", "4"]
```

### Deployment Commands

```bash
# Pull latest code
git pull origin main

# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f api

# Stop services
docker-compose -f docker-compose.prod.yml down

# Database migrations (if needed)
docker-compose -f docker-compose.prod.yml exec api \
  alembic upgrade head
```

---

## Kubernetes Deployment

### Kubernetes Manifests

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: socrates-api
  namespace: socrates
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
        image: socrates-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8008
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
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8008
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8008
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: socrates-api-service
  namespace: socrates
spec:
  type: LoadBalancer
  selector:
    app: socrates-api
  ports:
  - port: 80
    targetPort: 8008
```

---

## Database Setup

### PostgreSQL Migration

```bash
# Connect to database
psql postgresql://user:password@localhost:5432/socrates_prod

# Create extensions
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

# Run migrations
alembic upgrade head
```

### SQLite (Development/Small Scale)

```bash
# Initialize database
sqlite3 /data/socrates/projects.db < schema.sql

# Verify
sqlite3 /data/socrates/projects.db ".tables"
```

---

## Monitoring & Logging

### Application Metrics

Configure Prometheus scraping:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'socrates-api'
    static_configs:
      - targets: ['localhost:8008']
    metrics_path: '/metrics'
```

### Log Aggregation

```bash
# ELK Stack (Elasticsearch, Logstash, Kibana)
# Send logs to ELK
export ELASTICSEARCH_HOST=elasticsearch:9200

# Or use cloud solutions
# - Datadog: https://app.datadoghq.com
# - New Relic: https://one.newrelic.com
# - Splunk Cloud: https://www.splunk.com/
```

### Health Checks

```bash
# Check API health
curl http://localhost:8008/health

# Check readiness
curl http://localhost:8008/health/ready

# Get metrics
curl http://localhost:8008/metrics
```

---

## SSL/TLS Configuration

### Using Let's Encrypt with Nginx

Create `nginx/nginx.conf`:

```nginx
upstream socrates_api {
    server api:8008;
}

server {
    listen 80;
    server_name api.socrates.dev;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.socrates.dev;

    ssl_certificate /etc/letsencrypt/live/api.socrates.dev/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.socrates.dev/privkey.pem;

    location / {
        proxy_pass http://socrates_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Backup & Recovery

### Automated Database Backups

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR=/backups
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
docker-compose exec -T postgres pg_dump -U socrates socrates_prod | \
    gzip > $BACKUP_DIR/socrates_db_$DATE.sql.gz

# Retain last 30 days
find $BACKUP_DIR -name "socrates_db_*.sql.gz" -mtime +30 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/socrates_db_$DATE.sql.gz \
    s3://socrates-backups/db/
```

### Restore from Backup

```bash
# Restore PostgreSQL
gunzip < /backups/socrates_db_YYYYMMDD_HHMMSS.sql.gz | \
    docker-compose exec -T postgres psql -U socrates socrates_prod
```

---

## Performance Tuning

### Database Connection Pool

```python
# In environment variables
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_RECYCLE=3600
```

### Caching Configuration

```bash
# Redis cache configuration
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE_MB=256
```

### Rate Limiting

```bash
# Rate limit configuration
RATE_LIMIT_STORAGE=redis
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_AUTH=5/minute
```

---

## Scaling

### Horizontal Scaling (Load Balancing)

```bash
# Using Docker Swarm
docker stack deploy -c docker-compose.prod.yml socrates

# Or Kubernetes (see above)
kubectl scale deployment socrates-api --replicas=5
```

### Auto-scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: socrates-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: socrates-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Troubleshooting

### Common Issues

#### API not starting
```bash
# Check logs
docker-compose logs -f api

# Verify environment variables
env | grep SOCRATES

# Test database connection
psql $DATABASE_URL
```

#### High latency
```bash
# Check metrics
curl http://localhost:8008/metrics | grep http_request_duration

# Monitor database
docker stats postgres

# Check Redis
redis-cli info
```

#### Out of memory
```bash
# Increase container limits
# In docker-compose.prod.yml:
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
```

---

## Production Checklist

- [ ] Environment variables configured securely
- [ ] Database backups automated and tested
- [ ] SSL/TLS certificates configured
- [ ] Monitoring and alerting enabled
- [ ] Log aggregation configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] API keys rotated
- [ ] Health checks passing
- [ ] Load balancing configured
- [ ] Auto-scaling policies set
- [ ] Disaster recovery plan documented
- [ ] Security headers enabled
- [ ] DDoS protection enabled
- [ ] API documentation updated
- [ ] Support contacts configured

---

## Support

- **Production Issues:** incident@socrates.dev
- **Deployment Help:** devops@socrates.dev
- **Documentation:** https://docs.socrates.dev
