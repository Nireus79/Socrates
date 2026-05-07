"""
Phase 1 Tests: ProjectService

Test suite validating that ProjectService works with orchestrator dependencies.
"""

from unittest.mock import Mock

import pytest

from socratic_system.models import ProjectContext
from socratic_system.repositories import ProjectRepository
from socratic_system.services import ProjectService


class TestProjectServiceInitialization:
    """Test ProjectService initialization"""

    def test_project_service_can_be_instantiated(self):
        """Test that ProjectService can be created with orchestrator dependencies"""
        mock_config = Mock()
        mock_database = Mock()
        mock_claude_client = Mock()
        mock_event_emitter = Mock()

        service = ProjectService(mock_config, mock_database, mock_claude_client, mock_event_emitter)

        assert service is not None
        assert service.config == mock_config
        assert service.database == mock_database
        assert service.claude_client == mock_claude_client
        assert service.event_emitter == mock_event_emitter

    def test_project_service_has_required_methods(self):
        """Test that ProjectService has all required methods"""
        mock_config = Mock()
        mock_database = Mock()
        mock_claude_client = Mock()
        mock_event_emitter = Mock()

        service = ProjectService(mock_config, mock_database, mock_claude_client, mock_event_emitter)

        assert hasattr(service, "create_project")
        assert hasattr(service, "load_project")
        assert hasattr(service, "save_project")


class TestProjectServiceOperations:
    """Test ProjectService operations"""

    def test_create_project_with_valid_data(self):
        """Test creating a project with valid data"""
        mock_config = Mock()
        mock_database = Mock()
        mock_claude_client = Mock()
        mock_event_emitter = Mock()

        service = ProjectService(mock_config, mock_database, mock_claude_client, mock_event_emitter)

        project = service.create_project(
            spec={"name": "Test Project", "description": "Test Description", "user_id": "user_123"}
        )

        assert project is not None
        assert project.name == "Test Project"
        assert project.description == "Test Description"
        assert project.owner == "user_123"
        # Verify event was emitted
        mock_event_emitter.emit.assert_called()

    def test_create_project_with_empty_name(self):
        """Test that creating project with empty name raises ValueError"""
        mock_config = Mock()
        mock_database = Mock()
        mock_claude_client = Mock()
        mock_event_emitter = Mock()

        service = ProjectService(mock_config, mock_database, mock_claude_client, mock_event_emitter)

        with pytest.raises(ValueError):
            service.create_project(spec={"name": "", "user_id": "user_123"})

    def test_load_project_calls_database(self):
        """Test that load_project delegates to database"""
        mock_config = Mock()
        mock_database = Mock()
        mock_claude_client = Mock()
        mock_event_emitter = Mock()

        service = ProjectService(mock_config, mock_database, mock_claude_client, mock_event_emitter)

        mock_project = Mock(spec=ProjectContext)
        mock_database.load_project = Mock(return_value=mock_project)

        result = service.load_project("proj_123")

        mock_database.load_project.assert_called_once_with("proj_123")
        assert result == mock_project

    def test_save_project_calls_database(self):
        """Test that save_project delegates to database"""
        mock_config = Mock()
        mock_database = Mock()
        mock_claude_client = Mock()
        mock_event_emitter = Mock()

        service = ProjectService(mock_config, mock_database, mock_claude_client, mock_event_emitter)

        mock_project = Mock(spec=ProjectContext)
        mock_project.project_id = "proj_123"

        service.save_project(mock_project)

        mock_database.save_project.assert_called_once_with(mock_project)
        # Verify event was emitted
        mock_event_emitter.emit.assert_called()


class TestProjectRepositoryInitialization:
    """Test ProjectRepository initialization"""

    def test_project_repository_can_be_instantiated(self):
        """Test that ProjectRepository can be created"""
        mock_database = Mock()

        repo = ProjectRepository(mock_database)

        assert repo is not None
        assert repo.database == mock_database

    def test_project_repository_has_required_methods(self):
        """Test that ProjectRepository has all required methods"""
        mock_database = Mock()

        repo = ProjectRepository(mock_database)

        assert hasattr(repo, "save_project")
        assert hasattr(repo, "load_project")
        assert hasattr(repo, "delete_project")
        assert hasattr(repo, "project_exists")
        assert hasattr(repo, "get_all_projects")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
