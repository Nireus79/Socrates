# Project Creation Flow - What Should Happen

## Expected Log Flow for Free User Creating 2nd Project

### Step 1: User tries to POST /projects (REST API)
**Line:** `socrates-api/src/socrates_api/routers/projects.py:179`
```
Expected Log: "Creating project: <project_name> for user <username>"
```

### Step 2: Get user object from database
**Line:** `socrates-api/src/socrates_api/routers/projects.py:187-188`
```
User is loaded from database
subscription_tier should be "free"
testing_mode should be False (or not set)
```

### Step 3: Check subscription limits
**Line:** `socrates-api/src/socrates_api/routers/projects.py:183`
```
Expected Log: "Checking subscription limits..."
```

### Step 4: Get all projects for user
**Line:** `socrates-api/src/socrates_api/routers/projects.py:195`
```
db.get_user_projects(current_user) is called
Should return:
  - First project created by user (if any)
  - Any projects user collaborates on
```

### Step 5: Filter owned projects only
**Line:** `socrates-api/src/socrates_api/routers/projects.py:196`
```
owned_projects = [p for p in all_projects if p.owner == current_user]

For 1st project creation:
  - owned_projects = [] (empty)
  - len(owned_projects) = 0

For 2nd project creation:
  - owned_projects = [ProjectContext(...)] (has first project)
  - len(owned_projects) = 1
```

### Step 6: Call subscription checker
**Line:** `socrates-api/src/socrates_api/routers/projects.py:197-199`
```python
can_create, error_msg = SubscriptionChecker.can_create_projects(
    subscription_tier, len(owned_projects)
)
```

### Step 7: Check logic
**Line:** `socrates-api/src/socrates_api/middleware/subscription.py:113`
```
For 1st creation: current_count = 0, max = 1
  if 0 >= 1: False → allow creation ✓

For 2nd creation: current_count = 1, max = 1
  if 1 >= 1: True → DENY creation ✓
  Expected: return False, "Project limit (1) reached for free tier"
```

### Step 8: Check if can create
**Line:** `socrates-api/src/socrates_api/routers/projects.py:200-202`
```
For 2nd creation (should fail):
  if not can_create:  # True
    Expected Log: "User <username> exceeded project limit: Project limit (1) reached for free tier"
    Expected Response: 403 Forbidden
```

### Step 9: If allowed, continue to orchestrator
**Line:** `socrates-api/src/socrates_api/routers/projects.py:214`
```
Expected Log: "Checking if orchestrator is available..."
```

---

## Instructions: Check Your Logs

### 1. Enable Debug Logging
Add this to your logging config:
```python
logging.getLogger("socrates_api.routers.projects").setLevel(logging.DEBUG)
logging.getLogger("socratic_system.subscription.checker").setLevel(logging.DEBUG)
logging.getLogger("socrates_api.middleware.subscription").setLevel(logging.DEBUG)
```

### 2. Create a Test Scenario
1. Create a free tier test user (e.g., `testuser@test.com`)
2. Verify they have 0 projects: `SELECT COUNT(*) FROM projects WHERE owner = 'testuser@test.com'`
3. Create 1st project via API
4. Verify it exists: `SELECT COUNT(*) FROM projects WHERE owner = 'testuser@test.com'` (should be 1)
5. Verify owner field: `SELECT project_id, owner FROM projects WHERE owner = 'testuser@test.com'`
6. Try to create 2nd project via API
7. Check logs for messages

### 3. Look for These Specific Logs

**Expected for 1st project (should succeed):**
```
Checking subscription limits...
Got 0 projects for user testuser@test.com
Subscription validation passed for testuser@test.com (tier: free)
Checking if orchestrator is available...
Project created successfully
```

**Expected for 2nd project (should fail):**
```
Checking subscription limits...
Got 1 projects for user testuser@test.com
User testuser@test.com exceeded project limit: Project limit (1) reached for free tier
Error response: 403 Forbidden
```

---

## Possible Issues

### Issue 1: Missing Log Messages
If you don't see "Checking subscription limits..." log:
- **Cause:** Code changes not deployed or reloaded
- **Fix:** Restart application again, verify file timestamps

### Issue 2: Shows 0 Projects When Should Show 1
If 2nd creation still shows "Got 0 projects":
- **Cause:** Projects not being saved correctly, or get_user_projects not finding them
- **Check:**
  ```sql
  SELECT * FROM projects WHERE owner = 'testuser@test.com';
  ```
  If query returns 0, project was never saved!

### Issue 3: Owner Field is NULL or Wrong Value
If projects exist but owner field is blank/wrong:
- **Cause:** Project saved without owner, or with different username format
- **Check:**
  ```sql
  SELECT project_id, name, owner FROM projects LIMIT 5;
  ```
  Look for NULL owners or username mismatches

### Issue 4: Filter Logic Not Working
If projects exist with correct owner but still can create 2nd:
- **Cause:** Filter `p.owner == current_user` not matching
- **Check:** Verify exact string match in database vs code
  - Username might be: `user@example.com` vs `user`
  - Check both REST API current_user and database owner values

### Issue 5: Wrong Tier in Database
If user is actually "pro" instead of "free":
- **Check:**
  ```sql
  SELECT username, subscription_tier, testing_mode FROM users WHERE username = 'testuser@test.com';
  ```
- **Verify:** subscription_tier = 'free', testing_mode = 0

### Issue 6: Exception Being Caught and Silently Ignored
If something throws an exception in the check block:
- **Look for:** Errors in logs like "Error validating subscription: ..."
- **Would show:** 500 Internal Server Error response

---

## Debug SQL Queries

Run these to understand current state:

```sql
-- Check user tier and testing mode
SELECT username, subscription_tier, testing_mode FROM users WHERE username = '<testusername>';

-- Check projects for user
SELECT project_id, name, owner FROM projects WHERE owner = '<testusername>';

-- Count projects owned by user
SELECT COUNT(*) as owned_count FROM projects WHERE owner = '<testusername>' AND is_archived = 0;

-- Check if any projects exist at all
SELECT COUNT(*) as total_projects FROM projects;

-- Check user projects with all details
SELECT project_id, name, owner, created_at FROM projects WHERE owner = '<testusername>' ORDER BY created_at DESC;
```

---

## Report Format

Please provide:

1. **Logs when creating 2nd project** (paste last 20 lines from app logs)
2. **SQL output** for:
   - User tier query
   - Project count query
   - Project details query
3. **Error response** (full HTTP response when trying to create 2nd project)
4. **Confirmation**: Did you restart after code changes?
