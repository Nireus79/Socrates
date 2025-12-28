#!/usr/bin/env python
"""
Simple test for chat sessions endpoint
"""
import requests
import json
import time
import sys
import os

# Add project to path
sys.path.insert(0, "socrates-api/src")
sys.path.insert(0, ".")

BASE_URL = "http://localhost:8000"

def test_chat_sessions():
    print("=" * 70)
    print("CHAT SESSIONS ENDPOINT TEST")
    print("=" * 70)

    # Step 1: Register user
    print("\n1. Registering user...")
    timestamp = str(int(time.time() * 1000))
    username = f"chattest_{timestamp}"
    email = f"chattest_{timestamp}@example.com"

    reg_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "Test@1234!"
        }
    )
    print(f"   Status: {reg_response.status_code}")

    # Step 2: Login
    print("\n2. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": username,
            "password": "Test@1234!"
        }
    )
    print(f"   Status: {login_response.status_code}")
    if login_response.status_code != 200:
        print(f"   Error: {login_response.text}")
        return False

    token = login_response.json().get("access_token")
    print(f"   Token: {token[:20]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: Create project
    print("\n3. Creating project...")
    project_response = requests.post(
        f"{BASE_URL}/projects",
        json={
            "name": f"Chat Test Project {timestamp}",
            "description": "Testing chat sessions"
        },
        headers=headers
    )
    print(f"   Status: {project_response.status_code}")
    if project_response.status_code not in [200, 201]:
        print(f"   Error: {project_response.text}")
        return False

    project_data = project_response.json()
    project_id = project_data.get("project_id") or project_data.get("id")
    print(f"   Project ID: {project_id}")

    if not project_id:
        print("   ERROR: No project ID returned")
        print(f"   Response keys: {list(project_data.keys())}")
        return False

    # Step 4: Create chat session
    print("\n4. Creating chat session...")
    session_response = requests.post(
        f"{BASE_URL}/projects/{project_id}/chat/sessions",
        json={"title": "Test Chat Session"},
        headers=headers
    )
    print(f"   Status: {session_response.status_code}")
    print(f"   Response: {session_response.text[:200]}")

    if session_response.status_code == 201:
        session_data = session_response.json()
        session_id = session_data.get("session_id")
        print(f"   SUCCESS! Session ID: {session_id}")

        # Step 5: Send message
        print("\n5. Sending message...")
        message_response = requests.post(
            f"{BASE_URL}/projects/{project_id}/chat/{session_id}/message",
            json={"message": "Hello, assistant!"},
            headers=headers
        )
        print(f"   Status: {message_response.status_code}")
        print(f"   Response: {message_response.text[:200]}")

        if message_response.status_code == 201:
            print("   SUCCESS!")
            return True
    else:
        print(f"   FAILED")
        return False

if __name__ == "__main__":
    os.chdir("C:\\Users\\themi\\PycharmProjects\\Socrates")
    success = test_chat_sessions()
    sys.exit(0 if success else 1)
