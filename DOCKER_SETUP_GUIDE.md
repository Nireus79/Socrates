# Socrates Docker Setup Guide

**Simple guide for setting up and troubleshooting Socrates in Docker.**

---

## Quick Start (First Time)

```bash
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Start Docker (encryption keys auto-generate on first run)
sudo docker compose up --build
```

Then open: **http://localhost:3000**

**That's it!** Encryption keys are auto-generated and saved to the persistent Docker volume on first run. No manual setup needed.

---

## Restart After Closing

### Simple Restart (Keep Database)

```bash
# Just start the containers again
sudo docker compose up
```

### Full Restart (Clean State, Keep Database)

```bash
# Stop and remove containers, but keep database
sudo docker compose down

# Restart
sudo docker compose up
```

### Complete Reset (Delete Everything)

```bash
# Stop containers and delete volume (loses all data including API keys)
sudo docker compose down -v

# Rebuild completely fresh
sudo docker compose up --build

# Set your LLM API keys again in Settings
```

---

## Encryption Keys & Security

### How Keys Work

1. **First Run**: Docker detects no encryption key exists
2. **Auto-Generate**: System creates a secure random key using `secrets.token_urlsafe(32)`
3. **Persist**: Key saved to `/app/data/.encryption_key` (inside persistent Docker volume)
4. **On Restart**: System loads existing key from volume
5. **Result**: Same encryption key persists across container restarts automatically

### Where Keys Are Stored

- **Inside Container**: `/app/data/.encryption_key`
- **On Host**: Docker managed volume `socrates_data` (usually at `/var/lib/docker/volumes/`)
- **Persists Across**: Container restarts, updates, rebuilds

### Backup Keys

```bash
# Backup encryption key (in case of volume loss)
docker run --rm -v socrates_data:/data -v $(pwd):/backup \
  alpine cp /data/.encryption_key /backup/.encryption_key.backup

# Keep this file safe!
```

### Rotating Keys (Change Encryption)

```bash
# WARNING: Old API keys won't decrypt with new keys
# Users must re-enter their API credentials after rotation

# Delete the key file to force new key generation
sudo docker compose down
sudo docker volume rm socrates_data

# Start fresh (will generate new key)
sudo docker compose up --build

# Set LLM API keys again in Settings
```

---

## Docker Compose Commands

### Basic Operations

```bash
# Start services (attach to logs)
sudo docker compose up

# Start in background
sudo docker compose up -d

# Stop services
sudo docker compose down

# Stop and remove volumes (delete database!)
sudo docker compose down -v

# Rebuild images
sudo docker compose up --build

# View running services
sudo docker compose ps

# View all services (running and stopped)
sudo docker compose ps -a
```

### Logs

```bash
# View logs for all services
sudo docker compose logs

# Follow logs (live, press Ctrl+C to stop)
sudo docker compose logs -f

# View logs for specific service
sudo docker compose logs -f socrates-api
sudo docker compose logs -f socrates-frontend
sudo docker compose logs -f nginx

# View last N lines
sudo docker compose logs --tail 100

# Show timestamps
sudo docker compose logs -f --timestamps
```

### Maintenance

```bash
# Clean up stopped containers
sudo docker container prune -f

# Delete unused images
sudo docker image prune -a -f

# Delete build cache
sudo docker builder prune -a -f

# Delete unused volumes
sudo docker volume prune -f

# Show disk usage
sudo docker system df

# Show detailed info
sudo docker system df -v
```

---

## Troubleshooting

### API Fails to Start

**Check logs:**
```bash
sudo docker compose logs -f socrates-api
```

**Common causes:**
- Port 8000 already in use: `sudo docker compose down` or change port in `docker-compose.yml`
- Database permission issue: Try `sudo docker compose down -v` and rebuild
- Corrupted database: Delete volume `sudo docker volume rm socrates_data` and rebuild

### Can't Connect to Frontend

```bash
# Check if all services are running
sudo docker compose ps

# Check frontend logs
sudo docker compose logs -f socrates-frontend

# Check nginx (reverse proxy)
sudo docker compose logs -f nginx

# Try direct port
curl http://localhost:80

# Try direct API
curl http://localhost:8000/health
```

### Port Already in Use

```bash
# Option 1: Stop Docker
sudo docker compose down

# Option 2: Change ports in docker-compose.yml
# Edit and change:
#   ports:
#     - "3000:80"  <- change first number
#     - "8000:8000" <- change first number

# Then restart
sudo docker compose up
```

### Database Encryption Error

**Error:** `Failed to decrypt API key`

This happens when:
- Encryption key was lost (volume deleted but database still exists somewhere)
- Or mixing incompatible databases

**Fix:**
```bash
# Delete the old database and volume
sudo docker compose down
sudo docker volume rm socrates_data

# Rebuild fresh
sudo docker compose up --build
```

### Container Exits Immediately

```bash
# Check why it exited
sudo docker compose logs socrates-api

# Common causes:
# - Port already in use
# - Corrupted database file
# - Permission issues
```

### High Disk Usage

```bash
# See what's using space
sudo docker system df

# Clean up old images
sudo docker image prune -a -f

# Clean up build cache
sudo docker builder prune -a -f

# Check if volumes are taking space
sudo docker volume ls

# Remove unused volumes
sudo docker volume prune -f
```

---

## Docker Architecture

### Services

**api** (socrates-api)
- FastAPI server on port 8000
- Handles all business logic
- Connects to SQLite database
- Auto-generates encryption keys on first run

**frontend** (socrates-frontend)
- React/Vue UI
- Maps to http://localhost:3000 externally
- Communicates with API via reverse proxy

**nginx** (reverse proxy)
- Routes requests to API and frontend
- Handles CORS and security headers
- Maps port 80 internally to 3000 externally

**redis** (cache)
- In-memory cache for sessions
- Optional performance improvement

### Volumes

**socrates_data**
- Persistent storage for database and encryption keys
- Contains:
  - `projects.db` - SQLite database
  - `.encryption_key` - Auto-generated encryption key
  - `logs/` - Application logs
- Survives container restarts
- Deleted with `docker compose down -v`

**redis_data**
- Redis cache storage
- Deleted with `docker compose down -v`

### Networks

**socrates-network**
- Docker bridge network
- Allows services to communicate by name
- All services connected

---

## Production Deployment

### Kubernetes

```bash
# Use docker-compose.yml as reference
# Create Kubernetes manifests for:
# - Deployment (api, frontend, nginx)
# - Services (expose ports)
# - PersistentVolumeClaim (for data storage)
# - Secrets (for encryption keys via K8s Secrets)
```

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Create secrets (instead of env files)
echo "secure-random-key-here" | docker secret create socrates_encryption_key -

# Deploy stack
docker stack deploy -c docker-compose.yml socrates
```

### Environment Variables

For production, override at runtime:
```bash
export ENVIRONMENT=production
export ALLOWED_HOSTS=yourdomain.com
export CORS_ORIGINS=https://yourdomain.com

sudo docker compose up --build
```

---

## Health Checks

Docker automatically monitors service health. View status:

```bash
sudo docker compose ps

# Example output:
# NAME          STATUS
# socrates-api  Up 2 minutes (healthy)
```

Services have built-in health checks that verify:
- API responds to HTTP requests
- Frontend is accessible
- Redis is responding
- Nginx is routing correctly

---

## Performance Tips

### Speed Up Builds

```bash
# Enable BuildKit for faster, more efficient builds
export DOCKER_BUILDKIT=1
sudo docker compose up --build
```

### Reduce Memory Usage

```bash
# Check resource usage
sudo docker stats

# If using too much memory:
# 1. Close unused applications
# 2. Reduce Redis memory: edit docker-compose.yml
# 3. Use lightweight base images (already done)
```

### Reduce Disk Usage

```bash
# Clean up aggressively
sudo docker system prune -a --volumes -f

# Or selective cleanup
sudo docker image prune -a -f     # Remove unused images
sudo docker builder prune -a -f   # Remove build cache
sudo docker volume prune -f       # Remove unused volumes
```

---

## Backup and Restore

### Backup Database

```bash
# While Docker is running
sudo docker cp socrates-api:/app/data/projects.db ./projects.db.backup
```

### Restore Database

```bash
# Stop Docker
sudo docker compose down

# Copy database back
sudo docker cp ./projects.db.backup socrates-api:/app/data/projects.db

# Start Docker
sudo docker compose up
```

### Backup Everything (Database + Keys)

```bash
# Create archive of entire volume
sudo docker run --rm -v socrates_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/socrates_backup.tar.gz -C /data .

# Restore from archive
sudo docker run --rm -v socrates_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/socrates_backup.tar.gz -C /data
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Port 3000 not accessible | Frontend not running | `docker compose logs -f socrates-frontend` |
| Port 8000 not accessible | API not running | `docker compose logs -f socrates-api` |
| Database errors | Volume permissions | `docker compose down -v && docker compose up --build` |
| High memory usage | Redis cache | Reduce in docker-compose.yml or restart |
| Can't encrypt API key | Missing encryption key | Should auto-generate, check logs |
| Slow performance | Disk I/O bottleneck | Use SSD for Docker storage |

---

## Notes for Users

✅ **Always** start with `sudo docker compose up --build` first time
✅ **Always** use `sudo docker compose down` before major changes
✅ **Always** check logs with `sudo docker compose logs -f` when debugging
✅ **Always** backup your data before `docker compose down -v`
❌ **Never** edit encryption keys manually
❌ **Never** delete database files directly
❌ **Never** run `docker system prune -a` on production

---

## Getting Help

1. **Check logs first**: `sudo docker compose logs -f`
2. **Verify prerequisites**: Docker installed and running
3. **Try clean rebuild**: `docker compose down -v && docker compose up --build`
4. **Check disk space**: `docker system df`
5. **Review this guide**: Most issues are covered above

---

**Last Updated**: July 8, 2026  
**Version**: Production-Ready (Auto-Generated Keys)
