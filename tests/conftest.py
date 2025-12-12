"""
Pytest configuration and fixtures for Socrates test suite.

Handles:
- File handle management on Windows
- Common test fixtures
- Mock object configuration
"""

import sys
from unittest.mock import MagicMock

import pytest

# Fix for Windows file handle closure issue with pytest 9.x
# Issue: https://github.com/pytest-dev/pytest/issues/9920
# When running on Windows, pytest closes the capture file prematurely,
# causing "ValueError: I/O operation on closed file" during cleanup.

# Patch pytest.capture.FDCapture methods to handle closed files gracefully
try:
    from _pytest.capture import FDCapture

    _original_snap = FDCapture.snap
    _original_resume = FDCapture.resume

    def _patched_snap(self):
        """Patched snap() that handles already-closed files."""
        try:
            # Try original snap
            return _original_snap(self)
        except ValueError as e:
            if "closed file" in str(e):
                # File is already closed, return empty string
                return ""
            raise

    def _patched_resume(self):
        """Patched resume() that handles already-closed files."""
        try:
            # Try original resume
            return _original_resume(self)
        except ValueError as e:
            if "closed file" in str(e):
                # File is already closed, nothing to resume
                return
            raise

    FDCapture.snap = _patched_snap
    FDCapture.resume = _patched_resume
except Exception:
    # If patching fails, continue without it
    pass


@pytest.fixture(scope="session", autouse=True)
def _fix_file_handles():
    """
    Workaround for pytest file handle closure issue on Windows.

    The issue occurs when pytest tries to close stdout/stderr file handles
    prematurely, causing "ValueError: I/O operation on closed file".

    This fixture prevents that by keeping file handles open.
    """
    # Store original file handles
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    yield

    # Restore original file handles (they should already be open)
    if sys.stdout is None or sys.stdout.closed:
        sys.stdout = original_stdout
    if sys.stderr is None or sys.stderr.closed:
        sys.stderr = original_stderr


# Common fixtures for mocking
@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing."""
    orchestrator = MagicMock()
    orchestrator.event_emitter = MagicMock()
    orchestrator.database = MagicMock()
    orchestrator.claude_client = MagicMock()
    orchestrator.vector_db = MagicMock()
    orchestrator.config = MagicMock()
    orchestrator.config.claude_model = "claude-3-5-sonnet-20241022"
    return orchestrator


@pytest.fixture
def mock_database():
    """Create a mock database for testing."""
    db = MagicMock()
    db.save_project = MagicMock(return_value=True)
    db.load_project = MagicMock(return_value=None)
    db.delete_project = MagicMock(return_value=True)
    db.save_user = MagicMock(return_value=True)
    db.load_user = MagicMock(return_value=None)
    return db


@pytest.fixture
def mock_claude_client():
    """Create a mock Claude client for testing."""
    client = MagicMock()
    client.generate_code = MagicMock(return_value="# Generated code")
    client.extract_insights = MagicMock(return_value={"insights": {}})
    client.generate_socratic_question = MagicMock(return_value="What do you think?")
    return client


@pytest.fixture
def test_config(mock_api_key, tmp_path):
    """Create a test configuration object."""
    from socratic_system.config import SocratesConfig

    config = SocratesConfig(
        api_key=mock_api_key,
        data_dir=tmp_path / "socrates",
    )
    return config


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    import datetime

    from socratic_system.models import ProjectContext

    return ProjectContext(
        project_id="test-proj-123",
        name="Test Project",
        owner="testuser",
        collaborators=[],
        goals="Build a test application",
        requirements=["Requirement 1", "Requirement 2"],
        tech_stack=["Python", "FastAPI"],
        constraints=["Time constraint"],
        team_structure="individual",
        language_preferences="python",
        deployment_target="cloud",
        code_style="documented",
        phase="planning",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    import datetime

    from socratic_system.models import User

    user = User(
        username="testuser",
        passcode_hash="hash123",
        created_at=datetime.datetime.now(),
        projects=["test-proj-123"],
    )
    user.questions_used_this_month = 0
    return user


@pytest.fixture
def mock_api_key():
    """Create a mock API key for testing."""
    return "sk-test-key-12345"


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for testing."""
    return tmp_path


@pytest.fixture
def mock_event_emitter():
    """Create a mock event emitter for testing."""
    from socratic_system.events.event_emitter import EventEmitter

    return EventEmitter()


# Pytest hooks for better error handling
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "unit: mark test as a unit test (no external dependencies)")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow (takes >1 second)")
    config.addinivalue_line("markers", "requires_api: mark test as requiring valid API key")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end")


def pytest_collection_modifyitems(config, items):
    """Modify collected tests to add markers based on naming."""
    for item in items:
        # Add unit marker to tests that don't require external dependencies
        if "test_" in item.nodeid and not any(
            marker in item.nodeid for marker in ["integration", "e2e", "requires_api"]
        ):
            item.add_marker(pytest.mark.unit)
