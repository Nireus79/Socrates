"""
Custom exception classes for Socrates system
"""

from typing import Any, Dict, Optional


class SocratesError(Exception):
    """
    Base exception for all Socrates errors.

    Attributes:
        message: Error message
        error_code: Optional error code for categorization
        context: Optional context dictionary with additional details
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        """Initialize SocratesError"""
        self.message = message
        self.error_code = error_code
        self.context = context
        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation"""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
        }


class ConfigurationError(SocratesError):
    """Raised when configuration is invalid or missing"""

    pass


class AgentError(SocratesError):
    """Raised when an agent encounters an error during processing"""

    pass


class DatabaseError(SocratesError):
    """Raised when a database operation fails"""

    pass


class AuthenticationError(SocratesError):
    """Raised when user authentication fails"""

    pass


class ProjectNotFoundError(DatabaseError):
    """Raised when a project is not found in the database"""

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        """Initialize ProjectNotFoundError"""
        super().__init__(message, error_code="PROJECT_NOT_FOUND", context=context)


class UserNotFoundError(DatabaseError):
    """Raised when a user is not found in the database"""

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        """Initialize UserNotFoundError"""
        super().__init__(message, error_code="USER_NOT_FOUND", context=context)


class ValidationError(SocratesError):
    """Raised when input validation fails"""

    pass


class APIError(SocratesError):
    """Raised when an API call fails (Claude API, external APIs, etc.)"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_type: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        """Initialize APIError"""
        if context is None:
            context = {}
        if status_code:
            context["status_code"] = status_code
        if error_type:
            context["error_type"] = error_type

        super().__init__(message, error_code="API_ERROR", context=context)
