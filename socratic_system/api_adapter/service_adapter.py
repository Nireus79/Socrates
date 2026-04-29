"""
Service adapter for exposing services via API.

Maps HTTP requests to service method calls with validation and error handling.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from inspect import iscoroutinefunction

from .base_adapter import BaseAdapter, AdapterError, AdapterValidationError
from .service_registry import ServiceRegistry, get_service_registry


class ServiceAdapter(BaseAdapter):
    """
    Adapter for exposing services via HTTP.

    Handles:
    - Service method discovery
    - Request validation
    - Async/sync method invocation
    - Response transformation
    """

    def __init__(
        self,
        service_registry: Optional[ServiceRegistry] = None,
        version: str = "v1",
    ):
        """
        Initialize service adapter.

        Args:
            service_registry: ServiceRegistry instance (uses global if None)
            version: API version
        """
        super().__init__("service_adapter", version)
        self.registry = service_registry or get_service_registry()

    def validate_service_exists(self, service_name: str) -> bool:
        """
        Validate that service exists.

        Args:
            service_name: Service name

        Returns:
            True if exists

        Raises:
            AdapterValidationError: If service not found
        """
        if not self.registry.service_exists(service_name):
            available = self.registry.list_services()
            raise AdapterValidationError(
                f"Service '{service_name}' not found",
                {
                    "service": service_name,
                    "available_services": available,
                },
            )
        return True

    def validate_method_exists(
        self,
        service_name: str,
        method_name: str,
    ) -> bool:
        """
        Validate that method exists in service.

        Args:
            service_name: Service name
            method_name: Method name

        Returns:
            True if exists

        Raises:
            AdapterValidationError: If method not found
        """
        if not self.registry.method_exists(service_name, method_name):
            service_info = self.registry.get_service_info(service_name)
            available_methods = service_info.get("methods", []) if service_info else []
            raise AdapterValidationError(
                f"Method '{method_name}' not found in service '{service_name}'",
                {
                    "service": service_name,
                    "method": method_name,
                    "available_methods": available_methods,
                },
            )
        return True

    async def call_service_method(
        self,
        service_name: str,
        method_name: str,
        params: Dict[str, Any],
    ) -> Any:
        """
        Call service method.

        Args:
            service_name: Service name
            method_name: Method name
            params: Method parameters

        Returns:
            Method result

        Raises:
            AdapterError: If method call fails
        """
        self.logger.debug(
            f"Calling {service_name}.{method_name} with params: {list(params.keys())}"
        )

        method = self.registry.get_method(service_name, method_name)
        if not method:
            raise AdapterError(f"Method '{method_name}' not callable")

        try:
            # Check if method is async
            if iscoroutinefunction(method):
                result = await method(**params)
            else:
                # Run sync method in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: method(**params),
                )

            self.logger.debug(
                f"Successfully called {service_name}.{method_name}"
            )
            return result

        except TypeError as e:
            self.logger.error(
                f"Invalid parameters for {service_name}.{method_name}: {str(e)}"
            )
            raise AdapterValidationError(
                f"Invalid parameters: {str(e)}",
                {"method": method_name, "error": str(e)},
            )
        except Exception as e:
            self.logger.error(
                f"Error calling {service_name}.{method_name}: {str(e)}"
            )
            raise AdapterError(
                f"Service method failed: {str(e)}",
                error_code="SERVICE_CALL_FAILED",
            )

    async def handle_request(
        self,
        request_data: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Handle service request.

        Args:
            request_data: Request data with 'service', 'method', 'params'
            **kwargs: Additional arguments (user_id, etc.)

        Returns:
            Response data

        Raises:
            AdapterValidationError: If validation fails
            AdapterError: If service call fails
        """
        # Validate required fields
        self.validate_request(
            request_data,
            required_fields=["service", "method"],
        )

        service_name = request_data["service"]
        method_name = request_data["method"]
        params = request_data.get("params", {})

        # Validate service exists
        self.validate_service_exists(service_name)

        # Validate method exists
        self.validate_method_exists(service_name, method_name)

        # Call service method
        result = await self.call_service_method(
            service_name,
            method_name,
            params,
        )

        return self.transform_response(
            result,
            message=f"Successfully called {service_name}.{method_name}",
        )

    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get service registry information.

        Returns:
            Registry information
        """
        return self.registry.get_registry_info()

    def get_service_info(self, service_name: str) -> Dict[str, Any]:
        """
        Get service information.

        Args:
            service_name: Service name

        Returns:
            Service information

        Raises:
            AdapterValidationError: If service not found
        """
        if not self.registry.service_exists(service_name):
            raise AdapterValidationError(
                f"Service '{service_name}' not found",
                {"available_services": self.registry.list_services()},
            )

        return self.registry.get_service_info(service_name)

    def get_method_info(
        self,
        service_name: str,
        method_name: str,
    ) -> Dict[str, Any]:
        """
        Get method information.

        Args:
            service_name: Service name
            method_name: Method name

        Returns:
            Method information

        Raises:
            AdapterValidationError: If service or method not found
        """
        if not self.registry.service_exists(service_name):
            raise AdapterValidationError(
                f"Service '{service_name}' not found"
            )

        if not self.registry.method_exists(service_name, method_name):
            raise AdapterValidationError(
                f"Method '{method_name}' not found in service '{service_name}'"
            )

        return self.registry.get_method_info(service_name, method_name)
