# Phase 2 Critical Blocker: Route Registration Issue

**Status**: BLOCKED - Systematic FastAPI routing issue
**Date**: 2025-12-27
**Impact**: All Phase 2 new endpoints (Chat Sessions, Knowledge Documents, Collaborator Invitations)

---

## The Problem

New routes added to existing FastAPI routers are NOT being registered with the FastAPI app at startup, even though:
- ✅ Code syntax is valid
- ✅ Decorators are correctly formatted (@router.post, @router.get, etc.)
- ✅ Request models are properly defined
- ✅ Routes appear in router.routes when inspected
- ✅ Router is properly imported and included in main.py
- ✅ Multiple cache clears and backend restarts attempted
- ❌ Routes do NOT appear in OpenAPI schema
- ❌ Requests return 404 (route not found)
- ❌ Endpoint functions are never called (verified with logging)

## Evidence

### Working Routes (Phase 1):
```
✅ GET /projects/{id}/chat/question
✅ POST /projects/{id}/chat/message
✅ GET /projects/{id}/chat/history
✅ PUT /projects/{id}/chat/mode
✅ GET /projects/{id}/chat/hint
✅ DELETE /projects/{id}/chat/clear
✅ GET /projects/{id}/chat/summary
✅ POST /projects/{id}/chat/search
```

### Broken Routes (Phase 2):
```
❌ POST /projects/{id}/chat/sessions     (404 - not found)
❌ GET /projects/{id}/chat/sessions      (404 - not found)
❌ GET /projects/{id}/chat/sessions/{id} (404 - not found)
❌ DELETE /projects/{id}/chat/sessions/{id} (404 - not found)
❌ POST /projects/{id}/chat/{id}/message (404 - not found)
❌ GET /projects/{id}/chat/{id}/messages (404 - not found)
```

### Broken Routes (Collaborator):
```
❌ POST /projects/{id}/collaborators     (422 - validation error, expects old signature)
```

### Broken Routes (Knowledge):
```
❌ POST /projects/{id}/knowledge/documents (405 - method not allowed)
```

## Root Cause Analysis

The issue appears to be in how FastAPI discovers and registers routes at **application startup**:

1. **Theory**: FastAPI reads function signatures and registers routes at app instantiation time
2. **Evidence**: Routes defined early in routers (Phase 1) work; routes added later (Phase 2) don't
3. **Pattern**: ALL new routes added to existing routers fail this way (collaborator, knowledge, chat sessions)
4. **Hypothesis**: The app may load and register routes from routers BEFORE certain code paths complete, or Python module caching prevents new definitions from being picked up

## Verification Done

```python
# ✅ Router object has the routes
from socrates_api.routers import projects_chat
for route in projects_chat.router.routes:
    if 'sessions' in route.path:
        print(f"{route.path} {route.methods}")
# Output: ✅ Found chat/sessions POST, GET, etc.

# ❌ But FastAPI app doesn't know about them
curl http://localhost:8000/projects/{id}/chat/sessions
# Output: ❌ 404 Not Found

# ❌ OpenAPI schema doesn't list them
curl http://localhost:8000/openapi.json | grep "chat/sessions"
# Output: ❌ No results
```

## What Was Tried

1. ✅ Cleared all `__pycache__` directories
2. ✅ Cleared all `.pyc` and `.pyo` files
3. ✅ Set `PYTHONDONTWRITEBYTECODE=1` environment variable
4. ✅ Restarted backend 10+ times with fresh Python processes
5. ✅ Renamed functions to bypass caching (add_collaborator → add_collaborator_new)
6. ✅ Added explicit `Body(...)` specifications
7. ✅ Verified router imports and registration
8. ✅ Checked function signatures and decorators
9. ✅ Added debug logging
10. ✅ Attempted reordering endpoints in source file

**Result**: All attempts failed. Routes still not registered.

## Solution Paths (for investigation)

### Option A: Fresh Environment (Recommended)
- Clone repo to new directory
- Create fresh virtualenv
- Run backend from clean state
- Test if Phase 2 routes register properly
- **Time**: 30-60 minutes
- **Success rate**: 50% (may reveal environment-specific issue)

### Option B: Application-Level Route Reload
- Implement route refresh mechanism in FastAPI app
- Call after app startup to catch newly defined routes
- **Complexity**: Medium
- **Risk**: Could have performance implications

### Option C: Move Phase 2 to Separate Router
- Create new dedicated routers for each Phase 2 feature
- Don't add to existing routers
- **Complexity**: Low
- **Trade-off**: Slightly different architecture

### Option D: Implement as Middleware
- Use custom middleware to handle new routes
- Register before FastAPI discovers routes
- **Complexity**: High
- **Risk**: Architectural change required

## Recommended Next Step

**Option C** is the lowest-risk, highest-probability solution:

```python
# Instead of adding to projects_chat_router (existing):
@projects_chat_router.post("/...")  # ❌ Broken

# Create new dedicated router:
chat_sessions_router = APIRouter(prefix="/projects", tags=["chat-sessions"])

@chat_sessions_router.post("/{project_id}/chat/sessions")  # ✅ Should work
async def create_chat_session(...):
    ...

# Then in main.py:
app.include_router(chat_sessions_router)
```

## Phase 2 Status

**Blocked**: Cannot proceed with standard router-based endpoint additions
**Workaround**: Use separate routers for each Phase 2 feature group
**Impact**: Adds ~1-2 hours for refactoring; doesn't delay feature implementation

---

## Files Affected

- `socrates-api/src/socrates_api/routers/projects_chat.py` (Phase 2 endpoints defined but not registered)
- `socrates-api/src/socrates_api/routers/collaboration.py` (Phase 2 collaborator endpoints defined but not registered)
- `socrates-api/src/socrates_api/routers/knowledge_management.py` (Phase 2 knowledge endpoints defined but not registered)

## Test Results

**Phase 1 (Working)**: 11/15 tests passing (73.3%)
**Phase 2 (Blocked)**: 0/4 tests passing (0%) - all fail with 404 or route registration errors

---

**Next Action**: Implement Option C (separate routers) and re-test Phase 2 endpoints

Generated: 2025-12-27 20:45 UTC
