from socrates_api.models_local import LearningIntegration
"""
Learning Analytics API Router

Provides endpoints for tracking and analyzing user learning progress, mastery levels,
and educational effectiveness through the socratic-learning integration.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning", tags=["Learning Analytics"])


# ============================================================================
# LOCAL MODELS (moved from non-existent socratic_system.models)
# ============================================================================

class QuestionEffectiveness(BaseModel):
    """Model for question effectiveness metrics"""
    question_id: str
    effectiveness_score: float = 0.0
    times_asked: int = 0
    correct_responses: int = 0

class UserBehaviorPattern(BaseModel):
    """Model for user behavior patterns"""
    user_id: str
    pattern_type: str
    frequency: int = 0
    last_observed: Optional[str] = None


# ============================================================================
# MORE MODELS
# ============================================================================


class InteractionLogEntry(BaseModel):
    """Log entry for user-system interaction"""

    timestamp: datetime
    user_id: str
    interaction_type: str  # question_asked, response_given, concept_mastered, etc.
    topic: Optional[str] = None
    success: bool
    duration_seconds: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConceptMastery(BaseModel):
    """Tracks mastery level for a specific concept"""

    concept_id: str
    concept_name: str
    mastery_level: float = Field(..., ge=0, le=100, description="Mastery percentage 0-100")
    interactions_count: int
    last_interaction: datetime
    confidence_level: float = Field(..., ge=0, le=1, description="Confidence score 0-1")


class MisconcceptionDetection(BaseModel):
    """Detected misconception in user understanding"""

    misconception_id: str
    concept_id: str
    description: str
    frequency: int
    last_occurrence: datetime
    suggested_correction: str


class LearningProgressResponse(BaseModel):
    """Overall learning progress"""

    user_id: str
    total_interactions: int
    concepts_mastered: int
    total_concepts: int
    average_mastery: float
    learning_velocity: float  # Rate of progress
    study_streak: int  # Consecutive days
    overall_score: float = Field(..., ge=0, le=100)
    strengths: List[str]
    areas_for_improvement: List[str]
    predicted_mastery_date: Optional[datetime] = None


class LearningRecommendation(BaseModel):
    """Personalized learning recommendation"""

    recommendation_id: str
    type: str  # "concept", "practice", "review", "challenge"
    description: str
    target_concept: str
    priority_score: float
    estimated_time_minutes: int
    rationale: str


class LearningAnalytics(BaseModel):
    """Comprehensive learning analytics"""

    user_id: str
    period: str  # "daily", "weekly", "monthly"
    start_date: datetime
    end_date: datetime
    total_interactions: int
    unique_concepts_studied: int
    average_concept_mastery: float
    learning_efficiency: float  # Concepts mastered per hour studied
    engagement_score: float
    trend: str  # "improving", "stable", "declining"


# ============================================================================
# STATE
# ============================================================================

_learning_integration: Optional[LearningIntegration] = None


def get_learning_integration() -> Optional[LearningIntegration]:
    """Get or initialize learning integration"""
    global _learning_integration
    if _learning_integration is None:
        _learning_integration = LearningIntegration()
    return _learning_integration


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/interactions")
def log_interaction(
    user_id: str,
    interaction_type: str,
    topic: Optional[str] = None,
    success: bool = True,
    duration_seconds: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Log a learning interaction.

    Records user interactions with the system for pattern analysis and
    personalized recommendations.

    Query Parameters:
    - user_id: User identifier
    - interaction_type: Type of interaction (question_asked, response_given, etc.)
    - topic: Optional topic/concept
    - success: Whether interaction was successful
    - duration_seconds: Time spent on interaction
    - metadata: Additional metadata

    Returns:
    - Confirmation and interaction ID
    """
    try:
        learning = get_learning_integration()
        if learning is None or learning.interaction_logger is None:
            raise HTTPException(
                status_code=503,
                detail="Learning integration not available",
            )

        context = {
            "topic": topic,
            "success": success,
            "duration_seconds": duration_seconds,
        }

        success_log = learning.log_interaction(
            user_id=user_id,
            interaction_type=interaction_type,
            context=context,
            metadata=metadata,
        )

        if not success_log:
            raise HTTPException(
                status_code=500,
                detail="Failed to log interaction",
            )

        return {
            "status": "success",
            "message": f"Logged {interaction_type} interaction for user {user_id}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{user_id}", response_model=LearningProgressResponse)
def get_learning_progress(user_id: str) -> LearningProgressResponse:
    """
    Get overall learning progress for a user.

    Provides comprehensive view of learning progress including:
    - Total interactions and concepts studied
    - Mastery levels and learning velocity
    - Strengths and areas for improvement

    Path Parameters:
    - user_id: User identifier

    Returns:
    - Detailed learning progress metrics
    """
    try:
        learning = get_learning_integration()
        if learning is None:
            raise HTTPException(
                status_code=503,
                detail="Learning integration not available",
            )

        # This would load actual user progress data
        progress = LearningProgressResponse(
            user_id=user_id,
            total_interactions=0,
            concepts_mastered=0,
            total_concepts=0,
            average_mastery=0.0,
            learning_velocity=0.0,
            study_streak=0,
            overall_score=0.0,
            strengths=[],
            areas_for_improvement=[],
        )

        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mastery/{user_id}")
def get_concept_mastery(
    user_id: str,
    concept_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get concept mastery levels for a user.

    Returns mastery information for all concepts or a specific concept.

    Path Parameters:
    - user_id: User identifier

    Query Parameters:
    - concept_id: Optional specific concept (all if not provided)

    Returns:
    - Mastery levels with confidence scores
    """
    try:
        learning = get_learning_integration()
        if learning is None:
            raise HTTPException(
                status_code=503,
                detail="Learning integration not available",
            )

        mastery_data: List[ConceptMastery] = []
        # Would load actual mastery data from database

        return {
            "status": "success",
            "user_id": user_id,
            "mastery_levels": mastery_data,
            "average_mastery": 0.0,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mastery levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/misconceptions/{user_id}")
def get_misconceptions(user_id: str) -> Dict[str, Any]:
    """
    Get detected misconceptions for a user.

    Identifies common misunderstandings and provides corrections.

    Path Parameters:
    - user_id: User identifier

    Returns:
    - List of detected misconceptions with corrections
    """
    try:
        misconceptions: List[MisconcceptionDetection] = []
        # Would load actual misconception data

        return {
            "status": "success",
            "user_id": user_id,
            "total_misconceptions": len(misconceptions),
            "misconceptions": misconceptions,
        }

    except Exception as e:
        logger.error(f"Error getting misconceptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{user_id}")
def get_recommendations(
    user_id: str,
    count: int = Query(5, ge=1, le=20),
) -> Dict[str, Any]:
    """
    Get personalized learning recommendations.

    Provides tailored recommendations based on:
    - Current mastery levels
    - Identified misconceptions
    - Learning patterns
    - Predicted difficulty

    Path Parameters:
    - user_id: User identifier

    Query Parameters:
    - count: Number of recommendations (default: 5)

    Returns:
    - Prioritized learning recommendations
    """
    try:
        learning = get_learning_integration()
        if learning is None:
            raise HTTPException(
                status_code=503,
                detail="Learning integration not available",
            )

        recommendations: List[LearningRecommendation] = []
        # Would generate recommendations using recommendation engine

        return {
            "status": "success",
            "user_id": user_id,
            "recommendations": recommendations,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{user_id}")
def get_learning_analytics(
    user_id: str,
    period: str = Query("weekly", pattern="daily|weekly|monthly"),
    days_back: int = Query(30, ge=1, le=365),
) -> LearningAnalytics:
    """
    Get comprehensive learning analytics for a user.

    Analyzes learning patterns over a specified period including:
    - Study frequency and duration
    - Concept coverage
    - Learning efficiency
    - Engagement trends

    Path Parameters:
    - user_id: User identifier

    Query Parameters:
    - period: Analysis period (daily, weekly, monthly)
    - days_back: How many days to analyze (default: 30)

    Returns:
    - Detailed learning analytics
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        analytics = LearningAnalytics(
            user_id=user_id,
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_interactions=0,
            unique_concepts_studied=0,
            average_concept_mastery=0.0,
            learning_efficiency=0.0,
            engagement_score=0.0,
            trend="stable",
        )

        return analytics

    except Exception as e:
        logger.error(f"Error getting learning analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def get_learning_system_status() -> Dict[str, Any]:
    """
    Get status of the learning analytics system.

    Returns:
    - System status and capabilities
    """
    try:
        learning = get_learning_integration()

        return {
            "status": "operational",
            "learning_integration_available": learning is not None,
            "interaction_logger_available": learning.interaction_logger is not None if learning else False,
            "recommendation_engine_available": learning.recommendation_engine is not None if learning else False,
            "capabilities": [
                "interaction_logging",
                "mastery_tracking",
                "misconception_detection",
                "personalized_recommendations",
                "progress_analytics",
                "learning_patterns",
            ],
        }

    except Exception as e:
        logger.error(f"Error getting learning status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "capabilities": [],
        }
