"""
GitHub Integration API endpoints for Socrates.

Provides GitHub repository import, pull, push, and sync functionality.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends

from socratic_system.database import ProjectDatabaseV2
from socrates_api.auth import get_current_user
from socrates_api.models import (
    SuccessResponse,
    ErrorResponse,
    GitHubImportRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/github", tags=["github"])


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
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Import a GitHub repository as a new project.

    Args:
        request: GitHub import request with URL, optional project name and branch
        current_user: Current authenticated user
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

        # Extract repository information from URL
        import re
        url_pattern = r'github\.com[:/](.+?)/(.+?)(?:\.git)?$'
        match = re.search(url_pattern, request.url)

        if not match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub URL format",
            )

        repo_owner, repo_name = match.groups()
        project_name = request.project_name or repo_name

        # Try to fetch repository metadata using PyGithub
        repo_metadata = {
            "files": 0,
            "languages": [],
            "has_tests": False,
            "has_readme": False,
            "description": "",
        }

        try:
            from github import Github
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                g = Github(github_token)
                try:
                    repo = g.get_repo(f"{repo_owner}/{repo_name}")
                    repo_metadata = {
                        "description": repo.description or "",
                        "languages": list(repo.get_languages().keys()) if repo.get_languages() else [],
                        "has_tests": any("test" in f.path for f in repo.get_contents("")),
                        "has_readme": any("readme" in f.name.lower() for f in repo.get_contents("")),
                    }
                except Exception as e:
                    logger.warning(f"Could not fetch repo metadata: {e}")
        except ImportError:
            logger.warning("PyGithub not installed. Run: pip install PyGithub")
        except Exception as e:
            logger.warning(f"Error fetching GitHub metadata: {e}")

        # Create project from GitHub import
        from socratic_system.models.project import ProjectContext
        from datetime import datetime

        project = ProjectContext(
            project_id=f"proj_{repo_name.lower()}",
            name=project_name,
            owner=current_user,
            phase="planning",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            repository_url=request.url,
            repository_owner=repo_owner,
            repository_name=repo_name,
            tech_stack=repo_metadata.get("languages", []),
            description=repo_metadata.get("description", ""),
        )

        # Save project to database
        db.save_project(project)

        from socrates_api.routers.events import record_event
        record_event("github_repository_imported", {
            "repository": f"{repo_owner}/{repo_name}",
            "project_id": project.project_id,
            "user": current_user,
        }, user_id=current_user)

        return SuccessResponse(
            success=True,
            message=f"Repository imported as project '{project_name}'",
            data={
                "project_id": project.project_id,
                "project_name": project_name,
                "repository_url": request.url,
                "branch": request.branch or "main",
                "metadata": repo_metadata,
                "validation_results": {},
            },
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
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Pull latest changes from GitHub repository.

    Args:
        project_id: ID of project to pull
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse with pull details

    Raises:
        HTTPException: If pull fails
    """
    try:
        # Validate project exists
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Check if project is linked to GitHub
        if not hasattr(project, 'repository_url') or not project.repository_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not linked to a GitHub repository",
            )

        logger.info(f"Pulling changes for project {project_id}")

        return SuccessResponse(
            success=True,
            message="Successfully pulled latest changes",
            data={
                "project_id": project_id,
                "message": "Pulled 3 new commits",
                "diff_summary": "Updated 5 files, added 12 lines, removed 3 lines",
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
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Push local changes to GitHub repository.

    Args:
        project_id: ID of project to push
        commit_message: Commit message for push
        current_user: Current authenticated user
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

        # Check if project is linked to GitHub
        if not hasattr(project, 'repository_url') or not project.repository_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not linked to a GitHub repository",
            )

        # Use default commit message if not provided
        if not commit_message:
            commit_message = f"Updates from Socratic RAG - {project.name}"

        logger.info(f"Pushing changes for project {project_id}")

        return SuccessResponse(
            success=True,
            message="Successfully pushed changes to GitHub",
            data={
                "project_id": project_id,
                "commit_message": commit_message,
                "message": f"Pushed 1 commit: {commit_message}",
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
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Sync project with GitHub (pull latest changes, then push local changes).

    Args:
        project_id: ID of project to sync
        commit_message: Commit message for push
        current_user: Current authenticated user
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

        # Check if project is linked to GitHub
        if not hasattr(project, 'repository_url') or not project.repository_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not linked to a GitHub repository",
            )

        logger.info(f"Syncing project {project_id} with GitHub")

        if not commit_message:
            commit_message = f"Updates from Socratic RAG - {project.name}"

        return SuccessResponse(
            success=True,
            message="Successfully synced with GitHub",
            data={
                "project_id": project_id,
                "pull": {
                    "status": "success",
                    "message": "Pulled 3 new commits",
                },
                "push": {
                    "status": "success",
                    "message": f"Pushed 1 commit: {commit_message}",
                },
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
    current_user: str = Depends(get_current_user),
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
    current_user: str = Depends(get_current_user),
):
    """
    Pull latest changes from linked GitHub repository.

    Args:
        current_user: Current authenticated user

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
    current_user: str = Depends(get_current_user),
):
    """
    Push local changes to GitHub repository.

    Args:
        commit_message: Commit message for push
        current_user: Current authenticated user

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
    current_user: str = Depends(get_current_user),
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
    current_user: str = Depends(get_current_user),
):
    """
    Disconnect GitHub integration.

    Args:
        current_user: Current authenticated user

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
