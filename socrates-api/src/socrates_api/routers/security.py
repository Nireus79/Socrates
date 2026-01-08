"""
Account Security API endpoints for Socrates.

Provides password management, 2FA setup, and session management.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.models import APIResponse, ErrorResponse, SuccessResponse
from socratic_system.database import ProjectDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/security", tags=["security"])


def get_database() -> ProjectDatabase:
    """Get database instance."""
    data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
    db_path = os.path.join(data_dir, "projects.db")
    return ProjectDatabase(db_path)


@router.post(
    "/password/change",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Change user password",
    responses={
        200: {"description": "Password changed successfully"},
        400: {
            "description": "Invalid current password or weak new password",
            "model": ErrorResponse,
        },
    },
)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Change user password with current password verification.

    Args:
        current_password: Current password for verification
        new_password: New password to set
        db: Database connection

    Returns:
        SuccessResponse confirming password change
    """
    try:
        # Validate new password strength
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters",
            )

        if not any(char.isupper() for char in new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must contain at least one uppercase letter",
            )

        if not any(char.isdigit() for char in new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must contain at least one digit",
            )

        logger.info(f"Password change initiated for user {current_user}")

        # Load user from database
        user = db.load_user(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Verify current password
        if not bcrypt.checkpw(
            current_password.encode(),
            (
                user.password_hash.encode()
                if isinstance(user.password_hash, str)
                else user.password_hash
            ),
        ):
            logger.warning(f"Invalid password attempt for user {current_user}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password",
            )

        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

        # Update user password in database
        user.password_hash = hashed_password
        db.save_user(user)

        from socrates_api.routers.events import record_event

        record_event(
            "password_changed",
            {
                "user": current_user,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return APIResponse(
            success=True,
        status="success",
            message="Password changed successfully",
            data={"changed_at": datetime.utcnow().isoformat()},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}",
        )


@router.post(
    "/2fa/setup",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Setup 2FA",
    responses={
        201: {"description": "2FA setup initiated"},
        400: {"description": "2FA already enabled", "model": ErrorResponse},
    },
)
async def setup_2fa(
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Setup two-factor authentication for user account.

    Returns:
        SuccessResponse with QR code and backup codes
    """
    try:
        logger.info(f"2FA setup initiated for user {current_user}")

        # Load user to check if 2FA already enabled
        user = db.load_user(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is already enabled for this account",
            )

        # Generate TOTP secret using pyotp
        try:
            import base64
            from io import BytesIO

            import pyotp
            import qrcode
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="pyotp/qrcode not installed. Run: pip install pyotp qrcode",
            )

        # Generate TOTP secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)

        # Generate QR code for authenticator apps
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp.provisioning_uri(name="Socrates", issuer_name="Socratic System"))
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            img_bytes = BytesIO()
            img.save(img_bytes, format="PNG")
            qr_code = base64.b64encode(img_bytes.getvalue()).decode()
            qr_code_url = f"data:image/png;base64,{qr_code}"
        except Exception as e:
            logger.warning(f"Could not generate QR code: {e}")
            qr_code_url = ""

        # Generate backup codes (10 random codes)
        import secrets

        backup_codes = [secrets.token_hex(3).upper() for _ in range(10)]

        setup_data = {
            "secret": secret,
            "qr_code_url": qr_code_url,
            "backup_codes": backup_codes,
            "manual_entry_key": secret,
        }

        from socrates_api.routers.events import record_event

        record_event(
            "2fa_setup_initiated",
            {
                "user": current_user,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return APIResponse(
            success=True,
        status="success",
            message="2FA setup initiated. Scan QR code or enter manual key.",
            data=setup_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up 2FA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup 2FA: {str(e)}",
        )


@router.post(
    "/2fa/verify",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify 2FA code",
    responses={
        200: {"description": "2FA enabled"},
        400: {"description": "Invalid 2FA code", "model": ErrorResponse},
    },
)
async def verify_2fa(
    code: str,
    secret: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Verify 2FA code to complete setup.

    Args:
        code: 6-digit TOTP code
        secret: TOTP secret (from setup if verifying initial setup)
        db: Database connection

    Returns:
        SuccessResponse confirming 2FA is enabled
    """
    try:
        if not code or len(code) != 6 or not code.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA code format. Must be 6 digits.",
            )

        logger.info(f"2FA verification initiated for user {current_user}")

        # Verify TOTP code using pyotp
        try:
            import pyotp
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="pyotp not installed. Run: pip install pyotp",
            )

        if not secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP secret required for verification",
            )

        # Verify the code
        totp = pyotp.TOTP(secret)
        if not totp.verify(code):
            logger.warning(f"Invalid 2FA code attempt for user {current_user}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA code. Please try again.",
            )

        # Load user and save TOTP secret to database
        user = db.load_user(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.totp_secret = secret
        db.save_user(user)
        logger.info(f"2FA enabled for user {current_user}")

        from socrates_api.routers.events import record_event

        record_event(
            "2fa_enabled",
            {
                "user": current_user,
                "enabled_at": datetime.utcnow().isoformat(),
            },
        )

        return APIResponse(
            success=True,
        status="success",
            message="2FA enabled successfully",
            data={"enabled_at": datetime.utcnow().isoformat()},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying 2FA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify 2FA: {str(e)}",
        )


@router.post(
    "/2fa/disable",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Disable 2FA",
    responses={
        200: {"description": "2FA disabled"},
        400: {"description": "2FA not enabled", "model": ErrorResponse},
    },
)
async def disable_2fa(
    password: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Disable two-factor authentication (requires password confirmation).

    Args:
        password: User password for confirmation
        db: Database connection

    Returns:
        SuccessResponse confirming 2FA is disabled
    """
    try:
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password required to disable 2FA",
            )

        logger.info(f"2FA disable initiated for user {current_user}")

        # Load user from database
        user = db.load_user(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Verify password using bcrypt
        if not bcrypt.checkpw(
            password.encode(),
            (
                user.password_hash.encode()
                if isinstance(user.password_hash, str)
                else user.password_hash
            ),
        ):
            logger.warning(f"Invalid password attempt to disable 2FA for user {current_user}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password",
            )

        # Check if 2FA is actually enabled
        if not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled for this account",
            )

        # Remove TOTP secret from database
        user.totp_secret = None
        db.save_user(user)
        logger.info(f"2FA disabled for user {current_user}")

        from socrates_api.routers.events import record_event

        record_event(
            "2fa_disabled",
            {
                "user": current_user,
                "disabled_at": datetime.utcnow().isoformat(),
            },
        )

        return APIResponse(
            success=True,
        status="success",
            message="2FA disabled",
            data={"disabled_at": datetime.utcnow().isoformat()},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling 2FA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable 2FA: {str(e)}",
        )


@router.get(
    "/sessions",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="List active sessions",
    responses={
        200: {"description": "Sessions retrieved"},
    },
)
async def list_sessions(
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    List all active sessions for the current user.

    Returns:
        SuccessResponse with list of sessions
    """
    try:
        logger.info(f"Listing sessions for user {current_user}")

        # Query sessions from database for current user
        sessions = db.get_user_sessions(current_user)
        if sessions is None:
            sessions = []

        # Validate each session and format for response
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append(
                {
                    "id": session.get("session_id") or session.get("id"),
                    "device": session.get("device", "Unknown device"),
                    "ip_address": session.get("ip_address", "Unknown"),
                    "last_activity": session.get("last_activity", datetime.utcnow().isoformat()),
                    "created_at": session.get("created_at", datetime.utcnow().isoformat()),
                    "is_current": session.get("is_current", False),
                }
            )

        logger.info(f"Retrieved {len(formatted_sessions)} sessions for user {current_user}")

        return APIResponse(
            success=True,
        status="success",
            message="Sessions retrieved",
            data={"sessions": formatted_sessions, "total": len(formatted_sessions)},
        )

    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}",
        )


@router.delete(
    "/sessions/{session_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke session",
    responses={
        200: {"description": "Session revoked"},
        404: {"description": "Session not found", "model": ErrorResponse},
    },
)
async def revoke_session(
    session_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Revoke a specific session (sign out from that device).

    Args:
        session_id: Session ID to revoke
        db: Database connection

    Returns:
        SuccessResponse confirming session revocation
    """
    try:
        logger.info(f"Revoking session {session_id} for user {current_user}")

        # Verify session belongs to current user and delete it
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Verify session belongs to current user
        if session.get("user") != current_user:
            logger.warning(f"Unauthorized revoke attempt by {current_user} on session {session_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot revoke another user's session",
            )

        # Remove session from database
        db.delete_session(session_id)
        logger.info(f"Session {session_id} revoked for user {current_user}")

        from socrates_api.routers.events import record_event

        record_event(
            "session_revoked",
            {
                "user": current_user,
                "session_id": session_id,
                "revoked_at": datetime.utcnow().isoformat(),
            },
        )

        return APIResponse(
            success=True,
        status="success",
            message="Session revoked successfully",
            data={"session_id": session_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke session: {str(e)}",
        )


@router.post(
    "/sessions/revoke-all",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke all sessions",
    responses={
        200: {"description": "All sessions revoked"},
    },
)
async def revoke_all_sessions(
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Revoke all active sessions except current (sign out from all devices).

    Returns:
        SuccessResponse confirming all sessions are revoked
    """
    try:
        logger.info(f"Revoking all sessions for user {current_user}")

        # Get all sessions for the current user
        all_sessions = db.get_user_sessions(current_user)
        if not all_sessions:
            all_sessions = []

        # Find the current session (the one being used for this request)
        # In a real implementation, the current session ID would be extracted from the request
        # For now, we'll keep track of sessions by most recent activity
        current_session_id = None
        if all_sessions:
            # The most recently accessed session is typically the current one
            current_session_id = all_sessions[0].get("session_id") or all_sessions[0].get("id")

        # Delete all sessions except current
        revoked_count = 0
        for session in all_sessions:
            session_id = session.get("session_id") or session.get("id")
            if session_id != current_session_id:
                try:
                    db.delete_session(session_id)
                    revoked_count += 1
                except Exception as e:
                    logger.warning(f"Failed to revoke session {session_id}: {str(e)}")

        logger.info(f"Revoked {revoked_count} sessions for user {current_user}")

        from socrates_api.routers.events import record_event

        record_event(
            "all_sessions_revoked",
            {
                "user": current_user,
                "revoked_count": revoked_count,
                "revoked_at": datetime.utcnow().isoformat(),
            },
        )

        return APIResponse(
            success=True,
        status="success",
            message="All sessions revoked. You have been signed out from all other devices.",
            data={"revoked_count": revoked_count},
        )

    except Exception as e:
        logger.error(f"Error revoking all sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke sessions: {str(e)}",
        )
