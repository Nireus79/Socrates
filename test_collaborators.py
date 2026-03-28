#!/usr/bin/env python
"""Test collaborators endpoint after fix."""

import requests
import json

API_BASE = "http://127.0.0.1:8000"

# Get all projects first to find a valid project
print("Getting projects list...")
response = requests.get(
    f"{API_BASE}/projects",
    headers={"Authorization": "Bearer test_token"},
    timeout=5
)

if response.status_code == 401:
    print("Need valid token. Login first.")
    # Try a simple login test
    login_response = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": "Themis", "password": "password"},
        timeout=5
    )
    print(f"Login response: {login_response.status_code}")
    if login_response.status_code == 200:
        data = login_response.json()
        token = data.get("data", {}).get("access_token")
        print(f"Got token: {token[:20]}..." if token else "No token")

        # Try getting projects with real token
        projects_response = requests.get(
            f"{API_BASE}/projects",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        print(f"\nProjects list: {projects_response.status_code}")
        if projects_response.status_code == 200:
            projects_data = projects_response.json()
            projects = projects_data.get("data", {}).get("projects", [])
            if projects:
                project_id = projects[0]["project_id"]
                print(f"Found project: {project_id}")

                # Test collaborators endpoint
                collab_response = requests.get(
                    f"{API_BASE}/projects/{project_id}/collaborators",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                print(f"\nCollaborators endpoint: {collab_response.status_code}")
                print(json.dumps(collab_response.json(), indent=2))
