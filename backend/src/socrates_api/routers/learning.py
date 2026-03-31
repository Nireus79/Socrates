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

from socrates_api.models_local import LearningIntegration
from socrates_api.library_cache import get_learning_service

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
# DEPENDENCY INJECTION
# ============================================================================

# Use library singleton caching via dependency injection
# The get_learning_service function from library_cache provides the singleton instance


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
    learning: LearningIntegration = Depends(get_learning_service),
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
    - learning: LearningIntegration singleton (injected)

    Returns:
    - Confirmation and interaction ID
    """
    try:
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
        logger.debug("Error logging interaction", exc_info=True)
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


@router.get("/progress/{user_id}", response_model=LearningProgressResponse)
def get_learning_progress(
    user_id: str,
    learning: LearningIntegration = Depends(get_learning_service),
) -> LearningProgressResponse:
    """
    Get overall learning progress for a user.

    Provides comprehensive view of learning progress including:
    - Total interactions and concepts studied
    - Mastery levels and learning velocity
    - Strengths and areas for improvement

    Uses the socratic-learning library for accurate metrics.

    Path Parameters:
    - user_id: User identifier
    - learning: LearningIntegration singleton (injected)

    Returns:
    - Detailed learning progress metrics
    """
    try:
        # Get actual progress data from library
        progress_data = learning.get_progress(user_id)

        # Map library response to API model
        progress = LearningProgressResponse(
            user_id=user_id,
            total_interactions=progress_data.get("total_interactions", 0),
            concepts_mastered=progress_data.get("concepts_mastered", 0),
            total_concepts=progress_data.get("total_concepts", 0),
            average_mastery=progress_data.get("average_mastery", 0.0),
            learning_velocity=progress_data.get("learning_velocity", 0.0),
            study_streak=progress_data.get("study_streak", 0),
            overall_score=progress_data.get("overall_score", 0.0),
            strengths=progress_data.get("strengths", []),
            areas_for_improvement=progress_data.get("areas_for_improvement", []),
            predicted_mastery_date=progress_data.get("predicted_mastery_date"),
        )

        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning progress: {e}")
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


@router.get("/mastery/{user_id}")
def get_concept_mastery(
    user_id: str,
    concept_id: Optional[str] = None,
    learning: LearningIntegration = Depends(get_learning_service),
) -> Dict[str, Any]:
    """
    Get concept mastery levels for a user.

    Returns mastery information for all concepts or a specific concept
    using the socratic-learning library.

    Path Parameters:
    - user_id: User identifier
    - learning: LearningIntegration singleton (injected)

    Query Parameters:
    - concept_id: Optional specific concept (all if not provided)

    Returns:
    - Mastery levels with confidence scores
    """
    try:
        # Get mastery data from library
        mastery_list = learning.get_mastery(user_id, concept_id)

        # Calculate average mastery
        if mastery_list:
            average_mastery = sum(m.get("mastery_level", 0) for m in mastery_list) / len(mastery_list)
        else:
            average_mastery = 0.0

        return {
            "status": "success",
            "user_id": user_id,
            "concept_id": concept_id,
            "mastery_levels": mastery_list,
            "average_mastery": average_mastery,
            "count": len(mastery_list),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mastery levels: {e}")
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


@router.get("/misconceptions/{user_id}")
def get_misconceptions(
    user_id: str,
    learning: LearningIntegration = Depends(get_learning_service),
) -> Dict[str, Any]:
    """
    Get detected misconceptions for a user.

    Identifies common misunderstandings and provides corrections
    using the socratic-learning library's pattern detection.

    Path Parameters:
    - user_id: User identifier
    - learning: LearningIntegration singleton (injected)

    Returns:
    - List of detected misconceptions with corrections
    """
    try:
        misconceptions = learning.detect_misconceptions(user_id)

        return {
            "status": "success",
            "user_id": user_id,
            "total_misconceptions": len(misconceptions),
            "misconceptions": misconceptions,
        }

    except Exception as e:
        logger.error(f"Error getting misconceptions: {e}")
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


@router.get("/recommendations/{user_id}")
def get_recommendations(
    user_id: str,
    count: int = Query(5, ge=1, le=20),
    learning: LearningIntegration = Depends(get_learning_service),
) -> Dict[str, Any]:
    """
    Get personalized learning recommendations.

    Provides tailored recommendations based on:
    - Current mastery levels
    - Identified misconceptions
    - Learning patterns
    - Predicted difficulty

    Uses the socratic-learning library's recommendation engine.

    Path Parameters:
    - user_id: User identifier
    - learning: LearningIntegration singleton (injected)

    Query Parameters:
    - count: Number of recommendations (default: 5, max: 20)

    Returns:
    - Prioritized learning recommendations
    """
    try:
        # Get recommendations from library
        recommendations = learning.get_recommendations(user_id, count=count)

        return {
            "status": "success",
            "user_id": user_id,
            "count": len(recommendations),
            "recommendations": recommendations,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


@router.get("/analytics/{user_id}")
def get_learning_analytics(
    user_id: str,
    period: str = Query("weekly", pattern="daily|weekly|monthly"),
    days_back: int = Query(30, ge=1, le=365),
    learning: LearningIntegration = Depends(get_learning_service),
) -> LearningAnalytics:
    """
    Get comprehensive learning analytics for a user.

    Analyzes learning patterns over a specified period including:
    - Study frequency and duration
    - Concept coverage
    - Learning efficiency
    - Engagement trends

    Uses the socratic-learning library's metrics collector.

    Path Parameters:
    - user_id: User identifier
    - learning: LearningIntegration singleton (injected)

    Query Parameters:
    - period: Analysis period (daily, weekly, monthly)
    - days_back: How many days to analyze (default: 30, max: 365)

    Returns:
    - Detailed learning analytics
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        analytics_data = learning.get_analytics(user_id, period=period, days_back=days_back)

        # Map library response to API model
        analytics = LearningAnalytics(
            user_id=user_id,
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_interactions=analytics_data.get("total_interactions", 0),
            unique_concepts_studied=analytics_data.get("unique_concepts_studied", 0),
            average_concept_mastery=analytics_data.get("average_concept_mastery", 0.0),
            learning_efficiency=analytics_data.get("learning_efficiency", 0.0),
            engagement_score=analytics_data.get("engagement_score", 0.0),
            trend=analytics_data.get("trend", "stable"),
        )

        return analytics

    except Exception as e:
        logger.error(f"Error getting learning analytics: {e}")
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


@router.get("/status")
def get_learning_system_status(
    learning: LearningIntegration = Depends(get_learning_service),
) -> Dict[str, Any]:
    """
    Get status of the learning analytics system.

    Returns the availability of the socratic-learning library and all capabilities.

    Parameters:
    - learning: LearningIntegration singleton (injected)

    Returns:
    - System status and capabilities
    """
    try:
        status_info = learning.get_status()

        capabilities = []
        if status_info.get("engine"):
            capabilities.append("interaction_logging")
        if status_info.get("metrics_collector"):
            capabilities.extend(["mastery_tracking", "progress_analytics", "learning_patterns"])
        if status_info.get("pattern_detector"):
            capabilities.append("misconception_detection")
        if status_info.get("recommendation_engine"):
            capabilities.append("personalized_recommendations")
        if status_info.get("user_feedback"):
            capabilities.append("feedback_integration")
        if status_info.get("fine_tuning_exporter"):
            capabilities.append("fine_tuning_data_export")

        return {
            "status": "operational",
            "learning_integration_available": True,
            "library_details": status_info,
            "capabilities": capabilities,
            "message": "All learning features operational"
        }

    except Exception as e:
        logger.error(f"Error getting learning status: {e}")
        return {
            "status": "error",
            "message": str(e),
            "learning_integration_available": False,
            "capabilities": [],
        }
