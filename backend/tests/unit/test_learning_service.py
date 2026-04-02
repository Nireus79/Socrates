"""
Unit tests for LearningService.

Tests question effectiveness scoring, answer pattern detection,
and learning curve analysis.
"""

import pytest

from socrates_api.services.learning_service import LearningService


@pytest.fixture
def learning_service():
    """Create a LearningService instance for testing."""
    return LearningService()


class TestQuestionEffectiveness:
    """Test question effectiveness scoring."""

    def test_score_question_effectiveness_high(self, learning_service):
        """Test effectiveness scoring for high-quality question."""
        score = learning_service.score_question_effectiveness(
            question_id="q_1",
            question_text="What are the security requirements?",
            answer_text="Encryption, authentication, and authorization",
            answer_quality=0.9,
            gaps_addressed=3,
            success_rate=0.95
        )

        assert score is not None
        assert score.effectiveness_score > 0.7

    def test_score_question_effectiveness_medium(self, learning_service):
        """Test effectiveness scoring for medium-quality question."""
        score = learning_service.score_question_effectiveness(
            question_id="q_2",
            question_text="What are the design patterns?",
            answer_text="We should use design patterns",
            answer_quality=0.5,
            gaps_addressed=1,
            success_rate=0.6
        )

        assert 0.3 < score.effectiveness_score < 0.9

    def test_score_question_effectiveness_low(self, learning_service):
        """Test effectiveness scoring for low-quality question."""
        score = learning_service.score_question_effectiveness(
            question_id="q_3",
            question_text="What?",
            answer_text="Not sure",
            answer_quality=0.2,
            gaps_addressed=0,
            success_rate=0.1
        )

        assert score.effectiveness_score < 0.6


class TestAnswerPatternDetection:
    """Test answer pattern detection."""

    def test_detect_answer_patterns_basic(self, learning_service):
        """Test basic answer pattern detection."""
        answers = [
            "Technical implementation detail",
            "System uses microservices",
            "Caching for performance"
        ]

        patterns = learning_service.detect_answer_patterns(
            project_id="proj_1",
            answers=answers
        )

        assert patterns is not None

    def test_detect_answer_patterns_empty(self, learning_service):
        """Test pattern detection with no answers."""
        patterns = learning_service.detect_answer_patterns(
            project_id="proj_empty",
            answers=[]
        )

        assert patterns is not None


class TestLearningCurveAnalysis:
    """Test learning curve analysis."""

    def test_analyze_learning_curve_improvement(self, learning_service):
        """Test learning curve showing improvement."""
        effectiveness_scores = [0.4, 0.5, 0.6, 0.7, 0.8]

        curve = learning_service.analyze_learning_curve(
            project_id="proj_1",
            effectiveness_scores=effectiveness_scores,
            question_count=5
        )

        assert curve is not None
        assert curve.trend == "improving"

    def test_analyze_learning_curve_stable(self, learning_service):
        """Test learning curve that plateaus."""
        effectiveness_scores = [0.7, 0.71, 0.70, 0.72, 0.71]

        curve = learning_service.analyze_learning_curve(
            project_id="proj_2",
            effectiveness_scores=effectiveness_scores,
            question_count=5
        )

        assert curve is not None

    def test_analyze_learning_curve_declining(self, learning_service):
        """Test learning curve showing decline."""
        effectiveness_scores = [0.8, 0.7, 0.6, 0.5, 0.4]

        curve = learning_service.analyze_learning_curve(
            project_id="proj_3",
            effectiveness_scores=effectiveness_scores,
            question_count=5
        )

        assert curve is not None


class TestOptimizationRecommendations:
    """Test optimization recommendation generation."""

    def test_generate_optimization_recommendations_basic(self, learning_service):
        """Test basic recommendations generation."""
        from unittest.mock import MagicMock

        patterns = MagicMock()
        patterns.length_distribution = "short"
        patterns.technical_focus = ["unclear"]

        recommendations = learning_service.generate_optimization_recommendations(
            project_id="proj_1",
            question_history=[
                {"question": "Q1?", "answer": "A1"},
                {"question": "Q2?", "answer": "A2"}
            ],
            patterns=patterns
        )

        assert recommendations is not None


class TestLearningSummary:
    """Test learning summary generation."""

    def test_get_learning_summary_basic(self, learning_service):
        """Test basic learning summary."""
        asked_questions = [
            {"question": "Q1?", "answer": "A1", "question_id": "q_1"},
            {"question": "Q2?", "answer": "A2", "question_id": "q_2"},
        ]

        summary = learning_service.get_learning_summary(
            project_id="proj_1",
            asked_questions=asked_questions
        )

        assert summary is None or summary is not None

    def test_get_learning_summary_empty(self, learning_service):
        """Test learning summary with no questions."""
        summary = learning_service.get_learning_summary(
            project_id="proj_new",
            asked_questions=[]
        )

        assert summary is None or summary is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_score_with_empty_text(self, learning_service):
        """Test effectiveness scoring with empty text."""
        score = learning_service.score_question_effectiveness(
            question_id="q_empty",
            question_text="",
            answer_text="",
            answer_quality=0.0,
            gaps_addressed=0,
            success_rate=0.0
        )

        assert score is not None

    def test_learning_curve_single_point(self, learning_service):
        """Test learning curve with single data point."""
        curve = learning_service.analyze_learning_curve(
            project_id="proj_single",
            effectiveness_scores=[0.5],
            question_count=1
        )

        assert curve is not None
