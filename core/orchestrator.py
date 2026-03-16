"""
ServiceOrchestrator - Central orchestrator for managing all services.

Responsible for:
- Starting/stopping all services
- Routing requests between services
- Managing service dependencies
- Health monitoring
"""

from typing import Dict, Any, Optional, Type
from core.base_service import BaseService
from core.event_bus import EventBus


class ServiceOrchestrator:
    """Orchestrates all services in the platform."""

    def __init__(self):
        """Initialize orchestrator."""
        self._services: Dict[str, BaseService] = {}
        self.event_bus = EventBus()

    def register_service(self, service: BaseService) -> None:
        """
        Register a service with the orchestrator.

        Args:
            service: Service instance to register
        """
        self._services[service.service_name] = service

    async def start_all_services(self) -> None:
        """Start all registered services."""
        for service_name, service in self._services.items():
            try:
                await service.start()
                print(f"✓ Started service: {service_name}")
            except Exception as e:
                print(f"✗ Failed to start {service_name}: {e}")
                raise

    async def stop_all_services(self) -> None:
        """Stop all registered services in reverse order."""
        services_list = list(reversed(self._services.items()))
        for service_name, service in services_list:
            try:
                await service.stop()
                print(f"✓ Stopped service: {service_name}")
            except Exception as e:
                print(f"✗ Failed to stop {service_name}: {e}")

    async def get_service(self, service_name: str) -> Optional[BaseService]:
        """
        Get a service by name.

        Args:
            service_name: Name of the service to retrieve

        Returns:
            Service instance or None if not found
        """
        return self._services.get(service_name)

    async def health_check_all(self) -> Dict[str, Any]:
        """
        Check health of all services.

        Returns:
            Dictionary with health status of each service
        """
        health_status = {}
        for service_name, service in self._services.items():
            try:
                health = await service.health_check()
                health_status[service_name] = {"status": "healthy", "details": health}
            except Exception as e:
                health_status[service_name] = {"status": "unhealthy", "error": str(e)}
        return health_status

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        return {
            service_name: service.get_status()
            for service_name, service in self._services.items()
        }

    def list_services(self) -> Dict[str, str]:
        """List all registered services."""
        return {
            service_name: service.__class__.__name__
            for service_name, service in self._services.items()
        }
