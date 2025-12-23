"""
FastAPI Dependencies for Authentication.

Provides FastAPI Depends() callables for extracting and validating
authenticated user information from requests.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from socrates_api.auth.jwt_handler import verify_access_token
from socratic_system.models import User
from socrates_api.database import get_database
from socratic_system.database import ProjectDatabaseV2

# Security scheme for Swagger/OpenAPI documentation
security = HTTPBearer(auto_error=False)


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
    # 401 when auth header is missing or token is invalid
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are required",
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
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
    db: ProjectDatabaseV2 = Depends(get_database),
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
    db: ProjectDatabaseV2 = Depends(get_database),
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
