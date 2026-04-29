"""
Base adapter class for API service exposure.

Provides foundation for service adapters with validation,
error handling, and request/response transformation.
"""

import logging
from typing import Any, Dict, Optional, Type, TypeVar
from abc import ABC, abstractmethod

T = TypeVar("T")


class AdapterError(Exception):
    """Base adapter error"""

    def __init__(self, message: str, error_code: str = "ADAPTER_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class AdapterValidationError(AdapterError):
    """Request validation error"""

    def __init__(self, message: str, validation_errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.validation_errors = validation_errors or {}


class AdapterAuthorizationError(AdapterError):
    """Authorization error"""

    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class BaseAdapter(ABC):
    """
    Base adapter for service exposure.

    Provides:
    - Request validation
    - Error handling
    - Response transformation
    - Logging and tracing
    """

    def __init__(self, service_name: str, version: str = "v1"):
        """
        Initialize adapter.

        Args:
            service_name: Name of the service being adapted
            version: API version
        """
        self.service_name = service_name
        self.version = version
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    def validate_request(
        self,
        request_data: Dict[str, Any],
        required_fields: list[str],
    ) -> Dict[str, Any]:
        """
        Validate request data.

        Args:
            request_data: Request data to validate
            required_fields: List of required field names

        Returns:
            Validated request data

        Raises:
            AdapterValidationError: If validation fails
        """
        self.logger.debug(f"Validating request for {self.service_name}")

        missing_fields = []
        for field in required_fields:
            if field not in request_data or request_data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            raise AdapterValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                {"missing_fields": missing_fields},
            )

        return request_data

    def check_authorization(
        self,
        current_user: str,
        resource_owner: str,
        allow_same_user: bool = True,
    ) -> bool:
        """
        Check if user is authorized to access resource.

        Args:
            current_user: Authenticated user ID
            resource_owner: Owner of the resource
            allow_same_user: Allow access if user is owner

        Returns:
            True if authorized

        Raises:
            AdapterAuthorizationError: If not authorized
        """
        if allow_same_user and current_user == resource_owner:
            return True

        self.logger.warning(
            f"Authorization denied for user {current_user} to access resource owned by {resource_owner}"
        )
        raise AdapterAuthorizationError(f"Not authorized to access this resource")

    def transform_response(
        self,
        data: Any,
        status: str = "success",
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transform service result to API response.

        Args:
            data: Service result data
            status: Response status
            message: Optional message

        Returns:
            API response dictionary
        """
        response = {
            "status": status,
            "service": self.service_name,
            "version": self.version,
            "data": data,
        }

        if message:
            response["message"] = message

        return response

    def transform_error(
        self,
        error: Exception,
        status_code: int = 400,
    ) -> Dict[str, Any]:
        """
        Transform exception to error response.

        Args:
            error: Exception to transform
            status_code: HTTP status code

        Returns:
            Error response dictionary
        """
        error_response = {
            "status": "error",
            "service": self.service_name,
            "version": self.version,
            "error": {
                "type": error.__class__.__name__,
                "message": str(error),
            },
            "status_code": status_code,
        }

        if isinstance(error, AdapterError):
            error_response["error"]["code"] = error.error_code
            if isinstance(error, AdapterValidationError):
                error_response["error"]["validation_errors"] = error.validation_errors

        self.logger.error(
            f"Error in {self.service_name}: {error.__class__.__name__}: {str(error)}"
        )

        return error_response

    @abstractmethod
    async def handle_request(
        self,
        request_data: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Handle incoming request.

        Args:
            request_data: Request data
            **kwargs: Additional arguments

        Returns:
            Response data

        Must be implemented by subclasses.
        """
        pass

    def get_adapter_info(self) -> Dict[str, Any]:
        """
        Get adapter information.

        Returns:
            Adapter metadata
        """
        return {
            "service": self.service_name,
            "version": self.version,
            "class": self.__class__.__name__,
            "module": self.__class__.__module__,
        }
