"""
Unit tests for AdvancementTracker service.

Tests gap closure tracking, completeness calculation, advancement metrics,
progress snapshots, and answer impact analysis.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from socrates_api.services.advancement_tracker import (
    AdvancementTracker,
    GapClosureRecord,
    CompletenessMetrics,
    AdvancementMetrics,
    ProgressSnapshot,
)


@pytest.fixture
def advancement_tracker():
    """Create an AdvancementTracker instance for testing."""
    return AdvancementTracker()


@pytest.fixture
def mock_database():
    """Create a mock database."""
    db = MagicMock()
    db.save_advancement_record = MagicMock(return_value=True)
    db.load_advancement_records = MagicMock(return_value=[])
    db.save_progress_snapshot = MagicMock(return_value=True)
    db.load_progress_snapshots = MagicMock(return_value=[])
    return db


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
        assert result.project_id == "proj_1"
        assert result.gap_id == "gap_security"
        assert result.closure_confidence == 0.85

    def test_record_gap_closure_high_confidence(self, advancement_tracker):
        """Test gap closure with high confidence."""
        result = advancement_tracker.record_gap_closure(
            project_id="proj_2",
            gap_id="gap_performance",
            question_id="q_456",
            answer_text="Performance optimized with caching and indexing",
            closure_confidence=0.95
        )

        assert result.closure_confidence == 0.95

    def test_record_gap_closure_low_confidence(self, advancement_tracker):
        """Test gap closure with low confidence."""
        result = advancement_tracker.record_gap_closure(
            project_id="proj_3",
            gap_id="gap_vague",
            question_id="q_789",
            answer_text="Maybe this helps",
            closure_confidence=0.3
        )

        assert result.closure_confidence == 0.3

    def test_get_gap_closure_status(self, advancement_tracker):
        """Test retrieving gap closure status."""
        # Record multiple gaps
        advancement_tracker.record_gap_closure(
            project_id="proj_1",
            gap_id="gap_1",
            question_id="q_1",
            answer_text="Answer 1",
            closure_confidence=0.8
        )
        advancement_tracker.record_gap_closure(
            project_id="proj_1",
            gap_id="gap_2",
            question_id="q_2",
            answer_text="Answer 2",
            closure_confidence=0.9
        )

        status = advancement_tracker.get_gap_closure_status("proj_1")
        assert status is not None
        assert len(status) >= 2


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

        assert metrics.overall == 1.0
        assert metrics.trend == "completed"

    def test_calculate_completeness_partial(self, advancement_tracker):
        """Test completeness with partial coverage."""
        metrics = advancement_tracker.calculate_completeness(
            project_id="proj_2",
            total_gaps=20,
            identified_gaps=18,
            closed_gaps=12,
            project_specs={"requirements": 10, "design": 10}
        )

        assert 0.5 < metrics.overall < 1.0
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
        assert metrics.trend == "not_started"

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

        assert "by_category" in vars(metrics)
        assert metrics.overall > 0


class TestAdvancementMetrics:
    """Test advancement and phase readiness prediction."""

    def test_calculate_advancement_metrics_ready(self, advancement_tracker):
        """Test advancement when ready to advance."""
        metrics = advancement_tracker.calculate_advancement_metrics(
            project_id="proj_1",
            phase="design",
            maturity=0.85,
            total_gaps=20,
            closed_gaps=15,
            question_count=50
        )

        assert metrics.phase == "design"
        assert metrics.maturity == 0.85
        assert metrics.readiness is not None

    def test_calculate_advancement_metrics_not_ready(self, advancement_tracker):
        """Test advancement when not ready to advance."""
        metrics = advancement_tracker.calculate_advancement_metrics(
            project_id="proj_2",
            phase="requirements",
            maturity=0.3,
            total_gaps=25,
            closed_gaps=3,
            question_count=10
        )

        assert metrics.maturity == 0.3
        assert metrics.readiness.get("can_advance") is False

    def test_advancement_quality_score(self, advancement_tracker):
        """Test quality score calculation."""
        metrics = advancement_tracker.calculate_advancement_metrics(
            project_id="proj_3",
            phase="implementation",
            maturity=0.75,
            total_gaps=15,
            closed_gaps=12,
            question_count=45
        )

        assert 0 <= metrics.quality_score <= 1.0
        assert metrics.quality_score > 0

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
            gap_closure_percentage=0.7,
            question_count=40,
            quality_score=0.8
        )

        assert snapshot is not None
        assert snapshot.project_id == "proj_1"
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
                gap_closure_percentage=0.5 + (i * 0.1),
                question_count=30 + (i * 10),
                quality_score=0.7 + (i * 0.05)
            )

        timeline = advancement_tracker.get_progress_timeline("proj_1")
        assert timeline is not None
        assert len(timeline.snapshots) >= 3

    def test_progress_timeline_time_range(self, advancement_tracker):
        """Test progress timeline with specific time range."""
        # Record snapshots
        for i in range(5):
            advancement_tracker.record_progress_snapshot(
                project_id="proj_2",
                phase="requirements",
                completeness=0.4 + (i * 0.1),
                gap_closure_percentage=0.4 + (i * 0.1),
                question_count=20 + (i * 5),
                quality_score=0.6 + (i * 0.05)
            )

        timeline = advancement_tracker.get_progress_timeline("proj_2", days=7)
        assert timeline is not None


class TestAnswerImpactAnalysis:
    """Test answer impact analysis and effectiveness."""

    def test_analyze_answer_impact_high_quality(self, advancement_tracker):
        """Test impact analysis for high-quality answer."""
        impact = advancement_tracker.analyze_answer_impact(
            project_id="proj_1",
            question_id="q_1",
            answer_text="Comprehensive answer with multiple aspects covered",
            gap_closure_records=[
                {"gap_id": "gap_1", "confidence": 0.9},
                {"gap_id": "gap_2", "confidence": 0.85}
            ],
            quality_score=0.9
        )

        assert impact is not None
        assert impact.quality_assessment == "high"

    def test_analyze_answer_impact_partial(self, advancement_tracker):
        """Test impact analysis for partial answer."""
        impact = advancement_tracker.analyze_answer_impact(
            project_id="proj_2",
            question_id="q_2",
            answer_text="Partial answer covering some aspects",
            gap_closure_records=[
                {"gap_id": "gap_3", "confidence": 0.6}
            ],
            quality_score=0.6
        )

        assert impact.quality_assessment in ["medium", "partial"]

    def test_analyze_answer_impact_poor(self, advancement_tracker):
        """Test impact analysis for poor quality answer."""
        impact = advancement_tracker.analyze_answer_impact(
            project_id="proj_3",
            question_id="q_3",
            answer_text="Unclear response",
            gap_closure_records=[],
            quality_score=0.2
        )

        assert impact.quality_assessment in ["low", "poor"]


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

    def test_advancement_with_negative_inputs(self, advancement_tracker):
        """Test advancement metrics handles invalid inputs gracefully."""
        # Should handle negative values by clamping
        metrics = advancement_tracker.calculate_advancement_metrics(
            project_id="proj_4",
            phase="design",
            maturity=-0.5,  # Invalid
            total_gaps=-10,  # Invalid
            closed_gaps=-5,  # Invalid
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

    def test_progress_snapshot_immutability(self, advancement_tracker):
        """Test that snapshots are immutable once recorded."""
        snapshot1 = advancement_tracker.record_progress_snapshot(
            project_id="proj_1",
            phase="design",
            completeness=0.5,
            gap_closure_percentage=0.5,
            question_count=20,
            quality_score=0.7
        )

        # Record another snapshot with different values
        snapshot2 = advancement_tracker.record_progress_snapshot(
            project_id="proj_1",
            phase="design",
            completeness=0.75,
            gap_closure_percentage=0.75,
            question_count=40,
            quality_score=0.8
        )

        # Original snapshot should still have original values
        assert snapshot1.completeness == 0.5
        assert snapshot2.completeness == 0.75
