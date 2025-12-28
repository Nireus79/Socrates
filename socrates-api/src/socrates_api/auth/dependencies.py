"""
FastAPI Dependencies for Authentication.

Provides FastAPI Depends() callables for extracting and validating
authenticated user information from requests.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from socrates_api.auth.jwt_handler import verify_access_token
from socratic_system.models import User
from socrates_api.database import get_database
from socratic_system.database import ProjectDatabase

logger = logging.getLogger(__name__)

# Security scheme for Swagger/OpenAPI documentation
security = HTTPBearer(auto_error=False)

# Security scheme for optional authentication (returns None on missing/invalid)
security_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    Extract and validate current user from Authorization header.

    Expected header format: Authorization: Bearer <jwt_token>

    Args:
        credentials: HTTP Bearer credentials from request (None if missing)

    Returns:
        User ID (subject) from valid JWT token

    Raises:
        HTTPException: 401 if credentials missing or token invalid
    """
    logger.debug(f"get_current_user called with credentials: {credentials}")
    # 401 when auth header is missing
    if not credentials:
        logger.warning("Missing authentication credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # 401 when token is invalid/expired
    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain user information",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> Optional[str]:
    """
    Extract user ID from token if present, otherwise return None.

    Useful for endpoints that support both authenticated and anonymous access.

    Args:
        credentials: HTTP Bearer credentials (optional)

    Returns:
        User ID if authenticated, None otherwise
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_access_token(token)

    if payload is None:
        return None

    return payload.get("sub")


async def get_current_user_object(
    username: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
) -> User:
    """
    Get full User object from database for authenticated user.

    This provides the complete User context (subscription info, email, status, etc.)
    needed for proper authorization and business logic checks.

    Args:
        username: Authenticated username from JWT token
        db: Database connection from dependency injection

    Returns:
        Full User object with all properties

    Raises:
        HTTPException: 404 if user not found in database
    """
    try:
        user = db.load_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {username} not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading user information"
        )


async def get_current_user_object_optional(
    username: Optional[str] = Depends(get_current_user_optional),
    db: ProjectDatabase = Depends(get_database),
) -> Optional[User]:
    """
    Get full User object if authenticated, otherwise return None.

    Useful for endpoints that support both authenticated and anonymous access
    and need full user context when available.

    Args:
        username: Authenticated username or None
        db: Database connection

    Returns:
        Full User object if authenticated, None otherwise
    """
    if username is None:
        return None

    try:
        user = db.load_user(username)
        return user
    except Exception:
        return None


def require_project_role(required_role: str):
    """
    Dependency factory to enforce role-based access control for project endpoints.

    Role hierarchy: owner > editor > viewer

    Usage in endpoint:
        @router.put("/{project_id}/settings", dependencies=[Depends(require_project_role("editor"))])
        async def update_project_settings(project_id: str, current_user: str = Depends(get_current_user)):
            ...

    Args:
        required_role: Minimum required role (owner, editor, or viewer)

    Returns:
        A dependency that validates the user's role for the project
    """

    async def check_role(
        project_id: str,
        current_user: str = Depends(get_current_user),
        db: ProjectDatabase = Depends(get_database),
    ) -> str:
        """
        Validate user has required role for project.

        Args:
            project_id: Project identifier
            current_user: Current authenticated user
            db: Database connection

        Returns:
            Current user (if authorized)

        Raises:
            HTTPException: 403 if user lacks required role
            HTTPException: 404 if project not found
        """
        # Load project
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Owner always has access
        if project.owner == current_user:
            return current_user

        # Check team members for role
        user_role = None
        if project.team_members:
            for member in project.team_members:
                if member.username == current_user:
                    user_role = member.role
                    break

        # User must be team member
        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a project member"
            )

        # Validate role hierarchy
        role_hierarchy = {"owner": 3, "editor": 2, "viewer": 1}
        required_level = role_hierarchy.get(required_role, 0)
        user_level = role_hierarchy.get(user_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role (user has {user_role})"
            )

        return current_user

    return Depends(check_role)
