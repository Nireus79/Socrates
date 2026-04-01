"""
Enhanced Error Handling Service

CRITICAL FIX #7: Improves error handling with explicit error states and proper propagation.
Prevents silent failures and ensures users are informed of errors.
"""

import logging
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorSeverity(str, Enum):
    """Error severity levels"""

    CRITICAL = "critical"  # Operation completely failed
    HIGH = "high"  # Operation failed but has workaround
    MEDIUM = "medium"  # Operation degraded
    LOW = "low"  # Operation succeeded with warnings


class OperationResult:
    """
    Structured result for operations that may fail.

    CRITICAL FIX #7: Provides explicit error state instead of silent failures.
    """

    def __init__(
        self,
        success: bool = True,
        data: Optional[Any] = None,
        error: Optional[str] = None,
        error_code: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.LOW,
        warnings: Optional[list[str]] = None,
    ):
        self.success = success
        self.data = data
        self.error = error
        self.error_code = error_code
        self.severity = severity
        self.warnings = warnings or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code,
            "severity": self.severity.value,
            "warnings": self.warnings,
        }

    def add_warning(self, warning: str) -> "OperationResult":
        """Add a warning to the result"""
        self.warnings.append(warning)
        return self

    @staticmethod
    def success_result(data: Any = None, warnings: Optional[list[str]] = None) -> "OperationResult":
        """Create a successful result"""
        return OperationResult(success=True, data=data, warnings=warnings)

    @staticmethod
    def failure_result(
        error: str,
        error_code: str = "OPERATION_FAILED",
        severity: ErrorSeverity = ErrorSeverity.HIGH,
    ) -> "OperationResult":
        """Create a failure result"""
        return OperationResult(success=False, error=error, error_code=error_code, severity=severity)

    @staticmethod
    def degraded_result(
        data: Any = None,
        error: str = "",
        warnings: Optional[list[str]] = None,
    ) -> "OperationResult":
        """Create a degraded result (partial success)"""
        return OperationResult(
            success=True,
            data=data,
            error=error,
            severity=ErrorSeverity.MEDIUM,
            warnings=warnings,
        )


class ErrorHandler:
    """
    Centralized error handling for operations.

    CRITICAL FIX #7: Catches exceptions and converts them to explicit error states.
    """

    @staticmethod
    def handle_operation(
        operation_name: str,
        operation_func: Callable[[], T],
        default_return: Optional[T] = None,
        suppress_errors: bool = False,
    ) -> T | OperationResult:
        """
        Execute an operation with error handling.

        Args:
            operation_name: Name of operation for logging
            operation_func: Function to execute
            default_return: Return this if operation fails and suppress_errors=True
            suppress_errors: If True, return default_return on error; if False, raise

        Returns:
            Result of operation or OperationResult with error info
        """
        try:
            logger.debug(f"Starting operation: {operation_name}")
            result = operation_func()
            logger.debug(f"Operation succeeded: {operation_name}")
            return result
        except Exception as e:
            logger.error(f"Operation failed: {operation_name}", exc_info=True)
            if suppress_errors:
                logger.warning(f"Error suppressed for operation {operation_name}: {str(e)}")
                return default_return
            else:
                # CRITICAL FIX #7: Don't suppress - let error propagate
                raise


class OptionalOperation:
    """
    Decorator for operations that might fail but shouldn't crash.

    CRITICAL FIX #7: Automatically handles optional operations.
    """

    def __init__(self, default_value: Any = None, log_level: str = "warning"):
        self.default_value = default_value
        self.log_level = log_level

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_func = getattr(logger, self.log_level)
                log_func(f"Optional operation failed: {func.__name__}: {str(e)}")
                return self.default_value

        return wrapper


def require_success(result: OperationResult, error_message: str = "") -> Any:
    """
    CRITICAL FIX #7: Assert operation succeeded, raise if not.

    Prevents silent failures from going unnoticed.

    Args:
        result: OperationResult to check
        error_message: Additional context for error

    Returns:
        Result data if successful

    Raises:
        ValueError: If operation failed
    """
    if not result.success:
        full_message = f"{error_message}: {result.error}" if error_message else result.error
        logger.error(f"Required operation failed: {full_message}")
        raise ValueError(full_message)
    return result.data


def with_fallback(primary_func: Callable, fallback_func: Callable) -> Callable:
    """
    CRITICAL FIX #7: Create operation with automatic fallback.

    Tries primary operation, falls back to fallback if it fails.

    Args:
        primary_func: Primary operation to try
        fallback_func: Fallback operation if primary fails

    Returns:
        Callable that implements fallback logic
    """

    def wrapper(*args, **kwargs):
        try:
            logger.debug(f"Trying primary operation: {primary_func.__name__}")
            return primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(
                f"Primary operation failed, using fallback: {primary_func.__name__} -> {fallback_func.__name__}",
                exc_info=True,
            )
            try:
                return fallback_func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
                raise

    return wrapper


class ValidationError(Exception):
    """
    Raised when validation fails.

    CRITICAL FIX #7: Explicit error type for validation failures.
    """

    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"Validation error in {field}: {message}")


def validate_required(value: Any, field_name: str) -> Any:
    """Validate that a value is not None/empty"""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(field_name, "Required field cannot be empty", value)
    return value


def validate_type(value: Any, expected_type: type, field_name: str) -> Any:
    """Validate that a value is of expected type"""
    if not isinstance(value, expected_type):
        raise ValidationError(
            field_name,
            f"Expected {expected_type.__name__}, got {type(value).__name__}",
            value,
        )
    return value
