"""
Project Progress Tracking API endpoints for Socrates.

Provides REST endpoints for tracking project progress including:
- Getting overall project progress
- Tracking completion status and milestones
- Reporting progress metrics and trends
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import APIResponse, SuccessResponse

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

        # Maturity progress - safely convert dict values to numbers
        maturity_score = getattr(project, "maturity_score", 0)
        if isinstance(maturity_score, dict):
            maturity_score = maturity_score.get("score", 0)
        try:
            maturity_score = float(maturity_score) if maturity_score else 0.0
        except (TypeError, ValueError):
            maturity_score = 0.0

        previous_maturity = getattr(project, "previous_maturity", 0)
        if isinstance(previous_maturity, dict):
            previous_maturity = previous_maturity.get("score", 0)
        try:
            previous_maturity = float(previous_maturity) if previous_maturity else 0.0
        except (TypeError, ValueError):
            previous_maturity = 0.0

        progress_data["maturity_progress"] = {
            "current_score": maturity_score,
            "previous_score": previous_maturity,
            "improvement": maturity_score - previous_maturity,
        }

        # Phase progress
        phase_scores = getattr(project, "phase_maturity_scores", {})
        # Safely extract numeric values from phase scores (handle dict values)
        safe_phase_scores = {}
        completed = 0
        for phase, score in (phase_scores.items() if isinstance(phase_scores, dict) else []):
            if isinstance(score, dict):
                numeric_score = score.get("score", 0) if isinstance(score, dict) else score
            else:
                numeric_score = score
            try:
                numeric_score = float(numeric_score) if numeric_score else 0.0
            except (TypeError, ValueError):
                numeric_score = 0.0
            safe_phase_scores[phase] = numeric_score
            if numeric_score >= 80:
                completed += 1

        progress_data["phase_progress"] = {
            "current_phase": getattr(project, "current_phase", "planning"),
            "phase_scores": safe_phase_scores,
            "total_phases": len(safe_phase_scores),
            "completed_phases": completed,
        }

        # Category progress
        category_scores = getattr(project, "category_scores", {})
        # Safely convert category scores to numbers
        safe_category_scores = {}
        numeric_values = []
        for category, score in (category_scores.items() if isinstance(category_scores, dict) else []):
            if isinstance(score, dict):
                numeric_score = score.get("score", 0) if isinstance(score, dict) else score
            else:
                numeric_score = score
            try:
                numeric_score = float(numeric_score) if numeric_score else 0.0
            except (TypeError, ValueError):
                numeric_score = 0.0
            safe_category_scores[category] = numeric_score
            numeric_values.append(numeric_score)

        progress_data["category_progress"] = {
            "total_categories": len(safe_category_scores),
            "categories": safe_category_scores,
            "average_category_score": (
                sum(numeric_values) / len(numeric_values) if numeric_values else 0
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

        # Use already-converted maturity score from above
        if maturity_score > 0:
            completion_metrics.append(min(100, float(maturity_score)))
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
            detail=f"Failed to get progress: {str(e)}",
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


@router.get(
    "/{project_id}/stats",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project statistics",
)
async def get_project_stats(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get project statistics including message count, insights, and questions.

    Args:
        project_id: Project identifier
        current_user: Authenticated user

    Returns:
        SuccessResponse with project statistics
    """
    try:
        logger.info(f"Getting stats for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Count conversation messages
        conversation_history = getattr(project, "conversation_history", []) or []
        message_count = len(conversation_history)

        # Count insights (messages with type='insight')
        insight_count = len(
            [msg for msg in conversation_history if isinstance(msg, dict) and msg.get("type") == "insight"]
        )

        # Count questions (messages with type='question')
        question_count = len(
            [msg for msg in conversation_history if isinstance(msg, dict) and msg.get("type") == "question"]
        )

        # Count code blocks generated
        code_count = len(
            [msg for msg in conversation_history if isinstance(msg, dict) and msg.get("type") == "code"]
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
            detail=f"Failed to get project stats: {str(e)}",
        )
