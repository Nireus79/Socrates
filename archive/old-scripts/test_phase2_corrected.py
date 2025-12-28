#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test Phase 2 routes with corrected URL patterns"""
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
print("PHASE 2 CORRECTED URL PATTERNS TEST")
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

# Test endpoints with CORRECTED URLs
print("\n" + "=" * 80)
print("TESTING PHASE 2 ENDPOINTS (CORRECTED URLs)")
print("=" * 80)

endpoints = [
    ("POST", f"/projects/{project_id}/chat/sessions", {"title": "Test Session"}, "Create session"),
    ("GET", f"/projects/{project_id}/chat/sessions", None, "List sessions"),
]

session_id = None
for method, path, body, desc in endpoints:
    url = f"{BASE_URL}{path}"
    print(f"\n{method} {path}")
    print(f"  ({desc})")

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
                    if 'session_id' in data:
                        session_id = data.get('session_id')
                        print(f"  Session ID: {session_id}")
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

# Test message endpoints if we have a session
if session_id:
    print(f"\n" + "=" * 80)
    print("TESTING MESSAGE ENDPOINTS")
    print("=" * 80)

    message_endpoints = [
        ("POST", f"/projects/{project_id}/chat/sessions/{session_id}/message",
         {"message": "Hello", "role": "user"}, "Send message"),
        ("GET", f"/projects/{project_id}/chat/sessions/{session_id}/messages",
         None, "Get messages"),
    ]

    for method, path, body, desc in message_endpoints:
        url = f"{BASE_URL}{path}"
        print(f"\n{method} {path}")
        print(f"  ({desc})")

        try:
            if method == "POST":
                resp = requests.post(url, json=body, headers=headers, timeout=5)
            else:
                resp = requests.get(url, headers=headers, timeout=5)

            print(f"  Status: {resp.status_code}")

            if resp.status_code in [200, 201]:
                print(f"  [OK] SUCCESS")
            else:
                print(f"  [FAIL] Status {resp.status_code}")
                print(f"  Response: {resp.text[:200]}")
        except Exception as e:
            print(f"  [ERROR] {str(e)}")

# Check OpenAPI
print("\n" + "=" * 80)
print("CHECKING OPENAPI SCHEMA")
print("=" * 80)

openapi = requests.get(f"{BASE_URL}/openapi.json")
if openapi.status_code == 200:
    schema = openapi.json()
    paths = schema.get("paths", {})

    chat_sessions_paths = [p for p in paths.keys() if "chat/sessions" in p]
    print(f"\nChat/sessions paths in OpenAPI schema: {len(chat_sessions_paths)}")
    for path in sorted(chat_sessions_paths):
        methods = list(paths[path].keys())
        print(f"  {path}: {methods}")

    if chat_sessions_paths:
        print("\n[OK] Chat sessions routes are NOW REGISTERED!")
    else:
        print("\n[FAIL] Chat sessions routes still NOT in schema")
