"""Quick API connectivity test

Tests basic API endpoints to verify the server is running and responding correctly.
This test assumes the API server is already running on localhost:8000.
"""

import pytest
import requests
from typing import Tuple

# Base URL for API server
API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 5


@pytest.fixture(scope="module")
def api_available() -> bool:
    """Check if API server is available."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


class TestAPIQuickCheck:
    """Quick smoke tests for API endpoints."""

    def test_api_root_endpoint(self):
        """Test root endpoint returns 200."""
        response = requests.get(f"{API_BASE_URL}/", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200, f"Root endpoint failed: {response.status_code}"
        data = response.json()
        assert "message" in data
        assert data["message"] == "Socrates API"

    def test_api_health_endpoint(self):
        """Test health endpoint returns 200."""
        response = requests.get(f"{API_BASE_URL}/health", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200, f"Health endpoint failed: {response.status_code}"
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]

    def test_api_csrf_token_endpoint(self):
        """Test CSRF token endpoint returns 200."""
        response = requests.get(f"{API_BASE_URL}/auth/csrf-token", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200, f"CSRF endpoint failed: {response.status_code}"
        data = response.json()
        assert "data" in data
        assert "csrf_token" in data["data"]

    def test_api_projects_endpoint_unauthorized(self):
        """Test projects endpoint returns 401 without token."""
        response = requests.get(f"{API_BASE_URL}/projects", timeout=REQUEST_TIMEOUT)
        # Should be 401 Unauthorized without auth token
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    @pytest.mark.parametrize("path,description", [
        ("/", "root endpoint"),
        ("/health", "health check"),
        ("/auth/csrf-token", "CSRF token"),
        ("/projects", "projects list"),
    ])
    def test_endpoints_respond(self, path: str, description: str):
        """Test that all endpoints respond (with any status code except 404/503)."""
        response = requests.get(f"{API_BASE_URL}{path}", timeout=REQUEST_TIMEOUT)
        # Should not return 404 (not found) or 503 (service unavailable)
        assert response.status_code not in [404, 503], \
            f"{description} returned {response.status_code}"


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    def test_invalid_endpoint_returns_404(self):
        """Test that invalid endpoints return 404."""
        response = requests.get(
            f"{API_BASE_URL}/this/endpoint/does/not/exist",
            timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 404, \
            f"Expected 404 for invalid endpoint, got {response.status_code}"

    def test_projects_requires_authentication(self):
        """Test that /projects endpoint requires authentication."""
        response = requests.get(f"{API_BASE_URL}/projects", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 401, \
            f"Expected 401 for /projects without token, got {response.status_code}"


# Standalone execution for quick testing without pytest
if __name__ == "__main__":
    import sys

    print("\n=== Quick API Smoke Tests ===\n")

    endpoints = [
        ("/", "Root"),
        ("/health", "Health"),
        ("/auth/csrf-token", "CSRF Token"),
        ("/projects", "Projects"),
    ]

    passed = 0
    failed = 0

    for path, desc in endpoints:
        try:
            r = requests.get(f"{API_BASE_URL}{path}", timeout=REQUEST_TIMEOUT)
            status = "PASS" if r.status_code != 503 else "FAIL"
            print(f"[{status}] {desc:20} {path:30} -> {r.status_code}")
            if status == "PASS":
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] {desc:20} {path:30} -> ERROR: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
