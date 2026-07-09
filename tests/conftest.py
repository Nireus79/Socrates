"""
pytest configuration for client integration tests

Provides fixtures and configuration for testing LLM clients.
"""

from pathlib import Path

import os
import sys
import tempfile

import pytest

# Set up JWT_SECRET_KEY file for tests
# This ensures JWTHandler.create_access_token() works in module-level code
def _setup_jwt_for_tests():
    """Initialize JWT key file for test environment."""
    test_data_dir = Path(tempfile.gettempdir()) / "socrates_pytest"
    test_data_dir.mkdir(exist_ok=True)
    jwt_key_file = test_data_dir / ".jwt_secret_key"
    if not jwt_key_file.exists():
        jwt_key_file.write_text("test-secret-key-for-pytest-do-not-use-in-production")
    os.environ["SOCRATES_DATA_DIR"] = str(test_data_dir)


_setup_jwt_for_tests()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_db_dir(tmp_path):
    """Create temporary directory for test databases"""
    return tmp_path / "test_db"


@pytest.fixture
def mock_quality_project():
    """Create a properly mocked ProjectContext for QualityController tests"""
    from unittest.mock import MagicMock

    project = MagicMock()
    project.name = "Test Project"
    project.project_id = "proj-123"
    project.phase = "discovery"
    project.project_type = "software"
    project.status = "active"
    project.phase_maturity_scores = {
        "discovery": 75.0,
        "analysis": 70.0,
        "planning": 65.0,
    }
    project.categorized_specs = {
        "discovery": [],
        "analysis": [],
        "planning": [],
    }
    project.category_scores = {}
    project.created_at = "2025-01-01T00:00:00"
    project.notes = []

    return project


@pytest.fixture(autouse=True)
def cleanup_mocks():
    """Cleanup after each test"""
    yield
    # Reset any global state if needed


# Configure pytest
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async (deselect with '-m \"not asyncio\"')"
    )
    config.addinivalue_line("markers", "slow: mark test as slow (deselect with '-m \"not slow\"')")


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        if "asyncio" in item.nodeid:
            item.add_marker(pytest.mark.asyncio)
