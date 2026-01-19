"""
Project Access Control Helpers.

Provides utilities for checking and enforcing role-based access control
for project endpoints. Handles authorization for Owner, Editor, and Viewer roles.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from socrates_api.database import get_database
from socratic_system.database import ProjectDatabase
from socrates_api.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

# Role hierarchy levels
ROLE_HIERARCHY = {
    "owner": 3,
    "editor": 2,
    "viewer": 1,
}


async def get_user_project_role(
    project_id: str,
    current_user: str,
    db: ProjectDatabase,
) -> Optional[str]:
    """
    Get the role of a user in a specific project.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user (username)
        db: Database connection

    Returns:
        User's role (owner, editor, viewer) or None if not a member

    Raises:
        HTTPException: 404 if project not found
    """
    project = db.load_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Owner is always an owner
    if project.owner == current_user:
        return "owner"

    # Check team members
    if project.team_members:
        for member in project.team_members:
            if member.username == current_user:
                return member.role

    return None


async def check_project_access(
    project_id: str,
    current_user: str,
    db: ProjectDatabase,
    min_role: str = "viewer",
) -> str:
    """
    Check if user has access to a project with minimum required role.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user (username)
        db: Database connection
        min_role: Minimum required role (viewer, editor, or owner)

    Returns:
        User's role in the project

    Raises:
        HTTPException: 403 if user lacks required role
        HTTPException: 404 if project not found
    """
    user_role = await get_user_project_role(project_id, current_user, db)

    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project",
        )

    # Check role hierarchy
    required_level = ROLE_HIERARCHY.get(min_role, 0)
    user_level = ROLE_HIERARCHY.get(user_role, 0)

    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Requires {min_role} role.",
        )

    return user_role


# Convenient dependency factories for common use cases

def require_editor_or_owner():
    """
    Dependency that ensures user has editor or owner role.

    Usage:
        @router.post("/{project_id}/chat/message")
        async def send_message(
            project_id: str,
            current_user: str = Depends(get_current_user),
            role: str = Depends(require_editor_or_owner()),
            db: ProjectDatabase = Depends(get_database),
        ):
            ...
    """
    async def verify_role(
        project_id: str,
        current_user: str = Depends(get_current_user),
        db: ProjectDatabase = Depends(get_database),
    ) -> str:
        return await check_project_access(
            project_id, current_user, db, min_role="editor"
        )

    return Depends(verify_role)


def require_owner():
    """
    Dependency that ensures user is the project owner.

    Usage:
        @router.delete("/{project_id}")
        async def delete_project(
            project_id: str,
            current_user: str = Depends(get_current_user),
            role: str = Depends(require_owner()),
            db: ProjectDatabase = Depends(get_database),
        ):
            ...
    """
    async def verify_owner(
        project_id: str,
        current_user: str = Depends(get_current_user),
        db: ProjectDatabase = Depends(get_database),
    ) -> str:
        return await check_project_access(
            project_id, current_user, db, min_role="owner"
        )

    return Depends(verify_owner)


def require_viewer_or_better():
    """
    Dependency that ensures user has at least viewer role (any access level).

    Usage:
        @router.get("/{project_id}/stats")
        async def get_stats(
            project_id: str,
            current_user: str = Depends(get_current_user),
            role: str = Depends(require_viewer_or_better()),
            db: ProjectDatabase = Depends(get_database),
        ):
            ...
    """
    async def verify_viewer(
        project_id: str,
        current_user: str = Depends(get_current_user),
        db: ProjectDatabase = Depends(get_database),
    ) -> str:
        return await check_project_access(
            project_id, current_user, db, min_role="viewer"
        )

    return Depends(verify_viewer)
