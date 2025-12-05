"""
Pytest configuration and shared fixtures for Socrates test suite
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Handle module alias: socratic_system -> socrates
try:
    import socrates
except ModuleNotFoundError:
    import socratic_system as socrates

    sys.modules["socrates"] = socrates


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for tests"""
    return "sk-ant-test-key-12345"


@pytest.fixture
def test_config(temp_data_dir, mock_api_key):
    """Create a test configuration"""
    return socrates.SocratesConfig(
        api_key=mock_api_key,
        data_dir=temp_data_dir,
        claude_model="claude-opus-4-5-20251101",
        embedding_model="all-MiniLM-L6-v2",
        log_level="DEBUG",
    )


@pytest.fixture
def config_builder(mock_api_key):
    """Create a config builder for testing"""
    return socrates.ConfigBuilder(mock_api_key)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test response")]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_event_emitter():
    """Create a mock event emitter"""
    return socrates.EventEmitter()


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    import datetime

    from socratic_system.models import User

    return User(
        username="testuser",
        passcode_hash="hashed_password",
        created_at=datetime.datetime.now(),
        is_archived=False,
        archived_at=None,
    )


@pytest.fixture
def sample_project():
    """Create a sample project for testing"""
    import datetime

    from socratic_system.models import ProjectContext

    return ProjectContext(
        project_id="test_proj_001",
        name="Test Project",
        owner="testuser",
        description="A test project",
        phase="active",
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        is_archived=False,
        archived_at=None,
        collaborators=[],
        notes=[],
    )


@pytest.fixture
def sample_knowledge_entry():
    """Create a sample knowledge entry for testing"""
    from socratic_system.models import KnowledgeEntry

    return KnowledgeEntry(
        id="test_knowledge_001",
        content="Test knowledge content about REST APIs",
        category="api_design",
        metadata={"source": "test", "difficulty": "beginner"},
    )


@pytest.fixture
def sample_token_usage():
    """Create a sample token usage for testing"""
    import datetime

    from socratic_system.models import TokenUsage

    return TokenUsage(
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        model="claude-opus-4-5-20251101",
        timestamp=datetime.datetime.now(),
    )


# Parametrize common test values
@pytest.fixture(params=["DEBUG", "INFO", "WARNING", "ERROR"])
def log_levels(request):
    """Parametrized log levels"""
    return request.param


@pytest.fixture(params=["python", "javascript", "typescript", "go", "rust"])
def programming_languages(request):
    """Parametrized programming languages"""
    return request.param


@pytest.fixture(params=["beginner", "intermediate", "advanced"])
def difficulty_levels(request):
    """Parametrized difficulty levels"""
    return request.param


# Markers for different test types
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "requires_api: mark test as requiring API key")


# Skip tests if API key not available
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip tests that require API key"""
    skip_requires_api = pytest.mark.skip(reason="ANTHROPIC_API_KEY not set")

    api_key = os.getenv("ANTHROPIC_API_KEY")

    for item in items:
        if "requires_api" in item.keywords and not api_key:
            item.add_marker(skip_requires_api)
