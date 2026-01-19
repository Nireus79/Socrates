"""
Pytest configuration for integration tests.

Integration tests use real HTTP calls to a live API server and are excluded
from CI/CD runs with -m "not integration" because CI/CD environments don't
have a running API server. These tests are designed for local testing only.
"""

import pytest
import socket


@pytest.fixture(scope="session", autouse=True)
def skip_integration_if_no_api_server():
    """Skip all integration tests if API server is not running."""
    def check_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            return result == 0
        except Exception:
            return False

    # Check if API server is available on port 8000
    if not check_port(8000):
        pytest.skip(
            "Integration API server (localhost:8000) is not running. "
            "Integration tests are local-only and require manual API server startup.",
            allow_module_level=True
        )
