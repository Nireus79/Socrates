"""
Pytest configuration for E2E tests.

Provides fixtures for end-to-end testing of system workflows.
"""

import pytest
from unittest.mock import MagicMock
from socratic_system.models import User, ProjectContext


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for E2E testing."""
    orchestrator = MagicMock()

    # Setup agent bus
    orchestrator.agent_bus = MagicMock()
    orchestrator.agent_registry = MagicMock()

    # Setup database
    orchestrator.database = MagicMock()
    orchestrator.database.save_project = MagicMock(return_value=True)
    orchestrator.database.load_project = MagicMock()
    orchestrator.database.load_user = MagicMock()

    # Setup Claude client
    orchestrator.claude_client = MagicMock()
    orchestrator.claude_client.generate_code = MagicMock(return_value="# Generated code")
    orchestrator.claude_client.generate_artifact = MagicMock(return_value="# Artifact")

    # Setup event emitter
    orchestrator.event_emitter = MagicMock()
    orchestrator.event_emitter.on = MagicMock()
    orchestrator.event_emitter.emit = MagicMock()

    return orchestrator


@pytest.fixture
def sample_user():
    """Create a sample user for E2E testing."""
    user = MagicMock(spec=User)
    user.username = "test_user"
    user.email = "test@example.com"
    user.user_id = "user_123"
    user.subscription_tier = "free"
    user.max_projects = 3
    return user


@pytest.fixture
def pro_user():
    """Create a pro tier user for E2E testing."""
    user = MagicMock(spec=User)
    user.username = "pro_user"
    user.email = "pro@example.com"
    user.user_id = "user_pro_123"
    user.subscription_tier = "pro"
    user.max_projects = 50
    user.can_collaborate = True
    return user


@pytest.fixture
def sample_project():
    """Create a sample project for E2E testing."""
    project = MagicMock(spec=ProjectContext)
    project.project_id = "proj_123"
    project.name = "Test Project"
    project.owner = "test_user"
    project.goals = "Test goals"
    project.tech_stack = ["Python", "FastAPI"]
    project.requirements = ["Requirement 1", "Requirement 2"]
    project.constraints = ["Constraint 1"]
    project.deployment_target = "Docker"
    project.collaborators = []

    # Additional attributes that agents may access
    project.phase = "planning"
    project.status = "active"
    project.created_at = "2025-01-01T00:00:00"
    project.updated_at = "2025-01-02T00:00:00"
    project.description = "Test project description"
    project.architecture = None
    project.notes = []

    return project


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for E2E testing."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir(exist_ok=True)

    # Create sample files for document processing tests
    pdf_file = data_dir / "design_doc.pdf"
    pdf_file.write_text("Sample PDF content for testing")

    return data_dir
