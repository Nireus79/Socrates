"""
Pytest configuration for integration tests.

Note: Integration tests use mocks instead of requiring a live API server.
This allows tests to run in CI/CD environments without external dependencies.
"""

import pytest
