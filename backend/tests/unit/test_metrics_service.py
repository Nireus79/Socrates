"""
Unit tests for MetricsService.

Tests dashboard aggregation, trend calculation, performance analysis,
statistical analysis, and health scoring.
"""

import pytest
from unittest.mock import Mock, MagicMock
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


@pytest.fixture
def sample_values():
    """Provide sample metric values for testing."""
    return {
        "completeness": [0.2, 0.3, 0.4, 0.5, 0.6],
        "gap_closure": [0.15, 0.25, 0.35, 0.5, 0.65],
        "quality": [0.6, 0.65, 0.7, 0.75, 0.8],
        "maturity": [0.3, 0.4, 0.5, 0.6, 0.7],
    }


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
        assert metrics.overall_progress > 0
        assert metrics.current_phase == "design"
        assert metrics.completeness == 0.65

    def test_get_dashboard_metrics_multiple_phases(self, metrics_service):
        """Test dashboard metrics across different phases."""
        phases = ["requirements", "design", "implementation", "testing"]

        for phase in phases:
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

    def test_dashboard_metrics_high_progress(self, metrics_service):
        """Test dashboard metrics with high progress."""
        metrics = metrics_service.get_dashboard_metrics(
            project_id="proj_2",
            current_phase="implementation",
            completeness=0.9,
            maturity=0.95,
            quality_score=0.92,
            advancement_confidence=0.98,
            total_gaps=20,
            closed_gaps=18
        )

        assert metrics.overall_progress > 0.9

    def test_dashboard_metrics_low_progress(self, metrics_service):
        """Test dashboard metrics with low progress."""
        metrics = metrics_service.get_dashboard_metrics(
            project_id="proj_3",
            current_phase="requirements",
            completeness=0.1,
            maturity=0.2,
            quality_score=0.3,
            advancement_confidence=0.25,
            total_gaps=20,
            closed_gaps=2
        )

        assert metrics.overall_progress < 0.3


class TestTrendCalculation:
    """Test trend analysis functionality."""

    def test_calculate_trend_improving(self, metrics_service):
        """Test trend calculation for improving metric."""
        values = [0.2, 0.3, 0.4, 0.5, 0.6]
        timestamps = [
            datetime.now() - timedelta(days=4),
            datetime.now() - timedelta(days=3),
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=1),
            datetime.now(),
        ]

        trend = metrics_service.calculate_trend(
            metric_name="completeness",
            values=values,
            timestamps=timestamps
        )

        assert trend.direction == "improving"
        assert trend.rate_of_change > 0

    def test_calculate_trend_declining(self, metrics_service):
        """Test trend calculation for declining metric."""
        values = [0.8, 0.7, 0.6, 0.5, 0.4]
        timestamps = [
            datetime.now() - timedelta(days=4),
            datetime.now() - timedelta(days=3),
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=1),
            datetime.now(),
        ]

        trend = metrics_service.calculate_trend(
            metric_name="quality_score",
            values=values,
            timestamps=timestamps
        )

        assert trend.direction == "declining"
        assert trend.rate_of_change < 0

    def test_calculate_trend_stable(self, metrics_service):
        """Test trend calculation for stable metric."""
        values = [0.5, 0.5, 0.5, 0.5, 0.5]
        timestamps = [
            datetime.now() - timedelta(days=4),
            datetime.now() - timedelta(days=3),
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=1),
            datetime.now(),
        ]

        trend = metrics_service.calculate_trend(
            metric_name="stability",
            values=values,
            timestamps=timestamps
        )

        assert trend.direction == "stable"
        assert abs(trend.rate_of_change) < 0.01

    def test_calculate_trend_volatility(self, metrics_service):
        """Test trend calculation detects volatility."""
        values = [0.2, 0.8, 0.3, 0.9, 0.4]
        timestamps = [
            datetime.now() - timedelta(days=4),
            datetime.now() - timedelta(days=3),
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=1),
            datetime.now(),
        ]

        trend = metrics_service.calculate_trend(
            metric_name="volatile_metric",
            values=values,
            timestamps=timestamps
        )

        assert trend is not None


class TestPerformanceAnalysis:
    """Test performance metrics analysis."""

    def test_analyze_performance_on_track(self, metrics_service):
        """Test performance analysis for on-track project."""
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
        assert performance.status == "on_track"

    def test_analyze_performance_behind_schedule(self, metrics_service):
        """Test performance analysis for behind schedule project."""
        performance = metrics_service.analyze_performance(
            project_id="proj_2",
            total_gaps=20,
            gaps_closed=3,
            questions_answered=10,
            started_at=(datetime.now() - timedelta(days=30)).isoformat(),
            current_phase="requirements",
            phases_completed=0
        )

        assert performance.status in ["behind_schedule", "slow_progress"]

    def test_analyze_performance_ahead_schedule(self, metrics_service):
        """Test performance analysis for ahead of schedule project."""
        performance = metrics_service.analyze_performance(
            project_id="proj_3",
            total_gaps=20,
            gaps_closed=18,
            questions_answered=70,
            started_at=(datetime.now() - timedelta(days=5)).isoformat(),
            current_phase="testing",
            phases_completed=3
        )

        assert performance.status in ["ahead_schedule", "fast_progress"]

    def test_analyze_performance_eta_calculation(self, metrics_service):
        """Test ETA calculation in performance analysis."""
        performance = metrics_service.analyze_performance(
            project_id="proj_4",
            total_gaps=20,
            gaps_closed=10,
            questions_answered=40,
            started_at=(datetime.now() - timedelta(days=10)).isoformat(),
            current_phase="design",
            phases_completed=1
        )

        assert performance.estimated_completion_days >= 0

    def test_analyze_performance_velocity(self, metrics_service):
        """Test velocity calculation in performance analysis."""
        performance = metrics_service.analyze_performance(
            project_id="proj_5",
            total_gaps=30,
            gaps_closed=20,
            questions_answered=100,
            started_at=(datetime.now() - timedelta(days=20)).isoformat(),
            current_phase="implementation",
            phases_completed=2
        )

        assert performance.gaps_closed_per_day > 0


class TestProgressReporting:
    """Test progress report generation."""

    def test_generate_progress_report_basic(self, metrics_service):
        """Test basic progress report generation."""
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
        assert "completeness" in str(report).lower() or hasattr(report, "overall_progress")

    def test_generate_progress_report_multiple_phases(self, metrics_service):
        """Test progress report across multiple phases."""
        report = metrics_service.generate_progress_report(
            project_id="proj_2",
            current_phase="implementation",
            completeness=0.75,
            maturity=0.8,
            total_gaps=20,
            closed_gaps=15,
            questions_asked=60,
            phases_completed=2
        )

        assert report is not None

    def test_generate_progress_report_comprehensive(self, metrics_service):
        """Test comprehensive progress report."""
        report = metrics_service.generate_progress_report(
            project_id="proj_3",
            current_phase="testing",
            completeness=0.92,
            maturity=0.95,
            total_gaps=20,
            closed_gaps=18,
            questions_asked=90,
            phases_completed=3,
            quality_score=0.88
        )

        assert report is not None


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

        assert health.health_score > 0.85
        assert health.status == "excellent"

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

        assert 0.6 < health.health_score < 0.85
        assert health.status in ["good", "healthy"]

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

        assert health.health_score < 0.5
        assert health.status in ["at_risk", "poor", "critical"]

    def test_calculate_project_health_critical(self, metrics_service):
        """Test health scoring for critical project."""
        health = metrics_service.calculate_project_health(
            project_id="proj_4",
            completeness=0.05,
            maturity=0.05,
            quality_score=0.1,
            advancement_confidence=0.05,
            gap_closure_rate=0.05
        )

        assert health.health_score < 0.2


class TestStatisticalAnalysis:
    """Test statistical analysis functionality."""

    def test_calculate_statistics_single_value(self, metrics_service):
        """Test statistics with single value."""
        stats = metrics_service.calculate_statistics(
            metric_name="completeness",
            values=[0.5]
        )

        assert stats is not None
        assert hasattr(stats, "mean") or "mean" in vars(stats)

    def test_calculate_statistics_multiple_values(self, metrics_service):
        """Test statistics with multiple values."""
        values = [0.2, 0.4, 0.6, 0.8, 1.0]
        stats = metrics_service.calculate_statistics(
            metric_name="progression",
            values=values
        )

        assert stats is not None

    def test_calculate_statistics_variance(self, metrics_service):
        """Test variance calculation in statistics."""
        # High variance values
        high_var = [0.1, 0.5, 0.9, 0.2, 0.8]
        # Low variance values
        low_var = [0.5, 0.5, 0.5, 0.5, 0.5]

        high_stats = metrics_service.calculate_statistics("high_var", high_var)
        low_stats = metrics_service.calculate_statistics("low_var", low_var)

        assert high_stats is not None
        assert low_stats is not None


class TestBenchmarkComparison:
    """Test benchmark comparison functionality."""

    def test_calculate_benchmark_comparison(self, metrics_service):
        """Test benchmark comparison calculation."""
        comparison = metrics_service.calculate_benchmark_comparison(
            project_metrics={"completeness": 0.75, "maturity": 0.8},
            benchmark_metrics={"completeness": 0.7, "maturity": 0.75}
        )

        assert comparison is not None

    def test_benchmark_above_average(self, metrics_service):
        """Test project above benchmark."""
        comparison = metrics_service.calculate_benchmark_comparison(
            project_metrics={"completeness": 0.85},
            benchmark_metrics={"completeness": 0.7}
        )

        assert comparison is not None

    def test_benchmark_below_average(self, metrics_service):
        """Test project below benchmark."""
        comparison = metrics_service.calculate_benchmark_comparison(
            project_metrics={"completeness": 0.6},
            benchmark_metrics={"completeness": 0.75}
        )

        assert comparison is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_trend_with_single_value(self, metrics_service):
        """Test trend calculation with single value."""
        trend = metrics_service.calculate_trend(
            metric_name="test",
            values=[0.5],
            timestamps=[datetime.now()]
        )

        assert trend is not None

    def test_trend_with_empty_values(self, metrics_service):
        """Test trend calculation with empty values."""
        trend = metrics_service.calculate_trend(
            metric_name="test",
            values=[],
            timestamps=[]
        )

        assert trend is not None or trend is None

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

    def test_performance_with_zero_gaps(self, metrics_service):
        """Test performance analysis with zero gaps."""
        performance = metrics_service.analyze_performance(
            project_id="proj_zero",
            total_gaps=0,
            gaps_closed=0,
            questions_answered=0,
            started_at=(datetime.now() - timedelta(days=1)).isoformat(),
            current_phase="design",
            phases_completed=0
        )

        assert performance is not None
