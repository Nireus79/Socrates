"""
BaseService - Abstract base class for all services in the modular platform.

All services (Agents, Learning, Knowledge, Workflow, Analytics, Foundation)
inherit from BaseService to ensure consistent interface and lifecycle management.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class BaseService(ABC):
    """Abstract base class for all platform services."""

    def __init__(self, service_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize service.

        Args:
            service_name: Unique identifier for this service
            config: Service-specific configuration dictionary
        """
        self.service_name = service_name
        self.config = config or {}
        self.is_ready = False
        self.created_at = datetime.utcnow()
        self.last_health_check = None
        self.orchestrator = None  # Injected by ServiceOrchestrator

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service - called once on startup."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown service - called on application termination."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check service health.

        Returns:
            Dictionary with health status, latency, and other metrics
        """
        pass

    async def start(self) -> None:
        """Start the service."""
        await self.initialize()
        self.is_ready = True

    async def stop(self) -> None:
        """Stop the service."""
        self.is_ready = False
        await self.shutdown()

    def set_orchestrator(self, orchestrator: Any) -> None:
        """
        Set the orchestrator for inter-service communication.

        Args:
            orchestrator: ServiceOrchestrator instance
        """
        self.orchestrator = orchestrator

    def get_status(self) -> Dict[str, Any]:
        """Get current service status."""
        return {
            "service_name": self.service_name,
            "is_ready": self.is_ready,
            "created_at": self.created_at.isoformat(),
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
        }
