"""Pytest configuration and fixtures for integration tests."""

import pytest
from socrates_api.auth.jwt_handler import create_access_token


@pytest.fixture
def valid_token():
    """Create a valid JWT token for testing."""
    return create_access_token("testuser")


@pytest.fixture
def auth_headers(valid_token):
    """Fixture to provide authorization headers with valid token."""
    return {"Authorization": f"Bearer {valid_token}"}
