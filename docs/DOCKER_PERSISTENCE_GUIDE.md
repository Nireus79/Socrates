# Docker Persistence & Session Management Guide

**Problem**: Users lose their session and must re-authenticate when Docker containers restart.

**Root Cause**: JWT secret key was not configured in docker-compose environment, causing session validation to fail after container restarts.

---

## ✅ Solution Applied

### What was fixed:

1. **Added JWT_SECRET_KEY to docker-compose.yml** (required for session persistence)
2. **Updated .env and .env.example** with JWT configuration documentation
3. **Fixed CORS settings** to support VSCode port forwarding (`host.docker.internal`)

---

## 🚀 Quick Start - Docker with Data Persistence

### Step 1: Prepare Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env and set stable values (do NOT use placeholders in production)
vim .env
```

**Required variables in .env:**
```bash
# These MUST be set and CONSISTENT across all deployments
SOCRATES_ENCRYPTION_KEY=<generate-stable-key>
DATABASE_ENCRYPTION_KEY=<generate-stable-key>
JWT_SECRET_KEY=<generate-stable-key>

# These persist automatically
DATABASE_URL=sqlite:////app/data/socrates.db
REDIS_URL=redis://redis:6379/0
```

### Step 2: Generate Secure Keys

Run these commands and copy output to `.env`:

```bash
# Generate SOCRATES_ENCRYPTION_KEY
python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"

# Generate DATABASE_ENCRYPTION_KEY
python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Start Containers

```bash
docker-compose -f deployment/docker/docker-compose.yml up -d
```

### Step 4: Verify Everything Works

```bash
# Check if API is healthy
curl http://localhost:8000/health

# Check if database is initialized
docker-compose -f deployment/docker/docker-compose.yml logs api | grep "Database"
```

---

## 🔄 Container Restart Workflow

### Test Session Persistence:

```bash
# 1. Start fresh
docker-compose -f deployment/docker/docker-compose.yml up -d
sleep 5

# 2. Register user
REGISTER=$(curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
  }')

echo "Registration response: $REGISTER"

# 3. Login and get token
LOGIN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }')

TOKEN=$(echo $LOGIN | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Auth token: $TOKEN"

# 4. Verify user can access projects (BEFORE restart)
echo "\n=== BEFORE CONTAINER RESTART ==="
curl -s -X GET http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" | jq .

# 5. RESTART CONTAINERS
echo "\n=== RESTARTING CONTAINERS ==="
docker-compose -f deployment/docker/docker-compose.yml down
sleep 3
docker-compose -f deployment/docker/docker-compose.yml up -d
sleep 5

# 6. Verify token STILL WORKS (AFTER restart)
echo "\n=== AFTER CONTAINER RESTART ==="
curl -s -X GET http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" | jq .

# 7. Verify user data persists
echo "\n=== VERIFY USER DATA PERSISTED ==="
# Login again with same credentials
LOGIN2=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }')

TOKEN2=$(echo $LOGIN2 | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "New token after restart: $TOKEN2"

# Same projects should be accessible
curl -s -X GET http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN2" | jq .
```

**Expected result**: Both before and after restart, the token should be valid and user data should persist.

---

## 🐛 Troubleshooting

### Problem: "Token validation failed" after restart

**Symptoms:**
- User login works initially
- After `docker-compose down/up`, token becomes invalid
- User must re-login

**Solution:**
1. Check `.env` file exists and has `JWT_SECRET_KEY` set:
   ```bash
   cat .env | grep JWT_SECRET_KEY
   ```

2. Verify it's being passed to container:
   ```bash
   docker-compose -f deployment/docker/docker-compose.yml config | grep JWT_SECRET_KEY
   ```

3. If empty, generate and set:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   # Copy output to .env file
   ```

4. Restart containers:
   ```bash
   docker-compose -f deployment/docker/docker-compose.yml down
   docker-compose -f deployment/docker/docker-compose.yml up -d
   ```

### Problem: Database not persisting

**Symptoms:**
- Users lose project data after restart
- Must re-create everything

**Diagnosis:**
```bash
# Check if volumes are mounted correctly
docker-compose -f deployment/docker/docker-compose.yml exec api ls -la /app/data/

# Check volume status
docker volume ls | grep socrates
```

**Solution:**
```bash
# Verify docker-compose.yml has volume definitions
cat deployment/docker/docker-compose.yml | grep -A 5 "volumes:"

# If volumes are missing, recreate:
docker-compose -f deployment/docker/docker-compose.yml down -v
docker-compose -f deployment/docker/docker-compose.yml up -d
```

### Problem: CORS errors from VSCode port forwarding

**Symptoms:**
```
Access to XMLHttpRequest at 'http://localhost:3000' from 'http://127.0.0.1:5173' has been blocked by CORS policy
```

**Solution:**
The docker-compose.yml now includes `host.docker.internal` in CORS origins. If still failing:

```bash
# Check current CORS configuration
docker-compose -f deployment/docker/docker-compose.yml config | grep CORS_ORIGINS

# Update .env to include your port-forwarded URLs:
# CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://api:3000
```

### Problem: "Database connection refused"

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solution:**
```bash
# Check if database is actually running
docker-compose -f deployment/docker/docker-compose.yml logs postgres

# Restart database container
docker-compose -f deployment/docker/docker-compose.yml restart postgres

# Check connection string in .env
cat .env | grep DATABASE_URL
```

---

## 📊 Persistence Architecture

### What Gets Persisted:

| Component | Storage | Persists? | Details |
|-----------|---------|-----------|---------|
| User accounts | SQLite/PostgreSQL | ✅ YES | Stored in `postgres_data` volume |
| Projects | SQLite/PostgreSQL | ✅ YES | Stored in `postgres_data` volume |
| Sessions | In-memory (then Redis) | ✅ YES* | Stored in `redis_data` volume |
| JWT tokens | Browser localStorage | ⚠️ CONDITIONAL | Valid if `JWT_SECRET_KEY` is consistent |
| Logs | `/app/logs` | ✅ YES | Stored in `socrates_logs` volume |
| Cache | Redis | ✅ YES | Stored in `redis_data` volume |

*JWT tokens remain valid as long as `JWT_SECRET_KEY` environment variable doesn't change between restarts.

### Volume Definitions:

```yaml
# In docker-compose.yml
volumes:
  socrates_data:     # /app/data - SQLite database and app data
  socrates_logs:     # /app/logs - Application logs
  postgres_data:     # /var/lib/postgresql/data - PostgreSQL data
  redis_data:        # /data - Redis persistent storage
```

These volumes are **persistent** across:
- Container restarts ✅
- Image rebuilds ✅
- Docker Compose down/up cycles ✅

They are **deleted** only with:
- `docker-compose down -v` (removes volumes)
- `docker volume prune` (removes unused volumes)

---

## 🔐 Environment Variable Best Practices

### For Development:

```bash
# .env file (DO NOT COMMIT)
SOCRATES_ENCRYPTION_KEY=dev-key-12345
DATABASE_ENCRYPTION_KEY=dev-key-67890
JWT_SECRET_KEY=dev-jwt-secret-abc123

DATABASE_URL=sqlite:////app/data/socrates.db
REDIS_URL=redis://redis:6379/0

ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### For Production:

```bash
# .env file (KEEP SECURE)
SOCRATES_ENCRYPTION_KEY=$(python3 -c "import secrets, base64; print(...)")
DATABASE_ENCRYPTION_KEY=$(python3 -c "import secrets, base64; print(...)")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

DATABASE_URL=postgresql://prod-user:prod-pass@prod-db:5432/socrates_prod
REDIS_URL=redis://prod-redis:6379/0

ENVIRONMENT=production
LOG_LEVEL=WARNING
```

---

## 📝 Checklist Before Deployment

- [ ] `.env` file created and not committed to git
- [ ] `JWT_SECRET_KEY` is set (not placeholder)
- [ ] `SOCRATES_ENCRYPTION_KEY` is set (not placeholder)
- [ ] `DATABASE_ENCRYPTION_KEY` is set (not placeholder)
- [ ] Database connection string is correct
- [ ] Redis URL is correct
- [ ] CORS origins include your frontend URL
- [ ] Docker volumes are properly mounted
- [ ] `.env` is in `.gitignore`
- [ ] Tested container restart workflow

---

## 🔗 Related Documentation

- [docker-compose.yml](../deployment/docker/docker-compose.yml)
- [JWT Handler](../socrates-api/src/socrates_api/auth/jwt_handler.py)
- [Docker Installation Guide](./DOCKER_SETUP.md)
