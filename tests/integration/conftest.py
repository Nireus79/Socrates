"""
Pytest configuration for integration tests.

Integration tests use real HTTP calls to a live API server and are excluded
from CI/CD runs with -m "not integration" because CI/CD environments don't
have a running API server. These tests are designed for local testing only.
"""
