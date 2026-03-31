# Docker Setup Guide for Socrates

Complete guide to running Socrates with Docker.

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### Start Everything
```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### Access Services
- **Socrates API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ChromaDB**: http://localhost:8001
- **PostgreSQL**: localhost:5432 (pgAdmin at port 5050 in dev mode)
- **Redis**: localhost:6379

## Services Overview

### Main Services

**api** - Socrates API Server
- Port: 8000
- Service for all platform functionality
- Requires: PostgreSQL, Redis, ChromaDB

**postgres** - PostgreSQL Database
- Port: 5432
- Stores projects, users, knowledge
- Data persisted in `postgres_data` volume

**redis** - Redis Cache
- Port: 6379
- Caches sessions, rate limits, embeddings
- Data persisted in `redis_data` volume

**chromadb** - Vector Database
- Port: 8001
- Stores embeddings for RAG
- Data persisted in `chromadb_data` volume

### Development Services (Optional)

Run with `--profile dev`:
- **pgadmin** - PostgreSQL management (port 5050)
- **redis-commander** - Redis management (port 8002)

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail 100
```

### Access Service Shells
```bash
# PostgreSQL
docker-compose exec postgres psql -U socrates -d socrates

# Redis
docker-compose exec redis redis-cli

# API container
docker-compose exec api bash
```

### Database Management
```bash
# Create database backup
docker-compose exec postgres pg_dump -U socrates socrates > backup.sql

# Restore database
docker-compose exec -T postgres psql -U socrates socrates < backup.sql

# Reset database (careful!)
docker-compose exec postgres dropdb -U socrates socrates
docker-compose exec postgres createdb -U socrates socrates
```

### View Resource Usage
```bash
# Memory and CPU
docker stats

# Disk usage
docker system df
```

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Database
POSTGRES_PASSWORD=your_secure_password

# Admin Tools (dev only)
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=secure_password

# Socrates Config
SOCRATES_LOG_LEVEL=INFO
SOCRATES_LOG_FILE=/data/socrates.log
```

### Custom Configuration

Modify `docker-compose.yml`:

```yaml
api:
  environment:
    SOCRATES_API_PORT: 9000  # Change port
    SOCRATES_LOG_LEVEL: DEBUG  # More verbose logging
```

## Development Workflow

### 1. Start Services
```bash
docker-compose up -d
```

### 2. Make Code Changes
Edit files locally (they persist in containers via volumes)

### 3. Rebuild After Changes
```bash
# Rebuild API service
docker-compose build api

# Apply changes
docker-compose up -d api
```

### 4. View Logs
```bash
docker-compose logs -f api
```

### 5. Run Tests
```bash
docker-compose exec api pytest tests/
```

## Production Deployment

### Security Hardening
1. Change all default passwords
2. Use strong API key
3. Configure CORS properly
4. Use HTTPS with reverse proxy
5. Enable authentication
6. Set resource limits

### Example Production Compose
```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
  restart_policy:
    condition: on-failure
    delay: 5s
    max_attempts: 3
```

### Reverse Proxy (Nginx)
```nginx
upstream socrates {
    server api:8000;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://socrates;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### API Won't Start
```bash
# Check logs
docker-compose logs api

# Common issues:
# 1. Missing ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY="your-key"

# 2. Port already in use
# Change port in docker-compose.yml:
# ports:
#   - "9000:8000"

# 3. Database connection
docker-compose down -v  # Reset everything
docker-compose up -d
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Reset and reinitialize
docker-compose stop postgres
docker-compose rm -f postgres
docker-compose up -d postgres
```

### Out of Memory
```bash
# Clean up unused images/containers
docker system prune

# Check disk space
df -h

# Increase Docker memory allocation
# (Docker Desktop settings)
```

### Slow Performance
```bash
# Check resource usage
docker stats

# View logs for errors
docker-compose logs -f api

# Consider increasing allocations
# or spreading services across multiple machines
```

## Cleanup

### Stop All Services
```bash
docker-compose stop
```

### Remove Containers (Keep Data)
```bash
docker-compose down
```

### Remove Everything (Including Data)
```bash
docker-compose down -v
```

### Remove Images
```bash
docker-compose down --rmi all
```

## Advanced Topics

### Custom Images
Build your own image:
```bash
docker build -t my-socrates:latest .
```

### Volume Management
Mount local code:
```yaml
api:
  volumes:
    - ./socrates-api:/app/socrates-api
    - ./socratic-core:/app/socratic-core
```

### Network Configuration
```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge

services:
  api:
    networks:
      - frontend
      - backend
```

### Health Checks
Already configured, but customize with:
```yaml
api:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

## Performance Tuning

### PostgreSQL Optimization
```yaml
postgres:
  command:
    - "postgres"
    - "-c"
    - "max_connections=200"
    - "-c"
    - "shared_buffers=256MB"
```

### Redis Optimization
```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### API Server
```yaml
api:
  environment:
    GUNICORN_WORKERS: 4
    GUNICORN_THREADS: 2
```

## Monitoring

### Basic Monitoring
```bash
# Watch resource usage
watch -n 1 'docker stats --no-stream'

# Check service health
docker-compose ps

# View container logs in real-time
docker-compose logs -f --tail 50
```

### Prometheus Integration (Optional)
Add to docker-compose.yml for metrics collection:
```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## Support & Troubleshooting

- **Logs**: `docker-compose logs <service>`
- **Shell Access**: `docker-compose exec <service> bash`
- **Issues**: https://github.com/themsou/Socrates/issues
- **Documentation**: See [INSTALL.md](INSTALL.md) and [ARCHITECTURE.md](ARCHITECTURE.md)

## Next Steps

1. **Access API**: http://localhost:8000/docs
2. **Create Project**: `curl -X POST http://localhost:8000/projects ...`
3. **Use CLI**: `socrates project list`
4. **Deploy**: See production configuration above
