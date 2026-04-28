# Socrates Docker Deployment

This directory contains Docker configurations for running Socrates in a containerized environment.

## Quick Start (Development)

### 1. Prepare Environment

```bash
cd deployment/docker

# Copy the environment template
cp .env.docker .env

# Edit .env and set your API key
# IMPORTANT: Replace placeholder values before running
nano .env  # or use your editor
```

**Required settings in .env**:
```env
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
SOCRATES_ENCRYPTION_KEY=your-secure-32-char-random-key
DATABASE_ENCRYPTION_KEY=your-secure-32-char-random-key
```

### 2. Generate Secure Encryption Keys

```bash
# Generate encryption keys (do this twice for two different keys)
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Copy the output to .env for SOCRATES_ENCRYPTION_KEY and DATABASE_ENCRYPTION_KEY
```

### 3. Start Services

```bash
# From deployment/docker directory
docker-compose up -d

# Or from root directory
docker-compose -f deployment/docker/docker-compose.yml up -d

# Check status
docker-compose ps
```

### 4. Access Services

- **Frontend**: http://localhost:3000 (via Nginx reverse proxy)
- **Backend API**: http://localhost:8000 (direct access)
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432 (user: socrates, password from .env)
- **Redis**: localhost:6379

### 5. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### 6. Stop Services

```bash
# Stop all services (data persists in volumes)
docker-compose down

# Stop and remove all data
docker-compose down -v
```

---

## Files Included

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Main orchestration - defines all services |
| `Dockerfile` | API backend image build (links to root Dockerfile) |
| `socrates-frontend/Dockerfile` | Frontend React app image build |
| `.env.docker` | Environment variables template (copy to .env) |
| `nginx.conf` | Reverse proxy configuration |
| `README.md` | This file |

---

## Services Configuration

### API Backend
- **Image**: Built from root `Dockerfile`
- **Port**: 8000 (internal) → 8000 (host)
- **Database**: SQLite for development, can switch to PostgreSQL
- **Environment**: All variables from `.env`
- **Health Check**: Every 30 seconds via `/health` endpoint

### Frontend
- **Image**: Built from `socrates-frontend/Dockerfile`
- **Port**: 3000 (via Nginx), 5173 (Vite dev, if running locally)
- **Build Args**: `VITE_API_URL=http://api:8000`
- **Environment**: API URL configuration

### PostgreSQL
- **Image**: `postgres:15-alpine`
- **Credentials**: From `.env` (default: socrates/socrates_dev_password)
- **Database**: `socrates_db`
- **Port**: 5432
- **Volume**: `postgres_data` (persistent)
- **Health Check**: Every 10 seconds

### Redis
- **Image**: `redis:7.4-alpine`
- **Port**: 6379
- **Volume**: `redis_data` (persistent)
- **Purpose**: Caching and session storage

### Nginx
- **Image**: `nginx:1.27-alpine`
- **Ports**: 80 (HTTP), 443 (HTTPS for production)
- **Configuration**: `nginx.conf`
- **Purpose**: Reverse proxy, static file serving

---

## Environment Variables

### Security Variables (REQUIRED)
```env
ANTHROPIC_API_KEY           # Claude API key (from console.anthropic.com)
SOCRATES_ENCRYPTION_KEY     # For encrypting API keys in database
DATABASE_ENCRYPTION_KEY     # For database-level encryption
```

### Database Variables
```env
POSTGRES_USER               # Default: socrates
POSTGRES_PASSWORD           # Default: socrates_dev_password (CHANGE FOR PRODUCTION!)
POSTGRES_DB                 # Default: socrates_db
REDIS_URL                   # Default: redis://redis:6379/0
```

### API Variables
```env
ENVIRONMENT                 # development or production
LOG_LEVEL                   # DEBUG, INFO, WARNING, ERROR
ALLOWED_HOSTS               # Comma-separated list of allowed hosts
CORS_ORIGINS                # Comma-separated list of CORS origins
```

---

## Volumes

| Volume | Purpose | Persistence |
|--------|---------|-------------|
| `socrates_data` | Application data files | ✅ Persistent |
| `socrates_logs` | Application logs | ✅ Persistent |
| `postgres_data` | PostgreSQL database | ✅ Persistent |
| `redis_data` | Redis persistence | ✅ Persistent |
| `/app/node_modules` | Frontend node modules | ✅ Persistent |

---

## Network

All services communicate via the `socrates_network` bridge network:
- `api` hostname resolves to API backend
- `postgres` hostname resolves to database
- `redis` hostname resolves to cache
- `frontend` hostname resolves to frontend app

---

## Production Deployment

### Security Checklist

- [ ] Change `ENVIRONMENT=production`
- [ ] Generate new encryption keys for production
- [ ] Use a strong PostgreSQL password (20+ chars, mixed case, symbols, numbers)
- [ ] Set `ANTHROPIC_API_KEY` to production API key
- [ ] Configure proper `CORS_ORIGINS` for your domain
- [ ] Enable HTTPS/TLS (update `nginx.conf`)
- [ ] Set up regular backups for `postgres_data` volume
- [ ] Use `.env.production` for production settings
- [ ] Don't commit `.env` to version control
- [ ] Rotate encryption keys quarterly

### Production Configuration

1. Create `production.env` with strong credentials
2. Use `--env-file production.env` with docker-compose
3. Configure SSL/TLS certificates in `certs/` directory
4. Update `nginx.conf` for production domain
5. Set up volume backups:
   ```bash
   docker run --rm -v postgres_data:/data -v $(pwd)/backups:/backup \
     busybox tar czf /backup/postgres_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
   ```

### Scaling for Production

For larger deployments, consider:
- Running API on multiple containers with load balancing
- Using managed PostgreSQL (AWS RDS, Azure Database, etc.)
- Using managed Redis (AWS ElastiCache, Azure Cache, etc.)
- Using Kubernetes instead of Docker Compose
- See root `DEPLOYMENT.md` for Kubernetes setup

---

## Troubleshooting

### Port Already in Use

```bash
# Find what's using the port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use different port in .env
# Or stop the conflicting service
```

### Database Connection Error

```bash
# Check if postgres is healthy
docker-compose ps postgres
docker-compose logs postgres

# Rebuild the postgres volume
docker-compose down -v
docker-compose up -d postgres
sleep 30  # Wait for postgres to initialize
docker-compose up -d
```

### API Key Encryption Error

```bash
# Check if encryption keys are set
docker-compose exec api env | grep ENCRYPTION

# Verify keys are valid (32+ characters)
# Regenerate if needed:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Frontend Not Connecting to API

```bash
# Check nginx configuration
docker-compose logs nginx

# Verify API is healthy
docker-compose exec api curl http://localhost:8000/health

# Check frontend API URL
docker-compose exec frontend env | grep VITE_API_URL
```

### Out of Disk Space

```bash
# Check volumes
docker volume ls
du -sh /var/lib/docker/volumes/*

# Clean up unused volumes
docker volume prune

# Or move volumes to different disk
```

---

## Development Tips

### Running Commands in Containers

```bash
# Access API shell
docker-compose exec api bash

# Run database migrations
docker-compose exec api alembic upgrade head

# Check logs with timestamps
docker-compose logs -f --timestamps api

# Monitor resource usage
docker stats
```

### Rebuilding Images

```bash
# Rebuild all images
docker-compose build

# Rebuild specific image
docker-compose build api

# Rebuild without cache
docker-compose build --no-cache
```

### Debugging API

```bash
# Enable debug logging
docker-compose exec api env | grep LOG_LEVEL

# Check config
docker-compose exec api python -c "from socrates_api.config import get_settings; print(get_settings())"

# Run in debug mode
docker-compose exec api python -m pdb socrates_api/main.py
```

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. See root `TROUBLESHOOTING.md`
3. Check GitHub Issues: https://github.com/Nireus79/Socrates/issues
4. Review `DEPLOYMENT.md` for advanced options

---

## Related Documentation

- Root directory: See `README.md`, `DEPLOYMENT.md`, `INSTALLATION.md`
- Kubernetes: See `deployment/kubernetes/README.md`
- Frontend: See `socrates-frontend/README.md`
