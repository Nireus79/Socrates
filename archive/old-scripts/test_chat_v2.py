#!/usr/bin/env python
"""Test chat session endpoints"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_chat():
    print("Testing Chat Sessions Endpoints\n")

    # Register and login
    timestamp = str(int(time.time() * 1000))
    username = f"chattest_{timestamp}"
    email = f"chattest_{timestamp}@example.com"

    print("1. Registering user...")
    requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "email": email,
        "password": "Test@1234!"
    })

    print("2. Logging in...")
    login = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": "Test@1234!"
    })
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    print("3. Creating project...")
    proj = requests.post(f"{BASE_URL}/projects", json={
        "name": f"Chat Test {timestamp}",
        "description": "Test"
    }, headers=headers)
    project_id = proj.json().get("project_id")
    print(f"   Project ID: {project_id}\n")

    # Test chat session endpoints
    endpoints = [
        ("POST", f"/projects/{project_id}/chat/sessions", {"title": "Test Session"}),
        ("GET", f"/projects/{project_id}/chat/sessions", None),
    ]

    for method, path, body in endpoints:
        print(f"{method:4} {path}")
        if method == "POST":
            resp = requests.post(f"{BASE_URL}{path}", json=body, headers=headers)
        else:
            resp = requests.get(f"{BASE_URL}{path}", headers=headers)

        print(f"  Status: {resp.status_code}")
        if resp.status_code not in [200, 201]:
            print(f"  Error: {resp.text[:200]}")
        else:
            print(f"  ✓ Success")
        print()

if __name__ == "__main__":
    test_chat()
