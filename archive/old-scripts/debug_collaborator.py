#!/usr/bin/env python
"""
Debug script for collaborator endpoint - shows exact error
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_collaborator_debug():
    print("=" * 70)
    print("COLLABORATOR ENDPOINT DEBUG")
    print("=" * 70)

    # Step 1: Register first user
    print("\n1. Registering first user...")
    timestamp = str(int(time.time() * 1000))
    username1 = f"collab_test1_{timestamp}"
    email1 = f"collab_test1_{timestamp}@example.com"

    reg_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": username1,
            "email": email1,
            "password": "Test@1234!"
        }
    )
    print(f"   Status: {reg_response.status_code}")
    if reg_response.status_code not in [200, 201]:
        print(f"   Error: {reg_response.text}")
        return False

    # Step 2: Register second user
    print("\n2. Registering second user...")
    username2 = f"collab_test2_{timestamp}"
    email2 = f"collab_test2_{timestamp}@example.com"

    reg_response2 = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": username2,
            "email": email2,
            "password": "Test@1234!"
        }
    )
    print(f"   Status: {reg_response2.status_code}")

    # Step 3: Login as first user
    print("\n3. Logging in as first user...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": username1,
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

    # Step 4: Create project
    print("\n4. Creating project...")
    project_response = requests.post(
        f"{BASE_URL}/projects",
        json={
            "name": f"Collaborator Test {timestamp}",
            "description": "Testing collaborator endpoint"
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
        return False

    # Step 5: Try to add collaborator
    print("\n5. Adding collaborator...")
    print(f"   Endpoint: POST /projects/{project_id}/collaborators")

    request_body = {
        "email": email2,
        "role": "editor"
    }
    print(f"   Request body: {json.dumps(request_body, indent=2)}")
    print(f"   Headers: {headers}")

    collab_response = requests.post(
        f"{BASE_URL}/projects/{project_id}/collaborators",
        json=request_body,
        headers=headers
    )

    print(f"   Status: {collab_response.status_code}")
    print(f"   Response: {collab_response.text}")

    if collab_response.status_code in [200, 201]:
        print("   SUCCESS!")
        return True
    else:
        print("   FAILED")

        # Try to parse JSON response for detailed error
        try:
            error_json = collab_response.json()
            print(f"\n   Detailed error response:")
            print(f"   {json.dumps(error_json, indent=2)}")
        except:
            pass

        return False

if __name__ == "__main__":
    import os
    os.chdir("C:\\Users\\themi\\PycharmProjects\\Socrates")
    success = test_collaborator_debug()
    sys.exit(0 if success else 1)
