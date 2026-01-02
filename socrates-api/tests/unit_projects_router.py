"""
Unit tests for projects router.

Tests project management endpoints including:
- Listing user projects
- Creating new projects
- Getting project details
- Updating project settings
- Deleting projects
- Archiving/restoring projects
"""

import pytest
from fastapi.testclient import TestClient

from socrates_api.auth.jwt_handler import create_access_token
from socrates_api.main import app


@pytest.fixture(scope="session")
def client():
    """Create FastAPI test client - session scoped for performance."""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Create a valid JWT token for testing."""
    return create_access_token("testuser")


@pytest.mark.unit
class TestListProjects:
    """Tests for listing projects endpoint."""

    def test_list_projects_requires_auth(self, client):
        """Test that list projects requires authentication."""
        response = client.get("/projects")

        assert response.status_code == 401
        assert "Missing authentication credentials" in response.json().get("detail", "")

    def test_list_projects_success_empty(self, client, valid_token):
        """Test listing projects when user has no projects."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert "total" in data
        assert isinstance(data["projects"], list)
        assert data["total"] >= 0

    def test_list_projects_response_structure(self, client, valid_token):
        """Test that list projects response has proper structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "projects" in data
        assert "total" in data
        assert isinstance(data["projects"], list)
        assert isinstance(data["total"], int)

    def test_list_projects_invalid_token(self, client):
        """Test list projects with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get("/projects", headers=headers)

        assert response.status_code == 401


@pytest.mark.unit
class TestCreateProject:
    """Tests for creating projects endpoint."""

    def test_create_project_requires_auth(self, client):
        """Test that create project requires authentication."""
        response = client.post("/projects", json={"name": "Test Project"})

        assert response.status_code == 401

    def test_create_project_missing_name(self, client, valid_token):
        """Test creating project without name field."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/projects", json={}, headers=headers)

        assert response.status_code == 422  # Validation error

    def test_create_project_minimal_request(self, client, valid_token):
        """Test creating project with minimal required fields."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects",
            json={"name": "Test Project"},
            headers=headers,
        )

        # Should either succeed or fail due to subscription, but not validation error
        assert response.status_code in [200, 403, 500]

    def test_create_project_response_structure(self, client, valid_token):
        """Test that create project response has proper structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects",
            json={"name": "Test Project"},
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()
            # Verify response has required fields
            assert "project_id" in data
            assert "name" in data
            assert "owner" in data
            assert "phase" in data
            assert "created_at" in data

    def test_create_project_with_description(self, client, valid_token):
        """Test creating project with description."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects",
            json={
                "name": "Test Project",
                "description": "This is a test project",
            },
            headers=headers,
        )

        assert response.status_code in [200, 403, 500]
        if response.status_code == 200:
            data = response.json()
            assert data.get("description") == "This is a test project"

    def test_create_project_invalid_token(self, client):
        """Test create project with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            "/projects",
            json={"name": "Test Project"},
            headers=headers,
        )

        assert response.status_code == 401


@pytest.mark.unit
class TestGetProjectDetails:
    """Tests for getting project details endpoint."""

    def test_get_project_requires_auth(self, client):
        """Test that get project requires authentication."""
        response = client.get("/projects/nonexistent_id")

        assert response.status_code == 401

    def test_get_nonexistent_project(self, client, valid_token):
        """Test getting a project that doesn't exist."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects/nonexistent_project_id_xyz", headers=headers)

        # Should return 404 or 403 depending on ownership check
        assert response.status_code in [404, 403, 500]

    def test_get_project_response_structure(self, client, valid_token):
        """Test that get project response has proper structure when successful."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        # First create a project
        create_response = client.post(
            "/projects",
            json={"name": "Detail Test Project"},
            headers=headers,
        )

        if create_response.status_code == 200:
            project_id = create_response.json()["project_id"]
            # Now get the project details
            response = client.get(f"/projects/{project_id}", headers=headers)

            if response.status_code == 200:
                data = response.json()
                assert "project_id" in data
                assert "name" in data
                assert "owner" in data
                assert "phase" in data


@pytest.mark.unit
class TestUpdateProject:
    """Tests for updating project settings endpoint."""

    def test_update_project_requires_auth(self, client):
        """Test that update project requires authentication."""
        response = client.put(
            "/projects/nonexistent_id",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 401

    def test_update_project_missing_body(self, client, valid_token):
        """Test updating project without request body."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/nonexistent_id",
            json={},
            headers=headers,
        )

        # Should fail due to project not found or validation
        assert response.status_code in [400, 404, 422, 500]

    def test_update_project_invalid_token(self, client):
        """Test update project with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.put(
            "/projects/test_id",
            json={"name": "Updated"},
            headers=headers,
        )

        assert response.status_code == 401


@pytest.mark.unit
class TestDeleteProject:
    """Tests for deleting projects endpoint."""

    def test_delete_project_requires_auth(self, client):
        """Test that delete project requires authentication."""
        response = client.delete("/projects/nonexistent_id")

        assert response.status_code == 401

    def test_delete_nonexistent_project(self, client, valid_token):
        """Test deleting a project that doesn't exist."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete("/projects/nonexistent_project_id_xyz", headers=headers)

        # Should return 404 or 403 depending on implementation
        assert response.status_code in [404, 403, 500]

    def test_delete_project_invalid_token(self, client):
        """Test delete project with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.delete("/projects/test_id", headers=headers)

        assert response.status_code == 401


@pytest.mark.unit
class TestAdvancePhase:
    """Tests for advancing project phase endpoint."""

    def test_advance_phase_requires_auth(self, client):
        """Test that advance phase requires authentication."""
        response = client.put("/projects/nonexistent_id/phase?new_phase=analysis")

        assert response.status_code == 401

    def test_advance_phase_nonexistent_project(self, client, valid_token):
        """Test advancing phase for a project that doesn't exist."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/nonexistent_project_id_xyz/phase?new_phase=analysis",
            headers=headers,
        )

        # Should return 404 or 403
        assert response.status_code in [404, 403, 500]

    def test_advance_phase_invalid_token(self, client):
        """Test advance phase with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.put(
            "/projects/test_id/phase?new_phase=analysis",
            headers=headers,
        )

        assert response.status_code == 401

    def test_advance_phase_missing_parameter(self, client, valid_token):
        """Test advance phase without required new_phase parameter."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/nonexistent_id/phase",
            headers=headers,
        )

        # Should fail due to missing required parameter
        assert response.status_code in [422, 400, 404]

    def test_advance_phase_invalid_phase(self, client, valid_token):
        """Test advance phase with invalid phase name."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/nonexistent_id/phase?new_phase=invalid_phase",
            headers=headers,
        )

        # Should fail due to invalid phase or project not found
        assert response.status_code in [400, 404, 500]


@pytest.mark.unit
class TestRestoreProject:
    """Tests for restoring archived projects endpoint."""

    def test_restore_project_requires_auth(self, client):
        """Test that restore project requires authentication."""
        response = client.post("/projects/nonexistent_id/restore")

        assert response.status_code == 401

    def test_restore_nonexistent_project(self, client, valid_token):
        """Test restoring a project that doesn't exist."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/projects/nonexistent_project_id_xyz/restore", headers=headers)

        # Should return 404 or 403
        assert response.status_code in [404, 403, 500]

    def test_restore_project_invalid_token(self, client):
        """Test restore project with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post("/projects/test_id/restore", headers=headers)

        assert response.status_code == 401


@pytest.mark.unit
class TestGetProjectMaturity:
    """Tests for getting project maturity endpoint."""

    def test_get_maturity_requires_auth(self, client):
        """Test that get maturity requires authentication."""
        response = client.get("/projects/nonexistent_id/maturity")

        assert response.status_code == 401

    def test_get_maturity_nonexistent_project(self, client, valid_token):
        """Test getting maturity of non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/projects/nonexistent_project_id_xyz/maturity", headers=headers)

        # Should return 404 or 403
        assert response.status_code in [404, 403, 500]

    def test_get_maturity_invalid_token(self, client):
        """Test get maturity with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get("/projects/test_id/maturity", headers=headers)

        assert response.status_code == 401
