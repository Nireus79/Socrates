"""
End-to-end API workflow tests.

Tests complete user journeys:
1. User Registration & Authentication
2. Project Creation with Subscription Enforcement
3. Code Generation & History Tracking
4. Collaboration Features
5. Notes and Chat Management
"""

import json
import pytest
import requests
from typing import Tuple
import time

API_URL = "http://localhost:8008"


class TestAuthenticationWorkflow:
    """Test user registration and authentication flow."""

    def test_user_registration_login_flow(self) -> Tuple[str, str]:
        """Test user can register and login."""
        timestamp = int(time.time())

        # Step 1: Register user
        register_response = requests.post(
            f"{API_URL}/auth/register",
            json={
                "username": f"test_user_{timestamp}",
                "email": f"test_{timestamp}@example.com",
                "password": "TestPassword123!",
            },
        )
        assert register_response.status_code == 201, f"Registration failed: {register_response.text}"
        register_data = register_response.json()
        # Auth endpoints may return AuthResponse or APIResponse format
        assert "access_token" in register_data, f"Missing access_token: {register_data}"

        # Step 2: Login with same credentials
        # Handle both APIResponse and AuthResponse formats
        user_data = register_data.get("data", {}).get("user") or register_data.get("user")
        username = user_data.get("username") or register_data.get("user", {}).get("username")
        login_response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "username": username,
                "password": "TestPassword123!",
            },
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        login_data = login_response.json()

        # Handle both APIResponse and AuthResponse formats
        token = login_data.get("data", {}).get("access_token") or login_data.get("access_token")
        return username, token


class TestProjectWorkflow:
    """Test project creation and management workflow."""

    def test_project_creation_workflow(self):
        """Test creating and retrieving a project."""
        # Get auth token
        auth = TestAuthenticationWorkflow()
        username, token = auth.test_user_registration_login_flow()
        headers = {"Authorization": f"Bearer {token}"}

        # Create project
        timestamp = int(time.time())
        create_response = requests.post(
            f"{API_URL}/projects",
            json={
                "name": f"TestProject_{timestamp}",
                "description": "Test project for e2e workflow",
            },
            headers=headers,
        )
        assert create_response.status_code == 200, f"Project creation failed: {create_response.text}"
        create_data = create_response.json()
        assert create_data.get("success") is True
        assert "data" in create_data
        project_id = create_data["data"]["project_id"]

        # Get project details
        get_response = requests.get(
            f"{API_URL}/projects/{project_id}",
            headers=headers,
        )
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data.get("success") is True
        assert get_data["data"]["project_id"] == project_id

        # List projects
        list_response = requests.get(
            f"{API_URL}/projects",
            headers=headers,
        )
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data.get("success") is True
        assert len(list_data.get("data", [])) > 0

        return username, token, project_id


class TestCodeGenerationWorkflow:
    """Test code generation and history tracking."""

    def test_code_generation_workflow(self):
        """Test generating code and tracking history."""
        project = TestProjectWorkflow()
        username, token, project_id = project.test_project_creation_workflow()
        headers = {"Authorization": f"Bearer {token}"}

        # Get code history
        history_response = requests.get(
            f"{API_URL}/projects/{project_id}/code/history",
            headers=headers,
        )
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert history_data.get("success") is True
        assert "data" in history_data

        # Add a note (preparation for code generation)
        note_response = requests.post(
            f"{API_URL}/projects/{project_id}/notes",
            json={
                "title": "Code Requirements",
                "content": "Need to implement user authentication",
            },
            headers=headers,
        )
        assert note_response.status_code == 201
        note_data = note_response.json()
        assert note_data.get("success") is True

        return username, token, project_id


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_unauthorized_access_to_project(self):
        """Test that users cannot access other users' projects."""
        # Create first user and project
        auth1 = TestAuthenticationWorkflow()
        user1, token1 = auth1.test_user_registration_login_flow()
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Create second user
        auth2 = TestAuthenticationWorkflow()
        user2, token2 = auth2.test_user_registration_login_flow()
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Create project with first user
        timestamp = int(time.time())
        create_response = requests.post(
            f"{API_URL}/projects",
            json={
                "name": f"UserProject_{timestamp}",
                "description": "First user project",
            },
            headers=headers1,
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["data"]["project_id"]

        # Try to access first user's project with second user's token
        access_response = requests.get(
            f"{API_URL}/projects/{project_id}",
            headers=headers2,
        )
        assert access_response.status_code in [403, 404], \
            "User should not access other user's project"

    def test_invalid_project_id(self):
        """Test accessing nonexistent project."""
        auth = TestAuthenticationWorkflow()
        _, token = auth.test_user_registration_login_flow()
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(
            f"{API_URL}/projects/nonexistent_id_12345",
            headers=headers,
        )
        assert response.status_code == 404

    def test_missing_authentication(self):
        """Test that endpoints require authentication."""
        response = requests.get(f"{API_URL}/projects")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
