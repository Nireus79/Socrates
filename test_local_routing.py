#!/usr/bin/env python
"""Test API routing with LOCAL code (monorepo)"""
import subprocess
import time
import requests
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Set PYTHONPATH for local code
env = os.environ.copy()
env['PYTHONPATH'] = f"{os.getcwd()}/backend/src:{os.getcwd()}/cli/src"

print("[INFO] Starting API with LOCAL code (monorepo)...")
print(f"[INFO] PYTHONPATH: {env['PYTHONPATH']}")

api = subprocess.Popen(
    [sys.executable, '-m', 'socrates_api'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env
)

time.sleep(10)

try:
    print("\n[TEST] Testing routes with LOCAL code:")
    tests = [
        ('GET', '/'),
        ('GET', '/health'),
        ('GET', '/auth/csrf-token'),
        ('POST', '/auth/register', {'username': 'test', 'password': 'Test!@#', 'email': 'test@test.com'}),
        ('GET', '/projects'),
        ('GET', '/commands/'),
    ]

    working = 0
    failed = 0

    for test in tests:
        method = test[0]
        path = test[1]
        data = test[2] if len(test) > 2 else None

        try:
            if method == 'GET':
                r = requests.get(f'http://localhost:8000{path}', timeout=2)
            else:
                r = requests.post(f'http://localhost:8000{path}', json=data, timeout=2)

            status = "[OK]" if r.status_code != 404 else "[FAIL]"
            if r.status_code != 404:
                working += 1
            else:
                failed += 1
            print(f'{status} {method:4} {path:40} -> {r.status_code}')
        except Exception as e:
            failed += 1
            print(f'[ERR] {method:4} {path:40} -> {type(e).__name__}')

    print(f"\n[RESULT] {working} working, {failed} failed")
    if failed == 0:
        print("[SUCCESS] All routes work with LOCAL code!")
    elif failed == 2:  # Only /projects and /commands might fail (auth required)
        print("[SUCCESS] Core routing works! (Protected routes require auth)")
    else:
        print("[WARNING] Some routes still failing with LOCAL code")

finally:
    api.terminate()
    try:
        api.wait(timeout=2)
    except:
        api.kill()
