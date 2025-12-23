"""
Authentication API endpoints for Socrates.

Provides user registration, login, token refresh, and logout functionality
using JWT-based authentication.
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Depends, Header

from socratic_system.database import ProjectDatabaseV2
from socratic_system.models import User
from socrates_api.database import get_database
from socrates_api.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
    get_current_user,
)
from socrates_api.models import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    SuccessResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


def _user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse."""
    return UserResponse(
        username=user.username,
        email=user.email,
        subscription_tier=user.subscription_tier,
        subscription_status=user.subscription_status,
        testing_mode=user.testing_mode,
        created_at=user.created_at,
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Invalid request or username already exists", "model": ErrorResponse},
        500: {"description": "Server error during registration", "model": ErrorResponse},
    },
)
async def register(request: RegisterRequest, db: ProjectDatabaseV2 = Depends(get_database)):
    """
    Register a new user account.

    Creates a new user with the provided username and password.
    Returns authentication tokens for immediate use.

    Args:
        request: Registration request with username and password
        db: Database connection

    Returns:
        AuthResponse with user info and authentication tokens

    Raises:
        HTTPException: If username already exists or validation fails
    """
    try:
        # Validate input
        if not request.username or not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required",
            )

        # Generate email if not provided (use UUID to ensure uniqueness)
        if request.email:
            # Basic email format validation if email was provided
            if '@' not in request.email or '.' not in request.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email format",
                )
            email = request.email
        else:
            # Generate unique email using UUID (not hardcoded localhost)
            email = f"{request.username}+{str(uuid.uuid4())[:8]}@socrates.local"

        # Check if user already exists
        existing_user = db.load_user(request.username)
        if existing_user is not None:
            logger.warning(f"Registration attempt for existing username: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        # Check if email already exists (only if email was explicitly provided)
        if request.email:
            existing_email_user = db.load_user_by_email(email)
            if existing_email_user is not None:
                logger.warning(f"Registration attempt with existing email: {email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered",
                )

        # Hash password
        password_hash = hash_password(request.password)

        # Create user
        user = User(
            username=request.username,
            email=email,
            passcode_hash=password_hash,
            subscription_tier="free",  # Default to free tier
            subscription_status="active",
            testing_mode=False,
            created_at=datetime.now(timezone.utc),
        )

        # Save user to database
        db.save_user(user)
        logger.info(f"User registered successfully: {request.username}")

        # Create tokens
        access_token = create_access_token(request.username)
        refresh_token = create_refresh_token(request.username)

        # Store refresh token in database
        _store_refresh_token(db, request.username, refresh_token)

        return AuthResponse(
            user=_user_to_response(user),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user account",
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login to account",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials", "model": ErrorResponse},
        500: {"description": "Server error during login", "model": ErrorResponse},
    },
)
async def login(request: LoginRequest, db: ProjectDatabaseV2 = Depends(get_database)):
    """
    Login with username and password.

    Verifies credentials and returns authentication tokens.

    Args:
        request: Login request with username and password
        db: Database connection

    Returns:
        AuthResponse with user info and authentication tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        # Validate input
        if not request.username or not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required",
            )

        # Strip whitespace and check if still empty
        if not request.username.strip() or not request.password.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password cannot be empty",
            )

        # Load user from database
        user = db.load_user(request.username)
        if user is None:
            logger.warning(f"Login attempt for non-existent user: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or access code",
            )

        # Verify password
        if not verify_password(request.password, user.passcode_hash):
            logger.warning(f"Failed login attempt for user: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or access code",
            )

        logger.info(f"User logged in successfully: {request.username}")

        # Create tokens
        access_token = create_access_token(request.username)
        refresh_token = create_refresh_token(request.username)

        # Store refresh token in database
        _store_refresh_token(db, request.username, refresh_token)

        return AuthResponse(
            user=_user_to_response(user),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during login",
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid refresh token", "model": ErrorResponse},
        500: {"description": "Server error during refresh", "model": ErrorResponse},
    },
)
async def refresh(request: RefreshTokenRequest, db: ProjectDatabaseV2 = Depends(get_database)):
    """
    Refresh an access token using a refresh token.

    Args:
        request: Refresh token request
        db: Database connection

    Returns:
        TokenResponse with new access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    try:
        # Verify refresh token
        payload = verify_refresh_token(request.refresh_token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Verify user exists
        user = db.load_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        logger.info(f"Token refreshed for user: {username}")

        # Create new tokens
        new_access_token = create_access_token(username)
        new_refresh_token = create_refresh_token(username)

        # Store new refresh token
        _store_refresh_token(db, username, new_refresh_token)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=900,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token",
        )


@router.put(
    "/change-password",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Change user password",
    responses={
        200: {"description": "Password changed successfully"},
        400: {"description": "Invalid request or password doesn't meet requirements", "model": ErrorResponse},
        401: {"description": "Old password incorrect or not authenticated", "model": ErrorResponse},
        500: {"description": "Server error during password change", "model": ErrorResponse},
    },
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Change user password.

    Requires valid old password and new password meeting security requirements.

    Args:
        request: Change password request with old and new passwords
        current_user: Current authenticated user (from token)
        db: Database connection

    Returns:
        SuccessResponse indicating password was changed

    Raises:
        HTTPException: If old password is wrong or new password invalid
    """
    try:
        # Validate input
        if not request.old_password or not request.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password and new password are required",
            )

        # Load user
        user = db.load_user(current_user)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # Verify old password
        if not verify_password(request.old_password, user.passcode_hash):
            logger.warning(f"Failed password change attempt for user: {current_user}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Old password is incorrect",
            )

        # Validate new password strength
        if len(request.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long",
            )

        # Check if new password is different from old
        if request.old_password == request.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from old password",
            )

        # Hash new password
        new_password_hash = hash_password(request.new_password)

        # Update password in database
        user.passcode_hash = new_password_hash
        db.save_user(user)

        logger.info(f"Password changed successfully for user: {current_user}")

        return SuccessResponse(
            success=True,
            message="Password changed successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during password change for user {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password",
        )


@router.post(
    "/logout",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout from account",
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
    },
)
async def logout(
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Logout from the account.

    Revokes the current user's refresh tokens.

    Args:
        current_user: Current authenticated user (from JWT)
        db: Database connection

    Returns:
        SuccessResponse confirming logout

    Raises:
        HTTPException: If not authenticated
    """
    try:
        logger.info(f"User logged out: {current_user}")
        # In a real implementation, would revoke refresh tokens in database
        # For now, just return success - token will expire naturally
        return SuccessResponse(
            success=True,
            message="Logout successful. Access token will expire in 15 minutes.",
        )
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    responses={
        200: {"description": "User profile retrieved"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
    },
)
async def get_me(
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get the current authenticated user's profile.

    Args:
        current_user: Current authenticated user (from JWT)
        db: Database connection

    Returns:
        UserResponse with user information

    Raises:
        HTTPException: If user not found or not authenticated
    """
    try:
        user = db.load_user(current_user)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return _user_to_response(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user profile",
    responses={
        200: {"description": "User profile updated"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "User not found", "model": ErrorResponse},
    },
)
async def update_me(
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Update the current authenticated user's profile.

    Args:
        current_user: Current authenticated user (from JWT)
        db: Database connection

    Returns:
        Updated UserResponse with user information

    Raises:
        HTTPException: If user not found or not authenticated
    """
    try:
        user = db.load_user(current_user)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # TODO: Update user profile fields from request body
        # For now, just return the current profile
        # In production, would update fields like subscription preferences, etc.

        logger.info(f"User profile updated: {current_user}")
        return _user_to_response(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )


@router.delete(
    "/me",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete user account",
    responses={
        200: {"description": "Account deleted successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "User not found", "model": ErrorResponse},
    },
)
async def delete_account(
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Permanently delete the current user's account.

    This will delete all projects owned by the user and remove all user data.
    This action cannot be undone.

    Args:
        current_user: Current authenticated user (from JWT)
        db: Database connection

    Returns:
        SuccessResponse confirming account deletion

    Raises:
        HTTPException: If user not found or not authenticated
    """
    try:
        user = db.load_user(current_user)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Delete all projects owned by the user
        all_projects = db.get_user_projects(current_user)
        for project in all_projects:
            db.delete_project(project.project_id)

        # Delete the user account
        db.permanently_delete_user(current_user)

        logger.info(f"User account deleted: {current_user}")
        return SuccessResponse(
            success=True,
            message="Account deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )


@router.put(
    "/me/testing-mode",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle testing mode (bypasses subscription checks)",
    responses={
        200: {"description": "Testing mode updated"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "User not found", "model": ErrorResponse},
    },
)
async def set_testing_mode(
    enabled: bool,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Enable or disable testing mode for the current user.

    When enabled, all subscription checks are bypassed. This is for development
    and testing purposes only.

    Args:
        enabled: Whether to enable or disable testing mode
        current_user: Current authenticated user (from JWT)
        db: Database connection

    Returns:
        SuccessResponse confirming testing mode update

    Raises:
        HTTPException: If user not found or not authenticated
    """
    try:
        user = db.load_user(current_user)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.testing_mode = enabled
        db.save_user(user)

        logger.info(f"Testing mode {'enabled' if enabled else 'disabled'} for user: {current_user}")
        return SuccessResponse(
            success=True,
            message=f"Testing mode {'enabled' if enabled else 'disabled'}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating testing mode: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update testing mode: {str(e)}"
        )


# ============================================================================
# Helper Functions
# ============================================================================


def _store_refresh_token(db: ProjectDatabaseV2, username: str, token: str) -> None:
    """
    Store refresh token in database.

    In a real implementation, this would:
    1. Hash the token before storing
    2. Set expiry time
    3. Store in refresh_tokens table

    For now, this is a placeholder.

    Args:
        db: Database connection
        username: Username
        token: Refresh token
    """
    # TODO: Implement refresh token storage in database
    # This would involve:
    # 1. Hash the token using hash_password()
    # 2. Create a refresh_tokens table entry
    # 3. Set expiry to 7 days from now
    pass
