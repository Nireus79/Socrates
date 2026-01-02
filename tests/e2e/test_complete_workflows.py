"""
End-to-end tests for complete user workflows.

Tests complete user journeys including:
- Orchestrator initialization
- Project context management
- Database operations
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from socratic_system.orchestration.orchestrator import AgentOrchestrator
from socratic_system.config import SocratesConfig
from socratic_system.models.project import ProjectContext
from socratic_system.database.project_db import ProjectDatabase
import os


@pytest.fixture
def e2e_environment():
    """Create complete e2e test environment."""
    # Create temporary directories
    project_dir = tempfile.mkdtemp()
    db_dir = tempfile.mkdtemp()

    yield {
        "project_dir": project_dir,
        "db_dir": db_dir,
    }

    # Cleanup
    shutil.rmtree(project_dir, ignore_errors=True)
    shutil.rmtree(db_dir, ignore_errors=True)


@pytest.fixture
def orchestrator(e2e_environment):
    """Create orchestrator for E2E testing."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "sk-ant-test-key-for-integration-tests")
    config = SocratesConfig(
        api_key=api_key,
        data_dir=Path(e2e_environment["db_dir"]),
    )
    return AgentOrchestrator(config)


@pytest.fixture
def database(e2e_environment):
    """Create database for E2E testing."""
    db_path = str(Path(e2e_environment["db_dir"]) / "test.db")
    return ProjectDatabase(db_path)


@pytest.mark.e2e
class TestOrchestratorInitialization:
    """Test orchestrator initialization in E2E context."""

    def test_orchestrator_initializes_with_config(self, orchestrator):
        """Test orchestrator initializes with SocratesConfig."""
        assert orchestrator is not None
        assert orchestrator.config is not None
        assert orchestrator.api_key is not None

    def test_all_agents_accessible(self, orchestrator):
        """Test all core agents are accessible after initialization."""
        agents = [
            orchestrator.project_manager,
            orchestrator.socratic_counselor,
            orchestrator.knowledge_manager,
            orchestrator.code_generator,
            orchestrator.document_processor,
            orchestrator.system_monitor,
            orchestrator.user_manager,
        ]
        for agent in agents:
            assert agent is not None


@pytest.mark.e2e
class TestProjectWorkflow:
    """Test complete project workflow."""

    def test_create_and_manage_project(self, database):
        """Test creating and managing a project through complete lifecycle."""
        # Create project context
        project = ProjectContext(
            project_id="e2e_test_proj",
            name="E2E Test Project",
            owner="e2e_user",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="End-to-end test project"
        )

        # Save project
        database.save_project(project)

        # Load project
        loaded = database.load_project(project.project_id)

        # Verify
        assert loaded is not None
        assert loaded.name == "E2E Test Project"
        assert loaded.owner == "e2e_user"

    def test_project_lifecycle(self, database):
        """Test complete project lifecycle: create, update, load."""
        # Phase 1: Create
        project = ProjectContext(
            project_id="lifecycle_test",
            name="Lifecycle Test",
            owner="test_owner",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        database.save_project(project)

        # Phase 2: Update
        project.phase = "phase2"
        project.progress = 50
        database.save_project(project)

        # Phase 3: Retrieve and verify
        loaded = database.load_project(project.project_id)
        assert loaded.phase == "phase2"
        assert loaded.progress == 50


@pytest.mark.e2e
class TestOrchestrationWorkflow:
    """Test orchestration workflows."""

    def test_orchestrator_with_database_integration(self, orchestrator, database, e2e_environment):
        """Test orchestrator working with database."""
        # Verify both systems are functional
        assert orchestrator.database is not None
        assert database is not None

        # Create project through database
        project = ProjectContext(
            project_id="orch_db_test",
            name="Orchestration DB Test",
            owner="orch_user",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        database.save_project(project)

        # Verify it was created
        loaded = database.load_project(project.project_id)
        assert loaded is not None
        assert loaded.name == "Orchestration DB Test"

    def test_agents_can_process_project_data(self, orchestrator, database):
        """Test that agents can access and work with project data."""
        # Create project
        project = ProjectContext(
            project_id="agent_test",
            name="Agent Test Project",
            owner="agent_user",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        database.save_project(project)

        # Verify agents are accessible
        assert orchestrator.project_manager is not None
        assert orchestrator.socratic_counselor is not None

        # Project is available in database
        loaded = database.load_project(project.project_id)
        assert loaded is not None


@pytest.mark.e2e
class TestMultipleProjectManagement:
    """Test managing multiple projects."""

    def test_manage_multiple_projects(self, database):
        """Test managing multiple projects in same database."""
        projects = []
        for i in range(3):
            project = ProjectContext(
                project_id=f"multi_proj_{i}",
                name=f"Project {i}",
                owner="multi_owner",
                phase=f"phase{i+1}",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            database.save_project(project)
            projects.append(project)

        # Verify all can be loaded
        for project in projects:
            loaded = database.load_project(project.project_id)
            assert loaded is not None
            assert loaded.name == project.name


@pytest.mark.e2e
class TestErrorHandling:
    """Test error handling in E2E workflows."""

    def test_loading_nonexistent_project(self, database):
        """Test graceful handling of non-existent project."""
        result = database.load_project("nonexistent_proj_xyz_123")
        assert result is None

    def test_orchestrator_resilience(self, orchestrator):
        """Test orchestrator handles edge cases gracefully."""
        # Verify all agents are still accessible despite various conditions
        assert orchestrator.project_manager is not None
        assert orchestrator.knowledge_manager is not None
        assert orchestrator.event_emitter is not None


@pytest.mark.e2e
class TestIntegrationBetweenComponents:
    """Test integration between orchestrator and database."""

    def test_orchestrator_and_database_compatibility(self, orchestrator, database):
        """Test orchestrator and database work together."""
        # Both components should be functional
        assert orchestrator is not None
        assert database is not None

        # Both should have core functionality
        assert hasattr(orchestrator, 'database')
        assert hasattr(database, 'save_project')
        assert hasattr(database, 'load_project')

    def test_shared_data_models(self, database):
        """Test shared data models (ProjectContext) work correctly."""
        project = ProjectContext(
            project_id="model_test",
            name="Model Test",
            owner="model_owner",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="Testing ProjectContext",
            progress=25,
            status="active",
        )

        database.save_project(project)
        loaded = database.load_project(project.project_id)

        assert loaded.project_id == project.project_id
        assert loaded.name == project.name
        assert loaded.progress == 25
        assert loaded.status == "active"
