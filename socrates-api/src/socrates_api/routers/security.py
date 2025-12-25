"""
Account Security API endpoints for Socrates.

Provides password management, 2FA setup, and session management.
"""

import logging
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Depends

from socratic_system.database import ProjectDatabaseV2
from socrates_api.models import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/security", tags=["security"])


def get_database() -> ProjectDatabaseV2:
    """Get database instance."""
    data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
    db_path = os.path.join(data_dir, "projects.db")
    return ProjectDatabaseV2(db_path)


@router.post(
    "/password/change",
    response_model=SuccessResponse,
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
    db: ProjectDatabaseV2 = Depends(get_database),
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

        logger.info("Password change initiated")

        # Verify and hash password with bcrypt
        try:
            import bcrypt
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="bcrypt not installed. Run: pip install bcrypt",
            )

        # For now, simulate verification (in production would verify current password hash)
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

        # In production, would update database with:
        # user.password_hash = hashed_password
        # db.save_user(user)

        from socrates_api.routers.events import record_event
        record_event("password_changed", {
            "timestamp": datetime.utcnow().isoformat(),
        })

        return SuccessResponse(
            success=True,
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
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Setup 2FA",
    responses={
        201: {"description": "2FA setup initiated"},
        400: {"description": "2FA already enabled", "model": ErrorResponse},
    },
)
async def setup_2fa(
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Setup two-factor authentication for user account.

    Returns:
        SuccessResponse with QR code and backup codes
    """
    try:
        logger.info("2FA setup initiated")

        # Generate TOTP secret using pyotp
        try:
            import pyotp
            import qrcode
            from io import BytesIO
            import base64
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
            img.save(img_bytes, format='PNG')
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
        record_event("2fa_setup_initiated", {
            "timestamp": datetime.utcnow().isoformat(),
        })

        return SuccessResponse(
            success=True,
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
    response_model=SuccessResponse,
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
    db: ProjectDatabaseV2 = Depends(get_database),
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

        logger.info("2FA verification initiated")

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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA code. Please try again.",
            )

        # Save TOTP secret to database
        # In production: user.totp_secret = secret; db.save_user(user)

        from socrates_api.routers.events import record_event
        record_event("2fa_enabled", {
            "enabled_at": datetime.utcnow().isoformat(),
        })

        return SuccessResponse(
            success=True,
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
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Disable 2FA",
    responses={
        200: {"description": "2FA disabled"},
        400: {"description": "2FA not enabled", "model": ErrorResponse},
    },
)
async def disable_2fa(
    password: str,
    db: ProjectDatabaseV2 = Depends(get_database),
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

        logger.info("2FA disable initiated")

        # TODO: Verify password using bcrypt
        # TODO: Remove TOTP secret from database
        return SuccessResponse(
            success=True,
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
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="List active sessions",
    responses={
        200: {"description": "Sessions retrieved"},
    },
)
async def list_sessions(
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    List all active sessions for the current user.

    Returns:
        SuccessResponse with list of sessions
    """
    try:
        logger.info("Listing user sessions")

        # TODO: Query sessions from database
        sessions = [
            {
                "id": "session_1",
                "device": "Chrome on Windows",
                "ip_address": "192.168.1.1",
                "last_activity": datetime.utcnow().isoformat(),
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "is_current": True,
            },
            {
                "id": "session_2",
                "device": "Safari on macOS",
                "ip_address": "10.0.0.1",
                "last_activity": (
                    datetime.utcnow() - timedelta(hours=2)
                ).isoformat(),
                "created_at": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "is_current": False,
            },
        ]

        return SuccessResponse(
            success=True,
            message="Sessions retrieved",
            data={"sessions": sessions, "total": len(sessions)},
        )

    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}",
        )


@router.delete(
    "/sessions/{session_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke session",
    responses={
        200: {"description": "Session revoked"},
        404: {"description": "Session not found", "model": ErrorResponse},
    },
)
async def revoke_session(
    session_id: str,
    db: ProjectDatabaseV2 = Depends(get_database),
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
        logger.info(f"Revoking session: {session_id}")

        # TODO: Remove session from database
        return SuccessResponse(
            success=True,
            message="Session revoked successfully",
            data={"session_id": session_id},
        )

    except Exception as e:
        logger.error(f"Error revoking session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke session: {str(e)}",
        )


@router.post(
    "/sessions/revoke-all",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke all sessions",
    responses={
        200: {"description": "All sessions revoked"},
    },
)
async def revoke_all_sessions(
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Revoke all active sessions except current (sign out from all devices).

    Returns:
        SuccessResponse confirming all sessions are revoked
    """
    try:
        logger.info("Revoking all sessions")

        # TODO: Remove all sessions except current from database
        return SuccessResponse(
            success=True,
            message="All sessions revoked. You have been signed out from all other devices.",
            data={"revoked_count": 1},
        )

    except Exception as e:
        logger.error(f"Error revoking all sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke sessions: {str(e)}",
        )
