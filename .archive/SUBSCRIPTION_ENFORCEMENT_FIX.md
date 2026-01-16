# Subscription Limit Enforcement - Critical Gap Fixed

## Issue Found

Free tier users were able to create multiple projects despite subscription limits being set to 1 project maximum. Investigation revealed a **critical security gap** in the GitHub import endpoint.

## Root Cause

The REST API endpoint `POST /github/import` (socrates-api/src/socrates_api/routers/github.py, lines 203-218) was creating projects WITHOUT checking subscription limits.

### Vulnerable Code Path
```python
# socrates-api/src/socrates_api/routers/github.py:203-218
project = ProjectContext(
    project_id=f"proj_{repo_name.lower()}",
    name=project_name,
    owner=current_user,
    ...
)

# Saved directly without subscription check!
db.save_project(project)
```

This allowed users to bypass the 1-project-per-free-user limit by importing repositories via GitHub instead of creating projects normally.

## Affected Code Paths

### Protected (Already Had Enforcement)
1. ✅ `POST /projects` - Main project creation endpoint (lines 194-202, 286-293)
2. ✅ `ProjectManagerAgent._create_project()` - Agent-based creation (lines 106-111)
3. ✅ `ProjectManagerAgent._create_from_github()` - Agent GitHub import (line 302)

### Unprotected (Security Gap - NOW FIXED)
4. ❌ `POST /github/import` - GitHub repository import endpoint

## Fix Applied

Added comprehensive subscription limit checking to `POST /github/import` endpoint **before** project creation:

```python
# NEW CODE (socrates-api/src/socrates_api/routers/github.py:149-184)

# CRITICAL: Check subscription limit BEFORE attempting to create project
logger.info("Checking subscription limits for GitHub import...")
try:
    from socrates_api.routers.projects import get_current_user_object
    from socratic_system.subscription.checker import SubscriptionChecker

    user_object = get_current_user_object(current_user)

    # Determine subscription tier - default to free if user not in DB yet
    subscription_tier = "free"
    if user_object:
        subscription_tier = getattr(user_object, "subscription_tier", "free")

    # Check project limit for subscription tier (testing mode checked via database flag)
    # If testing mode is enabled in database, bypass subscription checks
    testing_mode_enabled = getattr(user_object, "testing_mode", False) if user_object else False
    if not testing_mode_enabled:
        # Count only OWNED projects for tier limit, not collaborated projects
        all_projects = db.get_user_projects(current_user)
        owned_projects = [p for p in all_projects if p.owner == current_user]
        can_create, error_msg = SubscriptionChecker.can_create_projects(
            subscription_tier, len(owned_projects)
        )
        if not can_create:
            logger.warning(f"User {current_user} exceeded project limit via GitHub import: {error_msg}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)

    logger.info(f"Subscription validation passed for {current_user} (tier: {subscription_tier})")
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Error validating subscription for GitHub import: {type(e).__name__}: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error validating subscription: {str(e)[:100]}",
    )
```

## Key Enforcement Details

The fix ensures:
1. **Consistent Limit Checking**: GitHub import now uses same SubscriptionChecker as main endpoint
2. **Owned Projects Only**: Counts only projects where `owner == current_user` (ignores collaborated projects)
3. **Testing Mode Bypass**: Respects testing mode flag - if enabled, no limits apply
4. **Clear Error Messages**: Returns HTTP 403 Forbidden with descriptive error message
5. **Comprehensive Logging**: Logs subscription validation at each step for audit trail

## Test Verification

To verify the fix works correctly:

### Test Case 1: Free User - First Project (Should Succeed)
```bash
1. Create test user with free tier
2. POST /github/import with valid GitHub URL
3. Expected: ✅ Project created successfully
4. Status: 201 Created
```

### Test Case 2: Free User - Second Project (Should Fail)
```bash
1. User has 1 owned project already
2. POST /github/import with different GitHub URL
3. Expected: ❌ HTTP 403 Forbidden
4. Message: "Project limit (1) reached for free tier"
```

### Test Case 3: Pro User - Multiple Projects (Should Succeed)
```bash
1. Upgrade user to pro tier (10 project limit)
2. POST /github/import (1st, 2nd, ... 10th repo)
3. Expected: ✅ All projects created successfully
4. 11th import: ❌ HTTP 403 Forbidden with "Project limit (10) reached"
```

### Test Case 4: Testing Mode - Bypass (Should Always Succeed)
```bash
1. Enable testing mode: PUT /subscription/testing-mode?enabled=true
2. POST /github/import (even if already at limit)
3. Expected: ✅ Project created, limits bypassed
4. Logs show: "Testing mode enabled - subscription restrictions bypassed"
```

## Files Modified

- **socrates-api/src/socrates_api/routers/github.py**
  - Lines 149-184: Added subscription limit validation before project creation
  - Follows same pattern as main POST /projects endpoint for consistency

## Impact

- **Before**: Users could create unlimited projects via GitHub import
- **After**: GitHub import respects subscription tier limits (1 for free, 10 for pro, unlimited for enterprise)
- **Severity**: HIGH - Security fix that closes critical quota bypass
- **Backward Compatibility**: No change to API response format; only adds proper validation

## Deployment Notes

1. Restart Socrates application to load code changes
2. No database migration needed
3. Existing projects are unaffected
4. Future GitHub imports will be limited per subscription tier

## Related Code

- Subscription checker logic: `socratic_system/subscription/checker.py:can_create_projects()`
- Tier limits: `socratic_system/subscription/tiers.py:TIER_FEATURES`
- Main project creation: `socrates-api/src/socrates_api/routers/projects.py:create_project()`
