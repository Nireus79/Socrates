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
from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

if TYPE_CHECKING:
    import socrates

from socrates_api.auth import get_current_user, get_current_user_object, get_current_user_object_optional
from socrates_api.database import get_database
from socrates_api.middleware import SubscriptionChecker
from socrates_api.models import (
    APIResponse,
    CreateProjectRequest,
    ErrorResponse,
    ListProjectsResponse,
    ProjectAnalyticsData,
    ProjectResponse,
    SuccessResponse,
    UpdateProjectRequest,
)
from socratic_system.database import ProjectDatabase
from socratic_system.models import ProjectContext, User
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
    response_model=APIResponse,
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

        project_responses = [_project_to_response(p).dict() if hasattr(_project_to_response(p), 'dict') else _project_to_response(p) for p in projects]

        return APIResponse(
            success=True,
            status="success",
            message="Projects retrieved successfully",
            data={"projects": project_responses, "total": len(project_responses)},
        )

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
    response_model=APIResponse,
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
    user_object: Optional[User] = Depends(get_current_user_object_optional),
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

        # CRITICAL: Check subscription limit BEFORE attempting to create project
        # This must happen regardless of whether orchestrator is used
        logger.info("Checking subscription limits...")
        try:
            # Determine subscription tier - default to free if user not in DB yet
            subscription_tier = "free"
            if user_object:
                subscription_tier = getattr(user_object, "subscription_tier", "free")

            # Check project limit for subscription tier
            active_projects = db.get_user_projects(current_user)
            can_create, error_msg = SubscriptionChecker.can_create_projects(
                subscription_tier, len(active_projects)
            )
            if not can_create:
                logger.warning(f"User {current_user} exceeded project limit: {error_msg}")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)

            logger.info(f"Subscription validation passed for {current_user} (tier: {subscription_tier})")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating subscription: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating subscription: {str(e)[:100]}",
            )

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
                    return APIResponse(
                        success=True,
                        status="created",
                        message="Project created successfully",
                        data=_project_to_response(project).dict() if hasattr(_project_to_response(project), 'dict') else _project_to_response(project),
                    )
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
            if user_object.subscription_status != "active":
                logger.warning(
                    f"User {current_user} attempted to create project without active subscription"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active subscription required to create projects",
                )

            # Check project limit for subscription tier
            active_projects = db.get_user_projects(current_user)
            can_create, error_msg = SubscriptionChecker.can_create_projects(
                user_object.subscription_tier, len(active_projects)
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
        return APIResponse(
            success=True,
            status="created",
            message="Project created successfully",
            data=_project_to_response(project).dict() if hasattr(_project_to_response(project), 'dict') else _project_to_response(project),
        )

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
    response_model=APIResponse,
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

        return APIResponse(
            success=True,
            status="success",
            message="Project retrieved successfully",
            data=_project_to_response(project).dict() if hasattr(_project_to_response(project), 'dict') else _project_to_response(project),
        )

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
    response_model=APIResponse,
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

        return APIResponse(
            success=True,
            status="updated",
            message="Project updated successfully",
            data=_project_to_response(project).dict() if hasattr(_project_to_response(project), 'dict') else _project_to_response(project),
        )

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
    response_model=APIResponse,
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

        return APIResponse(
            success=True,
            status="success",
            message=f"Project '{project_name}' has been permanently deleted",
            data={"project_id": project_id, "name": project_name},
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
    response_model=APIResponse,
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

        return APIResponse(
            success=True,
            status="success",
            message="Project restored successfully",
            data=_project_to_response(project).dict() if hasattr(_project_to_response(project), 'dict') else _project_to_response(project),
        )

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
    response_model=APIResponse,
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
    response_model=APIResponse,
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
            "categories": getattr(project, "categories", {}),
        }

        return APIResponse(
            success=True,
            status="success",
            data=maturity,
            message="Maturity assessment retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting maturity for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving maturity assessment",
        )


@router.get(
    "/{project_id}/maturity/analysis",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed maturity analysis",
    responses={
        200: {"description": "Detailed analysis retrieved successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_maturity_analysis(
    project_id: str,
    phase: str = Query(None, description="Specific phase to analyze (optional)"),
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get detailed maturity analysis for a project or specific phase.

    Includes:
    - Category breakdown with scores, targets, and percentages
    - Category analysis (strong, adequate, weak, missing)
    - Summary statistics
    - Action plans to reach milestones (60%, 80%, 100%)
    - Recommended questions for next session
    - Prioritized focus areas

    Args:
        project_id: Project identifier
        phase: Optional specific phase to analyze
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Detailed analysis with all metrics and recommendations
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

        # Get maturity data
        phase_scores = getattr(project, "phase_maturity_scores", {})
        category_scores = getattr(project, "category_scores", {})
        analytics = getattr(project, "analytics_metrics", {})

        # If specific phase requested, analyze only that phase
        phases_to_analyze = [phase] if phase else list(phase_scores.keys())

        analysis_data = {
            "project_id": project_id,
            "project_type": getattr(project, "project_type", "software"),
            "current_phase": getattr(project, "current_phase", "discovery"),
            "overall_maturity": getattr(project, "overall_maturity", 0.0),
            "phases": {}
        }

        # Analyze each phase
        for phase_name in phases_to_analyze:
            phase_score = phase_scores.get(phase_name, 0.0)
            phase_categories = category_scores.get(phase_name, {})

            if not phase_categories and phase_score == 0:
                continue  # Skip phases with no data

            # Categorize categories by strength
            strong_categories = []
            adequate_categories = []
            weak_categories = []
            missing_categories = []

            for cat_name, cat_data in phase_categories.items():
                percentage = cat_data.get("percentage", 0.0) if isinstance(cat_data, dict) else getattr(cat_data, "percentage", 0.0)
                current_score = cat_data.get("current_score", 0.0) if isinstance(cat_data, dict) else getattr(cat_data, "current_score", 0.0)
                target_score = cat_data.get("target_score", 15.0) if isinstance(cat_data, dict) else getattr(cat_data, "target_score", 15.0)
                spec_count = cat_data.get("spec_count", 0) if isinstance(cat_data, dict) else getattr(cat_data, "spec_count", 0)
                confidence = cat_data.get("confidence", 0.0) if isinstance(cat_data, dict) else getattr(cat_data, "confidence", 0.0)

                category_info = {
                    "name": cat_name,
                    "current_score": current_score,
                    "target_score": target_score,
                    "percentage": percentage,
                    "spec_count": spec_count,
                    "confidence": confidence,
                    "remaining_score": max(0.0, target_score - current_score),
                    "specs_needed_estimate": max(0, int((target_score - current_score) / 0.85))
                }

                if percentage >= 80:
                    strong_categories.append(category_info)
                elif percentage >= 30:
                    adequate_categories.append(category_info)
                elif percentage > 0:
                    weak_categories.append(category_info)
                else:
                    missing_categories.append(category_info)

            # Calculate statistics
            total_categories = len(phase_categories)
            completed_categories = sum(1 for cat in phase_categories.values()
                                     if (isinstance(cat, dict) and cat.get("percentage", 0) >= 100) or
                                        (hasattr(cat, "percentage") and cat.percentage >= 100))

            # Estimate metrics for reaching milestones
            current_score_sum = sum((cat.get("current_score", 0) if isinstance(cat, dict) else getattr(cat, "current_score", 0))
                                   for cat in phase_categories.values())

            milestone_60 = max(0, 54.0 - current_score_sum)  # 60% of 90
            milestone_80 = max(0, 72.0 - current_score_sum)  # 80% of 90
            milestone_100 = max(0, 90.0 - current_score_sum) # 100% of 90

            # Estimate sessions needed (assuming 6.5 points per session)
            avg_points_per_session = analytics.get("velocity", 6.5)
            sessions_to_60 = max(0, int(milestone_60 / avg_points_per_session)) + 1
            sessions_to_80 = max(0, int(milestone_80 / avg_points_per_session)) + 1
            sessions_to_100 = max(0, int(milestone_100 / avg_points_per_session)) + 1

            analysis_data["phases"][phase_name] = {
                "overall_percentage": phase_score,
                "status": "complete" if phase_score >= 100 else "ready" if phase_score >= 60 else "warning" if phase_score >= 40 else "critical",
                "ready_to_advance": phase_score >= 60,
                "categories": {
                    "strong": strong_categories,
                    "adequate": adequate_categories,
                    "weak": weak_categories,
                    "missing": missing_categories
                },
                "statistics": {
                    "total_categories": total_categories,
                    "completed_categories": completed_categories,
                    "strong_count": len(strong_categories),
                    "adequate_count": len(adequate_categories),
                    "weak_count": len(weak_categories),
                    "missing_count": len(missing_categories),
                    "total_points_earned": current_score_sum,
                    "total_points_possible": 90.0,
                    "average_category_confidence": analytics.get("avg_confidence", 0.85)
                },
                "milestones": {
                    "reach_60_percent": {
                        "target_score": 54.0,
                        "points_needed": milestone_60,
                        "estimated_specs": max(0, int(milestone_60 / 0.85)),
                        "estimated_sessions": sessions_to_60
                    },
                    "reach_80_percent": {
                        "target_score": 72.0,
                        "points_needed": milestone_80,
                        "estimated_specs": max(0, int(milestone_80 / 0.85)),
                        "estimated_sessions": sessions_to_80
                    },
                    "reach_100_percent": {
                        "target_score": 90.0,
                        "points_needed": milestone_100,
                        "estimated_specs": max(0, int(milestone_100 / 0.85)),
                        "estimated_sessions": sessions_to_100
                    }
                },
                "recommendations": _generate_recommendations(
                    weak_categories,
                    missing_categories,
                    phase_score
                )
            }

        return APIResponse(
            success=True,
            status="success",
            message="Detailed maturity analysis retrieved successfully",
            data=analysis_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting maturity analysis for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving maturity analysis",
        )


def _generate_recommendations(weak_categories, missing_categories, phase_score):
    """Generate prioritized action recommendations based on phase status."""
    recommendations = []

    # Priority 1: Critical gaps
    if phase_score < 40:
        recommendations.append({
            "priority": "critical",
            "title": "Phase Maturity Very Low",
            "description": "Your phase maturity is below 40%. Consider answering more questions to strengthen your specification.",
            "focus_areas": [cat["name"] for cat in missing_categories[:3]]
        })

    # Priority 2: Weak categories
    if weak_categories:
        weakest = sorted(weak_categories, key=lambda x: x["percentage"])[:2]
        recommendations.append({
            "priority": "high",
            "title": f"Strengthen Weak Areas",
            "description": f"Focus on {', '.join([cat['name'] for cat in weakest])} categories to improve overall maturity.",
            "focus_areas": [cat["name"] for cat in weakest]
        })

    # Priority 3: Missing categories
    if missing_categories:
        recommendations.append({
            "priority": "high",
            "title": f"Complete Missing Categories",
            "description": f"Start coverage in: {', '.join([cat['name'] for cat in missing_categories[:3]])}",
            "focus_areas": [cat["name"] for cat in missing_categories[:3]]
        })

    # Priority 4: Ready decision
    if phase_score >= 60:
        if phase_score < 80:
            recommendations.append({
                "priority": "info",
                "title": "Ready to Advance (Consider Strengthening)",
                "description": "Your phase is ready (60%+), but strengthening weak areas before advancing will reduce rework later.",
                "focus_areas": [cat["name"] for cat in weak_categories[:2]] if weak_categories else []
            })
        elif phase_score >= 100:
            recommendations.append({
                "priority": "success",
                "title": "Phase Complete",
                "description": "Excellent work! This phase is fully specified and ready for the next phase.",
                "focus_areas": []
            })

    return recommendations


@router.put(
    "/{project_id}/phase",
    response_model=APIResponse,
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
    request: Optional[UpdateProjectRequest] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Advance project to the next phase.

    If a request body with phase is provided, set the project to that phase.
    Otherwise, auto-advance to the next phase in the sequence.

    Args:
        project_id: Project identifier
        request: Optional update request with phase field
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

        # Determine the new phase
        valid_phases = ["discovery", "analysis", "design", "implementation"]
        old_phase = project.phase or "discovery"

        if request and request.phase:
            # Use the provided phase
            new_phase = request.phase
            if new_phase not in valid_phases:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid phase. Must be one of: {', '.join(valid_phases)}",
                )
        else:
            # Auto-advance to the next phase
            try:
                current_index = valid_phases.index(old_phase)
                if current_index < len(valid_phases) - 1:
                    new_phase = valid_phases[current_index + 1]
                else:
                    new_phase = valid_phases[-1]  # Stay at the last phase
            except (ValueError, IndexError):
                new_phase = "discovery"  # Default to discovery if phase is invalid

        project.phase = new_phase
        project.updated_at = datetime.now(timezone.utc)

        # Save changes
        db.save_project(project)

        logger.info(f"Project {project_id} phase advanced from {old_phase} to {new_phase}")

        return APIResponse(
            success=True,
            status="updated",
            message=f"Project phase advanced to {new_phase}",
            data=_project_to_response(project).dict() if hasattr(_project_to_response(project), 'dict') else _project_to_response(project),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error advancing phase for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error advancing project phase",
        )

@router.post(
    "/{project_id}/phase/rollback",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Rollback project to previous phase",
    responses={
        200: {"description": "Project phase rolled back successfully"},
        400: {"description": "Invalid phase transition", "model": ErrorResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        403: {"description": "Access denied", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def rollback_phase(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Roll back project to the previous phase.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Updated ProjectResponse with previous phase
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

        # Determine the previous phase
        valid_phases = ["discovery", "analysis", "design", "implementation"]
        old_phase = project.phase or "discovery"

        try:
            current_index = valid_phases.index(old_phase)
            if current_index > 0:
                new_phase = valid_phases[current_index - 1]
            else:
                # Already at the first phase
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot roll back from discovery phase (first phase)",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid current phase: {old_phase}",
            )

        project.phase = new_phase
        project.updated_at = datetime.now(timezone.utc)

        # Save changes
        db.save_project(project)

        logger.info(f"Project {project_id} phase rolled back from {old_phase} to {new_phase}")

        return APIResponse(
            success=True,
            status="updated",
            message=f"Project phase rolled back to {new_phase}",
            data=_project_to_response(project).dict() if hasattr(_project_to_response(project), 'dict') else _project_to_response(project),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rolling back phase for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error rolling back project phase",
        )



@router.get(
    "/{project_id}/analytics",
    response_model=APIResponse,
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

        return APIResponse(
            success=True,
            status="success",
            message="Analytics retrieved",
            data=ProjectAnalyticsData(
                project_id=project_id,
                period="all_time",
                metrics=analytics,
            ).dict(),
        )

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
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project files",
    responses={
        200: {"description": "Files retrieved successfully", "model": APIResponse},
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

        # Read actual project files from filesystem
        from pathlib import Path
        from datetime import datetime

        files = []
        project_data_dir = Path(f"~/.socrates/projects/{project_id}").expanduser()

        if project_data_dir.exists():
            # Scan for files in project directory and subdirectories
            file_id_counter = 1
            for file_path in sorted(project_data_dir.rglob("*")):
                if file_path.is_file():
                    # Skip certain system files
                    if file_path.name.startswith("."):
                        continue

                    # Determine file type from extension
                    suffix = file_path.suffix.lower()
                    type_map = {
                        ".py": "python",
                        ".js": "javascript",
                        ".ts": "typescript",
                        ".tsx": "typescript",
                        ".jsx": "javascript",
                        ".java": "java",
                        ".cs": "csharp",
                        ".cpp": "cpp",
                        ".go": "go",
                        ".rs": "rust",
                        ".sql": "sql",
                        ".txt": "text",
                        ".md": "markdown",
                        ".json": "json",
                        ".yaml": "yaml",
                        ".yml": "yaml",
                    }
                    file_type = type_map.get(suffix, "file")

                    # Get file stats
                    stat = file_path.stat()
                    rel_path = "/" + str(file_path.relative_to(project_data_dir))

                    files.append(
                        {
                            "id": f"file_{file_id_counter}",
                            "name": file_path.name,
                            "path": rel_path,
                            "type": file_type,
                            "size": stat.st_size,
                            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        }
                    )
                    file_id_counter += 1

        return APIResponse(
            success=True,
            status="success",
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


@router.get("/{project_id}/files/content")
def get_file_content(
    project_id: str,
    file_name: str = Query(..., description="Name of the file to retrieve"),
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
) -> APIResponse:
    """
    Get content of a specific file in a project.

    Args:
        project_id: Project identifier
        file_name: Name of the file to retrieve
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse with file content
    """
    try:
        from pathlib import Path

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

        # Construct the file path
        # Files can be in generated_files or refactored_files subdirectories
        project_data_dir = Path(f"~/.socrates/projects/{project_id}").expanduser()

        # Security: Prevent directory traversal attacks
        # Normalize the file_name and ensure it doesn't contain path separators
        if "/" in file_name or "\\" in file_name or file_name.startswith("."):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file name",
            )

        # Try to find the file in standard locations
        possible_paths = [
            project_data_dir / "generated_files" / file_name,
            project_data_dir / "refactored_files" / file_name,
            project_data_dir / file_name,  # Also check root project dir
        ]

        file_path = None
        for path in possible_paths:
            if path.exists() and path.is_file():
                file_path = path
                break

        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{file_name}' not found in project",
            )

        # Read the file content
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # If UTF-8 fails, try with default encoding
            try:
                content = file_path.read_text()
            except Exception as read_error:
                logger.error(f"Error reading file {file_name}: {str(read_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to read file content",
                )

        return APIResponse(
            success=True,
            status="success",
            message=f"File content retrieved for {file_name}",
            data={
                "project_id": project_id,
                "file_name": file_name,
                "content": content,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file content for {project_id}/{file_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving file content",
        )


@router.delete("/{project_id}/files")
async def delete_project_file(
    project_id: str,
    file_name: str = Query(..., description="Name of the file to delete"),
    current_user: str = Depends(get_current_user),
):
    """
    Delete a file from a project

    Args:
        project_id: ID of the project
        file_name: Name of the file to delete
        current_user: Current authenticated user

    Returns:
        Success response with deleted file details
    """
    try:
        # Get and verify project ownership
        project = await ProjectManager.get_project(project_id)
        if not project or project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete files from this project",
            )

        # Security: Prevent directory traversal
        if "/" in file_name or "\\" in file_name or file_name.startswith("."):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file name",
            )

        # Check for file in different directories
        file_path = None
        possible_paths = [
            Path.home() / ".socrates" / "projects" / project_id / "generated_files" / file_name,
            Path.home() / ".socrates" / "projects" / project_id / "refactored_files" / file_name,
            Path.home() / ".socrates" / "projects" / project_id / file_name,
        ]

        for path in possible_paths:
            if path.exists() and path.is_file():
                file_path = path
                break

        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{file_name}' not found",
            )

        # Delete the file
        file_path.unlink()
        logger.info(f"Deleted file {project_id}/{file_name}")

        return APIResponse(
            success=True,
            status="success",
            message=f"File '{file_name}' deleted successfully",
            data={
                "project_id": project_id,
                "file_name": file_name,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {project_id}/{file_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting file",
        )
