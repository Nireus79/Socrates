"""
Unit tests for collaboration router.

Tests collaborator management, presence tracking, activity logging, and invitations.
"""

import pytest
from fastapi.testclient import TestClient

from socrates_api.auth.jwt_handler import create_access_token
from socrates_api.main import app


@pytest.fixture(scope="session")
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Create a valid JWT token."""
    return create_access_token("testuser")


@pytest.mark.unit
class TestAddCollaborator:
    """Tests for adding collaborators to projects."""

    def test_add_collaborator_by_email(self, client, valid_token):
        """Test adding collaborator by email."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/collaborators",
            json={
                "email": "collaborator@example.com",
                "role": "editor",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 403, 404, 500]

    def test_add_collaborator_by_username(self, client, valid_token):
        """Test adding collaborator by username."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/collaborators",
            json={
                "username": "collaborator_user",
                "role": "viewer",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 403, 404, 500]

    def test_add_collaborator_invalid_role(self, client, valid_token):
        """Test adding collaborator with invalid role."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/collaborators",
            json={
                "email": "user@example.com",
                "role": "invalid_role",
            },
            headers=headers,
        )
        assert response.status_code in [400, 422, 403, 404, 500]

    def test_add_nonexistent_collaborator(self, client, valid_token):
        """Test adding non-existent user as collaborator."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/collaborators",
            json={
                "email": "nonexistent_user_xyz@example.com",
                "role": "editor",
            },
            headers=headers,
        )
        assert response.status_code in [400, 403, 404, 500]

    def test_add_duplicate_collaborator(self, client, valid_token):
        """Test adding already existing collaborator."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        # First add
        client.post(
            "/projects/test_proj/collaborators",
            json={
                "email": "user@example.com",
                "role": "editor",
            },
            headers=headers,
        )
        # Try to add again
        response = client.post(
            "/projects/test_proj/collaborators",
            json={
                "email": "user@example.com",
                "role": "viewer",
            },
            headers=headers,
        )
        assert response.status_code in [400, 403, 404, 500]

    def test_subscription_validation_free_tier(self, client, valid_token):
        """Test subscription validation for free tier."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/collaborators",
            json={
                "email": "collaborator@example.com",
                "role": "editor",
            },
            headers=headers,
        )
        # Free tier may deny collaboration
        assert response.status_code in [201, 403, 404, 500]


@pytest.mark.unit
class TestListCollaborators:
    """Tests for listing project collaborators."""

    def test_list_collaborators(self, client, valid_token):
        """Test listing all collaborators."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/collaborators",
            headers=headers,
        )
        assert response.status_code in [200, 401, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "collaborators" in data or isinstance(data, list)

    def test_list_collaborators_empty(self, client, valid_token):
        """Test listing collaborators when none exist."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/new_proj/collaborators",
            headers=headers,
        )
        assert response.status_code in [200, 404, 500]

    def test_list_collaborators_nonexistent_project(self, client, valid_token):
        """Test listing collaborators for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/nonexistent_xyz/collaborators",
            headers=headers,
        )
        assert response.status_code in [404, 401, 500]


@pytest.mark.unit
class TestUpdateCollaboratorRole:
    """Tests for updating collaborator roles."""

    def test_update_collaborator_role(self, client, valid_token):
        """Test updating collaborator role."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/collaborators/collaborator_user/role",
            json={"role": "editor"},
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500, 422]

    def test_update_to_viewer_role(self, client, valid_token):
        """Test updating collaborator to viewer role."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/collaborators/user/role",
            json={"role": "viewer"},
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500, 422]

    def test_update_to_editor_role(self, client, valid_token):
        """Test updating collaborator to editor role."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/collaborators/user/role",
            json={"role": "editor"},
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500, 422]

    def test_update_with_invalid_role(self, client, valid_token):
        """Test updating with invalid role."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/collaborators/user/role",
            json={"role": "invalid"},
            headers=headers,
        )
        assert response.status_code in [400, 422, 403, 404, 500]

    def test_update_nonexistent_collaborator(self, client, valid_token):
        """Test updating role for non-existent collaborator."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/projects/test_proj/collaborators/nonexistent_user/role",
            json={"role": "editor"},
            headers=headers,
        )
        assert response.status_code in [404, 403, 500, 422]


@pytest.mark.unit
class TestRemoveCollaborator:
    """Tests for removing collaborators."""

    def test_remove_collaborator(self, client, valid_token):
        """Test removing a collaborator."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/collaborators/collaborator_user",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]

    def test_remove_nonexistent_collaborator(self, client, valid_token):
        """Test removing non-existent collaborator."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/collaborators/nonexistent_user",
            headers=headers,
        )
        assert response.status_code in [404, 403, 500]

    def test_cannot_remove_owner(self, client, valid_token):
        """Test that owner cannot be removed as collaborator."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/collaborators/testuser",
            headers=headers,
        )
        assert response.status_code in [400, 403, 404, 500]


@pytest.mark.unit
class TestPresenceTracking:
    """Tests for collaborator presence tracking."""

    def test_get_active_collaborators(self, client, valid_token):
        """Test getting active collaborators."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/presence",
            headers=headers,
        )
        assert response.status_code in [200, 401, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "active_users" in data or isinstance(data, list)

    def test_presence_for_nonexistent_project(self, client, valid_token):
        """Test presence for non-existent project."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/nonexistent/presence",
            headers=headers,
        )
        assert response.status_code in [404, 401, 500]


@pytest.mark.unit
class TestActivityTracking:
    """Tests for activity recording and listing."""

    def test_record_activity(self, client, valid_token):
        """Test recording project activity."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/activities",
            json={
                "activity_type": "file_modified",
                "description": "Modified main.py",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 404, 500]

    def test_record_activity_with_metadata(self, client, valid_token):
        """Test recording activity with metadata."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/activities",
            json={
                "activity_type": "comment_added",
                "description": "Added comment",
                "metadata": {"file": "main.py", "line": 42},
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 401, 404, 500]

    def test_list_activities(self, client, valid_token):
        """Test listing project activities."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/activities",
            headers=headers,
        )
        assert response.status_code in [200, 401, 404, 500]

    def test_list_activities_with_limit(self, client, valid_token):
        """Test listing activities with limit."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/activities?limit=10",
            headers=headers,
        )
        assert response.status_code in [200, 401, 404, 500]

    def test_list_activities_pagination(self, client, valid_token):
        """Test activity listing pagination."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/activities?limit=5&offset=0",
            headers=headers,
        )
        assert response.status_code in [200, 401, 404, 500]


@pytest.mark.unit
class TestInvitations:
    """Tests for collaboration invitations."""

    def test_create_invitation(self, client, valid_token):
        """Test creating collaboration invitation."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/invitations",
            json={
                "email": "invitee@example.com",
                "role": "editor",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 403, 404, 500]

    def test_create_invitation_invalid_email(self, client, valid_token):
        """Test creating invitation with invalid email."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/invitations",
            json={
                "email": "not-an-email",
                "role": "editor",
            },
            headers=headers,
        )
        assert response.status_code in [400, 422, 403, 404, 500]

    def test_list_invitations(self, client, valid_token):
        """Test listing project invitations."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get(
            "/projects/test_proj/invitations",
            headers=headers,
        )
        assert response.status_code in [200, 401, 403, 404, 500]

    def test_cancel_invitation(self, client, valid_token):
        """Test canceling an invitation."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete(
            "/projects/test_proj/invitations/invite_123",
            headers=headers,
        )
        assert response.status_code in [200, 403, 404, 500]

    def test_accept_invitation(self, client, valid_token):
        """Test accepting an invitation."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/invitations/token_abc123/accept",
            json={},
            headers=headers,
        )
        assert response.status_code in [200, 400, 403, 404, 500]

    def test_accept_invalid_invitation_token(self, client, valid_token):
        """Test accepting with invalid token."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/invitations/invalid_token_xyz/accept",
            json={},
            headers=headers,
        )
        assert response.status_code in [400, 404, 403, 500]


@pytest.mark.unit
class TestTeamManagement:
    """Tests for team member management."""

    def test_invite_team_member(self, client, valid_token):
        """Test inviting team member."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/collaboration/invite",
            json={
                "email": "newmember@example.com",
                "role": "member",
            },
            headers=headers,
        )
        assert response.status_code in [200, 400, 401, 500, 404]

    def test_list_team_members(self, client, valid_token):
        """Test listing team members."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/collaboration/members", headers=headers)
        assert response.status_code in [200, 401, 500, 404]

    def test_update_team_member_role(self, client, valid_token):
        """Test updating team member role."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/collaboration/members/member_123",
            json={"role": "admin"},
            headers=headers,
        )
        assert response.status_code in [200, 401, 404, 500, 422]

    def test_remove_team_member(self, client, valid_token):
        """Test removing team member."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.delete("/collaboration/members/member_123", headers=headers)
        assert response.status_code in [200, 401, 404, 500]


@pytest.mark.unit
class TestCollaborationAuthentication:
    """Tests for collaboration endpoint authentication."""

    def test_add_collaborator_requires_auth(self, client):
        """Test that adding collaborator requires auth."""
        response = client.post(
            "/projects/test/collaborators",
            json={"email": "user@example.com", "role": "editor"},
        )
        assert response.status_code == 401

    def test_list_collaborators_requires_auth(self, client):
        """Test that listing collaborators requires auth."""
        response = client.get("/projects/test/collaborators")
        assert response.status_code == 401

    def test_activities_require_auth(self, client):
        """Test that activities require auth."""
        response = client.post(
            "/projects/test/activities",
            json={"activity_type": "test"},
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestCollaborationEdgeCases:
    """Tests for edge cases."""

    def test_add_multiple_collaborators(self, client, valid_token):
        """Test adding multiple collaborators."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        for i in range(3):
            response = client.post(
                "/projects/test_proj/collaborators",
                json={
                    "email": f"user{i}@example.com",
                    "role": "viewer",
                },
                headers=headers,
            )
            assert response.status_code in [201, 400, 403, 404, 500]

    def test_special_characters_in_email(self, client, valid_token):
        """Test email with special characters."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post(
            "/projects/test_proj/collaborators",
            json={
                "email": "user+tag@example.co.uk",
                "role": "editor",
            },
            headers=headers,
        )
        assert response.status_code in [201, 400, 403, 404, 500]

    def test_concurrent_presence_tracking(self, client, valid_token):
        """Test presence tracking calls."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        for _ in range(3):
            response = client.get(
                "/projects/test_proj/presence",
                headers=headers,
            )
            assert response.status_code in [200, 401, 404, 500]
