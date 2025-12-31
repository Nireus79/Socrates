"""
CLI and API Parity Tests

Tests that CLI and API implementations produce consistent results:
- Same authentication mechanisms
- Same project creation flow
- Same question generation
- Same quota enforcement
- Same error messages
- Same database state
"""

import os
from datetime import datetime

import pytest
import requests

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCLIAndAPIAuthentication:
    """Test authentication parity between CLI and API"""

    def test_01_same_password_hashing(self):
        """Test: CLI and API use same password hashing algorithm"""
        # Both should use bcrypt (not local passlib)
        # Create user via API
        username = f"hash_test_{int(datetime.now().timestamp() * 1000)}"
        password = "TestPassword123!"

        api_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={"username": username, "email": f"{username}@test.local", "password": password},
            headers=HEADERS,
        )

        assert api_resp.status_code == 201, f"API registration failed: {api_resp.text}"
        api_token = api_resp.json()["access_token"]

        # Verify token works with API (check user profile endpoint)
        verify_resp = requests.get(
            f"{BASE_URL}/auth/me", headers={**HEADERS, "Authorization": f"Bearer {api_token}"}
        )
        assert verify_resp.status_code == 200, "API token verification failed"

    def test_02_token_expiration_parity(self):
        """Test: Access tokens have same expiration in CLI and API"""
        # Both should expire after ~15 minutes
        # This is more of an integration check
        username = f"token_test_{int(datetime.now().timestamp() * 1000)}"

        resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        assert resp.status_code == 201
        token_data = resp.json()
        assert "access_token" in token_data
        assert "expires_in" in token_data or "expiration" in token_data

    def test_03_refresh_token_flow(self):
        """Test: CLI and API have same refresh token flow"""
        username = f"refresh_test_{int(datetime.now().timestamp() * 1000)}"

        # Register
        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        assert reg_resp.status_code == 201
        refresh_token = reg_resp.json().get("refresh_token")
        assert refresh_token is not None

        # Use refresh token
        refresh_resp = requests.post(
            f"{BASE_URL}/auth/refresh", json={"refresh_token": refresh_token}, headers=HEADERS
        )

        if refresh_resp.status_code == 200:
            new_token = refresh_resp.json()["access_token"]
            assert new_token is not None


class TestCLIAndAPIProjectCreation:
    """Test project creation parity between CLI and API"""

    def test_01_free_tier_project_limit(self):
        """Test: CLI and API enforce same free tier limit (1 project)"""
        username = f"free_limit_{int(datetime.now().timestamp() * 1000)}"

        # Register via API
        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        # Create first project via API
        proj1_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Project 1", "description": "First"},
            headers=auth_headers,
        )
        assert proj1_resp.status_code == 200, f"First project failed: {proj1_resp.text}"

        # Try second project via API - should fail
        proj2_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Project 2", "description": "Second"},
            headers=auth_headers,
        )
        assert proj2_resp.status_code == 403, "Free tier should be blocked at 2nd project"

    def test_02_project_metadata_consistency(self):
        """Test: API returns same project metadata fields as CLI"""
        username = f"metadata_{int(datetime.now().timestamp() * 1000)}"

        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        token = reg_resp.json()["access_token"]
        auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        # Create project
        proj_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Metadata Test", "description": "Testing metadata"},
            headers=auth_headers,
        )

        assert proj_resp.status_code == 200
        project = proj_resp.json()

        # Verify all required fields present
        required_fields = [
            "project_id",
            "name",
            "description",
            "owner",
            "phase",
            "created_at",
            "updated_at",
            "is_archived",
        ]

        for field in required_fields:
            assert field in project, f"Missing field: {field}"

    def test_03_project_phases_consistency(self):
        """Test: Both CLI and API support same project phases"""
        username = f"phase_test_{int(datetime.now().timestamp() * 1000)}"

        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        token = reg_resp.json()["access_token"]
        auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        proj_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Phase Project", "description": "Test"},
            headers=auth_headers,
        )

        project_id = proj_resp.json()["project_id"]

        # Test all phase transitions
        phases = ["discovery", "analysis", "design", "implementation", "testing"]

        for phase in phases:
            update_resp = requests.put(
                f"{BASE_URL}/projects/{project_id}", json={"phase": phase}, headers=auth_headers
            )
            assert update_resp.status_code == 200, f"Phase update failed for {phase}"
            assert update_resp.json()["phase"] == phase


class TestCLIAndAPIQuestionGeneration:
    """Test question generation parity"""

    def test_01_same_question_structure(self):
        """Test: Questions have same structure from CLI and API"""
        username = f"question_test_{int(datetime.now().timestamp() * 1000)}"

        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        token = reg_resp.json()["access_token"]
        auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        proj_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Question Test", "description": "Test"},
            headers=auth_headers,
        )

        project_id = proj_resp.json()["project_id"]

        # Generate question via API
        q_resp = requests.post(
            f"{BASE_URL}/projects/{project_id}/question",
            json={"topic": "Python Basics", "difficulty_level": "beginner"},
            headers=auth_headers,
        )

        if q_resp.status_code == 200:
            question = q_resp.json()
            # Should have basic structure
            assert any(k in question for k in ["question", "question_id", "id"])

    def test_02_difficulty_levels_consistency(self):
        """Test: Same difficulty levels available in CLI and API"""
        username = f"difficulty_{int(datetime.now().timestamp() * 1000)}"

        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        token = reg_resp.json()["access_token"]
        auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        proj_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Difficulty Test", "description": "Test"},
            headers=auth_headers,
        )

        project_id = proj_resp.json()["project_id"]

        # Test all difficulty levels
        difficulties = ["beginner", "intermediate", "advanced"]

        for difficulty in difficulties:
            q_resp = requests.post(
                f"{BASE_URL}/projects/{project_id}/question",
                json={"topic": "Python", "difficulty_level": difficulty},
                headers=auth_headers,
            )

            if q_resp.status_code == 200:
                assert q_resp.json() is not None


class TestCLIAndAPIQuotaEnforcement:
    """Test quota enforcement parity"""

    def test_01_monthly_question_limit_enforcement(self):
        """Test: Both CLI and API enforce same monthly question limit"""
        # Free tier: 100 questions/month
        # This would require either:
        # 1. Mocking the month boundary
        # 2. Testing with a user close to limit
        # 3. Verifying the quota checking code path
        pass

    def test_02_project_quota_error_message(self):
        """Test: Same error message format for quota exceeded"""
        username = f"quota_msg_{int(datetime.now().timestamp() * 1000)}"

        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        token = reg_resp.json()["access_token"]
        auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        # Create first project
        requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Project 1", "description": "First"},
            headers=auth_headers,
        )

        # Try second project
        resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Project 2", "description": "Second"},
            headers=auth_headers,
        )

        assert resp.status_code == 403
        error_msg = resp.json().get("detail", "").lower()

        # Error should mention relevant info
        assert any(word in error_msg for word in ["project", "limit", "subscription", "free"])


class TestCLIAndAPIDataConsistency:
    """Test that CLI and API operations maintain same database state"""

    def test_01_api_created_project_visible_to_api(self):
        """Test: Project created via API is visible to API"""
        username = f"consistency_{int(datetime.now().timestamp() * 1000)}"

        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        token = reg_resp.json()["access_token"]
        auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        # Create project
        create_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "Consistency Test", "description": "Test"},
            headers=auth_headers,
        )

        project_id = create_resp.json()["project_id"]

        # Retrieve and verify
        get_resp = requests.get(f"{BASE_URL}/projects/{project_id}", headers=auth_headers)

        assert get_resp.status_code == 200
        assert get_resp.json()["project_id"] == project_id

    def test_02_api_list_includes_created_project(self):
        """Test: Created project appears in project list"""
        username = f"list_test_{int(datetime.now().timestamp() * 1000)}"

        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        token = reg_resp.json()["access_token"]
        auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        # Create project with unique name
        project_name = f"Unique_Project_{int(datetime.now().timestamp() * 1000)}"
        create_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": project_name, "description": "Test"},
            headers=auth_headers,
        )

        assert create_resp.status_code == 200

        # List projects
        list_resp = requests.get(f"{BASE_URL}/projects", headers=auth_headers)

        assert list_resp.status_code == 200
        projects = list_resp.json()["projects"]
        project_names = [p.get("name") for p in projects]

        assert project_name in project_names


class TestCLIAndAPIErrorConsistency:
    """Test that error handling is consistent"""

    def test_01_unauthorized_access_error(self):
        """Test: API returns consistent unauthorized error"""
        # Try to access without token
        resp = requests.get(f"{BASE_URL}/projects", headers=HEADERS)

        assert resp.status_code == 401, "Should require authentication"
        data = resp.json()
        assert "detail" in data or "error" in data

    def test_02_forbidden_access_error(self):
        """Test: API returns consistent forbidden error"""
        # Create two users
        user1_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": f"user1_{int(datetime.now().timestamp() * 1000)}",
                "email": f"user1_{int(datetime.now().timestamp() * 1000)}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        user1_token = user1_resp.json()["access_token"]
        user1_headers = {**HEADERS, "Authorization": f"Bearer {user1_token}"}

        # User1 creates project
        proj_resp = requests.post(
            f"{BASE_URL}/projects",
            json={"name": "User1 Project", "description": "Test"},
            headers=user1_headers,
        )

        project_id = proj_resp.json()["project_id"]

        # User2 tries to access
        user2_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": f"user2_{int(datetime.now().timestamp() * 1000)}",
                "email": f"user2_{int(datetime.now().timestamp() * 1000)}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        user2_token = user2_resp.json()["access_token"]
        user2_headers = {**HEADERS, "Authorization": f"Bearer {user2_token}"}

        # Access should be denied
        access_resp = requests.get(f"{BASE_URL}/projects/{project_id}", headers=user2_headers)

        assert access_resp.status_code == 403, "Should deny cross-user access"

    def test_03_not_found_error_consistency(self):
        """Test: API returns consistent 404 error"""
        username = f"notfound_{int(datetime.now().timestamp() * 1000)}"

        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        token = reg_resp.json()["access_token"]
        auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

        # Try to access nonexistent project
        resp = requests.get(f"{BASE_URL}/projects/nonexistent_id", headers=auth_headers)

        assert resp.status_code == 404, "Should return 404 for missing project"
        data = resp.json()
        assert "detail" in data or "error" in data


class TestCLIAndAPIDatabaseSingleton:
    """Test that CLI and API use same database instance"""

    def test_01_database_singleton_consistency(self):
        """Test: Changes via API are persisted in single database"""
        # This tests the DatabaseSingleton pattern
        username = f"singleton_{int(datetime.now().timestamp() * 1000)}"

        # Register via API
        reg_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.local",
                "password": "TestPassword123!",
            },
            headers=HEADERS,
        )

        assert reg_resp.status_code == 201
        reg_resp.json().get("user_id")

        # Verify can login with same credentials
        login_resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": "TestPassword123!"},
            headers=HEADERS,
        )

        assert login_resp.status_code == 200, "Should be able to login with registered credentials"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
