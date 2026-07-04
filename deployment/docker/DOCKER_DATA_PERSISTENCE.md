# Docker Data Persistence Guide

## Issue: User Data Lost After Container Restart

**Symptom:** After running `docker-compose down` and `docker-compose up`, user accounts and projects are lost.

**Root Cause:** The API uses `SOCRATES_DATA_DIR` environment variable to locate the SQLite database, but this variable wasn't set in `docker-compose.yml`. Without it, the database defaulted to `~/.socrates/` (inside the container), which is NOT persisted to a Docker volume.

---

## Solution

The `docker-compose.yml` and `.env.docker` have been updated to fix this:

### 1. **Environment Variable Configuration**

Added to `docker-compose.yml` API service:
```yaml
environment:
  - SOCRATES_DATA_DIR=/app/data
```

And to `.env.docker`:
```bash
SOCRATES_DATA_DIR=/app/data
```

### 2. **Volume Mounting**

The `socrates_data` volume is already correctly configured:
```yaml
volumes:
  - socrates_data:/app/data
```

This ensures `/app/data` persists across container restarts.

---

## How to Apply the Fix

### Option 1: Using the Updated Files (Recommended)

If you have the latest `docker-compose.yml` and `.env.docker`:

1. **Clean up old data** (optional, if you want a fresh start):
   ```bash
   docker-compose down -v
   ```

2. **Pull the latest configuration:**
   - Ensure you have the latest `docker-compose.yml`
   - Ensure you have the latest `.env.docker`

3. **Start services:**
   ```bash
   docker-compose up -d
   ```

4. **Verify persistence:**
   - Create a user and project
   - Run `docker-compose down`
   - Run `docker-compose up -d`
   - Check that your user and project still exist

### Option 2: Manual Fix (If Needed)

Edit your `docker-compose.yml` and locate the `api:` service environment section. Add this line:

```yaml
- SOCRATES_DATA_DIR=/app/data
```

Make sure the `socrates_data` volume is already defined (it should be):
```yaml
volumes:
  socrates_data:
```

---

## Database Configuration Explained

The Socrates API uses the `SOCRATES_DATA_DIR` environment variable to locate its SQLite project database:

```
SOCRATES_DATA_DIR=/app/data
     ↓
/app/data/projects.db  ← The actual database file
     ↓
Persists to Docker volume: socrates_data:/app/data
     ↓
Survives container restarts ✓
```

### Incorrect Configuration (Before Fix)

```
SOCRATES_DATA_DIR not set
     ↓
Defaults to ~/.socrates (container home directory)
     ↓
~/.socrates/projects.db  ← NOT mounted to any volume
     ↓
Lost when container restarts ✗
```

---

## Frontend API URL Configuration

Additionally, the `VITE_API_URL` for the frontend has been updated to:
```
VITE_API_URL=http://localhost:8000
```

This ensures the frontend can properly communicate with the API from the browser.

---

## Troubleshooting

### Symptom: Still losing data after restart

1. **Verify environment variable is set:**
   ```bash
   docker-compose exec api env | grep SOCRATES_DATA_DIR
   ```

   Should output:
   ```
   SOCRATES_DATA_DIR=/app/data
   ```

2. **Check volume persistence:**
   ```bash
   docker volume ls
   docker volume inspect deployment_docker_socrates_data
   ```

3. **Verify database file exists:**
   ```bash
   docker-compose exec api ls -la /app/data/
   ```

   Should show: `projects.db` file

### Symptom: "Cannot access database" errors

1. **Check volume mounting:**
   ```bash
   docker-compose exec api mount | grep "app/data"
   ```

2. **Verify file permissions:**
   ```bash
   docker-compose exec api ls -la /app/data/
   ```

   The `socrates` user (UID 1000) should own the directory.

### Symptom: Volume not being created

```bash
# Clean and recreate volumes
docker-compose down -v
docker-compose up -d

# Verify volume was created
docker volume ls | grep socrates_data
```

---

## Production Notes

For **production deployments**:

1. **Use PostgreSQL** instead of SQLite:
   - Set `ENVIRONMENT=production` in environment
   - Configure PostgreSQL credentials
   - Update database connection string

2. **Set up proper backup strategy** for `postgres_data` volume:
   ```bash
   docker run --rm -v postgres_data:/data -v $(pwd):/backup \
     postgres:15-alpine \
     pg_dump -h localhost -U socrates -d socrates_db > /backup/backup.sql
   ```

3. **Use external volume drivers** for cloud deployments (AWS EBS, GCP Persistent Disk, etc.)

4. **Enable TLS/HTTPS** with proper certificates (currently using self-signed for dev)

---

## References

- Docker Volumes Documentation: https://docs.docker.com/storage/volumes/
- Socrates Data Directory: `socratic_system/database/project_db.py`
- API Database Initialization: `socrates-api/src/socrates_api/database.py`
