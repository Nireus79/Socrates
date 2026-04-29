"""
Simple CORS middleware that explicitly adds CORS headers to all responses.
Works around issues with Starlette's CORSMiddleware and BaseHTTPMiddleware interactions.
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class SimpleCORSMiddleware(BaseHTTPMiddleware):
    """
    Simple CORS middleware that adds CORS headers to all responses.

    This is a workaround for compatibility issues between Starlette's CORSMiddleware
    and custom BaseHTTPMiddleware classes.
    """

    def __init__(self, app, allowed_origins: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.allow_credentials = "*" not in self.allowed_origins

    async def dispatch(self, request: Request, call_next) -> Response:
        # Handle OPTIONS requests (preflight)
        if request.method == "OPTIONS":
            logger.info(f"[CORS] OPTIONS preflight request from origin: {request.headers.get('origin')}")
            return self.get_cors_response()

        # Get the response
        response = await call_next(request)

        # Add CORS headers
        origin = request.headers.get("origin")
        logger.info(f"[CORS] Request from origin: {origin}, Path: {request.url.path}")
        logger.info(f"[CORS] Allowed origins: {self.allowed_origins}")

        if origin:
            if "*" in self.allowed_origins or origin in self.allowed_origins:
                logger.info(f"[CORS] Origin {origin} is allowed, adding CORS headers")
                response.headers["Access-Control-Allow-Origin"] = origin if self.allow_credentials else "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, X-Testing-Mode"
                response.headers["Access-Control-Expose-Headers"] = "X-Process-Time, X-Request-ID, X-RateLimit-Limit, X-RateLimit-Remaining"
                if self.allow_credentials:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Max-Age"] = "3600"
            else:
                logger.warning(f"[CORS] Origin {origin} NOT in allowed list: {self.allowed_origins}")
        else:
            logger.info("[CORS] No origin header in request")

        return response

    def get_cors_response(self) -> Response:
        """Create a CORS preflight response"""
        response = Response()
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, X-Testing-Mode"
        response.headers["Access-Control-Expose-Headers"] = "X-Process-Time, X-Request-ID, X-RateLimit-Limit, X-RateLimit-Remaining"
        response.headers["Access-Control-Max-Age"] = "3600"
        return response
