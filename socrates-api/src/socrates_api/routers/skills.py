"""
Skills Management API endpoints for Socrates.

Provides REST endpoints for tracking and managing project skills including:
- Adding and updating project skills
- Listing acquired skills with proficiency levels
- Tracking skill progress and improvement
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends, Body

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["skills"])


@router.post(
    "/{project_id}/skills",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set or update project skills",
)
async def set_skills(
    project_id: str,
    skill_name: str = Body(...),
    proficiency_level: Optional[str] = Body("beginner"),
    confidence: Optional[float] = Body(0.5),
    notes: Optional[str] = Body(None),
    current_user: str = Depends(get_current_user),
):
    """
    Set or update a skill in the project.

    Args:
        project_id: Project identifier
        skill_name: Name of the skill (e.g., "Python", "REST API Design", "Unit Testing")
        proficiency_level: Level of proficiency (beginner, intermediate, advanced, expert)
        confidence: Confidence score (0.0-1.0) in understanding the skill
        notes: Optional notes about the skill
        current_user: Authenticated user

    Returns:
        SuccessResponse with updated skill information
    """
    try:
        logger.info(f"Setting skill '{skill_name}' for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Validate proficiency level
        valid_levels = ["beginner", "intermediate", "advanced", "expert"]
        if proficiency_level not in valid_levels:
            proficiency_level = "beginner"

        # Validate confidence
        if confidence < 0 or confidence > 1:
            confidence = max(0, min(1, confidence))

        # Initialize skills if needed
        if not hasattr(project, "skills") or project.skills is None:
            project.skills = []

        # Check if skill already exists
        existing_skill = None
        for skill in project.skills:
            if skill.get("name").lower() == skill_name.lower():
                existing_skill = skill
                break

        if existing_skill:
            # Update existing skill
            existing_skill["proficiency_level"] = proficiency_level
            existing_skill["confidence"] = confidence
            existing_skill["notes"] = notes
            existing_skill["updated_at"] = datetime.now(timezone.utc).isoformat()
            existing_skill["update_count"] = existing_skill.get("update_count", 0) + 1
        else:
            # Create new skill
            skill_item = {
                "id": f"skill_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                "name": skill_name,
                "proficiency_level": proficiency_level,
                "confidence": confidence,
                "notes": notes,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": current_user,
                "update_count": 0,
                "progress_history": [
                    {
                        "level": proficiency_level,
                        "confidence": confidence,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            }
            project.skills.append(skill_item)
            existing_skill = skill_item

        # Persist changes
        db.save_project(project)

        logger.info(f"Skill '{skill_name}' updated: {proficiency_level}")

        return SuccessResponse(
            success=True,
            message=f"Skill '{skill_name}' set successfully",
            data={
                "skill_id": existing_skill.get("id"),
                "skill_name": skill_name,
                "proficiency_level": proficiency_level,
                "confidence": confidence,
                "created_at": existing_skill.get("created_at"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting skill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set skill: {str(e)}",
        )


@router.get(
    "/{project_id}/skills",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="List project skills",
)
async def list_skills(
    project_id: str,
    proficiency_level: Optional[str] = None,
    min_confidence: Optional[float] = None,
    sort_by: Optional[str] = "proficiency",
    current_user: str = Depends(get_current_user),
):
    """
    List all skills acquired in the project.

    Args:
        project_id: Project identifier
        proficiency_level: Optional filter by proficiency level
        min_confidence: Optional minimum confidence score (0.0-1.0)
        sort_by: Sort field (proficiency, confidence, name, created_at)
        current_user: Authenticated user

    Returns:
        SuccessResponse with list of skills and statistics
    """
    try:
        logger.info(f"Listing skills for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get skills
        skills = getattr(project, "skills", []) or []

        # Filter by proficiency level if specified
        if proficiency_level:
            skills = [s for s in skills if s.get("proficiency_level") == proficiency_level]

        # Filter by minimum confidence if specified
        if min_confidence is not None:
            skills = [s for s in skills if s.get("confidence", 0) >= min_confidence]

        # Calculate statistics
        level_distribution = {}
        total_confidence = 0
        for skill in skills:
            level = skill.get("proficiency_level", "unknown")
            level_distribution[level] = level_distribution.get(level, 0) + 1
            total_confidence += skill.get("confidence", 0)

        avg_confidence = total_confidence / len(skills) if skills else 0

        # Sort skills
        if sort_by == "confidence":
            skills.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        elif sort_by == "name":
            skills.sort(key=lambda x: x.get("name", "").lower())
        elif sort_by == "created_at":
            skills.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        else:  # Default: proficiency
            proficiency_rank = {"expert": 4, "advanced": 3, "intermediate": 2, "beginner": 1}
            skills.sort(
                key=lambda x: proficiency_rank.get(x.get("proficiency_level"), 0),
                reverse=True,
            )

        return SuccessResponse(
            success=True,
            message="Skills retrieved successfully",
            data={
                "project_id": project_id,
                "total_skills": len(skills),
                "skills": skills,
                "statistics": {
                    "level_distribution": level_distribution,
                    "average_confidence": round(avg_confidence, 2),
                    "proficiency_levels": {
                        "beginner": len([s for s in skills if s.get("proficiency_level") == "beginner"]),
                        "intermediate": len([s for s in skills if s.get("proficiency_level") == "intermediate"]),
                        "advanced": len([s for s in skills if s.get("proficiency_level") == "advanced"]),
                        "expert": len([s for s in skills if s.get("proficiency_level") == "expert"]),
                    },
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list skills: {str(e)}",
        )
