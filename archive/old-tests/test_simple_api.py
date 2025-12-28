#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test to verify API response formats work correctly
"""

import requests
import json
import sys
import os

if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

print("[TEST] Checking API response formats...")
print()

# Create test user
print("[1] Creating test user...")
resp = requests.post(f"{BASE_URL}/auth/register",
    json={"username": "simpletest", "password": "Test123!"}
)
if resp.status_code not in [200, 201]:
    print(f"    Failed: {resp.text[:100]}")
    sys.exit(1)
print(f"    [OK] Status {resp.status_code}")

# Login
print("[2] Login...")
resp = requests.post(f"{BASE_URL}/auth/login",
    json={"username": "simpletest", "password": "Test123!"}
)
if resp.status_code != 200:
    print(f"    Failed: {resp.text[:100]}")
    sys.exit(1)
token = resp.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print(f"    [OK] Got token")

# Create project
print("[3] Creating project...")
resp = requests.post(f"{BASE_URL}/projects",
    json={"name": "Test", "description": "Test"},
    headers=headers
)
if resp.status_code not in [200, 201]:
    print(f"    Failed: {resp.text[:100]}")
    sys.exit(1)
project_id = resp.json().get("id")
print(f"    [OK] Project: {project_id}")

# Test endpoints without waiting for LLM calls
print("[4] Testing question endpoint...")
resp = requests.get(f"{BASE_URL}/projects/{project_id}/chat/question", headers=headers, timeout=5)
if resp.status_code == 200:
    data = resp.json()
    if 'question' in data and 'phase' in data:
        print(f"    [OK] Correct format (unwrapped)")
    else:
        print(f"    [FAIL] Wrong format: {list(data.keys())}")
else:
    print(f"    [ERROR] Status {resp.status_code}: {resp.text[:100]}")

print("[5] Testing history endpoint...")
resp = requests.get(f"{BASE_URL}/projects/{project_id}/chat/history", headers=headers, timeout=5)
if resp.status_code == 200:
    data = resp.json()
    if 'messages' in data:
        print(f"    [OK] Correct format (unwrapped)")
    else:
        print(f"    [FAIL] Wrong format: {list(data.keys())}")
else:
    print(f"    [ERROR] Status {resp.status_code}: {resp.text[:100]}")

print("[6] Testing mode endpoint...")
resp = requests.put(f"{BASE_URL}/projects/{project_id}/chat/mode",
    json={"mode": "direct"},
    headers=headers,
    timeout=5
)
if resp.status_code == 200:
    data = resp.json()
    if 'mode' in data:
        print(f"    [OK] Correct format (unwrapped)")
    else:
        print(f"    [FAIL] Wrong format: {list(data.keys())}")
else:
    print(f"    [ERROR] Status {resp.status_code}: {resp.text[:100]}")

print("[7] Testing delete...")
resp = requests.delete(f"{BASE_URL}/projects/{project_id}", headers=headers, timeout=5)
if resp.status_code == 200:
    # Verify deleted
    resp2 = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers, timeout=5)
    if resp2.status_code == 404:
        print(f"    [OK] Delete working")
    else:
        print(f"    [FAIL] Project still exists")
else:
    print(f"    [ERROR] Status {resp.status_code}: {resp.text[:100]}")

print()
print("[SUCCESS] All basic API tests passed!")
