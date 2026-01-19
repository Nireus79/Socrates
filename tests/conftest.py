"""
Pytest configuration and fixtures for Socrates test suite.

Handles:
- File handle management on Windows
- Common test fixtures
- Mock object configuration
"""

import builtins
import sys
from unittest.mock import MagicMock

import pytest

# Check if running in PyCharm (IDE) or other test runners
# PyCharm sets PYCHARM_MATPLOTLIB_INTERACTIVE or has specific pytest mode indicators
_is_pycharm = (
    "PYCHARM_MATPLOTLIB_INTERACTIVE" in sys.modules or "PYCHARM_PYPLOT_INTERACTIVE" in sys.modules
)
_is_ide = sys.stdout.__class__.__name__ == "PyCharmOutput" or hasattr(sys.stdout, "_stream")

# Only apply patches when NOT running in PyCharm IDE
if not (_is_pycharm or _is_ide):
    # Fix for Windows file handle closure issue with pytest 9.x
    # Issue: https://github.com/pytest-dev/pytest/issues/9920
    # When running on Windows, pytest closes the capture file prematurely,
    # causing "ValueError: I/O operation on closed file" during cleanup.

    # Patch builtins.print to handle closed file errors gracefully
    _original_print = builtins.print

    def _patched_print(*args, **kwargs):
        """Patched print() that handles closed file errors gracefully."""
        try:
            return _original_print(*args, **kwargs)
        except ValueError as e:
            if "closed file" in str(e) or "I/O operation on closed file" in str(e):
                # File is closed, skip printing (likely in test cleanup or when stdout was redirected)
                # Don't raise an error - just skip printing silently
                return
            # If it's a different ValueError, re-raise it
            raise
        except Exception:
            # For any other exception, let it propagate
            raise

    builtins.print = _patched_print

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
    client.generate_response = MagicMock(return_value="Mock response from Claude")
    return client


@pytest.fixture
def test_config(mock_api_key, tmp_path):
    """
    Create an isolated test configuration object.

    This creates a temporary data directory for both:
    - projects.db (SQLite database)
    - vector_db (ChromaDB vector store)

    Never touches production data in ~/.socrates/
    """
    from socratic_system.config import SocratesConfig

    config = SocratesConfig(
        api_key=mock_api_key,
        data_dir=tmp_path / "socrates",  # Isolated temp directory
    )
    return config


@pytest.fixture
def isolated_socrates_config(mock_api_key, tmp_path):
    """
    Create an isolated test configuration with explicit database paths.

    Ensures both projects.db and vector_db are in temp directory,
    completely isolated from production.
    """
    from socratic_system.config import SocratesConfig

    test_data_dir = tmp_path / "socrates"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    config = SocratesConfig(
        api_key=mock_api_key,
        data_dir=test_data_dir,
        projects_db_path=test_data_dir / "projects.db",
        vector_db_path=test_data_dir / "vector_db",
    )
    return config


@pytest.fixture
def sample_project():
    """Create a sample free tier project for testing solo features."""
    import datetime

    from socratic_system.models import ProjectContext

    return ProjectContext(
        project_id="test_proj_001",
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
def pro_project():
    """Create a sample pro tier project for testing team collaboration."""
    import datetime

    from socratic_system.models import ProjectContext

    return ProjectContext(
        project_id="pro_proj_001",
        name="Pro Project",
        owner="prouser",
        collaborators=[],
        goals="Build a collaborative application",
        requirements=["Multi-user support", "Team features"],
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
        constraints=["Performance", "Scalability"],
        team_structure="team",
        language_preferences="python",
        deployment_target="cloud",
        code_style="documented",
        phase="design",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )


@pytest.fixture
def sample_user():
    """Create a sample free tier user for testing."""
    import datetime

    from socratic_system.models import User

    user = User(
        username="testuser",
        email="testuser@example.com",
        passcode_hash="hash123",
        created_at=datetime.datetime.now(),
        projects=["test-proj-123"],
        subscription_tier="free",
    )
    user.questions_used_this_month = 0
    return user


@pytest.fixture
def pro_user():
    """Create a sample pro tier user for testing team collaboration features."""
    import datetime

    from socratic_system.models import User

    user = User(
        username="prouser",
        email="prouser@example.com",
        passcode_hash="hash123",
        created_at=datetime.datetime.now(),
        projects=["pro-proj-001"],
        subscription_tier="pro",
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


@pytest.fixture
def sample_knowledge_entry():
    """Create a sample knowledge entry for testing."""
    from socratic_system.models import KnowledgeEntry

    return KnowledgeEntry(
        id="test_knowledge_001",
        content="REST API design best practices and patterns for building scalable services",
        category="api_design",
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        metadata={"source": "documentation", "difficulty": "intermediate", "tags": ["REST", "API"]},
    )


@pytest.fixture
def sample_token_usage():
    """Create a sample token usage record for testing."""
    import datetime

    from socratic_system.models import TokenUsage

    return TokenUsage(
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        model="claude-opus-4-5-20251101",
        timestamp=datetime.datetime.now(),
        cost_estimate=0.001,
    )


# Pytest hooks for better error handling
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "unit: mark test as a unit test (no external dependencies)")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow (takes >1 second)")
    config.addinivalue_line("markers", "requires_api: mark test as requiring valid API key")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end")
    config.addinivalue_line(
        "markers",
        "test_isolation: mark test as potentially failing due to test ordering/isolation issues",
    )


def pytest_collection_modifyitems(config, items):
    """Modify collected tests to add markers and skip unavailable tests."""
    import socket

    # Check if API servers are available once at the start
    def check_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            return result == 0
        except Exception:
            return False

    api_8008_available = check_port(8008)
    api_8000_available = check_port(8000)

    for item in items:
        # Add unit marker to tests that don't require external dependencies
        if "test_" in item.nodeid and not any(
            marker in item.nodeid for marker in ["integration", "e2e", "requires_api"]
        ):
            item.add_marker(pytest.mark.unit)

        # Add integration marker to tests in the integration directory if not already marked
        if "tests/integration/" in item.nodeid and not any(
            marker.name == "integration" for marker in item.iter_markers()
        ):
            item.add_marker(pytest.mark.integration)

        # Skip e2e API tests if server not available (prevents 4+ second timeouts on port 8008)
        if not api_8008_available and "test_api_workflows" in str(item.fspath):
            item.add_marker(
                pytest.mark.skip(
                    reason="E2E API server (localhost:8008) is not running. "
                    "Start the API server to run these tests."
                )
            )

        # Skip integration tests if API server not available (prevents connection errors on port 8000)
        if not api_8000_available and "tests/integration/" in str(item.fspath):
            item.add_marker(
                pytest.mark.skip(
                    reason="Integration API server (localhost:8000) is not running. "
                    "Start the API server to run integration tests."
                )
            )


@pytest.fixture(autouse=True)
def protect_production_environment(monkeypatch):
    """
    Protect production environment from test pollution.

    Ensures tests never modify SOCRATES_DATA_DIR or other critical
    environment variables that would affect production.
    """
    import os

    # Save original environment variables
    original_socrates_data_dir = os.environ.get("SOCRATES_DATA_DIR")

    # Unset any test-modified environment variables
    if "SOCRATES_DATA_DIR" in os.environ:
        monkeypatch.delenv("SOCRATES_DATA_DIR")

    yield

    # Restore original environment (monkeypatch automatically reverts)


@pytest.fixture(scope="session", autouse=True)
def cleanup_embedding_models():
    """
    Session-level fixture to clean up embedding models.

    This helps prevent file handle issues with SentenceTransformer models
    when running large test suites that create multiple VectorDatabase instances.
    """
    import gc

    yield

    # After all tests complete, force garbage collection to release
    # any remaining file handles or resources held by embedding models
    gc.collect()


@pytest.fixture(scope="session")
def api_server_available():
    """
    Check if API server is available at localhost:8008.

    Returns True if server responds, False otherwise.
    """
    import socket

    # Quick check without making a full request - just check TCP connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)  # 1 second timeout
        result = sock.connect_ex(("localhost", 8008))
        sock.close()
        return result == 0
    except Exception:
        return False
