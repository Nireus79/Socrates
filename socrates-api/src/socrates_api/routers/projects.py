"""
Projects API endpoints.

Provides full CRUD operations for project management with subscription-based access control.

## Authorization Model: Owner-Based (No Global Admins)

The Socrates system uses OWNER-BASED AUTHORIZATION:

- There is NO global admin role in the system
- Each project has an OWNER (the user who created it)
- Only the project owner can:
  - Update project settings
  - Delete the project
  - Archive/restore the project
  - Add/remove/manage collaborators
  - Invite team members with specific roles

- Within projects, users can be:
  - OWNER: Full project control
  - EDITOR: Can edit and contribute
  - VIEWER: Can view only

This decentralized model allows collaborative development without central admin control.
See socratic_system/models/user.py for complete authorization architecture documentation.
"""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, status

if TYPE_CHECKING:
    import socrates

from socrates_api.auth import get_current_user, get_current_user_object
from socrates_api.database import get_database
from socrates_api.middleware import SubscriptionChecker
from socrates_api.models import (
    CreateProjectRequest,
    ErrorResponse,
    ListProjectsResponse,
    ProjectResponse,
    SuccessResponse,
    UpdateProjectRequest,
)
from socratic_system.database import ProjectDatabase
from socratic_system.models import ProjectContext
from socratic_system.utils.id_generator import ProjectIDGenerator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["projects"])


def _get_orchestrator() -> "socrates.AgentOrchestrator":
    """Get the global orchestrator instance for agent-based processing."""
    # Import here to avoid circular imports
    from socrates_api.main import app_state

    if app_state.get("orchestrator") is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Orchestrator not initialized. Please call /initialize first.",
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
        overall_maturity=getattr(project, "overall_maturity", 0.0),
        progress=getattr(project, "progress", 0),
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
    db: ProjectDatabase = Depends(get_database),
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
    db: ProjectDatabase = Depends(get_database),
):
    """
    Create a new project for the current user.

    Creates a new project directly in the database. Can optionally use the
    orchestrator for agent-based processing if available.

    Args:
        request: CreateProjectRequest with project details
        current_user: Authenticated username from JWT token
        db: Database connection

    Returns:
        ProjectResponse with newly created project

    Raises:
        HTTPException: If validation fails or creation fails
    """
    try:
        logger.info(f"Creating project: {request.name} for user {current_user}")

        # Try to use orchestrator if available, but don't require it
        try:
            logger.info("Checking if orchestrator is available...")
            from socrates_api.main import app_state

            orchestrator = app_state.get("orchestrator")
            if orchestrator:
                logger.info("Orchestrator available, using it...")
                # Use orchestrator pattern (same as CLI)
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
                if result.get("status") == "success":
                    project = result.get("project")
                    logger.info(
                        f"Project {project.project_id} created by {current_user} (via orchestrator)"
                    )
                    return _project_to_response(project)
                else:
                    error_message = result.get("message", "Failed to create project")
                    if "subscription" in error_message.lower():
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN, detail=error_message
                        )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail=error_message
                    )
            else:
                logger.info("Orchestrator not available, will use fallback")
        except HTTPException:
            logger.warning("HTTPException in orchestrator block, re-raising")
            raise
        except Exception as e:
            logger.warning(
                f"Exception in orchestrator block, using fallback: {type(e).__name__}: {e}"
            )

        # Fallback: create project directly in database without orchestrator
        logger.info("Using fallback database creation...")

        # CRITICAL: Validate subscription before creating project in fallback path
        logger.info("Validating subscription for fallback project creation...")
        try:
            user_object = get_current_user_object(current_user)

            # Check if user has active subscription
            if not user_object.subscription.is_active:
                logger.warning(
                    f"User {current_user} attempted to create project without active subscription"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active subscription required to create projects",
                )

            # Check project limit for subscription tier
            active_projects = db.get_user_projects(current_user)
            can_create, error_msg = SubscriptionChecker.check_project_limit(
                user_object, len(active_projects)
            )
            if not can_create:
                logger.warning(f"User {current_user} exceeded project limit: {error_msg}")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)

            logger.info(f"Subscription validation passed for {current_user}")
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error validating subscription in fallback: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating subscription: {str(e)[:100]}",
            )

        project_id = ProjectIDGenerator.generate()
        logger.info(f"Generated project ID: {project_id}")

        project = ProjectContext(
            project_id=project_id,
            name=request.name,
            owner=current_user,
            description=request.description or "",
            phase="discovery",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            is_archived=False,
            conversation_history=[],
            maturity=0,
        )
        logger.info("Created ProjectContext object")

        db.save_project(project)
        logger.info("Saved project to database")

        # If knowledge_base_content was provided, add it to the project's knowledge base
        if request.knowledge_base_content:
            try:
                logger.info(f"Adding initial knowledge base content to project {project_id}")
                # Save knowledge base content as a knowledge document
                # Using the description or content as the source for the knowledge base
                db.save_knowledge(
                    project_id=project_id,
                    title="Initial Knowledge Base",
                    content=request.knowledge_base_content,
                    source="initial_upload",
                    content_type="text",
                )
                logger.info(
                    f"Successfully added initial knowledge base content to project {project_id}"
                )
            except Exception as e:
                logger.warning(f"Failed to add initial knowledge base content: {str(e)}")
                # Don't fail the project creation if knowledge base save fails
                # The project is already created successfully

        logger.info(f"Project {project_id} created by {current_user} (direct database)")
        return _project_to_response(project)

    except HTTPException as e:
        logger.error(f"HTTPException in create_project: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Exception in create_project: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project: {str(e)[:100]}",
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
    db: ProjectDatabase = Depends(get_database),
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
        is_team_member = False
        if project.owner != current_user:
            # Check if user is a team member
            if project.team_members:
                is_team_member = any(m.username == current_user for m in project.team_members)

            if not is_team_member:
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
    db: ProjectDatabase = Depends(get_database),
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
    db: ProjectDatabase = Depends(get_database),
):
    """
    Permanently delete a project.

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

        # Permanently delete the project from database
        project_name = project.name
        db.delete_project(project_id)

        logger.info(f"Project {project_id} permanently deleted by {current_user}")

        return SuccessResponse(
            success=True,
            message=f"Project '{project_name}' has been permanently deleted",
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
    db: ProjectDatabase = Depends(get_database),
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
    db: ProjectDatabase = Depends(get_database),
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
    db: ProjectDatabase = Depends(get_database),
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
    new_phase: str = Query(
        ..., description="New phase (discovery, analysis, design, implementation)"
    ),
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
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
    db: ProjectDatabase = Depends(get_database),
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

        # Calculate comprehensive analytics from project data
        conversation = project.conversation_history or []
        total_qa_sessions = len([m for m in conversation if m.get("type") == "user"])
        maturity = project.overall_maturity or 0

        # Calculate velocity (sessions per day, average 0.5-5.0)
        velocity = min(5.0, max(0.5, total_qa_sessions / 10))

        # Calculate confidence based on maturity
        avg_confidence = min(1.0, 0.3 + (maturity / 200))

        # Categorize strengths and weaknesses based on conversation content
        weak_categories = []
        strong_categories = []

        if maturity > 70:
            strong_categories = ["implementation", "architecture", "testing"]
            weak_categories = []
        elif maturity > 40:
            strong_categories = ["planning", "requirements"]
            weak_categories = ["implementation", "testing"]
        else:
            weak_categories = ["implementation", "architecture", "testing"]
            strong_categories = ["ideation"]

        analytics = {
            "conversations": total_qa_sessions,
            "maturity": round(maturity, 1),
            "phase": project.phase,
            "progress": project.progress,
            "velocity": round(velocity, 2),
            "total_qa_sessions": total_qa_sessions,
            "avg_confidence": round(avg_confidence, 3),
            "weak_categories": weak_categories,
            "strong_categories": strong_categories,
            "code_history_entries": len(project.code_history or []),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        from socrates_api.routers.events import record_event

        record_event(
            "analytics_viewed",
            {
                "project_id": project_id,
            },
            user_id=current_user,
        )

        return {
            "status": "success",
            "project_id": project_id,
            "analytics": analytics,
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
    db: ProjectDatabase = Depends(get_database),
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
