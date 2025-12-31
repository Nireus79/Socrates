"""
WebSocket Message Handler - Processes and routes WebSocket messages.

Handles:
- Message type routing (chat_message, command, etc.)
- Request validation
- Agent orchestrator integration
- Error handling and logging
"""

import json
import logging
from enum import Enum
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types."""

    CHAT_MESSAGE = "chat_message"
    COMMAND = "command"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


class ResponseType(str, Enum):
    """WebSocket response types."""

    ASSISTANT_RESPONSE = "assistant_response"
    EVENT = "event"
    ERROR = "error"
    ACKNOWLEDGMENT = "acknowledgment"


@dataclass
class WebSocketMessage:
    """Parsed WebSocket message."""

    type: MessageType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


@dataclass
class WebSocketResponse:
    """WebSocket response to send to client."""

    type: ResponseType
    content: Optional[str] = None
    event_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def to_json(self) -> str:
        """Convert response to JSON string."""
        payload = {
            "type": self.type.value,
            "timestamp": None,  # Will be added by caller
        }

        if self.content is not None:
            payload["content"] = self.content

        if self.event_type is not None:
            payload["eventType"] = self.event_type

        if self.data is not None:
            payload["data"] = self.data

        if self.request_id is not None:
            payload["requestId"] = self.request_id

        if self.error_code is not None:
            payload["errorCode"] = self.error_code

        if self.error_message is not None:
            payload["errorMessage"] = self.error_message

        return json.dumps(payload)


class MessageHandler:
    """
    Processes and routes WebSocket messages.

    Supports:
    - Message parsing and validation
    - Handler registration for message types
    - Error handling
    """

    def __init__(self):
        """Initialize message handler."""
        self._handlers: Dict[MessageType, Callable] = {}
        logger.info("MessageHandler initialized")

    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable,
    ) -> None:
        """
        Register a handler for a message type.

        Args:
            message_type: Type of message to handle
            handler: Async callable to handle the message
        """
        self._handlers[message_type] = handler
        logger.debug(f"Registered handler for {message_type.value}")

    async def parse_message(self, raw_message: str) -> Optional[WebSocketMessage]:
        """
        Parse raw WebSocket message into structured format.

        Args:
            raw_message: Raw message string

        Returns:
            Parsed WebSocketMessage or None if invalid

        Raises:
            ValueError: If message format is invalid
        """
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
            raise ValueError(f"Invalid JSON: {str(e)}")

        # Validate required fields
        if "type" not in data:
            raise ValueError("Message must have 'type' field")

        if "content" not in data:
            raise ValueError("Message must have 'content' field")

        try:
            message_type = MessageType(data["type"])
        except ValueError:
            raise ValueError(f"Invalid message type: {data['type']}")

        return WebSocketMessage(
            type=message_type,
            content=data["content"],
            metadata=data.get("metadata"),
            request_id=data.get("requestId"),
        )

    async def handle_message(
        self,
        message: WebSocketMessage,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[WebSocketResponse]:
        """
        Route and handle a parsed message.

        Args:
            message: Parsed WebSocketMessage
            context: Additional context (user_id, project_id, etc.)

        Returns:
            WebSocketResponse to send to client, or None if no response
        """
        logger.debug(f"Handling message type: {message.type.value}")

        # Get handler for message type
        handler = self._handlers.get(message.type)

        if handler is None:
            logger.warning(f"No handler for message type: {message.type.value}")
            return WebSocketResponse(
                type=ResponseType.ERROR,
                error_code="UNKNOWN_MESSAGE_TYPE",
                error_message=f"No handler for message type: {message.type.value}",
                request_id=message.request_id,
            )

        try:
            # Call handler
            response = await handler(message, context)
            return response

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            return WebSocketResponse(
                type=ResponseType.ERROR,
                error_code="HANDLER_ERROR",
                error_message=str(e),
                request_id=message.request_id,
            )

    @staticmethod
    async def create_event_response(
        event_type: str,
        data: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> WebSocketResponse:
        """
        Create an event response.

        Args:
            event_type: Type of event (e.g., "QUESTION_GENERATED", "MATURITY_UPDATED")
            data: Event payload
            request_id: Optional request ID to correlate with request

        Returns:
            WebSocketResponse
        """
        return WebSocketResponse(
            type=ResponseType.EVENT,
            event_type=event_type,
            data=data,
            request_id=request_id,
        )

    @staticmethod
    async def create_assistant_response(
        content: str,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WebSocketResponse:
        """
        Create an assistant response.

        Args:
            content: Response content
            request_id: Optional request ID
            metadata: Optional response metadata

        Returns:
            WebSocketResponse
        """
        return WebSocketResponse(
            type=ResponseType.ASSISTANT_RESPONSE,
            content=content,
            request_id=request_id,
            data=metadata,
        )

    @staticmethod
    async def create_error_response(
        error_code: str,
        error_message: str,
        request_id: Optional[str] = None,
    ) -> WebSocketResponse:
        """
        Create an error response.

        Args:
            error_code: Error code identifier
            error_message: Human-readable error message
            request_id: Optional request ID

        Returns:
            WebSocketResponse
        """
        return WebSocketResponse(
            type=ResponseType.ERROR,
            error_code=error_code,
            error_message=error_message,
            request_id=request_id,
        )

    @staticmethod
    async def create_acknowledgment(request_id: str) -> WebSocketResponse:
        """
        Create an acknowledgment response.

        Args:
            request_id: Request ID being acknowledged

        Returns:
            WebSocketResponse
        """
        return WebSocketResponse(
            type=ResponseType.ACKNOWLEDGMENT,
            request_id=request_id,
        )


# Module-level singleton instance
_message_handler: Optional[MessageHandler] = None


def get_message_handler() -> MessageHandler:
    """
    Get the singleton MessageHandler instance.

    Returns:
        MessageHandler singleton
    """
    global _message_handler
    if _message_handler is None:
        _message_handler = MessageHandler()
    return _message_handler
