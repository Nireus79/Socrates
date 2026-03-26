#!/usr/bin/env python
"""Test if uvicorn startup hangs"""
import sys
import os
import time

# Set up path
backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_src)

from fastapi import FastAPI
from contextlib import asynccontextmanager

# Simple lifespan
@asynccontextmanager
async def simple_lifespan(app: FastAPI):
    print("[LIFESPAN] Starting up...")
    yield
    print("[LIFESPAN] Shutting down...")

print("[TEST] Creating app...")
app = FastAPI(title="TestUvicornStart", lifespan=simple_lifespan)

print("[TEST] Including routers...")
from socrates_api import routers
app.include_router(routers.auth_router)
app.include_router(routers.projects_router)

@app.get("/direct")
async def direct():
    return {"message": "direct"}

print(f"[TEST] App ready with {len(app.routes)} routes")

print("[TEST] Starting uvicorn...")
import uvicorn

print(f"[TEST] About to call uvicorn.run()")
start = time.time()
try:
    # Use server instance approach instead of direct run
    config = uvicorn.Config(app, host="127.0.0.1", port=8802, log_level="critical")
    server = uvicorn.Server(config)
    print(f"[TEST] Server instance created, calling serve()...")
    # This will block until shutdown
    import asyncio
    asyncio.run(server.serve())
except KeyboardInterrupt:
    print("[TEST] Interrupted by KeyboardInterrupt")
except Exception as e:
    elapsed = time.time() - start
    print(f"[TEST] Error ({elapsed:.2f}s): {e}")
