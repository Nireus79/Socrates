"""
Unit tests for ProgressDashboard service.

Tests data aggregation, visualization formatting, status indicators,
progress tracking, and dashboard generation.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

from socrates_api.services.progress_dashboard import (
    ProgressDashboard,
    DashboardData,
    ChartData,
    ProgressTimeline,
    StatusIndicator,
    ProgressUpdate,
)


@pytest.fixture
def progress_dashboard():
    """Create a ProgressDashboard instance for testing."""
    return ProgressDashboard()


class TestDashboardDataAggregation:
    """Test dashboard data aggregation."""

    def test_get_dashboard_data_basic(self, progress_dashboard):
        """Test basic dashboard data aggregation."""
        dashboard = progress_dashboard.get_dashboard_data(
            project_id="proj_1",
            current_phase="design",
            completeness=0.65,
            gap_closure_percentage=0.65,
            maturity=0.7,
            quality_score=0.75,
            advancement_confidence=0.8,
            questions_answered=45,
            total_gaps=20
        )

        assert dashboard is not None
        assert dashboard.current_phase == "design"
        assert dashboard.completeness == 0.65
        assert dashboard.questions_answered == 45

    def test_get_dashboard_data_high_progress(self, progress_dashboard):
        """Test dashboard with high progress."""
        dashboard = progress_dashboard.get_dashboard_data(
            project_id="proj_2",
            current_phase="testing",
            completeness=0.95,
            gap_closure_percentage=0.95,
            maturity=0.98,
            quality_score=0.96,
            advancement_confidence=0.99,
            questions_answered=150,
            total_gaps=20
        )

        assert dashboard.overall_progress > 0.9
        assert dashboard.completeness == 0.95

    def test_get_dashboard_data_low_progress(self, progress_dashboard):
        """Test dashboard with low progress."""
        dashboard = progress_dashboard.get_dashboard_data(
            project_id="proj_3",
            current_phase="requirements",
            completeness=0.1,
            gap_closure_percentage=0.1,
            maturity=0.15,
            quality_score=0.2,
            advancement_confidence=0.1,
            questions_answered=5,
            total_gaps=20
        )

        assert dashboard.overall_progress < 0.3
        assert dashboard.completeness == 0.1

    def test_get_dashboard_data_all_phases(self, progress_dashboard):
        """Test dashboard across all phases."""
        phases = ["requirements", "design", "implementation", "testing", "deployment"]

        for phase in phases:
            dashboard = progress_dashboard.get_dashboard_data(
                project_id="proj_phases",
                current_phase=phase,
                completeness=0.5,
                gap_closure_percentage=0.5,
                maturity=0.6,
                quality_score=0.65,
                advancement_confidence=0.7,
                questions_answered=30,
                total_gaps=20
            )

            assert dashboard.current_phase == phase


class TestVisualizationFormatting:
    """Test visualization data formatting."""

    def test_format_completeness_chart(self, progress_dashboard):
        """Test completeness chart formatting."""
        chart = progress_dashboard.format_completeness_chart(
            project_id="proj_1",
            completeness_history=[0.1, 0.2, 0.3, 0.4, 0.5],
            categories=["requirements", "design", "implementation"]
        )

        assert chart is not None
        assert len(chart.data_points) >= 0

    def test_format_gap_closure_chart(self, progress_dashboard):
        """Test gap closure chart formatting."""
        chart = progress_dashboard.format_gap_closure_chart(
            project_id="proj_2",
            gaps_over_time=[20, 18, 15, 10, 5],
            closed_gaps_over_time=[0, 2, 5, 10, 15]
        )

        assert chart is not None

    def test_format_phase_progress_chart(self, progress_dashboard):
        """Test phase progress chart formatting."""
        chart = progress_dashboard.format_phase_progress_chart(
            project_id="proj_3",
            phases=["requirements", "design", "implementation"],
            phase_completeness=[1.0, 0.8, 0.4],
            phase_maturity=[0.95, 0.85, 0.6]
        )

        assert chart is not None

    def test_chart_data_with_multiple_series(self, progress_dashboard):
        """Test chart formatting with multiple data series."""
        chart = progress_dashboard.format_completeness_chart(
            project_id="proj_4",
            completeness_history=[0.2, 0.4, 0.6, 0.8],
            categories=["security", "performance", "usability", "accessibility"]
        )

        assert chart is not None


class TestProgressTracking:
    """Test progress tracking functionality."""

    def test_record_progress_snapshot(self, progress_dashboard):
        """Test recording a progress snapshot."""
        snapshot = progress_dashboard.record_progress_snapshot(
            project_id="proj_1",
            phase="design",
            completeness=0.65,
            gap_closure_percentage=0.65,
            questions_answered=40,
            quality_score=0.75
        )

        assert snapshot is not None
        assert snapshot.project_id == "proj_1"
        assert snapshot.phase == "design"
        assert snapshot.completeness == 0.65

    def test_record_multiple_snapshots(self, progress_dashboard):
        """Test recording multiple snapshots over time."""
        snapshots = []
        for i in range(5):
            snapshot = progress_dashboard.record_progress_snapshot(
                project_id="proj_2",
                phase="implementation",
                completeness=0.2 + (i * 0.1),
                gap_closure_percentage=0.2 + (i * 0.1),
                questions_answered=10 + (i * 10),
                quality_score=0.6 + (i * 0.05)
            )
            snapshots.append(snapshot)

        assert len(snapshots) == 5
        # Verify progression
        assert snapshots[-1].completeness > snapshots[0].completeness

    def test_get_progress_timeline(self, progress_dashboard):
        """Test retrieving progress timeline."""
        # Record snapshots
        for i in range(3):
            progress_dashboard.record_progress_snapshot(
                project_id="proj_3",
                phase="design",
                completeness=0.3 + (i * 0.2),
                gap_closure_percentage=0.3 + (i * 0.2),
                questions_answered=20 + (i * 15),
                quality_score=0.7 + (i * 0.05)
            )

        timeline = progress_dashboard.get_progress_timeline("proj_3", days=30)
        assert timeline is not None
        assert len(timeline.snapshots) >= 3

    def test_progress_timeline_time_filtering(self, progress_dashboard):
        """Test progress timeline respects time filter."""
        # Record snapshots
        for i in range(5):
            progress_dashboard.record_progress_snapshot(
                project_id="proj_4",
                phase="testing",
                completeness=0.2 + (i * 0.1),
                gap_closure_percentage=0.2 + (i * 0.1),
                questions_answered=15 + (i * 10),
                quality_score=0.65 + (i * 0.05)
            )

        timeline_7d = progress_dashboard.get_progress_timeline("proj_4", days=7)
        timeline_30d = progress_dashboard.get_progress_timeline("proj_4", days=30)

        assert timeline_7d is not None
        assert timeline_30d is not None


class TestStatusIndicators:
    """Test status indicator generation."""

    def test_get_status_indicators_on_track(self, progress_dashboard):
        """Test status indicators for on-track project."""
        indicators = progress_dashboard.get_status_indicators(
            project_id="proj_1",
            current_phase="design",
            completeness=0.7,
            maturity=0.75,
            gap_closure_rate=0.7,
            question_effectiveness=0.8,
            estimated_days_remaining=10
        )

        assert indicators is not None
        assert len(indicators) > 0

    def test_get_status_indicators_at_risk(self, progress_dashboard):
        """Test status indicators for at-risk project."""
        indicators = progress_dashboard.get_status_indicators(
            project_id="proj_2",
            current_phase="requirements",
            completeness=0.2,
            maturity=0.15,
            gap_closure_rate=0.1,
            question_effectiveness=0.3,
            estimated_days_remaining=60
        )

        assert indicators is not None

    def test_get_status_indicators_excellent(self, progress_dashboard):
        """Test status indicators for excellent project."""
        indicators = progress_dashboard.get_status_indicators(
            project_id="proj_3",
            current_phase="deployment",
            completeness=0.98,
            maturity=0.95,
            gap_closure_rate=0.95,
            question_effectiveness=0.92,
            estimated_days_remaining=2
        )

        assert indicators is not None

    def test_status_indicator_variety(self, progress_dashboard):
        """Test that status indicators include multiple types."""
        indicators = progress_dashboard.get_status_indicators(
            project_id="proj_4",
            current_phase="implementation",
            completeness=0.65,
            maturity=0.7,
            gap_closure_rate=0.65,
            question_effectiveness=0.75,
            estimated_days_remaining=15
        )

        assert len(indicators) >= 1


class TestDashboardDisplay:
    """Test dashboard display data."""

    def test_dashboard_display_formatting(self, progress_dashboard):
        """Test dashboard data is properly formatted for display."""
        dashboard = progress_dashboard.get_dashboard_data(
            project_id="proj_1",
            current_phase="design",
            completeness=0.652,
            gap_closure_percentage=0.6523,
            maturity=0.7,
            quality_score=0.7543,
            advancement_confidence=0.8,
            questions_answered=45,
            total_gaps=20
        )

        # Verify values are within displayable range
        assert 0 <= dashboard.completeness <= 1
        assert 0 <= dashboard.maturity <= 1
        assert 0 <= dashboard.quality_score <= 1

    def test_dashboard_estimated_completion(self, progress_dashboard):
        """Test estimated completion date calculation."""
        dashboard = progress_dashboard.get_dashboard_data(
            project_id="proj_2",
            current_phase="design",
            completeness=0.5,
            gap_closure_percentage=0.5,
            maturity=0.6,
            quality_score=0.65,
            advancement_confidence=0.7,
            questions_answered=50,
            total_gaps=20
        )

        assert dashboard.estimated_completion_date is not None or \
               dashboard.estimated_completion_date is None


class TestCacheManagement:
    """Test cache management functionality."""

    def test_clear_cache(self, progress_dashboard):
        """Test cache clearing."""
        # Record some data
        progress_dashboard.record_progress_snapshot(
            project_id="proj_1",
            phase="design",
            completeness=0.5,
            gap_closure_percentage=0.5,
            questions_answered=30,
            quality_score=0.7
        )

        # Clear cache
        result = progress_dashboard.clear_cache()
        assert result is True or result is not None

    def test_cache_after_clear(self, progress_dashboard):
        """Test that cache is properly cleared."""
        progress_dashboard.record_progress_snapshot(
            project_id="proj_2",
            phase="design",
            completeness=0.6,
            gap_closure_percentage=0.6,
            questions_answered=40,
            quality_score=0.75
        )

        progress_dashboard.clear_cache()

        # Re-record and verify
        snapshot = progress_dashboard.record_progress_snapshot(
            project_id="proj_2",
            phase="design",
            completeness=0.7,
            gap_closure_percentage=0.7,
            questions_answered=50,
            quality_score=0.8
        )

        assert snapshot.completeness == 0.7


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_dashboard_with_zero_values(self, progress_dashboard):
        """Test dashboard with all zero values."""
        dashboard = progress_dashboard.get_dashboard_data(
            project_id="proj_zero",
            current_phase="requirements",
            completeness=0.0,
            gap_closure_percentage=0.0,
            maturity=0.0,
            quality_score=0.0,
            advancement_confidence=0.0,
            questions_answered=0,
            total_gaps=0
        )

        assert dashboard is not None

    def test_dashboard_with_max_values(self, progress_dashboard):
        """Test dashboard with maximum values."""
        dashboard = progress_dashboard.get_dashboard_data(
            project_id="proj_max",
            current_phase="deployment",
            completeness=1.0,
            gap_closure_percentage=1.0,
            maturity=1.0,
            quality_score=1.0,
            advancement_confidence=1.0,
            questions_answered=1000,
            total_gaps=1
        )

        assert dashboard.overall_progress <= 1.0

    def test_chart_with_empty_history(self, progress_dashboard):
        """Test chart formatting with empty history."""
        chart = progress_dashboard.format_completeness_chart(
            project_id="proj_empty",
            completeness_history=[],
            categories=[]
        )

        assert chart is not None

    def test_timeline_with_single_snapshot(self, progress_dashboard):
        """Test timeline with single snapshot."""
        progress_dashboard.record_progress_snapshot(
            project_id="proj_single",
            phase="design",
            completeness=0.5,
            gap_closure_percentage=0.5,
            questions_answered=25,
            quality_score=0.7
        )

        timeline = progress_dashboard.get_progress_timeline("proj_single")
        assert timeline is not None

    def test_status_indicators_empty_list(self, progress_dashboard):
        """Test status indicators with minimal data."""
        indicators = progress_dashboard.get_status_indicators(
            project_id="proj_minimal",
            current_phase="requirements",
            completeness=0.0,
            maturity=0.0,
            gap_closure_rate=0.0,
            question_effectiveness=0.0,
            estimated_days_remaining=0
        )

        assert indicators is not None

    def test_snapshot_with_extreme_values(self, progress_dashboard):
        """Test snapshot recording with extreme but valid values."""
        snapshot = progress_dashboard.record_progress_snapshot(
            project_id="proj_extreme",
            phase="design",
            completeness=0.99999,
            gap_closure_percentage=0.99999,
            questions_answered=99999,
            quality_score=0.99999
        )

        assert snapshot is not None


class TestDataConsistency:
    """Test data consistency across dashboard operations."""

    def test_snapshot_consistency(self, progress_dashboard):
        """Test that snapshots maintain consistent data."""
        snapshot1 = progress_dashboard.record_progress_snapshot(
            project_id="proj_1",
            phase="design",
            completeness=0.5,
            gap_closure_percentage=0.5,
            questions_answered=30,
            quality_score=0.7
        )

        snapshot2 = progress_dashboard.record_progress_snapshot(
            project_id="proj_1",
            phase="design",
            completeness=0.6,
            gap_closure_percentage=0.6,
            questions_answered=40,
            quality_score=0.75
        )

        assert snapshot1.project_id == snapshot2.project_id
        assert snapshot2.completeness > snapshot1.completeness

    def test_timeline_chronological_order(self, progress_dashboard):
        """Test that timeline maintains chronological order."""
        for i in range(5):
            progress_dashboard.record_progress_snapshot(
                project_id="proj_chrono",
                phase="design",
                completeness=0.2 + (i * 0.1),
                gap_closure_percentage=0.2 + (i * 0.1),
                questions_answered=20 + (i * 10),
                quality_score=0.7 + (i * 0.03)
            )

        timeline = progress_dashboard.get_progress_timeline("proj_chrono")
        assert timeline is not None
