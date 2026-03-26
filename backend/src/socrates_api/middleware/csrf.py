"""
CSRF Protection Middleware - Prevent Cross-Site Request Forgery attacks.

Implements double-submit cookie pattern:
- Generates unique tokens per session
- Stores token in secure HTTP-only cookie
- Validates token in request header or body
- Optional enforcement per endpoint
"""

import logging
import secrets
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Global CSRF configuration
csrf_config = {
    "enabled": False,  # Off by default for API mode (enable for web UI)
    "cookie_name": "csrf-token",
    "header_name": "X-CSRF-Token",
    "token_length": 32,
}


def generate_csrf_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure CSRF token.

    Args:
        length: Length of token in bytes

    Returns:
        URL-safe CSRF token
    """
    return secrets.token_urlsafe(length)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect against Cross-Site Request Forgery (CSRF) attacks.

    Uses double-submit cookie pattern:
    1. Generate unique token per session
    2. Store in secure, HTTP-only cookie
    3. Validate token in X-CSRF-Token header or _csrf form field
    4. Only validates for state-changing methods (POST, PUT, DELETE, PATCH)
    """

    def __init__(self, app, enabled: bool = False, cookie_name: str = "csrf-token"):
        """
        Initialize CSRF middleware.

        Args:
            app: FastAPI application
            enabled: Whether to enforce CSRF protection (default: False for API mode)
            cookie_name: Name of cookie to store token
        """
        super().__init__(app)
        self.enabled = enabled
        self.cookie_name = cookie_name
        self.token_length = csrf_config.get("token_length", 32)
        logger.info(f"CSRF middleware initialized (enabled={enabled})")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and handle CSRF token validation.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response with CSRF token cookie set if needed
        """
        # Get or create CSRF token
        csrf_token = request.cookies.get(self.cookie_name)
        if not csrf_token:
            csrf_token = generate_csrf_token(self.token_length)
            logger.debug(f"Generated new CSRF token for session")

        # Validate CSRF token for state-changing requests if enabled
        if self.enabled and request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Skip validation for certain paths (e.g., public APIs)
            if not self._should_skip_validation(request):
                request_token = await self._get_request_token(request)
                if not request_token or not self._validate_token(csrf_token, request_token):
                    logger.warning(
                        f"CSRF token mismatch for {request.method} {request.url.path} "
                        f"from {request.client.host if request.client else 'unknown'}"
                    )
                    return self._csrf_error_response()

        # Process request
        response = await call_next(request)

        # Add CSRF token to response cookie
        response.set_cookie(
            key=self.cookie_name,
            value=csrf_token,
            max_age=3600,  # 1 hour
            secure=True,  # HTTPS only in production
            httponly=True,  # Not accessible via JavaScript
            samesite="Strict",  # Prevent cross-site cookie sending
        )

        return response

    def _should_skip_validation(self, request: Request) -> bool:
        """
        Check if request should skip CSRF validation.

        Skip validation for:
        - Public endpoints (configurable)
        - API endpoints that require authentication

        Args:
            request: HTTP request

        Returns:
            True if validation should be skipped
        """
        # Skip for certain public paths
        skip_paths = [
            "/health",
            "/docs",
            "/openapi.json",
            "/auth/register",  # Registration allows POST without CSRF initially
            "/auth/login",  # Login allows POST without CSRF initially
        ]

        path = request.url.path
        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return True

        return False

    async def _get_request_token(self, request: Request) -> Optional[str]:
        """
        Extract CSRF token from request (header or body).

        Checks in order:
        1. X-CSRF-Token header
        2. _csrf form field (POST/PUT)
        3. csrf query parameter

        Args:
            request: HTTP request

        Returns:
            CSRF token if found, None otherwise
        """
        # Check header first (most common for AJAX)
        header_token = request.headers.get(csrf_config.get("header_name", "X-CSRF-Token"))
        if header_token:
            return header_token

        # Check form data or JSON body (for HTML forms and POST requests)
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
                    # Form data
                    form_data = await request.form()
                    return form_data.get("_csrf")
                elif request.headers.get("content-type", "").startswith("application/json"):
                    # JSON body
                    try:
                        body = await request.json()
                        return body.get("_csrf")
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"Error extracting CSRF token from body: {e}")

        # Check query parameter (fallback)
        return request.query_params.get("_csrf")

    def _validate_token(self, stored_token: str, request_token: str) -> bool:
        """
        Validate CSRF token using double-submit pattern.

        Uses constant-time comparison to prevent timing attacks.

        Args:
            stored_token: Token from cookie
            request_token: Token from request (header/body)

        Returns:
            True if tokens match, False otherwise
        """
        if not stored_token or not request_token:
            return False

        # Use constant-time comparison
        return secrets.compare_digest(stored_token, request_token)

    def _csrf_error_response(self) -> Response:
        """
        Return CSRF validation error response.

        Returns:
            403 Forbidden response with CSRF error message
        """
        return Response(
            content='{"detail": "CSRF token missing or invalid"}',
            status_code=403,
            media_type="application/json",
        )


def add_csrf_middleware(app, enabled: bool = False, cookie_name: str = "csrf-token"):
    """
    Add CSRF protection middleware to FastAPI application.

    Note: CSRF protection is typically only needed for web UI endpoints,
    not for API clients that use proper CORS and authentication.

    Args:
        app: FastAPI application
        enabled: Enable CSRF protection (default: False for API mode)
        cookie_name: Name of cookie to store token

    Example:
        ```python
        from fastapi import FastAPI
        from socrates_api.middleware.csrf import add_csrf_middleware

        app = FastAPI()
        # Enable CSRF for web UI endpoints
        add_csrf_middleware(app, enabled=True)
        ```
    """
    app.add_middleware(CSRFMiddleware, enabled=enabled, cookie_name=cookie_name)
    logger.info(f"CSRF middleware added (enabled={enabled})")


def get_csrf_token_from_request(request: Request) -> Optional[str]:
    """
    Extract CSRF token from request cookie.

    Args:
        request: HTTP request

    Returns:
        CSRF token if present, None otherwise
    """
    return request.cookies.get(csrf_config.get("cookie_name", "csrf-token"))
