"""
FastAPI Dependencies for Authentication.

Provides FastAPI Depends() callables for extracting and validating
authenticated user information from requests.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from socrates_api.auth.jwt_handler import verify_access_token

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
        HTTPException: 403 if credentials missing, 401 if token invalid
    """
    # 403 when auth header is missing
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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
