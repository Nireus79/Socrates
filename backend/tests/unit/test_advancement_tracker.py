"""
Unit tests for AdvancementTracker service.

Tests gap closure tracking, completeness calculation, advancement metrics,
progress snapshots, and answer impact analysis.
"""

import pytest
from datetime import datetime

from socrates_api.services.advancement_tracker import (
    AdvancementTracker,
    GapClosureRecord,
    CompletenessMetrics,
    AdvancementMetrics,
    ProgressSnapshot,
    GapStatus,
)


@pytest.fixture
def advancement_tracker():
    """Create an AdvancementTracker instance for testing."""
    return AdvancementTracker()


class TestGapClosureRecording:
    """Test gap closure tracking functionality."""

    def test_record_gap_closure_basic(self, advancement_tracker):
        """Test basic gap closure recording."""
        result = advancement_tracker.record_gap_closure(
            project_id="proj_1",
            gap_id="gap_security",
            question_id="q_123",
            answer_text="Security measures include encryption and authentication",
            closure_confidence=0.85
        )

        assert result is not None
        assert isinstance(result, GapClosureRecord)
        assert result.gap_id == "gap_security"
        assert result.question_id == "q_123"
        assert result.closure_confidence == 0.85
        assert result.status == GapStatus.CLOSED

    def test_record_gap_closure_high_confidence(self, advancement_tracker):
        """Test gap closure with high confidence results in RESOLVED status."""
        result = advancement_tracker.record_gap_closure(
            project_id="proj_2",
            gap_id="gap_performance",
            question_id="q_456",
            answer_text="Performance optimized with caching",
            closure_confidence=0.95
        )

        assert result.closure_confidence == 0.95
        assert result.status == GapStatus.RESOLVED

    def test_record_gap_closure_medium_confidence(self, advancement_tracker):
        """Test gap closure with medium confidence (CLOSED status)."""
        result = advancement_tracker.record_gap_closure(
            project_id="proj_2",
            gap_id="gap_design",
            question_id="q_123",
            answer_text="Design patterns implemented",
            closure_confidence=0.85
        )

        assert result.status == GapStatus.CLOSED

    def test_record_gap_closure_very_low_confidence(self, advancement_tracker):
        """Test gap closure with very low confidence (OPEN status)."""
        result = advancement_tracker.record_gap_closure(
            project_id="proj_3",
            gap_id="gap_vague",
            question_id="q_789",
            answer_text="Maybe this helps",
            closure_confidence=0.3
        )

        assert result.closure_confidence == 0.3
        assert result.status == GapStatus.OPEN

    def test_record_gap_closure_partial_confidence(self, advancement_tracker):
        """Test gap closure with partial confidence (PARTIAL status)."""
        result = advancement_tracker.record_gap_closure(
            project_id="proj_3",
            gap_id="gap_partial",
            question_id="q_600",
            answer_text="Partially addresses the question",
            closure_confidence=0.6
        )

        assert result.closure_confidence == 0.6
        assert result.status == GapStatus.PARTIAL

    def test_get_gap_closure_status_single_gap(self, advancement_tracker):
        """Test retrieving gap closure status for single gap."""
        advancement_tracker.record_gap_closure(
            project_id="proj_1",
            gap_id="gap_1",
            question_id="q_1",
            answer_text="Answer 1",
            closure_confidence=0.8
        )

        status = advancement_tracker.get_gap_closure_status("proj_1", "gap_1")
        assert status is not None
        assert status["closed"] is True
        assert status["closure_confidence"] == 0.8
        assert status["status"] == GapStatus.CLOSED.value

    def test_get_gap_closure_status_multiple_attempts(self, advancement_tracker):
        """Test gap closure status with multiple closure attempts."""
        advancement_tracker.record_gap_closure(
            project_id="proj_1",
            gap_id="gap_x",
            question_id="q_1",
            answer_text="First attempt",
            closure_confidence=0.6
        )
        advancement_tracker.record_gap_closure(
            project_id="proj_1",
            gap_id="gap_x",
            question_id="q_2",
            answer_text="Second attempt",
            closure_confidence=0.9
        )

        status = advancement_tracker.get_gap_closure_status("proj_1", "gap_x")
        assert status["closure_attempts"] == 2
        assert status["successful_closures"] >= 1

    def test_get_gap_closure_status_nonexistent_gap(self, advancement_tracker):
        """Test getting status for non-existent gap."""
        status = advancement_tracker.get_gap_closure_status("proj_1", "gap_nonexistent")
        assert status["status"] == GapStatus.OPEN.value
        assert status["closed"] is False


class TestCompletenessCalculation:
    """Test specification completeness metrics."""

    def test_calculate_completeness_fully_covered(self, advancement_tracker):
        """Test completeness when all gaps are closed."""
        metrics = advancement_tracker.calculate_completeness(
            project_id="proj_1",
            total_gaps=10,
            identified_gaps=10,
            closed_gaps=10,
            project_specs={"design": 5, "implementation": 5}
        )

        assert isinstance(metrics, CompletenessMetrics)
        assert metrics.overall == 1.0

    def test_calculate_completeness_partial(self, advancement_tracker):
        """Test completeness with partial coverage."""
        metrics = advancement_tracker.calculate_completeness(
            project_id="proj_2",
            total_gaps=20,
            identified_gaps=18,
            closed_gaps=12,
            project_specs={"requirements": 10, "design": 10}
        )

        assert 0 < metrics.overall <= 1.0
        assert metrics.trend in ["improving", "stable", "declining"]

    def test_calculate_completeness_no_progress(self, advancement_tracker):
        """Test completeness with no progress."""
        metrics = advancement_tracker.calculate_completeness(
            project_id="proj_3",
            total_gaps=15,
            identified_gaps=0,
            closed_gaps=0,
            project_specs={"scope": 15}
        )

        assert metrics.overall == 0.0

    def test_completeness_by_category(self, advancement_tracker):
        """Test category-wise completeness breakdown."""
        metrics = advancement_tracker.calculate_completeness(
            project_id="proj_4",
            total_gaps=20,
            identified_gaps=20,
            closed_gaps=15,
            project_specs={
                "requirements": 5,
                "design": 5,
                "implementation": 5,
                "testing": 5
            }
        )

        assert isinstance(metrics.by_category, dict)
        assert metrics.overall > 0


class TestAdvancementMetrics:
    """Test advancement and phase readiness prediction."""

    def test_calculate_advancement_metrics(self, advancement_tracker):
        """Test advancement metrics calculation."""
        metrics = advancement_tracker.calculate_advancement_metrics(
            project_id="proj_1",
            phase="design",
            maturity=0.85,
            total_gaps=20,
            closed_gaps=15,
            question_count=50
        )

        assert isinstance(metrics, AdvancementMetrics)
        assert metrics.phase == "design"
        assert metrics.maturity == 0.85
        assert metrics.gap_closure_rate > 0

    def test_advancement_metrics_not_ready(self, advancement_tracker):
        """Test advancement metrics when not ready to advance."""
        metrics = advancement_tracker.calculate_advancement_metrics(
            project_id="proj_2",
            phase="requirements",
            maturity=0.3,
            total_gaps=25,
            closed_gaps=3,
            question_count=10
        )

        assert metrics.maturity == 0.3

    def test_advancement_quality_score(self, advancement_tracker):
        """Test quality score is calculated."""
        metrics = advancement_tracker.calculate_advancement_metrics(
            project_id="proj_3",
            phase="implementation",
            maturity=0.75,
            total_gaps=15,
            closed_gaps=12,
            question_count=45
        )

        assert 0 <= metrics.quality_score <= 1.0

    def test_advancement_gap_closure_rate(self, advancement_tracker):
        """Test gap closure rate calculation."""
        metrics = advancement_tracker.calculate_advancement_metrics(
            project_id="proj_4",
            phase="design",
            maturity=0.8,
            total_gaps=20,
            closed_gaps=16,
            question_count=60
        )

        expected_rate = 16 / 20
        assert abs(metrics.gap_closure_rate - expected_rate) < 0.01


class TestProgressSnapshots:
    """Test progress snapshot recording and retrieval."""

    def test_record_progress_snapshot(self, advancement_tracker):
        """Test recording a progress snapshot."""
        snapshot = advancement_tracker.record_progress_snapshot(
            project_id="proj_1",
            phase="design",
            completeness=0.75,
            gap_closure_count=15,
            total_gaps=20,
            maturity=0.8,
            questions_answered=40
        )

        assert snapshot is not None
        assert isinstance(snapshot, ProgressSnapshot)
        assert snapshot.phase == "design"
        assert snapshot.completeness == 0.75

    def test_get_progress_timeline(self, advancement_tracker):
        """Test retrieving progress timeline."""
        # Record multiple snapshots
        for i in range(3):
            advancement_tracker.record_progress_snapshot(
                project_id="proj_1",
                phase="design",
                completeness=0.5 + (i * 0.1),
                gap_closure_count=10 + (i * 3),
                total_gaps=20,
                maturity=0.6 + (i * 0.05),
                questions_answered=30 + (i * 10)
            )

        timeline = advancement_tracker.get_progress_timeline("proj_1")
        assert timeline is not None
        assert isinstance(timeline, list)
        assert len(timeline) >= 3

    def test_get_progress_timeline_empty(self, advancement_tracker):
        """Test progress timeline for project with no snapshots."""
        timeline = advancement_tracker.get_progress_timeline("proj_new")
        assert timeline is not None
        assert isinstance(timeline, list)
        assert len(timeline) == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_completeness_with_zero_gaps(self, advancement_tracker):
        """Test completeness calculation with zero total gaps."""
        metrics = advancement_tracker.calculate_completeness(
            project_id="proj_1",
            total_gaps=0,
            identified_gaps=0,
            closed_gaps=0,
            project_specs={}
        )

        assert metrics.overall >= 0

    def test_advancement_with_single_gap(self, advancement_tracker):
        """Test advancement metrics with single gap."""
        metrics = advancement_tracker.calculate_advancement_metrics(
            project_id="proj_2",
            phase="design",
            maturity=0.5,
            total_gaps=1,
            closed_gaps=1,
            question_count=1
        )

        assert metrics.gap_closure_rate == 1.0

    def test_gap_closure_with_empty_answer(self, advancement_tracker):
        """Test gap closure recording with empty answer."""
        result = advancement_tracker.record_gap_closure(
            project_id="proj_3",
            gap_id="gap_1",
            question_id="q_1",
            answer_text="",
            closure_confidence=0.0
        )

        assert result is not None
        assert result.status == GapStatus.OPEN

    def test_advancement_with_boundary_values(self, advancement_tracker):
        """Test advancement metrics with boundary confidence values."""
        metrics = advancement_tracker.calculate_advancement_metrics(
            project_id="proj_4",
            phase="design",
            maturity=0.0,
            total_gaps=20,
            closed_gaps=0,
            question_count=0
        )

        assert metrics is not None


class TestDataConsistency:
    """Test data consistency and integrity."""

    def test_multiple_gap_closures_same_gap(self, advancement_tracker):
        """Test recording multiple closures for same gap."""
        gap_id = "gap_1"
        project_id = "proj_1"

        record1 = advancement_tracker.record_gap_closure(
            project_id=project_id,
            gap_id=gap_id,
            question_id="q_1",
            answer_text="First attempt",
            closure_confidence=0.5
        )

        record2 = advancement_tracker.record_gap_closure(
            project_id=project_id,
            gap_id=gap_id,
            question_id="q_2",
            answer_text="Second attempt",
            closure_confidence=0.9
        )

        assert record1.gap_id == record2.gap_id
        assert record2.closure_confidence > record1.closure_confidence

    def test_progress_snapshot_ordering(self, advancement_tracker):
        """Test that snapshots are ordered chronologically."""
        project_id = "proj_1"

        snapshot1 = advancement_tracker.record_progress_snapshot(
            project_id=project_id,
            phase="design",
            completeness=0.5,
            gap_closure_count=10,
            total_gaps=20,
            maturity=0.6,
            questions_answered=25
        )

        snapshot2 = advancement_tracker.record_progress_snapshot(
            project_id=project_id,
            phase="design",
            completeness=0.75,
            gap_closure_count=15,
            total_gaps=20,
            maturity=0.8,
            questions_answered=45
        )

        assert snapshot1.timestamp <= snapshot2.timestamp
