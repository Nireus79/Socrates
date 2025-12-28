#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test if endpoint location in file matters for registration"""
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
print("TESTING IF ROUTE LOCATION IN FILE MATTERS")
print("=" * 80)

# Register and login
reg = requests.post(f"{BASE_URL}/auth/register", json={
    "username": username, "email": email, "password": "Test@1234!"
})
print(f"1. User registration: {reg.status_code}")

login = requests.post(f"{BASE_URL}/auth/login", json={
    "username": username, "password": "Test@1234!"
})
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print(f"2. User login: {login.status_code}")

# Create project
proj = requests.post(f"{BASE_URL}/projects", json={
    "name": f"Test {timestamp}", "description": "Test"
}, headers=headers)
project_id = proj.json().get("project_id")
print(f"3. Project creation: {proj.status_code}")

# Test the test-endpoint (at end of file)
print(f"\n" + "=" * 80)
print("TESTING ENDPOINT AT END OF FILE")
print("=" * 80)

print(f"\nGET /projects/{project_id}/chat/test-endpoint")
resp = requests.get(
    f"{BASE_URL}/projects/{project_id}/chat/test-endpoint",
    headers=headers,
    timeout=5
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"[OK] Test endpoint at END of file works!")
    print(f"Response: {resp.json()}")
else:
    print(f"[FAIL] Test endpoint returns {resp.status_code}")
    print(f"Response: {resp.text[:200]}")

# Test a Phase 2 endpoint that's at the beginning of the file
print(f"\n" + "=" * 80)
print("TESTING PHASE 2 ENDPOINTS AT BEGINNING OF FILE")
print("=" * 80)

print(f"\nPOST /projects/{project_id}/chat/sessions")
resp = requests.post(
    f"{BASE_URL}/projects/{project_id}/chat/sessions",
    json={"title": "Test"},
    headers=headers,
    timeout=5
)
print(f"Status: {resp.status_code}")
if resp.status_code in [200, 201]:
    print(f"[OK] Phase 2 endpoint at BEGINNING works!")
else:
    print(f"[FAIL] Phase 2 endpoint returns {resp.status_code}")

# Check OpenAPI
print(f"\n" + "=" * 80)
print("OPENAPI SCHEMA CHECK")
print("=" * 80)

openapi = requests.get(f"{BASE_URL}/openapi.json")
schema = openapi.json()
paths = schema.get("paths", {})

test_found = any("test-endpoint" in p for p in paths.keys())
sessions_found = any("chat/sessions" in p for p in paths.keys())

print(f"\nTest endpoint in OpenAPI: {'YES' if test_found else 'NO'}")
print(f"Chat sessions in OpenAPI: {'YES' if sessions_found else 'NO'}")

if test_found and not sessions_found:
    print("\n[EVIDENCE] Routes at end of file ARE registered, but routes at beginning are NOT!")
    print("CONCLUSION: Routes need to be at the END of the file to be registered")
