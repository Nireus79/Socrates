"""
Phase 1: InsightService and InsightRepository Tests

Tests for insight analysis, categorization, and recommendation generation.
Validates repository pattern enforcement and service isolation.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from socratic_system.config import SocratesConfig
from socratic_system.repositories.insight_repository import InsightRepository
from socratic_system.services.insight_service import InsightService


class TestInsightRepositoryInitialization:
    """Test InsightRepository initialization."""

    def test_repository_initialization(self):
        """Test repository initializes with database."""
        mock_db = MagicMock()
        repo = InsightRepository(mock_db)
        assert repo.database is mock_db
        assert repo.logger is not None

    def test_repository_has_logger(self):
        """Test repository has logging configured."""
        mock_db = MagicMock()
        repo = InsightRepository(mock_db)
        assert isinstance(repo.logger, logging.Logger)


class TestInsightRepositoryOperations:
    """Test InsightRepository data access methods."""

    def test_add_insight_success(self):
        """Test adding insight to project."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.insights = []
        mock_db.load_project.return_value = mock_project

        repo = InsightRepository(mock_db)
        result = repo.add_insight(
            project_id="test_proj",
            content="Test requirement",
            category="requirement",
            confidence=0.85,
            metadata={"source": "analysis"},
        )

        assert result is True
        assert len(mock_project.insights) == 1
        assert mock_project.insights[0]["content"] == "Test requirement"
        assert mock_project.insights[0]["category"] == "requirement"
        assert mock_project.insights[0]["confidence"] == 0.85
        assert mock_db.save_project.called

    def test_add_insight_confidence_bounds(self):
        """Test confidence is bounded between 0 and 1."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.insights = []
        mock_db.load_project.return_value = mock_project

        repo = InsightRepository(mock_db)

        # Test over 1.0
        repo.add_insight(
            project_id="test_proj",
            content="Test",
            category="requirement",
            confidence=1.5,
        )
        assert mock_project.insights[0]["confidence"] == 1.0

        # Test under 0.0
        mock_project.insights = []
        repo.add_insight(
            project_id="test_proj",
            content="Test",
            category="requirement",
            confidence=-0.5,
        )
        assert mock_project.insights[0]["confidence"] == 0.0

    def test_add_insight_project_not_found(self):
        """Test adding insight when project doesn't exist."""
        mock_db = MagicMock()
        mock_db.load_project.return_value = None

        repo = InsightRepository(mock_db)
        result = repo.add_insight(
            project_id="nonexistent",
            content="Test",
            category="requirement",
        )

        assert result is False

    def test_get_project_insights(self):
        """Test retrieving all insights for project."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        insights_data = [
            {"content": "Requirement 1", "category": "requirement", "confidence": 0.9},
            {"content": "Risk 1", "category": "risk", "confidence": 0.8},
        ]
        mock_project.insights = insights_data
        mock_db.load_project.return_value = mock_project

        repo = InsightRepository(mock_db)
        result = repo.get_project_insights("test_proj")

        assert result == insights_data
        assert len(result) == 2

    def test_get_project_insights_empty(self):
        """Test getting insights for project with none."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.insights = []
        mock_db.load_project.return_value = mock_project

        repo = InsightRepository(mock_db)
        result = repo.get_project_insights("test_proj")

        assert result == []

    def test_get_insights_by_category(self):
        """Test filtering insights by category."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        insights_data = [
            {"content": "Req 1", "category": "requirement", "confidence": 0.9},
            {"content": "Req 2", "category": "requirement", "confidence": 0.85},
            {"content": "Risk 1", "category": "risk", "confidence": 0.8},
        ]
        mock_project.insights = insights_data
        mock_db.load_project.return_value = mock_project

        repo = InsightRepository(mock_db)
        result = repo.get_insights_by_category("test_proj", "requirement")

        assert len(result) == 2
        assert all(i["category"] == "requirement" for i in result)

    def test_get_high_confidence_insights(self):
        """Test filtering insights by confidence threshold."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        insights_data = [
            {"content": "High 1", "category": "requirement", "confidence": 0.95},
            {"content": "High 2", "category": "risk", "confidence": 0.85},
            {"content": "Low 1", "category": "requirement", "confidence": 0.7},
        ]
        mock_project.insights = insights_data
        mock_db.load_project.return_value = mock_project

        repo = InsightRepository(mock_db)
        result = repo.get_high_confidence_insights("test_proj", min_confidence=0.8)

        assert len(result) == 2
        assert all(i["confidence"] >= 0.8 for i in result)

    def test_get_insight_statistics(self):
        """Test calculating insight statistics."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        insights_data = [
            {"content": "Req 1", "category": "requirement", "confidence": 0.9},
            {"content": "Req 2", "category": "requirement", "confidence": 0.8},
            {"content": "Risk 1", "category": "risk", "confidence": 0.85},
        ]
        mock_project.insights = insights_data
        mock_db.load_project.return_value = mock_project

        repo = InsightRepository(mock_db)
        stats = repo.get_insight_statistics("test_proj")

        assert stats["total_insights"] == 3
        assert stats["by_category"]["requirement"] == 2
        assert stats["by_category"]["risk"] == 1
        assert pytest.approx(stats["avg_confidence"], rel=1e-2) == 0.85

    def test_clear_insights(self):
        """Test clearing all insights for project."""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.insights = [{"content": "Test", "category": "requirement"}]
        mock_db.load_project.return_value = mock_project

        repo = InsightRepository(mock_db)
        result = repo.clear_insights("test_proj")

        assert result is True
        assert mock_project.insights == []
        assert mock_db.save_project.called


class TestInsightServiceInitialization:
    """Test InsightService initialization."""

    def test_service_initialization(self):
        """Test service initializes with config and database."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)

        assert service.config is mock_config
        assert service.repository is not None
        assert isinstance(service.repository, InsightRepository)

    def test_service_has_logger(self):
        """Test service has logging configured."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)

        assert isinstance(service.logger, logging.Logger)

    def test_service_default_categories(self):
        """Test service initializes with default categories."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)

        assert "requirement" in service.default_categories
        assert "architecture" in service.default_categories
        assert "constraint" in service.default_categories
        assert "risk" in service.default_categories
        assert "opportunity" in service.default_categories
        assert "dependency" in service.default_categories


class TestInsightServiceAnalysis:
    """Test InsightService analysis methods."""

    def test_analyze_insights_success(self):
        """Test analyzing insights with categorization and confidence."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)

        insights_dict = {
            "requirements": "System must support 10k concurrent users with minimal latency",
            "architecture": "Use microservices pattern with event-driven components",
            "risks": "Database scalability could become a bottleneck",
        }

        result = service.analyze_insights("test_proj", insights_dict)

        assert result["status"] == "success"
        assert result["analyzed"] == 3
        assert len(result["insights"]) == 3

        # Check categorization
        categories = [i["category"] for i in result["insights"]]
        assert "requirement" in categories
        assert "architecture" in categories
        assert "risk" in categories

    def test_analyze_insights_empty(self):
        """Test analyzing empty insights dict."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)
        result = service.analyze_insights("test_proj", {})

        assert result["status"] == "success"
        assert result["analyzed"] == 0
        assert result["insights"] == []

    def test_categorize_insight_requirement(self):
        """Test categorizing requirement insights."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()
        service = InsightService(mock_config, mock_db)

        assert service._categorize_insight("requirements") == "requirement"
        assert service._categorize_insight("feature_spec") == "requirement"
        assert service._categorize_insight("system_features") == "requirement"

    def test_categorize_insight_architecture(self):
        """Test categorizing architecture insights."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()
        service = InsightService(mock_config, mock_db)

        assert service._categorize_insight("architecture") == "architecture"
        assert service._categorize_insight("design_pattern") == "architecture"

    def test_categorize_insight_risk(self):
        """Test categorizing risk insights."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()
        service = InsightService(mock_config, mock_db)

        assert service._categorize_insight("risks") == "risk"
        assert service._categorize_insight("issues") == "risk"

    def test_calculate_confidence_short_content(self):
        """Test confidence calculation for short content."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()
        service = InsightService(mock_config, mock_db)

        # Short content should have lower confidence
        confidence = service._calculate_confidence("Short")
        assert 0.5 < confidence < 0.7

    def test_calculate_confidence_long_content(self):
        """Test confidence calculation for long content."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()
        service = InsightService(mock_config, mock_db)

        # Long content should approach 0.95
        long_content = " ".join(["word"] * 150)
        confidence = service._calculate_confidence(long_content)
        assert confidence > 0.90


class TestInsightServiceStorage:
    """Test InsightService storage operations."""

    def test_store_insights_success(self):
        """Test storing analyzed insights."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)
        service.repository.add_insight = MagicMock(return_value=True)

        insights = [
            {
                "content": "Requirement 1",
                "category": "requirement",
                "confidence": 0.9,
                "metadata": {"source": "analysis"},
            },
            {
                "content": "Risk 1",
                "category": "risk",
                "confidence": 0.85,
                "metadata": {},
            },
        ]

        result = service.store_insights("test_proj", insights)

        assert result["status"] == "success"
        assert result["stored"] == 2
        assert result["total"] == 2
        assert service.repository.add_insight.call_count == 2

    def test_store_insights_partial_failure(self):
        """Test storing insights with partial failures."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)
        # First call succeeds, second fails
        service.repository.add_insight = MagicMock(side_effect=[True, False])

        insights = [
            {"content": "Insight 1", "category": "requirement", "confidence": 0.9},
            {"content": "Insight 2", "category": "risk", "confidence": 0.85},
        ]

        result = service.store_insights("test_proj", insights)

        assert result["status"] == "success"
        assert result["stored"] == 1
        assert result["total"] == 2


class TestInsightServiceRetrieval:
    """Test InsightService retrieval operations."""

    def test_get_project_insights_success(self):
        """Test retrieving project insights with statistics."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)

        insights_data = [
            {"content": "Req 1", "category": "requirement", "confidence": 0.9},
            {"content": "Risk 1", "category": "risk", "confidence": 0.8},
        ]
        stats_data = {
            "total_insights": 2,
            "by_category": {"requirement": 1, "risk": 1},
            "avg_confidence": 0.85,
        }

        service.repository.get_project_insights = MagicMock(return_value=insights_data)
        service.repository.get_insight_statistics = MagicMock(return_value=stats_data)

        result = service.get_project_insights("test_proj")

        assert result["status"] == "success"
        assert result["total"] == 2
        assert result["insights"] == insights_data
        assert result["statistics"] == stats_data

    def test_get_insights_by_category_success(self):
        """Test retrieving insights filtered by category."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)

        requirements = [
            {"content": "Req 1", "category": "requirement", "confidence": 0.9},
            {"content": "Req 2", "category": "requirement", "confidence": 0.85},
        ]

        service.repository.get_insights_by_category = MagicMock(return_value=requirements)

        result = service.get_insights_by_category("test_proj", "requirement")

        assert result["status"] == "success"
        assert result["category"] == "requirement"
        assert result["count"] == 2
        assert result["insights"] == requirements


class TestInsightServiceRecommendations:
    """Test InsightService recommendation generation."""

    def test_generate_recommendations_success(self):
        """Test generating recommendations from high-confidence insights."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)

        high_conf_insights = [
            {"content": "Req 1", "category": "requirement", "confidence": 0.95},
            {"content": "Req 2", "category": "requirement", "confidence": 0.92},
            {"content": "Risk 1", "category": "risk", "confidence": 0.88},
            {"content": "Risk 2", "category": "risk", "confidence": 0.85},
        ]

        service.repository.get_project_insights = MagicMock(return_value=[])
        service.repository.get_high_confidence_insights = MagicMock(
            return_value=high_conf_insights
        )

        result = service.generate_recommendations("test_proj")

        assert result["status"] == "success"
        assert result["count"] == 2

        # Should have recommendations for requirement and risk (both have 2+ insights)
        recommendations = result["recommendations"]
        categories = [r["category"] for r in recommendations]
        assert "requirement" in categories
        assert "risk" in categories

        # Check recommendation structure
        for rec in recommendations:
            assert "category" in rec
            assert "priority" in rec
            assert "insight_count" in rec
            assert "recommendation" in rec

    def test_calculate_priority_high(self):
        """Test priority calculation for high confidence insights."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()
        service = InsightService(mock_config, mock_db)

        insights = [
            {"confidence": 0.95},
            {"confidence": 0.92},
            {"confidence": 0.88},
        ]

        priority = service._calculate_priority(insights)
        assert priority == "high"

    def test_calculate_priority_medium(self):
        """Test priority calculation for medium confidence insights."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()
        service = InsightService(mock_config, mock_db)

        insights = [
            {"confidence": 0.75},
            {"confidence": 0.70},
        ]

        priority = service._calculate_priority(insights)
        assert priority == "medium"

    def test_calculate_priority_low(self):
        """Test priority calculation for low confidence insights."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()
        service = InsightService(mock_config, mock_db)

        insights = [
            {"confidence": 0.55},
            {"confidence": 0.50},
        ]

        priority = service._calculate_priority(insights)
        assert priority == "low"

    def test_generate_recommendation_text_requirement(self):
        """Test recommendation text generation for requirements."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()
        service = InsightService(mock_config, mock_db)

        insights = [{"content": "Req 1"}, {"content": "Req 2"}]
        text = service._generate_recommendation_text("requirement", insights)

        assert "requirements" in text.lower()
        assert "2" in text

    def test_generate_recommendation_text_risk(self):
        """Test recommendation text generation for risks."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()
        service = InsightService(mock_config, mock_db)

        insights = [{"content": "Risk 1"}]
        text = service._generate_recommendation_text("risk", insights)

        assert "risk" in text.lower() or "address" in text.lower()


class TestServiceIsolation:
    """Test service isolation and architecture compliance."""

    def test_service_no_orchestrator_dependency(self):
        """Test service has no orchestrator coupling."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)

        # Should only have config, logger, and repository
        assert hasattr(service, "config")
        assert hasattr(service, "logger")
        assert hasattr(service, "repository")
        assert isinstance(service.repository, InsightRepository)

        # Should not have orchestrator or claude_client
        assert not hasattr(service, "orchestrator")
        assert not hasattr(service, "claude_client")

    def test_repository_no_service_dependency(self):
        """Test repository has no service coupling."""
        mock_db = MagicMock()
        repo = InsightRepository(mock_db)

        # Should only have database and logger
        assert hasattr(repo, "database")
        assert hasattr(repo, "logger")

        # Should not have service or orchestrator
        assert not hasattr(repo, "service")
        assert not hasattr(repo, "orchestrator")

    def test_service_uses_repository_for_data_access(self):
        """Test service delegates all data access to repository."""
        mock_config = MagicMock(spec=SocratesConfig)
        mock_db = MagicMock()

        service = InsightService(mock_config, mock_db)

        # Mock the repository
        service.repository.add_insight = MagicMock(return_value=True)
        service.repository.get_project_insights = MagicMock(return_value=[])
        service.repository.get_insights_by_category = MagicMock(return_value=[])

        # Store insights should use repository
        insights = [
            {"content": "Test", "category": "requirement", "confidence": 0.9}
        ]
        service.store_insights("proj_id", insights)
        service.repository.add_insight.assert_called_once()

        # Reset mocks for next test
        service.repository.get_project_insights.reset_mock()
        service.repository.get_insights_by_category.reset_mock()

        # Get insights should use repository
        service.get_project_insights("proj_id")
        assert service.repository.get_project_insights.call_count >= 1

        # Get by category should use repository
        service.repository.get_insights_by_category.reset_mock()
        service.get_insights_by_category("proj_id", "requirement")
        service.repository.get_insights_by_category.assert_called_once()
