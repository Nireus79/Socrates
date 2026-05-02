"""
Phase 1 Tests - QualityService and QualityRepository

Tests the maturity calculation service and repository pattern for quality metrics.
Validates that:
1. QualityRepository provides single point of change for maturity data
2. QualityService uses repository instead of direct database calls
3. No orchestrator coupling
4. Services work independently
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from socratic_system.models import ProjectContext
from socratic_system.repositories.quality_repository import QualityRepository
from socratic_system.services.quality_service import QualityService


class TestQualityRepositoryInitialization:
    """Test QualityRepository initialization and setup."""

    def test_quality_repository_can_be_instantiated(self):
        """QualityRepository should initialize with database."""
        mock_db = MagicMock()
        repo = QualityRepository(mock_db)
        assert repo is not None
        assert repo.database == mock_db

    def test_quality_repository_has_required_methods(self):
        """QualityRepository should have all required data access methods."""
        mock_db = MagicMock()
        repo = QualityRepository(mock_db)

        required_methods = [
            "get_phase_maturity_scores",
            "update_phase_maturity_score",
            "get_category_scores",
            "update_category_scores",
            "get_analytics_metrics",
            "update_analytics_metrics",
            "get_maturity_history",
            "add_maturity_event",
            "get_categorized_specs",
            "add_categorized_specs",
        ]

        for method in required_methods:
            assert hasattr(repo, method), f"Missing method: {method}"
            assert callable(getattr(repo, method)), f"Not callable: {method}"


class TestQualityRepositoryOperations:
    """Test QualityRepository data access operations."""

    def test_get_phase_maturity_scores_returns_dict(self):
        """get_phase_maturity_scores should return phase scores."""
        mock_db = MagicMock()
        project = MagicMock()
        project.phase_maturity_scores = {"discovery": 50.0, "analysis": 30.0}
        mock_db.load_project.return_value = project

        repo = QualityRepository(mock_db)
        scores = repo.get_phase_maturity_scores("test-project")

        assert isinstance(scores, dict)
        assert scores == {"discovery": 50.0, "analysis": 30.0}
        mock_db.load_project.assert_called_once_with("test-project")

    def test_get_phase_maturity_scores_handles_missing_project(self):
        """get_phase_maturity_scores should return empty dict if project not found."""
        mock_db = MagicMock()
        mock_db.load_project.return_value = None

        repo = QualityRepository(mock_db)
        scores = repo.get_phase_maturity_scores("missing-project")

        assert scores == {}

    def test_update_phase_maturity_score_clamps_values(self):
        """update_phase_maturity_score should clamp score to 0-100."""
        mock_db = MagicMock()
        project = MagicMock()
        project.phase_maturity_scores = {"discovery": 50.0}
        project._calculate_overall_maturity.return_value = 60.0
        mock_db.load_project.return_value = project

        repo = QualityRepository(mock_db)

        # Test clamping to 100
        result = repo.update_phase_maturity_score("test-project", "discovery", 150.0)
        assert result is True
        assert project.phase_maturity_scores["discovery"] == 100.0

        # Test clamping to 0
        result = repo.update_phase_maturity_score("test-project", "discovery", -50.0)
        assert result is True
        assert project.phase_maturity_scores["discovery"] == 0.0

    def test_get_analytics_metrics_returns_dict(self):
        """get_analytics_metrics should return analytics data."""
        mock_db = MagicMock()
        project = MagicMock()
        project.analytics_metrics = {
            "velocity": 2.5,
            "total_qa_sessions": 10,
            "avg_confidence": 0.85
        }
        mock_db.load_project.return_value = project

        repo = QualityRepository(mock_db)
        metrics = repo.get_analytics_metrics("test-project")

        assert isinstance(metrics, dict)
        assert metrics["velocity"] == 2.5
        assert metrics["total_qa_sessions"] == 10

    def test_add_maturity_event_appends_to_history(self):
        """add_maturity_event should append event to history."""
        mock_db = MagicMock()
        project = MagicMock()
        project.maturity_history = []
        mock_db.load_project.return_value = project

        repo = QualityRepository(mock_db)
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "phase": "discovery",
            "score_before": 50.0,
            "score_after": 52.5,
            "delta": 2.5,
            "event_type": "response_processed",
            "details": {"specs_added": 2}
        }

        result = repo.add_maturity_event("test-project", event)

        assert result is True
        assert len(project.maturity_history) == 1
        assert project.maturity_history[0] == event
        mock_db.save_project.assert_called_once()

    def test_add_categorized_specs_creates_phase_list(self):
        """add_categorized_specs should create phase list if not exists."""
        mock_db = MagicMock()
        project = MagicMock()
        project.categorized_specs = {}
        mock_db.load_project.return_value = project

        repo = QualityRepository(mock_db)
        specs = [
            {"name": "spec1", "value": 1.0, "confidence": 0.9},
            {"name": "spec2", "value": 1.0, "confidence": 0.85}
        ]

        result = repo.add_categorized_specs("test-project", "discovery", specs)

        assert result is True
        assert "discovery" in project.categorized_specs
        assert len(project.categorized_specs["discovery"]) == 2


class TestQualityServiceInitialization:
    """Test QualityService initialization and setup."""

    @patch("socratic_system.services.quality_service.MaturityCalculator")
    def test_quality_service_can_be_instantiated(self, mock_calculator_class):
        """QualityService should initialize with config and database."""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.READY_THRESHOLD = 60.0
        mock_calculator.COMPLETE_THRESHOLD = 100.0
        mock_calculator.WARNING_THRESHOLD = 40.0

        service = QualityService(mock_config, mock_db)

        assert service is not None
        assert service.repository is not None
        assert service.calculator is not None

    @patch("socratic_system.services.quality_service.MaturityCalculator")
    def test_quality_service_has_required_methods(self, mock_calculator_class):
        """QualityService should have all required business logic methods."""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.READY_THRESHOLD = 60.0
        mock_calculator.COMPLETE_THRESHOLD = 100.0
        mock_calculator.WARNING_THRESHOLD = 40.0

        service = QualityService(mock_config, mock_db)

        required_methods = [
            "update_maturity_after_response",
            "calculate_phase_maturity",
            "get_maturity_summary",
            "get_maturity_history",
            "update_analytics_metrics",
        ]

        for method in required_methods:
            assert hasattr(service, method), f"Missing method: {method}"
            assert callable(getattr(service, method)), f"Not callable: {method}"


class TestQualityServiceOperations:
    """Test QualityService business logic operations."""

    @patch("socratic_system.services.quality_service.MaturityCalculator")
    def test_update_maturity_after_response_incremental_scoring(self, mock_calculator_class):
        """update_maturity_after_response should use incremental scoring."""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.READY_THRESHOLD = 60.0
        mock_calculator.COMPLETE_THRESHOLD = 100.0
        mock_calculator.WARNING_THRESHOLD = 40.0

        # Mock categorize_insights to return specs
        mock_calculator.categorize_insights.return_value = [
            {"name": "spec1", "value": 1.0, "confidence": 0.9},
            {"name": "spec2", "value": 1.0, "confidence": 0.8}
        ]

        # Mock project
        project = MagicMock()
        project.phase = "discovery"
        project.phase_maturity_scores = {"discovery": 50.0}
        project.categorized_specs = {}
        project._calculate_overall_maturity.return_value = 51.7

        service = QualityService(mock_config, mock_db)
        service.repository.add_categorized_specs = MagicMock(return_value=True)
        service.repository.update_phase_maturity_score = MagicMock(return_value=True)
        service.update_analytics_metrics = MagicMock(return_value=True)

        result = service.update_maturity_after_response(
            "test-project",
            project,
            {"test": "insight"},
            "user123"
        )

        assert result["status"] == "success"
        assert result["score_before"] == 50.0
        assert pytest.approx(result["answer_score"], rel=1e-9) == 1.7  # 1.0 * 0.9 + 1.0 * 0.8
        assert pytest.approx(result["score_after"], rel=1e-9) == 51.7

    @patch("socratic_system.services.quality_service.MaturityCalculator")
    def test_update_maturity_after_response_handles_no_specs(self, mock_calculator_class):
        """update_maturity_after_response should handle case with no specs."""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.READY_THRESHOLD = 60.0
        mock_calculator.COMPLETE_THRESHOLD = 100.0
        mock_calculator.WARNING_THRESHOLD = 40.0
        mock_calculator.categorize_insights.return_value = []

        project = MagicMock()
        project.phase = "discovery"
        project.phase_maturity_scores = {"discovery": 50.0}

        service = QualityService(mock_config, mock_db)
        result = service.update_maturity_after_response(
            "test-project",
            project,
            {"test": "insight"}
        )

        assert result["status"] == "success"
        assert result["message"] == "No new specs added"

    @patch("socratic_system.services.quality_service.MaturityCalculator")
    def test_get_maturity_summary_returns_all_phases(self, mock_calculator_class):
        """get_maturity_summary should return summary for all phases."""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.READY_THRESHOLD = 60.0
        mock_calculator.COMPLETE_THRESHOLD = 100.0
        mock_calculator.WARNING_THRESHOLD = 40.0

        project = MagicMock()
        project.phase_maturity_scores = {
            "discovery": 50.0,
            "analysis": 70.0,
            "design": 80.0,
            "implementation": 30.0
        }

        service = QualityService(mock_config, mock_db)
        result = service.get_maturity_summary("test-project", project)

        assert result["status"] == "success"
        summary = result["summary"]
        assert "discovery" in summary
        assert "analysis" in summary
        assert "design" in summary
        assert "implementation" in summary
        assert summary["discovery"]["score"] == 50.0
        assert summary["analysis"]["ready"] is True  # 70 >= 60
        assert summary["design"]["complete"] is False  # 80 < 100

    @patch("socratic_system.services.quality_service.MaturityCalculator")
    def test_get_maturity_history_returns_events(self, mock_calculator_class):
        """get_maturity_history should return maturity events."""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.READY_THRESHOLD = 60.0
        mock_calculator.COMPLETE_THRESHOLD = 100.0
        mock_calculator.WARNING_THRESHOLD = 40.0

        events = [
            {"timestamp": "2024-01-01T00:00:00", "event_type": "response_processed"},
            {"timestamp": "2024-01-02T00:00:00", "event_type": "response_processed"}
        ]

        service = QualityService(mock_config, mock_db)
        service.repository.get_maturity_history = MagicMock(return_value=events)

        result = service.get_maturity_history("test-project")

        assert result["status"] == "success"
        assert result["total_events"] == 2
        assert len(result["history"]) == 2

    @patch("socratic_system.services.quality_service.MaturityCalculator")
    @patch("socratic_system.services.quality_service.AnalyticsCalculator")
    def test_update_analytics_metrics_calculates_velocity(self, mock_analytics_class, mock_calculator_class):
        """update_analytics_metrics should calculate velocity from history."""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.READY_THRESHOLD = 60.0
        mock_calculator.COMPLETE_THRESHOLD = 100.0
        mock_calculator.WARNING_THRESHOLD = 40.0

        mock_analytics = MagicMock()
        mock_analytics_class.return_value = mock_analytics
        mock_analytics.identify_weak_categories.return_value = []
        mock_analytics.identify_strong_categories.return_value = []

        project = MagicMock()
        project.project_type = "software"
        project.maturity_history = [
            {"event_type": "response_processed", "delta": 2.5},
            {"event_type": "response_processed", "delta": 2.0}
        ]
        project.categorized_specs = {
            "discovery": [
                {"confidence": 0.9},
                {"confidence": 0.85}
            ]
        }

        service = QualityService(mock_config, mock_db)
        service.repository.update_analytics_metrics = MagicMock(return_value=True)

        result = service.update_analytics_metrics("test-project", project)

        assert result is True
        service.repository.update_analytics_metrics.assert_called_once()
        call_args = service.repository.update_analytics_metrics.call_args[0]
        metrics = call_args[1]
        assert pytest.approx(metrics["velocity"], rel=1e-9) == 2.25  # (2.5 + 2.0) / 2
        assert metrics["total_qa_sessions"] == 2


class TestServiceIsolation:
    """Test that services work independently without orchestrator."""

    @patch("socratic_system.services.quality_service.MaturityCalculator")
    def test_quality_service_no_orchestrator_dependency(self, mock_calculator_class):
        """QualityService should not require orchestrator."""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.READY_THRESHOLD = 60.0
        mock_calculator.COMPLETE_THRESHOLD = 100.0
        mock_calculator.WARNING_THRESHOLD = 40.0

        # Create service without orchestrator
        service = QualityService(mock_config, mock_db)

        # Verify no orchestrator attribute
        assert not hasattr(service, "orchestrator")

        # Verify it has repository and config instead
        assert hasattr(service, "repository")
        assert hasattr(service, "config")

    @patch("socratic_system.services.quality_service.MaturityCalculator")
    def test_quality_service_uses_repository_not_direct_db_calls(self, mock_calculator_class):
        """QualityService should use repository, not direct database calls."""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.READY_THRESHOLD = 60.0
        mock_calculator.COMPLETE_THRESHOLD = 100.0
        mock_calculator.WARNING_THRESHOLD = 40.0

        service = QualityService(mock_config, mock_db)

        # Verify repository is used
        assert isinstance(service.repository, QualityRepository)

        # Get mock to verify method calls go through repository
        service.repository.get_phase_maturity_scores = MagicMock(return_value={})
        service.repository.get_phase_maturity_scores("test-project")
        service.repository.get_phase_maturity_scores.assert_called_once()
