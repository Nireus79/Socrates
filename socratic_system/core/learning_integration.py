"""
Learning system integration using socratic-learning library.

Provides interaction tracking, pattern detection, and learning recommendations
using socratic-learning's InteractionLogger and recommendation engine.
"""

import logging
from typing import Any, Dict, List, Optional

from socratic_learning import InteractionLogger
from socratic_learning.recommendations.engine import RecommendationEngine

from socratic_system.models.learning import QuestionEffectiveness, UserBehaviorPattern


class LearningIntegration:
    """
    Integrated learning system combining:
    - socratic-learning's InteractionLogger for tracking user interactions
    - Pattern detection and learning analytics
    - Personalized recommendations based on user behavior
    """

    def __init__(self, log_path: str = "./learning_logs", llm_client: Optional[Any] = None):
        """
        Initialize learning integration.

        Args:
            log_path: Path to store interaction logs
            llm_client: Optional LLM client for enhanced recommendations
        """
        self.log_path = log_path
        self.llm_client = llm_client
        self.logger = logging.getLogger("socrates.learning")

        try:
            # Initialize interaction logger for tracking user behavior
            self.interaction_logger = InteractionLogger(
                storage_path=log_path,
                enable_analytics=True,
                session_tracking=True
            )
            self.logger.info("InteractionLogger initialized (socratic-learning)")

            # Initialize recommendation engine
            self.recommendation_engine = RecommendationEngine(
                interaction_logger=self.interaction_logger,
                use_llm=bool(llm_client),
                llm_client=llm_client if llm_client else None
            )
            self.logger.info("RecommendationEngine initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize learning integration: {e}")
            raise

    def log_interaction(
        self,
        user_id: str,
        interaction_type: str,
        context: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Log a user interaction for pattern analysis.

        Args:
            user_id: User identifier
            interaction_type: Type of interaction (question_asked, response_given, etc.)
            context: Context information (project_id, topic, etc.)
            metadata: Additional metadata

        Returns:
            True if logging successful
        """
        try:
            self.interaction_logger.log_interaction(
                user_id=user_id,
                interaction_type=interaction_type,
                context=context,
                metadata=metadata or {}
            )
            self.logger.debug(f"Logged interaction for user {user_id}: {interaction_type}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to log interaction: {e}")
            return False

    def log_question_asked(
        self,
        user_id: str,
        question_id: str,
        project_id: str,
        topic: str,
        difficulty: str = "medium"
    ) -> bool:
        """
        Log when a question is asked to the user.

        Args:
            user_id: User identifier
            question_id: Question identifier
            project_id: Project context
            topic: Question topic/category
            difficulty: Question difficulty level

        Returns:
            True if logged successfully
        """
        return self.log_interaction(
            user_id=user_id,
            interaction_type="question_asked",
            context={
                "question_id": question_id,
                "project_id": project_id,
                "topic": topic,
                "difficulty": difficulty
            }
        )

    def log_response_quality(
        self,
        user_id: str,
        question_id: str,
        quality_score: float,
        response_time: float,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Log the quality of a user's response.

        Args:
            user_id: User identifier
            question_id: Question answered
            quality_score: Quality score (0.0-1.0)
            response_time: Time taken to respond in seconds
            metadata: Additional metadata

        Returns:
            True if logged successfully
        """
        return self.log_interaction(
            user_id=user_id,
            interaction_type="response_quality",
            context={
                "question_id": question_id,
                "quality_score": quality_score,
                "response_time": response_time
            },
            metadata=metadata
        )

    def detect_patterns(
        self,
        user_id: str,
        window_size: int = 10
    ) -> Optional[UserBehaviorPattern]:
        """
        Detect learning patterns for a user.

        Args:
            user_id: User identifier
            window_size: Number of interactions to analyze

        Returns:
            UserBehaviorPattern object or None
        """
        try:
            patterns = self.interaction_logger.detect_patterns(
                user_id=user_id,
                window_size=window_size
            )

            if not patterns:
                return None

            # Convert to Socrates UserBehaviorPattern
            return UserBehaviorPattern(
                user_id=user_id,
                communication_style=patterns.get("communication_style", "analytical"),
                detail_level=patterns.get("detail_level", "medium"),
                learning_pace=patterns.get("learning_pace", "steady"),
                preferred_topics=patterns.get("preferred_topics", []),
                strength_areas=patterns.get("strength_areas", []),
                improvement_areas=patterns.get("improvement_areas", [])
            )

        except Exception as e:
            self.logger.error(f"Failed to detect patterns: {e}")
            return None

    def get_recommendations(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations for a user.

        Args:
            user_id: User identifier
            context: Optional context for recommendations
            top_k: Number of recommendations to return

        Returns:
            List of recommendations with descriptions and rationale
        """
        try:
            recommendations = self.recommendation_engine.generate_recommendations(
                user_id=user_id,
                context=context or {},
                top_k=top_k
            )

            formatted = []
            for rec in recommendations:
                formatted.append({
                    "type": getattr(rec, "recommendation_type", "suggestion"),
                    "description": getattr(rec, "description", ""),
                    "priority": getattr(rec, "priority", "medium"),
                    "rationale": getattr(rec, "rationale", ""),
                    "expected_impact": getattr(rec, "expected_impact", "unknown")
                })

            self.logger.debug(f"Generated {len(formatted)} recommendations for user {user_id}")
            return formatted

        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            return []

    def get_learning_metrics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive learning metrics for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with engagement, velocity, experience level, and other metrics
        """
        try:
            metrics = self.interaction_logger.get_user_metrics(user_id)

            return {
                "engagement_score": getattr(metrics, "engagement_score", 0.0),
                "learning_velocity": getattr(metrics, "learning_velocity", 0.0),
                "experience_level": getattr(metrics, "experience_level", "beginner"),
                "total_interactions": getattr(metrics, "total_interactions", 0),
                "average_response_quality": getattr(metrics, "avg_response_quality", 0.5),
                "topics_covered": getattr(metrics, "topics_covered", []),
                "last_activity": getattr(metrics, "last_activity", None),
                "consistency_score": getattr(metrics, "consistency_score", 0.0)
            }

        except Exception as e:
            self.logger.error(f"Failed to get learning metrics: {e}")
            return {}

    def export_learning_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export learning data for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing interactions, patterns, and metrics
        """
        try:
            data = self.interaction_logger.export_user_data(user_id)
            return {
                "interactions": getattr(data, "interactions", []),
                "patterns": getattr(data, "patterns", {}),
                "metrics": getattr(data, "metrics", {}),
                "recommendations": getattr(data, "recommendations", [])
            }
        except Exception as e:
            self.logger.error(f"Failed to export learning data: {e}")
            return {}

    def clear_user_data(self, user_id: str) -> bool:
        """
        Clear all learning data for a user.

        Args:
            user_id: User identifier

        Returns:
            True if cleared successfully
        """
        try:
            self.interaction_logger.clear_user_data(user_id)
            self.logger.info(f"Cleared learning data for user {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear user data: {e}")
            return False

    def close(self):
        """Close learning integration and flush logs"""
        try:
            self.interaction_logger.flush()
            self.logger.info("Learning integration closed")
        except Exception as e:
            self.logger.error(f"Error closing learning integration: {e}")

    def __del__(self):
        """Cleanup on object deletion"""
        try:
            self.close()
        except Exception:
            pass
