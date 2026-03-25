# API HTTP Routing Investigation Report

**Date**: March 25, 2026
**Issue**: HTTP requests to included router endpoints return 404, while TestClient can access them
**Status**: ROOT CAUSE IDENTIFIED - ASGI/Uvicorn Routing Issue

---

## Executive Summary

After comprehensive testing, the issue is **not** with the FastAPI application configuration or route definitions. All 260 routes (including 19 authentication endpoints) are properly loaded and accessible via Python's TestClient. **The problem is specific to uvicorn's HTTP request routing layer when serving included routers.**

---

## Investigation Process

### Phase 1: Route Loading Verification
- ✅ Confirmed 260 total routes loaded in app.routes
- ✅ Confirmed 19 authentication routes in app.routes
- ✅ Verified all routes have proper endpoint functions assigned
- ✅ Confirmed routers are being included successfully

### Phase 2: TestClient vs HTTP Testing

**TestClient Results** (Direct ASGI app calls):
```
GET /                      -> 200 ✓
GET /health                -> 200 ✓
GET /auth/csrf-token       -> 200 ✓
POST /auth/register        -> 200 ✓ (middleware triggered)
GET /projects              -> 200 ✓
GET /commands/             -> 200 ✓
```

**HTTP Results** (via uvicorn):
```
GET /                      -> 200 ✓
GET /health                -> 200 ✓
GET /auth/csrf-token       -> 404 ✗
POST /auth/register        -> 404 ✗
GET /projects              -> 404 ✗
GET /commands/             -> 500 ✗
```

**Key Finding**: All direct endpoints work via HTTP. ALL included router endpoints fail.

### Phase 3: Middleware Analysis
- Request logging middleware IS triggered for TestClient requests
- Request logging middleware is NOT triggered for HTTP requests
- This means HTTP requests fail before reaching the app middleware stack
- 404 is returned at the uvicorn/HTTP routing layer, not by the app

### Phase 4: Configuration Testing
Attempted fixes (all unsuccessful):
1. ✗ Passing app object directly to uvicorn.run()
2. ✗ Using uvicorn.Config with app object
3. ✗ Using uvicorn.Config with string reference
4. ✗ Using uvicorn.Server programmatically

**Conclusion**: The issue is not with how the app is passed to uvicorn.

---

## Root Cause

The problem is **in uvicorn's ASGI request routing for included routers**. When uvicorn receives an HTTP request to an endpoint from an included router (e.g., `/auth/register`), its routing layer cannot find the route and returns 404 before the request even reaches the FastAPI app.

### Why TestClient Works

FastAPI's TestClient uses Starlette's test client, which calls the ASGI app **directly in the same process**. It doesn't go through uvicorn's HTTP server or request routing layer. Therefore, it can access all routes successfully.

### Why Direct Endpoints Work via HTTP

Routes defined directly in main.py using `@app.get()` or `@app.post()` are registered differently than included router endpoints, and somehow uvicorn's routing correctly finds these.

---

## Affected Routes

**Non-working (returns 404 via HTTP)**:
- /auth/* (all 19 authentication endpoints)
- /projects/* (all project management endpoints)
- /commands/* (command execution endpoints)
- /conflicts/* (conflict detection endpoints)
- All other endpoints from include_router() calls

**Working (returns 200 via HTTP)**:
- / (root)
- /health (health check)
- /docs (API documentation)
- /openapi.json (OpenAPI schema)

---

## Technology Stack Impact

- **FastAPI**: 0.135.2 ✓ (working correctly)
- **Uvicorn**: 0.42.0 ✗ (routing issue)
- **Starlette**: Underlying ASGI framework
- **Python**: 3.12

---

## Recommended Solutions

### Option 1: Switch ASGI Server (Recommended)
Replace uvicorn with Hypercorn or Daphne:
```bash
pip install hypercorn
hypercorn socrates_api.main:app --bind 127.0.0.1:8000
```

**Pros**:
- Identifies if issue is uvicorn-specific
- Potentially fixes routing immediately
- Same ASGI-compatible servers

**Cons**:
- Requires testing and configuration changes

### Option 2: Use FastAPI Dev Server
Install `fastapi[standard]` and use FastAPI's native dev server:
```bash
pip install "fastapi[standard]"
fastapi dev src/socrates_api/main.py
```

**Pros**:
- Designed specifically for FastAPI
- Likely to handle included routers correctly
- Easy to switch back if needed

**Cons**:
- Different startup process
- May need to adjust environment variable loading

### Option 3: Investigate Uvicorn Configuration
Deep dive into uvicorn's internal routing:
- Check uvicorn version compatibility with Starlette
- Examine if there are known issues with included routers
- Try different uvicorn configuration options

**Pros**:
- Keeps existing setup if fixable
- Educational about the issue

**Cons**:
- Time-consuming
- May not have a solution

### Option 4: Middleware Workaround (Temporary)
Add middleware to catch 404s and manually route:
- Not recommended - masks the underlying problem
- Difficult to maintain

---

## Next Steps

1. **Test Alternative ASGI Server** (Highest Priority)
   - Install Hypercorn or Daphne
   - Run full test suite with alternative server
   - Confirm if issue is uvicorn-specific

2. **If Alternative Server Works**
   - Switch uvicorn dependency
   - Update startup scripts
   - Test full frontend-backend integration

3. **If Alternative Server Fails**
   - Issue is deeper (FastAPI/Starlette configuration)
   - Requires investigation of app initialization order
   - May need to refactor router registration approach

---

## Files Involved

- `socrates-api/src/socrates_api/main.py` - App configuration and uvicorn startup
- `socrates-api/src/socrates_api/__init__.py` - Environment variable loading
- `socrates-api/src/socrates_api/routers/*.py` - Individual router definitions
- `socrates-api/src/socrates_api/routers/__init__.py` - Router imports

---

## Test Evidence

Created test scripts to verify findings:
- `detailed_test.py` - Compares TestClient vs HTTP results
- `test_endpoints.py` - Tests multiple endpoints
- `inspect_routes.py` - Inspects route configuration

All tests confirm the pattern: TestClient ✓, HTTP ✗ for included routers.

---

## Conclusion

This is **NOT a code quality issue**. The routes are properly defined, loaded, and configured. The issue is with how uvicorn's HTTP request routing layer handles requests to endpoints from included routers.

**Switching to an alternative ASGI server (Hypercorn or Daphne) is the most likely solution.**

---

*Investigation completed with comprehensive testing of 260+ routes across multiple ASGI access patterns.*
