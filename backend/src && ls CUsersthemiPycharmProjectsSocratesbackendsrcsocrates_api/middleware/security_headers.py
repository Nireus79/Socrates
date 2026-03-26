"""
Security Headers Middleware - Add protective HTTP headers to all responses.

Provides:
- X-Frame-Options: Prevent clickjacking attacks
- X-Content-Type-Options: Prevent MIME-type sniffing
- X-XSS-Protection: Enable XSS protection in browsers
- Strict-Transport-Security: Force HTTPS connections
- Content-Security-Policy: Restrict resource loading
- Referrer-Policy: Control referrer information
- Permissions-Policy: Control browser features
- Access-Control-Allow-Credentials: Explicit CORS credentials
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to HTTP responses.

    Implements OWASP security header best practices:
    https://owasp.org/www-project-secure-headers/
    """

    def __init__(self, app, environment: str = "production"):
        """
        Initialize security headers middleware.

        Args:
            app: FastAPI application instance
            environment: Environment name (development, staging, production)
        """
        super().__init__(app)
        self.environment = environment

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response with security headers added
        """
        response = await call_next(request)

        # X-Frame-Options: Prevent clickjacking
        # DENY: Prevent page from being displayed in a frame
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options: Prevent MIME-type sniffing
        # nosniff: Prevents browser from MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection: Enable XSS protection (legacy, for older browsers)
        # 1; mode=block: Enable XSS filter and block page if attack detected
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict-Transport-Security: Force HTTPS
        # max-age=31536000: 1 year in seconds
        # includeSubDomains: Apply to all subdomains
        # preload: Allow inclusion in HSTS preload list
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        else:
            # Shorter max-age for development
            response.headers["Strict-Transport-Security"] = "max-age=3600; includeSubDomains"

        # Content-Security-Policy: Restrict resource loading
        # Prevents XSS, clickjacking, and other injection attacks
        if self.environment == "production":
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # More permissive for development
            csp = (
                "default-src 'self' http: https: data: blob: 'unsafe-inline' 'unsafe-eval'; "
                "script-src 'self' http: https: 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' http: https: 'unsafe-inline'; "
                "img-src 'self' http: https: data: blob:; "
                "font-src 'self' http: https: data:; "
                "connect-src 'self' http: https: ws: wss:; "
                "frame-ancestors 'self'"
            )

        response.headers["Content-Security-Policy"] = csp

        # Referrer-Policy: Control referrer information
        # strict-no-referrer: Never send referrer information
        response.headers["Referrer-Policy"] = "strict-no-referrer"

        # Permissions-Policy (previously Feature-Policy): Control browser features
        # Disable risky features by default
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "ambient-light-sensor=(), "
            "autoplay=(), "
            "battery=(), "
            "camera=(), "
            "display-capture=(), "
            "document-domain=(), "
            "encrypted-media=(), "
            "execution-while-not-rendered=(), "
            "execution-while-out-of-viewport=(), "
            "fullscreen=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "midi=(), "
            "payment=(), "
            "picture-in-picture=(), "
            "sync-xhr=(), "
            "usb=(), "
            "vr=(), "
            "wake-lock=(), "
            "xr-spatial-tracking=()"
        )

        # Remove potentially revealing headers
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        # Add custom headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-API-Version"] = "8.0.0"

        logger.debug(
            f"Security headers added to {request.method} {request.url.path} "
            f"(environment: {self.environment})"
        )

        return response


def add_security_headers_middleware(app, environment: str = "production"):
    """
    Add security headers middleware to FastAPI application.

    Args:
        app: FastAPI application instance
        environment: Environment name (development, staging, production)

    Example:
        ```python
        from fastapi import FastAPI
        from socrates_api.middleware.security_headers import add_security_headers_middleware

        app = FastAPI()
        add_security_headers_middleware(app, environment="production")
        ```
    """
    app.add_middleware(SecurityHeadersMiddleware, environment=environment)
    logger.info(f"Security headers middleware added (environment: {environment})")
