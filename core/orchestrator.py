"""
ServiceOrchestrator - Central orchestrator for managing all services.

Responsible for:
- Starting/stopping all services with dependency ordering
- Routing requests between services
- Managing service dependencies
- Health monitoring
- Event-driven inter-service communication
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from core.base_service import BaseService
from core.event_bus import EventBus


class ServiceOrchestrator:
    """Orchestrates all services in the platform."""

    # Dependency map: service -> list of services it depends on
    DEPENDENCIES = {
        "foundation": [],
        "knowledge": ["foundation"],
        "learning": ["foundation"],
        "agents": ["foundation", "learning"],
        "workflow": ["foundation", "agents"],
        "analytics": ["foundation"],
    }

    # Startup order based on dependencies
    STARTUP_ORDER = [
        "foundation",
        "knowledge",
        "learning",
        "agents",
        "analytics",
        "workflow",
    ]

    def __init__(self):
        """Initialize orchestrator."""
        self._services: Dict[str, BaseService] = {}
        self.event_bus = EventBus()
        self._started_services: List[str] = []
        self.logger = logging.getLogger("socrates.orchestrator")

    def register_service(self, service: BaseService) -> None:
        """
        Register a service with the orchestrator.

        Args:
            service: Service instance to register
        """
        self._services[service.service_name] = service

        # Inject orchestrator for inter-service communication
        service.set_orchestrator(self)

        # Inject event bus into service if it has the set_event_bus method
        if hasattr(service, "set_event_bus"):
            service.set_event_bus(self.event_bus)

        self.logger.debug(f"Registered service: {service.service_name}")

    async def start_all_services(self) -> None:
        """Start all registered services in dependency order."""
        self._started_services = []
        self.logger.info("Starting all services...")

        # Start services in order
        for service_name in self.STARTUP_ORDER:
            if service_name not in self._services:
                self.logger.debug(f"Service {service_name} not registered, skipping")
                continue

            # Check dependencies are started
            deps = self.DEPENDENCIES.get(service_name, [])
            for dep in deps:
                if dep not in self._started_services:
                    self.logger.error(
                        f"Cannot start {service_name}: dependency {dep} not started"
                    )
                    raise RuntimeError(
                        f"Dependency {dep} not started for service {service_name}"
                    )

            service = self._services[service_name]
            try:
                await service.initialize()
                self._started_services.append(service_name)
                self.logger.info(f"Started service: {service_name}")
            except Exception as e:
                self.logger.error(f"Failed to start {service_name}: {e}")
                raise

        # Publish system started event
        await self.event_bus.publish("system_started", "orchestrator", {"services": self._started_services})
        self.logger.info(f"All services started: {', '.join(self._started_services)}")

    async def stop_all_services(self) -> None:
        """Stop all registered services in reverse dependency order."""
        self.logger.info("Stopping all services...")

        # Reverse the startup order for shutdown
        shutdown_order = list(reversed(self.STARTUP_ORDER))

        for service_name in shutdown_order:
            if service_name not in self._services:
                continue

            if service_name not in self._started_services:
                continue

            service = self._services[service_name]
            try:
                await service.shutdown()
                self._started_services.remove(service_name)
                self.logger.info(f"Stopped service: {service_name}")
            except Exception as e:
                self.logger.error(f"Error stopping {service_name}: {e}")

        # Publish system stopped event
        await self.event_bus.publish("system_stopped", "orchestrator", {"services": []})
        self.logger.info("All services stopped")

    async def get_service(self, service_name: str) -> Optional[BaseService]:
        """
        Get a service by name.

        Args:
            service_name: Name of the service to retrieve

        Returns:
            Service instance or None if not found
        """
        return self._services.get(service_name)

    async def call_service(
        self,
        service_name: str,
        method_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Call a method on a service through the orchestrator.

        This is the standard way services communicate with each other.

        Args:
            service_name: Name of the service to call
            method_name: Name of the method to call
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Result of the method call
        """
        service = self._services.get(service_name)
        if not service:
            raise RuntimeError(f"Service {service_name} not found")

        if service_name not in self._started_services:
            raise RuntimeError(f"Service {service_name} is not running")

        method = getattr(service, method_name, None)
        if not method:
            raise RuntimeError(f"Service {service_name} has no method {method_name}")

        self.logger.debug(f"Calling {service_name}.{method_name}")
        return await method(*args, **kwargs)

    async def health_check_all(self) -> Dict[str, Any]:
        """
        Check health of all services.

        Returns:
            Dictionary with health status of each service
        """
        health_status = {}
        system_healthy = True

        for service_name, service in self._services.items():
            try:
                health = await service.health_check()
                is_running = service_name in self._started_services
                health_status[service_name] = {
                    "status": "healthy" if is_running else "stopped",
                    "running": is_running,
                    "details": health,
                }
            except Exception as e:
                health_status[service_name] = {
                    "status": "unhealthy",
                    "running": False,
                    "error": str(e),
                }
                system_healthy = False

        return {
            "overall_status": "healthy" if system_healthy else "unhealthy",
            "services": health_status,
            "started_services": self._started_services,
        }

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        return {
            service_name: {
                "class": service.__class__.__name__,
                "running": service_name in self._started_services,
            }
            for service_name, service in self._services.items()
        }

    def list_services(self) -> Dict[str, str]:
        """List all registered services."""
        return {
            service_name: service.__class__.__name__
            for service_name, service in self._services.items()
        }

    def get_dependencies(self, service_name: str) -> List[str]:
        """Get dependencies for a service."""
        return self.DEPENDENCIES.get(service_name, [])

    async def subscribe_service_to_events(
        self, service_name: str, event_type: str, handler: Callable
    ) -> None:
        """
        Subscribe a service to an event type.

        Args:
            service_name: Name of the service subscribing
            event_type: Type of event to subscribe to
            handler: Async function to handle the event
        """
        self.event_bus.subscribe(event_type, handler)
        self.logger.debug(f"Service {service_name} subscribed to event {event_type}")
