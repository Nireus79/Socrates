"""
Event system for Socrates - Allows decoupled communication between components
"""

from .event_types import EventType
from .event_emitter import EventEmitter

__all__ = ['EventType', 'EventEmitter']
