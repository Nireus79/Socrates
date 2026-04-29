"""
Base Service class - Foundation for all services without orchestrator dependency.

Services encapsulate business logic and are injected with their dependencies,
enabling testability, reusability, and loose coupling.
"""

import logging
from typing import Optional

from socratic_system.config import SocratesConfig


class Service:
    """
    Base class for all services.

    Provides common functionality:
    - Configuration access
    - Logging
    - No orchestrator dependency

    All services should inherit from this class and accept their
    dependencies via dependency injection.
    """

    def __init__(self, config: SocratesConfig):
        """
        Initialize base service.

        Args:
            config: SocratesConfig instance for configuration access
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(message, **kwargs)

    def log_info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.logger.info(message, **kwargs)

    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(message, **kwargs)

    def log_error(self, message: str, **kwargs) -> None:
        """Log error message"""
        self.logger.error(message, **kwargs)
