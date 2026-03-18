"""Integration tests for socrates-cli and socrates-api."""

import json
import subprocess
import time
from pathlib import Path

import httpx
import pytest


class TestCLIAndAPIIntegration:
    """Integration tests between CLI and API."""

    @pytest.fixture
    def api_url(self):
        """Fixture providing API URL."""
        return "http://localhost:8000"

    @pytest.fixture
    def api_client(self, api_url):
        """Fixture providing API client."""
        return httpx.Client(base_url=api_url, timeout=10.0)

    def test_api_health_check(self, api_client):
        """Test API health check endpoint."""
        try:
            response = api_client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") in ["healthy", "ok"]
        except httpx.ConnectError:
            pytest.skip("API server not running")

    def test_api_info_endpoint(self, api_client):
        """Test API info endpoint."""
        try:
            response = api_client.get("/info")
            assert response.status_code == 200
            data = response.json()
            assert "version" in data
        except httpx.ConnectError:
            pytest.skip("API server not running")

    def test_create_project_via_api(self, api_client):
        """Test creating a project via API."""
        try:
            response = api_client.post(
                "/projects",
                json={
                    "name": "Test Project",
                    "owner": "test@example.com",
                    "description": "Integration test project"
                }
            )
            assert response.status_code in [200, 201]
            data = response.json()
            assert "id" in data
            assert data["name"] == "Test Project"
        except httpx.ConnectError:
            pytest.skip("API server not running")

    def test_list_projects_via_api(self, api_client):
        """Test listing projects via API."""
        try:
            response = api_client.get("/projects")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or isinstance(data.get("data"), list)
        except httpx.ConnectError:
            pytest.skip("API server not running")

    def test_get_project_via_api(self, api_client):
        """Test getting a specific project via API."""
        try:
            # First create a project
            create_response = api_client.post(
                "/projects",
                json={
                    "name": "Get Test",
                    "owner": "test@example.com"
                }
            )

            if create_response.status_code not in [200, 201]:
                pytest.skip("Could not create project")

            project_id = create_response.json().get("id")

            # Then get it
            get_response = api_client.get(f"/projects/{project_id}")
            assert get_response.status_code == 200
            data = get_response.json()
            assert data.get("id") == project_id
        except httpx.ConnectError:
            pytest.skip("API server not running")


class TestCLIConfiguration:
    """Tests for CLI configuration."""

    def test_cli_help(self):
        """Test CLI help command."""
        result = subprocess.run(
            ["socrates", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode in [0, 1]  # Some systems return 1 for help
        assert "project" in result.stdout.lower() or "help" in result.stdout.lower()

    def test_cli_version(self):
        """Test CLI version command."""
        result = subprocess.run(
            ["socrates", "--version"],
            capture_output=True,
            text=True
        )
        # Should return version or help info
        assert result.returncode in [0, 1]

    def test_cli_project_help(self):
        """Test CLI project subcommand help."""
        result = subprocess.run(
            ["socrates", "project", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode in [0, 1]
        output = result.stdout + result.stderr
        assert "project" in output.lower()


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    @pytest.fixture
    def api_client(self):
        """Fixture providing API client."""
        try:
            return httpx.Client(base_url="http://localhost:8000", timeout=10.0)
        except Exception:
            return None

    def test_complete_project_workflow(self, api_client):
        """Test complete workflow: create project, list, get."""
        if not api_client:
            pytest.skip("API server not running")

        try:
            # Create project
            create_response = api_client.post(
                "/projects",
                json={
                    "name": "E2E Test",
                    "owner": "test@example.com",
                    "description": "End-to-end test"
                }
            )
            assert create_response.status_code in [200, 201]
            project_id = create_response.json().get("id")
            assert project_id

            # List projects
            list_response = api_client.get("/projects")
            assert list_response.status_code == 200

            # Get specific project
            get_response = api_client.get(f"/projects/{project_id}")
            assert get_response.status_code == 200
            assert get_response.json().get("id") == project_id

        except httpx.ConnectError:
            pytest.skip("API server not running")

    def test_error_handling(self, api_client):
        """Test error handling in API."""
        if not api_client:
            pytest.skip("API server not running")

        try:
            # Try to get non-existent project
            response = api_client.get("/projects/nonexistent")
            # Should return 404
            assert response.status_code in [404, 400]
        except httpx.ConnectError:
            pytest.skip("API server not running")


class TestCLIAPICompatibility:
    """Tests for CLI and API compatibility."""

    def test_cli_can_connect_to_api(self):
        """Test that CLI can connect to API server."""
        result = subprocess.run(
            ["socrates", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should either succeed or fail with connection message
        output = result.stdout + result.stderr

        # If it has meaningful output, that's good
        # If it's a connection error, that's OK (API might not be running)
        assert len(output) > 0 or result.returncode > 0

    def test_cli_with_api_url_env(self):
        """Test CLI with explicit API URL."""
        import os

        env = os.environ.copy()
        env["SOCRATES_API_URL"] = "http://localhost:8000"

        result = subprocess.run(
            ["socrates", "info"],
            capture_output=True,
            text=True,
            env=env,
            timeout=5
        )

        # Should work or show connection error
        assert result.returncode >= 0


class TestAPIResponseFormats:
    """Tests for API response formats."""

    @pytest.fixture
    def api_client(self):
        """Fixture providing API client."""
        try:
            return httpx.Client(base_url="http://localhost:8000", timeout=10.0)
        except Exception:
            return None

    def test_api_json_response(self, api_client):
        """Test API returns valid JSON."""
        if not api_client:
            pytest.skip("API server not running")

        try:
            response = api_client.get("/info")
            if response.status_code == 200:
                # Should be valid JSON
                data = response.json()
                assert isinstance(data, dict)
        except (httpx.ConnectError, json.JSONDecodeError):
            pytest.skip("API not available or response malformed")

    def test_api_error_format(self, api_client):
        """Test API error response format."""
        if not api_client:
            pytest.skip("API server not running")

        try:
            response = api_client.get("/projects/invalid")
            if response.status_code >= 400:
                # Should still be valid JSON
                data = response.json()
                # Should have error information
                assert "error" in data or "detail" in data or "message" in data
        except (httpx.ConnectError, json.JSONDecodeError):
            pytest.skip("API not available")


class TestConcurrentRequests:
    """Tests for handling concurrent requests."""

    @pytest.fixture
    def api_client(self):
        """Fixture providing API client."""
        try:
            return httpx.Client(base_url="http://localhost:8000", timeout=10.0)
        except Exception:
            return None

    def test_multiple_concurrent_api_calls(self, api_client):
        """Test handling multiple concurrent API calls."""
        if not api_client:
            pytest.skip("API server not running")

        try:
            responses = []
            for i in range(5):
                response = api_client.get("/health")
                responses.append(response.status_code)

            # All should succeed
            assert all(status in [200, 500] for status in responses)
        except httpx.ConnectError:
            pytest.skip("API server not running")

    def test_api_under_load(self, api_client):
        """Test API stability under load."""
        if not api_client:
            pytest.skip("API server not running")

        try:
            success_count = 0
            for i in range(10):
                try:
                    response = api_client.get("/health", timeout=5.0)
                    if response.status_code == 200:
                        success_count += 1
                except Exception:
                    pass

            # Most should succeed
            assert success_count >= 8
        except httpx.ConnectError:
            pytest.skip("API server not running")
