"""
pytest configuration for client integration tests

Provides fixtures and configuration for testing LLM clients.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_db_dir(tmp_path):
    """Create temporary directory for test databases"""
    return tmp_path / "test_db"


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
