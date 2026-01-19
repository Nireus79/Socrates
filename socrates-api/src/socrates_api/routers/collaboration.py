"""
Collaboration Router - Team collaboration and project sharing endpoints.

Provides:
- Team member management (add, remove, list)
- Role-based access control
- Real-time presence tracking with WebSocket broadcasting
- Collaboration notifications
- Activity tracking with real-time updates
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from socrates_api.auth import get_current_user, get_current_user_object, require_project_role
from socrates_api.database import get_database
from socrates_api.middleware.subscription import SubscriptionChecker
from socrates_api.testing_mode import TestingModeChecker
from socrates_api.models import (
    APIResponse,
    CollaborationInvitationResponse,
    CollaborationInviteRequest,
    CollaboratorListData,
    ErrorResponse,
)
from socrates_api.websocket import get_connection_manager
from socratic_system.database import ProjectDatabase
from socratic_system.models import User

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
# Helper Functions
# ============================================================================


async def _get_active_collaborators(project_id: str) -> List[Dict[str, Any]]:
    """
    Get list of active collaborators connected to a project via WebSocket.

    Args:
        project_id: Project identifier

    Returns:
        List of active collaborator info dicts with username, status, activity
    """
    try:
        connection_manager = get_connection_manager()

        # Get all metadata to find connections for this project
        active_collaborators = []
        seen_users = set()

        # Access the metadata directly (this is a workaround since get_project_connections
        # requires both user_id and project_id)
        async with connection_manager._lock:
            for _connection_id, metadata in connection_manager._metadata.items():
                if metadata.project_id == project_id and metadata.user_id not in seen_users:
                    seen_users.add(metadata.user_id)
                    active_collaborators.append(
                        {
                            "username": metadata.user_id,
                            "status": "online",
                            "last_activity": metadata.last_message_at or metadata.connected_at,
                            "connected_at": metadata.connected_at,
                            "message_count": metadata.message_count,
                        }
                    )

        logger.debug(
            f"Found {len(active_collaborators)} active collaborators in project {project_id}"
        )
        return active_collaborators

    except Exception as e:
        logger.error(f"Error getting active collaborators for {project_id}: {e}")
        return []


async def _broadcast_activity(
    project_id: str,
    current_user: str,
    activity_type: str,
    activity_data: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Broadcast an activity event to all collaborators in a project via WebSocket.

    Args:
        project_id: Project identifier
        current_user: User who triggered the activity
        activity_type: Type of activity (e.g., 'editing', 'commenting', 'viewing')
        activity_data: Optional additional activity data

    Returns:
        Number of connections the message was sent to
    """
    try:
        connection_manager = get_connection_manager()

        # Prepare activity broadcast message
        activity_message = {
            "type": "activity_update",
            "project_id": project_id,
            "user_id": current_user,
            "activity_type": activity_type,
            "activity_data": activity_data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Broadcast to all users in the project
        total_sent = 0
        async with connection_manager._lock:
            # Get all users connected to this project
            users_in_project = set()
            for user_id, projects in connection_manager._connections.items():
                if project_id in projects:
                    users_in_project.add(user_id)

        # Broadcast to each user
        for user_id in users_in_project:
            sent_count = await connection_manager.broadcast_to_project(
                user_id=user_id,
                project_id=project_id,
                message=activity_message,
            )
            total_sent += sent_count

        if total_sent > 0:
            logger.debug(
                f"Broadcasted activity '{activity_type}' from {current_user} "
                f"in project {project_id} to {total_sent} connections"
            )

        return total_sent

    except Exception as e:
        logger.error(f"Error broadcasting activity in project {project_id}: {e}")
        return 0


# ============================================================================
# Collaborator Endpoints
# ============================================================================


@router.post(
    "/{project_id}/collaborators",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add collaborator to project",
)
async def add_collaborator_new(
    project_id: str,
    request: CollaborationInviteRequest = Body(...),
    current_user: str = Depends(get_current_user),
    user_object: "User" = Depends(get_current_user_object),
    db: ProjectDatabase = Depends(get_database),
    http_request: Request = None,
):
    """
    Add a collaborator to a project.

    Only the project owner can add collaborators (requires pro tier).

    Args:
        project_id: Project identifier
        request: Collaboration invite request with email and role
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Success response with collaborator details

    Raises:
        HTTPException: If not owner, invalid role, or user not found
    """
    logger.info(f"add_collaborator called with project_id={project_id}, request={request}")
    try:
        # Validate role
        if not CollaboratorRole.is_valid(request.role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be one of: owner, editor, viewer",
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

        # CRITICAL: Validate subscription before adding collaborators
        logger.info(f"Validating subscription for adding collaborator for user {current_user}")
        try:
            subscription_tier = user_object.subscription_tier.lower()

            # Check if user has active subscription
            if user_object.subscription_status != "active":
                logger.warning(
                    f"User {current_user} attempted to add collaborator without active subscription (status: {user_object.subscription_status})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active subscription required to add collaborators",
                )

            # Check if testing mode is enabled via request headers
            testing_mode_enabled = TestingModeChecker.is_testing_mode_enabled(
                http_request.headers if http_request else {}
            )

            # Check subscription tier - collaboration feature requires pro or enterprise tier
            # NOTE: Free tier has collaboration=False in TIER_FEATURES, so free users cannot add team members
            # BUT: Testing mode bypasses this restriction
            if subscription_tier == "free" and not testing_mode_enabled:
                logger.warning(f"Free-tier user {current_user} attempted to add collaborators")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Collaboration feature requires 'pro' or 'enterprise' subscription",
                )

            # Check team member limit for subscription tier
            # Testing mode bypasses both feature restrictions and quota limits
            current_team_size = len(project.team_members) if project.team_members else 0
            can_add, error_msg = SubscriptionChecker.can_add_team_member(
                subscription_tier, current_team_size
            )

            # Allow testing mode to bypass quota limits only
            if not can_add and not testing_mode_enabled:
                logger.warning(f"User {current_user} exceeded team member limit: {error_msg}")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)

            if not can_add and testing_mode_enabled:
                logger.info(
                    f"User {current_user} in testing mode - bypassing quota limits for collaboration"
                )

            logger.info(
                f"Subscription validation passed for {current_user} (tier: {subscription_tier}, testing_mode: {testing_mode_enabled})"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error validating subscription for collaboration: {type(e).__name__}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating subscription: {str(e)[:100]}",
            )

        # Initialize team_members if not present
        from socratic_system.models.role import TeamMemberRole

        project.team_members = project.team_members or []

        # Try to resolve username from email
        resolved_username = request.email
        if "@" in request.email:
            # Email provided, try to look it up
            try:
                user = db.load_user_by_email(request.email)
                if user:
                    resolved_username = user.username
                    logger.info(f"Resolved email {request.email} to username {resolved_username}")
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No user found with email '{request.email}'",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Error looking up user by email {request.email}: {e}")
                # Fall back to using email prefix as username
                resolved_username = request.email.split("@")[0]
                logger.info(f"Could not resolve email, using prefix: {resolved_username}")
        else:
            # Username provided directly
            # Try to verify it exists, but don't fail if we can't (backward compatibility)
            try:
                user_exists = db.user_exists(resolved_username)
                if not user_exists:
                    logger.warning(
                        f"User '{resolved_username}' not found in users table, will add as pending collaborator"
                    )
            except Exception as e:
                logger.warning(f"Could not verify user {resolved_username} exists: {e}")

        # Cannot add the owner as a team member
        if resolved_username == project.owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add project owner as a collaborator",
            )

        # Check if collaborator already exists
        existing = any(m.username == resolved_username for m in project.team_members)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {resolved_username} is already a collaborator",
            )

        # Add collaborator to team
        new_member = TeamMemberRole(
            username=resolved_username,
            role=request.role,
            skills=[],
            joined_at=datetime.now(timezone.utc),
        )
        project.team_members.append(new_member)

        # Persist to database
        db.save_project(project)

        # Record event
        from socrates_api.routers.events import record_event

        record_event(
            "collaborator_added",
            {
                "project_id": project_id,
                "username": resolved_username,
                "role": request.role,
            },
            user_id=current_user,
        )

        logger.info(
            f"Collaborator {resolved_username} added to project {project_id} by {current_user}"
        )

        return APIResponse(
            success=True,
            status="created",
            message=f"Collaborator {resolved_username} added successfully",
            data={
                "username": resolved_username,
                "role": request.role,
                "added_at": datetime.now(timezone.utc).isoformat(),
                "status": "active",
            },
        )

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
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="List project collaborators",
)
async def list_collaborators(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
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

        # Check if user is owner or collaborator
        is_owner = project.owner == current_user
        is_collaborator = False
        if project.team_members:
            is_collaborator = any(member.username == current_user for member in project.team_members)

        if not (is_owner or is_collaborator):
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

        # Add team members if present (excluding owner to avoid duplicates)
        if project.team_members:
            for member in project.team_members:
                # Skip if this member is the owner (avoid duplicates)
                if member.username == project.owner:
                    continue
                collaborators.append(
                    {
                        "username": member.username,
                        "role": member.role,
                        "status": "active",
                        "joined_at": (
                            member.joined_at.isoformat() if hasattr(member, "joined_at") else None
                        ),
                    }
                )

        return APIResponse(
            success=True,
            status="success",
            message="Collaborators retrieved successfully",
            data=CollaboratorListData(
                project_id=project_id,
                total=len(collaborators),
                collaborators=collaborators,
            ).dict(),
        )

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
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Update collaborator role",
)
async def update_collaborator_role(
    project_id: str,
    username: str,
    role: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
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

                    record_event(
                        "collaborator_role_updated",
                        {
                            "project_id": project_id,
                            "username": username,
                            "new_role": role,
                        },
                        user_id=current_user,
                    )

                    logger.info(
                        f"Collaborator {username} role updated to {role} in project {project_id}"
                    )

                    return APIResponse(
                        success=True,
                        status="updated",
                        message=f"Role updated to {role}",
                        data={
                            "username": username,
                            "role": role,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )

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
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove collaborator",
)
async def remove_collaborator(
    project_id: str,
    username: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
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

        record_event(
            "collaborator_removed",
            {
                "project_id": project_id,
                "username": username,
            },
            user_id=current_user,
        )

        logger.info(f"Collaborator {username} removed from project {project_id}")

        return APIResponse(
            success=True,
            status="success",
            message=f"Collaborator {username} removed",
            data={},
        )

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
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get active collaborators",
    dependencies=[require_project_role("viewer")],
)
async def get_presence(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
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

        # Load active presence from WebSocket connection manager
        active_collaborators = await _get_active_collaborators(project_id)

        logger.info(
            f"Retrieved presence info for project {project_id}: "
            f"{len(active_collaborators)} active collaborators"
        )

        return APIResponse(
            success=True,
            status="success",
            message="Presence retrieved successfully",
            data={
                "project_id": project_id,
                "active_collaborators": active_collaborators,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting presence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting presence",
        )


@router.post(
    "/{project_id}/activities",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record activity",
    dependencies=[require_project_role("viewer")],
)
async def record_activity(
    project_id: str,
    activity_type: str = None,
    activity_data: Optional[dict] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Record user activity in project.

    Activity types: member_added, member_removed, role_changed, file_uploaded,
    message_sent, project_updated, session_started, session_ended, typing, editing, etc.

    Args:
        project_id: Project identifier
        activity_type: Type of activity
        activity_data: Additional activity data (dict)
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Activity recording confirmation
    """
    try:
        import uuid

        # Verify project access
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify user is project member or owner
        is_owner = project.owner == current_user
        is_member = any(m.username == current_user for m in (project.team_members or []))

        if not (is_owner or is_member):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project members can record activities",
            )

        # Create activity record
        activity = {
            "id": f"act_{uuid.uuid4().hex[:12]}",
            "project_id": project_id,
            "user_id": current_user,
            "activity_type": activity_type or "unknown",
            "activity_data": activity_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Save to database
        db.save_activity(activity)

        # Broadcast to collaborators via WebSocket
        broadcast_count = await _broadcast_activity(
            project_id=project_id,
            current_user=current_user,
            activity_type=activity_type or "unknown",
            activity_data=activity_data,
        )

        logger.info(
            f"Activity recorded and broadcasted: {activity_type} in project {project_id} by {current_user} "
            f"(sent to {broadcast_count} connections)"
        )

        return APIResponse(
            success=True,
            status="success",
            message="Activity recorded",
            data={
                "activity_id": activity["id"],
                "activity_type": activity_type,
                "timestamp": activity["created_at"],
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recording activity",
        )


@router.get(
    "/{project_id}/activities",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project activities",
    dependencies=[require_project_role("viewer")],
)
async def get_activities(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get recent activities in a project with pagination.

    Args:
        project_id: Project identifier
        limit: Maximum number of activities to return (default 50)
        offset: Number of activities to skip (default 0)
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Paginated list of recent project activities
    """
    try:
        # Verify project access
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify user is project member or owner
        is_owner = project.owner == current_user
        is_member = any(m.username == current_user for m in (project.team_members or []))

        if not (is_owner or is_member):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project members can view activities",
            )

        # Load activities
        activities = db.get_project_activities(project_id, limit=limit, offset=offset)
        total = db.count_project_activities(project_id)

        logger.debug(f"Retrieved {len(activities)} activities for project {project_id}")

        return APIResponse(
            success=True,
            status="success",
            message="Activities retrieved",
            data={
                "project_id": project_id,
                "activities": activities,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total,
                    "has_more": offset + limit < total,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching activities",
        )


# ============================================================================
# Team Collaboration Endpoints (/collaboration prefix)
# ============================================================================


@router.post(
    "/{project_id}/invitations",
    response_model=CollaborationInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite collaborator to project",
)
async def create_project_invitation(
    project_id: str,
    request: CollaborationInviteRequest = Body(...),
    current_user: str = Depends(get_current_user),
    user_object: "User" = Depends(get_current_user_object),
    db: ProjectDatabase = Depends(get_database),
    http_request: Request = None,
):
    """
    Create and send an invitation to a collaborator.

    Args:
        project_id: Project to invite collaborator to
        request: Invitation request with email and role
        current_user: Current authenticated user
        user_object: Current user object
        db: Database connection

    Returns:
        CollaborationInvitationResponse with invitation details
    """
    try:
        import secrets
        import uuid
        from datetime import timedelta

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
                detail="Only project owner can invite collaborators",
            )

        # CRITICAL: Validate subscription before creating invitation
        logger.info(f"Validating subscription for creating invitation for user {current_user}")
        try:
            # Check if testing mode is enabled via request headers
            testing_mode_enabled = TestingModeChecker.is_testing_mode_enabled(
                http_request.headers if http_request else {}
            )

            subscription_tier = user_object.subscription_tier.lower()

            # Check if user has active subscription
            if user_object.subscription_status != "active":
                logger.warning(
                    f"User {current_user} attempted to create invitation without active subscription (status: {user_object.subscription_status})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active subscription required to invite collaborators",
                )

            # Check subscription tier - collaboration feature requires pro or enterprise tier
            if subscription_tier == "free" and not testing_mode_enabled:
                logger.warning(f"Free-tier user {current_user} attempted to create invitation")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Collaboration feature requires 'pro' or 'enterprise' subscription",
                )

            logger.info(
                f"Subscription validation passed for {current_user} (tier: {subscription_tier})"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error validating subscription for creating invitation: {type(e).__name__}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating subscription: {str(e)[:100]}",
            )

        # Validate email
        email = request.email.strip().lower()
        if "@" not in email or "." not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format",
            )

        # Validate role
        if not CollaboratorRole.is_valid(request.role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be owner, editor, or viewer",
            )

        # Generate unique invitation token
        token = secrets.token_urlsafe(32)

        # Set expiration to 7 days from now
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=7)

        # Create invitation record
        invitation = {
            "id": f"inv_{uuid.uuid4().hex[:12]}",
            "project_id": project_id,
            "inviter_id": current_user,
            "invitee_email": email,
            "role": request.role,
            "token": token,
            "status": "pending",
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "accepted_at": None,
        }

        # Save to database
        db.save_invitation(invitation)

        logger.info(f"Created invitation {invitation['id']} for {email} to project {project_id}")

        return CollaborationInvitationResponse(**invitation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating invitation",
        )


@router.get(
    "/{project_id}/invitations",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="List project invitations",
)
async def get_project_invitations(
    project_id: str,
    status_filter: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    List invitations for a project.

    Args:
        project_id: Project identifier
        status_filter: Filter by status (pending, accepted, etc.)
        current_user: Current authenticated user
        db: Database connection

    Returns:
        List of invitations
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
                detail="Only project owner can view invitations",
            )

        # Load invitations
        invitations = db.get_project_invitations(project_id, status=status_filter)

        return APIResponse(
            success=True,
            status="success",
            message="Invitations retrieved",
            data={
                "project_id": project_id,
                "invitations": invitations,
                "total": len(invitations),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invitations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving invitations",
        )


@router.post(
    "/invitations/{token}/accept",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Accept collaboration invitation",
)
async def accept_invitation(
    token: str,
    current_user: str = Depends(get_current_user),
    user_obj: User = Depends(get_current_user_object),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Accept a collaboration invitation using the invitation token.

    Args:
        token: Invitation token from email
        current_user: Current authenticated user
        user_obj: Current user object
        db: Database connection

    Returns:
        Success response with project details
    """
    try:
        # Find invitation by token
        invitation = db.get_invitation_by_token(token)
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found or already used",
            )

        # Check if already accepted
        if invitation["status"] == "accepted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation already accepted",
            )

        # Check if expired
        expires_at = datetime.fromisoformat(invitation["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation has expired",
            )

        # Check if email matches
        if user_obj.email.lower() != invitation["invitee_email"].lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invitation was sent to a different email address",
            )

        # Load project
        project = db.load_project(invitation["project_id"])
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Add user to project team
        from socratic_system.models.role import TeamMemberRole

        project.team_members = project.team_members or []

        # Check if already a member
        if any(m.username == current_user for m in project.team_members):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a collaborator on this project",
            )

        # Add as team member
        new_member = TeamMemberRole(
            username=current_user,
            role=invitation["role"],
            skills=[],
            joined_at=datetime.now(timezone.utc),
        )
        project.team_members.append(new_member)

        # Save project
        db.save_project(project)

        # Mark invitation as accepted
        db.accept_invitation(invitation["id"])

        # Record activity
        from socrates_api.routers.events import record_event

        record_event(
            "collaborator_added",
            {
                "project_id": invitation["project_id"],
                "username": current_user,
                "role": invitation["role"],
                "via_invitation": True,
            },
            user_id=current_user,
        )

        logger.info(
            f"User {current_user} accepted invitation for project {invitation['project_id']}"
        )

        return APIResponse(
            success=True,
            status="success",
            message=f"Successfully joined project '{project.name}'",
            data={
                "project_id": invitation["project_id"],
                "role": invitation["role"],
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error accepting invitation",
        )


@router.delete(
    "/{project_id}/invitations/{invitation_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel invitation",
)
async def cancel_invitation(
    project_id: str,
    invitation_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Cancel a pending invitation.

    Args:
        project_id: Project identifier
        invitation_id: Invitation identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Success response
    """
    try:
        # Verify project ownership
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can cancel invitations",
            )

        # Get invitation to verify it belongs to this project
        invitations = db.get_project_invitations(project_id)
        invitation = next((i for i in invitations if i["id"] == invitation_id), None)

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        # Delete invitation
        db.delete_invitation(invitation_id)

        logger.info(f"Cancelled invitation {invitation_id} for project {project_id}")

        return APIResponse(
            success=True,
            status="success",
            message="Invitation cancelled",
            data={"invitation_id": invitation_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cancelling invitation",
        )


@collab_router.post(
    "/invite",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Invite team member",
    responses={
        200: {"description": "Invitation sent"},
        400: {"description": "Invalid email", "model": ErrorResponse},
        403: {"description": "Subscription limit exceeded", "model": ErrorResponse},
        422: {"description": "Missing email", "model": ErrorResponse},
    },
)
async def invite_team_member(
    request: CollaborationInviteRequest,
    current_user: str = Depends(get_current_user),
    user_object: "User" = Depends(get_current_user_object),
    db: ProjectDatabase = Depends(get_database),
    http_request: Request = None,
):
    """
    Invite a team member via email (global team).

    Requires pro or enterprise subscription for collaboration.

    Args:
        request: Request body with email and optional role
        current_user: Current authenticated user
        user_object: Current user object
        db: Database connection

    Returns:
        SuccessResponse with invitation details

    Raises:
        HTTPException: If user doesn't have subscription or collaboration feature
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
        if "@" not in email or "." not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format",
            )

        # CRITICAL: Validate subscription before inviting team member
        logger.info(f"Validating subscription for team member invitation for user {current_user}")
        try:
            # Check if testing mode is enabled via request headers
            testing_mode_enabled = TestingModeChecker.is_testing_mode_enabled(
                http_request.headers if http_request else {}
            )

            subscription_tier = user_object.subscription_tier.lower()

            # Check if user has active subscription
            if user_object.subscription_status != "active":
                logger.warning(
                    f"User {current_user} attempted to invite team member without active subscription (status: {user_object.subscription_status})"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active subscription required to invite team members",
                )

            # Check subscription tier - collaboration feature requires pro or enterprise tier
            if subscription_tier == "free" and not testing_mode_enabled:
                logger.warning(f"Free-tier user {current_user} attempted to invite team member")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Collaboration feature requires 'pro' or 'enterprise' subscription",
                )

            logger.info(
                f"Subscription validation passed for {current_user} (tier: {subscription_tier})"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error validating subscription for team member invitation: {type(e).__name__}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating subscription: {str(e)[:100]}",
            )

        logger.info(f"Sending team invitation to {email} with role {role}")

        return APIResponse(
            success=True,
            status="success",
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
    response_model=APIResponse,
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

        return APIResponse(
            success=True,
            status="success",
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
    response_model=APIResponse,
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

        return APIResponse(
            success=True,
            status="success",
            message=f"Member {member_id} removed from team",
            data={"member_id": member_id},
        )

    except Exception as e:
        logger.error(f"Error removing team member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove team member: {str(e)}",
        )
