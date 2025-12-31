"""
Project Progress Tracking API endpoints for Socrates.

Provides REST endpoints for tracking project progress including:
- Getting overall project progress
- Tracking completion status and milestones
- Reporting progress metrics and trends
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["progress"])


@router.get(
    "/{project_id}/progress",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get overall project progress",
)
async def get_progress(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get overall progress of the project.

    Args:
        project_id: Project identifier
        current_user: Authenticated user

    Returns:
        SuccessResponse with project progress details
    """
    try:
        logger.info(f"Getting progress for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Calculate progress metrics
        progress_data = {
            "project_id": project_id,
            "project_name": project.name,
            "status": getattr(project, "status", "active"),
            "created_at": getattr(project, "created_at", None),
            "updated_at": getattr(project, "updated_at", None),
        }

        # Conversation progress
        conversation_count = len(getattr(project, "conversation_history", []) or [])
        progress_data["conversation_progress"] = {
            "total_messages": conversation_count,
            "last_message_at": None,
        }
        if conversation_count > 0:
            last_msg = getattr(project, "conversation_history", [])[-1]
            progress_data["conversation_progress"]["last_message_at"] = (
                last_msg.get("timestamp") if isinstance(last_msg, dict) else str(last_msg)
            )

        # Code generation progress
        generated_code_count = len(
            [
                msg
                for msg in getattr(project, "conversation_history", []) or []
                if isinstance(msg, dict) and msg.get("type") == "code"
            ]
        )
        progress_data["code_generation_progress"] = {
            "total_code_blocks": generated_code_count,
        }

        # Maturity progress
        progress_data["maturity_progress"] = {
            "current_score": getattr(project, "maturity_score", 0),
            "previous_score": getattr(project, "previous_maturity", 0),
            "improvement": getattr(project, "maturity_score", 0)
            - getattr(project, "previous_maturity", 0),
        }

        # Phase progress
        phase_scores = getattr(project, "phase_maturity_scores", {})
        progress_data["phase_progress"] = {
            "current_phase": getattr(project, "current_phase", "planning"),
            "phase_scores": phase_scores,
            "total_phases": len(phase_scores),
            "completed_phases": sum(1 for score in phase_scores.values() if score >= 80),
        }

        # Category progress
        category_scores = getattr(project, "category_scores", {})
        progress_data["category_progress"] = {
            "total_categories": len(category_scores),
            "categories": category_scores,
            "average_category_score": (
                sum(category_scores.values()) / len(category_scores) if category_scores else 0
            ),
        }

        # Skills progress
        skills = getattr(project, "skills", []) or []
        progress_data["skills_progress"] = {
            "total_skills": len(skills),
            "proficiency_breakdown": {
                "beginner": len([s for s in skills if s.get("proficiency_level") == "beginner"]),
                "intermediate": len(
                    [s for s in skills if s.get("proficiency_level") == "intermediate"]
                ),
                "advanced": len([s for s in skills if s.get("proficiency_level") == "advanced"]),
                "expert": len([s for s in skills if s.get("proficiency_level") == "expert"]),
            },
        }

        # Knowledge progress
        knowledge = getattr(project, "knowledge_base", []) or []
        progress_data["knowledge_progress"] = {
            "total_items": len(knowledge),
            "pinned_items": len([k for k in knowledge if k.get("pinned", False)]),
        }

        # Calculate overall completion percentage
        completion_metrics = []
        if conversation_count > 0:
            completion_metrics.append(min(100, conversation_count * 10))
        if generated_code_count > 0:
            completion_metrics.append(min(100, generated_code_count * 20))
        if getattr(project, "maturity_score", 0) > 0:
            completion_metrics.append(getattr(project, "maturity_score", 0))
        if len(skills) > 0:
            completion_metrics.append(min(100, len(skills) * 5))

        overall_progress = (
            sum(completion_metrics) / len(completion_metrics) if completion_metrics else 0
        )

        progress_data["overall_progress"] = {
            "percentage": round(overall_progress, 1),
            "status": (
                "not_started"
                if overall_progress == 0
                else "in_progress" if overall_progress < 100 else "completed"
            ),
        }

        return SuccessResponse(
            success=True,
            message="Project progress retrieved successfully",
            data=progress_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}",
        )


@router.get(
    "/{project_id}/progress/status",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed progress status",
)
async def get_progress_status(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get detailed progress status with milestone tracking and trends.

    Args:
        project_id: Project identifier
        current_user: Authenticated user

    Returns:
        SuccessResponse with detailed status information
    """
    try:
        logger.info(f"Getting progress status for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get maturity history
        maturity_history = getattr(project, "maturity_history", []) or []

        # Calculate trends
        recent_history = maturity_history[-5:] if len(maturity_history) > 5 else maturity_history
        trend = "stable"
        if len(recent_history) >= 2:
            recent_scores = [h.get("score", 0) for h in recent_history]
            if recent_scores[-1] > recent_scores[0]:
                trend = "improving"
            elif recent_scores[-1] < recent_scores[0]:
                trend = "declining"

        # Identify milestones
        milestones = []
        if len(getattr(project, "conversation_history", []) or []) >= 5:
            milestones.append("Started learning project")
        if getattr(project, "maturity_score", 0) >= 50:
            milestones.append("Reached 50% maturity")
        if getattr(project, "maturity_score", 0) >= 80:
            milestones.append("Reached 80% maturity")
        if len(getattr(project, "skills", []) or []) >= 5:
            milestones.append("Acquired 5+ skills")
        if len(getattr(project, "knowledge_base", []) or []) >= 10:
            milestones.append("Built knowledge base with 10+ items")

        # Build status response
        status_data = {
            "project_id": project_id,
            "project_name": project.name,
            "current_status": getattr(project, "status", "active"),
            "current_maturity": getattr(project, "maturity_score", 0),
            "milestones": {
                "completed": milestones,
                "total": 5,
                "completion_rate": f"{(len(milestones) / 5 * 100):.1f}%",
            },
            "trend": {
                "direction": trend,
                "recent_change": (
                    f"{round(recent_history[-1].get('score', 0) - recent_history[0].get('score', 0), 1)} points"
                    if len(recent_history) >= 2
                    else "No data"
                ),
                "last_update": recent_history[-1].get("timestamp") if recent_history else None,
            },
            "phase_status": {
                "current": getattr(project, "current_phase", "planning"),
                "phases": getattr(project, "phase_maturity_scores", {}),
            },
            "quality_metrics": {
                "categories": getattr(project, "category_scores", {}),
                "analytics": getattr(project, "analytics_metrics", {}),
            },
            "learning_metrics": {
                "total_conversations": len(getattr(project, "conversation_history", []) or []),
                "total_skills": len(getattr(project, "skills", []) or []),
                "knowledge_items": len(getattr(project, "knowledge_base", []) or []),
            },
            "recommendations": _generate_recommendations(project),
        }

        return SuccessResponse(
            success=True,
            message="Progress status retrieved successfully",
            data=status_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress status: {str(e)}",
        )


def _generate_recommendations(project) -> list:
    """Generate recommendations based on project progress."""
    recommendations = []

    maturity = getattr(project, "maturity_score", 0)
    if maturity < 30:
        recommendations.append("Continue working on project foundations")
    if maturity < 50:
        recommendations.append("Focus on core concepts and skills development")
    if maturity >= 50 and maturity < 80:
        recommendations.append("Work on advanced topics and integration")

    skills = getattr(project, "skills", []) or []
    if len(skills) < 3:
        recommendations.append("Build more diverse skills in this project")

    knowledge = getattr(project, "knowledge_base", []) or []
    if len(knowledge) < 5:
        recommendations.append("Document more knowledge items for future reference")

    category_scores = getattr(project, "category_scores", {})
    if category_scores:
        low_categories = [k for k, v in category_scores.items() if v < 50]
        if low_categories:
            recommendations.append(f"Improve in areas: {', '.join(low_categories)}")

    if len(recommendations) == 0:
        recommendations.append("Continue making progress on your project goals")

    return recommendations
