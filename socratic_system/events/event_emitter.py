"""
Event emitter system for Socrates - Thread-safe event publishing and subscription
"""

import logging
import threading
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime

from .event_types import EventType


class EventEmitter:
    """
    Thread-safe event emitter for Socrates system.

    Allows components to emit events and other components to subscribe to them
    without direct coupling. Events are emitted synchronously to all listeners.

    Example:
        >>> emitter = EventEmitter()
        >>>
        >>> def on_info(data):
        ...     print(f"Info: {data['message']}")
        >>>
        >>> emitter.on(EventType.LOG_INFO, on_info)
        >>> emitter.emit(EventType.LOG_INFO, {"message": "Hello"})
        Info: Hello
    """

    def __init__(self):
        """Initialize the event emitter"""
        self._listeners: Dict[EventType, List[Callable]] = {}
        self._logger = logging.getLogger("socrates.events")
        self._lock = threading.RLock()

    def on(self, event_type: EventType, callback: Callable) -> None:
        """
        Register an event listener for a specific event type.

        Args:
            event_type: The type of event to listen for
            callback: A callable that will be invoked with the event data

        Example:
            >>> def handle_code_generated(data):
            ...     print(f"Generated {len(data['code'])} chars")
            >>>
            >>> emitter.on(EventType.CODE_GENERATED, handle_code_generated)
        """
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(callback)

    def once(self, event_type: EventType, callback: Callable) -> None:
        """
        Register a one-time event listener that will be removed after first invocation.

        Args:
            event_type: The type of event to listen for
            callback: A callable that will be invoked once with the event data
        """
        def wrapper(data):
            try:
                callback(data)
            finally:
                self.remove_listener(event_type, wrapper)

        self.on(event_type, wrapper)

    def remove_listener(self, event_type: EventType, callback: Callable) -> bool:
        """
        Remove a specific listener for an event type.

        Args:
            event_type: The type of event
            callback: The callback to remove

        Returns:
            True if the listener was found and removed, False otherwise
        """
        with self._lock:
            if event_type not in self._listeners:
                return False

            try:
                self._listeners[event_type].remove(callback)
                return True
            except ValueError:
                return False

    def remove_all_listeners(self, event_type: Optional[EventType] = None) -> None:
        """
        Remove all listeners for a specific event type, or all listeners if no type specified.

        Args:
            event_type: The specific event type to clear, or None to clear all
        """
        with self._lock:
            if event_type is None:
                self._listeners.clear()
            elif event_type in self._listeners:
                self._listeners[event_type].clear()

    def emit(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        skip_logging: bool = False
    ) -> None:
        """
        Emit an event to all registered listeners.

        Args:
            event_type: The type of event to emit
            data: Optional dictionary of data to pass to listeners
            skip_logging: If True, skip logging this event (useful for high-frequency events)

        Example:
            >>> emitter.emit(
            ...     EventType.PROJECT_CREATED,
            ...     {"project_id": "123", "name": "My Project"}
            ... )
        """
        if data is None:
            data = {}

        # Add timestamp if not already present
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()

        # Log to Python logger (unless skipped)
        if not skip_logging:
            self._logger.debug(f"Event: {event_type.value} - {data}")

        # Notify all listeners
        with self._lock:
            listeners = self._listeners.get(event_type, []).copy()

        for callback in listeners:
            try:
                callback(data)
            except Exception as e:
                self._logger.error(
                    f"Error in event listener for {event_type.value}: {e}",
                    exc_info=e
                )

    def listener_count(self, event_type: Optional[EventType] = None) -> int:
        """
        Get the number of listeners for a specific event type or total.

        Args:
            event_type: The specific event type to count, or None for total count

        Returns:
            The number of listeners
        """
        with self._lock:
            if event_type is None:
                return sum(len(listeners) for listeners in self._listeners.values())
            return len(self._listeners.get(event_type, []))

    def get_event_names(self) -> List[EventType]:
        """
        Get all event types that have at least one listener.

        Returns:
            A list of EventTypes with registered listeners
        """
        with self._lock:
            return list(self._listeners.keys())

    def __repr__(self) -> str:
        """String representation of the emitter"""
        total = self.listener_count()
        event_names = len(self.get_event_names())
        return f"<EventEmitter with {total} listener(s) on {event_names} event type(s)>"
