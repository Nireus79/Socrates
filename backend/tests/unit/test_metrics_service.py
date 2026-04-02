"""
Unit tests for MetricsService.

Tests dashboard aggregation, trend calculation, performance analysis,
and health scoring.
"""

import pytest
from datetime import datetime, timedelta

from socrates_api.services.metrics_service import (
    MetricsService,
    DashboardMetrics,
    TrendData,
    PerformanceMetrics,
)


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
            gap_closure_count=13,
            total_gaps=20,
            questions_answered=45,
            quality_score=0.75,
            advancement_confidence=0.8
        )

        assert isinstance(metrics, DashboardMetrics)
        assert metrics.project_id == "proj_1"
        assert metrics.current_phase == "design"
        assert metrics.completeness == 0.65

    def test_get_dashboard_metrics_high_progress(self, metrics_service):
        """Test dashboard with high progress."""
        metrics = metrics_service.get_dashboard_metrics(
            project_id="proj_2",
            current_phase="testing",
            completeness=0.95,
            maturity=0.98,
            gap_closure_count=19,
            total_gaps=20,
            questions_answered=150,
            quality_score=0.96,
            advancement_confidence=0.99
        )

        assert metrics.completeness == 0.95
        assert metrics.maturity == 0.98

    def test_get_dashboard_metrics_low_progress(self, metrics_service):
        """Test dashboard with low progress."""
        metrics = metrics_service.get_dashboard_metrics(
            project_id="proj_3",
            current_phase="requirements",
            completeness=0.1,
            maturity=0.15,
            gap_closure_count=2,
            total_gaps=20,
            questions_answered=5,
            quality_score=0.2,
            advancement_confidence=0.1
        )

        assert metrics.completeness == 0.1
        assert metrics.maturity == 0.15


class TestTrendCalculation:
    """Test trend analysis functionality."""

    def test_calculate_trend_improving(self, metrics_service):
        """Test trend calculation for improving metric."""
        values = [0.2, 0.3, 0.4, 0.5, 0.6]
        timestamps = [
            (datetime.now() - timedelta(days=i)).isoformat() for i in range(4, -1, -1)
        ]

        trend = metrics_service.calculate_trend(
            metric_name="completeness",
            values=values,
            timestamps=timestamps
        )

        assert isinstance(trend, TrendData)
        assert trend.metric_name == "completeness"
        assert trend.direction == "improving"

    def test_calculate_trend_stable(self, metrics_service):
        """Test trend calculation for stable metric."""
        values = [0.5, 0.5, 0.5, 0.5, 0.5]
        timestamps = [
            (datetime.now() - timedelta(days=i)).isoformat() for i in range(4, -1, -1)
        ]

        trend = metrics_service.calculate_trend(
            metric_name="stability",
            values=values,
            timestamps=timestamps
        )

        assert trend.direction == "stable"

    def test_calculate_trend_declining(self, metrics_service):
        """Test trend calculation for declining metric."""
        values = [0.8, 0.7, 0.6, 0.5, 0.4]
        timestamps = [
            (datetime.now() - timedelta(days=i)).isoformat() for i in range(4, -1, -1)
        ]

        trend = metrics_service.calculate_trend(
            metric_name="quality",
            values=values,
            timestamps=timestamps
        )

        assert trend.direction == "declining"


class TestHealthScoring:
    """Test project health scoring."""

    def test_calculate_project_health_excellent(self, metrics_service):
        """Test health scoring for excellent project."""
        health = metrics_service.calculate_project_health(
            maturity=0.95,
            completeness=0.9,
            gap_closure_percentage=0.9,
            quality_score=0.92
        )

        assert health is not None
        assert health.get("health_score", 0) > 0.75

    def test_calculate_project_health_good(self, metrics_service):
        """Test health scoring for good project."""
        health = metrics_service.calculate_project_health(
            maturity=0.75,
            completeness=0.7,
            gap_closure_percentage=0.7,
            quality_score=0.78
        )

        assert health is not None
        assert 0.5 < health.get("health_score", 0) <= 1.0

    def test_calculate_project_health_at_risk(self, metrics_service):
        """Test health scoring for at-risk project."""
        health = metrics_service.calculate_project_health(
            maturity=0.2,
            completeness=0.3,
            gap_closure_percentage=0.25,
            quality_score=0.4
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

        assert isinstance(performance, PerformanceMetrics)
        assert performance.gaps_per_day > 0

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

        assert performance.estimated_project_duration >= 0


class TestStatisticalAnalysis:
    """Test statistical analysis functionality."""

    def test_calculate_statistics_basic(self, metrics_service):
        """Test statistics with basic values."""
        stats = metrics_service.calculate_statistics(
            values=[0.2, 0.4, 0.6, 0.8, 1.0]
        )

        assert stats is not None


class TestProgressReporting:
    """Test progress report generation."""

    def test_generate_progress_report(self, metrics_service):
        """Test progress report generation."""
        from socrates_api.services.metrics_service import DashboardMetrics, PerformanceMetrics

        dashboard = DashboardMetrics(
            project_id="proj_1",
            current_phase="design",
            completeness=0.65,
            maturity=0.7,
            gap_closure_percentage=0.65,
            questions_answered=45,
            total_gaps=20,
            quality_score=0.75,
            advancement_confidence=0.8
        )

        performance = PerformanceMetrics(
            avg_time_per_gap=1.0,
            gaps_per_day=2.0,
            questions_per_gap=3.0,
            phase_progression_rate=10.0,
            estimated_project_duration=10
        )

        report = metrics_service.generate_progress_report(
            project_id="proj_1",
            dashboard=dashboard,
            performance=performance,
            trends={}
        )

        assert report is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_health_with_zero_values(self, metrics_service):
        """Test health scoring with zero values."""
        health = metrics_service.calculate_project_health(
            maturity=0.0,
            completeness=0.0,
            gap_closure_percentage=0.0,
            quality_score=0.0
        )

        assert health is not None

    def test_health_with_max_values(self, metrics_service):
        """Test health scoring with maximum values."""
        health = metrics_service.calculate_project_health(
            maturity=1.0,
            completeness=1.0,
            gap_closure_percentage=1.0,
            quality_score=1.0
        )

        assert health.get("health_score", 0) <= 1.0

    def test_dashboard_zero_gaps(self, metrics_service):
        """Test dashboard with zero total gaps."""
        metrics = metrics_service.get_dashboard_metrics(
            project_id="proj_zero",
            current_phase="requirements",
            completeness=0.0,
            maturity=0.0,
            gap_closure_count=0,
            total_gaps=0,
            questions_answered=0,
            quality_score=0.0,
            advancement_confidence=0.0
        )

        assert metrics is not None
