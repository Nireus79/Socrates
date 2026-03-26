#!/usr/bin/env python
"""Test socrates_api WITHOUT complex lifespan"""
import sys
import os

# Set up path
backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_src)

print("[TEST] Creating simple FastAPI app...")
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Simple lifespan - no complex async tasks
@asynccontextmanager
async def simple_lifespan(app: FastAPI):
    print("[LIFESPAN] Starting up...")
    yield
    print("[LIFESPAN] Shutting down...")

# Create app with simple lifespan
app = FastAPI(title="SimpleTest", lifespan=simple_lifespan)

print("[TEST] App created. Now including routers...")

# Import and add just auth router
try:
    from socrates_api.routers import auth_router, projects_router
    app.include_router(auth_router)
    print("[TEST] Auth router included")
    app.include_router(projects_router)
    print("[TEST] Projects router included")
except Exception as e:
    print(f"[ERROR] Failed to include routers: {e}")

@app.get("/direct")
async def direct_endpoint():
    return {"message": "direct works"}

print(f"[TEST] App has {len(app.routes)} routes")

# Start server
if __name__ == "__main__":
    import uvicorn
    print("[TEST] Starting uvicorn...")
    uvicorn.run(app, host="127.0.0.1", port=8801, log_level="warning")
