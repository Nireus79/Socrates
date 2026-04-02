"""
Unit tests for MetricsService.

Tests dashboard aggregation, trend calculation, performance analysis,
and health scoring.
"""

import pytest
from datetime import datetime, timedelta

from socrates_api.services.metrics_service import MetricsService


@pytest.fixture
def metrics_service():
    """Create a MetricsService instance for testing."""
    return MetricsService()


class TestDashboardMetrics:
    """Test dashboard metrics aggregation."""

    def test_get_dashboard_metrics_basic(self, metrics_service):
        """Test basic dashboard metrics aggregation."""
        metrics = metrics_service.get_dashboard_metrics(
            project_id="proj_1",
            current_phase="design",
            completeness=0.65,
            maturity=0.7,
            quality_score=0.75,
            advancement_confidence=0.8,
            total_gaps=20,
            closed_gaps=13
        )

        assert metrics is not None
        assert metrics.current_phase == "design"
        assert metrics.completeness == 0.65

    def test_get_dashboard_metrics_multiple_phases(self, metrics_service):
        """Test dashboard metrics across different phases."""
        for phase in ["requirements", "design", "implementation"]:
            metrics = metrics_service.get_dashboard_metrics(
                project_id="proj_1",
                current_phase=phase,
                completeness=0.5,
                maturity=0.6,
                quality_score=0.7,
                advancement_confidence=0.8,
                total_gaps=20,
                closed_gaps=10
            )

            assert metrics.current_phase == phase

    def test_dashboard_metrics_progress_calculation(self, metrics_service):
        """Test dashboard calculates overall progress."""
        metrics = metrics_service.get_dashboard_metrics(
            project_id="proj_2",
            current_phase="implementation",
            completeness=0.8,
            maturity=0.85,
            quality_score=0.88,
            advancement_confidence=0.9,
            total_gaps=20,
            closed_gaps=16
        )

        assert metrics.overall_progress > 0.7


class TestTrendCalculation:
    """Test trend analysis functionality."""

    def test_calculate_trend_improving(self, metrics_service):
        """Test trend calculation for improving metric."""
        values = [0.2, 0.3, 0.4, 0.5, 0.6]
        timestamps = [
            datetime.now() - timedelta(days=i) for i in range(4, -1, -1)
        ]

        trend = metrics_service.calculate_trend(
            metric_name="completeness",
            values=values,
            timestamps=timestamps
        )

        assert trend is not None
        assert trend.direction == "improving"

    def test_calculate_trend_stable(self, metrics_service):
        """Test trend calculation for stable metric."""
        values = [0.5, 0.5, 0.5, 0.5, 0.5]
        timestamps = [
            datetime.now() - timedelta(days=i) for i in range(4, -1, -1)
        ]

        trend = metrics_service.calculate_trend(
            metric_name="stability",
            values=values,
            timestamps=timestamps
        )

        assert trend is not None


class TestHealthScoring:
    """Test project health scoring."""

    def test_calculate_project_health_excellent(self, metrics_service):
        """Test health scoring for excellent project."""
        health = metrics_service.calculate_project_health(
            project_id="proj_1",
            completeness=0.9,
            maturity=0.95,
            quality_score=0.92,
            advancement_confidence=0.98,
            gap_closure_rate=0.9
        )

        assert health is not None
        assert health.health_score > 0.8

    def test_calculate_project_health_good(self, metrics_service):
        """Test health scoring for good project."""
        health = metrics_service.calculate_project_health(
            project_id="proj_2",
            completeness=0.7,
            maturity=0.75,
            quality_score=0.78,
            advancement_confidence=0.8,
            gap_closure_rate=0.7
        )

        assert health is not None
        assert 0.5 < health.health_score <= 1.0

    def test_calculate_project_health_at_risk(self, metrics_service):
        """Test health scoring for at-risk project."""
        health = metrics_service.calculate_project_health(
            project_id="proj_3",
            completeness=0.3,
            maturity=0.2,
            quality_score=0.4,
            advancement_confidence=0.3,
            gap_closure_rate=0.25
        )

        assert health is not None


class TestPerformanceAnalysis:
    """Test performance metrics analysis."""

    def test_analyze_performance_basic(self, metrics_service):
        """Test basic performance analysis."""
        performance = metrics_service.analyze_performance(
            project_id="proj_1",
            total_gaps=20,
            gaps_closed=15,
            questions_answered=50,
            started_at=(datetime.now() - timedelta(days=15)).isoformat(),
            current_phase="implementation",
            phases_completed=2
        )

        assert performance is not None
        assert performance.status in ["on_track", "ahead_schedule", "behind_schedule"]

    def test_analyze_performance_eta(self, metrics_service):
        """Test ETA calculation in performance analysis."""
        performance = metrics_service.analyze_performance(
            project_id="proj_2",
            total_gaps=20,
            gaps_closed=10,
            questions_answered=40,
            started_at=(datetime.now() - timedelta(days=10)).isoformat(),
            current_phase="design",
            phases_completed=1
        )

        assert performance.estimated_completion_days >= 0


class TestStatisticalAnalysis:
    """Test statistical analysis functionality."""

    def test_calculate_statistics_basic(self, metrics_service):
        """Test statistics with basic values."""
        stats = metrics_service.calculate_statistics(
            metric_name="completeness",
            values=[0.2, 0.4, 0.6, 0.8, 1.0]
        )

        assert stats is not None


class TestProgressReporting:
    """Test progress report generation."""

    def test_generate_progress_report(self, metrics_service):
        """Test progress report generation."""
        report = metrics_service.generate_progress_report(
            project_id="proj_1",
            current_phase="design",
            completeness=0.65,
            maturity=0.7,
            total_gaps=20,
            closed_gaps=13,
            questions_asked=45
        )

        assert report is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_health_with_zero_values(self, metrics_service):
        """Test health scoring with zero values."""
        health = metrics_service.calculate_project_health(
            project_id="proj_zero",
            completeness=0.0,
            maturity=0.0,
            quality_score=0.0,
            advancement_confidence=0.0,
            gap_closure_rate=0.0
        )

        assert health is not None

    def test_health_with_max_values(self, metrics_service):
        """Test health scoring with maximum values."""
        health = metrics_service.calculate_project_health(
            project_id="proj_max",
            completeness=1.0,
            maturity=1.0,
            quality_score=1.0,
            advancement_confidence=1.0,
            gap_closure_rate=1.0
        )

        assert health.health_score <= 1.0
