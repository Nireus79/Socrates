#!/usr/bin/env python
"""
Test collaborator endpoint WITH username query parameter
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_with_param():
    print("Testing with username query parameter...")

    # Register and login
    timestamp = str(int(time.time() * 1000))
    username1 = f"test1_{timestamp}"
    email1 = f"test1_{timestamp}@example.com"

    requests.post(f"{BASE_URL}/auth/register", json={
        "username": username1,
        "email": email1,
        "password": "Test@1234!"
    })

    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username1,
        "password": "Test@1234!"
    })
    token = login_response.json().get("access_token")

    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    project_response = requests.post(f"{BASE_URL}/projects", json={
        "name": f"Test {timestamp}",
        "description": "Test"
    }, headers=headers)
    project_id = project_response.json().get("project_id")

    # Try with query parameter
    print(f"\n1. WITH username query parameter:")
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/collaborators?username=someuser",
        json={"email": f"test2_{timestamp}@example.com", "role": "editor"},
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")

    # Try without query parameter
    print(f"\n2. WITHOUT username query parameter:")
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/collaborators",
        json={"email": f"test2_{timestamp}@example.com", "role": "editor"},
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")

if __name__ == "__main__":
    test_with_param()
