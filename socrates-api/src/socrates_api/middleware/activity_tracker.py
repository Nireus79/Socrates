"""
Activity Tracking Middleware - Track last API activity per user
and manage server shutdown scheduling.
"""
import time
import logging
from typing import Dict, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# In-memory activity tracking (per-user last activity timestamp)
_user_activity: Dict[str, float] = {}
_shutdown_scheduled_at: Optional[float] = None
_shutdown_delay_seconds: int = 60  # 1 minute for browser-close


class ActivityTrackerMiddleware(BaseHTTPMiddleware):
    """Track last activity timestamp per authenticated user"""

    async def dispatch(self, request: Request, call_next):
        # Update activity timestamp for authenticated users
        if request.headers.get("authorization"):
            try:
                # Extract username from JWT token
                from socrates_api.auth.jwt_handler import verify_access_token

                token = request.headers.get("authorization", "").replace("Bearer ", "")
                payload = verify_access_token(token)
                if payload and payload.get("sub"):
                    username = payload["sub"]
                    _user_activity[username] = time.time()
                    logger.debug(f"Updated activity for user: {username}")
            except Exception as e:
                # Ignore token errors, just don't track activity
                logger.debug(f"Failed to extract user from token: {e}")

        response = await call_next(request)
        return response


def get_last_activity(username: str) -> Optional[float]:
    """Get last activity timestamp for user"""
    return _user_activity.get(username)


def get_all_activity() -> Dict[str, float]:
    """Get all user activity timestamps"""
    return _user_activity.copy()


def clear_activity(username: str) -> None:
    """Clear activity for user (e.g., on logout)"""
    if username in _user_activity:
        del _user_activity[username]
        logger.info(f"Cleared activity for user: {username}")


def has_recent_activity(since_seconds: int = 300) -> bool:
    """Check if ANY user has had activity in the last N seconds"""
    if not _user_activity:
        logger.debug("No users in activity tracking")
        return False

    now = time.time()
    cutoff = now - since_seconds

    has_activity = any(
        timestamp > cutoff for timestamp in _user_activity.values()
    )

    if has_activity:
        logger.debug(f"Recent activity detected within {since_seconds} seconds")
    else:
        logger.debug(f"No activity within {since_seconds} seconds")

    return has_activity


# Shutdown scheduling functions
def schedule_shutdown(delay_seconds: int = 60) -> None:
    """Schedule server shutdown after delay"""
    global _shutdown_scheduled_at, _shutdown_delay_seconds
    _shutdown_scheduled_at = time.time()
    _shutdown_delay_seconds = delay_seconds
    logger.info(f"Shutdown scheduled in {delay_seconds} seconds")


def cancel_shutdown() -> None:
    """Cancel scheduled shutdown"""
    global _shutdown_scheduled_at
    if _shutdown_scheduled_at:
        logger.info("Shutdown cancelled")
    _shutdown_scheduled_at = None


def is_shutdown_scheduled() -> bool:
    """Check if shutdown is scheduled"""
    return _shutdown_scheduled_at is not None


def get_shutdown_time_remaining() -> Optional[int]:
    """Get seconds remaining until shutdown, or None if not scheduled"""
    if not _shutdown_scheduled_at:
        return None

    elapsed = time.time() - _shutdown_scheduled_at
    remaining = _shutdown_delay_seconds - elapsed
    return max(0, int(remaining))


def should_shutdown_now() -> bool:
    """Check if it's time to execute scheduled shutdown"""
    if not _shutdown_scheduled_at:
        return False

    elapsed = time.time() - _shutdown_scheduled_at
    return elapsed >= _shutdown_delay_seconds
