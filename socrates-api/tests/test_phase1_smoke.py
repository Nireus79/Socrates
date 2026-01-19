"""
Phase 1 Smoke Tests - Quick validation of critical endpoints.

Tests core functionality of:
- Authentication (register, login, refresh, logout, me)
- Project management (CRUD operations)
- Access control (authorization, forbidden, not found)
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add the source directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from socrates_api.main import app

# Test client
client = TestClient(app)

# Generate unique test usernames to avoid database pollution
_test_timestamp = int(datetime.now().timestamp() * 1000)

# Test data
TEST_USER = {
    "username": f"testuser_smoke_{_test_timestamp}",
    "password": "TestPassword123!",
}

TEST_USER_2 = {
    "username": f"testuser_other_{_test_timestamp}",
    "password": "OtherPassword123!",
}


@pytest.mark.integration
class TestAuthenticationEndpoints:
    """Test authentication endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user for auth tests."""
        # Create a unique user for this test instance
        self.test_user = {
            "username": f"authtest_{id(self)}",
            "password": "TestPassword123!",
        }
        # Register the user
        response = client.post("/auth/register", json=self.test_user)
        if response.status_code in [200, 201]:
            self.access_token = response.json().get("access_token")
        else:
            # User might already exist, try to login
            login_response = client.post("/auth/login", json=self.test_user)
            if login_response.status_code == 200:
                self.access_token = login_response.json().get("access_token")

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_register_new_user(self):
        """Test user registration."""
        new_user = {
            "username": f"newreg_{id(self)}",
            "password": "TestPassword123!",
        }
        response = client.post("/auth/register", json=new_user)
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["username"] == new_user["username"]
        assert data["user"]["subscription_tier"] == "free"
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_user(self):
        """Test registering duplicate username fails."""
        # First registration
        client.post("/auth/register", json=TEST_USER)

        # Second registration with same username
        response = client.post("/auth/register", json=TEST_USER)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_register_invalid_password(self):
        """Test registration with short password fails."""
        response = client.post(
            "/auth/register",
            json={"username": "newuser", "password": "short"},
        )
        assert response.status_code == 422  # Validation error

    def test_login_success(self):
        """Test successful login."""
        # Register first
        client.post("/auth/register", json=TEST_USER_2)

        # Login
        response = client.post("/auth/login", json=TEST_USER_2)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == TEST_USER_2["username"]
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_credentials(self):
        """Test login with wrong password."""
        # Register
        client.post("/auth/register", json=TEST_USER_2)

        # Login with wrong password
        response = client.post(
            "/auth/login",
            json={"username": TEST_USER_2["username"], "password": "WrongPassword123!"},
        )
        assert response.status_code == 401
        assert "Invalid username or access code" in response.json()["detail"]

    def test_login_nonexistent_user(self):
        """Test login for non-existent user."""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent_user", "password": "anypassword"},
        )
        assert response.status_code == 401

    def test_get_current_user(self):
        """Test getting current user profile."""
        # Use the access token from setup fixture
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == self.test_user["username"]
        assert data["subscription_tier"] == "free"

    def test_get_current_user_unauthorized(self):
        """Test getting current user without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401  # No credentials

    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    def test_logout_success(self):
        """Test successful logout."""
        # Use the access token from setup fixture
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_logout_unauthorized(self):
        """Test logout without token."""
        response = client.post("/auth/logout")
        assert response.status_code == 401


@pytest.mark.integration
class TestProjectEndpoints:
    """Test project management endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user and get token."""
        user_data = {
            "username": f"testproj_user_{id(self)}",
            "password": "TestPassword123!",
        }
        response = client.post("/auth/register", json=user_data)
        self.access_token = response.json()["access_token"]
        self.username = user_data["username"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

    def _create_project(self, name="Test Project"):
        """Helper to create a project."""
        response = client.post(
            "/projects",
            json={
                "name": name,
                "owner": self.username,
                "description": "Test description",
            },
            headers=self.headers,
        )
        return response

    def test_list_projects_empty(self):
        """Test listing projects when none exist."""
        response = client.get(
            "/projects",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["projects"] == []

    def test_list_projects_unauthorized(self):
        """Test listing projects without authentication."""
        response = client.get("/projects")
        assert response.status_code == 401

    def test_create_project(self):
        """Test creating a project."""
        response = self._create_project()
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["owner"] == self.username
        assert data["phase"] == "discovery"
        self.project_id = data["project_id"]

    def test_list_projects_with_projects(self):
        """Test listing projects when projects exist."""
        # Create a project
        create_response = self._create_project("Project 1")
        assert create_response.status_code == 200

        # List projects
        response = client.get(
            "/projects",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_get_project_details(self):
        """Test getting project details."""
        # Create project
        create_response = self._create_project()
        project_id = create_response.json()["project_id"]

        # Get project
        response = client.get(
            f"/projects/{project_id}",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert data["owner"] == self.username

    def test_get_project_not_found(self):
        """Test getting non-existent project."""
        response = client.get(
            "/projects/nonexistent_id",
            headers=self.headers,
        )
        assert response.status_code == 404

    def test_get_project_unauthorized(self):
        """Test getting project without authentication."""
        response = client.get("/projects/some_id")
        assert response.status_code == 401

    def test_update_project(self):
        """Test updating project."""
        # Create project
        create_response = self._create_project()
        project_id = create_response.json()["project_id"]

        # Update project - send as JSON body, not query params
        response = client.put(
            f"/projects/{project_id}",
            json={"name": "Updated Name", "phase": "analysis"},
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["phase"] == "analysis"

    def test_delete_project(self):
        """Test deleting (archiving) project."""
        # Create project
        create_response = self._create_project()
        project_id = create_response.json()["project_id"]

        # Delete project
        response = client.delete(
            f"/projects/{project_id}",
            headers=self.headers,
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_restore_project(self):
        """Test restoring archived project."""
        # Create project
        create_response = self._create_project()
        project_id = create_response.json()["project_id"]

        # Archive project
        client.delete(f"/projects/{project_id}", headers=self.headers)

        # Restore project
        response = client.post(
            f"/projects/{project_id}/restore",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] is False

    def test_get_project_stats(self):
        """Test getting project statistics."""
        # Create project
        create_response = self._create_project()
        project_id = create_response.json()["project_id"]

        # Get stats
        response = client.get(
            f"/projects/{project_id}/stats",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert "phase" in data
        assert "progress" in data

    def test_get_project_maturity(self):
        """Test getting project maturity."""
        # Create project
        create_response = self._create_project()
        project_id = create_response.json()["project_id"]

        # Get maturity
        response = client.get(
            f"/projects/{project_id}/maturity",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data

    def test_advance_project_phase(self):
        """Test advancing project phase."""
        # Create project
        create_response = self._create_project()
        project_id = create_response.json()["project_id"]

        # Advance phase
        response = client.put(
            f"/projects/{project_id}/phase",
            params={"new_phase": "analysis"},
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phase"] == "analysis"

    def test_advance_project_invalid_phase(self):
        """Test advancing to invalid phase."""
        # Create project
        create_response = self._create_project()
        project_id = create_response.json()["project_id"]

        # Try invalid phase
        response = client.put(
            f"/projects/{project_id}/phase",
            params={"new_phase": "invalid_phase"},
            headers=self.headers,
        )
        assert response.status_code == 400


@pytest.mark.integration
class TestAccessControl:
    """Test access control and authorization."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup two users."""
        # User 1
        user1_data = {
            "username": f"user1_{id(self)}",
            "password": "Password123!",
        }
        response1 = client.post("/auth/register", json=user1_data)
        self.user1_token = response1.json()["access_token"]
        self.user1_headers = {"Authorization": f"Bearer {self.user1_token}"}
        self.user1_name = user1_data["username"]

        # User 2
        user2_data = {
            "username": f"user2_{id(self)}",
            "password": "Password123!",
        }
        response2 = client.post("/auth/register", json=user2_data)
        self.user2_token = response2.json()["access_token"]
        self.user2_headers = {"Authorization": f"Bearer {self.user2_token}"}

    def test_user_cannot_access_other_users_project(self):
        """Test that user cannot access another user's project."""
        # User 1 creates project
        create_response = client.post(
            "/projects",
            json={
                "name": "User 1 Project",
                "owner": self.user1_name,
                "description": "Private project",
            },
            headers=self.user1_headers,
        )
        project_id = create_response.json()["project_id"]

        # User 2 tries to access User 1's project
        response = client.get(
            f"/projects/{project_id}",
            headers=self.user2_headers,
        )
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    def test_user_cannot_update_other_users_project(self):
        """Test that user cannot update another user's project."""
        # User 1 creates project
        create_response = client.post(
            "/projects",
            json={
                "name": "User 1 Project",
                "owner": self.user1_name,
                "description": "Private project",
            },
            headers=self.user1_headers,
        )
        project_id = create_response.json()["project_id"]

        # User 2 tries to update User 1's project
        response = client.put(
            f"/projects/{project_id}",
            json={"name": "Hacked Name"},
            headers=self.user2_headers,
        )
        assert response.status_code == 403

    def test_user_cannot_delete_other_users_project(self):
        """Test that user cannot delete another user's project."""
        # User 1 creates project
        create_response = client.post(
            "/projects",
            json={
                "name": "User 1 Project",
                "owner": self.user1_name,
                "description": "Private project",
            },
            headers=self.user1_headers,
        )
        project_id = create_response.json()["project_id"]

        # User 2 tries to delete User 1's project
        response = client.delete(
            f"/projects/{project_id}",
            headers=self.user2_headers,
        )
        assert response.status_code == 403


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_json_request(self):
        """Test invalid JSON in request."""
        response = client.post(
            "/auth/register",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]

    def test_missing_required_fields(self):
        """Test request with missing required fields."""
        response = client.post("/auth/register", json={"username": "test"})
        assert response.status_code == 422

    def test_empty_project_list_structure(self):
        """Test list projects returns proper structure."""
        # Register user
        user_data = {"username": f"listtest_{id(self)}", "password": "Pass123!"}
        reg_response = client.post("/auth/register", json=user_data)
        headers = {"Authorization": f"Bearer {reg_response.json()['access_token']}"}

        # List projects
        response = client.get("/projects", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["projects"], list)
        assert isinstance(data["total"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
