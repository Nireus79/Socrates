"""
Event system for Socrates - Allows decoupled communication between components
"""

from .event_emitter import EventEmitter
from .event_types import EventType

__all__ = ["EventType", "EventEmitter"]
