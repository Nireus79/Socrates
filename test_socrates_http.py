#!/usr/bin/env python
"""Test socrates_api HTTP routing with proper Python path setup"""
import sys
import os
import subprocess
import time
import requests

# Add backend/src to path
backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_src)

print(f"[TEST] PYTHONPATH set to: {backend_src}")
print(f"[TEST] sys.path[0]: {sys.path[0]}")

# Now start the app
print("\n[TEST] Starting uvicorn with socrates_api...")
proc = subprocess.Popen(
    [sys.executable, '-c', f'''
import sys
sys.path.insert(0, r"{backend_src}")
from socrates_api.main import app
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8800, log_level="warning")
'''],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(6)

try:
    print("\n[TEST] Testing HTTP routes:")
    for path in ['/', '/health', '/auth/csrf-token', '/projects']:
        try:
            r = requests.get(f'http://127.0.0.1:8800{path}', timeout=2)
            status = "OK" if r.status_code != 404 else "FAIL"
            print(f'{path:30} {r.status_code:3} {status}')
        except Exception as e:
            print(f'{path:30} ERROR: {type(e).__name__}')
finally:
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except:
        proc.kill()
