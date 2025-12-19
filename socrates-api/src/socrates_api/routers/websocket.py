"""
WebSocket Router - Real-time chat and event streaming endpoints.

Provides:
- WebSocket endpoint for chat and event streaming
- HTTP fallback endpoints for WebSocket-incompatible clients
- Message routing and orchestrator integration
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status

from socratic_system.database import ProjectDatabaseV2

from socrates_api.auth import get_current_user
from socrates_api.websocket import (
    get_connection_manager,
    get_message_handler,
    get_event_bridge,
    MessageType,
    ResponseType,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["websocket"])


def get_database() -> ProjectDatabaseV2:
    """Get database instance."""
    global _database
    if _database is None:
        data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
        db_path = os.path.join(data_dir, "projects.db")
        _database = ProjectDatabaseV2(db_path)
    return _database


_database = None


@router.websocket("/ws/chat/{project_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    project_id: str,
    token: str = None,
):
    """
    WebSocket endpoint for real-time chat and events.

    Clients connect with:
    - URL: /ws/chat/{project_id}
    - Query param: token={jwt_token}

    Send messages with format:
    {
        "type": "chat_message" | "command",
        "content": "message text",
        "metadata": {"mode": "socratic|direct", "requestHint": true/false}
    }

    Receive events with format:
    {
        "type": "assistant_response" | "event" | "error",
        "content": "...",
        "eventType": "QUESTION_GENERATED",
        "data": {...},
        "timestamp": "ISO8601"
    }

    Args:
        websocket: FastAPI WebSocket connection
        project_id: Project identifier
        token: JWT token for authentication
    """
    connection_id = str(uuid.uuid4())
    connection_manager = get_connection_manager()
    message_handler = get_message_handler()
    db = get_database()

    try:
        # Verify user (token would be extracted from query params in real implementation)
        # For now, we'll accept the connection and verify inside
        user_id = None  # Would be extracted from token

        # Accept connection
        try:
            await connection_manager.connect(
                websocket,
                user_id or "anonymous",
                project_id,
                connection_id,
            )
        except RuntimeError as e:
            await websocket.close(code=1008, reason=str(e))
            return

        logger.info(f"WebSocket connected: {connection_id} for project {project_id}")

        # Send welcome message
        await websocket.send_json(
            {
                "type": "acknowledgment",
                "message": "Connected to chat",
                "connectionId": connection_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Message processing loop
        while True:
            # Receive message from client
            raw_message = await websocket.receive_text()

            try:
                # Parse message
                message = await message_handler.parse_message(raw_message)

                # Handle ping/pong
                if message.type == MessageType.PING:
                    pong_response = {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    await websocket.send_json(pong_response)
                    continue

                # Route message based on type
                if message.type == MessageType.CHAT_MESSAGE:
                    # Process chat message with orchestrator
                    response = await _handle_chat_message(
                        message,
                        user_id or "anonymous",
                        project_id,
                        connection_id,
                    )

                    if response:
                        await websocket.send_text(response.to_json())

                elif message.type == MessageType.COMMAND:
                    # Process command
                    response = await _handle_command(
                        message,
                        user_id or "anonymous",
                        project_id,
                        connection_id,
                    )

                    if response:
                        await websocket.send_text(response.to_json())

                else:
                    # Unknown message type
                    error_response = {
                        "type": "error",
                        "errorCode": "UNKNOWN_MESSAGE_TYPE",
                        "errorMessage": f"Unknown message type: {message.type}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    await websocket.send_json(error_response)

            except ValueError as e:
                # Invalid message format
                error_response = {
                    "type": "error",
                    "errorCode": "INVALID_MESSAGE",
                    "errorMessage": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await websocket.send_json(error_response)

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                error_response = {
                    "type": "error",
                    "errorCode": "PROCESSING_ERROR",
                    "errorMessage": "Error processing message",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await websocket.send_json(error_response)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        await connection_manager.disconnect(connection_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Server error")
        except Exception:
            pass
        finally:
            await connection_manager.disconnect(connection_id)


async def _handle_chat_message(
    message,
    user_id: str,
    project_id: str,
    connection_id: str,
):
    """
    Handle a chat message.

    Args:
        message: Parsed WebSocketMessage
        user_id: User identifier
        project_id: Project identifier
        connection_id: Connection identifier

    Returns:
        WebSocketResponse or None
    """
    try:
        # Extract metadata
        metadata = message.metadata or {}
        mode = metadata.get("mode", "socratic")
        request_hint = metadata.get("requestHint", False)

        logger.info(
            f"Chat message from {user_id} in project {project_id}: "
            f"{message.content[:50]}... (mode={mode})"
        )

        # TODO: Integrate with orchestrator to process message
        # For now, just echo back the message

        response = {
            "type": ResponseType.ASSISTANT_RESPONSE.value,
            "content": f"Echo: {message.content}",
            "requestId": message.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return None  # Response handled via broadcast

    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        raise


async def _handle_command(
    message,
    user_id: str,
    project_id: str,
    connection_id: str,
):
    """
    Handle a command message.

    Args:
        message: Parsed WebSocketMessage
        user_id: User identifier
        project_id: Project identifier
        connection_id: Connection identifier

    Returns:
        WebSocketResponse or None
    """
    try:
        logger.info(f"Command from {user_id}: {message.content}")

        # TODO: Route to appropriate command handler

        response = {
            "type": ResponseType.ACKNOWLEDGMENT.value,
            "requestId": message.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return None  # Response handled inline

    except Exception as e:
        logger.error(f"Error handling command: {e}")
        raise


# ============================================================================
# Chat API Endpoints (HTTP Fallback for WebSocket)
# ============================================================================


@router.post(
    "/projects/{project_id}/chat/message",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Send chat message (HTTP fallback)",
)
async def send_chat_message(
    project_id: str,
    message: str,
    mode: str = "socratic",
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Send a chat message (HTTP fallback for WebSocket).

    Args:
        project_id: Project identifier
        message: Message content
        mode: Chat mode ('socratic' or 'direct')
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Response with assistant reply and metadata
    """
    try:
        # Verify project ownership
        project = db.load_project(project_id)
        if project is None or project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # TODO: Process message with orchestrator
        # For now, return echo response

        return {
            "status": "success",
            "message": f"Echo: {message}",
            "mode": mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing message",
        )


@router.get(
    "/projects/{project_id}/chat/history",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get chat history",
)
async def get_chat_history(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get chat message history for a project.

    Args:
        project_id: Project identifier
        limit: Number of messages to return
        offset: Message offset for pagination
        current_user: Current authenticated user
        db: Database connection

    Returns:
        List of chat messages with metadata
    """
    try:
        # Verify project ownership
        project = db.load_project(project_id)
        if project is None or project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # TODO: Load conversation history from database

        return {
            "status": "success",
            "project_id": project_id,
            "messages": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving history",
        )


@router.put(
    "/projects/{project_id}/chat/mode",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Switch chat mode",
)
async def switch_chat_mode(
    project_id: str,
    mode: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Switch between Socratic and Direct chat modes.

    Args:
        project_id: Project identifier
        mode: Chat mode ('socratic' or 'direct')
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Confirmation with new mode
    """
    try:
        # Validate mode
        if mode not in ["socratic", "direct"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid mode. Must be 'socratic' or 'direct'",
            )

        # Verify project ownership
        project = db.load_project(project_id)
        if project is None or project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # TODO: Update user's chat mode preference

        return {
            "status": "success",
            "project_id": project_id,
            "mode": mode,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching chat mode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error switching mode",
        )


@router.get(
    "/projects/{project_id}/chat/hint",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Request hint",
)
async def request_hint(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Request a hint for the current question.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Hint for current question
    """
    try:
        # Verify project ownership
        project = db.load_project(project_id)
        if project is None or project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # TODO: Generate hint using orchestrator

        return {
            "status": "success",
            "hint": "This is a hint for the current question",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting hint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating hint",
        )


@router.delete(
    "/projects/{project_id}/chat/clear",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Clear chat history",
)
async def clear_chat_history(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Clear chat history for a project.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Confirmation of deletion
    """
    try:
        # Verify project ownership
        project = db.load_project(project_id)
        if project is None or project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # TODO: Delete conversation history from database

        return {
            "status": "success",
            "message": "Chat history cleared",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing history",
        )


@router.get(
    "/projects/{project_id}/chat/summary",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get conversation summary",
)
async def get_chat_summary(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Get a summary of the conversation for a project.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Summary of conversation with key insights
    """
    try:
        # Verify project ownership
        project = db.load_project(project_id)
        if project is None or project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # TODO: Generate summary using orchestrator

        return {
            "status": "success",
            "project_id": project_id,
            "summary": "Conversation summary will be generated here",
            "key_points": [],
            "insights": [],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating summary",
        )
