# Docker Deployment Guide for Socrates

## Quick Start: Docker Compose

```bash
# 1. Clone and setup
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# 2. Create environment file
cp deployment/configurations/.env.example .env.docker
# Edit .env.docker with your API key and settings

# 3. Build and start
docker-compose up -d

# 4. Verify all services are healthy
docker-compose ps
# Status should show: healthy/running

# 5. Test API
curl http://localhost:8000/health/detailed
```

---

## Docker Images: Two Options

### Option 1: Build Locally (docker-compose.yml)
```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    # API starts building from Dockerfile
    # Suitable for: Development, customization
```

**When to use**:
- Local development
- Custom modifications
- Testing before pushing to hub

**Build time**: ~5-10 minutes (first time), ~2 minutes (cached)

### Option 2: Use Pre-Built from Docker Hub (Production)
```yaml
services:
  api:
    image: nireus79/socrates-api:latest
    # Uses pre-built image from Docker Hub
    # Suitable for: Quick deployments, production
```

**When to use**:
- Production deployments
- No local changes needed
- Want consistent environments

**Startup time**: < 1 minute (just pull + start)

---

## Docker Compose Configuration

### Services
```yaml
services:
  api:              # FastAPI backend
  web:              # Nginx reverse proxy + React frontend
  redis:            # Optional: distributed cache
  postgres:         # Optional: production database
```

### Environment Setup

**Required**:
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx      # Your Claude API key
ENVIRONMENT=production              # development/staging/production
```

**Optional**:
```env
SOCRATES_API_HOST=0.0.0.0          # 0.0.0.0 for Docker (listens on all interfaces)
SOCRATES_API_PORT=8000              # Container port
REDIS_URL=redis://redis:6379        # For distributed cache
DATABASE_URL=postgresql://...       # For PostgreSQL (else SQLite)
MAX_CONCURRENT_GENERATIONS=5        # Concurrency limit
LOG_LEVEL=INFO                      # DEBUG/INFO/WARNING/ERROR
```

### Volumes
```yaml
volumes:
  socrates_data:      # Persistent: projects.db, vector_db, knowledge
  socrates_logs:      # Persistent: application logs
  postgres_data:      # Persistent: PostgreSQL data (if used)
  redis_data:         # Persistent: Redis snapshots (if used)
```

### Networks
```yaml
networks:
  socrates_network:
    driver: bridge
    # All services communicate via service names:
    # api:8000, redis:6379, postgres:5432
```

---

## Docker Build Details

### Multi-Stage Build (Dockerfile.api)

**Stage 1: Dependencies**
```dockerfile
FROM python:3.11-slim as dependencies

# Install build tools + packages
RUN apt-get update && apt-get install -y curl git ...

# Copy all pyproject.toml + setup files
COPY pyproject.toml setup.py ./

# Install packages (cached separately)
RUN pip install -e .
```

**Stage 2: Runtime**
```dockerfile
FROM python:3.11-slim

# Copy only installed packages (not source)
COPY --from=dependencies /usr/local/lib/python3.11 /usr/local/lib/python3.11

# Copy source code
COPY . /app

# Non-root user
RUN useradd -u 1000 socrates && chown -R socrates /app

USER socrates

CMD ["uvicorn", "socrates_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Benefits**:
- Only 2 layers: one for dependencies (cached), one for source (changes frequently)
- Smaller final image (no build tools)
- Faster rebuilds (dependencies cached)

### Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

Ensures:
- API is responding
- All components ready before traffic
- Auto-restart if unhealthy

---

## Pushing to Docker Hub

### Prerequisites
```bash
# 1. Create Docker Hub account
#    https://hub.docker.com

# 2. Create repositories
#    https://hub.docker.com/repositories
#    - socrates-api (public)
#    - socrates-web (public)

# 3. Generate access token
#    Docker Hub → Account Settings → Security → Generate New Token

# 4. Add GitHub Secrets (for CI/CD)
#    Repository → Settings → Secrets → Actions
#    - DOCKER_USERNAME: nireus79
#    - DOCKER_PASSWORD: <generated token>
```

### Using GitHub Actions (Automated)
We've set up automated Docker builds in `.github/workflows/docker-build-push.yml`:

```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [main]
  workflow_dispatch:      # Can manually trigger

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push API
        uses: docker/build-push-action@v4
        with:
          context: .
          file: ./Dockerfile.api
          push: true
          tags: nireus79/socrates-api:latest

      - name: Build and push Web
        uses: docker/build-push-action@v4
        with:
          context: .
          file: ./Dockerfile.reverse-proxy
          push: true
          tags: nireus79/socrates-web:latest
```

**How it works**:
1. Push code to GitHub
2. GitHub Actions automatically triggers
3. Builds Docker images
4. Pushes to Docker Hub
5. Available as `nireus79/socrates-api:latest`

### Manual Build & Push (If Needed)
```bash
# Build locally
docker build -f Dockerfile.api -t nireus79/socrates-api:latest .
docker build -f Dockerfile.reverse-proxy -t nireus79/socrates-web:latest .

# Login to Docker Hub
docker login

# Push
docker push nireus79/socrates-api:latest
docker push nireus79/socrates-web:latest
```

---

## Running from Docker Hub

### Single Command
```bash
docker run -e ANTHROPIC_API_KEY=sk-ant-xxxxx \
           -p 8000:8000 \
           nireus79/socrates-api:latest
```

### With Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    image: nireus79/socrates-api:latest  # Pre-built from Docker Hub
    ports:
      - "8000:8000"
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      ENVIRONMENT: production
    volumes:
      - socrates_data:/app/data

volumes:
  socrates_data:
```

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx docker-compose up
```

---

## Production Deployment Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Generate strong encryption keys (32+ chars)
- [ ] Use managed PostgreSQL (not SQLite) for data durability
- [ ] Enable Redis for distributed caching
- [ ] Set resource limits:
  ```yaml
  resources:
    limits:
      cpus: '1'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 1G
  ```
- [ ] Configure health checks (interval, timeout, retries)
- [ ] Set up log aggregation (ELK, CloudWatch, etc.)
- [ ] Enable monitoring (Prometheus, Datadog)
- [ ] Use HTTPS/TLS (update nginx config)
- [ ] Restrict CORS_ORIGINS to your domain
- [ ] Regular backups of postgres_data volume
- [ ] Use `.env.production` (never commit)
- [ ] Rotate encryption keys quarterly

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs api

# Common issues:
# 1. ANTHROPIC_API_KEY not set → Add to .env file
# 2. Port 8000 in use → Change port in docker-compose.yml
# 3. Insufficient disk space → Free up space
```

### Database connection refused
```bash
# Check if postgres service is running
docker-compose ps

# If postgres not healthy, check its logs
docker-compose logs postgres
```

### API responding but health check failing
```bash
# SSH into container
docker-compose exec api bash

# Check if health endpoint works
curl http://localhost:8000/health

# Check logs
tail -f /app/data/logs/socrates.log
```

### OutOfMemory errors
```yaml
# Increase memory limit in docker-compose.yml
resources:
  limits:
    memory: 4G  # Increase from 2G
```

---

## Performance Tuning

### For Development (Fast feedback)
```yaml
api:
  build:
    context: .
    dockerfile: Dockerfile.api
    # Local build - reuses layers
  environment:
    LOG_LEVEL: DEBUG
    # More verbose logging
```

### For Production (Optimal performance)
```yaml
api:
  image: nireus79/socrates-api:latest
  # Pre-built image - no build overhead
  environment:
    LOG_LEVEL: WARNING
    # Less verbose logging
    MAX_CONCURRENT_GENERATIONS: 10
    # Higher concurrency for more throughput
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

### Caching Strategy
```yaml
redis:
  image: redis:7-alpine
  volumes:
    - redis_data:/data
  # Cache hits significantly improve performance
  # Reduce database queries
  # Faster search results
```

---

## Scaling Beyond Docker Compose

For production with high availability, consider:

1. **Kubernetes Deployment**
   - Use existing K8s manifests in `deployment/kubernetes/`
   - Auto-scaling based on load
   - Self-healing (restart failed pods)

2. **Managed Services**
   - AWS ECS (managed Docker orchestration)
   - Google Cloud Run (serverless containers)
   - DigitalOcean App Platform

3. **Database Scaling**
   - PostgreSQL read replicas
   - Managed database (RDS, Cloud SQL)
   - Automatic backups

4. **Cache Scaling**
   - Redis Cluster (multi-node)
   - Managed Redis (ElastiCache, MemoryStore)

---

## Summary

Docker deployment provides:
- **Consistency**: Same environment everywhere
- **Simplicity**: One docker-compose.yml
- **Scalability**: From single container to K8s
- **Automation**: GitHub Actions handles builds
- **Reliability**: Health checks + restarts

Start with `docker-compose up`, scale to Kubernetes when ready.
