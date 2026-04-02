"""
Phase 6 Advancement Tracking & Metrics API Endpoints

Provides REST endpoints for:
- Gap closure status
- Specification completeness metrics
- Advancement metrics and readiness
- Dashboard visualization data
- Progress history and trends
- Question effectiveness scores
- Optimization recommendations
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["advancement"])


# ============================================================================
# Gap Closure Status Endpoint
# ============================================================================

@router.get(
    "/{project_id}/advancement/gaps",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get gap closure status",
)
async def get_gap_closure_status(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get gap closure status for a project.

    Returns which gaps have been closed and their closure confidence.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        APIResponse with gap closure status
    """
    try:
        logger.info(f"Getting gap closure status for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        from socrates_api.orchestrator import APIOrchestrator
        orchestrator = APIOrchestrator()

        if not orchestrator.advancement_tracker:
            raise HTTPException(status_code=503, detail="Advancement tracker not available")

        gap_closure_status = orchestrator.advancement_tracker.get_gap_closure_status(project_id)

        return APIResponse(
            success=True,
            status="success",
            data={
                "gap_closure_status": gap_closure_status,
                "total_gaps": getattr(project, "total_gaps", 20),
                "closed_gaps": len(getattr(project, "closed_gaps", [])),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting gap closure status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get gap closure status",
        )


# ============================================================================
# Completeness Metrics Endpoint
# ============================================================================

@router.get(
    "/{project_id}/advancement/completeness",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specification completeness",
)
async def get_completeness_metrics(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get specification completeness metrics.

    Returns overall and per-category completeness scores.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        APIResponse with completeness metrics
    """
    try:
        logger.info(f"Getting completeness metrics for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        from socrates_api.orchestrator import APIOrchestrator
        orchestrator = APIOrchestrator()

        if not orchestrator.advancement_tracker:
            raise HTTPException(status_code=503, detail="Advancement tracker not available")

        total_gaps = getattr(project, "total_gaps", 20)
        identified_gaps = len(getattr(project, "identified_gaps", []))
        closed_gaps = len(getattr(project, "closed_gaps", []))

        completeness = orchestrator.advancement_tracker.calculate_completeness(
            project_id=project_id,
            total_gaps=total_gaps,
            identified_gaps=identified_gaps,
            closed_gaps=closed_gaps,
            project_specs=getattr(project, "specifications", {})
        )

        return APIResponse(
            success=True,
            status="success",
            data={
                "overall": int(completeness.overall * 100),
                "by_category": {k: int(v * 100) for k, v in completeness.by_category.items()},
                "trend": completeness.trend,
                "projected_completion": completeness.projected_completion,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting completeness metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get completeness metrics",
        )


# ============================================================================
# Advancement Metrics Endpoint
# ============================================================================

@router.get(
    "/{project_id}/advancement/metrics",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get advancement metrics",
)
async def get_advancement_metrics(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get full advancement metrics including phase readiness prediction.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        APIResponse with advancement metrics
    """
    try:
        logger.info(f"Getting advancement metrics for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        from socrates_api.orchestrator import APIOrchestrator
        orchestrator = APIOrchestrator()

        if not orchestrator.advancement_tracker:
            raise HTTPException(status_code=503, detail="Advancement tracker not available")

        maturity = getattr(project, "phase_maturity", {}).get(project.phase, 0.5)
        total_gaps = getattr(project, "total_gaps", 20)
        closed_gaps = len(getattr(project, "closed_gaps", []))
        question_count = len(getattr(project, "asked_questions", []))

        metrics = orchestrator.advancement_tracker.calculate_advancement_metrics(
            project_id=project_id,
            phase=project.phase,
            maturity=maturity / 100.0 if maturity > 1 else maturity,
            total_gaps=total_gaps,
            closed_gaps=closed_gaps,
            question_count=question_count
        )

        return APIResponse(
            success=True,
            status="success",
            data={
                "phase": metrics.phase,
                "maturity": int(metrics.maturity * 100),
                "quality_score": int(metrics.quality_score * 100),
                "gap_closure_rate": int(metrics.gap_closure_rate * 100),
                "confidence": int(metrics.confidence * 100),
                "readiness": {
                    "can_advance": metrics.readiness.get("can_advance", False),
                    "ready_percentage": int(metrics.readiness.get("ready_percentage", 0)),
                    "required_percentage": int(metrics.readiness.get("required_percentage", 100)),
                    "estimated_days": metrics.readiness.get("estimated_days", 0),
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting advancement metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get advancement metrics",
        )


# ============================================================================
# Dashboard Data Endpoint
# ============================================================================

@router.get(
    "/{project_id}/advancement/dashboard",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get advancement dashboard data",
)
async def get_advancement_dashboard(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get aggregated dashboard data for advancement visualization.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        APIResponse with dashboard data ready for visualization
    """
    try:
        logger.info(f"Getting advancement dashboard for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        from socrates_api.orchestrator import APIOrchestrator
        orchestrator = APIOrchestrator()

        if not orchestrator.progress_dashboard or not orchestrator.metrics_service:
            raise HTTPException(status_code=503, detail="Dashboard services not available")

        maturity = getattr(project, "phase_maturity", {}).get(project.phase, 50) / 100.0
        total_gaps = getattr(project, "total_gaps", 20)
        closed_gaps = len(getattr(project, "closed_gaps", []))
        questions_answered = len(getattr(project, "asked_questions", []))

        dashboard = orchestrator.progress_dashboard.get_dashboard_data(
            project_id=project_id,
            current_phase=project.phase,
            completeness=closed_gaps / max(total_gaps, 1),
            gap_closure_percentage=closed_gaps / max(total_gaps, 1),
            maturity=maturity,
            quality_score=0.75,
            advancement_confidence=0.8,
            questions_answered=questions_answered,
            total_gaps=total_gaps,
        )

        return APIResponse(
            success=True,
            status="success",
            data={
                "overall_progress": int(dashboard.overall_progress * 100),
                "current_phase": dashboard.current_phase,
                "completeness": int(dashboard.completeness * 100),
                "maturity": int(dashboard.maturity * 100),
                "gap_closure": int(dashboard.gap_closure_percentage * 100),
                "quality_score": int(dashboard.quality_score * 100),
                "confidence": int(dashboard.advancement_confidence * 100),
                "questions_answered": dashboard.questions_answered,
                "total_gaps": dashboard.total_gaps,
                "estimated_completion": dashboard.estimated_completion_date,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting advancement dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get advancement dashboard",
        )


# ============================================================================
# Progress History Endpoint
# ============================================================================

@router.get(
    "/{project_id}/advancement/history",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get progress history",
)
async def get_progress_history(
    project_id: str,
    days: int = 30,
    current_user: str = Depends(get_current_user),
):
    """
    Get historical progress data for trend analysis.

    Args:
        project_id: Project ID
        days: Number of days to retrieve (default 30)
        current_user: Authenticated user

    Returns:
        APIResponse with historical progress data
    """
    try:
        logger.info(f"Getting progress history for project {project_id} ({days} days)")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        from socrates_api.orchestrator import APIOrchestrator
        orchestrator = APIOrchestrator()

        if not orchestrator.progress_dashboard:
            raise HTTPException(status_code=503, detail="Dashboard service not available")

        timeline = orchestrator.progress_dashboard.get_progress_timeline(project_id, days)

        snapshots = []
        for snapshot in timeline.snapshots:
            snapshots.append({
                "timestamp": snapshot.timestamp,
                "phase": snapshot.phase,
                "completeness": int(snapshot.completeness * 100),
                "gap_closure": int(snapshot.gap_closure_percentage * 100),
                "maturity": int(snapshot.maturity * 100),
                "questions_answered": snapshot.questions_answered,
                "quality_score": int(snapshot.quality_score * 100),
            })

        return APIResponse(
            success=True,
            status="success",
            data={
                "snapshots": snapshots,
                "total_records": timeline.record_count,
                "oldest_timestamp": timeline.oldest_timestamp,
                "newest_timestamp": timeline.newest_timestamp,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get progress history",
        )


# ============================================================================
# Learning Effectiveness Endpoint
# ============================================================================

@router.get(
    "/{project_id}/learning/effectiveness",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get question effectiveness scores",
)
async def get_learning_effectiveness(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get question effectiveness scores and learning metrics.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        APIResponse with learning effectiveness data
    """
    try:
        logger.info(f"Getting learning effectiveness for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        from socrates_api.orchestrator import APIOrchestrator
        orchestrator = APIOrchestrator()

        if not orchestrator.learning_service:
            raise HTTPException(status_code=503, detail="Learning service not available")

        asked_questions = getattr(project, "asked_questions", [])

        question_scores = []
        for q in asked_questions:
            score = orchestrator.learning_service.score_question_effectiveness(
                question_id=q.get("question_id", ""),
                question_text=q.get("question", ""),
                answer_text=q.get("answer", ""),
                answer_quality=0.7,
                gaps_addressed=1,
                success_rate=0.8
            )
            question_scores.append({
                "question_id": q.get("question_id", ""),
                "question": q.get("question", ""),
                "effectiveness_score": int(score.effectiveness_score * 100),
                "answer_quality": int(score.answer_quality * 100),
                "gap_closure_value": int(score.gap_closure_value * 100),
                "success_rate": int(score.success_rate * 100),
            })

        summary = orchestrator.learning_service.get_learning_summary(
            project_id=project_id,
            asked_questions=asked_questions
        )

        return APIResponse(
            success=True,
            status="success",
            data={
                "question_scores": question_scores,
                "average_effectiveness": int(summary.overall_effectiveness * 100) if summary else 70,
                "total_questions": len(question_scores),
                "high_effectiveness_count": sum(1 for q in question_scores if q["effectiveness_score"] >= 75),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning effectiveness: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get learning effectiveness",
        )


# ============================================================================
# Optimization Recommendations Endpoint
# ============================================================================

@router.post(
    "/{project_id}/learning/optimize",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get optimization recommendations",
)
async def get_optimization_recommendations(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get recommendations to optimize future questions based on learning analysis.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        APIResponse with optimization recommendations
    """
    try:
        logger.info(f"Getting optimization recommendations for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        from socrates_api.orchestrator import APIOrchestrator
        orchestrator = APIOrchestrator()

        if not orchestrator.learning_service:
            raise HTTPException(status_code=503, detail="Learning service not available")

        asked_questions = getattr(project, "asked_questions", [])

        if not asked_questions:
            return APIResponse(
                success=True,
                status="success",
                data={
                    "recommendations": [],
                    "message": "Insufficient data for recommendations",
                },
            )

        patterns = orchestrator.learning_service.detect_answer_patterns(
            project_id=project_id,
            answers=[q.get("answer", "") for q in asked_questions]
        )

        recommendations = orchestrator.learning_service.generate_optimization_recommendations(
            project_id=project_id,
            question_history=asked_questions,
            patterns=patterns
        )

        rec_data = []
        for rec in recommendations:
            rec_data.append({
                "type": rec.recommendation_type,
                "priority": rec.priority,
                "description": rec.description,
                "impact_score": int(rec.impact_score * 100),
                "implementation_effort": rec.effort_estimate,
            })

        return APIResponse(
            success=True,
            status="success",
            data={
                "recommendations": rec_data,
                "detected_patterns": {
                    "length_distribution": patterns.length_distribution if hasattr(patterns, "length_distribution") else "balanced",
                    "focus_areas": patterns.technical_focus if hasattr(patterns, "technical_focus") else [],
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get optimization recommendations",
        )
