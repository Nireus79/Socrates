"""
Service registry for service discovery and management.

Maintains information about available services and their methods.
"""

import logging
import inspect
from typing import Any, Dict, List, Optional, Callable


class ServiceInfo:
    """Information about a service"""

    def __init__(
        self,
        name: str,
        service_instance: Any,
        version: str = "v1",
        description: Optional[str] = None,
    ):
        """
        Initialize service info.

        Args:
            name: Service name
            service_instance: Service instance
            version: Service version
            description: Service description
        """
        self.name = name
        self.service_instance = service_instance
        self.version = version
        self.description = description or service_instance.__class__.__doc__
        self.methods = self._discover_methods()

    def _discover_methods(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover available methods in service.

        Returns:
            Dictionary mapping method names to signatures
        """
        methods = {}

        for method_name in dir(self.service_instance):
            # Skip private/magic methods
            if method_name.startswith("_"):
                continue

            try:
                method = getattr(self.service_instance, method_name)

                # Only include callable methods
                if not callable(method):
                    continue

                # Get method signature
                sig = inspect.signature(method)
                params = {}

                for param_name, param in sig.parameters.items():
                    if param_name in ("self", "cls"):
                        continue

                    params[param_name] = {
                        "type": (
                            param.annotation.__name__
                            if hasattr(param.annotation, "__name__")
                            else str(param.annotation)
                        ),
                        "required": param.default == inspect.Parameter.empty,
                        "default": (
                            param.default if param.default != inspect.Parameter.empty else None
                        ),
                    }

                methods[method_name] = {
                    "parameters": params,
                    "return_type": (
                        sig.return_annotation.__name__
                        if hasattr(sig.return_annotation, "__name__")
                        else str(sig.return_annotation)
                    ),
                    "doc": method.__doc__,
                }

            except Exception:
                # Skip methods that can't be inspected
                continue

        return methods

    def get_method(self, method_name: str) -> Optional[Callable]:
        """
        Get method by name.

        Args:
            method_name: Method name

        Returns:
            Callable method or None if not found
        """
        if method_name not in self.methods:
            return None

        return getattr(self.service_instance, method_name)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Service info dictionary
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "methods": list(self.methods.keys()),
            "method_details": self.methods,
        }


class ServiceRegistry:
    """
    Registry for managing available services.

    Maintains service information, discovery, and routing.
    """

    def __init__(self):
        """Initialize service registry"""
        self.services: Dict[str, ServiceInfo] = {}
        self.logger = logging.getLogger(__name__)

    def register(
        self,
        name: str,
        service_instance: Any,
        version: str = "v1",
        description: Optional[str] = None,
    ) -> ServiceInfo:
        """
        Register a service.

        Args:
            name: Service name
            service_instance: Service instance
            version: Service version
            description: Service description

        Returns:
            ServiceInfo instance

        Raises:
            ValueError: If service already registered
        """
        if name in self.services:
            raise ValueError(f"Service '{name}' is already registered")

        service_info = ServiceInfo(name, service_instance, version, description)
        self.services[name] = service_info

        self.logger.info(
            f"Registered service '{name}' with {len(service_info.methods)} methods"
        )

        return service_info

    def unregister(self, name: str) -> bool:
        """
        Unregister a service.

        Args:
            name: Service name

        Returns:
            True if unregistered, False if not found
        """
        if name not in self.services:
            return False

        del self.services[name]
        self.logger.info(f"Unregistered service '{name}'")
        return True

    def get_service(self, name: str) -> Optional[ServiceInfo]:
        """
        Get service information.

        Args:
            name: Service name

        Returns:
            ServiceInfo or None if not found
        """
        return self.services.get(name)

    def get_service_instance(self, name: str) -> Optional[Any]:
        """
        Get service instance.

        Args:
            name: Service name

        Returns:
            Service instance or None if not found
        """
        service_info = self.services.get(name)
        if service_info:
            return service_info.service_instance
        return None

    def service_exists(self, name: str) -> bool:
        """
        Check if service is registered.

        Args:
            name: Service name

        Returns:
            True if registered
        """
        return name in self.services

    def method_exists(self, service_name: str, method_name: str) -> bool:
        """
        Check if service has method.

        Args:
            service_name: Service name
            method_name: Method name

        Returns:
            True if method exists
        """
        service = self.get_service(service_name)
        if not service:
            return False
        return method_name in service.methods

    def get_method(
        self,
        service_name: str,
        method_name: str,
    ) -> Optional[Callable]:
        """
        Get method from service.

        Args:
            service_name: Service name
            method_name: Method name

        Returns:
            Callable method or None
        """
        service = self.get_service(service_name)
        if not service:
            return None
        return service.get_method(method_name)

    def list_services(self) -> List[str]:
        """
        List all registered services.

        Returns:
            List of service names
        """
        return list(self.services.keys())

    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get information about all registered services.

        Returns:
            Dictionary of service information
        """
        return {
            name: service_info.to_dict()
            for name, service_info in self.services.items()
        }

    def get_service_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about specific service.

        Args:
            name: Service name

        Returns:
            Service information dictionary or None
        """
        service_info = self.get_service(name)
        if not service_info:
            return None
        return service_info.to_dict()

    def get_method_info(
        self,
        service_name: str,
        method_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about service method.

        Args:
            service_name: Service name
            method_name: Method name

        Returns:
            Method information dictionary or None
        """
        service = self.get_service(service_name)
        if not service or method_name not in service.methods:
            return None

        return {
            "service": service_name,
            "method": method_name,
            **service.methods[method_name],
        }


# Global registry instance
_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """
    Get global service registry instance.

    Returns:
        ServiceRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry
