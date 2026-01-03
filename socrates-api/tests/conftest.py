"""Pytest configuration and fixtures for Socrates API tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import socratic_system

# Add main project to path
main_project_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(main_project_path))

# Create alias for socratic_system
sys.modules['socrates'] = socratic_system


@pytest.fixture
def test_db(tmp_path):
    """
    Fixture to provide an isolated test database.

    Uses a temporary directory to avoid affecting production data.
    Each test gets its own isolated database.
    """
    from socratic_system.database import ProjectDatabase

    # Use temporary directory for test database (not home directory!)
    test_db_path = tmp_path / "test_projects.db"
    db = ProjectDatabase(str(test_db_path))

    yield db

    # Cleanup is automatic - tmp_path is deleted after test


@pytest.fixture
def test_db_inmemory():
    """
    Fixture for ultra-fast tests that don't need persistence.

    Uses SQLite in-memory database - no disk I/O.
    """
    from socratic_system.database import ProjectDatabase
    db = ProjectDatabase(":memory:")
    return db


@pytest.fixture
def app():
    """Fixture to provide FastAPI app instance."""
    try:
        from socrates_api.main import app
        return app
    except ImportError:
        pytest.skip("FastAPI or socrates_api not available")


@pytest.fixture
def client(app):
    """Fixture to provide FastAPI TestClient for API tests."""
    try:
        from fastapi.testclient import TestClient
        return TestClient(app)
    except ImportError:
        pytest.skip("FastAPI or socrates_api not available")


@pytest.fixture
def mock_auth():
    """Fixture to provide mock authentication token."""
    return {
        'access_token': 'test_token_xyz',
        'refresh_token': 'test_refresh_token_xyz',
        'user': {
            'id': 'test_user_id',
            'username': 'testuser',
            'email': 'test@example.com'
        }
    }


@pytest.fixture
def auth_headers(mock_auth):
    """Fixture to provide authorization headers."""
    return {'Authorization': f"Bearer {mock_auth['access_token']}"}


@pytest.fixture
def mock_database(monkeypatch):
    """Fixture to provide mock database for testing."""
    mock_db = MagicMock()
    mock_db.create_user = MagicMock(return_value=True)
    mock_db.get_user = MagicMock(return_value={'id': 'user_1', 'username': 'testuser'})
    mock_db.create_project = MagicMock(return_value={'id': 'proj_1', 'name': 'Test'})
    mock_db.get_projects = MagicMock(return_value=[])
    return mock_db


@pytest.fixture
def mock_vector_db(monkeypatch):
    """Fixture to provide mock vector database."""
    mock_vdb = MagicMock()
    mock_vdb.add_document = MagicMock(return_value='doc_1')
    mock_vdb.search = MagicMock(return_value=[])
    mock_vdb.close = MagicMock()
    return mock_vdb


@pytest.fixture
def test_vector_db(tmp_path):
    """
    Fixture to provide an isolated test vector database.

    Uses a temporary directory to avoid affecting production data.
    Each test gets its own isolated vector database.
    """
    from socratic_system.database.vector_db import VectorDatabase

    # Use temporary directory for test vector database (not home directory!)
    test_vector_db_path = tmp_path / "test_vector_db"
    vector_db = VectorDatabase(str(test_vector_db_path))

    yield vector_db

    # Cleanup is automatic - tmp_path is deleted after test
    # Vector database will be cleaned up automatically


@pytest.fixture
def test_socrates_config(tmp_path):
    """
    Fixture to provide isolated test configuration.

    Both projects.db and vector_db will be created in temp directory,
    never touching production data in ~/.socrates/
    """
    from socratic_system.config import SocratesConfig

    return SocratesConfig(
        api_key="sk-test-key-12345",
        data_dir=tmp_path / "socrates",  # Isolated temp directory
    )


@pytest.fixture(autouse=True)
def reset_imports():
    """Reset imports between tests to avoid state leakage."""
    yield
    # Cleanup after each test


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "security: mark test as a security test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test path."""
    for item in items:
        # Add markers based on file location
        if "test_e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "test_security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif "test_auth" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_database():
    """
    Test isolation fixture - do NOT modify production databases!

    CRITICAL: This fixture used to delete ~/.socrates/projects.db which
    caused user data loss. That code has been removed.

    Tests should ONLY use temporary directories via pytest tmp_path fixture,
    never touch the home directory or production data.

    See: https://github.com/your-org/socrates/issues/XXX
    """
    # Don't touch production database in ~/.socrates/
    # Tests must use isolated temporary directories only
    yield
    # No cleanup of home directory - tests should clean up their own temp files
