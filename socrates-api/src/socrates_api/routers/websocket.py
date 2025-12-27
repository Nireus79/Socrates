"""
WebSocket Router - Real-time chat and event streaming endpoints.

Provides:
- WebSocket endpoint for chat and event streaming
- HTTP fallback endpoints for WebSocket-incompatible clients
- Message routing and event broadcasting
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status

from socratic_system.database import ProjectDatabaseV2
from socratic_system.orchestration.orchestrator import AgentOrchestrator
from socrates_api.database import get_database
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
            logger.info(f"[WebSocket {connection_id}] Received raw message: {raw_message[:100]}")

            try:
                # Parse message
                message = await message_handler.parse_message(raw_message)
                logger.info(f"[WebSocket {connection_id}] Parsed message type: {message.type}, content: {message.content[:50] if hasattr(message, 'content') else 'N/A'}")

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
                    # Process chat message
                    response = await _handle_chat_message(
                        message,
                        user_id or "anonymous",
                        project_id,
                        connection_id,
                    )

                    if response:
                        response_text = json.dumps(response) if isinstance(response, dict) else response.to_json()
                        await websocket.send_text(response_text)

                elif message.type == MessageType.COMMAND:
                    # Process command
                    response = await _handle_command(
                        message,
                        user_id or "anonymous",
                        project_id,
                        connection_id,
                    )

                    if response:
                        response_text = json.dumps(response) if isinstance(response, dict) else response.to_json()
                        await websocket.send_text(response_text)

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
    Handle a chat message with AI processing.

    Args:
        message: Parsed WebSocketMessage
        user_id: User identifier
        project_id: Project identifier
        connection_id: Connection identifier

    Returns:
        WebSocketResponse or None
    """
    try:
        logger.info(f"[_handle_chat_message] Starting to handle chat message for project {project_id}")
        # Extract metadata
        metadata = message.metadata or {}
        mode = metadata.get("mode", "socratic")
        request_hint = metadata.get("requestHint", False)

        logger.info(
            f"[_handle_chat_message] Chat message from {user_id} in project {project_id}: "
            f"{message.content[:50]}... (mode={mode})"
        )

        # Get project and orchestrator for AI processing
        try:
            from socrates_api.main import get_orchestrator
            db = get_database()

            project = db.load_project(project_id)
            if not project:
                logger.error(f"Project {project_id} not found")
                return None

            orchestrator = get_orchestrator()
            logger.info(f"[_handle_chat_message] Got orchestrator, calling process_request")

            # Process message through orchestrator using process_request (standard pattern)
            result = orchestrator.process_request(
                "socratic_counselor",
                {
                    "action": "process_response",
                    "project": project,
                    "response": message.content,
                    "current_user": user_id,
                }
            )
            logger.info(f"[_handle_chat_message] Orchestrator result: {result.get('status')}")

            # Extract insights from response
            if result.get("status") == "success":
                insights = result.get("insights", {})
                # Format insights as a readable response
                response_parts = []
                if insights.get("goals"):
                    response_parts.append(f"Goals identified: {', '.join(insights['goals'])}")
                if insights.get("requirements"):
                    response_parts.append(f"Requirements: {', '.join(insights['requirements'])}")
                if insights.get("tech_stack"):
                    response_parts.append(f"Tech stack: {', '.join(insights['tech_stack'])}")
                if insights.get("constraints"):
                    response_parts.append(f"Constraints: {', '.join(insights['constraints'])}")

                ai_response = " | ".join(response_parts) if response_parts else "Thank you for sharing that information."

                # Handle conflicts if any
                if result.get("conflicts_pending"):
                    ai_response += "\n\nNote: There are some conflicting specifications to resolve."
            else:
                ai_response = result.get("message", "I'm processing your response.")

            # Generate hint if requested
            hint_text = ""
            if request_hint:
                try:
                    hint_text = orchestrator.claude_client.generate_suggestions(
                        f"Current question context: {message.content}",
                        project
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate hint: {e}")
                    hint_text = "Try breaking this down into smaller parts."

            # Save message to conversation history
            project.conversation_history.append({
                "id": f"msg_{len(project.conversation_history)}",
                "type": "user",
                "content": message.content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mode": mode,
            })

            # Save assistant response
            project.conversation_history.append({
                "id": f"msg_{len(project.conversation_history)}",
                "type": "assistant",
                "content": ai_response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hint": hint_text if hint_text else None,
            })

            db.save_project(project)

        except Exception as e:
            logger.error(f"Error processing chat message with AI: {e}")
            ai_response = f"I encountered an error: {str(e)}"

        response = {
            "type": ResponseType.ASSISTANT_RESPONSE.value,
            "content": ai_response,
            "requestId": message.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Return response so it gets sent to client
        return response

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
    Handle a command message with routing to appropriate handler.

    Args:
        message: Parsed WebSocketMessage
        user_id: User identifier
        project_id: Project identifier
        connection_id: Connection identifier

    Returns:
        WebSocketResponse or None
    """
    try:
        command_text = message.content.strip()
        logger.info(f"Command from {user_id}: {command_text}")

        # Extract command name and arguments
        parts = command_text.split(maxsplit=1)
        command_name = parts[0].lstrip("/").lower() if parts else ""
        command_args = parts[1] if len(parts) > 1 else ""

        # Route to appropriate command handler
        result = await _route_command(
            command_name,
            command_args,
            user_id,
            project_id
        )

        response = {
            "type": ResponseType.ASSISTANT_RESPONSE.value,
            "content": result.get("message", "Command executed"),
            "requestId": message.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Command '{command_name}' executed for {user_id}")
        return response

    except Exception as e:
        logger.error(f"Error handling command: {e}")
        return {
            "type": ResponseType.ERROR.value,
            "errorMessage": str(e),
            "requestId": message.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


async def _route_command(
    command: str,
    args: str,
    user_id: str,
    project_id: str,
) -> dict:
    """
    Route command to appropriate handler.

    Args:
        command: Command name (without /)
        args: Command arguments as string
        user_id: User ID
        project_id: Project ID

    Returns:
        Result dict with status and message
    """
    try:
        from socrates_api.main import get_orchestrator
        db = get_database()

        project = db.load_project(project_id)
        if not project:
            return {"status": "error", "message": f"Project {project_id} not found"}

        orchestrator = get_orchestrator()

        # Map common commands to handlers
        if command in ["hint", "help", "suggest"]:
            # Generate hint
            hint = orchestrator.claude_client.generate_suggestions(
                f"{command}: {args}" if args else "Help me with this task",
                project
            )
            return {"status": "success", "message": hint}

        elif command == "summary":
            # Generate conversation summary
            result = orchestrator.process_request(
                "context_analyzer",
                {
                    "action": "generate_summary",
                    "project": project,
                    "limit": 50,
                }
            )
            summary = result.get("summary", "No summary available")
            return {"status": "success", "message": summary}

        elif command == "status":
            # Show project status
            status_msg = (
                f"Project: {project.name}\n"
                f"Phase: {project.phase}\n"
                f"Maturity: {project.overall_maturity:.1f}%\n"
                f"Mode: {project.chat_mode}"
            )
            return {"status": "success", "message": status_msg}

        elif command == "mode":
            # Switch chat mode
            if args in ["socratic", "direct"]:
                project.chat_mode = args
                db.save_project(project)
                return {"status": "success", "message": f"Mode switched to {args}"}
            else:
                return {"status": "error", "message": "Mode must be 'socratic' or 'direct'"}

        elif command == "clear":
            # Clear conversation history
            count = len(project.conversation_history or [])
            project.conversation_history = []
            db.save_project(project)
            return {"status": "success", "message": f"Cleared {count} messages"}

        elif command == "advance":
            # Advance to next phase via orchestrator routing (not direct call)
            result = await orchestrator.process_request_async(
                "socratic_counselor",
                {
                    "action": "advance_phase",
                    "project": project,
                    "current_user": user_id,
                    "is_api_mode": True,
                }
            )
            if result.get("status") == "success":
                db.save_project(project)
                new_phase = result.get("new_phase", project.phase)
                return {"status": "success", "message": f"Advanced to {new_phase} phase"}
            else:
                return {"status": "error", "message": result.get("message", "Cannot advance phase")}

        else:
            return {"status": "error", "message": f"Unknown command: /{command}"}

    except Exception as e:
        logger.error(f"Error routing command '{command}': {e}")
        return {"status": "error", "message": str(e)}


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
    request_body: dict,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Send a chat message (HTTP fallback for WebSocket).

    Args:
        project_id: Project identifier
        request_body: JSON body with 'message' and 'mode'
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Response with assistant reply and metadata
    """
    try:
        logger.info(f"[send_chat_message] Starting for project {project_id}")
        # Import here to avoid circular dependency
        from socrates_api.main import get_orchestrator
        orchestrator = get_orchestrator()
        logger.info(f"[send_chat_message] Got orchestrator: {orchestrator is not None}")
        # Extract message and mode from request body
        message = request_body.get("message", "").strip()
        mode = request_body.get("mode", "socratic").lower()
        logger.info(f"[send_chat_message] Message: {message[:50]}, Mode: {mode}")

        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content is required",
            )

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

        # Store user message in conversation history
        project.conversation_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "user",
            "content": message,
            "mode": mode,
        })

        # Check if this is the first message - if so, generate initial question first
        assistant_messages = [msg for msg in project.conversation_history
                            if msg.get("type") == "assistant"]

        question_response = None
        if not assistant_messages:
            # Generate initial question via orchestrator routing (not direct call)
            try:
                question_result = await orchestrator.process_request_async(
                    "socratic_counselor",
                    {
                        "action": "generate_question",
                        "project": project,
                        "current_user": current_user,
                        "is_api_mode": True,
                    }
                )
                if question_result.get("status") == "success":
                    question_response = question_result.get("question")
                    logger.info(f"Generated initial question for {project_id}")
            except Exception as e:
                logger.error(f"Error generating initial question: {e}")

        # Process user response with orchestrator via routing (not direct call)
        try:
            logger.info(f"[send_chat_message] Calling orchestrator.process_request_async")
            response_result = await orchestrator.process_request_async(
                "socratic_counselor",
                {
                    "action": "process_response",
                    "project": project,
                    "current_user": current_user,
                    "mode": mode,
                    "is_api_mode": True,
                }
            )
            logger.info(f"[send_chat_message] Orchestrator returned: {response_result}")
            assistant_response = response_result.get("insights", {}).get("thoughts",
                                                    "Thank you for your response.")
            logger.info(f"[send_chat_message] Assistant response: {assistant_response[:50]}")
        except Exception as e:
            logger.error(f"[send_chat_message] Error processing response: {e}", exc_info=True)
            assistant_response = "Thank you for your response. I'm processing your input."

        # Save updated project
        db.save_project(project)

        # Return response in format expected by frontend
        return {
            "status": "success",
            "message": {
                "id": f"msg_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "initial_question": question_response,
            "mode": mode,
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

        # Load conversation history from project
        conversation_history = project.conversation_history or []
        total = len(conversation_history)

        # Apply pagination
        paginated_history = conversation_history[offset : offset + limit]

        # Transform to ChatMessage format for frontend
        messages = []
        for msg in paginated_history:
            messages.append({
                "id": msg.get("id", f"msg_{len(messages)}"),
                "role": msg.get("type", "user"),  # type -> role mapping
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp"),
            })

        logger.info(
            f"Retrieved {len(messages)} messages for project {project_id} "
            f"(offset={offset}, limit={limit}, total={total})"
        )

        return {
            "status": "success",
            "project_id": project_id,
            "messages": messages,
            "total": total,
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
    request_body: dict,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Switch between Socratic and Direct chat modes.

    Args:
        project_id: Project identifier
        request_body: JSON body with 'mode'
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Confirmation with new mode
    """
    try:
        # Extract mode from request body
        mode = request_body.get("mode", "").strip().lower()

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

        # Update chat mode preference in project
        old_mode = project.chat_mode
        project.chat_mode = mode
        db.save_project(project)

        logger.info(
            f"Chat mode switched for project {project_id}: "
            f"{old_mode} → {mode}"
        )

        return {
            "status": "success",
            "project_id": project_id,
            "mode": mode,
            "previous_mode": old_mode,
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

        # Get the latest assistant message or generate a new question
        assistant_messages = [
            msg for msg in (project.conversation_history or [])
            if msg.get("type") == "assistant"
        ]

        question = None
        if assistant_messages:
            # Use the last question from assistant
            question = assistant_messages[-1].get("content", "")
        else:
            # Generate initial question if no conversation yet via orchestrator routing (not direct call)
            from socrates_api.main import get_orchestrator
            try:
                orchestrator = get_orchestrator()
                question_result = await orchestrator.process_request_async(
                    "socratic_counselor",
                    {
                        "action": "generate_question",
                        "project": project,
                        "current_user": current_user,
                        "is_api_mode": True,
                    }
                )
                if question_result.get("status") == "success":
                    question = question_result.get("question")
            except Exception as e:
                logger.warning(f"Failed to generate question for hint: {e}")
                question = f"How would you describe the goals for {project.name}?"

        # Generate hint using Claude
        hint = None
        if question:
            try:
                from socrates_api.main import get_orchestrator
                orchestrator = get_orchestrator()
                hint = orchestrator.claude_client.generate_suggestions(question, project)
            except Exception as e:
                logger.error(f"Error generating hint: {e}")
                hint = "Try thinking about the main objectives and requirements."

        if not hint:
            hint = "Consider breaking down the problem into smaller parts."

        logger.info(f"Generated hint for project {project_id}")

        return {
            "status": "success",
            "hint": hint,
            "question": question or "Provide more details",
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

        # Delete conversation history
        message_count = len(project.conversation_history or [])
        project.conversation_history = []
        db.save_project(project)

        logger.info(
            f"Chat history cleared for project {project_id} "
            f"({message_count} messages deleted)"
        )

        return {
            "status": "success",
            "message": "Chat history cleared",
            "messages_deleted": message_count,
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

        # Get conversation history
        conversation_history = project.conversation_history or []
        if not conversation_history:
            logger.info(f"No conversation history for project {project_id}")
            return {
                "status": "success",
                "project_id": project_id,
                "summary": "No conversation history yet",
                "key_points": [],
                "insights": [],
            }

        # Generate summary using orchestrator or Claude
        summary_text = "No conversation history available"
        key_points = []
        insights = []

        try:
            from socrates_api.main import get_orchestrator
            orchestrator = get_orchestrator()

            # Use context_analyzer to generate summary
            summary_result = orchestrator.process_request(
                "context_analyzer",
                {
                    "action": "generate_summary",
                    "project": project,
                    "limit": len(conversation_history),
                }
            )

            if summary_result.get("status") == "success":
                summary_text = summary_result.get("summary", summary_text)
                key_points = summary_result.get("key_points", [])
                insights = summary_result.get("insights", [])
            else:
                logger.warning(f"Summary generation returned non-success status: {summary_result}")
        except Exception as e:
            logger.warning(f"Failed to use orchestrator for summary, using Claude directly: {e}")
            try:
                from socrates_api.main import get_orchestrator
                orchestrator = get_orchestrator()

                # Fallback: Use Claude directly to generate summary
                conversation_text = "\n".join([
                    f"{msg.get('type', 'unknown').upper()}: {msg.get('content', '')}"
                    for msg in conversation_history[-20:]  # Last 20 messages
                ])

                prompt = f"""Summarize this conversation in 2-3 sentences, then list 3-5 key points and insights.

Conversation:
{conversation_text}

Provide response in JSON format:
{{
    "summary": "...",
    "key_points": ["...", "..."],
    "insights": ["...", "..."]
}}"""

                response = orchestrator.claude_client.generate_response(prompt)

                # Parse response (assume JSON format)
                import json
                try:
                    parsed = json.loads(response)
                    summary_text = parsed.get("summary", summary_text)
                    key_points = parsed.get("key_points", [])
                    insights = parsed.get("insights", [])
                except json.JSONDecodeError:
                    summary_text = response[:200]  # Use first 200 chars as summary
            except Exception as e2:
                logger.error(f"Error generating summary: {e2}")
                summary_text = f"Conversation has {len(conversation_history)} messages"

        logger.info(f"Generated summary for project {project_id}")

        return {
            "status": "success",
            "project_id": project_id,
            "summary": summary_text,
            "key_points": key_points,
            "insights": insights,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating summary",
        )


@router.post(
    "/projects/{project_id}/chat/search",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Search conversation history",
)
async def search_conversations(
    project_id: str,
    request_body: dict,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabaseV2 = Depends(get_database),
):
    """
    Search through conversation history.

    Args:
        project_id: Project identifier
        request_body: JSON body with 'query' search term
        current_user: Current authenticated user
        db: Database connection

    Returns:
        List of matching messages
    """
    try:
        # Extract search query
        query = request_body.get("query", "").strip().lower()

        if not query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query is required",
            )

        # Verify project ownership
        project = db.load_project(project_id)
        if project is None or project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Search conversation history
        results = []
        for msg in project.conversation_history:
            content = msg.get("content", "").lower()
            if query in content:
                results.append({
                    "id": len(results),
                    "role": msg.get("type"),
                    "content": msg.get("content"),
                    "timestamp": msg.get("timestamp"),
                })

        return {
            "status": "success",
            "project_id": project_id,
            "query": query,
            "results": results,
            "count": len(results),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching conversations",
        )
