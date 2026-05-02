"""
Event system for Socrates - Allows decoupled communication between components.

Phase 3: Event-Driven Refactoring

Provides:
- EventEmitter for event-based communication
- Event handlers and async processing
- Background job queue for async operations
- Result caching for operation results
- Result polling for clients
"""

from .event_emitter import EventEmitter
from .event_types import EventType
from .handlers import (
    EventHandler,
    EventHandlerRegistry,
    AsyncEventProcessor,
)
from .job_queue import JobQueue, Job, JobStatus, JobResult
from .result_cache import ResultCache, CacheEntry
from .result_poller import ResultPoller

__all__ = [
    # Legacy
    "EventType",
    "EventEmitter",
    # Phase 3: Event handlers
    "EventHandler",
    "EventHandlerRegistry",
    "AsyncEventProcessor",
    # Phase 3: Job queue
    "JobQueue",
    "Job",
    "JobStatus",
    "JobResult",
    # Phase 3: Result caching
    "ResultCache",
    "CacheEntry",
    # Phase 3: Result polling
    "ResultPoller",
]
