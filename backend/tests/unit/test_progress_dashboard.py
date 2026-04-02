"""
Unit tests for ProgressDashboard service.

Tests data aggregation, visualization formatting, progress tracking,
and dashboard generation.
"""

import pytest

from socrates_api.services.progress_dashboard import ProgressDashboard


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


class TestVisualizationFormatting:
    """Test visualization data formatting."""

    def test_format_completeness_chart(self, progress_dashboard):
        """Test completeness chart formatting."""
        chart = progress_dashboard.format_completeness_chart(
            completeness_history=[0.1, 0.2, 0.3, 0.4, 0.5],
            timestamps=["2026-03-29T10:00:00", "2026-03-30T10:00:00",
                       "2026-03-31T10:00:00", "2026-04-01T10:00:00",
                       "2026-04-02T10:00:00"]
        )

        assert chart is not None

    def test_format_gap_closure_chart(self, progress_dashboard):
        """Test gap closure chart formatting."""
        chart = progress_dashboard.format_gap_closure_chart(
            closed_gaps_history=[0, 2, 5, 10, 15],
            total_gaps=20,
            timestamps=["2026-03-29T10:00:00", "2026-03-30T10:00:00",
                       "2026-03-31T10:00:00", "2026-04-01T10:00:00",
                       "2026-04-02T10:00:00"]
        )

        assert chart is not None

    def test_format_phase_progress_chart(self, progress_dashboard):
        """Test phase progress chart formatting."""
        chart = progress_dashboard.format_phase_progress_chart(
            phase_history={"requirements": 1.0, "design": 0.8, "implementation": 0.4}
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
            maturity=0.7,
            questions_answered=40,
            total_gaps=20,
            quality_score=0.75
        )

        assert snapshot is not None

    def test_record_multiple_snapshots(self, progress_dashboard):
        """Test recording multiple snapshots over time."""
        snapshots = []
        for i in range(5):
            snapshot = progress_dashboard.record_progress_snapshot(
                project_id="proj_2",
                phase="implementation",
                completeness=0.2 + (i * 0.1),
                gap_closure_percentage=0.2 + (i * 0.1),
                maturity=0.5 + (i * 0.05),
                questions_answered=10 + (i * 10),
                total_gaps=20,
                quality_score=0.6 + (i * 0.05)
            )
            snapshots.append(snapshot)

        assert len(snapshots) == 5

    def test_get_progress_timeline(self, progress_dashboard):
        """Test retrieving progress timeline."""
        for i in range(3):
            progress_dashboard.record_progress_snapshot(
                project_id="proj_3",
                phase="design",
                completeness=0.3 + (i * 0.2),
                gap_closure_percentage=0.3 + (i * 0.2),
                maturity=0.6 + (i * 0.1),
                questions_answered=20 + (i * 15),
                total_gaps=20,
                quality_score=0.7 + (i * 0.05)
            )

        timeline = progress_dashboard.get_progress_timeline("proj_3", days=30)
        assert timeline is not None


class TestStatusIndicators:
    """Test status indicator generation."""

    def test_get_status_indicators_on_track(self, progress_dashboard):
        """Test status indicators for on-track project."""
        from socrates_api.services.progress_dashboard import DashboardData

        dashboard = DashboardData(
            project_id="proj_1",
            current_phase="design",
            overall_progress=0.7,
            completeness=0.7,
            maturity=0.75,
            gap_closure_percentage=0.7,
            questions_answered=45,
            total_gaps=20,
            quality_score=0.8,
            advancement_confidence=0.8,
            estimated_completion_date=None
        )

        indicators = progress_dashboard.get_status_indicators(
            current_metrics=dashboard
        )

        assert indicators is not None

    def test_get_status_indicators_at_risk(self, progress_dashboard):
        """Test status indicators for at-risk project."""
        from socrates_api.services.progress_dashboard import DashboardData

        dashboard = DashboardData(
            project_id="proj_2",
            current_phase="requirements",
            overall_progress=0.2,
            completeness=0.2,
            maturity=0.15,
            gap_closure_percentage=0.1,
            questions_answered=5,
            total_gaps=20,
            quality_score=0.3,
            advancement_confidence=0.2,
            estimated_completion_date=None
        )

        indicators = progress_dashboard.get_status_indicators(
            current_metrics=dashboard
        )

        assert indicators is not None


class TestCacheManagement:
    """Test cache management functionality."""

    def test_clear_cache(self, progress_dashboard):
        """Test cache clearing."""
        result = progress_dashboard.clear_cache()
        assert result is True or result is None


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
            completeness_history=[],
            timestamps=[]
        )

        assert chart is not None
