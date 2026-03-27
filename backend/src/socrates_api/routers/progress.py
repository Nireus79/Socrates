"""
Project Progress Tracking API endpoints for Socrates.

Provides REST endpoints for tracking project progress including:
- Getting overall project progress
- Tracking completion status and milestones
- Reporting progress metrics and trends
"""

import logging
from socrates_api.models_local import ProjectContext

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.database import get_database, LocalDatabase
from socrates_api.auth.project_access import check_project_access
# Database import replaced with local module
from socrates_api.models import APIResponse
from socrates_api.models_local import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["progress"])


@router.get(
    "/{project_id}/progress",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get overall project progress",
)
async def get_progress(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Get overall progress of the project.

    Args:
        project_id: Project identifier
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with project progress details
    """
    try:
        await check_project_access(project_id, current_user, db, min_role="viewer")

        logger.info(f"Getting progress for project {project_id}")
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # SECURITY FIX: Allow team members with viewer+ role
        await check_project_access(project_id, current_user, db, min_role="viewer")

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
                last_msg.get("timestamp")
            )

        # Code generation progress
        generated_code_count = len(
            [
                msg
                for msg in getattr(project, "conversation_history", []) or []
                if isinstance(msg, dict) and msg.get("mode") == "code"
            ]
        )
        progress_data["code_generation_progress"] = {
            "total_code_blocks": generated_code_count,
        }

        # Maturity progress
        maturity_score = project.maturity_score if hasattr(project, 'maturity_score') else 0.0
        previous_maturity = project.previous_maturity if hasattr(project, 'previous_maturity') else 0.0

        progress_data["maturity_progress"] = {
            "current_score": float(maturity_score),
            "previous_score": float(previous_maturity),
            "improvement": float(maturity_score) - float(previous_maturity),
        }

        # Phase progress
        phase_scores = project.phase_maturity_scores if hasattr(project, 'phase_maturity_scores') else {}
        completed = 0
        for phase, score in phase_scores.items():
            if float(score) >= 80:
                completed += 1

        progress_data["phase_progress"] = {
            "current_phase": project.phase if hasattr(project, 'phase') else "planning",
            "phase_scores": {k: float(v) for k, v in phase_scores.items()},
            "total_phases": len(phase_scores),
            "completed_phases": completed,
        }

        # Category progress
        category_scores = project.category_scores if hasattr(project, 'category_scores') else {}
        numeric_values = [float(score) for score in category_scores.values()]
        average_score = sum(numeric_values) / len(numeric_values) if numeric_values else 0.0

        progress_data["category_progress"] = {
            "total_categories": len(category_scores),
            "categories": {k: float(v) for k, v in category_scores.items()},
            "average_category_score": average_score,
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

        # Use the actual project progress field (0-100) stored in database
        # This is the authoritative progress value, not calculated from metrics
        project_progress = getattr(project, "progress", 0)
        try:
            project_progress = int(project_progress) if project_progress else 0
        except (TypeError, ValueError):
            project_progress = 0

        # Ensure progress is within 0-100 range
        project_progress = max(0, min(100, project_progress))

        progress_data["overall_progress"] = {
            "percentage": project_progress,
            "status": (
                "not_started"
                if project_progress == 0
                else "in_progress" if project_progress < 100 else "completed"
            ),
        }

        return APIResponse(
            success=True,
        status="success",
            message="Project progress retrieved successfully",
            data=progress_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/{project_id}/progress/status",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed progress status",
)
async def get_progress_status(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Get detailed progress status with milestone tracking and trends.

    Args:
        project_id: Project identifier
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with detailed status information
    """
    try:
        await check_project_access(project_id, current_user, db, min_role="viewer")

        logger.info(f"Getting progress status for project {project_id}")
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # SECURITY FIX: Allow team members with viewer+ role
        await check_project_access(project_id, current_user, db, min_role="viewer")

        # Get maturity history
        maturity_history = getattr(project, "maturity_history", []) or []

        # Calculate trends
        recent_history = maturity_history[-5:] if len(maturity_history) > 5 else maturity_history
        trend = "stable"
        recent_scores = []  # Initialize before the if block
        if len(recent_history) >= 2:
            # Extract scores safely, handling various data types
            for h in recent_history:
                if isinstance(h, dict):
                    score = h.get("score", 0)
                else:
                    score = getattr(h, "score", 0)
                # Ensure score is numeric
                try:
                    score = float(score) if score else 0.0
                except (TypeError, ValueError):
                    score = 0.0
                recent_scores.append(score)

            if len(recent_scores) >= 2:
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
                    f"{round(float(recent_scores[-1] if isinstance(recent_scores[-1], (int, float)) else 0) - float(recent_scores[0] if isinstance(recent_scores[0], (int, float)) else 0), 1)} points"
                    if len(recent_scores) >= 2
                    else "No data"
                ),
                "last_update": recent_history[-1].get("timestamp") if recent_history and isinstance(recent_history[-1], dict) else (getattr(recent_history[-1], "timestamp", None) if recent_history else None),
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

        return APIResponse(
            success=True,
        status="success",
            message="Progress status retrieved successfully",
            data=status_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
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


@router.get(
    "/{project_id}/stats",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project statistics",
)
async def get_project_stats(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Get project statistics including message count, insights, and questions.

    Args:
        project_id: Project identifier
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with project statistics
    """
    try:
        await check_project_access(project_id, current_user, db, min_role="viewer")

        logger.info(f"Getting stats for project {project_id}")
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # SECURITY FIX: Allow team members with viewer+ role
        await check_project_access(project_id, current_user, db, min_role="viewer")

        # Count conversation messages
        conversation_history = getattr(project, "conversation_history", []) or []
        message_count = len(conversation_history)

        # Count insights (messages with type='insight')
        insight_count = len(
            [msg for msg in conversation_history if msg.get("type") == "insight"]
        )

        # Count questions (messages with type='question')
        question_count = len(
            [msg for msg in conversation_history if msg.get("mode") == "question"]
        )

        # Count code blocks generated
        code_count = len(
            [msg for msg in conversation_history if msg.get("mode") == "code"]
        )

        # Get current phase
        current_phase = getattr(project, "phase", "discovery")

        # Get maturity score
        maturity_score = getattr(project, "maturity", 0)

        # Get team info
        team_members = getattr(project, "team_members", []) or []
        collaborator_count = len(team_members)

        stats_data = {
            "project_id": project_id,
            "project_name": project.name,
            "message_count": message_count,
            "insight_count": insight_count,
            "question_count": question_count,
            "code_count": code_count,
            "current_phase": current_phase,
            "maturity_score": maturity_score,
            "collaborator_count": collaborator_count,
            "created_at": getattr(project, "created_at", None),
            "updated_at": getattr(project, "updated_at", None),
        }

        return APIResponse(
            success=True,
        status="success",
            message="Project statistics retrieved successfully",
            data=stats_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )
