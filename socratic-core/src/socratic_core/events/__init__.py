"""Events system for Socrates core framework"""

from .emitter import EventEmitter
from .event_types import EventType

__all__ = ["EventEmitter", "EventType"]
