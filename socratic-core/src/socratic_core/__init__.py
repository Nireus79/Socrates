"""
Socratic Core Framework

Core framework components for the Socrates AI ecosystem, including:
- Configuration management
- Exception handling
- Event system
- Logging infrastructure
- Utilities and helpers
"""

__version__ = "0.1.0"

# Export configuration components
from .config import ConfigBuilder, SocratesConfig

# Export exception components
from .exceptions import (
    APIError,
    AgentError,
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    ProjectNotFoundError,
    SocratesError,
    UserNotFoundError,
    ValidationError,
)

# Export event components
from .events import EventEmitter, EventType

# Export logging components
from .logging import (
    JsonFormatter,
    LoggingConfig,
    PerformanceFilter,
    PerformanceMonitor,
    get_logging_config,
    initialize_logging,
)

# Export utility components
from .utils import (
    ProjectIDGenerator,
    TTLCache,
    UserIDGenerator,
    cached,
    deserialize_datetime,
    serialize_datetime,
)

__all__ = [
    # Version
    "__version__",
    # Configuration
    "SocratesConfig",
    "ConfigBuilder",
    # Exceptions
    "SocratesError",
    "ConfigurationError",
    "AgentError",
    "DatabaseError",
    "AuthenticationError",
    "ProjectNotFoundError",
    "UserNotFoundError",
    "ValidationError",
    "APIError",
    # Events
    "EventEmitter",
    "EventType",
    # Logging
    "LoggingConfig",
    "JsonFormatter",
    "PerformanceFilter",
    "PerformanceMonitor",
    "initialize_logging",
    "get_logging_config",
    # Utilities
    "ProjectIDGenerator",
    "UserIDGenerator",
    "TTLCache",
    "cached",
    "serialize_datetime",
    "deserialize_datetime",
]
