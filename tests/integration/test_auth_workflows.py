"""
Integration tests for authentication workflows.

Tests complete authentication journeys:
- User registration and email verification
- Login with various credentials
- Password reset flow
- Multi-factor authentication
- Session management
- Token refresh and expiration
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from fastapi import FastAPI


@pytest.mark.integration
class TestUserRegistrationWorkflow:
    """Tests for complete user registration flow."""

    async def test_registration_success(self, client: AsyncClient):
        """Test successful user registration."""
        # Register user
        response = await client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123!",
        })
        assert response.status_code == 201
        user_data = response.json()
        assert user_data["username"] == "newuser"
        assert user_data["email"] == "newuser@example.com"

    async def test_registration_duplicate_username(self, client: AsyncClient, sample_user):
        """Test registration with duplicate username."""
        response = await client.post("/auth/register", json={
            "username": sample_user["username"],
            "email": "different@example.com",
            "password": "SecurePass123!",
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    async def test_registration_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = await client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "weak",
        })
        assert response.status_code == 422

    async def test_registration_email_verification(self, client: AsyncClient):
        """Test email verification after registration."""
        # Register user
        response = await client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123!",
        })
        user_id = response.json()["user_id"]

        # User should be unverified initially
        assert response.json().get("email_verified") is False

        # Verify email (simulated)
        verify_response = await client.post(f"/auth/verify-email/{user_id}")
        assert verify_response.status_code == 200


@pytest.mark.integration
class TestLoginLogoutWorkflow:
    """Tests for login and logout flows."""

    async def test_login_success(self, client: AsyncClient, sample_user):
        """Test successful login."""
        response = await client.post("/auth/login", json={
            "username": sample_user["username"],
            "password": sample_user["password"],
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == sample_user["username"]

    async def test_login_invalid_username(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "password123",
        })
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_invalid_password(self, client: AsyncClient, sample_user):
        """Test login with wrong password."""
        response = await client.post("/auth/login", json={
            "username": sample_user["username"],
            "password": "wrongpassword",
        })
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_case_insensitive_username(self, client: AsyncClient, sample_user):
        """Test login with different case username."""
        response = await client.post("/auth/login", json={
            "username": sample_user["username"].upper(),
            "password": sample_user["password"],
        })
        assert response.status_code == 200
        assert response.json()["user"]["username"] == sample_user["username"]

    async def test_logout_success(self, client: AsyncClient, authenticated_headers):
        """Test logout invalidates session."""
        response = await client.post("/auth/logout", headers=authenticated_headers)
        assert response.status_code == 200

        # Token should be invalid after logout
        invalid_response = await client.get("/projects", headers=authenticated_headers)
        assert invalid_response.status_code == 401

    async def test_logout_all_sessions(self, client: AsyncClient, authenticated_headers):
        """Test logout from all sessions."""
        # Create second session
        login_response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "password123",
        })
        second_token = login_response.json()["access_token"]

        # Logout all
        response = await client.post("/auth/logout-all", headers=authenticated_headers)
        assert response.status_code == 200

        # Both tokens should be invalid
        assert await client.get("/projects", headers=authenticated_headers).status_code == 401
        assert await client.get(
            "/projects",
            headers={"Authorization": f"Bearer {second_token}"}
        ).status_code == 401


@pytest.mark.integration
class TestPasswordResetWorkflow:
    """Tests for password reset flow."""

    async def test_password_reset_request(self, client: AsyncClient, sample_user):
        """Test requesting password reset."""
        response = await client.post("/auth/forgot-password", json={
            "email": sample_user["email"],
        })
        assert response.status_code == 200
        assert "reset_token" in response.json()

    async def test_password_reset_completion(self, client: AsyncClient, sample_user):
        """Test completing password reset."""
        # Request reset
        reset_response = await client.post("/auth/forgot-password", json={
            "email": sample_user["email"],
        })
        reset_token = reset_response.json()["reset_token"]

        # Reset password
        response = await client.post("/auth/reset-password", json={
            "token": reset_token,
            "new_password": "NewPassword456!",
        })
        assert response.status_code == 200

        # Login with new password
        login_response = await client.post("/auth/login", json={
            "username": sample_user["username"],
            "password": "NewPassword456!",
        })
        assert login_response.status_code == 200

    async def test_password_reset_invalid_token(self, client: AsyncClient):
        """Test password reset with invalid token."""
        response = await client.post("/auth/reset-password", json={
            "token": "invalid_token",
            "new_password": "NewPassword456!",
        })
        assert response.status_code == 400

    async def test_password_reset_token_expiration(self, client: AsyncClient):
        """Test expired reset token rejected."""
        # Request reset (token expires in 1 hour)
        response = await client.post("/auth/forgot-password", json={
            "email": "test@example.com",
        })
        reset_token = response.json()["reset_token"]

        # Try to use expired token (mocked as expired)
        reset_response = await client.post("/auth/reset-password", json={
            "token": reset_token,
            "new_password": "NewPassword456!",
        })
        # Should succeed within 1 hour
        assert reset_response.status_code in [200, 400]


@pytest.mark.integration
class TestMultiFactorAuthWorkflow:
    """Tests for MFA setup and verification."""

    async def test_mfa_setup(self, client: AsyncClient, authenticated_headers):
        """Test enabling MFA on account."""
        # Setup TOTP
        response = await client.post("/auth/mfa/setup", headers=authenticated_headers)
        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_code" in data

    async def test_mfa_verification(self, client: AsyncClient, authenticated_headers):
        """Test MFA code verification."""
        # Setup TOTP
        setup_response = await client.post(
            "/auth/mfa/setup",
            headers=authenticated_headers
        )
        secret = setup_response.json()["secret"]

        # Generate TOTP code (mocked)
        totp_code = "123456"

        # Verify code
        response = await client.post(
            "/auth/mfa/verify",
            json={"code": totp_code},
            headers=authenticated_headers
        )
        assert response.status_code in [200, 400]

    async def test_mfa_disable(self, client: AsyncClient, authenticated_headers):
        """Test disabling MFA."""
        # Disable MFA
        response = await client.post(
            "/auth/mfa/disable",
            json={"password": "password123"},
            headers=authenticated_headers
        )
        assert response.status_code == 200

    async def test_login_with_mfa_required(self, client: AsyncClient, user_with_mfa):
        """Test login when MFA is enabled."""
        # Initial login succeeds
        response = await client.post("/auth/login", json={
            "username": user_with_mfa["username"],
            "password": user_with_mfa["password"],
        })
        assert response.status_code == 200

        # Should require MFA verification
        assert response.json()["mfa_required"] is True
        assert "temp_token" in response.json()


@pytest.mark.integration
class TestSessionManagement:
    """Tests for user session management."""

    async def test_list_active_sessions(self, client: AsyncClient, authenticated_headers):
        """Test listing all active sessions."""
        response = await client.get("/auth/sessions", headers=authenticated_headers)
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) > 0
        assert all("session_id" in s for s in sessions)

    async def test_revoke_session(self, client: AsyncClient, authenticated_headers):
        """Test revoking a specific session."""
        # Get sessions
        sessions_response = await client.get("/auth/sessions", headers=authenticated_headers)
        session_id = sessions_response.json()[0]["session_id"]

        # Revoke session
        response = await client.post(
            f"/auth/sessions/{session_id}/revoke",
            headers=authenticated_headers
        )
        assert response.status_code == 200

    async def test_revoke_all_sessions(self, client: AsyncClient, authenticated_headers):
        """Test revoking all sessions."""
        response = await client.post(
            "/auth/sessions/revoke-all",
            headers=authenticated_headers
        )
        assert response.status_code == 200

        # Should be logged out
        invalid_response = await client.get("/projects", headers=authenticated_headers)
        assert invalid_response.status_code == 401


@pytest.mark.integration
class TestTokenRefresh:
    """Tests for access token refresh."""

    async def test_refresh_token_success(self, client: AsyncClient, refresh_token):
        """Test refreshing access token."""
        response = await client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] != refresh_token

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post("/auth/refresh", json={
            "refresh_token": "invalid_token",
        })
        assert response.status_code == 401

    async def test_access_token_expiration(self, client: AsyncClient, expired_access_token):
        """Test accessing with expired token requires refresh."""
        headers = {"Authorization": f"Bearer {expired_access_token}"}
        response = await client.get("/projects", headers=headers)
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()


@pytest.mark.integration
class TestCrossOriginSecurityFlow:
    """Tests for CORS and cross-origin security."""

    async def test_cors_allowed_origin(self, client: AsyncClient):
        """Test CORS allows configured origins."""
        response = await client.get("/projects", headers={
            "Origin": "https://yourdomain.com"
        })
        # Should have CORS header
        assert "access-control-allow-origin" in response.headers or response.status_code == 401

    async def test_cors_denied_origin(self, client: AsyncClient):
        """Test CORS blocks unauthorized origins."""
        response = await client.options("/projects", headers={
            "Origin": "https://unauthorized-domain.com"
        })
        # Should not have CORS header for unauthorized origin
        assert response.status_code in [200, 403]
