"""
Audit Logging Middleware - Log all API requests and security events for compliance.

Records:
- All API requests with user context
- Authentication events (login, register, logout)
- Data access and modifications
- Security events (lockout, token issues)
- Errors and exceptions

Stores audit logs in database for compliance and security analysis.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class AuditLogEntry:
    """Represents a single audit log entry"""

    def __init__(
        self,
        timestamp: datetime,
        user_id: Optional[str],
        ip_address: str,
        http_method: str,
        endpoint: str,
        path: str,
        status_code: int,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
    ):
        self.id = str(uuid.uuid4())
        self.timestamp = timestamp
        self.user_id = user_id
        self.ip_address = ip_address
        self.http_method = http_method
        self.endpoint = endpoint
        self.path = path
        self.status_code = status_code
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details = details or {}
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "http_method": self.http_method,
            "endpoint": self.endpoint,
            "path": self.path,
            "status_code": self.status_code,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": str(self.details),
            "duration_ms": self.duration_ms,
        }


class AuditLogger:
    """Manages audit logging to database"""

    def __init__(self, db=None):
        self.db = db
        self._ensure_audit_table()

    def _ensure_audit_table(self):
        """Ensure audit log table exists in database"""
        if not self.db:
            return

        try:
            # Check if table exists and create if needed
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    ip_address TEXT NOT NULL,
                    http_method TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT,
                    duration_ms REAL NOT NULL
                )
                """
            )
            self.db.conn.commit()
            logger.debug("Audit log table ensured")
        except Exception as e:
            logger.warning(f"Failed to ensure audit log table: {e}")

    def log_entry(self, entry: AuditLogEntry) -> bool:
        """Log an audit entry to database"""
        if not self.db:
            logger.debug(f"No database available, skipping audit log: {entry.action}")
            return False

        try:
            cursor = self.db.conn.cursor()
            entry_dict = entry.to_dict()
            cursor.execute(
                """
                INSERT INTO audit_log
                (id, timestamp, user_id, ip_address, http_method, endpoint, path,
                 status_code, action, resource_type, resource_id, details, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_dict["id"],
                    entry_dict["timestamp"],
                    entry_dict["user_id"],
                    entry_dict["ip_address"],
                    entry_dict["http_method"],
                    entry_dict["endpoint"],
                    entry_dict["path"],
                    entry_dict["status_code"],
                    entry_dict["action"],
                    entry_dict["resource_type"],
                    entry_dict["resource_id"],
                    entry_dict["details"],
                    entry_dict["duration_ms"],
                ),
            )
            self.db.conn.commit()
            logger.debug(f"Audit log recorded: {entry.action}")
            return True
        except Exception as e:
            logger.warning(f"Failed to log audit entry: {e}")
            return False

    def log_auth_event(
        self,
        username: str,
        ip_address: str,
        action: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log authentication event (login, register, logout, etc.)"""
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            user_id=username,
            ip_address=ip_address,
            http_method="POST",
            endpoint=f"/auth/{action}",
            path=f"/api/v1/auth/{action}",
            status_code=200 if success else 401,
            action=f"auth_{action}",
            resource_type="auth",
            resource_id=username,
            details={"success": success, **(details or {})},
        )
        return self.log_entry(entry)

    def log_api_request(
        self,
        request: Request,
        status_code: int,
        user_id: Optional[str],
        duration_ms: float,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log API request"""
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path.split("/")[-1] if request.url.path else "unknown"

        # Determine action from HTTP method
        action_map = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }
        action = action_map.get(request.method, "access")

        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            ip_address=client_ip,
            http_method=request.method,
            endpoint=endpoint,
            path=str(request.url.path),
            status_code=status_code,
            action=action,
            details=details,
            duration_ms=duration_ms,
        )
        return self.log_entry(entry)

    def get_logs(
        self, user_id: Optional[str] = None, limit: int = 100
    ) -> list[Dict[str, Any]]:
        """Retrieve audit logs, optionally filtered by user"""
        if not self.db:
            return []

        try:
            cursor = self.db.conn.cursor()
            if user_id:
                cursor.execute(
                    """
                    SELECT * FROM audit_log
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM audit_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.warning(f"Failed to retrieve audit logs: {e}")
            return []


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> Optional[AuditLogger]:
    """Get the global audit logger instance"""
    return _audit_logger


def initialize_audit_logger(db) -> None:
    """Initialize audit logger with database connection"""
    global _audit_logger
    _audit_logger = AuditLogger(db)
    logger.info("Audit logger initialized")


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests for audit trail"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """Log request and response"""
        start_time = time.time()

        # Extract user ID from JWT token if present
        user_id = None
        if request.headers.get("authorization"):
            try:
                from socrates_api.auth.jwt_handler import verify_access_token

                token = request.headers.get("authorization", "").replace("Bearer ", "")
                payload = verify_access_token(token)
                if payload and payload.get("sub"):
                    user_id = payload["sub"]
            except Exception:
                # Ignore token errors, just don't track user
                pass

        # Skip logging for some endpoints to reduce noise
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            "/.well-known",
        ]
        should_log = not any(request.url.path.startswith(p) for p in skip_paths)

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log request if enabled
            if should_log and _audit_logger:
                details = {}

                # Log sensitive events with more detail
                if "/auth/login" in request.url.path:
                    details["event"] = "login_attempt"
                elif "/auth/register" in request.url.path:
                    details["event"] = "registration_attempt"
                elif "/auth/logout" in request.url.path:
                    details["event"] = "logout"
                elif request.method in ["PUT", "DELETE", "PATCH"]:
                    details["event"] = "data_modification"

                _audit_logger.log_api_request(
                    request,
                    response.status_code,
                    user_id,
                    duration_ms,
                    details if details else None,
                )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Error in request to {request.url.path}: {e}")

            # Log the error event
            if should_log and _audit_logger:
                _audit_logger.log_api_request(
                    request,
                    500,
                    user_id,
                    duration_ms,
                    {"error": str(e)},
                )

            raise
