"""
Authentication API endpoints for Socrates.

Provides user registration, login, token refresh, and logout functionality
using JWT-based authentication.
"""

import hashlib
import logging
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
from socrates_api.database import get_database
from socrates_api.models import (
    APIResponse,
    AuthResponse,
    ChangePasswordRequest,
    ErrorResponse,
    LoginRequest,
    MFADisableRequest,
    MFASetupResponse,
    MFAStatusResponse,
    MFAVerifyEnableRequest,
    MFAVerifyRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from socrates_api.models_local import User, ProjectDatabase

# Import security features (REQUIRED)
from socratic_security.auth import (
    AccountLockoutManager,
    check_password_breach,
    get_breach_checker,
    MFAManager,
    get_mfa_manager,
)

# Import rate limiter if available
try:
    from socrates_api.main import limiter
except ImportError:
    limiter = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

# Initialize account lockout manager (REQUIRED)
lockout_manager = AccountLockoutManager()

# Initialize MFA manager (REQUIRED)
mfa_manager = get_mfa_manager()


def _get_rate_limit_decorator(limit_str: str):
    """Get rate limit decorator - handles both available and unavailable limiter."""
    if limiter:
        return limiter.limit(limit_str)
    else:
        # No-op decorator
        return lambda f: f


# Create rate limit decorators for auth endpoints
_auth_limit = _get_rate_limit_decorator("5/minute")  # AUTH_LIMIT: 5 per minute


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


@router.get(
    "/csrf-token",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get CSRF token",
    responses={
        200: {"description": "CSRF token retrieved successfully"},
    },
)
async def get_csrf_token(http_request: Request):
    """
    Get a CSRF token for web UI form submissions.

    This endpoint returns a CSRF token that should be included in:
    - POST/PUT/DELETE request headers as X-CSRF-Token
    - Form submissions as _csrf field
    - Or passed in _csrf query parameter

    The token is automatically set as an HTTP-only cookie by the middleware.
    Token expires after 1 hour of inactivity.

    Note: CSRF protection is primarily for web UI endpoints, not for API clients
    that use proper authentication and CORS.

    Returns:
        APIResponse with message about CSRF token

    Example:
        ```bash
        # Get CSRF token
        curl http://localhost:8000/auth/csrf-token

        # Use in form submission
        curl -X POST http://localhost:8000/auth/login \\
          -H "X-CSRF-Token: <token>" \\
          -H "Content-Type: application/json" \\
          -d '{"username":"alice","password":"password"}'
        ```
    """
    from socrates_api.middleware.csrf import generate_csrf_token

    csrf_token = generate_csrf_token()
    logger.info(f"CSRF token generated for client {http_request.client.host if http_request.client else 'unknown'}")

    return APIResponse(
        success=True,
        status="success",
        message="CSRF token generated. Include X-CSRF-Token header or _csrf field in requests.",
        data={
            "csrf_token": csrf_token,
            "expires_in": 3600,  # 1 hour in seconds
            "header_name": "X-CSRF-Token",
        },
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Register a new user",
    responses={
        200: {"description": "User registered successfully"},
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

        # Check if password has been breached (REQUIRED security check)
        is_breached, breach_count = await check_password_breach(register_request.password)
        if is_breached:
            logger.warning(
                f"Registration blocked: password found in {breach_count} breaches"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password has been found in known data breaches. Please use a different password.",
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

        # Extract client IP and User-Agent for token fingerprinting
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")

        # Create tokens with fingerprinting
        access_token = create_access_token(
            register_request.username,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        refresh_token = create_refresh_token(register_request.username)

        # Store refresh token in database
        _store_refresh_token(db, register_request.username, refresh_token)

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

        # Check account lockout status (REQUIRED security check)
        if lockout_manager.is_locked_out(login_request.username):
            logger.warning(f"Login attempt for locked-out account: {login_request.username}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account temporarily locked due to too many failed login attempts. Please try again later.",
            )

        # Load user from database
        user_dict = db.load_user(login_request.username)
        if user_dict is None:
            logger.warning(f"Login attempt for non-existent user: {login_request.username}")
            # Record failed attempt for security tracking (REQUIRED)
            lockout_manager.record_attempt(login_request.username, "unknown", success=False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or access code",
            )

        # Convert dict to User object
        user = User(**user_dict)

        # Verify password
        if not verify_password(login_request.password, user.passcode_hash):
            logger.warning(f"Failed login attempt for user: {login_request.username}")
            # Record failed attempt and check for lockout (REQUIRED)
            lockout_manager.check_and_lock(login_request.username, "api")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or access code",
            )

        logger.info(f"User logged in successfully: {login_request.username}")

        # Record successful login attempt (REQUIRED)
        lockout_manager.record_attempt(login_request.username, "api", success=True)

        # Check if MFA is enabled for user (REQUIRED security check)
        if mfa_manager.is_mfa_enabled(login_request.username):
            logger.info(f"MFA verification required for user: {login_request.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA verification required. Please provide TOTP code or recovery code at POST /auth/login/mfa-verify",
            )

        # Extract client IP and User-Agent for token fingerprinting
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")

        # Create tokens with fingerprinting
        access_token = create_access_token(
            login_request.username,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        refresh_token = create_refresh_token(login_request.username)

        # Store refresh token in database
        _store_refresh_token(db, login_request.username, refresh_token)

        # Check if user has API key configured (check all providers)
        # TODO: Implement API key storage in database
        api_key_configured = False
        api_key_message = (
            "No API key configured. "
            "Please save your API key in Settings > LLM > Anthropic to use AI features."
        )

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
    "/login/mfa-verify",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify MFA during login",
    responses={
        200: {"description": "MFA verified, login successful"},
        400: {"description": "Invalid MFA code", "model": ErrorResponse},
        401: {"description": "Invalid credentials", "model": ErrorResponse},
        429: {"description": "Too many failed attempts", "model": ErrorResponse},
        503: {"description": "MFA not available", "model": ErrorResponse},
    },
)
@_auth_limit
async def login_mfa_verify(
    request: MFAVerifyRequest,
    http_request: Request,
    db: ProjectDatabase = Depends(get_database),
):
    """
    Verify MFA code after successful username/password authentication.

    This endpoint is called when the login endpoint returns 403 Forbidden due to MFA being required.
    Provide either a TOTP code (from authenticator app) or a recovery code.

    Args:
        request: MFAVerifyRequest with username and TOTP or recovery code
        http_request: HTTP request for IP and User-Agent
        db: Database connection

    Returns:
        AuthResponse with tokens if MFA verified successfully

    Raises:
        HTTPException: If MFA code invalid or user not found
    """
    try:
        # Verify that both totp_code and recovery_code are not both provided
        if request.totp_code and request.recovery_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either TOTP code or recovery code, not both",
            )

        # Verify that at least one is provided
        if not request.totp_code and not request.recovery_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP code or recovery code required",
            )

        # Load user
        user = db.load_user(request.username)
        if user is None:
            logger.warning(f"MFA verification for non-existent user: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or access code",
            )

        # Verify MFA code
        mfa_result = mfa_manager.verify_mfa(
            request.username,
            totp_code=request.totp_code,
            recovery_code=request.recovery_code,
        )

        if not mfa_result.is_valid:
            logger.warning(f"MFA verification failed for user: {request.username}: {mfa_result.error}")
            # Record failed MFA attempt (REQUIRED)
            lockout_manager.check_and_lock(request.username, "api")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mfa_result.error or "Invalid MFA code",
            )

        logger.info(f"MFA verification successful for user: {request.username}")

        # Extract client IP and User-Agent for token fingerprinting
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")

        # Create tokens with fingerprinting
        access_token = create_access_token(
            request.username,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        refresh_token = create_refresh_token(request.username)

        # Store refresh token in database
        _store_refresh_token(db, request.username, refresh_token)

        # Check if user has API key configured
        api_key_configured = True
        api_key_message = None
        try:
            stored_api_key = db.get_api_key(request.username, "claude")
            if not stored_api_key:
                api_key_configured = False
                api_key_message = (
                    "No API key configured. "
                    "Please save your API key in Settings > LLM > Anthropic to use AI features."
                )
        except Exception as e:
            logger.warning(f"Error checking API key for user {request.username}: {e}")

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
        logger.error(f"Error during MFA verification for user {request.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying MFA",
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

        # Check if new password has been breached (REQUIRED security check)
        is_breached, breach_count = await check_password_breach(request.new_password)
        if is_breached:
            logger.warning(
                f"Password change blocked for {current_user}: password found in {breach_count} breaches"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password has been found in known data breaches. Please use a different password.",
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


# ============================================================================
# Multi-Factor Authentication (MFA) Endpoints
# ============================================================================


@router.post(
    "/mfa/enable",
    response_model=MFASetupResponse,
    status_code=status.HTTP_200_OK,
    summary="Initialize MFA setup",
    responses={
        200: {"description": "MFA setup initialized successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        503: {"description": "MFA not available", "model": ErrorResponse},
    },
)
async def mfa_enable(
    current_user: str = Depends(get_current_user),
):
    """
    Initialize MFA setup for the current user.

    Generates a TOTP secret, QR code for authenticator app, and backup recovery codes.
    User must verify the TOTP code before MFA is fully enabled.

    Args:
        current_user: Current authenticated user (from JWT)

    Returns:
        MFASetupResponse with secret, QR code URI, and backup codes

    Raises:
        HTTPException: If MFA not available
    """
    try:
        # Generate TOTP secret and backup codes (MFA is REQUIRED)
        mfa_setup = mfa_manager.generate_secret(current_user)

        logger.info(f"MFA setup initialized for user: {current_user}")

        return MFASetupResponse(
            secret=mfa_setup.secret,
            qr_code_uri=mfa_setup.qr_code_uri,
            backup_codes=mfa_setup.backup_codes,
            recovery_codes_display=mfa_setup.recovery_codes_display,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing MFA setup for user {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error initializing MFA",
        )


@router.post(
    "/mfa/verify-enable",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify TOTP and enable MFA",
    responses={
        200: {"description": "MFA enabled successfully"},
        400: {"description": "Invalid TOTP code", "model": ErrorResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        503: {"description": "MFA not available", "model": ErrorResponse},
    },
)
async def mfa_verify_enable(
    request: MFAVerifyEnableRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Verify TOTP code and enable MFA for the current user.

    User must provide the 6-digit code from their authenticator app to complete setup.

    Args:
        request: MFAVerifyEnableRequest with TOTP code
        current_user: Current authenticated user (from JWT)

    Returns:
        APIResponse confirming MFA enabled

    Raises:
        HTTPException: If TOTP code invalid or MFA not available
    """
    try:
        # Verify TOTP code and enable MFA (REQUIRED)
        success, message = mfa_manager.enable_mfa(
            current_user,
            mfa_manager.get_totp_secret(current_user),
            request.totp_code,
        )

        if not success:
            logger.warning(f"MFA verification failed for user {current_user}: {message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            )

        # Log the MFA enablement event (REQUIRED)
        logger.info(f"MFA enabled successfully for user: {current_user}")

        return APIResponse(
            success=True,
            status="success",
            message="MFA enabled successfully. Keep your backup codes safe!",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying MFA for user {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error enabling MFA",
        )


@router.post(
    "/mfa/disable",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Disable MFA",
    responses={
        200: {"description": "MFA disabled successfully"},
        401: {"description": "Invalid password or not authenticated", "model": ErrorResponse},
        503: {"description": "MFA not available", "model": ErrorResponse},
    },
)
async def mfa_disable(
    request: MFADisableRequest,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Disable MFA for the current user.

    Requires password verification for security. User will need to re-enable MFA
    to use it again.

    Args:
        request: MFADisableRequest with user password
        current_user: Current authenticated user (from JWT)
        db: Database connection

    Returns:
        APIResponse confirming MFA disabled

    Raises:
        HTTPException: If password invalid or MFA not available
    """
    try:
        # Load user and verify password
        user = db.load_user(current_user)
        if user is None or not verify_password(request.password, user.passcode_hash):
            logger.warning(f"MFA disable attempt with invalid password for user {current_user}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password",
            )

        # Disable MFA
        mfa_manager.disable_mfa(current_user)

        logger.info(f"MFA disabled for user: {current_user}")

        return APIResponse(
            success=True,
            status="success",
            message="MFA disabled successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling MFA for user {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error disabling MFA",
        )


@router.get(
    "/mfa/status",
    response_model=MFAStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check MFA status",
    responses={
        200: {"description": "MFA status retrieved"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
    },
)
async def mfa_status(
    current_user: str = Depends(get_current_user),
):
    """
    Check if MFA is enabled for the current user.

    Args:
        current_user: Current authenticated user (from JWT)

    Returns:
        MFAStatusResponse with MFA enabled status

    Raises:
        HTTPException: If not authenticated
    """
    try:
        # Check MFA status (MFA is REQUIRED)
        mfa_enabled = mfa_manager.is_mfa_enabled(current_user)

        return MFAStatusResponse(
            mfa_enabled=mfa_enabled,
            mfa_methods=["totp"] if mfa_enabled else [],
        )

    except Exception as e:
        logger.error(f"Error checking MFA status for user {current_user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking MFA status",
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


@router.get(
    "/audit-logs",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get audit logs",
    responses={
        200: {"description": "Audit logs retrieved successfully"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        403: {"description": "Forbidden - user cannot view audit logs", "model": ErrorResponse},
    },
)
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    user: dict = Depends(get_current_user),
):
    """
    Get audit logs for the authenticated user.

    Returns a list of audit log entries for the user's account,
    useful for security monitoring and compliance.

    Query Parameters:
    - limit: Maximum number of logs to return (default: 100, max: 1000)

    Returns:
        Dictionary with audit logs
    """
    try:
        from socrates_api.middleware.audit import get_audit_logger

        audit_logger = get_audit_logger()
        if not audit_logger:
            logger.warning("Audit logger not available")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Audit logging is not available",
            )

        username = user.get("sub") or user.get("username")
        logs = audit_logger.get_logs(user_id=username, limit=limit)

        return {
            "status": "success",
            "user": username,
            "count": len(logs),
            "logs": logs,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit logs for user {user}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving audit logs",
        )
