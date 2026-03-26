#!/usr/bin/env python
"""Test app WITHOUT lifespan orchestrator initialization"""
import sys
import os

# Set up path
backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_src)

print("[TEST] Creating app WITHOUT lifespan initialization logic...")

# First, patch main.py to skip orchestrator initialization
import types

# Create a simple lifespan that doesn't initialize orchestrator
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def simple_lifespan(app):
    print("[LIFESPAN] Simple startup")
    yield
    print("[LIFESPAN] Simple shutdown")

# Now import main and modify its lifespan before app is created
# Import the module
import socrates_api.main as main_module

# Replace the lifespan function
main_module.lifespan = simple_lifespan

# Now import the app from main
from socrates_api.main import app

print(f"[TEST] App ready with {len(app.routes)} routes")

# Start serving
if __name__ == "__main__":
    import uvicorn
    print("[TEST] Starting uvicorn...")
    uvicorn.run(app, host="127.0.0.1", port=8803, log_level="info")
