"""
Projects API endpoints.

Provides full CRUD operations for project management with subscription-based access control.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from fastapi import APIRouter, HTTPException, status, Depends, Query

if TYPE_CHECKING:
    import socrates

from socratic_system.database import ProjectDatabaseV2
from socratic_system.models import ProjectContext
from socratic_system.utils.id_generator import ProjectIDGenerator
from socrates_api.database import get_database
from socrates_api.auth import get_current_user, get_current_user_optional, get_current_user_object
from socrates_api.middleware import SubscriptionChecker, require_subscription_feature
from socrates_api.models import (
    ProjectResponse,
    ListProjectsResponse,
    CreateProjectRequest,
    UpdateProjectRequest,
    ErrorResponse,
    SuccessResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])


def _get_orchestrator() -> "socrates.AgentOrchestrator":
    """Get the global orchestrator instance for agent-based processing."""
    # Import here to avoid circular imports
    from socrates_api.main import app_state

    if app_state.get("orchestrator") is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Orchestrator not initialized. Please call /initialize first."
        )
    return app_state["orchestrator"]


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
        current_user: Current authenticated user (required for accessing projects)
        db: Database connection

    Returns:
        ListProjectsResponse with user's projects
    """
    try:
        # Load all projects for authenticated user, or return empty list if not authenticated

        # Load all projects for user
        projects = db.get_user_projects(current_user)

        project_responses = [_project_to_response(p) for p in projects]

        return ListProjectsResponse(projects=project_responses, total=len(project_responses))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing projects for {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving projects",
        )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Create new project",
    responses={
        200: {"description": "Project created successfully"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        403: {"description": "Subscription limit exceeded", "model": ErrorResponse},
    },
)
async def create_project(
    request: CreateProjectRequest,
    current_user: str = Depends(get_current_user),
    orchestrator = Depends(_get_orchestrator),
):
    """
    Create a new project for the current user.

    Uses the orchestrator-agent pattern to ensure proper validation,
    subscription checking, and business logic consistency with CLI.

    Args:
        request: CreateProjectRequest with project details
        current_user: Authenticated username from JWT token
        orchestrator: AgentOrchestrator instance for agent-based processing

    Returns:
        ProjectResponse with newly created project

    Raises:
        HTTPException: If validation fails, subscription check fails, or creation fails
    """
    try:
        # Use orchestrator pattern (same as CLI)
        # This ensures consistent validation and subscription checking
        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "create_project",
                "project_name": request.name,
                "owner": current_user,
                "project_type": request.knowledge_base_content or "general",
            },
        )

        # Check result status
        if result.get("status") != "success":
            error_message = result.get("message", "Failed to create project")
            # Return 403 for subscription errors
            if "subscription" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_message
                )
            # Return 400 for other errors
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )

        project = result.get("project")
        logger.info(f"Project {project.project_id} created by {current_user}")
        return _project_to_response(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating project",
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
    request: UpdateProjectRequest,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Update project metadata.

    Args:
        project_id: Project identifier
        request: UpdateProjectRequest with fields to update
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
        if request.name:
            project.name = request.name
        if request.phase:
            project.phase = request.phase

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
    new_phase: str = Query(..., description="New phase (discovery, analysis, design, implementation)"),
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


@router.get(
    "/{project_id}/files",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project files",
    responses={
        200: {"description": "Files retrieved successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_project_files(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get all files in a project.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse with list of project files
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

        # Return mock file structure
        files = [
            {
                "id": "file_1",
                "name": "main.py",
                "path": "/main.py",
                "type": "python",
                "size": 2048,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            },
            {
                "id": "file_2",
                "name": "utils.py",
                "path": "/utils.py",
                "type": "python",
                "size": 1024,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            },
            {
                "id": "file_3",
                "name": "requirements.txt",
                "path": "/requirements.txt",
                "type": "text",
                "size": 512,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
            },
        ]

        return SuccessResponse(
            success=True,
            message=f"Files retrieved for project {project_id}",
            data={
                "project_id": project_id,
                "files": files,
                "total": len(files),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting files for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving project files",
        )
