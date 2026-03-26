#!/usr/bin/env python
"""Test with detailed logging"""
import subprocess
import time
import requests
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

env = os.environ.copy()
env['PYTHONPATH'] = f"{os.getcwd()}/backend/src:{os.getcwd()}/cli/src"

print("[INFO] Starting API with verbose logging...")
api = subprocess.Popen(
    [sys.executable, '-m', 'socrates_api'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,  # Combine stderr and stdout
    text=True,
    env=env
)

time.sleep(10)

try:
    print("\n[TEST] Making requests...")

    print("\nTesting /health...")
    r = requests.get('http://localhost:8000/health', timeout=2)
    print(f"  Status: {r.status_code}")

    print("\nTesting /auth/csrf-token...")
    r = requests.get('http://localhost:8000/auth/csrf-token', timeout=2)
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.text[:100]}")

    time.sleep(1)

finally:
    api.terminate()
    # Print last 50 lines of output
    print("\n[LOGS] API Output (last lines):")
    try:
        stdout, _ = api.communicate(timeout=2)
        lines = stdout.split('\n')
        for line in lines[-50:]:
            if line.strip():
                print(f"  {line}")
    except:
        pass
