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
def test_db(monkeypatch):
    """Fixture to provide a test database."""
    from socratic_system.database import ProjectDatabase
    # Use in-memory database for tests
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
    """Clean up test database files before and after tests."""
    from pathlib import Path

    # Clean up test database before tests
    test_data_dir = Path.home() / ".socrates"
    if test_data_dir.exists():
        try:
            db_file = test_data_dir / "projects.db"
            if db_file.exists():
                db_file.unlink()
        except Exception:
            pass

    yield

    # Clean up after tests
    try:
        db_file = test_data_dir / "projects.db"
        if db_file.exists():
            db_file.unlink()
    except Exception:
        pass
