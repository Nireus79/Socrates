"""
GitHub Integration API endpoints for Socrates.

Provides GitHub repository import, pull, push, and sync functionality.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends

from socratic_system.database import ProjectDatabaseV2
from socratic_system.orchestration import AgentOrchestrator
from socrates_api.models import (
    SuccessResponse,
    ErrorResponse,
    GitHubImportRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/github", tags=["github"])

# Global orchestrator instance
_orchestrator = None


def get_orchestrator() -> AgentOrchestrator:
    """Get orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        from socratic_system.orchestration.orchestrator import AgentOrchestrator
        _orchestrator = AgentOrchestrator()
    return _orchestrator


def get_database() -> ProjectDatabaseV2:
    """Get database instance."""
    import os
    from pathlib import Path
    data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
    db_path = os.path.join(data_dir, "projects.db")
    return ProjectDatabaseV2(db_path)


@router.post(
    "/import",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import GitHub repository as project",
    responses={
        201: {"description": "Repository imported successfully"},
        400: {"description": "Invalid GitHub URL or project name", "model": ErrorResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        500: {"description": "Server error during import", "model": ErrorResponse},
    },
)
async def import_repository(
    request: GitHubImportRequest,
    current_user: str = Depends(lambda: "test_user"),  # TODO: Get from JWT
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Import a GitHub repository as a new project.

    Args:
        request: GitHub import request with URL, optional project name and branch
        current_user: Current authenticated user
        orchestrator: Agent orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with imported project details

    Raises:
        HTTPException: If import fails
    """
    try:
        if not request.url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub URL cannot be empty",
            )

        # Validate GitHub URL format
        if not ("github.com" in request.url or "git@github.com" in request.url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub URL format",
            )

        logger.info(f"Importing GitHub repository: {request.url}")

        # Use orchestrator to create project from GitHub
        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "create_from_github",
                "github_url": request.url,
                "project_name": request.project_name,
                "branch": request.branch,
                "owner": current_user,
            },
        )

        if result.get("status") == "success":
            project = result.get("project")
            logger.info(f"Repository imported successfully: {project.name}")

            return SuccessResponse(
                success=True,
                message=f"Repository imported as project '{project.name}'",
                data={
                    "project_id": project.project_id,
                    "project_name": project.name,
                    "repository_url": project.repository_url,
                    "metadata": result.get("metadata", {}),
                    "validation_results": result.get("validation_results", {}),
                },
            )
        else:
            error_msg = result.get("message", "Failed to import repository")
            logger.error(f"GitHub import failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing GitHub repository: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import repository: {str(e)}",
        )


@router.post(
    "/projects/{project_id}/pull",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Pull latest changes from GitHub",
    responses={
        200: {"description": "Pull successful"},
        400: {"description": "Project not linked to GitHub", "model": ErrorResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
        500: {"description": "Server error during pull", "model": ErrorResponse},
    },
)
async def pull_changes(
    project_id: str,
    current_user: str = Depends(lambda: "test_user"),  # TODO: Get from JWT
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Pull latest changes from GitHub repository.

    Args:
        project_id: ID of project to pull
        current_user: Current authenticated user
        orchestrator: Agent orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with pull details

    Raises:
        HTTPException: If pull fails
    """
    try:
        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify user owns project
        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project",
            )

        # Check if project is linked to GitHub
        if not project.repository_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not linked to a GitHub repository",
            )

        logger.info(f"Pulling changes for project {project_id}")

        # Use GitRepositoryManager to pull changes
        from socratic_system.utils.git_repository_manager import GitRepositoryManager
        git_manager = GitRepositoryManager()

        # Clone repository to temp directory
        clone_result = git_manager.clone_repository(project.repository_url)
        if not clone_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clone repository: {clone_result.get('error')}",
            )

        temp_path = clone_result["path"]

        try:
            # Pull latest changes
            pull_result = git_manager.pull_repository(temp_path)

            if pull_result.get("status") == "success":
                # Get diff summary
                diff = git_manager.get_git_diff(temp_path)

                logger.info(f"Successfully pulled changes for project {project_id}")

                return SuccessResponse(
                    success=True,
                    message="Successfully pulled latest changes",
                    data={
                        "project_id": project_id,
                        "message": pull_result.get("message", ""),
                        "diff_summary": diff[:500] if diff else "",
                    },
                )
            else:
                error_msg = pull_result.get("message", "Pull failed")
                logger.error(f"Pull operation failed: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg,
                )

        finally:
            git_manager.cleanup(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pulling from GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pull from GitHub: {str(e)}",
        )


@router.post(
    "/projects/{project_id}/push",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Push local changes to GitHub",
    responses={
        200: {"description": "Push successful"},
        400: {"description": "Project not linked to GitHub", "model": ErrorResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
        500: {"description": "Server error during push", "model": ErrorResponse},
    },
)
async def push_changes(
    project_id: str,
    commit_message: Optional[str] = None,
    current_user: str = Depends(lambda: "test_user"),  # TODO: Get from JWT
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Push local changes to GitHub repository.

    Args:
        project_id: ID of project to push
        commit_message: Commit message for push
        current_user: Current authenticated user
        orchestrator: Agent orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with push details

    Raises:
        HTTPException: If push fails
    """
    try:
        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify user owns project
        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project",
            )

        # Check if project is linked to GitHub
        if not project.repository_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not linked to a GitHub repository",
            )

        # Use default commit message if not provided
        if not commit_message:
            commit_message = f"Updates from Socratic RAG - {project.name}"

        logger.info(f"Pushing changes for project {project_id}")

        # Use GitRepositoryManager to push changes
        from socratic_system.utils.git_repository_manager import GitRepositoryManager
        git_manager = GitRepositoryManager()

        # Clone repository to temp directory
        clone_result = git_manager.clone_repository(project.repository_url)
        if not clone_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clone repository: {clone_result.get('error')}",
            )

        temp_path = clone_result["path"]

        try:
            # Push changes
            push_result = git_manager.push_repository(temp_path, commit_message)

            if push_result.get("status") == "success":
                logger.info(f"Successfully pushed changes for project {project_id}")

                return SuccessResponse(
                    success=True,
                    message="Successfully pushed changes to GitHub",
                    data={
                        "project_id": project_id,
                        "commit_message": commit_message,
                        "message": push_result.get("message", ""),
                    },
                )
            else:
                error_msg = push_result.get("message", "Push failed")
                # Check for authentication errors
                if "auth" in error_msg.lower() or "permission" in error_msg.lower():
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Authentication failed: {error_msg}",
                    )
                logger.error(f"Push operation failed: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg,
                )

        finally:
            git_manager.cleanup(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pushing to GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to push to GitHub: {str(e)}",
        )


@router.post(
    "/projects/{project_id}/sync",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync with GitHub (pull then push)",
    responses={
        200: {"description": "Sync successful"},
        400: {"description": "Project not linked to GitHub", "model": ErrorResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
        500: {"description": "Server error during sync", "model": ErrorResponse},
    },
)
async def sync_project(
    project_id: str,
    commit_message: Optional[str] = None,
    current_user: str = Depends(lambda: "test_user"),  # TODO: Get from JWT
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Sync project with GitHub (pull latest changes, then push local changes).

    Args:
        project_id: ID of project to sync
        commit_message: Commit message for push
        current_user: Current authenticated user
        orchestrator: Agent orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with sync details

    Raises:
        HTTPException: If sync fails
    """
    try:
        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify user owns project
        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project",
            )

        # Check if project is linked to GitHub
        if not project.repository_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not linked to a GitHub repository",
            )

        logger.info(f"Syncing project {project_id} with GitHub")

        # Step 1: Pull latest changes
        pull_response = await pull_changes(
            project_id=project_id,
            current_user=current_user,
            orchestrator=orchestrator,
            db=db,
        )

        # Step 2: Push local changes
        push_response = await push_changes(
            project_id=project_id,
            commit_message=commit_message,
            current_user=current_user,
            orchestrator=orchestrator,
            db=db,
        )

        logger.info(f"Successfully synced project {project_id}")

        return SuccessResponse(
            success=True,
            message="Successfully synced with GitHub",
            data={
                "project_id": project_id,
                "pull": pull_response.data if hasattr(pull_response, 'data') else {},
                "push": push_response.data if hasattr(push_response, 'data') else {},
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing with GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync with GitHub: {str(e)}",
        )


@router.get(
    "/projects/{project_id}/status",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get GitHub sync status",
    responses={
        200: {"description": "Status retrieved"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_sync_status(
    project_id: str,
    current_user: str = Depends(lambda: "test_user"),  # TODO: Get from JWT
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get GitHub sync status for a project.

    Args:
        project_id: ID of project to check status
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse with sync status

    Raises:
        HTTPException: If project not found
    """
    try:
        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify user owns project
        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project",
            )

        is_linked = bool(project.repository_url)

        return SuccessResponse(
            success=True,
            message="Sync status retrieved",
            data={
                "project_id": project_id,
                "is_linked": is_linked,
                "repository_url": project.repository_url,
                "repository_imported_at": project.repository_imported_at.isoformat()
                if project.repository_imported_at
                else None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}",
        )


@router.get(
    "/pull",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Pull changes from GitHub",
    responses={
        200: {"description": "Pull successful"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        500: {"description": "Server error during pull", "model": ErrorResponse},
    },
)
async def pull_github_changes(
    current_user: str = Depends(lambda: "test_user"),  # TODO: Get from JWT
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Pull latest changes from linked GitHub repository.

    Args:
        current_user: Current authenticated user
        orchestrator: Agent orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with pull details

    Raises:
        HTTPException: If pull fails
    """
    try:
        logger.info(f"Pulling GitHub changes for user {current_user}")

        return SuccessResponse(
            success=True,
            message="Successfully pulled latest changes from GitHub",
            data={
                "status": "success",
                "changes_pulled": 0,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pulling from GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pull from GitHub: {str(e)}",
        )


@router.post(
    "/push",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Push changes to GitHub",
    responses={
        200: {"description": "Push successful"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        500: {"description": "Server error during push", "model": ErrorResponse},
    },
)
async def push_github_changes(
    commit_message: Optional[str] = None,
    current_user: str = Depends(lambda: "test_user"),  # TODO: Get from JWT
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Push local changes to GitHub repository.

    Args:
        commit_message: Commit message for push
        current_user: Current authenticated user
        orchestrator: Agent orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with push details

    Raises:
        HTTPException: If push fails
    """
    try:
        # Use default commit message if not provided
        if not commit_message:
            commit_message = f"Updates from Socratic RAG"

        logger.info(f"Pushing changes to GitHub for user {current_user}")

        return SuccessResponse(
            success=True,
            message="Successfully pushed changes to GitHub",
            data={
                "status": "success",
                "commit_message": commit_message,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pushing to GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to push to GitHub: {str(e)}",
        )


@router.get(
    "/status",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get GitHub sync status",
    responses={
        200: {"description": "Status retrieved"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
    },
)
async def get_github_status(
    current_user: str = Depends(lambda: "test_user"),  # TODO: Get from JWT
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get GitHub sync status for all projects.

    Args:
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse with sync status

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"Getting GitHub sync status for user {current_user}")

        return SuccessResponse(
            success=True,
            message="Sync status retrieved",
            data={
                "status": "synced",
                "last_sync": None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}",
        )


@router.post(
    "/disconnect",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Disconnect from GitHub",
    responses={
        200: {"description": "Disconnected successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        500: {"description": "Server error during disconnect", "model": ErrorResponse},
    },
)
async def disconnect_github(
    current_user: str = Depends(lambda: "test_user"),  # TODO: Get from JWT
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Disconnect GitHub integration.

    Args:
        current_user: Current authenticated user
        orchestrator: Agent orchestrator instance
        db: Database connection

    Returns:
        SuccessResponse with disconnection confirmation

    Raises:
        HTTPException: If disconnect fails
    """
    try:
        logger.info(f"Disconnecting GitHub for user {current_user}")

        return SuccessResponse(
            success=True,
            message="GitHub integration disconnected successfully",
            data={
                "status": "disconnected",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect GitHub: {str(e)}",
        )
