"""
EventEmitter to WebSocket Bridge - Forwards orchestrator events to WebSocket clients.

Bridges:
- Orchestrator EventEmitter events
- WebSocket broadcast to connected clients
- Event filtering and transformation
"""

import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timezone

from socratic_system.events.event_emitter import EventType

from .connection_manager import get_connection_manager
from .message_handler import WebSocketResponse, ResponseType

logger = logging.getLogger(__name__)


class EventBridge:
    """
    Bridges orchestrator EventEmitter to WebSocket clients.

    Maps:
    - EventEmitter events (PROJECT_CREATED, CODE_GENERATED, etc.)
    - WebSocket responses sent to connected clients
    - Project-scoped event filtering
    """

    # Map EventType to WebSocket event names
    EVENT_MAPPING = {
        EventType.PROJECT_CREATED: "PROJECT_CREATED",
        EventType.PROJECT_UPDATED: "PROJECT_UPDATED",
        EventType.PROJECT_ARCHIVED: "PROJECT_ARCHIVED",
        EventType.PROJECT_RESTORED: "PROJECT_RESTORED",
        EventType.QUESTION_GENERATED: "QUESTION_GENERATED",
        EventType.RESPONSE_ANALYZED: "RESPONSE_EVALUATED",
        EventType.CODE_GENERATED: "CODE_GENERATED",
        EventType.CODE_ANALYSIS_COMPLETE: "CODE_VALIDATED",
        EventType.PHASE_MATURITY_UPDATED: "MATURITY_UPDATED",
        EventType.PHASE_ADVANCED: "PHASE_ADVANCED",
        EventType.DOCUMENT_IMPORTED: "DOCUMENT_UPLOADED",
        EventType.DOCUMENTS_INDEXED: "DOCUMENT_INDEXED",
        EventType.CONTEXT_ANALYZED: "INSIGHT_GENERATED",
        EventType.AGENT_START: "AGENT_STARTED",
        EventType.AGENT_COMPLETE: "AGENT_COMPLETED",
        EventType.AGENT_ERROR: "AGENT_ERROR",
    }

    def __init__(self):
        """Initialize event bridge."""
        self._connection_manager = get_connection_manager()
        self._event_handlers: Dict[EventType, Callable] = {}
        self._initialized = False
        logger.info("EventBridge initialized")

    async def setup_event_listeners(self, orchestrator) -> None:
        """
        Setup event listeners on orchestrator.

        Args:
            orchestrator: AgentOrchestrator instance
        """
        if self._initialized:
            logger.warning("Event listeners already setup")
            return

        try:
            # Register handler for all events
            for event_type in EventType:
                handler = self._create_event_handler(event_type)
                orchestrator.event_emitter.on(event_type, handler)
                logger.debug(f"Registered listener for {event_type.value}")

            self._initialized = True
            logger.info("Event listeners setup complete")

        except Exception as e:
            logger.error(f"Failed to setup event listeners: {e}")
            raise

    def _create_event_handler(self, event_type: EventType) -> Callable:
        """
        Create an event handler for a specific event type.

        Args:
            event_type: EventType to create handler for

        Returns:
            Async callable handler
        """

        async def handler(emitted_event_type, data):
            """Handle event from orchestrator."""
            try:
                # Get project_id from event data
                project_id = data.get("project_id")
                user_id = data.get("user_id")

                # Skip if no project_id
                if not project_id:
                    logger.debug(f"Skipping event without project_id: {event_type.value}")
                    return

                # Map to WebSocket event type
                ws_event_type = self.EVENT_MAPPING.get(event_type)
                if not ws_event_type:
                    logger.debug(f"No WebSocket mapping for {event_type.value}")
                    return

                # Create WebSocket response
                response = WebSocketResponse(
                    type=ResponseType.EVENT,
                    event_type=ws_event_type,
                    data=data,
                )

                # Add timestamp
                response_dict = {
                    "type": response.type.value,
                    "eventType": response.event_type,
                    "data": response.data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # Broadcast to project if user_id known, otherwise broadcast to all
                if user_id:
                    sent_count = await self._connection_manager.broadcast_to_project(
                        user_id,
                        project_id,
                        response_dict,
                    )
                    logger.debug(
                        f"Event {ws_event_type} broadcast to {sent_count} "
                        f"connections in project {project_id}"
                    )
                else:
                    # Broadcast to all connections globally
                    sent_count = await self._connection_manager.broadcast_to_all(response_dict)
                    logger.debug(
                        f"Event {ws_event_type} broadcast to {sent_count} global connections"
                    )

            except Exception as e:
                logger.error(f"Error handling event {event_type.value}: {e}", exc_info=True)

        return handler

    async def broadcast_message(
        self,
        user_id: str,
        project_id: str,
        message: str,
        request_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast a chat message to project connections.

        Args:
            user_id: User identifier
            project_id: Project identifier
            message: Message content
            request_id: Optional request ID for correlation

        Returns:
            Number of connections message was sent to
        """
        response = WebSocketResponse(
            type=ResponseType.ASSISTANT_RESPONSE,
            content=message,
            request_id=request_id,
        )

        response_dict = {
            "type": response.type.value,
            "content": response.content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if request_id:
            response_dict["requestId"] = request_id

        return await self._connection_manager.broadcast_to_project(
            user_id,
            project_id,
            response_dict,
        )

    async def notify_error(
        self,
        user_id: str,
        project_id: str,
        error_code: str,
        error_message: str,
        request_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast an error to project connections.

        Args:
            user_id: User identifier
            project_id: Project identifier
            error_code: Error code
            error_message: Error message
            request_id: Optional request ID

        Returns:
            Number of connections notified
        """
        response = WebSocketResponse(
            type=ResponseType.ERROR,
            error_code=error_code,
            error_message=error_message,
            request_id=request_id,
        )

        response_dict = {
            "type": response.type.value,
            "errorCode": response.error_code,
            "errorMessage": response.error_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if request_id:
            response_dict["requestId"] = request_id

        return await self._connection_manager.broadcast_to_project(
            user_id,
            project_id,
            response_dict,
        )

    async def notify_user(
        self,
        user_id: str,
        notification: Dict[str, Any],
    ) -> int:
        """
        Send a notification to all user connections.

        Args:
            user_id: User identifier
            notification: Notification payload

        Returns:
            Number of connections notified
        """
        notification_dict = {
            **notification,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return await self._connection_manager.broadcast_to_user(
            user_id,
            notification_dict,
        )


# Module-level singleton instance
_event_bridge: Optional[EventBridge] = None


def get_event_bridge() -> EventBridge:
    """
    Get the singleton EventBridge instance.

    Returns:
        EventBridge singleton
    """
    global _event_bridge
    if _event_bridge is None:
        _event_bridge = EventBridge()
    return _event_bridge
