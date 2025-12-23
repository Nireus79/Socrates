"""
Collaboration Router - Team collaboration and project sharing endpoints.

Provides:
- Team member management (add, remove, list)
- Role-based access control
- Real-time presence tracking
- Collaboration notifications
"""

import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends

from socratic_system.database import ProjectDatabaseV2

from socrates_api.auth import get_current_user
from socrates_api.models import (
    SuccessResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["collaboration"])

_database = None


def get_database() -> ProjectDatabaseV2:
    """Get database instance."""
    global _database
    if _database is None:
        data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
        db_path = os.path.join(data_dir, "projects.db")
        _database = ProjectDatabaseV2(db_path)
    return _database


# ============================================================================
# Collaborator Models
# ============================================================================


class CollaboratorRole:
    """Collaboration roles."""
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"

    @staticmethod
    def is_valid(role: str) -> bool:
        """Check if role is valid."""
        return role in [CollaboratorRole.OWNER, CollaboratorRole.EDITOR, CollaboratorRole.VIEWER]


# ============================================================================
# Collaborator Endpoints
# ============================================================================


@router.post(
    "/{project_id}/collaborators",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Add collaborator to project",
)
async def add_collaborator(
    project_id: str,
    username: str,
    role: str = CollaboratorRole.EDITOR,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Add a collaborator to a project.

    Only the project owner can add collaborators (requires pro tier).

    Args:
        project_id: Project identifier
        username: Username to add as collaborator
        role: Collaboration role (owner, editor, viewer)
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Success response with collaborator details

    Raises:
        HTTPException: If not owner, invalid role, or user not found
    """
    try:
        # Validate role
        if not CollaboratorRole.is_valid(role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: owner, editor, viewer",
            )

        # Verify project exists and user is owner
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can add collaborators",
            )

        # TODO: Check subscription tier (requires pro)
        # TODO: Add collaborator to database
        # TODO: Send invitation notification

        logger.info(f"Collaborator {username} added to project {project_id} by {current_user}")

        return {
            "status": "success",
            "collaborator": {
                "username": username,
                "role": role,
                "added_at": "2024-01-01T00:00:00Z",
                "status": "pending",  # pending until they accept
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding collaborator: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding collaborator",
        )


@router.get(
    "/{project_id}/collaborators",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List project collaborators",
)
async def list_collaborators(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    List all collaborators for a project.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        List of collaborators with their roles and status
    """
    try:
        # Verify project access
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # TODO: Load collaborators from database

        return {
            "status": "success",
            "project_id": project_id,
            "collaborators": [
                {
                    "username": project.owner,
                    "role": "owner",
                    "status": "active",
                    "joined_at": project.created_at,
                }
            ],
            "total": 1,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing collaborators: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing collaborators",
        )


@router.put(
    "/{project_id}/collaborators/{username}/role",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Update collaborator role",
)
async def update_collaborator_role(
    project_id: str,
    username: str,
    role: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Update a collaborator's role.

    Only the project owner can update roles.

    Args:
        project_id: Project identifier
        username: Collaborator username
        role: New role
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Updated collaborator details
    """
    try:
        # Validate role
        if not CollaboratorRole.is_valid(role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )

        # Verify project and ownership
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can update roles",
            )

        # TODO: Update role in database

        logger.info(f"Collaborator {username} role updated to {role} in project {project_id}")

        return {
            "status": "success",
            "collaborator": {
                "username": username,
                "role": role,
                "updated_at": "2024-01-01T00:00:00Z",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating role",
        )


@router.delete(
    "/{project_id}/collaborators/{username}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Remove collaborator",
)
async def remove_collaborator(
    project_id: str,
    username: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Remove a collaborator from a project.

    Only the project owner can remove collaborators.

    Args:
        project_id: Project identifier
        username: Collaborator to remove
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Success response
    """
    try:
        # Verify project and ownership
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can remove collaborators",
            )

        # Prevent removing owner
        if username == project.owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove project owner",
            )

        # TODO: Remove collaborator from database

        logger.info(f"Collaborator {username} removed from project {project_id}")

        return {
            "status": "success",
            "message": f"Collaborator {username} removed",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing collaborator: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error removing collaborator",
        )


# ============================================================================
# Presence & Activity Endpoints
# ============================================================================


@router.get(
    "/{project_id}/presence",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get active collaborators",
)
async def get_presence(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get list of currently active collaborators.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        List of active collaborators with presence info
    """
    try:
        # Verify project access
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # TODO: Load active presence from WebSocket connection manager

        return {
            "status": "success",
            "project_id": project_id,
            "active_collaborators": [
                {
                    "username": current_user,
                    "status": "online",
                    "last_activity": "2024-01-01T00:00:00Z",
                    "current_activity": "editing",
                }
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting presence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting presence",
        )


@router.post(
    "/{project_id}/activity",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Record activity",
)
async def record_activity(
    project_id: str,
    activity_type: str,
    data: Optional[dict] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Record user activity in project.

    Activity types: typing, editing, viewing, commenting, etc.

    Args:
        project_id: Project identifier
        activity_type: Type of activity
        data: Additional activity data
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Activity recording confirmation
    """
    try:
        # Verify project access
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # TODO: Store activity and broadcast to collaborators

        logger.debug(f"Activity recorded: {activity_type} in project {project_id}")

        return {
            "status": "success",
            "activity_id": f"act_{int(__import__('time').time() * 1000)}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recording activity",
        )
