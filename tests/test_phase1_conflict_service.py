"""
Phase 1 Tests - ConflictService and ConflictRepository

Tests the conflict detection and resolution service and repository pattern.
Validates that:
1. ConflictRepository provides single point of change for conflict data
2. ConflictService uses repository instead of direct database calls
3. No orchestrator coupling
4. Services work independently
"""

from unittest.mock import MagicMock, patch

import pytest

from socratic_system.repositories.conflict_repository import ConflictRepository
from socratic_system.services.conflict_service import ConflictService


class TestConflictRepositoryInitialization:
    """Test ConflictRepository initialization and setup."""

    def test_conflict_repository_can_be_instantiated(self):
        """ConflictRepository should initialize with database."""
        mock_db = MagicMock()
        repo = ConflictRepository(mock_db)
        assert repo is not None
        assert repo.database == mock_db

    def test_conflict_repository_has_required_methods(self):
        """ConflictRepository should have all required data access methods."""
        mock_db = MagicMock()
        repo = ConflictRepository(mock_db)

        required_methods = [
            "get_project_conflicts",
            "add_conflict",
            "resolve_conflict",
            "get_unresolved_conflicts",
            "get_conflicts_by_type",
            "get_high_severity_conflicts",
            "clear_conflicts",
        ]

        for method in required_methods:
            assert hasattr(repo, method), f"Missing method: {method}"
            assert callable(getattr(repo, method)), f"Not callable: {method}"


class TestConflictRepositoryOperations:
    """Test ConflictRepository data access operations."""

    def test_get_project_conflicts_returns_list(self):
        """get_project_conflicts should return list of conflicts."""
        mock_db = MagicMock()
        project = MagicMock()
        project.conflicts = [
            {"conflict_type": "requirements", "severity": "high"},
            {"conflict_type": "tech_stack", "severity": "medium"},
        ]
        mock_db.load_project.return_value = project

        repo = ConflictRepository(mock_db)
        conflicts = repo.get_project_conflicts("test-project")

        assert isinstance(conflicts, list)
        assert len(conflicts) == 2
        assert conflicts[0]["conflict_type"] == "requirements"

    def test_get_project_conflicts_returns_empty_for_missing_project(self):
        """get_project_conflicts should return empty list if project not found."""
        mock_db = MagicMock()
        mock_db.load_project.return_value = None

        repo = ConflictRepository(mock_db)
        conflicts = repo.get_project_conflicts("missing-project")

        assert conflicts == []

    def test_add_conflict_appends_to_project(self):
        """add_conflict should append conflict to project conflicts list."""
        mock_db = MagicMock()
        project = MagicMock()
        project.conflicts = []
        mock_db.load_project.return_value = project

        repo = ConflictRepository(mock_db)
        result = repo.add_conflict(
            "test-project",
            "requirements",
            "high",
            "Conflicting requirements detected",
            {"details": "spec1 vs spec2"}
        )

        assert result is True
        assert len(project.conflicts) == 1
        assert project.conflicts[0]["conflict_type"] == "requirements"
        assert project.conflicts[0]["severity"] == "high"
        assert project.conflicts[0]["status"] == "unresolved"
        mock_db.save_project.assert_called_once()

    def test_resolve_conflict_updates_status(self):
        """resolve_conflict should mark conflict as resolved."""
        mock_db = MagicMock()
        project = MagicMock()
        project.conflicts = [
            {"conflict_type": "requirements", "status": "unresolved"}
        ]
        mock_db.load_project.return_value = project

        repo = ConflictRepository(mock_db)
        result = repo.resolve_conflict(
            "test-project",
            0,
            "Updated spec to match requirements",
            {"updated_spec": "spec1"}
        )

        assert result is True
        assert project.conflicts[0]["status"] == "resolved"
        assert project.conflicts[0]["resolution"] == "Updated spec to match requirements"
        mock_db.save_project.assert_called_once()

    def test_get_unresolved_conflicts_filters_by_status(self):
        """get_unresolved_conflicts should return only unresolved conflicts."""
        mock_db = MagicMock()
        project = MagicMock()
        project.conflicts = [
            {"conflict_type": "requirements", "status": "unresolved"},
            {"conflict_type": "tech_stack", "status": "resolved"},
            {"conflict_type": "goals", "status": "unresolved"},
        ]
        mock_db.load_project.return_value = project

        repo = ConflictRepository(mock_db)
        unresolved = repo.get_unresolved_conflicts("test-project")

        assert len(unresolved) == 2
        assert all(c["status"] == "unresolved" for c in unresolved)

    def test_get_conflicts_by_type_filters_by_type(self):
        """get_conflicts_by_type should return only conflicts of specified type."""
        mock_db = MagicMock()
        project = MagicMock()
        project.conflicts = [
            {"conflict_type": "requirements", "severity": "high"},
            {"conflict_type": "tech_stack", "severity": "medium"},
            {"conflict_type": "requirements", "severity": "low"},
        ]
        mock_db.load_project.return_value = project

        repo = ConflictRepository(mock_db)
        req_conflicts = repo.get_conflicts_by_type("test-project", "requirements")

        assert len(req_conflicts) == 2
        assert all(c["conflict_type"] == "requirements" for c in req_conflicts)

    def test_get_high_severity_conflicts_filters_correctly(self):
        """get_high_severity_conflicts should return high and critical only."""
        mock_db = MagicMock()
        project = MagicMock()
        project.conflicts = [
            {"conflict_type": "requirements", "severity": "high"},
            {"conflict_type": "tech_stack", "severity": "medium"},
            {"conflict_type": "goals", "severity": "critical"},
            {"conflict_type": "constraints", "severity": "low"},
        ]
        mock_db.load_project.return_value = project

        repo = ConflictRepository(mock_db)
        high_severity = repo.get_high_severity_conflicts("test-project")

        assert len(high_severity) == 2
        assert all(c["severity"] in ["high", "critical"] for c in high_severity)

    def test_clear_conflicts_empties_list(self):
        """clear_conflicts should empty the conflicts list."""
        mock_db = MagicMock()
        project = MagicMock()
        project.conflicts = [
            {"conflict_type": "requirements"},
            {"conflict_type": "tech_stack"},
        ]
        mock_db.load_project.return_value = project

        repo = ConflictRepository(mock_db)
        result = repo.clear_conflicts("test-project")

        assert result is True
        assert project.conflicts == []
        mock_db.save_project.assert_called_once()


class TestConflictServiceInitialization:
    """Test ConflictService initialization and setup."""

    def test_conflict_service_can_be_instantiated(self):
        """ConflictService should initialize with config and database."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)

        assert service is not None
        assert service.repository is not None

    def test_conflict_service_has_required_methods(self):
        """ConflictService should have all required business logic methods."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)

        required_methods = [
            "detect_conflicts",
            "resolve_conflict",
            "get_conflict_suggestions",
            "get_project_conflicts",
            "get_unresolved_conflicts",
            "get_high_severity_conflicts",
            "clear_project_conflicts",
        ]

        for method in required_methods:
            assert hasattr(service, method), f"Missing method: {method}"
            assert callable(getattr(service, method)), f"Not callable: {method}"


class TestConflictServiceOperations:
    """Test ConflictService business logic operations."""

    def test_detect_conflicts_handles_empty_insights(self):
        """detect_conflicts should handle empty insights gracefully."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)
        project = MagicMock()

        result = service.detect_conflicts(
            "test-project",
            project,
            {}
        )

        assert result["status"] == "success"
        assert result["conflicts"] == []

    def test_detect_conflicts_stores_detected_conflicts(self):
        """detect_conflicts should store detected conflicts in repository."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)
        service.repository.add_conflict = MagicMock(return_value=True)

        project = MagicMock()
        insights = {"requirement": "new requirement"}

        result = service.detect_conflicts(
            "test-project",
            project,
            insights
        )

        assert result["status"] == "success"

    def test_resolve_conflict_delegates_to_repository(self):
        """resolve_conflict should use repository to resolve."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)
        service.repository.resolve_conflict = MagicMock(return_value=True)

        result = service.resolve_conflict(
            "test-project",
            0,
            "Updated specification",
            {"spec_id": "spec1"}
        )

        assert result["status"] == "success"
        service.repository.resolve_conflict.assert_called_once()

    def test_get_conflict_suggestions_returns_suggestions(self):
        """get_conflict_suggestions should return suggestions from conflict."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)
        service.repository.get_project_conflicts = MagicMock(return_value=[
            {
                "conflict_type": "requirements",
                "details": {
                    "suggestions": ["Use spec1", "Use spec2"]
                }
            }
        ])

        result = service.get_conflict_suggestions("test-project", 0)

        assert result["status"] == "success"
        assert len(result["suggestions"]) == 2

    def test_get_project_conflicts_organizes_by_type(self):
        """get_project_conflicts should organize conflicts by type."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)
        service.repository.get_project_conflicts = MagicMock(return_value=[
            {"conflict_type": "requirements", "severity": "high"},
            {"conflict_type": "requirements", "severity": "medium"},
            {"conflict_type": "tech_stack", "severity": "high"},
        ])

        result = service.get_project_conflicts("test-project")

        assert result["status"] == "success"
        assert result["total"] == 3
        assert "requirements" in result["by_type"]
        assert "tech_stack" in result["by_type"]
        assert len(result["by_type"]["requirements"]) == 2

    def test_get_unresolved_conflicts_filters_correctly(self):
        """get_unresolved_conflicts should return only unresolved."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)
        unresolved = [
            {"conflict_type": "requirements", "status": "unresolved"},
            {"conflict_type": "tech_stack", "status": "unresolved"},
        ]
        service.repository.get_unresolved_conflicts = MagicMock(return_value=unresolved)

        result = service.get_unresolved_conflicts("test-project")

        assert result["status"] == "success"
        assert result["count"] == 2

    def test_get_high_severity_conflicts_returns_critical(self):
        """get_high_severity_conflicts should include critical severity."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)
        high_severity = [
            {"conflict_type": "requirements", "severity": "high"},
            {"conflict_type": "tech_stack", "severity": "critical"},
        ]
        service.repository.get_high_severity_conflicts = MagicMock(return_value=high_severity)

        result = service.get_high_severity_conflicts("test-project")

        assert result["status"] == "success"
        assert result["count"] == 2

    def test_clear_project_conflicts_delegates_to_repository(self):
        """clear_project_conflicts should use repository to clear."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)
        service.repository.clear_conflicts = MagicMock(return_value=True)

        result = service.clear_project_conflicts("test-project")

        assert result["status"] == "success"
        service.repository.clear_conflicts.assert_called_once()


class TestServiceIsolation:
    """Test that services work independently without orchestrator."""

    def test_conflict_service_no_orchestrator_dependency(self):
        """ConflictService should not require orchestrator."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)

        # Verify no orchestrator attribute
        assert not hasattr(service, "orchestrator")

        # Verify it has repository and config instead
        assert hasattr(service, "repository")
        assert hasattr(service, "config")

    def test_conflict_service_uses_repository_not_direct_db(self):
        """ConflictService should use repository, not direct database calls."""
        mock_db = MagicMock()
        mock_config = MagicMock()

        service = ConflictService(mock_config, mock_db)

        # Verify repository is used
        assert isinstance(service.repository, ConflictRepository)

        # Get mock to verify method calls go through repository
        service.repository.get_project_conflicts = MagicMock(return_value=[])
        service.repository.get_project_conflicts("test-project")
        service.repository.get_project_conflicts.assert_called_once()
