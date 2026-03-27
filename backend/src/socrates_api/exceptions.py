"""
Socrates API Exception Hierarchy

This module defines all custom exceptions used throughout the Socrates API.
Exceptions are organized hierarchically to allow for specific error handling.

Hierarchy:
    SocratesException (base)
    ├── NotFoundError
    │   ├── ProjectNotFoundError
    │   ├── UserNotFoundError
    │   └── ResourceNotFoundError
    ├── ValidationError
    ├── DatabaseError
    ├── AuthenticationError
    ├── SubscriptionError
    │   └── SubscriptionLimitError
    └── OperationError
        ├── ConflictError
        └── OperationFailedError
"""

from typing import Optional, Any, Dict


class SocratesException(Exception):
    """
    Base exception class for all Socrates-specific exceptions.

    All custom exceptions in the Socrates API inherit from this class,
    enabling consistent error handling and logging.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code for programmatic handling
        status_code: HTTP status code to return (default 500)
        details: Additional error details (optional)
    """

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# NotFound Errors (4xx - 404)
# ============================================================================


class NotFoundError(SocratesException):
    """Base exception for resource not found errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=404,
            details=details,
        )


class ProjectNotFoundError(NotFoundError):
    """Raised when a requested project is not found."""

    def __init__(
        self,
        project_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"Project not found: {project_id}",
            error_code="PROJECT_NOT_FOUND",
            details=details or {"project_id": project_id},
        )


class UserNotFoundError(NotFoundError):
    """Raised when a requested user is not found."""

    def __init__(
        self,
        identifier: str,  # username, email, or user_id
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"User not found: {identifier}",
            error_code="USER_NOT_FOUND",
            details=details or {"identifier": identifier},
        )


class ResourceNotFoundError(NotFoundError):
    """Raised when a general resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            error_code="RESOURCE_NOT_FOUND",
            details=details or {"resource_type": resource_type, "resource_id": resource_id},
        )


# ============================================================================
# Validation Errors (4xx - 400)
# ============================================================================


class ValidationError(SocratesException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=error_details,
        )


# ============================================================================
# Authentication Errors (4xx - 401)
# ============================================================================


class AuthenticationError(SocratesException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTHENTICATION_FAILED",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details,
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when provided credentials are invalid."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Invalid credentials provided",
            error_code="INVALID_CREDENTIALS",
            details=details,
        )


class TokenExpiredError(AuthenticationError):
    """Raised when authentication token has expired."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Authentication token has expired",
            error_code="TOKEN_EXPIRED",
            details=details,
        )


class UnauthorizedError(SocratesException):
    """Raised when user lacks required permissions."""

    def __init__(
        self,
        message: str = "Unauthorized access",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if required_permission:
            error_details["required_permission"] = required_permission

        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=403,
            details=error_details,
        )


# ============================================================================
# Subscription Errors (4xx - 402/429)
# ============================================================================


class SubscriptionError(SocratesException):
    """Base exception for subscription-related errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "SUBSCRIPTION_ERROR",
        status_code: int = 402,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
        )


class SubscriptionLimitError(SubscriptionError):
    """Raised when user hits subscription limit (e.g., project limit)."""

    def __init__(
        self,
        limit_type: str,
        current_count: int,
        limit: int,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        error_details.update({
            "limit_type": limit_type,
            "current_count": current_count,
            "limit": limit,
        })

        super().__init__(
            message=f"{limit_type} limit exceeded: {current_count}/{limit}",
            error_code="SUBSCRIPTION_LIMIT_EXCEEDED",
            status_code=429,
            details=error_details,
        )


# ============================================================================
# Database Errors (5xx - 500)
# ============================================================================


class DatabaseError(SocratesException):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=error_details,
        )


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Failed to connect to database",
            error_code="DATABASE_CONNECTION_ERROR",
            details=details,
        )


class DatabaseIntegrityError(DatabaseError):
    """Raised when database integrity constraint is violated."""

    def __init__(
        self,
        message: str,
        constraint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if constraint:
            error_details["constraint"] = constraint

        super().__init__(
            message=message,
            error_code="DATABASE_INTEGRITY_ERROR",
            details=error_details,
        )


# ============================================================================
# Operation Errors (5xx)
# ============================================================================


class OperationError(SocratesException):
    """Base exception for operation-related errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "OPERATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details,
        )


class ConflictError(OperationError):
    """Raised when operation conflicts with current state."""

    def __init__(
        self,
        message: str,
        conflict_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if conflict_type:
            error_details["conflict_type"] = conflict_type

        super().__init__(
            message=message,
            error_code="CONFLICT",
            details=error_details,
        )


class OperationFailedError(OperationError):
    """Raised when an operation fails for an unexpected reason."""

    def __init__(
        self,
        message: str,
        operation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if operation_type:
            error_details["operation_type"] = operation_type

        super().__init__(
            message=message,
            error_code="OPERATION_FAILED",
            details=error_details,
        )


# ============================================================================
# External Service Errors (5xx)
# ============================================================================


class ExternalServiceError(SocratesException):
    """Raised when an external service (e.g., LLM, API) fails."""

    def __init__(
        self,
        service_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        error_details["service_name"] = service_name

        super().__init__(
            message=f"{service_name} service error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details=error_details,
        )


class LLMError(ExternalServiceError):
    """Raised when LLM service fails."""

    def __init__(
        self,
        message: str,
        llm_model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if llm_model:
            error_details["llm_model"] = llm_model

        super().__init__(
            service_name="LLM",
            message=message,
            details=error_details,
        )
