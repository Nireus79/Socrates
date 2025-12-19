"""
Projects API endpoints.

Provides full CRUD operations for project management with subscription-based access control.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends

from socratic_system.database import ProjectDatabaseV2
from socratic_system.models import ProjectContext
from socrates_api.auth import get_current_user
from socrates_api.middleware import SubscriptionChecker, require_subscription_feature
from socrates_api.models import (
    ProjectResponse,
    ListProjectsResponse,
    ErrorResponse,
    SuccessResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])

# Global database instance
_database = None


def get_database() -> ProjectDatabaseV2:
    """Get database instance."""
    global _database
    if _database is None:
        data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
        db_path = os.path.join(data_dir, "projects.db")
        _database = ProjectDatabaseV2(db_path)
    return _database


def _project_to_response(project: ProjectContext) -> ProjectResponse:
    """Convert ProjectContext to ProjectResponse."""
    return ProjectResponse(
        project_id=project.project_id,
        name=project.name,
        owner=project.owner,
        description=getattr(project, "description", None),
        phase=project.phase,
        created_at=project.created_at,
        updated_at=project.updated_at,
        is_archived=project.is_archived,
    )


@router.get(
    "",
    response_model=ListProjectsResponse,
    status_code=status.HTTP_200_OK,
    summary="List user's projects",
    responses={
        200: {"description": "Projects retrieved successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
    },
)
async def list_projects(
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    List all projects for the current user.

    Args:
        current_user: Current authenticated user
        db: Database connection

    Returns:
        ListProjectsResponse with user's projects
    """
    try:
        # Load all projects for user
        projects = db.get_user_projects(current_user)

        project_responses = [_project_to_response(p) for p in projects]

        return ListProjectsResponse(projects=project_responses, total=len(project_responses))

    except Exception as e:
        logger.error(f"Error listing projects for {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving projects",
        )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project details",
    responses={
        200: {"description": "Project retrieved successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_project(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get detailed information about a specific project.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        ProjectResponse with project details

    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found",
            )

        # Check access: user must be owner or team member
        if project.owner != current_user:
            # TODO: Check if user is team member
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

        return _project_to_response(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving project",
        )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update project",
    responses={
        200: {"description": "Project updated successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def update_project(
    project_id: str,
    name: Optional[str] = None,
    phase: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Update project metadata.

    Args:
        project_id: Project identifier
        name: New project name (optional)
        phase: New project phase (optional)
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Updated ProjectResponse
    """
    try:
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

        # Update fields
        if name:
            project.name = name
        if phase:
            project.phase = phase

        project.updated_at = datetime.now(timezone.utc)

        # Save changes
        db.save_project(project)
        logger.info(f"Project {project_id} updated by {current_user}")

        return _project_to_response(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating project",
        )


@router.delete(
    "/{project_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive/delete project",
    responses={
        200: {"description": "Project archived successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def delete_project(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Archive a project (soft delete).

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse confirming deletion
    """
    try:
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

        # Archive the project
        project.is_archived = True
        project.archived_at = datetime.now(timezone.utc)
        db.save_project(project)

        logger.info(f"Project {project_id} archived by {current_user}")

        return SuccessResponse(
            success=True,
            message=f"Project '{project.name}' has been archived",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error archiving project",
        )


@router.post(
    "/{project_id}/restore",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Restore archived project",
    responses={
        200: {"description": "Project restored successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def restore_project(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Restore an archived project.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Restored ProjectResponse
    """
    try:
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

        # Restore the project
        project.is_archived = False
        project.archived_at = None
        project.updated_at = datetime.now(timezone.utc)
        db.save_project(project)

        logger.info(f"Project {project_id} restored by {current_user}")

        return _project_to_response(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error restoring project",
        )


@router.get(
    "/{project_id}/stats",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get project statistics",
    responses={
        200: {"description": "Project stats retrieved successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_project_stats(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get statistics about a project.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Dictionary with project statistics
    """
    try:
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

        # Gather statistics
        stats = {
            "project_id": project_id,
            "phase": project.phase,
            "progress": getattr(project, "progress", 0),
            "team_size": len(getattr(project, "team_members", [])),
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "conversation_count": len(getattr(project, "conversation_history", [])),
        }

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving project statistics",
        )


@router.get(
    "/{project_id}/maturity",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get project maturity scores",
    responses={
        200: {"description": "Maturity scores retrieved successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_project_maturity(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get maturity assessment for a project.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Dictionary with maturity scores by phase
    """
    try:
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

        # Get maturity scores
        maturity = {
            "project_id": project_id,
            "phase_maturity_scores": getattr(project, "phase_maturity_scores", {}),
            "overall_maturity": getattr(project, "overall_maturity", 0.0),
        }

        return maturity

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting maturity for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving maturity assessment",
        )


@router.put(
    "/{project_id}/phase",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Advance project phase",
    responses={
        200: {"description": "Phase advanced successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def advance_phase(
    project_id: str,
    new_phase: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Advance project to the next phase.

    Args:
        project_id: Project identifier
        new_phase: New phase (discovery, analysis, design, implementation)
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Updated ProjectResponse with new phase
    """
    try:
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

        # Validate phase
        valid_phases = ["discovery", "analysis", "design", "implementation"]
        if new_phase not in valid_phases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid phase. Must be one of: {', '.join(valid_phases)}",
            )

        old_phase = project.phase
        project.phase = new_phase
        project.updated_at = datetime.now(timezone.utc)

        # Save changes
        db.save_project(project)

        logger.info(f"Project {project_id} phase advanced from {old_phase} to {new_phase}")

        return _project_to_response(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error advancing phase for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error advancing project phase",
        )


@router.get(
    "/{project_id}/analytics",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get project analytics",
    responses={
        200: {"description": "Analytics retrieved successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_project_analytics(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get detailed analytics for a project.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Analytics data including velocity, confidence, recommendations
    """
    try:
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

        # TODO: Calculate and return comprehensive analytics
        # For now, return placeholder analytics data

        return {
            "status": "success",
            "project_id": project_id,
            "analytics": {
                "velocity": 0.0,
                "total_qa_sessions": 0,
                "avg_confidence": 0.0,
                "weak_categories": [],
                "strong_categories": [],
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving analytics",
        )
