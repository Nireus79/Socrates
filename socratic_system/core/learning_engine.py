"""
Learning Engine - Pure business logic for user behavior analysis and personalization.

This module handles all learning-related calculations without database dependencies:
- User profile building from raw metrics
- Learning metrics calculation (engagement, velocity, experience)
- Personalization hints generation
- Question effectiveness scoring
- Behavior pattern analysis
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class LearningEngine:
    """
    Pure learning logic for analyzing user behavior and generating personalization.

    All methods are stateless computations - no database calls, no side effects.
    Input: raw user data (questions asked, response quality, topic interactions)
    Output: analyzed profiles, scores, and recommendations
    """

    def __init__(self, logger_instance: Optional[Any] = None):
        """
        Initialize the learning engine.

        Args:
            logger_instance: Optional logger instance (if None, uses module logger)
        """
        self.logger = logger_instance or logger
        self.logger.debug("LearningEngine initialized")

    # ============================================================================
    # User Profile Building
    # ============================================================================

    def build_user_profile(
        self,
        user_id: str,
        questions_asked: List[Dict[str, Any]],
        responses_quality: List[float],
        topic_interactions: List[str],
        projects_completed: int,
    ) -> "UserProfile":
        """
        Build a complete user behavior profile from raw metrics.

        Args:
            user_id: Unique user identifier
            questions_asked: List of {id, times_asked, times_answered_well}
            responses_quality: List of quality scores (0-1) for each response
            topic_interactions: List of topics/pattern types user has interacted with
            projects_completed: Number of projects completed by user

        Returns:
            UserProfile object with aggregated data
        """
        self.logger.debug(
            f"Building user profile for user: {user_id}, "
            f"questions={len(questions_asked)}, responses={len(responses_quality)}, "
            f"topics={len(topic_interactions)}, projects={projects_completed}"
        )

        # Calculate aggregate metrics
        total_questions_asked = sum(q.get("times_asked", 0) for q in questions_asked)
        total_answered_well = sum(q.get("times_answered_well", 0) for q in questions_asked)

        self.logger.debug(
            f"User {user_id} aggregated metrics: "
            f"total_questions={total_questions_asked}, "
            f"answered_well={total_answered_well}"
        )

        # Average response quality
        overall_response_quality = (
            sum(responses_quality) / len(responses_quality) if responses_quality else 0.5
        )

        # Unique topics explored
        topics_explored = len(set(topic_interactions))

        # Create profile object
        profile = UserProfile(
            user_id=user_id,
            total_questions_asked=total_questions_asked,
            total_answered_well=total_answered_well,
            overall_response_quality=overall_response_quality,
            topics_explored=topics_explored,
            projects_completed=projects_completed,
            topic_interactions=topic_interactions,
        )

        self.logger.debug(
            f"Built profile: {total_questions_asked} questions, "
            f"quality={overall_response_quality:.2f}, "
            f"topics={topics_explored}"
        )

        return profile

    # ============================================================================
    # Learning Metrics Calculation
    # ============================================================================

    def calculate_learning_metrics(self, profile: "UserProfile") -> Dict[str, Any]:
        """
        Calculate learning metrics from user profile.

        Metrics:
        - engagement_score: 0-1, based on participation frequency
        - learning_velocity: 0-1, how quickly user improves
        - experience_level: beginner/intermediate/advanced
        - recommendation_confidence: how much we should trust recommendations

        Args:
            profile: UserProfile object

        Returns:
            Dict with calculated metrics
        """
        self.logger.debug(
            f"Calculating metrics for user: {profile.user_id}, "
            f"questions={profile.total_questions_asked}, "
            f"quality={profile.overall_response_quality:.2f}"
        )

        # Engagement: based on number of questions asked
        # Scale: 0-100 questions -> 0-1 engagement
        engagement_score = min(1.0, profile.total_questions_asked / 100.0)

        # Learning Velocity: based on success rate (answered_well / asked)
        # High velocity = quickly improving answers
        if profile.total_questions_asked > 0:
            success_rate = profile.total_answered_well / profile.total_questions_asked
            # Velocity = how much better than random
            # 0.5 (random) -> 0 velocity, 1.0 (perfect) -> high velocity
            learning_velocity = max(0.0, success_rate - 0.5) * 2.0
        else:
            learning_velocity = 0.0

        # Experience Level: based on questions and success
        if profile.total_questions_asked < 10:
            experience_level = "beginner"
            self.logger.debug(f"User {profile.user_id} classified as beginner (questions < 10)")
        elif profile.total_questions_asked < 50:
            experience_level = "intermediate"
            self.logger.debug(f"User {profile.user_id} classified as intermediate (questions < 50)")
        else:
            experience_level = "advanced"
            self.logger.debug(f"User {profile.user_id} classified as advanced (questions >= 50)")

        success_rate = (
            profile.total_answered_well / profile.total_questions_asked
            if profile.total_questions_asked > 0
            else 0
        )

        recommendation_confidence = self._calculate_recommendation_confidence(
            profile, engagement_score, learning_velocity
        )

        metrics = {
            "engagement_score": round(engagement_score, 2),
            "learning_velocity": round(learning_velocity, 2),
            "experience_level": experience_level,
            "success_rate": round(success_rate, 2),
            "topics_explored": profile.topics_explored,
            "projects_completed": profile.projects_completed,
            "recommendation_confidence": recommendation_confidence,
        }

        self.logger.info(
            f"Calculated metrics for user {profile.user_id}: "
            f"engagement={metrics['engagement_score']}, "
            f"velocity={metrics['learning_velocity']}, "
            f"level={metrics['experience_level']}, "
            f"success_rate={metrics['success_rate']:.2f}, "
            f"confidence={recommendation_confidence:.2f}"
        )

        return metrics

    def _calculate_recommendation_confidence(
        self, profile: "UserProfile", engagement: float, velocity: float
    ) -> float:
        """
        Calculate how confident we should be in recommendations.

        Higher confidence with more data and consistent behavior.

        Args:
            profile: User profile
            engagement: Engagement score (0-1)
            velocity: Learning velocity (0-1)

        Returns:
            Confidence score (0-1)
        """
        # Need enough questions to build confidence
        question_confidence = min(1.0, profile.total_questions_asked / 20.0)

        # Consistent behavior (neither too fast nor too slow improvement)
        consistency_score = 1.0 - abs(velocity - 0.5)

        # Overall confidence
        confidence = (question_confidence * 0.7) + (consistency_score * 0.3)
        return round(confidence, 2)

    # ============================================================================
    # Personalization Hints
    # ============================================================================

    def get_personalization_hints(self, profile: "UserProfile") -> Dict[str, Any]:
        """
        Generate personalization hints based on user profile.

        Hints guide the Socratic Counselor on question selection strategy.

        Args:
            profile: User profile

        Returns:
            Dict with personalization recommendations
        """
        self.logger.debug(f"Generating personalization hints for user: {profile.user_id}")

        complexity = self._recommend_complexity(profile)
        style = self._recommend_style(profile)
        followup = self._recommend_follow_up(profile)
        gaps = self._identify_gaps(profile)
        strengths = self._identify_strengths(profile)

        hints = {
            "question_complexity": complexity,
            "question_style": style,
            "follow_up_strategy": followup,
            "knowledge_gaps": gaps,
            "strengths": strengths,
        }

        self.logger.info(
            f"Personalization hints for user {profile.user_id}: "
            f"complexity={complexity}, style={style}, "
            f"gaps={len(gaps)}, strengths={len(strengths)}"
        )

        return hints

    def _recommend_complexity(self, profile: "UserProfile") -> str:
        """Recommend question complexity level."""
        if profile.total_questions_asked < 5:
            return "simple"  # Start simple
        elif profile.overall_response_quality > 0.7:
            return "complex"  # User doing well, increase challenge
        else:
            return "moderate"  # Balanced difficulty

    def _recommend_style(self, profile: "UserProfile") -> str:
        """Recommend Socratic question style."""
        if profile.overall_response_quality > 0.8:
            return "challenging"  # Challenge advanced users
        elif profile.topics_explored > 5:
            return "synthesis"  # Connect across topics
        else:
            return "foundational"  # Build basics

    def _recommend_follow_up(self, profile: "UserProfile") -> str:
        """Recommend follow-up strategy."""
        if profile.overall_response_quality < 0.5:
            return "scaffolded"  # More supportive follow-ups
        else:
            return "exploratory"  # Open-ended follow-ups

    def _identify_gaps(self, profile: "UserProfile") -> List[str]:
        """Identify potential knowledge gaps."""
        gaps = []

        if profile.topics_explored < 3:
            gaps.append("Limited topic breadth - encourage exploration")

        if profile.overall_response_quality < 0.5:
            gaps.append("Weak response quality - focus on understanding")

        return gaps

    def _identify_strengths(self, profile: "UserProfile") -> List[str]:
        """Identify user strengths."""
        strengths = []

        if profile.overall_response_quality > 0.7:
            strengths.append("Strong comprehension")

        if profile.total_answered_well > profile.total_questions_asked * 0.6:
            strengths.append("Good learning trajectory")

        if profile.topics_explored > 5:
            strengths.append("Broad knowledge breadth")

        return strengths

    # ============================================================================
    # Question Effectiveness Analysis
    # ============================================================================

    def score_question_effectiveness(
        self, times_asked: int, times_answered_well: int, average_quality: float
    ) -> float:
        """
        Calculate effectiveness score for a question.

        Higher = better question for user
        Lower = question not working well

        Args:
            times_asked: How many times asked
            times_answered_well: How many times answered well
            average_quality: Average response quality (0-1)

        Returns:
            Effectiveness score (0-1)
        """
        if times_asked == 0:
            return 0.5  # Neutral if never asked

        # Success rate
        success_rate = times_answered_well / times_asked

        # Weighted by response quality
        effectiveness = (success_rate * 0.6) + (average_quality * 0.4)

        return round(min(1.0, max(0.0, effectiveness)), 2)

    def should_recommend_question(
        self, effectiveness_score: float, confidence: float, times_asked: int
    ) -> Tuple[bool, str]:
        """
        Determine if question should be recommended to user.

        Args:
            effectiveness_score: Question's effectiveness (0-1)
            confidence: Recommendation confidence (0-1)
            times_asked: How many times asked before

        Returns:
            (should_recommend: bool, reason: str)
        """
        # Need minimum data
        if times_asked < 3:
            return False, "Insufficient data (< 3 attempts)"

        # Check effectiveness threshold
        if effectiveness_score > 0.7 and confidence > 0.6:
            return True, "High effectiveness with good confidence"
        elif effectiveness_score > 0.6 and confidence > 0.5:
            return True, "Moderate effectiveness, acceptable confidence"

        return False, "Low effectiveness or insufficient confidence"

    # ============================================================================
    # Pattern Analysis
    # ============================================================================

    def analyze_behavior_pattern(
        self, pattern_data: Dict[str, Any], confidence: float, projects_count: int
    ) -> Dict[str, Any]:
        """
        Analyze and validate a behavior pattern.

        Args:
            pattern_data: Raw pattern data
            confidence: Confidence level (0-1)
            projects_count: Number of projects this pattern learned from

        Returns:
            Dict with analysis results
        """
        analysis = {
            "is_valid": confidence > 0.3,  # Minimum confidence threshold
            "confidence": round(confidence, 2),
            "data_points": projects_count,
            "stability": self._assess_stability(confidence, projects_count),
            "actionability": self._assess_actionability(pattern_data),
        }

        return analysis

    def _assess_stability(self, confidence: float, data_points: int) -> str:
        """Assess how stable/reliable the pattern is."""
        if data_points < 2:
            return "unstable"
        elif confidence < 0.5:
            return "emerging"
        elif confidence < 0.8:
            return "developing"
        else:
            return "stable"

    def _assess_actionability(self, pattern_data: Dict[str, Any]) -> str:
        """Assess if pattern is actionable for personalization."""
        if not pattern_data:
            return "not_actionable"

        # Count filled fields
        filled_fields = sum(1 for v in pattern_data.values() if v)
        if filled_fields < 2:
            return "not_actionable"

        return "actionable"


# ============================================================================
# Data Models (Lightweight)
# ============================================================================


class UserProfile:
    """Lightweight data model for user behavior profile."""

    def __init__(
        self,
        user_id: str,
        total_questions_asked: int,
        total_answered_well: int,
        overall_response_quality: float,
        topics_explored: int,
        projects_completed: int,
        topic_interactions: List[str],
    ):
        self.user_id = user_id
        self.total_questions_asked = total_questions_asked
        self.total_answered_well = total_answered_well
        self.overall_response_quality = round(overall_response_quality, 2)
        self.topics_explored = topics_explored
        self.projects_completed = projects_completed
        self.topic_interactions = topic_interactions

    def __repr__(self):
        return (
            f"UserProfile(user_id={self.user_id}, "
            f"questions={self.total_questions_asked}, "
            f"quality={self.overall_response_quality})"
        )
