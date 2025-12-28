#!/usr/bin/env python
"""Test chat sessions with dedicated router"""
import requests
import time

BASE_URL = "http://localhost:8000"

# Register
timestamp = str(int(time.time() * 1000))
username = f"test_{timestamp}"
email = f"test_{timestamp}@example.com"

requests.post(f"{BASE_URL}/auth/register", json={
    "username": username, "email": email, "password": "Test@1234!"
})

# Login
login = requests.post(f"{BASE_URL}/auth/login", json={
    "username": username, "password": "Test@1234!"
})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Create project
proj = requests.post(f"{BASE_URL}/projects", json={
    "name": f"Test {timestamp}", "description": "Test"
}, headers=headers)
project_id = proj.json().get("project_id")

print(f"Project: {project_id}\n")

# Test NEW dedicated router endpoints
print("Testing Dedicated Router Endpoints:")
print("=" * 60)

endpoints = [
    ("POST", f"/chat/sessions/projects/{project_id}/sessions", {"title": "Test"}),
    ("GET", f"/chat/sessions/projects/{project_id}/sessions", None),
]

for method, path, body in endpoints:
    print(f"\n{method} {path}")
    if method == "POST":
        resp = requests.post(f"{BASE_URL}{path}", json=body, headers=headers)
    else:
        resp = requests.get(f"{BASE_URL}{path}", headers=headers)

    print(f"  Status: {resp.status_code}")
    if resp.status_code in [200, 201]:
        print(f"  ✅ SUCCESS")
        data = resp.json()
        if isinstance(data, dict):
            print(f"  Keys: {list(data.keys())[:5]}")
    else:
        print(f"  ❌ FAILED: {resp.text[:100]}")
