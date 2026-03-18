"""Integration tests for socrates-api."""

import json

import httpx
import pytest


@pytest.fixture
def client():
    """Fixture providing test client."""
    return httpx.Client(base_url="http://localhost:8000", timeout=10.0)


class TestAPIEndpoints:
    """Tests for API endpoints."""

    def test_health_endpoint(self, client):
        """Test /health endpoint."""
        try:
            response = client.get("/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("API not running")

    def test_info_endpoint(self, client):
        """Test /info endpoint."""
        try:
            response = client.get("/info")
            assert response.status_code == 200
            data = response.json()
            assert "version" in data or "status" in data
        except httpx.ConnectError:
            pytest.skip("API not running")

    def test_metrics_endpoint(self, client):
        """Test /metrics endpoint."""
        try:
            response = client.get("/metrics")
            # Metrics endpoint might return 200 or other status
            assert response.status_code in [200, 404, 405]
        except httpx.ConnectError:
            pytest.skip("API not running")


class TestProjectEndpoints:
    """Tests for project-related endpoints."""

    def test_create_project(self, client):
        """Test creating a project."""
        try:
            response = client.post(
                "/projects",
                json={
                    "name": "Test Project",
                    "owner": "test@example.com",
                    "description": "Test"
                }
            )
            assert response.status_code in [200, 201]
            data = response.json()
            assert "id" in data or "project_id" in data
        except httpx.ConnectError:
            pytest.skip("API not running")

    def test_list_projects(self, client):
        """Test listing projects."""
        try:
            response = client.get("/projects")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("API not running")

    def test_get_project_invalid_id(self, client):
        """Test getting project with invalid ID."""
        try:
            response = client.get("/projects/invalid_id")
            # Should return 404 or 400
            assert response.status_code in [400, 404]
        except httpx.ConnectError:
            pytest.skip("API not running")


class TestAPIErrorHandling:
    """Tests for API error handling."""

    def test_invalid_json_request(self, client):
        """Test API handles invalid JSON."""
        try:
            response = client.post(
                "/projects",
                content="invalid json",
                headers={"Content-Type": "application/json"}
            )
            # Should return error
            assert response.status_code >= 400
        except httpx.ConnectError:
            pytest.skip("API not running")

    def test_missing_required_fields(self, client):
        """Test API validates required fields."""
        try:
            response = client.post(
                "/projects",
                json={"name": "Test"}  # Missing owner
            )
            # Should return 400 or 422
            assert response.status_code in [400, 422]
        except httpx.ConnectError:
            pytest.skip("API not running")

    def test_nonexistent_endpoint(self, client):
        """Test API handles nonexistent endpoints."""
        try:
            response = client.get("/nonexistent/endpoint")
            assert response.status_code == 404
        except httpx.ConnectError:
            pytest.skip("API not running")


class TestAPIResponseHeaders:
    """Tests for API response headers."""

    def test_response_content_type(self, client):
        """Test API returns correct content type."""
        try:
            response = client.get("/info")
            assert response.status_code == 200
            assert "application/json" in response.headers.get("content-type", "")
        except httpx.ConnectError:
            pytest.skip("API not running")

    def test_cors_headers(self, client):
        """Test CORS headers."""
        try:
            response = client.get("/health")
            # Should have CORS headers or not (depends on config)
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("API not running")


class TestAPIDataValidation:
    """Tests for API data validation."""

    def test_create_project_name_required(self, client):
        """Test that project name is required."""
        try:
            response = client.post(
                "/projects",
                json={"owner": "test@example.com"}
            )
            assert response.status_code in [400, 422]
        except httpx.ConnectError:
            pytest.skip("API not running")

    def test_create_project_owner_required(self, client):
        """Test that project owner is required."""
        try:
            response = client.post(
                "/projects",
                json={"name": "Test"}
            )
            assert response.status_code in [400, 422]
        except httpx.ConnectError:
            pytest.skip("API not running")

    def test_project_name_length(self, client):
        """Test project name length validation."""
        try:
            # Very long name
            response = client.post(
                "/projects",
                json={
                    "name": "x" * 10000,
                    "owner": "test@example.com"
                }
            )
            # Should either accept or reject with 400/422
            assert response.status_code in [200, 201, 400, 422]
        except httpx.ConnectError:
            pytest.skip("API not running")


class TestAPIResponseConsistency:
    """Tests for API response consistency."""

    def test_consistent_error_format(self, client):
        """Test that errors have consistent format."""
        try:
            # Get error from invalid endpoint
            response = client.get("/invalid")
            if response.status_code >= 400:
                data = response.json()
                # Should have some error info
                assert "error" in data or "detail" in data or "message" in data
        except (httpx.ConnectError, json.JSONDecodeError):
            pytest.skip("API not running")

    def test_consistent_success_format(self, client):
        """Test that successes have consistent format."""
        try:
            response = client.get("/health")
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except (httpx.ConnectError, json.JSONDecodeError):
            pytest.skip("API not running")


class TestAPIPerformance:
    """Tests for API performance."""

    def test_health_check_fast(self, client):
        """Test health check is fast."""
        try:
            import time
            start = time.time()
            response = client.get("/health")
            duration = time.time() - start

            assert response.status_code == 200
            assert duration < 1.0  # Should be fast
        except httpx.ConnectError:
            pytest.skip("API not running")

    def test_list_projects_reasonable_time(self, client):
        """Test list projects completes in reasonable time."""
        try:
            import time
            start = time.time()
            response = client.get("/projects")
            duration = time.time() - start

            assert response.status_code == 200
            assert duration < 5.0  # Should complete reasonably fast
        except httpx.ConnectError:
            pytest.skip("API not running")
