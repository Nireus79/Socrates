"""
Base Service class for all business logic extraction.

Phase 1: Service Layer - Extracts business logic from agents into reusable services.

All services inherit from this base class to ensure:
- Consistent initialization
- Proper logging
- Dependency management
- No hidden orchestrator coupling
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from socratic_system.config import SocratesConfig


class BaseService:
    """
    Base class for all services.

    Services encapsulate business logic extracted from agents.
    They receive only required dependencies via DI (Dependency Injection).

    Attributes:
        config: SocratesConfig instance
        logger: Logger for this service
    """

    def __init__(self, config: "SocratesConfig"):
        """
        Initialize base service.

        Args:
            config: SocratesConfig instance with settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"{self.__class__.__name__} initialized")

    def _log_operation(self, operation: str, details: dict = None):
        """
        Log a service operation.

        Args:
            operation: Operation name
            details: Additional operation details
        """
        if details:
            self.logger.debug(f"{operation}: {details}")
        else:
            self.logger.debug(operation)
