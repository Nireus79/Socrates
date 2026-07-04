# Database Initialization Bug Fix

## 🐛 The Bug

**Problem:** The `projects.db` file was never created in Docker, causing:
- User data loss on container restart
- New users couldn't be registered
- Existing users were deleted after `docker-compose down/up`

**Root Cause:** In `socrates-api/src/socrates_api/main.py`, database initialization was ONLY called if the orchestrator initialization **failed**:

```python
# WRONG - Database only initialized on ERROR
try:
    orchestrator = AgentOrchestrator(...)  # If this succeeds
except Exception as e:
    # Database ONLY initialized here (in error case)
    DatabaseSingleton.initialize()
```

When orchestrator successfully initialized (which it usually did), the database was **never initialized**. The `projects.db` file was never created.

## ✅ The Fix

**Solution:** Move database initialization BEFORE orchestrator initialization, making it ALWAYS run:

```python
# CORRECT - Database ALWAYS initialized first
logger.info("Initializing database...")
DatabaseSingleton.initialize()  # Initialize with defaults
db = DatabaseSingleton.get_instance()
logger.info(f"✓ Database initialized at {db.db_path}")

# Then initialize orchestrator (which may fail)
try:
    orchestrator = AgentOrchestrator(...)
except Exception as e:
    logger.warning("Orchestrator failed, but database is ready for auth endpoints")
```

## 📝 Changes Made

**File:** `socrates-api/src/socrates_api/main.py`

1. Moved `DatabaseSingleton.initialize()` call BEFORE orchestrator initialization
2. Added explicit error handling that re-raises if database fails to initialize
3. Updated orchestrator error handling to NOT try to initialize database (already done)
4. Added clear logging to show database initialization success/failure

## 🧪 Verification

After deploying this fix, verify that the database is created:

```bash
# After restart
docker-compose exec api ls -la /app/data/

# Should show:
# projects.db (new file!)
# logs/
# vector_db/
```

Check logs for confirmation:

```bash
docker-compose logs api | grep "Database initialized"

# Should show:
# ✓ Database initialized at /app/data/projects.db
```

## 🔄 Testing the Fix

1. **Fresh start:** `docker-compose up -d`
2. **Create user:** Register via http://localhost:3000
3. **Create project:** Create a test project
4. **Restart:** `docker-compose down && docker-compose up -d`
5. **Verify:** User and project should still exist (NOT lost)

## 📊 Impact

| Scenario | Before | After |
|----------|--------|-------|
| `docker-compose up` | projects.db NOT created ❌ | projects.db created ✅ |
| Create user → restart | User lost ❌ | User persisted ✅ |
| Create project → restart | Project lost ❌ | Project persisted ✅ |
| Orchestrator failure | Auth endpoints down ❌ | Auth endpoints work ✅ |

## 🚀 Deployment

No additional changes needed. Just:

```bash
# Pull latest code
git pull origin main

# Rebuild API image
docker-compose build api

# Restart
docker-compose down
docker-compose up -d

# Verify
docker-compose exec api ls -la /app/data/projects.db
```

---

**Status:** ✅ Fixed in commit [latest]
**Affected:** All Docker deployments
**Severity:** CRITICAL - Data persistence was broken
