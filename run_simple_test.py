#!/usr/bin/env python
"""Run simple lifespan test"""
import subprocess
import sys
import time
import requests
import os

backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')

print("[TEST] Starting simple lifespan test server...")
proc = subprocess.Popen(
    [sys.executable, 'test_simple_lifespan.py'],
    cwd=os.path.dirname(__file__),
    env={**os.environ, 'PYTHONPATH': backend_src},
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print(f"[TEST] Process started with PID {proc.pid}")
print(f"[TEST] Waiting for startup...")

# Read startup messages
for i in range(30):
    try:
        line = proc.stdout.readline()
        if line:
            print(f"[STARTUP] {line.rstrip()}")
        if 'Uvicorn running' in line or 'Application startup complete' in line:
            print(f"[TEST] Server appears to be running!")
            break
    except:
        break

time.sleep(3)

try:
    print("\n[TEST] Testing HTTP routes:")
    for path in ['/direct', '/auth/csrf-token', '/projects']:
        try:
            r = requests.get(f'http://127.0.0.1:8801{path}', timeout=2)
            status = "OK" if r.status_code != 404 else "FAIL"
            print(f'{path:30} {r.status_code:3} {status}')
        except Exception as e:
            print(f'{path:30} ERROR: {type(e).__name__}')
finally:
    proc.terminate()
    time.sleep(1)
    if proc.poll() is None:
        proc.kill()
