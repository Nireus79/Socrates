#!/usr/bin/env python
"""Test if middleware is causing the routing issue"""
from fastapi import APIRouter, FastAPI, Request
import uvicorn
import subprocess
import time
import requests
import os

# Create app with same middleware pattern as socrates_api
app = FastAPI(title="MiddlewareTest")

# Add middleware BEFORE including router (like socrates_api does)
@app.middleware("http")
async def test_middleware(request: Request, call_next):
    response = await call_next(request)
    return response

# Create router
test_router = APIRouter(prefix="/test")

@test_router.get("/endpoint")
async def test_endpoint():
    return {"message": "works"}

# Include router
app.include_router(test_router)

# Direct endpoint
@app.get("/direct")
async def direct_endpoint():
    return {"message": "direct"}

# Run it
if __name__ == "__main__":
    proc = subprocess.Popen([f"python -c \"from test_middleware_issue import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8766)\""], 
                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)
    try:
        for path, desc in [('/direct', 'Direct'), ('/test/endpoint', 'Router')]:
            try:
                r = requests.get(f'http://127.0.0.1:8766{path}', timeout=2)
                print(f'{desc:20} {r.status_code}')
            except:
                print(f'{desc:20} ERROR')
    finally:
        proc.terminate()
