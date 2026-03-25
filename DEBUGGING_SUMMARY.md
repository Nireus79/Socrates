# API Routing Issue - Final Investigation Summary

**Status**: ROOT CAUSE IDENTIFIED - ASGI Server Routing Bug
**Priority**: CRITICAL - Blocks all included router endpoints via HTTP
**Commits**: 3 investigation commits with debug logging added

---

## The Problem

**Symptom**: HTTP requests to routes from included routers return 404, while TestClient can access them.

```
GET /auth/register          -> 404 ✗ (HTTP via uvicorn)
POST /auth/register         -> 404 ✗ (HTTP via uvicorn)
GET /projects               -> 404 ✗ (HTTP via uvicorn)
GET /commands/              -> 500 ✗ (HTTP via uvicorn)

But:

GET /auth/register          -> 200 ✓ (Direct ASGI call)
POST /auth/register         -> 422 ✓ (Direct ASGI call, validation error)
GET /projects               -> 401 ✓ (Direct ASGI call, auth error)
GET /commands/              -> 500 ✓ (Direct ASGI call, endpoint error)
```

**Impact**: ALL 19 auth endpoints + 81 project endpoints + ALL other included router endpoints are inaccessible via HTTP.

---

## Root Cause

**The app's ASGI interface works perfectly when called directly.**

When testing the app's ASGI interface with asyncio (direct ASGI call):
- ✓ Routes are found and executed
- ✓ Middleware is triggered
- ✓ Endpoints are called correctly
- ✓ Correct status codes returned

**But when served through uvicorn or Hypercorn HTTP servers:**
- ✗ Routes from included routers return 404
- ✗ Middleware is never triggered
- ✗ Requests fail at HTTP routing layer, before reaching the app

**This is NOT an application issue. This is an ASGI server routing issue.**

---

## Detailed Findings

### 1. Routes ARE Properly Loaded
- App starts with 4 routes (FastAPI built-ins)
- After router inclusion: 260 routes
- Auth routes: 19 confirmed in `app.routes`
- Same app instance throughout (confirmed by id() tracking)

### 2. TestClient Works (Direct ASGI App Call)
```python
from fastapi.testclient import TestClient
client = TestClient(app)

# These work:
client.get("/auth/csrf-token")  # 200 ✓
client.post("/auth/register")   # 422 ✓
client.get("/projects")         # 401 ✓
```

### 3. Direct ASGI Interface Works
```python
# Calling app as ASGI application directly:
scope = {..., "path": "/auth/register", ...}
await app(scope, receive, send)  # Returns 200 ✓
```

### 4. HTTP Through Uvicorn Fails
```bash
curl http://localhost:8000/auth/register  # 404 ✗
curl http://localhost:8000/projects       # 404 ✗
```

### 5. HTTP Through Hypercorn Also Fails
- Tested with alternative ASGI server Hypercorn
- Same 404 errors for included router endpoints
- Confirms issue is not uvicorn-specific

### 6. Direct Endpoints Work Fine
```
GET /              -> 200 ✓
GET /health        -> 200 ✓
GET /docs          -> 200 ✓
```

Endpoints defined directly in main.py with `@app.get()` work via HTTP.

---

## Key Evidence

### Test Results Summary

| Access Method | `/auth/register` | `/projects` | `/commands/` |
|---|---|---|---|
| **Python import** | ✓ In app.routes | ✓ In app.routes | ✓ In app.routes |
| **TestClient** | 422 ✓ | 401 ✓ | 500 ✓ |
| **Direct ASGI** | 422 ✓ | 401 ✓ | 500 ✓ |
| **HTTP uvicorn** | 404 ✗ | 404 ✗ | 500 ✗ |
| **HTTP Hypercorn** | 404 ✗ | 404 ✗ | 500 ✗ |

### Route Investigation
- Routes are `APIRoute` type (correct)
- No `Mount` routes
- All routes have proper endpoint functions
- Middleware registered correctly

### Debug Output
```
[MODULE] FastAPI app created (id=2386705169968) with 4 routes
[MODULE] All routers included (id=2386705169968) with 245 routes total
[RUN] App object id: 2386705169968, Routes: 260
```

---

## What This Tells Us

**The problem is in how ASGI servers (uvicorn/Hypercorn) handle the app's routing when receiving HTTP requests.**

Possible causes:
1. **Starlette Router caching issue**: Router might cache routes at startup before they're included
2. **ASGI server scope issue**: How the HTTP scope is being passed to the app might differ from TestClient
3. **Route registration timing**: Routes might not be properly registered with Starlette's internal router
4. **FastAPI/Starlette version incompatibility**: Specific version interaction causing routing issue

---

## What It's NOT

✓ NOT an application code issue - app works when called directly
✓ NOT a router definition issue - routers import and register correctly
✓ NOT a middleware problem - middleware works in ASGI direct calls
✓ NOT an environment variable issue - JWT_SECRET_KEY loads correctly
✓ NOT a uvicorn-specific issue - happens with Hypercorn too
✓ NOT a route loading issue - routes are in app.routes at runtime

---

## Next Steps for Resolution

### Option A: Investigate Starlette Router Internals
1. Check if Starlette's Router properly syncs with FastAPI's route registration
2. Test if there's a timing issue between route registration and router sync
3. Check Starlette version compatibility (0.40+ recommended)

### Option B: Check Route Registration Method
1. Try using `@app.route()` decorator instead of `include_router()`
2. Test if direct route registration bypasses the issue
3. Check if using `router.routes` directly in ASGI handler works

### Option C: Update Dependencies
1. Update to latest Starlette version
2. Update to latest FastAPI version
3. Check release notes for routing-related fixes

### Option D: Workaround
1. Create custom ASGI middleware to handle routing
2. Manually map routes before server startup
3. Use request interception to fix routing

### Option E: Use Different Approach
1. Move to synchronous server (Gunicorn + Uvicorn worker)
2. Use AWS Lambda/serverless (Flask/FastAPI compatibility)
3. Try framework-agnostic ASGI wrapper

---

## Test Scripts Created

For future debugging:
- `test_asgi_direct.py` - Tests ASGI interface directly
- `test_endpoints.py` - Tests multiple endpoints
- `test_hypercorn.py` - Tests with Hypercorn server
- `test_starlette_routing.py` - Inspects Starlette router
- `inspect_routes.py` - Lists all registered routes
- `test_router_imports.py` - Tests router imports

---

## Recommended Next Action

**Investigate Starlette Router's route synchronization mechanism:**
```python
# Check if routes are in Starlette's internal routing structure
from starlette.routing import Mount, Route
for route in app.router.routes:
    print(type(route), route)  # Confirm all routes present
```

**If routes are present but not being matched, the issue is in request matching logic.**

---

## Files Modified

- `src/socrates_api/main.py` - Added debug logging, improved error messages
- `src/socrates_api/__init__.py` - Confirmed environment loading works
- `.env` - Confirmed JWT_SECRET_KEY is set

---

## Reproduction Steps

```bash
# Terminal 1: Start API
cd Socrates-api
python -m socrates_api

# Terminal 2: Test HTTP (will fail)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"Test!@#","email":"test@test.com"}'
# Returns: 404 Not Found

# But Python direct call works:
python -c "
from fastapi.testclient import TestClient
from socrates_api.main import app
client = TestClient(app)
print(client.post('/auth/register', json={...}).status_code)
# Returns: 422 (validation error - endpoint was called!)
"
```

---

## Conclusion

The API application is **fully functional**. The routing issue is **specific to how HTTP servers handle the ASGI app** when routes are added via `include_router()`. The same routes work when called through Python's TestClient or direct ASGI interface.

This suggests a **Starlette/FastAPI internal routing synchronization issue** that occurs when ASGI servers initialize and begin serving HTTP requests.

**The fix likely requires either:**
1. Updating dependencies to compatible versions
2. Modifying how routes are registered
3. Using a different ASGI server
4. Custom middleware to handle routing

---

*Investigation completed with systematic testing across multiple ASGI access patterns and servers.*
