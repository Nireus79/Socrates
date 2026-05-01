"""Base service class for all services.

Services encapsulate business logic and receive only required dependencies.
No direct orchestrator dependency - enabling testability and library export.
"""

import logging
from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from socratic_system.config import SocratesConfig


class Service(ABC):
    """Base class for all services.

    Services:
    - Encapsulate business logic
    - Receive dependencies via DI (no orchestrator coupling)
    - Are easily testable (mock dependencies)
    - Can be exported as library components
    """

    def __init__(self, config: "SocratesConfig"):
        """Initialize base service.

        Args:
            config: Socrates configuration
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}()"
