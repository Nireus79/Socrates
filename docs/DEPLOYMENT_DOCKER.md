# Docker Deployment Guide

Complete guide to deploying Socrates using Docker and Docker Compose, including configuration, networking, scaling, and troubleshooting.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Compose Setup](#docker-compose-setup)
3. [Configuration](#configuration)
4. [Networking](#networking)
5. [Data Persistence](#data-persistence)
6. [Scaling](#scaling)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)

---

## Quick Start

### Minimum Setup (Local Development)

```bash
# Clone repository
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Copy environment file
cp deployment/configurations/.env.example .env

# Edit .env and add your Anthropic API key
nano .env  # or use your preferred editor
# Set: ANTHROPIC_API_KEY=sk-ant-...

# Start services
docker-compose -f deployment/docker/docker-compose.yml up -d

# Wait for services (30-60 seconds)
docker-compose logs -f

# Access applications
# Frontend: http://localhost:3000 (via Nginx)
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Verify Services

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs socrates-api
docker-compose logs socrates-frontend
docker-compose logs postgres
docker-compose logs redis

# Test API
curl http://localhost:8000/health

# Test database connection
docker-compose exec postgres psql -U socrates -d socrates -c "SELECT version();"
```

---

## Docker Compose Setup

### Services Architecture

```yaml
# deployment/docker/docker-compose.yml

version: '3.8'

services:
  # Nginx reverse proxy
  nginx:
    ports:
      - "80:80"        # HTTP traffic
      - "443:443"      # HTTPS (optional)
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - socrates-api
      - socrates-frontend

  # PostgreSQL database
  postgres:
    environment:
      POSTGRES_USER: socrates
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: socrates
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"    # Internal only in production

  # Redis cache
  redis:
    ports:
      - "6379:6379"    # Internal only in production
    volumes:
      - redis_data:/data

  # ChromaDB vector database
  chromadb:
    ports:
      - "8000:8000"    # Internal only in production
    volumes:
      - chromadb_data:/data/chroma

  # Python API server
  socrates-api:
    build:
      context: .
      dockerfile: deployment/docker/Dockerfile.api
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      DATABASE_URL: postgresql://socrates:${DB_PASSWORD}@postgres:5432/socrates
      REDIS_URL: redis://redis:6379
      CHROMADB_URL: http://chromadb:8000
      ENVIRONMENT: ${ENVIRONMENT:-development}
    depends_on:
      - postgres
      - redis
      - chromadb
    volumes:
      - ./socratic_system:/app/socratic_system
    ports:
      - "8000:8000"    # Internal, accessed via Nginx

  # React frontend
  socrates-frontend:
    build:
      context: ./socrates-frontend
      dockerfile: Dockerfile
    environment:
      REACT_APP_API_URL: http://localhost:8000
    volumes:
      - ./socrates-frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"    # Internal, accessed via Nginx

volumes:
  postgres_data:
  redis_data:
  chromadb_data:

networks:
  default:
    name: socrates-network
```

### Service Definitions

**PostgreSQL**:
- Database for project and user data
- Persistence: `/var/lib/postgresql/data`
- Health check: Pg_isready every 10s

**Redis**:
- In-memory cache for sessions and rate limiting
- Persistence: `/data` (RDB snapshots)
- Health check: PING command every 10s

**ChromaDB**:
- Vector database for embeddings and RAG
- Persistence: `/data/chroma`
- Health check: HTTP GET /api/v1/heartbeat

**API Server**:
- FastAPI application
- Depends on: PostgreSQL, Redis, ChromaDB
- Port: 8000 (internal), accessed via Nginx
- Environment variables: API keys, database URLs

**Frontend**:
- React/Vite development server
- Depends on: API Server
- Port: 5173 (internal), served via Nginx
- Build-time variables: API endpoint configuration

**Nginx**:
- Reverse proxy and load balancer
- Ports: 80 (HTTP), 443 (HTTPS)
- Routes: /api → API, / → Frontend
- SSL/TLS termination point

---

## Configuration

### Environment Variables

**Required Variables**:

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
ENVIRONMENT=development  # or production
```

**Optional Variables**:

```bash
# Database
DB_PASSWORD=socrates_dev_password
DB_USER=socrates
DB_NAME=socrates
DB_HOST=postgres
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# ChromaDB
CHROMADB_URL=http://chromadb:8000

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4  # Number of gunicorn workers

# Frontend
REACT_APP_API_URL=http://localhost:8000
REACT_APP_LOG_LEVEL=debug

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/socrates/app.log

# Security
DEBUG_MODE=false
CORS_ORIGINS=https://app.socrates.local

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Timeouts
REQUEST_TIMEOUT=30
SHUTDOWN_TIMEOUT=30
```

### Configuration Files

**API Configuration** (`socratic_system/config.py`):

```python
from pydantic import BaseSettings
from pathlib import Path

class SocratesConfig(BaseSettings):
    # API Configuration
    anthropic_api_key: str
    claude_model: str = "claude-haiku-4-5-20251001"

    # Database
    database_url: str = "postgresql://socrates:password@postgres:5432/socrates"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Vector Database
    chromadb_url: str = "http://chromadb:8000"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # Security
    debug_mode: bool = False
    jwt_secret: str = ...

    class Config:
        env_file = ".env"
        case_sensitive = False
```

**Nginx Configuration** (`deployment/docker/nginx/nginx.conf`):

```nginx
upstream api {
    server socrates-api:8000;
}

upstream frontend {
    server socrates-frontend:5173;
}

server {
    listen 80;
    server_name localhost;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 30s;
    }

    # API documentation
    location /docs {
        proxy_pass http://api;
        proxy_set_header Host $host;
    }

    location /redoc {
        proxy_pass http://api;
        proxy_set_header Host $host;
    }
}
```

---

## Networking

### Service-to-Service Communication

```
Browser → Nginx (localhost:80)
           ├─→ /api → API Server (http://socrates-api:8000)
           └─→ / → Frontend (http://socrates-frontend:5173)

API Server → PostgreSQL (postgresql://postgres:5432)
          → Redis (redis://redis:6379)
          → ChromaDB (http://chromadb:8000)
```

### Port Mapping

| Service | Internal Port | External Port | Access |
|---------|---|---|---|
| Nginx | 80 | 80 | Public |
| Nginx | 443 | 443 | Public (HTTPS) |
| API | 8000 | N/A | Via Nginx |
| Frontend | 5173 | N/A | Via Nginx |
| PostgreSQL | 5432 | 5432 | Localhost only |
| Redis | 6379 | 6379 | Localhost only |
| ChromaDB | 8000 | N/A | Internal only |

### Hostname Resolution

Inside Docker network, services reach each other using service names:

```python
# From API container, connect to PostgreSQL
DATABASE_URL = "postgresql://postgres:5432/socrates"
# postgres resolves to socrates-postgres container

# From API container, connect to Redis
REDIS_URL = "redis://redis:6379"
# redis resolves to socrates-redis container
```

### DNS Configuration

**Development**:
```bash
# Add to /etc/hosts (macOS/Linux)
127.0.0.1 localhost
127.0.0.1 api.local
127.0.0.1 app.local

# Access applications
curl http://api.local/docs
curl http://app.local
```

**Production** (with real domain):
```nginx
# Update nginx.conf
server_name socrates-api.yourdomain.com;
```

---

## Data Persistence

### Volumes

```yaml
volumes:
  postgres_data:        # PostgreSQL data
  redis_data:          # Redis snapshots
  chromadb_data:       # Vector embeddings
  socrates_logs:       # Application logs
```

### Backup Strategy

**PostgreSQL Backup**:

```bash
# Full database backup
docker-compose exec postgres pg_dump \
  -U socrates \
  socrates > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose exec -T postgres psql \
  -U socrates \
  socrates < backup_20260502.sql

# Automated daily backup
# Add to crontab
0 2 * * * docker-compose -f ~/Socrates/docker-compose.yml exec -T postgres pg_dump -U socrates socrates > ~/backups/socrates_$(date +\%Y\%m\%d).sql
```

**Data Directory Volumes**:

```bash
# Backup volumes
docker run --rm \
  -v socrates_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volumes
docker run --rm \
  -v socrates_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

### Cleanup

**Remove unused volumes**:

```bash
# List unused volumes
docker volume ls -f dangling=true

# Remove specific volume
docker volume rm socrates_postgres_data

# Cleanup all
docker system prune -a --volumes
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)

```yaml
# docker-compose.yml with scaling
services:
  socrates-api:
    deploy:
      replicas: 3      # Run 3 instances
    environment:
      - WORKER_CLASS=uvicorn.workers.UvicornWorker
      - WORKERS=4      # 4 workers per instance
```

**With Nginx load balancing**:

```nginx
upstream api {
    least_conn;  # Load balancing strategy
    server socrates-api-1:8000;
    server socrates-api-2:8000;
    server socrates-api-3:8000;
}
```

### Vertical Scaling (Resources)

```yaml
services:
  socrates-api:
    resources:
      limits:
        cpus: '2'      # Max 2 CPU cores
        memory: 2G     # Max 2GB RAM
      reservations:
        cpus: '1'      # Guaranteed 1 CPU
        memory: 1G     # Guaranteed 1GB RAM
```

### Database Scaling

**Read Replicas**:

```yaml
services:
  postgres-primary:
    environment:
      POSTGRES_REPLICATION_MODE: master

  postgres-replica:
    image: postgres:14
    environment:
      POSTGRES_REPLICATION_MODE: replica
      REPLICATION_USER: replicator
      REPLICATION_PASSWORD: ${REPLICATION_PASSWORD}
    depends_on:
      - postgres-primary
```

**Connection Pooling** (pgBouncer):

```yaml
services:
  pgbouncer:
    image: pgbouncer:1.16
    environment:
      DATABASES_HOST: postgres
      DATABASES_PORT: 5432
      DATABASES_USER: socrates
      DATABASES_PASSWORD: ${DB_PASSWORD}
      DATABASES_DBNAME: socrates
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 1000
      DEFAULT_POOL_SIZE: 25
```

---

## Monitoring

### Health Checks

```yaml
services:
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U socrates"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  socrates-api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Logging

```bash
# View logs
docker-compose logs -f socrates-api

# Filter logs
docker-compose logs socrates-api | grep ERROR

# Follow specific service
docker-compose logs -f postgres

# Dump logs to file
docker-compose logs > logs_$(date +%Y%m%d).txt
```

### Metrics Collection (Prometheus)

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./deployment/docker/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
```

**Prometheus Configuration** (`prometheus.yml`):

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'socrates-api'
    static_configs:
      - targets: ['socrates-api:8000']
        metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

```bash
# Check logs
docker-compose logs socrates-api

# Common issues:
# - Port already in use
# - Missing environment variables
# - Database connection failed

# Solution: Start one service at a time
docker-compose up -d postgres
docker-compose up -d redis
docker-compose up -d chromadb
docker-compose up -d socrates-api
```

#### 2. Database Connection Errors

```bash
# Test database connectivity
docker-compose exec api psql -h postgres -U socrates -d socrates -c "SELECT 1;"

# Check PostgreSQL logs
docker-compose logs postgres

# Verify credentials
echo $DB_PASSWORD

# Reset database
docker-compose down -v
docker-compose up -d postgres
# Wait 30 seconds for initialization
```

#### 3. API Returns 502 Bad Gateway

```bash
# Check if API is running
docker-compose ps socrates-api

# Check API logs
docker-compose logs socrates-api

# Verify API is healthy
docker-compose exec socrates-api curl http://localhost:8000/health

# Restart API
docker-compose restart socrates-api
```

#### 4. Frontend Can't Connect to API

```bash
# Check API is accessible
curl http://localhost:8000/health

# Check Nginx configuration
docker-compose exec nginx cat /etc/nginx/nginx.conf

# Check frontend API URL
docker-compose logs socrates-frontend | grep API_URL
```

#### 5. Out of Disk Space

```bash
# Check disk usage
docker system df

# Clean up
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

### Debugging Commands

```bash
# Inspect container
docker-compose exec socrates-api /bin/bash

# View environment
docker-compose exec socrates-api env | grep API

# Check network
docker-compose exec socrates-api ping postgres

# Monitor resources
docker stats

# View container details
docker inspect socrates-api

# Check port bindings
docker port socrates-api
```

---

## Production Deployment

### Pre-Deployment Checklist

- ✅ Set `ENVIRONMENT=production` in `.env`
- ✅ Set `DEBUG_MODE=false` in `.env`
- ✅ Change all default passwords
- ✅ Set strong JWT secret
- ✅ Configure SSL/TLS certificates
- ✅ Set up database backups
- ✅ Set up monitoring and alerts
- ✅ Configure logging to persistent storage
- ✅ Test database recovery procedure
- ✅ Set up auto-restart policies

### Production docker-compose.yml

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro  # SSL certificates
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - socrates-api

  postgres:
    image: postgres:14-alpine
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - /data/postgres:/var/lib/postgresql/data
      - /backups/postgres:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - /data/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  chromadb:
    image: chromadb/chroma:latest
    restart: always
    volumes:
      - /data/chromadb:/data/chroma
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 3

  socrates-api:
    image: socrates-api:latest
    restart: always
    environment:
      ENVIRONMENT: production
      DEBUG_MODE: "false"
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379
      CHROMADB_URL: http://chromadb:8000
      LOG_LEVEL: INFO
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      chromadb:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G

  prometheus:
    image: prom/prometheus:latest
    restart: always
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - /data/prometheus:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    restart: always
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - /data/grafana:/var/lib/grafana
```

### Secrets Management

**Using Docker Secrets** (Swarm mode):

```bash
# Create secrets
echo "${ANTHROPIC_API_KEY}" | docker secret create anthropic_api_key -
echo "${DB_PASSWORD}" | docker secret create db_password -

# Reference in compose
services:
  socrates-api:
    secrets:
      - anthropic_api_key
      - db_password
    environment:
      ANTHROPIC_API_KEY_FILE: /run/secrets/anthropic_api_key
```

**Using External Secrets** (Production):

```bash
# Store in AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault
# Then inject at runtime

docker-compose up -d \
  -e ANTHROPIC_API_KEY=$(aws secretsmanager get-secret-value --secret-id anthropic-key --query SecretString --output text) \
  -e DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id db-password --query SecretString --output text)
```

---

**Last Updated**: May 2026
**Version**: 1.3.3
