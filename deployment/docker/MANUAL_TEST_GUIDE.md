# Manual Docker Configuration Test Guide

This guide walks through testing the docker-compose fixes step-by-step.

---

## Prerequisites

- Docker and Docker Compose installed
- Your Anthropic API key ready
- ~5 GB disk space
- 15-20 minutes

---

## Step 1: Prepare Environment

```bash
cd deployment/docker
```

### Check if .env exists:
```bash
ls -la .env
```

### If .env doesn't exist, create it from template:
```bash
cp .env.docker .env
```

### Edit .env and add your Anthropic API key:
```bash
nano .env  # or use your editor
```

Find this line:
```
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE
```

Replace with your actual key from [console.anthropic.com](https://console.anthropic.com)

Save the file.

---

## Step 2: Verify Configuration Files

### Check docker-compose.yml has the fix:
```bash
grep "SOCRATES_DATA_DIR=/app/data" docker-compose.yml
```

Expected output:
```
      - SOCRATES_DATA_DIR=/app/data
```

### Check frontend API URL is correct:
```bash
grep "VITE_API_URL" docker-compose.yml
```

Expected output:
```
        VITE_API_URL: http://localhost:8000
```

### Check both are present:
```bash
grep "REACT_APP_API_URL=http://localhost" docker-compose.yml
```

Expected output:
```
      - REACT_APP_API_URL=http://localhost:8000
```

---

## Step 3: Clean Up Old Data

```bash
# Stop any running containers
docker-compose down --remove-orphans

# Remove old volumes (for clean test)
docker volume rm socrates_data 2>/dev/null || true
docker volume rm socrates_logs 2>/dev/null || true

# Verify volumes are removed
docker volume ls | grep socrates
# Should show nothing
```

---

## Step 4: Build and Start Services

```bash
# Build images (this may take 3-5 minutes)
docker-compose build --no-cache

# Start all services
docker-compose up -d

# Wait 15-30 seconds for services to start
sleep 30

# Check status
docker-compose ps
```

Expected output (all should show "Up"):
```
NAME                COMMAND             STATUS
deployment_api_1    python -m socrates  Up (healthy)
deployment_frontend_1  /docker-entrypoint  Up
deployment_redis_1  redis-server        Up (healthy)
deployment_postgres_1  postgres        Up (healthy)
deployment_nginx_1  nginx               Up
```

---

## Step 5: Verify Configuration in Running Container

### Check SOCRATES_DATA_DIR is set:
```bash
docker-compose exec api env | grep SOCRATES_DATA_DIR
```

Expected output:
```
SOCRATES_DATA_DIR=/app/data
```

### Check database directory exists:
```bash
docker-compose exec api ls -la /app/data/
```

Expected output (initially):
```
total 8
drwxr-xr-x  2 socrates socrates 4096 <date> .
drwxr-xr-x  1 root     root     4096 <date> ..
```

Database file will be created on first use.

### Check volume is properly mounted:
```bash
docker volume inspect deployment_docker_socrates_data
```

Should show a `Mountpoint` like `/var/lib/docker/volumes/deployment_docker_socrates_data/_data`

---

## Step 6: Test in Browser

1. **Open Frontend**
   - Go to: http://localhost:3000
   - You should see the Socrates login page

2. **Create User Account**
   - Click "Register" or "Sign Up"
   - Fill in email, password
   - Click "Create Account"
   - You should be logged in

3. **Create Test Project**
   - Click "New Project" or similar button
   - Enter project name: `Test Project - Docker Fix`
   - Enter description: `This is a test to verify data persistence`
   - Click "Create"
   - Verify project appears in the list

4. **Test API Directly** (optional)
   - Open: http://localhost:8000/docs
   - Try a health check endpoint
   - You should get a `{"status": "healthy", ...}` response

---

## Step 7: Data Persistence Test (THE CRITICAL TEST)

This test verifies data survives container restarts.

### Note the project and user you created in Step 6

### Stop all containers:
```bash
docker-compose down
```

Expected output:
```
Stopping deployment_nginx_1   ... done
Stopping deployment_frontend_1 ... done
Stopping deployment_api_1      ... done
...
```

### Verify containers are stopped:
```bash
docker-compose ps
```

Should be empty or show all containers as "Down"

### Verify the Docker volume still exists:
```bash
docker volume ls | grep socrates_data
```

Should show:
```
local     deployment_docker_socrates_data
```

### Start containers again:
```bash
docker-compose up -d
sleep 30
```

### Verify containers are running:
```bash
docker-compose ps
```

All should show "Up"

### Open browser and go to http://localhost:3000

### Try to log in with the account created in Step 6
- Use the same email and password
- **You should successfully log in**

### Check if your test project is still there
- **It should appear in your project list**

---

## Step 8: Verify Volume Persistence

Check that the database file has data:

```bash
docker-compose exec api ls -la /app/data/
```

Should now show:
```
-rw-r--r--  1 socrates socrates 24576 <date> projects.db
```

(File size may vary, but should not be empty)

---

## Expected Results

### ✅ Success Indicators

1. **Configuration verified** ✓
   - SOCRATES_DATA_DIR set to /app/data
   - Frontend API URL is http://localhost:8000

2. **Services start** ✓
   - All containers show "Up" in docker-compose ps
   - API is accessible at http://localhost:8000

3. **User creation works** ✓
   - Successfully registered account
   - Logged in successfully

4. **Project creation works** ✓
   - Project created and visible in list
   - No network errors from frontend

5. **Data persists** ✓ **CRITICAL**
   - After docker-compose down/up
   - User account still exists
   - Project still appears in list
   - Login works with existing credentials

---

## Troubleshooting

### Issue: "Cannot connect to frontend"

```bash
# Check frontend logs
docker-compose logs frontend

# Restart frontend
docker-compose restart frontend

# Wait 10 seconds
sleep 10

# Try again
```

### Issue: "Cannot create user - network error"

This was the original issue. If you still see it:

```bash
# Check API URL in docker-compose.yml
grep -A5 "frontend:" docker-compose.yml

# Should show: VITE_API_URL: http://localhost:8000
# Not: http://api:8000

# If wrong, edit and restart
docker-compose down
# Edit docker-compose.yml
docker-compose up -d
```

### Issue: "Data lost after restart"

This was the original critical issue. If still happening:

```bash
# Check SOCRATES_DATA_DIR in running container
docker-compose exec api env | grep SOCRATES_DATA_DIR

# Should show: SOCRATES_DATA_DIR=/app/data
# Not: SOCRATES_DATA_DIR=<empty>

# Check if volume exists
docker volume ls | grep socrates_data

# If volume doesn't exist or is empty, rebuild:
docker-compose down -v
# Delete .env to force regeneration
rm .env
cp .env.docker .env
# Edit .env with API key
docker-compose build
docker-compose up -d
```

### Issue: "API not responding"

```bash
# Check API logs
docker-compose logs -f api

# Wait for startup (can take 30-40 seconds)
sleep 40

# Check again
docker-compose ps
```

### Issue: "Port already in use"

```bash
# Find process using port
lsof -i :8000  # or :3000

# Either kill the process or change ports in .env
# Add to .env:
SOCRATES_API_PORT=8001
CORS_ORIGINS=http://localhost:3001
```

---

## Quick Reference Commands

```bash
# View logs
docker-compose logs -f api       # API logs
docker-compose logs -f frontend  # Frontend logs
docker-compose logs              # All logs

# Container management
docker-compose ps                # Status
docker-compose up -d             # Start
docker-compose down              # Stop
docker-compose restart api       # Restart one service

# Access containers
docker-compose exec api bash                          # Shell in API
docker-compose exec api python -m socrates_api.main  # Run manually

# Volume inspection
docker volume ls                           # List volumes
docker volume inspect deployment_docker_socrates_data  # Details
docker volume rm socrates_data            # Delete volume

# Database inspection
docker-compose exec api ls -la /app/data/
docker-compose exec api sqlite3 /app/data/projects.db "SELECT COUNT(*) FROM projects;"
```

---

## Success Criteria

| Criterion | Before Fix | After Fix |
|-----------|-----------|-----------|
| User created | ✓ | ✓ |
| Project created | ✓ | ✓ |
| After `docker-compose down` | ✗ Data lost | ✓ Data persists |
| After `docker-compose up` | ✗ Can't log in | ✓ Can log in |
| Projects visible | ✗ Empty list | ✓ Shows saved projects |
| Frontend API calls work | ✗ Network error | ✓ Success |

---

## Next Steps

If all tests pass:
1. ✅ You can safely use docker-compose for development
2. ✅ Your data will persist across container restarts
3. ✅ Users can log in and their projects are preserved
4. 📝 Consider setting up automated backups for production
5. 🚀 Read [DOCKER_DATA_PERSISTENCE.md](./DOCKER_DATA_PERSISTENCE.md) for production setup

---

## Getting Help

If tests fail:
1. Check the troubleshooting section above
2. Review logs: `docker-compose logs api`
3. Compare your configuration with the files in this directory
4. Check that all volumes and environment variables are set correctly
5. See [DOCKER_DATA_PERSISTENCE.md](./DOCKER_DATA_PERSISTENCE.md) for detailed explanations
