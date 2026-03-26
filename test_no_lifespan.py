#!/usr/bin/env python
"""Test socrates_api app WITHOUT lifespan to see if that's the issue"""
import sys
import os

os.chdir(os.path.dirname(__file__))
sys.path.insert(0, "backend/src")

# Monkey-patch: Create a dummy lifespan
from contextlib import asynccontextmanager

@asynccontextmanager
async def dummy_lifespan(app):
    print("[TEST] Dummy lifespan starting")
    yield
    print("[TEST] Dummy lifespan ending")

# Now import and modify the app
from socrates_api import main as main_module

# Replace the lifespan with a dummy one
if hasattr(main_module, 'lifespan'):
    main_module.lifespan = dummy_lifespan

# Now create the app WITHOUT the complex lifespan
from fastapi import FastAPI
app = FastAPI(title="TestNoLifespan", lifespan=dummy_lifespan)

# Import and attach all the routers
from socrates_api.routers import auth_router, projects_router

app.include_router(auth_router)
app.include_router(projects_router)

@app.get("/direct")
async def direct():
    return {"ok": True}

# Test it
import subprocess, time, requests

print(f"[TEST] App has {len(app.routes)} routes")

proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'test_no_lifespan:app', '--host', '127.0.0.1', '--port', '8777'],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(5)

try:
    for path in ['/', '/direct', '/auth/csrf-token', '/projects']:
        try:
            r = requests.get(f'http://127.0.0.1:8777{path}', timeout=2)
            print(f'{path:30} {r.status_code}')
        except Exception as e:
            print(f'{path:30} ERROR')
finally:
    proc.terminate()
