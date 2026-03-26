#!/usr/bin/env python
"""Detailed test of routing to find the issue"""
import subprocess
import time
import requests
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

env = os.environ.copy()
env['PYTHONPATH'] = f"{os.getcwd()}/backend/src:{os.getcwd()}/cli/src"

# Start server and capture all output
print("[TEST] Starting API server...")
api = subprocess.Popen(
    [sys.executable, '-m', 'socrates_api'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=env
)

time.sleep(12)

try:
    # Test each type of route
    tests = [
        # Direct endpoints (work)
        ("GET", "/", "Direct root"),
        ("GET", "/health", "Direct health"),
        ("GET", "/debug/routes", "Debug endpoint"),
        
        # Included router endpoints (fail)
        ("GET", "/auth/csrf-token", "Auth router"),
        ("GET", "/projects", "Projects router"),
        ("GET", "/commands/", "Commands router"),
    ]
    
    print("\n[RESULTS] HTTP Routing Test:")
    print("-" * 80)
    
    for method, path, desc in tests:
        try:
            if method == "GET":
                r = requests.get(f"http://localhost:8000{path}", timeout=2)
            else:
                r = requests.post(f"http://localhost:8000{path}", timeout=2)
            
            status_text = "✓ WORKS" if r.status_code != 404 else "✗ FAILS"
            print(f"{desc:30} {path:30} {r.status_code:3} {status_text}")
            
        except Exception as e:
            print(f"{desc:30} {path:30} ERR {str(e)[:20]}")

finally:
    api.terminate()
    try:
        api.wait(timeout=2)
    except:
        api.kill()
