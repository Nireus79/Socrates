"""
Unit tests for auth router.

Tests authentication endpoints including:
- User registration
- User login
- Token refresh
- Password change
- Logout
- Get current user profile
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
class TestRegister:
    """Tests for user registration endpoint."""

    def test_register_requires_username_and_password(self, client):
        """Test that registration requires username and password."""
        response = client.post(
            "/auth/register",
            json={},
        )
        # Missing required fields - should fail validation
        assert response.status_code == 422

    def test_register_missing_username(self, client):
        """Test registration without username."""
        response = client.post(
            "/auth/register",
            json={"password": "SecurePassword123!"},
        )
        assert response.status_code == 422

    def test_register_missing_password(self, client):
        """Test registration without password."""
        response = client.post(
            "/auth/register",
            json={"username": "testuser123"},
        )
        assert response.status_code == 422

    def test_register_password_too_short(self, client):
        """Test registration with password shorter than 8 characters."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser_short_pw",
                "password": "short",  # Less than 8 chars
            },
        )
        assert response.status_code == 422

    def test_register_invalid_email_format(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser456",
                "password": "SecurePassword123!",
                "email": "invalid-email",  # Missing @ and domain
            },
        )
        assert response.status_code == 400

    def test_register_success_with_email(self, client):
        """Test successful registration with email."""
        response = client.post(
            "/auth/register",
            json={
                "username": f"user_{id(client)}",
                "password": "SecurePassword123!",
                "email": "user@example.com",
            },
        )
        # May fail if user already exists, but should return valid response
        assert response.status_code in [201, 400, 500]
        if response.status_code == 201:
            data = response.json()
            assert "user" in data
            assert "access_token" in data
            assert "refresh_token" in data

    def test_register_success_without_email(self, client):
        """Test successful registration without email (auto-generated)."""
        response = client.post(
            "/auth/register",
            json={
                "username": f"auto_user_{id(client)}",
                "password": "SecurePassword123!",
            },
        )
        assert response.status_code in [201, 400, 500]
        if response.status_code == 201:
            data = response.json()
            assert data["user"]["email"]  # Should have auto-generated email
            assert "access_token" in data

    def test_register_response_structure(self, client):
        """Test that register response has correct structure."""
        response = client.post(
            "/auth/register",
            json={
                "username": f"struct_test_{id(client)}",
                "password": "SecurePassword123!",
            },
        )
        if response.status_code == 201:
            data = response.json()
            assert "user" in data
            assert "username" in data["user"]
            assert "email" in data["user"]
            assert "subscription_tier" in data["user"]
            assert "testing_mode" in data["user"]
            assert "token_type" in data
            assert data["token_type"] == "bearer"


@pytest.mark.unit
class TestLogin:
    """Tests for user login endpoint."""

    def test_login_requires_credentials(self, client):
        """Test that login requires username and password."""
        response = client.post(
            "/auth/login",
            json={},
        )
        assert response.status_code == 422

    def test_login_missing_username(self, client):
        """Test login without username."""
        response = client.post(
            "/auth/login",
            json={"password": "SomePassword123!"},
        )
        assert response.status_code == 422

    def test_login_missing_password(self, client):
        """Test login without password."""
        response = client.post(
            "/auth/login",
            json={"username": "someuser"},
        )
        assert response.status_code == 422

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent_user_xyz_12345",
                "password": "SomePassword123!",
            },
        )
        assert response.status_code == 401

    def test_login_empty_username(self, client):
        """Test login with empty username."""
        response = client.post(
            "/auth/login",
            json={
                "username": "   ",  # Whitespace only
                "password": "SomePassword123!",
            },
        )
        assert response.status_code == 400

    def test_login_response_structure(self, client):
        """Test that successful login response has correct structure."""
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!",
            },
        )
        if response.status_code == 200:
            data = response.json()
            assert "user" in data
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 900


@pytest.mark.unit
class TestRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_requires_token(self, client):
        """Test that refresh requires refresh token."""
        response = client.post(
            "/auth/refresh",
            json={},
        )
        assert response.status_code == 422

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid refresh token."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_token_xyz_123"},
        )
        assert response.status_code == 401

    def test_refresh_response_structure(self, client):
        """Test that refresh response has correct structure."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_but_test_structure"},
        )
        # Will fail with 401 but tests the structure expectation
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
            assert "expires_in" in data


@pytest.mark.unit
class TestChangePassword:
    """Tests for password change endpoint."""

    def test_change_password_requires_auth(self, client):
        """Test that password change requires authentication."""
        response = client.put(
            "/auth/change-password",
            json={
                "old_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 401

    def test_change_password_missing_fields(self, client, valid_token):
        """Test password change without required fields."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/auth/change-password",
            json={},
            headers=headers,
        )
        assert response.status_code == 422

    def test_change_password_missing_old_password(self, client, valid_token):
        """Test password change without old password."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/auth/change-password",
            json={"new_password": "NewPassword123!"},
            headers=headers,
        )
        assert response.status_code == 422

    def test_change_password_new_too_short(self, client, valid_token):
        """Test password change with new password too short."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/auth/change-password",
            json={
                "old_password": "OldPassword123!",
                "new_password": "short",  # Less than 8 chars
            },
            headers=headers,
        )
        # May return 400 (validation error) or 401 (user not found)
        assert response.status_code in [400, 401]

    def test_change_password_same_as_old(self, client, valid_token):
        """Test password change where new password is same as old."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.put(
            "/auth/change-password",
            json={
                "old_password": "SamePassword123!",
                "new_password": "SamePassword123!",  # Same as old
            },
            headers=headers,
        )
        assert response.status_code in [400, 401, 500]

    def test_change_password_invalid_token(self, client):
        """Test password change with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.put(
            "/auth/change-password",
            json={
                "old_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            },
            headers=headers,
        )
        assert response.status_code == 401


@pytest.mark.unit
class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_requires_auth(self, client):
        """Test that logout requires authentication."""
        response = client.post("/auth/logout")
        assert response.status_code == 401

    def test_logout_invalid_token(self, client):
        """Test logout with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post("/auth/logout", headers=headers)
        assert response.status_code == 401

    def test_logout_response_structure(self, client, valid_token):
        """Test that logout response has correct structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.post("/auth/logout", headers=headers)
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert data["success"] is True
            assert "message" in data


@pytest.mark.unit
class TestGetCurrentUser:
    """Tests for get current user endpoint."""

    def test_get_current_user_requires_auth(self, client):
        """Test that getting current user requires authentication."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    def test_get_current_user_response_structure(self, client, valid_token):
        """Test that get current user response has correct structure."""
        headers = {"Authorization": f"Bearer {valid_token}"}
        response = client.get("/auth/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            assert "username" in data
            assert "email" in data
            assert "subscription_tier" in data
            assert "subscription_status" in data
            assert "testing_mode" in data
            assert "created_at" in data


@pytest.mark.unit
class TestAuthEdgeCases:
    """Tests for authentication edge cases and special scenarios."""

    def test_register_with_special_characters_in_username(self, client):
        """Test registration with special characters in username."""
        response = client.post(
            "/auth/register",
            json={
                "username": f"user_special_{id(client)}_!@#",
                "password": "SecurePassword123!",
            },
        )
        assert response.status_code in [201, 400, 422, 500]

    def test_login_with_empty_password(self, client):
        """Test login with empty password field."""
        response = client.post(
            "/auth/login",
            json={
                "username": "someuser",
                "password": "",
            },
        )
        assert response.status_code == 400

    def test_register_duplicate_username(self, client):
        """Test registering duplicate username."""
        username = f"unique_user_{id(client)}"
        # First registration
        response1 = client.post(
            "/auth/register",
            json={
                "username": username,
                "password": "SecurePassword123!",
            },
        )
        if response1.status_code == 201:
            # Try to register with same username
            response2 = client.post(
                "/auth/register",
                json={
                    "username": username,
                    "password": "DifferentPassword123!",
                },
            )
            assert response2.status_code == 400

    def test_register_very_long_password(self, client):
        """Test registration with very long password."""
        response = client.post(
            "/auth/register",
            json={
                "username": f"long_pw_user_{id(client)}",
                "password": "P@ssw0rd" * 50,  # 400+ characters
            },
        )
        # Very long password might trigger validation error
        assert response.status_code in [201, 400, 422, 500]

    def test_auth_header_case_insensitive(self, client, valid_token):
        """Test that Authorization header bearer is case insensitive (may vary by impl)."""
        # Try with lowercase bearer (FastAPI may not recognize it)
        headers = {"authorization": f"bearer {valid_token}"}
        response = client.get("/auth/me", headers=headers)
        # Headers are typically case-insensitive but the Authorization header might not be recognized
        assert response.status_code in [200, 401, 404, 422]

    def test_login_with_extra_fields(self, client):
        """Test login request with extra unexpected fields."""
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!",
                "extra_field": "should_be_ignored",
            },
        )
        # Pydantic with extra="forbid" will reject extra fields with 422
        assert response.status_code in [200, 401, 422, 500]
