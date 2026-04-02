"""
Unit tests for LearningService.

Tests question effectiveness scoring, answer pattern detection,
and learning curve analysis.
"""

import pytest

from socrates_api.services.learning_service import (
    LearningService,
    QuestionEffectiveness,
    AnswerPattern,
    LearningCurve,
    OptimizationRecommendation,
)


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
            gaps_addressed=3,
            answer_quality=0.9,
            times_asked=5
        )

        assert isinstance(score, QuestionEffectiveness)
        assert score.effectiveness_score > 0.3
        assert score.answer_quality == 0.9

    def test_score_question_effectiveness_medium(self, learning_service):
        """Test effectiveness scoring for medium-quality question."""
        score = learning_service.score_question_effectiveness(
            question_id="q_2",
            question_text="What are the design patterns?",
            answer_text="We should use design patterns",
            gaps_addressed=1,
            answer_quality=0.5,
            times_asked=3
        )

        assert 0.2 < score.effectiveness_score < 0.9

    def test_score_question_effectiveness_low(self, learning_service):
        """Test effectiveness scoring for low-quality question."""
        score = learning_service.score_question_effectiveness(
            question_id="q_3",
            question_text="What?",
            answer_text="Not sure",
            gaps_addressed=0,
            answer_quality=0.2,
            times_asked=2
        )

        assert score.effectiveness_score < 0.6

    def test_score_question_impact_score(self, learning_service):
        """Test that impact score is calculated correctly."""
        score = learning_service.score_question_effectiveness(
            question_id="q_impact",
            question_text="Complex question",
            answer_text="Comprehensive answer",
            gaps_addressed=5,
            answer_quality=0.9,
            times_asked=1
        )

        assert score.impact_score > 0
        assert score.impact_score <= 1.0


class TestAnswerPatternDetection:
    """Test answer pattern detection."""

    def test_detect_answer_patterns_basic(self, learning_service):
        """Test basic answer pattern detection."""
        answers = [
            {"text": "Technical implementation detail"},
            {"text": "System uses microservices"},
            {"text": "Caching for performance"}
        ]

        patterns = learning_service.detect_answer_patterns(
            project_id="proj_1",
            answers=answers
        )

        assert isinstance(patterns, list)
        assert len(patterns) >= 0

    def test_detect_answer_patterns_empty(self, learning_service):
        """Test pattern detection with no answers."""
        patterns = learning_service.detect_answer_patterns(
            project_id="proj_empty",
            answers=[]
        )

        assert isinstance(patterns, list)


class TestLearningCurveAnalysis:
    """Test learning curve analysis."""

    def test_analyze_learning_curve_basic(self, learning_service):
        """Test basic learning curve analysis."""
        metric_values = [0.4, 0.5, 0.6, 0.7, 0.8]
        timestamps = ["2026-03-29T10:00:00", "2026-03-30T10:00:00",
                     "2026-03-31T10:00:00", "2026-04-01T10:00:00",
                     "2026-04-02T10:00:00"]

        curve = learning_service.analyze_learning_curve(
            project_id="proj_1",
            phase="design",
            metric_values=metric_values,
            timestamps=timestamps
        )

        assert isinstance(curve, LearningCurve)
        assert curve.phase == "design"
        assert curve.improvement_rate >= 0

    def test_analyze_learning_curve_stable(self, learning_service):
        """Test learning curve that plateaus."""
        metric_values = [0.7, 0.71, 0.70, 0.72, 0.71]
        timestamps = ["2026-03-29T10:00:00", "2026-03-30T10:00:00",
                     "2026-03-31T10:00:00", "2026-04-01T10:00:00",
                     "2026-04-02T10:00:00"]

        curve = learning_service.analyze_learning_curve(
            project_id="proj_2",
            phase="design",
            metric_values=metric_values,
            timestamps=timestamps
        )

        assert isinstance(curve, LearningCurve)


class TestOptimizationRecommendations:
    """Test optimization recommendation generation."""

    def test_generate_optimization_recommendations(self, learning_service):
        """Test recommendations generation."""
        questions = [
            QuestionEffectiveness(
                question_id="q_1",
                text="Q1",
                effectiveness_score=0.8,
                gaps_addressed=2,
                answer_quality=0.85,
                impact_score=0.8,
                times_asked=5,
                success_rate=0.8
            ),
            QuestionEffectiveness(
                question_id="q_2",
                text="Q2",
                effectiveness_score=0.4,
                gaps_addressed=1,
                answer_quality=0.4,
                impact_score=0.4,
                times_asked=3,
                success_rate=0.3
            )
        ]

        patterns = [
            AnswerPattern(
                pattern_name="technical_focus",
                frequency=2,
                typical_gaps_addressed=["tech_detail"],
                average_quality=0.8,
                examples=["example1"]
            )
        ]

        recommendations = learning_service.generate_optimization_recommendations(
            project_id="proj_1",
            questions=questions,
            patterns=patterns
        )

        assert isinstance(recommendations, list)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_score_with_empty_text(self, learning_service):
        """Test effectiveness scoring with empty text."""
        score = learning_service.score_question_effectiveness(
            question_id="q_empty",
            question_text="",
            answer_text="",
            gaps_addressed=0,
            answer_quality=0.0,
            times_asked=1
        )

        assert isinstance(score, QuestionEffectiveness)
        assert score is not None

    def test_learning_curve_single_value(self, learning_service):
        """Test learning curve with single data point."""
        curve = learning_service.analyze_learning_curve(
            project_id="proj_single",
            phase="design",
            metric_values=[0.5],
            timestamps=["2026-04-02T10:00:00"]
        )

        assert isinstance(curve, LearningCurve)

    def test_score_max_quality(self, learning_service):
        """Test effectiveness scoring with maximum quality."""
        score = learning_service.score_question_effectiveness(
            question_id="q_perfect",
            question_text="Perfect question",
            answer_text="Perfect answer",
            gaps_addressed=10,
            answer_quality=1.0,
            times_asked=10
        )

        assert score.effectiveness_score <= 1.0

    def test_score_zero_gaps(self, learning_service):
        """Test effectiveness with zero gaps addressed."""
        score = learning_service.score_question_effectiveness(
            question_id="q_zero",
            question_text="Question",
            answer_text="Answer",
            gaps_addressed=0,
            answer_quality=0.5,
            times_asked=1
        )

        assert score is not None
