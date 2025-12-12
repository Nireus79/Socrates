"""
Tests for Learning Engine - User behavior and question effectiveness tracking.

Tests cover:
- Question effectiveness tracking
- Behavior pattern recognition
- Learning recommendations
- User progress tracking
"""

import datetime

import pytest

from socratic_system.models import (
    ProjectContext,
    QuestionEffectiveness,
    UserBehaviorPattern,
)


@pytest.fixture
def sample_qa_events():
    """Create sample Q&A events for testing."""
    return [
        {
            "question": "What are your goals?",
            "response": "Build a web app",
            "timestamp": datetime.datetime.now(),
            "effectiveness": 0.8,
        },
        {
            "question": "What tech stack?",
            "response": "Python and Django",
            "timestamp": datetime.datetime.now(),
            "effectiveness": 0.9,
        },
        {
            "question": "What constraints?",
            "response": "Time and budget",
            "timestamp": datetime.datetime.now(),
            "effectiveness": 0.7,
        },
    ]


@pytest.fixture
def sample_project():
    """Create a sample project with learning data."""
    return ProjectContext(
        project_id="proj-learn",
        name="Learning Project",
        owner="testuser",
        collaborators=[],
        goals="Test learning",
        requirements=[],
        tech_stack=[],
        constraints=[],
        team_structure="individual",
        language_preferences="python",
        deployment_target="local",
        code_style="documented",
        phase="discovery",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )


class TestQuestionEffectiveness:
    """Tests for question effectiveness tracking."""

    def test_create_effectiveness_record(self):
        """Test creating question effectiveness record."""
        effectiveness = QuestionEffectiveness(
            id="eff-1",
            user_id="testuser",
            question_template_id="qt-1",
            times_used=5,
            positive_responses=4,
            negative_responses=1,
            effectiveness_score=0.8,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        assert effectiveness.id == "eff-1"
        assert effectiveness.times_used == 5
        assert effectiveness.effectiveness_score == 0.8

    def test_effectiveness_score_calculation(self):
        """Test effectiveness score calculation."""
        effectiveness = QuestionEffectiveness(
            id="eff-2",
            user_id="user1",
            question_template_id="qt-2",
            times_used=10,
            positive_responses=9,
            negative_responses=1,
            effectiveness_score=0.9,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        # Score should be positive_responses / times_used
        expected_score = 9 / 10
        assert abs(effectiveness.effectiveness_score - expected_score) < 0.01

    def test_zero_usage_effectiveness(self):
        """Test effectiveness with zero usage."""
        effectiveness = QuestionEffectiveness(
            id="eff-3",
            user_id="user2",
            question_template_id="qt-3",
            times_used=0,
            positive_responses=0,
            negative_responses=0,
            effectiveness_score=0.0,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        assert effectiveness.times_used == 0
        assert effectiveness.effectiveness_score == 0.0

    def test_perfect_effectiveness(self):
        """Test perfect effectiveness (all positive responses)."""
        effectiveness = QuestionEffectiveness(
            id="eff-4",
            user_id="user3",
            question_template_id="qt-4",
            times_used=5,
            positive_responses=5,
            negative_responses=0,
            effectiveness_score=1.0,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        assert effectiveness.effectiveness_score == 1.0


class TestBehaviorPatterns:
    """Tests for user behavior pattern recognition."""

    def test_create_behavior_pattern(self):
        """Test creating behavior pattern record."""
        pattern = UserBehaviorPattern(
            id="pat-1",
            user_id="testuser",
            pattern_type="quick_responder",
            frequency=10,
            last_observed=datetime.datetime.now(),
            metadata={"avg_response_time": 2.5},
            learned_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        assert pattern.id == "pat-1"
        assert pattern.pattern_type == "quick_responder"
        assert pattern.frequency == 10

    def test_pattern_with_metadata(self):
        """Test behavior pattern with metadata."""
        metadata = {
            "avg_response_time": 3.2,
            "typical_response_length": "medium",
            "confidence": 0.85,
        }

        pattern = UserBehaviorPattern(
            id="pat-2",
            user_id="user1",
            pattern_type="thorough_responder",
            frequency=7,
            last_observed=datetime.datetime.now(),
            metadata=metadata,
            learned_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        assert pattern.metadata["avg_response_time"] == 3.2
        assert pattern.metadata["confidence"] == 0.85

    def test_pattern_types(self):
        """Test different behavior pattern types."""
        pattern_types = [
            "quick_responder",
            "thorough_responder",
            "collaborative",
            "independent",
            "questioning",
        ]

        for ptype in pattern_types:
            pattern = UserBehaviorPattern(
                id=f"pat-{ptype}",
                user_id="user",
                pattern_type=ptype,
                frequency=5,
                last_observed=datetime.datetime.now(),
                metadata={},
                learned_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            )

            assert pattern.pattern_type == ptype

    def test_pattern_frequency_tracking(self):
        """Test pattern frequency increases with observation."""
        pattern = UserBehaviorPattern(
            id="pat-3",
            user_id="user2",
            pattern_type="test_pattern",
            frequency=1,
            last_observed=datetime.datetime.now(),
            metadata={},
            learned_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        # Simulate observing pattern multiple times
        initial_freq = pattern.frequency
        pattern.frequency += 4

        assert pattern.frequency == initial_freq + 4


class TestLearningData:
    """Tests for learning data management."""

    def test_qa_event_tracking(self, sample_qa_events):
        """Test tracking Q&A events."""
        assert len(sample_qa_events) == 3

        # Verify event structure
        for event in sample_qa_events:
            assert "question" in event
            assert "response" in event
            assert "timestamp" in event
            assert "effectiveness" in event

    def test_event_effectiveness_scores(self, sample_qa_events):
        """Test effectiveness scores in Q&A events."""
        effectiveness_scores = [e["effectiveness"] for e in sample_qa_events]

        assert len(effectiveness_scores) == 3
        assert all(0 <= score <= 1 for score in effectiveness_scores)
        assert sum(effectiveness_scores) / len(effectiveness_scores) > 0.7

    def test_user_response_patterns(self, sample_qa_events):
        """Test analyzing user response patterns."""
        responses = [e["response"] for e in sample_qa_events]

        assert len(responses) == 3
        assert all(isinstance(r, str) for r in responses)
        assert all(len(r) > 0 for r in responses)


class TestLearningIntegration:
    """Integration tests for learning system."""

    def test_effectiveness_tracking_workflow(self):
        """Test effectiveness tracking workflow."""
        # Create effectiveness record
        eff = QuestionEffectiveness(
            id="workflow-1",
            user_id="user",
            question_template_id="qt",
            times_used=3,
            positive_responses=2,
            negative_responses=1,
            effectiveness_score=0.67,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        assert eff.effectiveness_score > 0.6

    def test_pattern_recognition_workflow(self):
        """Test pattern recognition workflow."""
        # Observe pattern multiple times
        pattern = UserBehaviorPattern(
            id="workflow-2",
            user_id="user",
            pattern_type="collaborative",
            frequency=0,
            last_observed=None,
            metadata={},
            learned_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        # Simulate observations
        for _i in range(5):
            pattern.frequency += 1
            pattern.last_observed = datetime.datetime.now()

        assert pattern.frequency == 5
        assert pattern.last_observed is not None

    def test_learning_improvement_tracking(self):
        """Test tracking learning improvements."""
        # Initial state
        eff1 = QuestionEffectiveness(
            id="improve-1",
            user_id="user",
            question_template_id="qt",
            times_used=10,
            positive_responses=5,
            negative_responses=5,
            effectiveness_score=0.5,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        # Improved state
        eff2 = QuestionEffectiveness(
            id="improve-2",
            user_id="user",
            question_template_id="qt",
            times_used=20,
            positive_responses=18,
            negative_responses=2,
            effectiveness_score=0.9,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        # Should show improvement
        assert eff2.effectiveness_score > eff1.effectiveness_score


class TestLearningEdgeCases:
    """Tests for edge cases in learning system."""

    def test_effectiveness_with_large_values(self):
        """Test effectiveness with large usage numbers."""
        eff = QuestionEffectiveness(
            id="large-1",
            user_id="user",
            question_template_id="qt",
            times_used=10000,
            positive_responses=9500,
            negative_responses=500,
            effectiveness_score=0.95,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        assert eff.times_used == 10000
        assert eff.effectiveness_score == 0.95

    def test_pattern_with_empty_metadata(self):
        """Test pattern with empty metadata."""
        pattern = UserBehaviorPattern(
            id="empty-meta",
            user_id="user",
            pattern_type="test",
            frequency=5,
            last_observed=datetime.datetime.now(),
            metadata={},
            learned_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        assert pattern.metadata == {}

    def test_multiple_patterns_same_user(self):
        """Test user with multiple patterns."""
        patterns = [
            UserBehaviorPattern(
                id=f"multi-{i}",
                user_id="user",
                pattern_type=ptype,
                frequency=i,
                last_observed=datetime.datetime.now(),
                metadata={},
                learned_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            )
            for i, ptype in enumerate(["pattern1", "pattern2", "pattern3"])
        ]

        assert len(patterns) == 3
        assert all(p.user_id == "user" for p in patterns)
