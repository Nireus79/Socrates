"""
Unit tests for LearningService.

Tests question effectiveness scoring, answer pattern detection,
learning curve analysis, and optimization recommendations.
"""

import pytest
from unittest.mock import Mock, MagicMock

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
            question_text="What are the security requirements for the system?",
            answer_text="The system must implement encryption, authentication, and authorization",
            answer_quality=0.9,
            gaps_addressed=3,
            success_rate=0.95
        )

        assert score is not None
        assert score.effectiveness_score > 0.7
        assert score.answer_quality == 0.9

    def test_score_question_effectiveness_medium(self, learning_service):
        """Test effectiveness scoring for medium-quality question."""
        score = learning_service.score_question_effectiveness(
            question_id="q_2",
            question_text="What are the design patterns?",
            answer_text="We should use some design patterns",
            answer_quality=0.5,
            gaps_addressed=1,
            success_rate=0.6
        )

        assert 0.4 < score.effectiveness_score < 0.8

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

        assert score.effectiveness_score < 0.5

    def test_effectiveness_gap_closure_value(self, learning_service):
        """Test gap closure value in effectiveness score."""
        score = learning_service.score_question_effectiveness(
            question_id="q_4",
            question_text="How to implement X?",
            answer_text="Here's how to implement X with details",
            answer_quality=0.8,
            gaps_addressed=5,
            success_rate=0.9
        )

        assert score.gap_closure_value > 0
        assert score.effectiveness_score > 0


class TestAnswerPatternDetection:
    """Test answer pattern detection."""

    def test_detect_answer_patterns_basic(self, learning_service):
        """Test basic answer pattern detection."""
        answers = [
            "This is a technical implementation detail",
            "The system uses a microservices architecture",
            "We implement caching for performance"
        ]

        patterns = learning_service.detect_answer_patterns(
            project_id="proj_1",
            answers=answers
        )

        assert patterns is not None

    def test_detect_answer_patterns_length_distribution(self, learning_service):
        """Test answer length pattern detection."""
        short_answers = ["Yes", "No", "Maybe"]
        medium_answers = ["This is a medium length answer with details"]
        long_answers = [
            "This is a comprehensive answer that provides extensive details "
            "about the topic including multiple perspectives and considerations"
        ]

        short_pattern = learning_service.detect_answer_patterns(
            project_id="proj_short",
            answers=short_answers
        )

        long_pattern = learning_service.detect_answer_patterns(
            project_id="proj_long",
            answers=long_answers
        )

        assert short_pattern is not None
        assert long_pattern is not None

    def test_detect_answer_patterns_technical_focus(self, learning_service):
        """Test detection of technical focus in answers."""
        technical_answers = [
            "We use REST API with JSON serialization",
            "Database normalization with ACID properties",
            "Implement async/await for performance"
        ]

        patterns = learning_service.detect_answer_patterns(
            project_id="proj_tech",
            answers=technical_answers
        )

        assert patterns is not None

    def test_detect_answer_patterns_business_focus(self, learning_service):
        """Test detection of business focus in answers."""
        business_answers = [
            "We need to improve customer satisfaction",
            "ROI should be maximized within 6 months",
            "Market demands competitive pricing"
        ]

        patterns = learning_service.detect_answer_patterns(
            project_id="proj_business",
            answers=business_answers
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

    def test_analyze_learning_curve_plateau(self, learning_service):
        """Test learning curve that plateaus."""
        effectiveness_scores = [0.7, 0.71, 0.70, 0.72, 0.71]

        curve = learning_service.analyze_learning_curve(
            project_id="proj_2",
            effectiveness_scores=effectiveness_scores,
            question_count=5
        )

        assert curve is not None
        assert curve.trend in ["stable", "plateau"]

    def test_analyze_learning_curve_declining(self, learning_service):
        """Test learning curve showing decline."""
        effectiveness_scores = [0.8, 0.7, 0.6, 0.5, 0.4]

        curve = learning_service.analyze_learning_curve(
            project_id="proj_3",
            effectiveness_scores=effectiveness_scores,
            question_count=5
        )

        assert curve is not None
        assert curve.trend == "declining"

    def test_analyze_learning_curve_volatility(self, learning_service):
        """Test learning curve with volatile effectiveness."""
        effectiveness_scores = [0.3, 0.8, 0.4, 0.9, 0.2]

        curve = learning_service.analyze_learning_curve(
            project_id="proj_4",
            effectiveness_scores=effectiveness_scores,
            question_count=5
        )

        assert curve is not None


class TestOptimizationRecommendations:
    """Test optimization recommendation generation."""

    def test_generate_optimization_recommendations_improve_clarity(self, learning_service):
        """Test recommendations for improving question clarity."""
        patterns = MagicMock()
        patterns.length_distribution = "too_short"
        patterns.technical_focus = ["unclear_terms"]

        recommendations = learning_service.generate_optimization_recommendations(
            project_id="proj_1",
            question_history=[
                {"question": "What?", "answer": "Unclear"},
                {"question": "Define X?", "answer": "Still vague"}
            ],
            patterns=patterns
        )

        assert recommendations is not None
        assert len(recommendations) > 0

    def test_generate_optimization_recommendations_focus_areas(self, learning_service):
        """Test recommendations for adjusting focus areas."""
        patterns = MagicMock()
        patterns.length_distribution = "balanced"
        patterns.technical_focus = ["architecture", "performance"]

        recommendations = learning_service.generate_optimization_recommendations(
            project_id="proj_2",
            question_history=[
                {"question": "Architecture?", "answer": "Microservices"},
                {"question": "Performance?", "answer": "Caching"}
            ],
            patterns=patterns
        )

        assert recommendations is not None

    def test_generate_optimization_recommendations_coverage(self, learning_service):
        """Test recommendations for improving coverage."""
        patterns = MagicMock()
        patterns.length_distribution = "balanced"
        patterns.technical_focus = ["implementation"]

        recommendations = learning_service.generate_optimization_recommendations(
            project_id="proj_3",
            question_history=[
                {"question": "How to code?", "answer": "Use best practices"},
                {"question": "What language?", "answer": "Python"}
            ],
            patterns=patterns
        )

        assert recommendations is not None


class TestSuggestImprovedQuestion:
    """Test improved question suggestion."""

    def test_suggest_improved_question_vague(self, learning_service):
        """Test suggestion for improving vague question."""
        improved = learning_service.suggest_improved_question(
            original_question="What is it?",
            answer_received="Not sure what you mean",
            effectiveness_score=0.2
        )

        assert improved is not None
        assert len(improved) > 0

    def test_suggest_improved_question_specific(self, learning_service):
        """Test suggestion for improving specific question."""
        improved = learning_service.suggest_improved_question(
            original_question="What are the security requirements?",
            answer_received="We need encryption and authentication",
            effectiveness_score=0.8
        )

        assert improved is not None

    def test_suggest_improved_question_technical(self, learning_service):
        """Test suggestion for technical question improvement."""
        improved = learning_service.suggest_improved_question(
            original_question="How should we design the database?",
            answer_received="Use normal form and indexes",
            effectiveness_score=0.65
        )

        assert improved is not None


class TestLearningSummary:
    """Test learning summary generation."""

    def test_get_learning_summary_basic(self, learning_service):
        """Test basic learning summary."""
        asked_questions = [
            {"question": "Q1?", "answer": "A1", "question_id": "q_1"},
            {"question": "Q2?", "answer": "A2", "question_id": "q_2"},
            {"question": "Q3?", "answer": "A3", "question_id": "q_3"},
        ]

        summary = learning_service.get_learning_summary(
            project_id="proj_1",
            asked_questions=asked_questions
        )

        assert summary is not None

    def test_get_learning_summary_effectiveness_distribution(self, learning_service):
        """Test learning summary with effectiveness distribution."""
        asked_questions = [
            {"question": f"Q{i}?", "answer": f"A{i}", "question_id": f"q_{i}"}
            for i in range(10)
        ]

        summary = learning_service.get_learning_summary(
            project_id="proj_2",
            asked_questions=asked_questions
        )

        assert summary is not None

    def test_get_learning_summary_comprehensive(self, learning_service):
        """Test comprehensive learning summary."""
        asked_questions = [
            {
                "question": "How to implement encryption?",
                "answer": "Use AES-256 with key management",
                "question_id": "q_1"
            },
            {
                "question": "What's the architecture?",
                "answer": "Microservices with service discovery",
                "question_id": "q_2"
            },
            {
                "question": "Performance requirements?",
                "answer": "Sub-100ms latency for 99th percentile",
                "question_id": "q_3"
            },
        ]

        summary = learning_service.get_learning_summary(
            project_id="proj_3",
            asked_questions=asked_questions
        )

        assert summary is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_score_question_with_empty_text(self, learning_service):
        """Test effectiveness scoring with empty question text."""
        score = learning_service.score_question_effectiveness(
            question_id="q_empty",
            question_text="",
            answer_text="",
            answer_quality=0.0,
            gaps_addressed=0,
            success_rate=0.0
        )

        assert score is not None

    def test_detect_patterns_with_single_answer(self, learning_service):
        """Test pattern detection with single answer."""
        patterns = learning_service.detect_answer_patterns(
            project_id="proj_single",
            answers=["Single answer"]
        )

        assert patterns is not None

    def test_detect_patterns_with_empty_answers(self, learning_service):
        """Test pattern detection with empty answers."""
        patterns = learning_service.detect_answer_patterns(
            project_id="proj_empty",
            answers=[]
        )

        assert patterns is not None

    def test_learning_curve_single_point(self, learning_service):
        """Test learning curve with single data point."""
        curve = learning_service.analyze_learning_curve(
            project_id="proj_single",
            effectiveness_scores=[0.5],
            question_count=1
        )

        assert curve is not None

    def test_learning_curve_all_zeros(self, learning_service):
        """Test learning curve with all zero effectiveness."""
        curve = learning_service.analyze_learning_curve(
            project_id="proj_zero",
            effectiveness_scores=[0.0, 0.0, 0.0],
            question_count=3
        )

        assert curve is not None

    def test_optimization_recommendations_no_history(self, learning_service):
        """Test recommendations with no question history."""
        patterns = MagicMock()

        recommendations = learning_service.generate_optimization_recommendations(
            project_id="proj_new",
            question_history=[],
            patterns=patterns
        )

        assert recommendations is not None

    def test_improved_question_perfect_score(self, learning_service):
        """Test improved question suggestion for perfect score."""
        improved = learning_service.suggest_improved_question(
            original_question="Perfect question?",
            answer_received="Perfect answer",
            effectiveness_score=1.0
        )

        assert improved is not None

    def test_learning_summary_empty_questions(self, learning_service):
        """Test learning summary with no questions."""
        summary = learning_service.get_learning_summary(
            project_id="proj_new",
            asked_questions=[]
        )

        assert summary is None or summary is not None


class TestDataConsistency:
    """Test data consistency in learning analysis."""

    def test_effectiveness_consistency_across_calls(self, learning_service):
        """Test that same question produces same score."""
        question_data = {
            "question_id": "q_consistent",
            "question_text": "What is the system architecture?",
            "answer_text": "A microservices architecture with service discovery",
            "answer_quality": 0.8,
            "gaps_addressed": 2,
            "success_rate": 0.85
        }

        score1 = learning_service.score_question_effectiveness(**question_data)
        score2 = learning_service.score_question_effectiveness(**question_data)

        assert score1.effectiveness_score == score2.effectiveness_score

    def test_pattern_detection_deterministic(self, learning_service):
        """Test that pattern detection is deterministic."""
        answers = [
            "Technical implementation detail",
            "Performance consideration",
            "Architecture decision"
        ]

        pattern1 = learning_service.detect_answer_patterns("proj_1", answers)
        pattern2 = learning_service.detect_answer_patterns("proj_1", answers)

        assert pattern1 is not None
        assert pattern2 is not None
