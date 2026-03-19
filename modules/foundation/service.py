"""
FoundationService - Core infrastructure services.

Includes:
- LLM service (Claude client wrapper)
- Database service (project and vector database)
- Connection pooling
- Caching
- Event bus support
"""

import logging
from typing import Any, Dict, Optional
from core.base_service import BaseService
from core.event_bus import EventBus


class FoundationService(BaseService):
    """Service for core infrastructure (LLM, database, cache)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize foundation service."""
        super().__init__("foundation", config)
        self.llm_service: Any = None
        self.database_service: Any = None
        self.cache_service: Dict[str, Any] = {}
        self.event_bus: Optional[EventBus] = None
        self.logger = logging.getLogger(f"socrates.{self.service_name}")

    async def initialize(self) -> None:
        """Initialize the foundation service."""
        try:
            # Import and initialize LLM service
            from modules.foundation.llm_service import ClaudeClient
            self.llm_service = ClaudeClient()
            self.logger.info("LLM service initialized")

            # Import and initialize database service
            from modules.foundation.database_service import ProjectDatabase
            self.database_service = ProjectDatabase()
            self.logger.info("Database service initialized")

            # Initialize simple cache (can be upgraded to Redis)
            self.cache_service = {}
            self.logger.info("Cache service initialized")

            self.logger.info("Foundation service fully initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize foundation service: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the foundation service."""
        try:
            # Cleanup database connections
            if hasattr(self.database_service, 'close'):
                self.database_service.close()
            self.logger.info("Database service closed")

            # Clear cache
            if self.cache_service:
                self.cache_service.clear()
            self.logger.info("Cache service cleared")

            self.logger.info("Foundation service shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during foundation shutdown: {e}")

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus for publishing events."""
        self.event_bus = event_bus
        self.logger.debug("Event bus set for foundation service")

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        health = {
            "llm_service": "healthy" if self.llm_service else "unavailable",
            "database_service": "healthy" if self.database_service else "unavailable",
            "cache_service": "healthy" if self.cache_service is not None else "unavailable",
        }

        try:
            # Quick health check on database
            if self.database_service and hasattr(self.database_service, 'health_check'):
                db_health = self.database_service.health_check()
                health["database_detail"] = db_health
        except Exception as e:
            health["database_error"] = str(e)

        return health

    async def get_llm_service(self) -> Any:
        """Get the LLM service."""
        if not self.llm_service:
            raise RuntimeError("LLM service not initialized")
        return self.llm_service

    async def get_database_service(self) -> Any:
        """Get the database service."""
        if not self.database_service:
            raise RuntimeError("Database service not initialized")
        return self.database_service

    async def get_cache_service(self) -> Dict[str, Any]:
        """Get the cache service."""
        if self.cache_service is None:
            raise RuntimeError("Cache service not initialized")
        return self.cache_service

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self.cache_service.get(key)

    async def cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        self.cache_service[key] = value

    async def cache_delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self.cache_service:
            del self.cache_service[key]

    async def cache_clear(self) -> None:
        """Clear entire cache."""
        self.cache_service.clear()
