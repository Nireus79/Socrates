"""
Phase 1 Tests: ProjectService

Test suite validating that ProjectService works standalone without orchestrator.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from socratic_system.services import ProjectService
from socratic_system.repositories import ProjectRepository
from socratic_system.models import ProjectContext


class TestProjectServiceInitialization:
    """Test ProjectService initialization"""

    def test_project_service_can_be_instantiated(self):
        """Test that ProjectService can be created without orchestrator"""
        mock_config = Mock()
        mock_database = Mock()

        service = ProjectService(mock_config, mock_database)

        assert service is not None
        assert service.config == mock_config
        assert service.repository is not None

    def test_project_service_has_required_methods(self):
        """Test that ProjectService has all required methods"""
        mock_config = Mock()
        mock_database = Mock()

        service = ProjectService(mock_config, mock_database)

        assert hasattr(service, "create_project")
        assert hasattr(service, "get_project")
        assert hasattr(service, "update_project")
        assert hasattr(service, "delete_project")
        assert hasattr(service, "project_exists")


class TestProjectServiceOperations:
    """Test ProjectService operations"""

    def test_create_project_with_valid_data(self):
        """Test creating a project with valid data"""
        mock_config = Mock()
        mock_database = Mock()

        service = ProjectService(mock_config, mock_database)
        service.repository.save_project = Mock(return_value=True)

        project = service.create_project(
            name="Test Project",
            description="Test Description",
            owner="user_123"
        )

        assert project is not None
        assert project.name == "Test Project"
        assert project.description == "Test Description"
        assert project.owner == "user_123"

    def test_create_project_with_empty_name(self):
        """Test that creating project with empty name returns None"""
        mock_config = Mock()
        mock_database = Mock()

        service = ProjectService(mock_config, mock_database)

        project = service.create_project(name="", owner="user_123")

        assert project is None

    def test_get_project_calls_repository(self):
        """Test that get_project delegates to repository"""
        mock_config = Mock()
        mock_database = Mock()

        service = ProjectService(mock_config, mock_database)

        mock_project = Mock(spec=ProjectContext)
        service.repository.load_project = Mock(return_value=mock_project)

        result = service.get_project("proj_123")

        service.repository.load_project.assert_called_once_with("proj_123")
        assert result == mock_project

    def test_project_exists_returns_true_for_existing(self):
        """Test that project_exists returns correct value"""
        mock_config = Mock()
        mock_database = Mock()

        service = ProjectService(mock_config, mock_database)
        service.repository.project_exists = Mock(return_value=True)

        exists = service.project_exists("proj_123")

        assert exists is True
        service.repository.project_exists.assert_called_once_with("proj_123")

    def test_delete_project_calls_repository(self):
        """Test that delete_project delegates to repository"""
        mock_config = Mock()
        mock_database = Mock()

        service = ProjectService(mock_config, mock_database)
        service.repository.delete_project = Mock(return_value=True)

        result = service.delete_project("proj_123")

        service.repository.delete_project.assert_called_once_with("proj_123")
        assert result is True


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
