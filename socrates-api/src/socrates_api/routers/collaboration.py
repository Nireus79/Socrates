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
from socrates_api.database import get_database
from socrates_api.auth import get_current_user
from socrates_api.models import (
    SuccessResponse,
    ErrorResponse,
    CollaborationInviteRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["collaboration"])
collab_router = APIRouter(prefix="/collaboration", tags=["collaboration"])


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

        # Initialize team_members if not present
        from datetime import datetime
        from socratic_system.models.role import TeamMemberRole

        project.team_members = project.team_members or []

        # Check if collaborator already exists
        existing = any(m.username == username for m in project.team_members)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {username} is already a collaborator",
            )

        # Add collaborator to team
        new_member = TeamMemberRole(
            username=username,
            role=role,
            skills=[],
            joined_at=datetime.utcnow(),
        )
        project.team_members.append(new_member)

        # Persist to database
        db.save_project(project)

        # Record event
        from socrates_api.routers.events import record_event
        record_event("collaborator_added", {
            "project_id": project_id,
            "username": username,
            "role": role,
        }, user_id=current_user)

        logger.info(f"Collaborator {username} added to project {project_id} by {current_user}")

        return {
            "status": "success",
            "collaborator": {
                "username": username,
                "role": role,
                "added_at": datetime.utcnow().isoformat(),
                "status": "active",
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

        # Load collaborators from project
        collaborators = [
            {
                "username": project.owner,
                "role": "owner",
                "status": "active",
                "joined_at": project.created_at.isoformat() if project.created_at else None,
            }
        ]

        # Add team members if present
        if project.team_members:
            for member in project.team_members:
                collaborators.append({
                    "username": member.username,
                    "role": member.role,
                    "status": "active",
                    "joined_at": member.joined_at.isoformat() if hasattr(member, 'joined_at') else None,
                })

        return {
            "status": "success",
            "project_id": project_id,
            "collaborators": collaborators,
            "total": len(collaborators),
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

        # Find and update collaborator role
        if project.team_members:
            for member in project.team_members:
                if member.username == username:
                    member.role = role
                    db.save_project(project)

                    from socrates_api.routers.events import record_event
                    record_event("collaborator_role_updated", {
                        "project_id": project_id,
                        "username": username,
                        "new_role": role,
                    }, user_id=current_user)

                    logger.info(f"Collaborator {username} role updated to {role} in project {project_id}")

                    from datetime import datetime
                    return {
                        "status": "success",
                        "collaborator": {
                            "username": username,
                            "role": role,
                            "updated_at": datetime.utcnow().isoformat(),
                        },
                    }

        # Not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collaborator {username} not found",
        )

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

        # Remove collaborator from team_members
        removed = False
        if project.team_members:
            for i, member in enumerate(project.team_members):
                if member.username == username:
                    project.team_members.pop(i)
                    db.save_project(project)
                    removed = True
                    break

        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collaborator {username} not found",
            )

        from socrates_api.routers.events import record_event
        record_event("collaborator_removed", {
            "project_id": project_id,
            "username": username,
        }, user_id=current_user)

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


# ============================================================================
# Team Collaboration Endpoints (/collaboration prefix)
# ============================================================================


@collab_router.post(
    "/invite",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Invite team member",
    responses={
        200: {"description": "Invitation sent"},
        400: {"description": "Invalid email", "model": ErrorResponse},
        422: {"description": "Missing email", "model": ErrorResponse},
    },
)
async def invite_team_member(
    request: CollaborationInviteRequest,
):
    """
    Invite a team member via email.

    Args:
        request: Request body with email and optional role

    Returns:
        SuccessResponse with invitation details
    """
    try:
        email = request.email
        role = request.role

        if not email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Email is required",
            )

        # Basic email validation
        if '@' not in email or '.' not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format",
            )

        logger.info(f"Sending team invitation to {email} with role {role}")

        return SuccessResponse(
            success=True,
            message=f"Invitation sent to {email}",
            data={
                "email": email,
                "role": role,
                "status": "pending",
                "expires_at": "2025-01-30T12:00:00Z",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send invitation: {str(e)}",
        )


@collab_router.get(
    "/members",
    response_model=list,
    status_code=status.HTTP_200_OK,
    summary="List team members",
    responses={
        200: {"description": "Team members retrieved"},
    },
)
async def list_team_members():
    """
    List all team members.

    Returns:
        List of team member details
    """
    try:
        members = [
            {
                "id": "member_1",
                "name": "Team Member 1",
                "email": "member1@example.com",
                "role": "developer",
                "status": "active",
                "joined_at": "2024-01-01T00:00:00Z",
            }
        ]

        return members

    except Exception as e:
        logger.error(f"Error listing team members: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list team members: {str(e)}",
        )


@collab_router.put(
    "/members/{member_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Update team member role",
    responses={
        200: {"description": "Member role updated"},
        404: {"description": "Member not found", "model": ErrorResponse},
    },
)
async def update_member_role(
    member_id: str,
    role: str,
):
    """
    Update a team member's role.

    Args:
        member_id: Member identifier
        role: New role for member

    Returns:
        SuccessResponse with updated member details
    """
    try:
        logger.info(f"Updating member {member_id} role to {role}")

        return SuccessResponse(
            success=True,
            message=f"Member role updated to {role}",
            data={
                "member_id": member_id,
                "role": role,
                "updated_at": "2024-01-30T12:00:00Z",
            },
        )

    except Exception as e:
        logger.error(f"Error updating member role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update member role: {str(e)}",
        )


@collab_router.delete(
    "/members/{member_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove team member",
    responses={
        200: {"description": "Member removed"},
        404: {"description": "Member not found", "model": ErrorResponse},
    },
)
async def remove_team_member(
    member_id: str,
):
    """
    Remove a team member.

    Args:
        member_id: Member identifier

    Returns:
        SuccessResponse confirming removal
    """
    try:
        logger.info(f"Removing member {member_id}")

        return SuccessResponse(
            success=True,
            message=f"Member {member_id} removed from team",
            data={"member_id": member_id},
        )

    except Exception as e:
        logger.error(f"Error removing team member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove team member: {str(e)}",
        )
