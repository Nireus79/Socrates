#!/usr/bin/env python
"""Minimal test case to reproduce routing issue"""
from fastapi import APIRouter, FastAPI
import uvicorn
import subprocess
import time
import requests
import os
import sys

# Create minimal app
app = FastAPI(title="MinimalTest")

# Create router with prefix
test_router = APIRouter(prefix="/test", tags=["test"])

@test_router.get("/endpoint")
async def test_endpoint():
    return {"message": "test endpoint"}

# Include router AT MODULE LEVEL (like socrates_api does)
app.include_router(test_router)

# Direct endpoint
@app.get("/direct")
async def direct_endpoint():
    return {"message": "direct endpoint"}

print(f"App has {len(app.routes)} routes")
print("Routes in app.routes:")
for r in app.routes:
    if hasattr(r, 'path'):
        print(f"  {r.path}")

# Start server in subprocess
print("\nStarting uvicorn...")
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', '__main__:app', '--host', '127.0.0.1', '--port', '8765'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=os.path.dirname(__file__)
)

time.sleep(5)

try:
    print("\nTesting routes via HTTP:")
    tests = [
        ("/direct", "Direct endpoint"),
        ("/test/endpoint", "Router endpoint"),
    ]

    for path, desc in tests:
        try:
            r = requests.get(f"http://127.0.0.1:8765{path}", timeout=2)
            status = "OK" if r.status_code != 404 else "FAIL"
            print(f"  {desc:30} {path:30} {r.status_code} {status}")
        except Exception as e:
            print(f"  {desc:30} {path:30} ERROR: {type(e).__name__}")

finally:
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except:
        proc.kill()
