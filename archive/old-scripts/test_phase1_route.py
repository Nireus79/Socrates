#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test a Phase 1 route to see if it works"""
import requests
import time
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

# Generate unique user
timestamp = str(int(time.time() * 1000))
username = f"test_{timestamp}"
email = f"test_{timestamp}@example.com"

print("=" * 80)
print("TESTING PHASE 1 ROUTE")
print("=" * 80)

# Register
print("\n1. Registering user...")
reg = requests.post(f"{BASE_URL}/auth/register", json={
    "username": username, "email": email, "password": "Test@1234!"
})
print(f"   Status: {reg.status_code}")

# Login
print("\n2. Logging in...")
login = requests.post(f"{BASE_URL}/auth/login", json={
    "username": username, "password": "Test@1234!"
})
print(f"   Status: {login.status_code}")
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Create project
print("\n3. Creating project...")
proj = requests.post(f"{BASE_URL}/projects", json={
    "name": f"Test {timestamp}", "description": "Test"
}, headers=headers)
print(f"   Status: {proj.status_code}")
project_id = proj.json().get("project_id")
print(f"   Project ID: {project_id}")

# Test Phase 1 routes
print("\n" + "=" * 80)
print("TESTING PHASE 1 ENDPOINTS (THESE SHOULD WORK)")
print("=" * 80)

# Test chat/question (Phase 1, should work)
print(f"\nGET /projects/{project_id}/chat/question")
resp = requests.get(f"{BASE_URL}/projects/{project_id}/chat/question", headers=headers, timeout=5)
print(f"  Status: {resp.status_code}")
if resp.status_code in [200, 201]:
    print(f"  [OK] Route is working!")
else:
    print(f"  [FAIL] Route not working: {resp.text[:100]}")

# Test chat/message (Phase 1, should work)
print(f"\nPOST /projects/{project_id}/chat/message")
resp = requests.post(
    f"{BASE_URL}/projects/{project_id}/chat/message",
    json={"message": "Hello", "mode": "socratic"},
    headers=headers,
    timeout=5
)
print(f"  Status: {resp.status_code}")
if resp.status_code in [200, 201]:
    print(f"  [OK] Route is working!")
else:
    print(f"  [FAIL] Route not working: {resp.text[:100]}")

# Check what's in OpenAPI
print("\n" + "=" * 80)
print("CHECKING OPENAPI SCHEMA FOR PHASE 1 ROUTES")
print("=" * 80)

openapi = requests.get(f"{BASE_URL}/openapi.json")
if openapi.status_code == 200:
    schema = openapi.json()
    paths = schema.get("paths", {})

    # Check for phase 1 routes
    phase1_routes = [p for p in paths.keys() if "chat" in p and "sessions" not in p]
    print(f"\nChat routes in OpenAPI (excluding sessions): {len(phase1_routes)}")
    for path in sorted(phase1_routes)[:10]:
        methods = list(paths[path].keys())
        print(f"  {path}: {methods}")
