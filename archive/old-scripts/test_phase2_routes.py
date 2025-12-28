#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test Phase 2 routes to verify they're registered"""
import requests
import time
import json
import sys

# Fix encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

# Generate unique user
timestamp = str(int(time.time() * 1000))
username = f"test_{timestamp}"
email = f"test_{timestamp}@example.com"

print("=" * 80)
print("PHASE 2 ROUTE REGISTRATION TEST")
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

# Test endpoints
print("\n" + "=" * 80)
print("TESTING PHASE 2 ENDPOINTS")
print("=" * 80)

endpoints = [
    ("POST", f"/chat/sessions/projects/{project_id}/sessions", {"title": "Test Session"}),
    ("GET", f"/chat/sessions/projects/{project_id}/sessions", None),
]

for method, path, body in endpoints:
    url = f"{BASE_URL}{path}"
    print(f"\n{method} {path}")

    try:
        if method == "POST":
            resp = requests.post(url, json=body, headers=headers, timeout=5)
        else:
            resp = requests.get(url, headers=headers, timeout=5)

        print(f"  Status: {resp.status_code}")

        if resp.status_code in [200, 201]:
            print(f"  [OK] SUCCESS")
            try:
                data = resp.json()
                if isinstance(data, dict):
                    print(f"  Response keys: {list(data.keys())[:5]}")
                elif isinstance(data, list):
                    print(f"  Response: List of {len(data)} items")
            except:
                print(f"  Response: {resp.text[:100]}")
        else:
            print(f"  [FAIL] Status {resp.status_code}")
            print(f"  Response: {resp.text[:200]}")
    except Exception as e:
        print(f"  [ERROR] {str(e)}")

print("\n" + "=" * 80)
print("CHECKING OPENAPI SCHEMA")
print("=" * 80)

openapi = requests.get(f"{BASE_URL}/openapi.json")
if openapi.status_code == 200:
    schema = openapi.json()
    paths = schema.get("paths", {})

    chat_sessions_paths = [p for p in paths.keys() if "chat/sessions" in p]
    print(f"\nChat/sessions paths in OpenAPI schema: {len(chat_sessions_paths)}")
    for path in chat_sessions_paths:
        methods = list(paths[path].keys())
        print(f"  {path}: {methods}")

    if not chat_sessions_paths:
        print("  [FAIL] NO CHAT/SESSIONS PATHS FOUND IN SCHEMA")

        # Show some sample paths for comparison
        print("\n  Existing project/chat paths in schema:")
        proj_chat_paths = [p for p in paths.keys() if "projects" in p and "chat" in p]
        for path in sorted(proj_chat_paths)[:10]:
            print(f"    {path}")

print("\n" + "=" * 80)
print("CHECKING ROUTER DEFINITIONS")
print("=" * 80)

try:
    from socrates_api.routers.chat_sessions import router as chat_sessions_router
    print(f"\nChat sessions router imported successfully")
    print(f"  Prefix: {chat_sessions_router.prefix}")
    print(f"  Routes defined in router: {len(chat_sessions_router.routes)}")
    for route in chat_sessions_router.routes[:5]:
        if hasattr(route, 'path'):
            print(f"    {str(route.methods or []).ljust(15)} {route.path}")
except Exception as e:
    print(f"[ERROR] Failed to import chat_sessions router: {e}")
