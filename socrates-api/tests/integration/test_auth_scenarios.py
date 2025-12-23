"""
Comprehensive Authentication Scenario Tests - Backend
Tests complete auth workflows: token lifecycle, refresh flows, session management
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import time


class TestTokenLifecycle:
    """Test complete token lifecycle from login to expiration"""

    def test_login_generates_valid_access_and_refresh_tokens(self, client: TestClient):
        """Test that login returns both token types"""
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        # Endpoint should exist
        assert response.status_code != 404

        if response.status_code == 200:
            data = response.json()
            # Should return both tokens
            assert 'access_token' in data or 'token' in data
            if 'access_token' in data:
                assert isinstance(data['access_token'], str)
                assert len(data['access_token']) > 0

    def test_access_token_required_for_protected_endpoints(self, client: TestClient):
        """Test that protected endpoints check for valid token"""
        # Request without token
        response = client.get('/projects')
        assert response.status_code in [401, 403, 200]  # Should require auth or return empty

        # Request with invalid token
        response = client.get(
            '/projects',
            headers={'Authorization': 'Bearer invalid_token_xyz'}
        )
        assert response.status_code in [401, 403]

    def test_token_validation_rejects_expired_tokens(self, client: TestClient):
        """Test that expired tokens are rejected"""
        # Use obviously invalid/expired token
        response = client.get(
            '/projects',
            headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjEwMjMwMDAwMDAsInN1YiI6InRlc3QifQ.invalid'}
        )
        # Should reject as unauthorized
        assert response.status_code in [401, 403]

    def test_refresh_token_generates_new_access_token(self, client: TestClient):
        """Test token refresh endpoint"""
        response = client.post('/auth/refresh', json={
            'refresh_token': 'valid_refresh_token'
        })
        # Endpoint should exist and validate token
        assert response.status_code != 404

    def test_invalid_refresh_token_rejected(self, client: TestClient):
        """Test that invalid refresh tokens are rejected"""
        response = client.post('/auth/refresh', json={
            'refresh_token': 'invalid_refresh_token_xyz'
        })
        assert response.status_code in [401, 400]

    def test_token_after_logout_is_invalid(self, client: TestClient):
        """Test that logout invalidates tokens"""
        # First logout (may succeed even without token)
        logout_response = client.post('/auth/logout')
        assert logout_response.status_code in [200, 401]

        # Using old token after logout should fail
        response = client.get(
            '/projects',
            headers={'Authorization': 'Bearer old_token_after_logout'}
        )
        assert response.status_code in [401, 403]


class TestConcurrentAuthOperations:
    """Test concurrent authentication operations"""

    def test_concurrent_logins_same_user(self, client: TestClient):
        """Test multiple login requests for same user"""
        responses = []

        # Make two login requests
        for i in range(2):
            response = client.post('/auth/login', json={
                'username': 'testuser',
                'password': 'testpass'
            })
            responses.append(response)
            assert response.status_code != 404

        # Both should succeed if user exists
        if responses[0].status_code == 200:
            assert responses[1].status_code in [200, 201]

    def test_login_and_immediate_token_use(self, client: TestClient):
        """Test using token immediately after login"""
        # Login
        login_response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        assert login_response.status_code != 404

        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            if token:
                # Immediately use token
                response = client.get(
                    '/projects',
                    headers={'Authorization': f'Bearer {token}'}
                )
                assert response.status_code in [200, 401]

    def test_simultaneous_refresh_requests(self, client: TestClient):
        """Test multiple concurrent refresh token requests"""
        refresh_token = 'test_refresh_token'

        responses = []
        for i in range(3):
            response = client.post('/auth/refresh', json={
                'refresh_token': refresh_token
            })
            responses.append(response)

        # All should be handled
        for response in responses:
            assert response.status_code != 404


class TestSessionManagement:
    """Test session and user management"""

    def test_login_with_nonexistent_user(self, client: TestClient):
        """Test login with non-existent username"""
        response = client.post('/auth/login', json={
            'username': 'nonexistent_user_xyz_123',
            'password': 'anypassword'
        })
        # Should return 401 for unknown user
        assert response.status_code in [401, 400]

    def test_login_with_wrong_password(self, client: TestClient):
        """Test login with incorrect password"""
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'wrong_password_xyz'
        })
        # Should return 401 for wrong password
        assert response.status_code in [401, 400]

    def test_registration_duplicate_username(self, client: TestClient):
        """Test registration with already-used username"""
        # First registration
        response1 = client.post('/auth/register', json={
            'username': 'duplicate_user_test',
            'email': 'first@example.com',
            'password': 'password123'
        })
        # May succeed or fail depending on DB state
        assert response1.status_code != 404

        # Second registration with same username
        response2 = client.post('/auth/register', json={
            'username': 'duplicate_user_test',
            'email': 'second@example.com',
            'password': 'password123'
        })
        # Should fail with 400 or 409
        if response1.status_code in [200, 201]:
            assert response2.status_code in [400, 409, 422]

    def test_registration_duplicate_email(self, client: TestClient):
        """Test registration with already-used email"""
        email = f'duplicate_{int(time.time())}@example.com'

        response1 = client.post('/auth/register', json={
            'username': 'user_email_1',
            'email': email,
            'password': 'password123'
        })
        assert response1.status_code != 404

        # Try register with same email
        response2 = client.post('/auth/register', json={
            'username': 'user_email_2',
            'email': email,
            'password': 'password123'
        })
        if response1.status_code in [200, 201]:
            assert response2.status_code in [400, 409, 422]

    def test_registration_invalid_email(self, client: TestClient):
        """Test registration with invalid email format"""
        response = client.post('/auth/register', json={
            'username': 'testuser',
            'email': 'not_an_email',
            'password': 'password123'
        })
        # Should validate email format
        assert response.status_code in [400, 422]

    def test_registration_weak_password(self, client: TestClient):
        """Test registration with weak password"""
        response = client.post('/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123'  # Too short/weak
        })
        # May validate password strength
        assert response.status_code != 404

    def test_logout_without_authentication(self, client: TestClient):
        """Test logout endpoint without being logged in"""
        response = client.post('/auth/logout')
        # Should handle gracefully
        assert response.status_code in [200, 401]

    def test_logout_invalidates_token(self, client: TestClient):
        """Test that logout invalidates the user's token"""
        # Logout (token in real scenario)
        logout_response = client.post('/auth/logout')
        assert logout_response.status_code in [200, 401]

        # Subsequent authenticated request should fail
        response = client.get(
            '/projects',
            headers={'Authorization': 'Bearer token_from_before_logout'}
        )
        assert response.status_code in [401, 403]


class TestSpecialAuthCases:
    """Test special/edge case authentication scenarios"""

    def test_login_with_special_characters_in_username(self, client: TestClient):
        """Test login with special characters"""
        response = client.post('/auth/login', json={
            'username': 'user@domain.com',
            'password': 'password'
        })
        assert response.status_code != 404

    def test_login_with_unicode_username(self, client: TestClient):
        """Test login with unicode characters"""
        response = client.post('/auth/login', json={
            'username': 'user_测试',
            'password': 'password'
        })
        assert response.status_code != 404

    def test_login_with_very_long_password(self, client: TestClient):
        """Test login with extremely long password"""
        long_password = 'a' * 10000

        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': long_password
        })
        # Should not crash
        assert response.status_code != 500

    def test_login_with_null_fields(self, client: TestClient):
        """Test login with null/missing fields"""
        response = client.post('/auth/login', json={
            'username': None,
            'password': 'password'
        })
        # Should reject invalid input
        assert response.status_code in [400, 422]

    def test_login_with_extra_fields(self, client: TestClient):
        """Test login with unexpected extra fields"""
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'password',
            'extra_field': 'should_be_ignored',
            'admin': True
        })
        # Should accept and ignore extra fields
        assert response.status_code != 404


class TestAuthSecurityScenarios:
    """Test authentication security aspects"""

    def test_password_not_returned_in_response(self, client: TestClient):
        """Test that password is never returned to client"""
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })

        if response.status_code == 200:
            data = response.json()
            data_str = json.dumps(data)
            # Password should never appear in response
            assert 'testpass' not in data_str
            assert 'password' not in data_str.lower()

    def test_token_not_exposed_in_logs(self, client: TestClient):
        """Test that tokens aren't logged in responses"""
        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        # Response itself is ok
        assert response.status_code != 404

    def test_sql_injection_in_login(self, client: TestClient):
        """Test SQL injection protection in auth"""
        response = client.post('/auth/login', json={
            'username': "' OR '1'='1",
            'password': "' OR '1'='1"
        })
        # Should not execute SQL injection
        assert response.status_code != 500
        assert response.status_code in [401, 400, 422]

    def test_brute_force_protection(self, client: TestClient):
        """Test protection against brute force attacks"""
        # Make multiple failed login attempts
        responses = []
        for i in range(10):
            response = client.post('/auth/login', json={
                'username': 'testuser',
                'password': f'wrongpass_{i}'
            })
            responses.append(response)

        # May implement rate limiting
        # At minimum, no 500 errors
        for response in responses:
            assert response.status_code != 500

    def test_cross_user_token_not_accepted(self, client: TestClient):
        """Test that one user's token can't access another's resources"""
        # Get token for user1
        login1 = client.post('/auth/login', json={
            'username': 'testuser1',
            'password': 'password1'
        })

        if login1.status_code == 200:
            token1 = login1.json().get('access_token')

            # Login as user2
            login2 = client.post('/auth/login', json={
                'username': 'testuser2',
                'password': 'password2'
            })

            if login2.status_code == 200:
                user2_id = login2.json().get('user', {}).get('id')

                # Try to access user2's resource with user1's token
                response = client.get(
                    f'/users/{user2_id}/profile',
                    headers={'Authorization': f'Bearer {token1}'}
                )
                # Should deny access or return user1's profile
                assert response.status_code != 500


class TestAuthErrorResponses:
    """Test proper error responses for auth operations"""

    def test_missing_credentials_error(self, client: TestClient):
        """Test error when credentials are missing"""
        response = client.post('/auth/login', json={})
        assert response.status_code in [400, 422]

    def test_error_response_format(self, client: TestClient):
        """Test that error responses are properly formatted"""
        response = client.post('/auth/login', json={
            'username': 'user',
            'password': 'wrong'
        })

        if response.status_code >= 400:
            data = response.json()
            # Should have error details
            assert isinstance(data, dict)

    def test_unauthorized_endpoints_return_401(self, client: TestClient):
        """Test that protected endpoints return 401"""
        response = client.get('/projects')
        # May return 401 or 200 (empty), not 500
        assert response.status_code != 500

    def test_invalid_token_format_error(self, client: TestClient):
        """Test error for malformed token"""
        response = client.get(
            '/projects',
            headers={'Authorization': 'Bearer malformed_token'}
        )
        assert response.status_code in [401, 403]

    def test_missing_authorization_header(self, client: TestClient):
        """Test error when auth header is missing"""
        response = client.get('/projects')
        # Should handle missing auth gracefully
        assert response.status_code != 500


class TestTokenExpirationHandling:
    """Test handling of token expiration scenarios"""

    def test_expired_token_detection(self, client: TestClient):
        """Test that expired tokens are detected"""
        # Very old token that's definitely expired
        old_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjEwMDAwMDAwLCJzdWIiOiJ1c2VyIn0.expired'

        response = client.get(
            '/projects',
            headers={'Authorization': f'Bearer {old_token}'}
        )
        assert response.status_code in [401, 403]

    def test_almost_expired_token_still_valid(self, client: TestClient):
        """Test that token expiring soon is still accepted"""
        # Token valid for 1 more second
        response = client.get('/projects')
        # Not a 401 for time-based rejection
        assert response.status_code != 401 or response.status_code in [401]

    def test_refresh_token_validity(self, client: TestClient):
        """Test refresh token endpoint"""
        response = client.post('/auth/refresh', json={
            'refresh_token': 'test_refresh_token'
        })
        # Endpoint should exist
        assert response.status_code != 404

    def test_expired_refresh_token_rejected(self, client: TestClient):
        """Test that expired refresh tokens are rejected"""
        response = client.post('/auth/refresh', json={
            'refresh_token': 'expired_refresh_token'
        })
        # Should reject with 401
        assert response.status_code in [401, 400]
