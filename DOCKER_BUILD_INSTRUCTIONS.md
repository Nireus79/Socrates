# Docker Build and Deployment Instructions

## Overview
The Docker images for Socrates v1.3.1 need to be built and pushed to your registry.

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
docker-compose up -d
```

### Stop All Services
```bash
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

## Notes

- Images include all dependencies and code from v1.3.1
- Production images are optimized multi-stage builds
- Database migrations run automatically on first startup
- Health checks are configured for all services
