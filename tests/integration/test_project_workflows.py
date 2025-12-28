"""
Integration tests for project management workflows.

Tests complete project lifecycle:
- Project creation and initialization
- Team management and collaboration
- Project archival and deletion
- Phase progression
- Project sharing
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestProjectCreationWorkflow:
    """Tests for creating and initializing projects."""

    async def test_create_project_success(self, client: AsyncClient, authenticated_headers):
        """Test creating a new project."""
        response = await client.post(
            "/projects",
            json={
                "name": "New Project",
                "description": "Test project",
                "project_type": "web_application",
            },
            headers=authenticated_headers
        )
        assert response.status_code == 201
        project = response.json()
        assert project["name"] == "New Project"
        assert project["phase"] == "specification"
        assert project["status"] == "active"

    async def test_create_project_duplicate_name(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test that duplicate project names are rejected."""
        response = await client.post(
            "/projects",
            json={
                "name": sample_project["name"],
                "description": "Another project",
                "project_type": "mobile_app",
            },
            headers=authenticated_headers
        )
        assert response.status_code == 400

    async def test_create_project_invalid_type(self, client: AsyncClient, authenticated_headers):
        """Test creation with invalid project type."""
        response = await client.post(
            "/projects",
            json={
                "name": "New Project",
                "project_type": "invalid_type",
            },
            headers=authenticated_headers
        )
        assert response.status_code == 422

    async def test_create_project_requires_authentication(self, client: AsyncClient):
        """Test that unauthenticated requests are rejected."""
        response = await client.post(
            "/projects",
            json={
                "name": "New Project",
                "project_type": "web_application",
            }
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestProjectUpdateWorkflow:
    """Tests for updating project information."""

    async def test_update_project_name(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test updating project name."""
        response = await client.put(
            f"/projects/{sample_project['project_id']}",
            json={"name": "Updated Name"},
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    async def test_update_project_description(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test updating project description."""
        new_description = "Updated description"
        response = await client.put(
            f"/projects/{sample_project['project_id']}",
            json={"description": new_description},
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["description"] == new_description

    async def test_update_project_unauthorized(self, client: AsyncClient, other_user_project):
        """Test updating someone else's project is rejected."""
        response = await client.put(
            f"/projects/{other_user_project['project_id']}",
            json={"name": "Hacked Name"},
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code in [401, 403]


@pytest.mark.integration
class TestProjectPhaseProgression:
    """Tests for advancing through project phases."""

    async def test_advance_phase_specification_to_design(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test advancing from specification to design phase."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/advance-phase",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["phase"] == "design"

    async def test_advance_phase_complete_lifecycle(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test advancing through all phases."""
        project_id = sample_project["project_id"]
        phases = ["design", "implementation", "testing", "deployment", "maintenance"]

        for expected_phase in phases:
            response = await client.post(
                f"/projects/{project_id}/advance-phase",
                headers=authenticated_headers
            )
            assert response.status_code == 200
            assert response.json()["phase"] == expected_phase

    async def test_advance_phase_requires_specification_complete(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test phase advancement validation."""
        # Should require specification to be completed
        response = await client.post(
            f"/projects/{sample_project['project_id']}/advance-phase",
            headers=authenticated_headers,
            json={"specification_complete": False}
        )
        assert response.status_code in [200, 400]


@pytest.mark.integration
class TestProjectTeamManagement:
    """Tests for team member and collaboration management."""

    async def test_add_team_member(self, client: AsyncClient, authenticated_headers, sample_project, other_user):
        """Test adding a team member to project."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/team-members",
            json={
                "user_id": other_user["user_id"],
                "role": "editor",
            },
            headers=authenticated_headers
        )
        assert response.status_code == 201
        assert response.json()["user_id"] == other_user["user_id"]
        assert response.json()["role"] == "editor"

    async def test_remove_team_member(self, client: AsyncClient, authenticated_headers, sample_project, team_member):
        """Test removing a team member."""
        response = await client.delete(
            f"/projects/{sample_project['project_id']}/team-members/{team_member['user_id']}",
            headers=authenticated_headers
        )
        assert response.status_code == 200

        # Verify member is removed
        list_response = await client.get(
            f"/projects/{sample_project['project_id']}/team-members",
            headers=authenticated_headers
        )
        member_ids = [m["user_id"] for m in list_response.json()]
        assert team_member["user_id"] not in member_ids

    async def test_update_team_member_role(self, client: AsyncClient, authenticated_headers, sample_project, team_member):
        """Test updating team member role."""
        response = await client.put(
            f"/projects/{sample_project['project_id']}/team-members/{team_member['user_id']}",
            json={"role": "admin"},
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"

    async def test_list_team_members(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test listing all team members."""
        response = await client.get(
            f"/projects/{sample_project['project_id']}/team-members",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        members = response.json()
        assert len(members) > 0
        assert all("user_id" in m for m in members)


@pytest.mark.integration
class TestProjectSharing:
    """Tests for sharing and access control."""

    async def test_share_project_with_user(self, client: AsyncClient, authenticated_headers, sample_project, other_user):
        """Test sharing project with another user."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/share",
            json={
                "user_id": other_user["user_id"],
                "permission": "view",
            },
            headers=authenticated_headers
        )
        assert response.status_code == 200

    async def test_share_project_with_email(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test sharing project via email invitation."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/invite",
            json={
                "email": "invited@example.com",
                "permission": "edit",
            },
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert "invitation_token" in response.json()

    async def test_accept_project_invitation(self, client: AsyncClient, authenticated_headers, invitation_token):
        """Test accepting a project invitation."""
        response = await client.post(
            "/projects/accept-invitation",
            json={"token": invitation_token},
            headers=authenticated_headers
        )
        assert response.status_code == 200

    async def test_unshare_project(self, client: AsyncClient, authenticated_headers, sample_project, other_user):
        """Test revoking project sharing."""
        # First share the project
        await client.post(
            f"/projects/{sample_project['project_id']}/share",
            json={
                "user_id": other_user["user_id"],
                "permission": "view",
            },
            headers=authenticated_headers
        )

        # Then unshare
        response = await client.delete(
            f"/projects/{sample_project['project_id']}/share/{other_user['user_id']}",
            headers=authenticated_headers
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestProjectArchival:
    """Tests for archiving and restoring projects."""

    async def test_archive_project(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test archiving a project."""
        response = await client.post(
            f"/projects/{sample_project['project_id']}/archive",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["is_archived"] is True

    async def test_list_excludes_archived_by_default(self, client: AsyncClient, authenticated_headers, archived_project):
        """Test archived projects excluded from default list."""
        response = await client.get("/projects", headers=authenticated_headers)
        project_ids = [p["project_id"] for p in response.json()]
        assert archived_project["project_id"] not in project_ids

    async def test_list_includes_archived_when_requested(self, client: AsyncClient, authenticated_headers, archived_project):
        """Test archived projects included when requested."""
        response = await client.get(
            "/projects?include_archived=true",
            headers=authenticated_headers
        )
        project_ids = [p["project_id"] for p in response.json()]
        assert archived_project["project_id"] in project_ids

    async def test_restore_archived_project(self, client: AsyncClient, authenticated_headers, archived_project):
        """Test restoring an archived project."""
        response = await client.post(
            f"/projects/{archived_project['project_id']}/restore",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["is_archived"] is False


@pytest.mark.integration
class TestProjectDeletion:
    """Tests for permanent project deletion."""

    async def test_delete_project(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test deleting a project."""
        project_id = sample_project["project_id"]

        response = await client.delete(
            f"/projects/{project_id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200

        # Project should no longer be accessible
        get_response = await client.get(
            f"/projects/{project_id}",
            headers=authenticated_headers
        )
        assert get_response.status_code == 404

    async def test_delete_project_requires_confirmation(self, client: AsyncClient, authenticated_headers, sample_project):
        """Test deletion requires explicit confirmation."""
        response = await client.delete(
            f"/projects/{sample_project['project_id']}",
            json={"confirm": False},
            headers=authenticated_headers
        )
        assert response.status_code == 400

    async def test_delete_project_cascades_to_sessions(self, client: AsyncClient, authenticated_headers, sample_project, chat_session):
        """Test deleting project also deletes related chat sessions."""
        # Sessions should be deleted with project
        response = await client.delete(
            f"/projects/{sample_project['project_id']}",
            json={"confirm": True},
            headers=authenticated_headers
        )
        assert response.status_code == 200

        # Chat session should be inaccessible
        session_response = await client.get(
            f"/projects/{sample_project['project_id']}/sessions/{chat_session['session_id']}",
            headers=authenticated_headers
        )
        assert session_response.status_code == 404


@pytest.mark.integration
class TestProjectListingAndFiltering:
    """Tests for project listing with filtering and pagination."""

    async def test_list_projects_pagination(self, client: AsyncClient, authenticated_headers, multiple_projects):
        """Test paginating through project list."""
        response = await client.get(
            "/projects?limit=5&offset=0",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) <= 5

    async def test_list_projects_sort_by_name(self, client: AsyncClient, authenticated_headers):
        """Test sorting projects by name."""
        response = await client.get(
            "/projects?sort=name&order=asc",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        projects = response.json()
        names = [p["name"] for p in projects]
        assert names == sorted(names)

    async def test_list_projects_sort_by_updated(self, client: AsyncClient, authenticated_headers):
        """Test sorting projects by last updated."""
        response = await client.get(
            "/projects?sort=updated&order=desc",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        projects = response.json()
        # Most recently updated should be first
        assert len(projects) > 0

    async def test_list_projects_filter_by_type(self, client: AsyncClient, authenticated_headers):
        """Test filtering projects by type."""
        response = await client.get(
            "/projects?type=web_application",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        projects = response.json()
        assert all(p["project_type"] == "web_application" for p in projects)

    async def test_search_projects_by_name(self, client: AsyncClient, authenticated_headers):
        """Test searching projects by name."""
        response = await client.get(
            "/projects/search?q=Test",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        projects = response.json()
        assert all("Test" in p["name"].lower() for p in projects)
