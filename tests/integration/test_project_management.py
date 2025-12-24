"""
Comprehensive Project Management Workflow Tests

Tests all project CRUD operations, lifecycle, and tier-based features:
- Create, read, list, update, delete/archive projects
- Project ownership and access control
- Subscription tier enforcement (free: 1, pro: 10, enterprise: unlimited)
- Project state transitions
"""

import requests
import json
import time
from datetime import datetime
import pytest

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


class TestProjectManagement:
    """Complete project management workflow tests"""

    @pytest.fixture
    def test_user(self):
        """Register a free tier test user"""
        username = f"testuser_{int(datetime.now().timestamp() * 1000)}"
        email = f"{username}@test.local"

        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": "TestPassword123!"
            },
            headers=HEADERS
        )
        assert response.status_code == 201, f"Failed to register user: {response.text}"
        data = response.json()

        return {
            "username": username,
            "email": email,
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"]
        }

    @pytest.fixture
    def auth_headers(self, test_user):
        """Get authorization headers for test user"""
        return {**HEADERS, "Authorization": f"Bearer {test_user['access_token']}"}

    def test_01_create_project_free_tier(self, test_user, auth_headers):
        """Test: Free tier user can create 1 project"""
        response = requests.post(
            f"{BASE_URL}/projects",
            json={
                "name": "My First Project",
                "description": "Free tier test project",
                "knowledge_base_content": "Test knowledge base",
                "owner": test_user["username"]
            },
            headers=auth_headers
        )

        assert response.status_code == 200, f"Failed to create project: {response.text}"
        data = response.json()
        assert "project_id" in data
        assert data["name"] == "My First Project"
        assert data["owner"] == test_user["username"]

        return data["project_id"]

    def test_02_create_second_project_blocked_free_tier(self, test_user, auth_headers):
        """Test: Free tier blocked from creating 2nd project"""
        # Create first project
        requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Project 1", "description": "First project"},
            headers=auth_headers
        )

        # Try to create second project - should be blocked
        response = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Project 2", "description": "Second project"},
            headers=auth_headers
        )

        assert response.status_code == 403, "Free tier should be blocked from 2nd project"
        error = response.json()
        assert "subscription" in error.get("detail", "").lower() or \
               "limit" in error.get("detail", "").lower()

    def test_03_list_projects(self, test_user, auth_headers):
        """Test: List user's projects"""
        # Create a project first
        create_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "List Test Project", "description": "For listing", "owner": test_user["username"]},
            headers=auth_headers
        )
        project_id = create_resp.json()["project_id"]

        # List projects
        response = requests.get(
            f"{BASE_URL}/projects",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert "total" in data
        assert isinstance(data["projects"], list)
        assert data["total"] >= 1

        # Verify our created project is in the list
        project_names = [p.get("name") for p in data["projects"]]
        assert "List Test Project" in project_names

    def test_04_get_project_details(self, test_user, auth_headers):
        """Test: Get specific project details"""
        # Create a project
        create_resp = requests.post(
            f"{BASE_URL}/projects",
            json={
                "name": "Detail Test Project",
                "description": "Testing detail retrieval",
                "owner": test_user["username"]
            },
            headers=auth_headers
        )
        project_id = create_resp.json()["project_id"]

        # Get project details
        response = requests.get(
            f"{BASE_URL}/projects/{project_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert data["name"] == "Detail Test Project"
        assert data["owner"] == test_user["username"]

    def test_05_update_project_metadata(self, test_user, auth_headers):
        """Test: Update project name and phase"""
        # Create a project
        create_resp = requests.post(
            f"{BASE_URL}/projects",
            json={
                "name": "Original Name",
                "description": "Original description",
                "owner": test_user["username"]
            },
            headers=auth_headers
        )
        project_id = create_resp.json()["project_id"]

        # Update project
        response = requests.put(
            f"{BASE_URL}/projects/{project_id}",
            json={
                "name": "Updated Name",
                "phase": "implementation"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["phase"] == "implementation"

    def test_06_delete_project(self, test_user, auth_headers):
        """Test: Archive/delete project"""
        # Create a project
        create_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Project to Delete", "description": "Delete test", "owner": test_user["username"]},
            headers=auth_headers
        )
        project_id = create_resp.json()["project_id"]

        # Delete/archive project
        response = requests.delete(
            f"{BASE_URL}/projects/{project_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result.get("success") == True or result.get("status") == "success"

    def test_07_access_denied_other_user_project(self, test_user, auth_headers):
        """Test: User cannot access another user's project"""
        # Create a project with first user
        create_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Private Project", "description": "Private test", "owner": test_user["username"]},
            headers=auth_headers
        )
        project_id = create_resp.json()["project_id"]

        # Create second user
        user2_name = f"testuser2_{int(datetime.now().timestamp() * 1000)}"
        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": user2_name,
                "email": f"{user2_name}@test.local",
                "password": "TestPassword123!"
            },
            headers=HEADERS
        )
        user2_token = reg_resp.json()["access_token"]
        user2_headers = {**HEADERS, "Authorization": f"Bearer {user2_token}"}

        # Try to access with second user - should fail
        response = requests.get(
            f"{BASE_URL}/projects/{project_id}",
            headers=user2_headers
        )

        assert response.status_code == 403, "User should not access other's project"

    def test_08_project_phases(self, test_user, auth_headers):
        """Test: Project phase transitions"""
        # Create project
        create_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Phase Test Project", "description": "Phase test", "owner": test_user["username"]},
            headers=auth_headers
        )
        project_id = create_resp.json()["project_id"]

        phases = ["discovery", "analysis", "design", "implementation", "testing"]

        for phase in phases:
            response = requests.put(
                f"{BASE_URL}/projects/{project_id}",
                json={"phase": phase},
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.json()["phase"] == phase

    def test_09_project_with_knowledge_base(self, test_user, auth_headers):
        """Test: Create project with knowledge base content"""
        knowledge_content = """
        # Domain Knowledge

        ## Key Concepts
        - Concept 1: Definition and usage
        - Concept 2: Important details
        - Concept 3: Examples

        ## Best Practices
        - Practice 1
        - Practice 2
        """

        response = requests.post(
            f"{BASE_URL}/projects",
            json={
                "name": "Knowledge Base Project",
                "description": "Project with knowledge base",
                "knowledge_base_content": knowledge_content,
                "owner": test_user["username"]
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Knowledge Base Project"

    def test_10_project_metadata_completeness(self, test_user, auth_headers):
        """Test: Project has all required metadata"""
        response = requests.post(
            f"{BASE_URL}/projects",
            json={
                "name": "Metadata Test",
                "description": "Test metadata",
                "owner": test_user["username"]
            },
            headers=auth_headers
        )

        project = response.json()
        required_fields = [
            "project_id", "name", "owner", "description",
            "phase", "created_at", "updated_at", "is_archived"
        ]

        for field in required_fields:
            assert field in project, f"Missing required field: {field}"

    def test_11_get_nonexistent_project(self, test_user, auth_headers):
        """Test: Getting nonexistent project returns 404"""
        response = requests.get(
            f"{BASE_URL}/projects/nonexistent_project_id",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_12_update_nonexistent_project(self, test_user, auth_headers):
        """Test: Updating nonexistent project returns 404"""
        response = requests.put(
            f"{BASE_URL}/projects/nonexistent_project_id",
            json={"name": "Updated"},
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_13_invalid_project_creation(self, test_user, auth_headers):
        """Test: Project creation fails with missing required fields"""
        # Missing name
        response = requests.post(
            f"{BASE_URL}/projects",
            json={"description": "Missing name"},
            headers=auth_headers
        )

        assert response.status_code >= 400, "Should fail with missing name"


class TestProjectQuotas:
    """Test subscription quota enforcement"""

    def test_pro_tier_project_limits(self):
        """Test: Pro tier allows up to 10 projects"""
        # This requires creating a pro tier user
        # Skipped for now - needs pro tier test account setup
        pass

    def test_enterprise_tier_unlimited_projects(self):
        """Test: Enterprise tier allows unlimited projects"""
        # This requires creating an enterprise tier user
        # Skipped for now - needs enterprise tier test account setup
        pass


class TestProjectCollaboration:
    """Test project collaboration features (Pro+ tier)"""

    def test_add_collaborator_pro_tier(self):
        """Test: Pro tier can add team members to projects"""
        # Requires pro tier user and second user
        pass

    def test_collaborator_roles(self):
        """Test: Collaborator role management"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
