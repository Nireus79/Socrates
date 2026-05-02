"""
API Adapter Layer for Phase 4.

Provides:
- Standardized service exposure via HTTP
- Request/response schema validation
- Async job handling with Phase 3 infrastructure
- Service registry and discovery
- Result streaming via Server-Sent Events
"""

from .base_adapter import BaseAdapter, AdapterError, AdapterValidationError
from .schemas import (
    RequestDTO,
    ResponseDTO,
    AsyncJobRequest,
    AsyncJobResponse,
    JobStatusResponse,
)
from .service_adapter import ServiceAdapter
from .service_registry import ServiceRegistry, ServiceInfo
from .async_handler import AsyncJobHandler

__all__ = [
    # Base adapter
    "BaseAdapter",
    "AdapterError",
    "AdapterValidationError",
    # Schemas
    "RequestDTO",
    "ResponseDTO",
    "AsyncJobRequest",
    "AsyncJobResponse",
    "JobStatusResponse",
    # Service adapter
    "ServiceAdapter",
    # Service registry
    "ServiceRegistry",
    "ServiceInfo",
    # Async handling
    "AsyncJobHandler",
]
