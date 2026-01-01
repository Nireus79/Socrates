"""WebSocket management module for real-time communication."""

from .connection_manager import (
    ConnectionManager,
    ConnectionMetadata,
    get_connection_manager,
)
from .event_bridge import EventBridge, get_event_bridge
from .message_handler import (
    MessageHandler,
    MessageType,
    ResponseType,
    WebSocketMessage,
    WebSocketResponse,
    get_message_handler,
)

__all__ = [
    "ConnectionManager",
    "get_connection_manager",
    "ConnectionMetadata",
    "MessageHandler",
    "get_message_handler",
    "MessageType",
    "ResponseType",
    "WebSocketMessage",
    "WebSocketResponse",
    "EventBridge",
    "get_event_bridge",
]
