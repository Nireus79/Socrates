# Docker Build and Deployment Instructions

## Overview
Complete guide for building and deploying Socrates using Docker and Docker Compose. Includes all services: API server, frontend, PostgreSQL database, and Redis cache.

## Prerequisites

### System Requirements
- **Docker Desktop** - Latest version (with WSL 2 on Windows)
- **8GB RAM minimum** (16GB recommended for full development)
- **10GB disk space minimum** for images, containers, and volumes
- **Internet connection** for pulling images and accessing Claude API

### Windows Users (WSL Integration)
1. Ensure Docker Desktop is installed
2. Verify WSL 2 integration is enabled:
   - Open Docker Desktop → Settings → Resources → WSL integration
   - Check "Enable integration with my default WSL distro"
   - Click "Apply & Restart"
3. Verify connectivity from WSL terminal:
   ```bash
   docker --version
   docker compose --version
   ```

### Anthropic API Key
- Get from [console.anthropic.com](https://console.anthropic.com)
- Add through Settings > LLM > Anthropic after starting Socrates
- Environment variable `ANTHROPIC_API_KEY` is optional (advanced users only)

## Critical Dependencies
The Docker builds include these specialized Socratic packages:
- `socratic-nexus>=0.4.0` - Universal LLM client library
- `socratic-knowledge>=0.1.6` - Knowledge base management
- `socratic-agents>=0.3.7` - Multi-agent orchestration
- `socratic-maturity>=0.2.0` - Project maturity tracking
- `socratic-docs>=0.2.1` - Documentation generation
- `socratic-morality>=0.0.3` - Ethical reasoning support

These packages must be present in `requirements.txt` for successful deployment. If the knowledge base fails to load during startup, verify all dependencies are installed.

## Backend API Image

### Build
```bash
cd deployment/docker
docker build -t socrates-api:1.3.1 -t socrates-api:latest -f Dockerfile ../..
```

### Push to Docker Hub
```bash
# Tag for Docker Hub (replace YOUR_USERNAME with your Docker Hub username)
docker tag socrates-api:1.3.1 YOUR_USERNAME/socrates-api:1.3.1
docker tag socrates-api:latest YOUR_USERNAME/socrates-api:latest

# Push
docker push YOUR_USERNAME/socrates-api:1.3.1
docker push YOUR_USERNAME/socrates-api:latest
```

## Frontend Image

### Build
```bash
cd socrates-frontend
docker build -t socrates-frontend:1.3.1 -t socrates-frontend:latest \
  --build-arg VITE_API_URL=https://api.socrates.app \
  -f Dockerfile .
```

### Push to Docker Hub
```bash
docker tag socrates-frontend:1.3.1 YOUR_USERNAME/socrates-frontend:1.3.1
docker tag socrates-frontend:latest YOUR_USERNAME/socrates-frontend:latest

docker push YOUR_USERNAME/socrates-frontend:1.3.1
docker push YOUR_USERNAME/socrates-frontend:latest
```

## Docker Compose (Development)

### Build All Services
```bash
cd deployment/docker
docker-compose build
```

### Run All Services
```bash
cd deployment/docker
docker-compose up -d
```

### Stop All Services
```bash
cd deployment/docker
docker-compose down
```

## What's Included in v1.3.1

✅ Phase action modal for interactive phase transitions
✅ Fixed analytics export functionality
✅ Improved API port discovery
✅ Database migration for knowledge_documents columns
✅ PyTorch device handling improvements
✅ UI layout centering and responsive design
✅ Component reorganization (Analysis → ProjectAssessment)

## Build Context

Both Dockerfiles expect to be built from the repository root:
- Backend: `deployment/docker/Dockerfile` context: `../..`
- Frontend: `socrates-frontend/Dockerfile` context: `.`

## Environment Variables

See `deployment/docker/docker-compose.yml` for full configuration options.

Key variables:
- `VITE_API_URL`: Frontend API endpoint (default: https://api.socrates.app)
- `DATABASE_URL`: Backend database connection
- `REDIS_URL`: Redis cache connection
- `LOG_LEVEL`: Logging verbosity

## First Startup - What to Expect

When you run `docker-compose up -d` for the first time:

1. **Database initialization** (PostgreSQL)
   - Creates database schema
   - Runs migrations from `socratic_system/database/migrations/`
   - Initializes user and project tables
   - Estimated time: 30 seconds

2. **Knowledge base loading** (ChromaDB)
   - Loads knowledge entries from `socratic_system/config/knowledge_base.json`
   - Generates embeddings with SentenceTransformer
   - Indexes ~100 knowledge entries
   - Estimated time: 2-3 minutes (first run)
   - If this fails, check logs: `docker-compose logs api`

3. **API server initialization**
   - Starts Uvicorn ASGI server
   - Initializes agent orchestrator
   - Loads all 10+ AI agents
   - Estimated time: 1 minute

4. **Frontend build** (React + Vite)
   - Compiles TypeScript and React components
   - Optimizes for production
   - Estimated time: 1-2 minutes

**Total first startup time: 5-7 minutes**

Verify services are running:
```bash
# Check container status
docker-compose ps

# All should show "Up" status
# API should be accessible at http://localhost:8000
# Frontend should be accessible at http://localhost:5173
```

## Viewing Logs

Monitor system operation during startup and runtime:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f redis

# Last 50 lines
docker-compose logs --tail=50 api

# Follow API logs in real-time
docker-compose logs -f api | grep -E "ERROR|WARNING|loaded|started"
```

## Troubleshooting

### Docker Daemon Not Running
**Error**: `Cannot connect to the Docker daemon`

**Solution**:
- Windows: Start Docker Desktop application
- Linux: `sudo systemctl start docker`
- Mac: Docker Desktop should auto-start

### Port Already in Use
**Error**: `bind: address already in use` for port 8000 or 5173

**Solutions**:
```bash
# Find what's using the port (Linux/Mac)
lsof -i :8000

# Stop existing containers
docker-compose down

# Remove all stopped containers
docker container prune -f

# Or use different ports in docker-compose.yml
```

### Knowledge Base Loading Fails
**Error in logs**: `[ERROR] orchestrator: Type error adding knowledge entry`

**Causes & Solutions**:
1. Missing dependency - verify `socratic-knowledge>=0.1.6` in requirements.txt
   ```bash
   docker-compose down
   # Edit requirements.txt to add socratic-knowledge>=0.1.6
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. ChromaDB corruption - clear and rebuild
   ```bash
   docker-compose down -v  # Remove volumes
   docker-compose up -d    # Rebuild from scratch
   ```

3. Insufficient disk space - free space and retry
   ```bash
   docker system prune -a --volumes  # Remove unused images/volumes
   df -h                             # Check available space
   ```

### Memory Issues
**Error**: Container exits with code 137 or OOMKilled

**Solutions**:
1. Increase Docker Desktop memory allocation:
   - Docker Desktop → Settings → Resources → Memory
   - Set to at least 8GB (16GB recommended)
   - Click "Apply & Restart"

2. Stop other applications consuming memory

3. Check current usage:
   ```bash
   docker stats
   ```

### WSL Integration Issues (Windows)
**Error**: `docker compose: command not found` in WSL terminal

**Solutions**:
1. Verify WSL integration in Docker Desktop:
   - Settings → Resources → WSL integration
   - Enable for your WSL distro
   - Restart Docker Desktop

2. Restart WSL:
   ```bash
   wsl --shutdown
   # Reopen WSL terminal
   docker compose --version
   ```

3. If still failing, reinstall Docker Desktop with WSL 2 backend

### API Returns 500 Errors
**Error**: HTTP 500 responses from API endpoints

**Solutions**:
1. Check API logs:
   ```bash
   docker-compose logs -f api | head -100
   ```

2. Verify environment variables:
   ```bash
   docker-compose exec api env | grep ANTHROPIC
   ```

3. Ensure Anthropic API key is set:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-your-key"
   docker-compose restart api
   ```

### Database Connection Errors
**Error**: `could not connect to server: Connection refused`

**Solutions**:
1. Wait for PostgreSQL to be ready (first startup can take 30 seconds):
   ```bash
   docker-compose logs postgres | tail -20
   ```

2. Check database is running:
   ```bash
   docker-compose ps postgres  # Should show "Up"
   ```

3. Reset database:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Disk Space Issues
**Error**: `no space left on device` during build or runtime

**Solutions**:
```bash
# Check disk usage
docker system df

# Remove unused images, containers, networks, volumes
docker system prune -a --volumes

# Remove specific old images
docker image prune -a --filter "until=48h"

# On Windows, compact WSL VHDX
# Open PowerShell as Administrator:
# wsl --shutdown
# diskpart
# > select vdisk file="C:\Users\YourUsername\AppData\Local\Docker\wsl\data\ext4.vhdx"
# > attach vdisk readonly
# > compact vdisk
# > detach vdisk
# > exit
```

### Building Custom Images Fails
**Error**: Build fails with version or dependency errors

**Solutions**:
1. Build with no cache:
   ```bash
   docker-compose build --no-cache
   ```

2. Pull latest base images:
   ```bash
   docker pull python:3.11-slim
   docker pull node:18-alpine
   docker-compose build --pull --no-cache
   ```

3. Check requirements.txt for syntax errors

4. Verify all dependencies are available:
   ```bash
   # View build output
   docker-compose build api 2>&1 | tail -50
   ```

## Verifying Deployment Success

Run these checks after starting the system:

```bash
# 1. Check all containers are running
docker-compose ps
# Expected: All services should show "Up"

# 2. Check API is responding
curl http://localhost:8000/health

# 3. Check API documentation
# Open browser: http://localhost:8000/docs

# 4. Check frontend is serving
curl http://localhost:5173

# 5. Check logs for errors
docker-compose logs api | grep ERROR
docker-compose logs api | grep WARNING

# 6. Verify database migrations completed
docker-compose logs postgres | grep "database system is ready"

# 7. Verify knowledge base loaded
docker-compose logs api | grep "knowledge entries loaded"
```

## Notes

- Images include all dependencies and code from v1.3.1
- Production images are optimized multi-stage builds
- Database migrations run automatically on first startup
- Health checks are configured for all services
- Knowledge base loads automatically; first load may take 2-3 minutes
- All services require internet connection for Claude API access
