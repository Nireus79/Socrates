"""
EventBus - Event-driven communication system for service coordination.

Services publish events and subscribe to events they care about.
Enables loose coupling between services.
"""

from typing import Callable, Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Event:
    """Represents an event published on the event bus."""

    event_type: str
    source_service: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: str(datetime.utcnow().timestamp()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "source_service": self.source_service,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
        }


class EventBus:
    """Central event bus for inter-service communication."""

    def __init__(self):
        """Initialize event bus."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Type of event to listen for (e.g., 'skill_generated')
            handler: Async callable to handle the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        Unsubscribe from events.

        Args:
            event_type: Type of event to stop listening for
            handler: Handler to remove
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)

    async def publish(
        self, event_type: str, source_service: str, data: Dict[str, Any]
    ) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event_type: Type of event
            source_service: Name of service publishing the event
            data: Event payload
        """
        event = Event(
            event_type=event_type,
            source_service=source_service,
            data=data,
        )

        # Store in history
        self._event_history.append(event)

        # Notify all subscribers
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    print(f"Error in event handler for {event_type}: {e}")

    def get_event_history(
        self, event_type: Optional[str] = None, limit: int = 100
    ) -> List[Event]:
        """
        Get event history.

        Args:
            event_type: Filter by event type (None = all)
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        events = self._event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history = []
