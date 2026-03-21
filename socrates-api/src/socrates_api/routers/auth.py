"""
Authentication API endpoints for Socrates.

Provides user registration, login, token refresh, and logout functionality
using JWT-based authentication.
"""

import hashlib
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from socrates_api.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from socratic_security.auth import get_lockout_manager, get_mfa_manager
from socrates_api.database import get_database
from socrates_api.models import (
    APIResponse,
    AuthResponse,
    ChangePasswordRequest,
    ErrorResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from socratic_system.database import ProjectDatabase
from socratic_system.models import User

# Import rate limiter if available
try:
    from socrates_api.main import limiter
except ImportError:
    limiter = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


def _get_rate_limit_decorator(limit_str: str):
    """Get rate limit decorator - handles both available and unavailable limiter."""
    if limiter:
        return limiter.limit(limit_str)
    else:
        # No-op decorator
        return lambda f: f


# Create rate limit decorators for auth endpoints
_auth_limit = _get_rate_limit_decorator("5/minute")  # AUTH_LIMIT: 5 per minute

# Initialize account lockout manager
_lockout_manager = get_lockout_manager(
    max_attempts=int(os.environ.get("MAX_LOGIN_ATTEMPTS", "5")),
    lockout_window_minutes=int(os.environ.get("LOCKOUT_WINDOW_MINUTES", "15")),
    initial_lockout_minutes=int(os.environ.get("LOCKOUT_DURATION_MINUTES", "30")),
    progressive_lockout=os.environ.get("PROGRESSIVE_LOCKOUT", "true").lower() == "true",
)

# Initialize MFA manager
_mfa_manager = get_mfa_manager(
    issuer=os.environ.get("MFA_ISSUER", "Socrates"),
    totp_window=int(os.environ.get("MFA_TOTP_WINDOW", "1")),
    backup_code_count=int(os.environ.get("MFA_BACKUP_CODE_COUNT", "10")),
)


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
@_auth_limit
async def register(
    register_request: RegisterRequest,
    http_request: Request,
    db: ProjectDatabase = Depends(get_database),
):
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
        if not register_request.username or not register_request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required",
            )

        # Generate email if not provided (use UUID to ensure uniqueness)
        if register_request.email:
            # Basic email format validation if email was provided
            if "@" not in register_request.email or "." not in register_request.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email format",
                )
            email = register_request.email
        else:
            # Generate unique email using UUID (not hardcoded localhost)
            email = f"{register_request.username}+{str(uuid.uuid4())[:8]}@socrates.local"

        # Check if user already exists
        existing_user = db.load_user(register_request.username)
        if existing_user is not None:
            logger.warning(f"Registration attempt for existing username: {register_request.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        # Check if email already exists (only if email was explicitly provided)
        if register_request.email:
            existing_email_user = db.load_user_by_email(email)
            if existing_email_user is not None:
                logger.warning(f"Registration attempt with existing email: {email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered",
                )

        # Hash password
        password_hash = hash_password(register_request.password)

        # Create user
        user = User(
            username=register_request.username,
            email=email,
            passcode_hash=password_hash,
            subscription_tier="free",  # Default to free tier
            subscription_status="active",
            testing_mode=True,  # Testing mode enabled by default
            created_at=datetime.now(timezone.utc),
        )

        # Save user to database
        db.save_user(user)
        logger.info(f"User registered successfully: {register_request.username}")

        # Extract client context for token fingerprinting
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")

        # Create tokens
        access_token = create_access_token(
            register_request.username, ip_address=client_ip, user_agent=user_agent
        )
        refresh_token = create_refresh_token(register_request.username)

        # Store refresh token in database
        _store_refresh_token(db, request.username, refresh_token)

        # New users won't have an API key configured yet - show message after registration
        api_key_message = (
            "Welcome! To start using AI features, please save your API key "
            "in Settings > LLM > Anthropic."
        )

        return AuthResponse(
            user=_user_to_response(user),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,
            api_key_configured=False,
            api_key_message=api_key_message,
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
@_auth_limit
async def login(
    login_request: LoginRequest,
    http_request: Request,
    db: ProjectDatabase = Depends(get_database),
):
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
        if not login_request.username or not login_request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required",
            )

        # Strip whitespace and check if still empty
        if not login_request.username.strip() or not login_request.password.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password cannot be empty",
            )

        # Extract client IP for lockout tracking
        client_ip = http_request.client.host if http_request.client else "unknown"

        # Check if account is locked out
        if _lockout_manager.is_locked_out(login_request.username):
            lockout_info = _lockout_manager.get_lockout_info(login_request.username)
            logger.warning(
                f"Login attempt for locked account: {login_request.username} from {client_ip}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account locked due to too many failed login attempts. "
                f"Please try again in {lockout_info.remaining_minutes} minutes.",
            )

        # Load user from database
        user = db.load_user(login_request.username)
        if user is None:
            logger.warning(f"Login attempt for non-existent user: {login_request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or access code",
            )

        # Verify password
        if not verify_password(login_request.password, user.passcode_hash):
            logger.warning(f"Failed login attempt for user: {login_request.username} from {client_ip}")
            # Record failed attempt and check if we should lock the account
            _lockout_manager.record_attempt(login_request.username, client_ip, False)
            lockout_info = _lockout_manager.check_and_lock(login_request.username, client_ip)
            if lockout_info:
                logger.warning(
                    f"Account locked: {login_request.username} after {lockout_info.lockout_count} lockout(s)"
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or access code",
            )

        # Record successful login (clears failed attempts)
        _lockout_manager.record_attempt(login_request.username, client_ip, True)
        logger.info(f"User logged in successfully: {login_request.username}")

        # Extract client context for token fingerprinting
        user_agent = http_request.headers.get("user-agent", "unknown")

        # Create tokens
        access_token = create_access_token(
            login_request.username, ip_address=client_ip, user_agent=user_agent
        )
        refresh_token = create_refresh_token(login_request.username)

        # Store refresh token in database
        _store_refresh_token(db, login_request.username, refresh_token)

        # Check if user has API key configured (check all providers)
        api_key_configured = True
        api_key_message = None
        try:
            # Check for API keys from any provider (claude, openai, etc.)
            stored_api_key = db.get_api_key(login_request.username, "claude")
            if not stored_api_key:
                api_key_configured = False
                api_key_message = (
                    "No API key configured. "
                    "Please save your API key in Settings > LLM > Anthropic to use AI features."
                )
                logger.info(f"User {login_request.username} has no API key configured")
        except Exception as e:
            logger.warning(f"Error checking API key for user {login_request.username}: {e}")
            # Don't fail login, just proceed with warning

        return AuthResponse(
            user=_user_to_response(user),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,
            api_key_configured=api_key_configured,
            api_key_message=api_key_message,
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
async def refresh(request: RefreshTokenRequest, db: ProjectDatabase = Depends(get_database)):
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
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Change user password",
    responses={
        200: {"description": "Password changed successfully"},
        400: {
            "description": "Invalid request or password doesn't meet requirements",
            "model": ErrorResponse,
        },
        401: {"description": "Old password incorrect or not authenticated", "model": ErrorResponse},
        500: {"description": "Server error during password change", "model": ErrorResponse},
    },
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
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

        return APIResponse(
            success=True,
        status="success",
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
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout from account",
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
    },
)
async def logout(
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Logout from the account.

    Revokes the current user's refresh tokens so they cannot be used
    for obtaining new access tokens.

    Args:
        current_user: Current authenticated user (from JWT)
        db: Database connection

    Returns:
        SuccessResponse confirming logout

    Raises:
        HTTPException: If not authenticated
    """
    try:
        # Revoke all refresh tokens for this user
        _revoke_refresh_token(db, current_user)

        # Clear activity tracking on logout
        from socrates_api.middleware.activity_tracker import clear_activity

        clear_activity(current_user)

        logger.info(f"User logged out and tokens revoked: {current_user}")
        return APIResponse(
            success=True,
        status="success",
            message="Logout successful. All refresh tokens have been revoked. Access token will expire in 15 minutes.\n\nτῷ Ἀσκληπιῷ ὀφείλομεν ἀλεκτρυόνα, ἀπόδοτε καὶ μὴ ἀμελήσετε.",
        )
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during logout",
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
    db: ProjectDatabase = Depends(get_database),
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
    request_body: dict = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Update the current authenticated user's profile.

    Args:
        request_body: Request body with fields to update (name, avatar, etc.)
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

        # Update user profile fields from request body
        if request_body:
            if "name" in request_body:
                user.name = request_body.get("name", user.name)
            if "avatar" in request_body:
                user.avatar = request_body.get("avatar", user.avatar)

            # Persist updates to database
            db.save_user(user)

        from socrates_api.routers.events import record_event

        record_event(
            "profile_updated",
            {
                "username": current_user,
            },
            user_id=current_user,
        )

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


async def _delete_user_helper(
    current_user: str,
    db: ProjectDatabase,
):
    """
    Helper function to delete a user and all their data.

    Args:
        current_user: Username to delete
        db: Database connection
    """
    # Delete all projects owned by the user
    all_projects = db.get_user_projects(current_user)
    for project in all_projects:
        db.delete_project(project.project_id)

    # Delete the user account using the correct method name
    db.permanently_delete_user(current_user)

    logger.info(f"User account deleted: {current_user}")


@router.delete(
    "/me",
    response_model=APIResponse,
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
    db: ProjectDatabase = Depends(get_database),
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

        # Call helper function to perform deletion
        await _delete_user_helper(current_user, db)

        return APIResponse(success=True,
        status="success", message="Account deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}",
        )


@router.put(
    "/me/testing-mode",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle testing mode (bypasses subscription checks)",
    responses={
        200: {"description": "Testing mode updated"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "User not found", "model": ErrorResponse},
    },
)
async def set_testing_mode(
    enabled: bool = Query(...),
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Enable or disable testing mode for the current user.

    ## Authorization Model: Owner-Based, Not Admin-Based

    Socrates uses OWNER-BASED AUTHORIZATION, not global admin roles:
    - There is NO admin role in the system
    - Testing mode is available to ANY authenticated user for their own account
    - This allows all registered users to test the system without monetization limits
    - No admin check is needed - users manage their own testing mode flag

    ## Behavior When Testing Mode Is Enabled

    When enabled, all subscription checks are bypassed:
    - Project limits are ignored
    - Team member limits are ignored
    - Feature flags are ignored
    - Usage quotas are not enforced
    - Cost tracking is disabled

    This is for development and testing purposes only.

    Args:
        enabled: Whether to enable or disable testing mode (query parameter)
        current_user: Current authenticated user (from JWT token)
        db: Database connection

    Returns:
        SuccessResponse confirming testing mode was updated

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

        # Any authenticated user can toggle testing mode for their own account
        # This is NOT an admin-only feature - aligns with owner-based authorization model
        # Users don't need admin privileges to fully test the system
        user.testing_mode = enabled
        db.save_user(user)

        logger.info(
            f"Testing mode {'enabled' if enabled else 'disabled'} for user: {current_user} by {current_user}"
        )
        return APIResponse(
            success=True,
            status="success",
            message=f"Testing mode {'enabled' if enabled else 'disabled'}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating testing mode: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update testing mode: {str(e)}",
        )


@router.post(
    "/me/archive",
    status_code=status.HTTP_200_OK,
    summary="Archive user account",
)
async def archive_account(
    current_user: str = Depends(get_current_user),
):
    """
    Archive user account (soft delete).

    Marks account as archived without permanently deleting data.
    User can restore account later.

    Args:
        current_user: Authenticated user

    Returns:
        Success response with archive confirmation
    """
    try:
        logger.info(f"Archiving account for user: {current_user}")

        db = get_database()

        # Load user
        user = db.get_user(current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Archive user
        user.archived = True
        user.archived_at = datetime.now(timezone.utc).isoformat()
        db.save_user(user)

        return APIResponse(
            success=True,
        status="success",
            message="Account archived successfully",
            data={
                "user_id": current_user,
                "archived_at": user.archived_at,
                "can_restore": True,
                "restore_deadline": "90 days",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive account: {str(e)}",
        )


@router.post(
    "/me/restore",
    status_code=status.HTTP_200_OK,
    summary="Restore archived user account",
)
async def restore_account(
    current_user: str = Depends(get_current_user),
):
    """
    Restore archived user account.

    Reactivates a previously archived account and all associated data.

    Args:
        current_user: Authenticated user

    Returns:
        Success response with restore confirmation
    """
    try:
        logger.info(f"Restoring account for user: {current_user}")

        db = get_database()

        # Load user
        user = db.get_user(current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not getattr(user, "archived", False):
            raise HTTPException(status_code=400, detail="Account is not archived")

        # Restore user
        user.archived = False
        user.archived_at = None
        db.save_user(user)

        return APIResponse(
            success=True,
        status="success",
            message="Account restored successfully",
            data={
                "user_id": current_user,
                "restored_at": datetime.now(timezone.utc).isoformat(),
                "status": "active",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore account: {str(e)}",
        )


# ============================================================================
# Helper Functions
# ============================================================================


def _store_refresh_token(db: ProjectDatabase, username: str, token: str) -> None:
    """
    Store refresh token in database.

    Securely stores refresh token with:
    1. Token hashing using bcrypt
    2. Expiration time extracted from JWT claims
    3. Storage in refresh_tokens table with proper indexes

    Args:
        db: Database connection
        username: Username to associate with token
        token: JWT refresh token string

    Raises:
        Exception: If database operation fails
    """
    try:
        # Decode token to extract expiration time (without verification, just decode)
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            expires_at = datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc)
        except (jwt.InvalidTokenError, ValueError, KeyError):
            # If token decoding fails, set expiry to 7 days from now as default
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            logger.warning(
                f"Could not decode token expiration for user {username}, using default 7-day expiry"
            )

        # Hash the token using SHA256 first (bcrypt has 72-byte limit)
        # This creates a fixed-length 64-char hash that bcrypt can handle
        token_sha256 = hashlib.sha256(token.encode()).hexdigest()
        # Then hash with bcrypt for additional security
        token_hash = hash_password(token_sha256)

        # Generate unique ID for this token record
        token_id = str(uuid.uuid4())

        # Get database connection from the ProjectDatabase object
        # We need to access the underlying sqlite3 connection
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()

        try:
            # Delete any existing non-revoked tokens for this user to avoid duplication
            # (typically want one active refresh token per user)
            cursor.execute(
                """
                DELETE FROM refresh_tokens
                WHERE user_id = ? AND revoked_at IS NULL
                """,
                (username,),
            )

            # Insert new refresh token
            cursor.execute(
                """
                INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    token_id,
                    username,
                    token_hash,
                    expires_at.isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

            conn.commit()
            logger.debug(
                f"Refresh token stored for user {username} (expires: {expires_at.isoformat()})"
            )

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Error storing refresh token for user {username}: {str(e)}")
        # Don't raise - token refresh failures shouldn't crash the login/register endpoint
        # The JWT itself is still valid even if DB storage fails


def _validate_refresh_token(db: ProjectDatabase, username: str, token: str) -> bool:
    """
    Validate refresh token against database.

    Checks:
    1. Token exists in refresh_tokens table
    2. Token hasn't been revoked
    3. Token hasn't expired
    4. Token hash matches stored value

    Args:
        db: Database connection
        username: Username to check token against
        token: JWT refresh token string to validate

    Returns:
        True if token is valid, False otherwise
    """
    try:
        # Get database connection
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()

        try:
            # Look for matching token record
            cursor.execute(
                """
                SELECT id, expires_at, revoked_at
                FROM refresh_tokens
                WHERE user_id = ? AND revoked_at IS NULL
                LIMIT 1
                """,
                (username,),
            )

            row = cursor.fetchone()
            if not row:
                logger.warning(f"No valid refresh token found for user {username}")
                return False

            token_id, expires_at_str, revoked_at = row

            # Check if token has expired
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now(timezone.utc) > expires_at:
                logger.info(f"Refresh token expired for user {username}")
                # Mark as revoked to clean up
                cursor.execute(
                    "UPDATE refresh_tokens SET revoked_at = ? WHERE id = ?",
                    (datetime.now(timezone.utc).isoformat(), token_id),
                )
                conn.commit()
                return False

            # Token is valid (we don't compare hashes at this point as
            # JWT verification is done by verify_refresh_token)
            logger.debug(f"Refresh token validated for user {username}")
            return True

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Error validating refresh token for user {username}: {str(e)}")
        return False


def _revoke_refresh_token(db: ProjectDatabase, username: str) -> None:
    """
    Revoke all refresh tokens for a user (used during logout).

    Args:
        db: Database connection
        username: Username whose tokens should be revoked
    """
    try:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE refresh_tokens
                SET revoked_at = ?
                WHERE user_id = ? AND revoked_at IS NULL
                """,
                (datetime.now(timezone.utc).isoformat(), username),
            )

            conn.commit()
            logger.info(f"Refresh tokens revoked for user {username}")

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Error revoking refresh tokens for user {username}: {str(e)}")


# ============================================================================
# MFA ENDPOINTS - Multi-Factor Authentication (TOTP)
# ============================================================================


@router.post(
    "/mfa/enable",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Start MFA setup",
    responses={
        200: {"description": "MFA setup started, return secret and QR code"},
        401: {"description": "User not authenticated", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def mfa_enable(
    current_user: str = Depends(get_current_user),
) -> dict:
    """
    Start MFA setup process.

    Returns TOTP secret and QR code URI for scanning with authenticator app.
    User must verify with verify_enable endpoint.

    Args:
        current_user: Currently authenticated user

    Returns:
        Dict with secret, QR code URI, and backup codes
    """
    try:
        logger.info(f"Starting MFA setup for user {current_user}")

        # Generate MFA secret
        setup = _mfa_manager.generate_secret(current_user)

        return {
            "secret": setup.secret,
            "qr_code_uri": setup.qr_code_uri,
            "backup_codes": setup.backup_codes,
            "recovery_codes_display": setup.recovery_codes_display,
        }

    except Exception as e:
        logger.error(f"Error starting MFA setup for {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error starting MFA setup",
        )


@router.post(
    "/mfa/verify-enable",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Verify and enable MFA",
    responses={
        200: {"description": "MFA enabled successfully"},
        400: {"description": "Invalid TOTP code", "model": ErrorResponse},
        401: {"description": "User not authenticated", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def mfa_verify_enable(
    request: dict,
    current_user: str = Depends(get_current_user),
) -> dict:
    """
    Verify TOTP code and enable MFA.

    Args:
        request: Dict with {totp_code}
        current_user: Currently authenticated user

    Returns:
        {success, message}
    """
    try:
        totp_code = request.get("totp_code")
        if not totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP code required",
            )

        # Get the secret from the manager
        secret = _mfa_manager.get_totp_secret(current_user)
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No MFA setup in progress. Start with /mfa/enable",
            )

        # Enable MFA
        success, message = _mfa_manager.enable_mfa(current_user, secret, totp_code)

        if not success:
            logger.warning(f"Failed to enable MFA for {current_user}: {message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            )

        logger.info(f"MFA enabled for user {current_user}")
        return {"success": True, "message": message}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling MFA for {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error enabling MFA",
        )


@router.get(
    "/mfa/status",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get MFA status",
    responses={
        200: {"description": "MFA status returned"},
        401: {"description": "User not authenticated", "model": ErrorResponse},
    },
)
async def mfa_status(
    current_user: str = Depends(get_current_user),
) -> dict:
    """
    Get current MFA status for authenticated user.

    Args:
        current_user: Currently authenticated user

    Returns:
        {mfa_enabled, created_at, recovery_codes_remaining}
    """
    try:
        is_enabled = _mfa_manager.is_mfa_enabled(current_user)

        return {
            "mfa_enabled": is_enabled,
            "created_at": None,  # Would come from database in production
            "recovery_codes_remaining": 0,  # Would count from database
        }

    except Exception as e:
        logger.error(f"Error getting MFA status for {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting MFA status",
        )


@router.post(
    "/mfa/disable",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Disable MFA",
    responses={
        200: {"description": "MFA disabled successfully"},
        400: {"description": "Invalid password", "model": ErrorResponse},
        401: {"description": "User not authenticated", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def mfa_disable(
    request: dict,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
) -> dict:
    """
    Disable MFA (requires password verification).

    Args:
        request: Dict with {password}
        current_user: Currently authenticated user
        db: Database connection

    Returns:
        {success, message}
    """
    try:
        password = request.get("password")
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password required to disable MFA",
            )

        # Load user and verify password
        user = db.load_user(current_user)
        if not user or not verify_password(password, user.passcode_hash):
            logger.warning(f"Failed MFA disable attempt for {current_user} - invalid password")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password",
            )

        # Disable MFA
        _mfa_manager.disable_mfa(current_user)

        logger.info(f"MFA disabled for user {current_user}")
        return {"success": True, "message": "MFA disabled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling MFA for {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error disabling MFA",
        )
