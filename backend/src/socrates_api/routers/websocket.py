"""
WebSocket Router - Real-time chat and event streaming endpoints.

Provides:
- WebSocket endpoint for chat and event streaming
- HTTP fallback endpoints for WebSocket-incompatible clients
- Message routing and event broadcasting
"""

import json
from socrates_api.models_local import ProjectContext
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from socrates_api.auth import get_current_user
from socrates_api.auth.jwt_handler import verify_access_token
from socrates_api.database import get_database, LocalDatabase
from socrates_api.models import APIResponse
from socrates_api.websocket import (
    MessageType,
    ResponseType,
    get_connection_manager,
    get_message_handler,
)
# Database import replaced with local module

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
    get_database()

    try:
        # CRITICAL FIX #1: Validate JWT token for WebSocket authentication
        if not token:
            logger.warning(f"WebSocket connection attempt without token for project {project_id}")
            await websocket.close(code=1008, reason="Authentication token required")
            return

        # Verify the JWT token
        payload = verify_access_token(token)
        if not payload:
            logger.warning(f"Invalid token for WebSocket connection to project {project_id}")
            await websocket.close(code=1008, reason="Invalid authentication token")
            return

        # Extract user_id from verified token payload
        user_id = payload.get("sub")
        if not user_id:
            logger.warning(f"Token missing subject (user_id) for project {project_id}")
            await websocket.close(code=1008, reason="Invalid token: missing user information")
            return

        logger.info(f"WebSocket authenticated: {connection_id} for user {user_id} on project {project_id}")

        # Accept connection
        try:
            await connection_manager.connect(
                websocket,
                user_id,
                project_id,
                connection_id,
            )
        except RuntimeError as e:
            await websocket.close(code=1008, reason=str(e))
            return

        logger.info(f"WebSocket connected: {connection_id} for user {user_id} on project {project_id}")

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
                logger.info(
                    f"[WebSocket {connection_id}] Parsed message type: {message.type}, content: {message.content[:50] if hasattr(message, 'content') else 'N/A'}"
                )

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
                        response_text = (
                            response.to_json()
                        )
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
                        response_text = (
                            response.to_json()
                        )
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
                logger.error(f"Error processing message in chat: {str(e)}", exc_info=True)
                error_response = {
                    "type": "error",
                    "errorCode": "PROCESSING_ERROR",
                    "errorMessage": f"Error processing message: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    await websocket.send_json(error_response)
                except Exception as send_error:
                    logger.error(
                        f"Failed to send error response to client: {str(send_error)}", exc_info=True
                    )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        await connection_manager.disconnect(connection_id)

    except Exception as e:
        logger.error(f"WebSocket error in chat endpoint: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Server error")
        except Exception as close_error:
            logger.error(f"Failed to close WebSocket connection: {str(close_error)}", exc_info=True)
        finally:
            try:
                await connection_manager.disconnect(connection_id)
            except Exception as disconnect_error:
                logger.error(
                    f"Error disconnecting from connection manager: {str(disconnect_error)}",
                    exc_info=True,
                )


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
        logger.info(
            f"[_handle_chat_message] Starting to handle chat message for project {project_id}"
        )
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
            from socrates_api.async_orchestrator import get_async_orchestrator

            db = get_database()

            project = db.load_project(project_id)
            if not project:
                logger.error(f"Project {project_id} not found")
                return None

            async_orch = get_async_orchestrator()
            logger.info("[_handle_chat_message] Got orchestrator, calling process_request")

            # Process message through orchestrator using process_request (standard pattern)
            result = await async_orch.process_request_async(
                "socratic_counselor",
                {
                    "action": "process_response",
                    "project": project,
                    "response": message.content,
                    "current_user": user_id,
                },
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

                ai_response = (
                    " | ".join(response_parts)
                    if response_parts
                    else "Thank you for sharing that information."
                )

                # Handle conflicts if any
                if result.get("conflicts_pending"):
                    ai_response += "\n\nNote: There are some conflicting specifications to resolve."
            else:
                ai_response = result.get("message", "I'm processing your response.")

            # Generate hint if requested
            hint_text = ""
            if request_hint:
                try:
                    # CRITICAL FIX #1: Build context for hint generation
                    # DEPRECATED: Agent builds context internally

                    # CRITICAL FIX #3: Use orchestrator handler instead of direct llm_client call
                    hint_result = await async_orch.process_request_async(
                        "context_analyzer",
                        {
                            "action": "generate_suggestions",
                            "project": project,
                            "conversation_history": context["conversation_history"],
                            "conversation_summary": context["conversation_summary"],
                            "context_text": message.content,
                        }
                    )
                    hint_text = hint_result.get("data", {}).get("suggestions", "Try breaking this down into smaller parts.")
                except Exception as e:
                    logger.debug("Operation failed")
                    logger.debug("Failed to generate hint:")
                    hint_text = "Try breaking this down into smaller parts."

            # CRITICAL FIX #8: Synchronize WebSocket messages with conversation_history atomically
            try:
                # Build message entries before modifying project state
                user_message = {
                    "id": f"msg_{len(project.conversation_history)}",
                    "role": "user",
                    "content": message.content,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "mode": mode,
                    "source": "websocket",  # Track message source for sync validation
                }

                assistant_message = {
                    "id": f"msg_{len(project.conversation_history) + 1}",
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "hint": hint_text if hint_text else None,
                    "source": "websocket",
                }

                # Use transaction to ensure atomic save
                # CRITICAL FIX #8: If save fails, both messages are discarded from project state
                project.conversation_history.append(user_message)
                project.conversation_history.append(assistant_message)

                # Persist to database
                db.save_project(project)
                logger.debug(
                    f"WebSocket messages synchronized with database for project {project_id}: "
                    f"user_msg={user_message['id']}, assistant_msg={assistant_message['id']}"
                )

                # CRITICAL FIX #2: Invalidate caches after WebSocket message sync
                from socrates_api.services.query_cache import get_query_cache
                cache = get_query_cache()
                cache.invalidate(f"metrics:{project_id}")
                cache.invalidate(f"readiness:{project_id}")
                cache.invalidate(f"conversation_history:{project_id}")
                cache.invalidate(f"project_detail:{project_id}")
                logger.debug(f"WebSocket: Invalidated caches for project {project_id} after message sync")

            except Exception as sync_error:
                # CRITICAL FIX #8: Explicit error if sync fails
                logger.error(
                    f"Failed to synchronize WebSocket messages with conversation history: {str(sync_error)}",
                    exc_info=True,
                )
                # Rollback in-memory changes to maintain consistency
                if user_message in project.conversation_history:
                    project.conversation_history.remove(user_message)
                if assistant_message in project.conversation_history:
                    project.conversation_history.remove(assistant_message)
                # Notify client of sync failure
                await websocket.send_json({
                    "type": "error",
                    "errorCode": "SYNC_FAILED",
                    "errorMessage": "Failed to persist messages to database. Your message was not saved.",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                return

        except Exception as e:
            logger.debug("Error processing chat message with AI", exc_info=True)
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
        logger.error(
            f"Unhandled error in _handle_chat_message for project {project_id}, user {user_id}: {str(e)}",
            exc_info=True,
        )
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
        result = await _route_command(command_name, command_args, user_id, project_id)

        response = {
            "type": ResponseType.ASSISTANT_RESPONSE.value,
            "content": result.get("message", "Command executed"),
            "requestId": message.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Command '{command_name}' executed for {user_id}")
        return response

    except Exception as e:
        logger.error(
            f"Error handling command '{message.content}' for user {user_id}: {str(e)}",
            exc_info=True,
        )
        return {
            "type": ResponseType.ERROR.value,
            "errorCode": "COMMAND_ERROR",
            "errorMessage": f"Error executing command: {str(e)}",
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
        from socrates_api.async_orchestrator import get_async_orchestrator

        db = get_database()

        project = db.load_project(project_id)
        if not project:
            return {"status": "error", "message": f"Project {project_id} not found"}

        async_orch = get_async_orchestrator()

        # Map common commands to handlers
        if command in ["hint", "help", "suggest"]:
            # Generate hint
            # CRITICAL FIX #1: Build context for hint generation
            # DEPRECATED: Agent builds context internally

            # CRITICAL FIX #3: Use orchestrator handler instead of direct llm_client call
            hint_result = await async_orch.process_request_async(
                "context_analyzer",
                {
                    "action": "generate_suggestions",
                    "project": project,
                    "conversation_history": context["conversation_history"],
                    "conversation_summary": context["conversation_summary"],
                    "request": f"{command}: {args}" if args else "Help me with this task",
                }
            )
            hint = hint_result.get("data", {}).get("suggestions", "I'm here to help!")
            return {"status": "success", "message": hint}

        elif command == "summary":
            # Generate conversation summary
            result = await async_orch.process_request_async(
                "context_analyzer",
                {
                    "action": "generate_summary",
                    "project": project,
                    "limit": 50,
                },
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
            result = await await async_orch.process_request_async(
                "socratic_counselor",
                {
                    "action": "advance_phase",
                    "project": project,
                    "current_user": user_id,
                    "is_api_mode": True,
                },
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
        logger.error(
            f"Error routing command '{command}' for user {user_id}: {str(e)}", exc_info=True
        )
        return {"status": "error", "message": f"Failed to execute command: {str(e)}"}


# ============================================================================
# Chat API Endpoints (HTTP Fallback for WebSocket)
# ============================================================================


@router.post(
    "/projects/{project_id}/chat/message",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message (HTTP fallback)",
)
async def send_chat_message(
    project_id: str,
    request_body: dict,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
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
        from socrates_api.async_orchestrator import get_async_orchestrator

        async_orch = get_async_orchestrator()
        logger.info(f"[send_chat_message] Got orchestrator: {orchestrator is not None}")

        # Build context for debug_logs
        context = {}
        try:
            # DEPRECATED: Agent builds context internally
        except Exception:
            context = {"debug_logs": []}

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
        project.conversation_history.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "role": "user",
                "content": message,
                "mode": mode,
            }
        )

        # Check if this is the first message - if so, generate initial question first
        assistant_messages = [
            msg for msg in project.conversation_history if msg.get("role") == "assistant"
        ]

        question_response = None
        if not assistant_messages:
            # Generate initial question via orchestrator routing (not direct call)
            try:
                question_result = await await async_orch.process_request_async(
                    "socratic_counselor",
                    {
                        "action": "generate_question",
                        "project": project,
                        "current_user": current_user,
                        "is_api_mode": True,
                    },
                )
                if question_result.get("status") == "success":
                    question_response = question_result.get("question")
                    logger.info(f"Generated initial question for {project_id}")
            except Exception as e:
                logger.debug("Error generating initial question", exc_info=True)

        # Process user response with orchestrator via routing (not direct call)
        try:
            logger.info("[send_chat_message] Calling orchestrator.process_request_async")
            response_result = await await async_orch.process_request_async(
                "socratic_counselor",
                {
                    "action": "process_response",
                    "project": project,
                    "current_user": current_user,
                    "mode": mode,
                    "is_api_mode": True,
                },
            )
            logger.info(f"[send_chat_message] Orchestrator returned: {response_result}")
            assistant_response = response_result.get("insights", {}).get(
                "thoughts", "Thank you for your response."
            )
            logger.info(f"[send_chat_message] Assistant response: {assistant_response[:50]}")
        except Exception as e:
            logger.debug("[send_chat_message] Error processing response", exc_info=True)
            assistant_response = "Thank you for your response. I'm processing your input."

        # Save updated project
        db.save_project(project)

        # Return response in format expected by frontend
        return APIResponse(
            success=True,
            status="success",
            message="Chat message processed successfully",
            data={
                "message": {
                    "id": f"msg_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                    "role": "assistant",
                    "content": assistant_response,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "initial_question": question_response,
                "mode": mode,
            },
            debug_logs=context.get("debug_logs", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Error sending chat message", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing message",
        )


@router.get(
    "/projects/{project_id}/chat/history",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chat history",
)
async def get_chat_history(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
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
            messages.append(
                {
                    "id": msg.get("id", f"msg_{len(messages)}"),
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("timestamp"),
                }
            )

        logger.info(
            f"Retrieved {len(messages)} messages for project {project_id} "
            f"(offset={offset}, limit={limit}, total={total})"
        )

        return APIResponse(
            success=True,
            status="success",
            message="Chat history retrieved successfully",
            data={
                "project_id": project_id,
                "messages": messages,
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Error getting chat history", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving history",
        )


@router.put(
    "/projects/{project_id}/chat/mode",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Switch chat mode",
)
async def switch_chat_mode(
    project_id: str,
    request_body: dict,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
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

        logger.info(f"Chat mode switched for project {project_id}: " f"{old_mode} → {mode}")

        return APIResponse(
            success=True,
            status="success",
            message=f"Chat mode switched to {mode}",
            data={
                "project_id": project_id,
                "mode": mode,
                "previous_mode": old_mode,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Error switching chat mode", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error switching mode",
        )


@router.get(
    "/projects/{project_id}/chat/hint",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Request hint",
)
async def request_hint(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
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

        # Build context for debug_logs early
        from socrates_api.async_orchestrator import get_async_orchestrator
        async_orch = get_async_orchestrator()
        context = {}
        try:
            # DEPRECATED: Agent builds context internally
        except Exception:
            context = {"debug_logs": []}

        # Get the latest assistant message or generate a new question
        assistant_messages = [
            msg for msg in (project.conversation_history or []) if msg.get("role") == "assistant"
        ]

        question = None
        if assistant_messages:
            # Use the last question from assistant
            question = assistant_messages[-1].get("content", "")
        else:
            # Generate initial question if no conversation yet via orchestrator routing (not direct call)
            from socrates_api.async_orchestrator import get_async_orchestrator

            try:
                async_orch = get_async_orchestrator()
                # CRITICAL FIX #1: Build context for question generation
                # DEPRECATED: Agent builds context internally

                question_result = await await async_orch.process_request_async(
                    "socratic_counselor",
                    {
                        "action": "generate_question",
                        "project": project,
                        "conversation_history": context["conversation_history"],
                        "conversation_summary": context["conversation_summary"],
                        "current_user": current_user,
                        "is_api_mode": True,
                    },
                )
                if question_result.get("status") == "success":
                    question = question_result.get("question")
            except Exception as e:
                logger.debug("Operation failed")
                logger.debug("Failed to generate question for hint:")
                question = f"How would you describe the goals for {project.name}?"

        # Generate hint using Claude
        hint = None
        if question:
            try:
                from socrates_api.async_orchestrator import get_async_orchestrator

                async_orch = get_async_orchestrator()
                # CRITICAL FIX #1: Build context for hint generation
                # DEPRECATED: Agent builds context internally

                # CRITICAL FIX #3: Use orchestrator handler instead of direct llm_client call
                hint_result = await async_orch.process_request_async(
                    "context_analyzer",
                    {
                        "action": "generate_suggestions",
                        "project": project,
                        "conversation_history": context["conversation_history"],
                        "conversation_summary": context["conversation_summary"],
                        "context_text": question,
                    }
                )
                hint = hint_result.get("data", {}).get("suggestions", "Try thinking about the main objectives and requirements.")
            except Exception as e:
                logger.debug("Error generating hint", exc_info=True)
                hint = "Try thinking about the main objectives and requirements."

        if not hint:
            hint = "Consider breaking down the problem into smaller parts."

        logger.info(f"Generated hint for project {project_id}")

        return APIResponse(
            success=True,
            status="success",
            message="Hint generated successfully",
            data={
                "hint": hint,
                "question": question or "Provide more details",
            },
            debug_logs=context.get("debug_logs", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Error requesting hint", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating hint",
        )


@router.delete(
    "/projects/{project_id}/chat/clear",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear chat history",
)
async def clear_chat_history(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
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
            f"Chat history cleared for project {project_id} " f"({message_count} messages deleted)"
        )

        return APIResponse(
            success=True,
            status="deleted",
            message="Chat history cleared",
            data={
                "messages_deleted": message_count,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Error clearing chat history", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing history",
        )


@router.get(
    "/projects/{project_id}/chat/summary",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation summary",
)
async def get_chat_summary(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
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
            return APIResponse(
                success=True,
                status="success",
                message="Summary retrieved (no conversation history yet)",
                data={
                    "project_id": project_id,
                    "summary": "No conversation history yet",
                    "key_points": [],
                    "insights": [],
                },
            )

        # Generate summary using orchestrator or Claude
        summary_text = "No conversation history available"
        key_points = []
        insights = []

        try:
            from socrates_api.async_orchestrator import get_async_orchestrator

            async_orch = get_async_orchestrator()

            # CRITICAL FIX #1: Build context for summary generation
            # DEPRECATED: Agent builds context internally

            # Use context_analyzer to generate summary
            summary_result = await async_orch.process_request_async(
                "context_analyzer",
                {
                    "action": "generate_summary",
                    "project": project,
                    "conversation_history": context["conversation_history"],
                    "conversation_summary": context["conversation_summary"],
                    "limit": len(conversation_history),
                },
            )

            if summary_result.get("status") == "success":
                summary_text = summary_result.get("summary", summary_text)
                key_points = summary_result.get("key_points", [])
                insights = summary_result.get("insights", [])
            else:
                logger.warning(f"Summary generation returned non-success status: {summary_result}")
        except Exception as e:
            logger.debug("Operation failed")
            logger.debug("Failed to use orchestrator for summary, using Claude directly:")
            try:
                from socrates_api.async_orchestrator import get_async_orchestrator

                async_orch = get_async_orchestrator()

                # Fallback: Use orchestrator to generate summary instead of direct llm_client
                conversation_text = "\n".join(
                    [
                        f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
                        for msg in conversation_history[-20:]  # Last 20 messages
                    ]
                )

                # CRITICAL FIX #3: Use orchestrator handler instead of direct llm_client call
                fallback_result = await async_orch.process_request_async(
                    "context_analyzer",
                    {
                        "action": "summarize_conversation",
                        "project": project,
                        "conversation_text": conversation_text,
                    }
                )
                response = fallback_result.get("data", {}).get("response", "{}")

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

        return APIResponse(
            success=True,
            status="success",
            message="Conversation summary generated successfully",
            data={
                "project_id": project_id,
                "summary": summary_text,
                "key_points": key_points,
                "insights": insights,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Error generating summary", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating summary",
        )


@router.post(
    "/projects/{project_id}/chat/search",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Search conversation history",
)
async def search_conversations(
    project_id: str,
    request_body: dict,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
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
                results.append(
                    {
                        "id": len(results),
                        "role": msg.get("role"),
                        "content": msg.get("content"),
                        "timestamp": msg.get("timestamp"),
                    }
                )

        return APIResponse(
            success=True,
            status="success",
            message=f"Found {len(results)} matching messages",
            data={
                "project_id": project_id,
                "query": query,
                "results": results,
                "count": len(results),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Error searching conversations", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching conversations",
        )


# ============================================================================
# Collaboration WebSocket Endpoint - Real-time Presence & Activity Tracking
# ============================================================================


@router.websocket("/ws/collaboration/{project_id}")
async def websocket_collaboration_endpoint(
    websocket: WebSocket,
    project_id: str,
    token: str = None,
):
    """
    WebSocket endpoint for real-time collaboration features.

    Clients connect with:
    - URL: /ws/collaboration/{project_id}
    - Query param: token={jwt_token}

    Send messages with format:
    {
        "type": "heartbeat" | "activity" | "typing",
        "typing": true/false,  (for typing indicator)
        "activity_type": "...",
        "activity_data": {...}
    }

    Receive events with format:
    {
        "type": "user_joined" | "user_left" | "typing" | "activity" | "presence",
        "user_id": "...",
        "user_status": "online|offline",
        "last_activity": "ISO8601",
        "current_activity": "...",
        "timestamp": "ISO8601"
    }

    Args:
        websocket: FastAPI WebSocket connection
        project_id: Project identifier
        token: JWT token for authentication (required)
    """
    connection_id = str(uuid.uuid4())
    connection_manager = get_connection_manager()
    db = get_database()

    try:
        # CRITICAL FIX #1: Validate JWT token for WebSocket authentication (Collaboration endpoint)
        if not token:
            logger.warning(f"Collaboration WebSocket connection attempt without token for project {project_id}")
            await websocket.close(code=1008, reason="Authentication token required")
            return

        # Verify the JWT token
        payload = verify_access_token(token)
        if not payload:
            logger.warning(f"Invalid token for collaboration WebSocket connection to project {project_id}")
            await websocket.close(code=1008, reason="Invalid authentication token")
            return

        # Extract user_id from verified token payload
        user_id = payload.get("sub")
        if not user_id:
            logger.warning(f"Token missing subject (user_id) for collaboration project {project_id}")
            await websocket.close(code=1008, reason="Invalid token: missing user information")
            return

        logger.info(f"Collaboration WebSocket authenticated: {connection_id} for user {user_id} on project {project_id}")

        # Accept connection
        try:
            await connection_manager.connect(
                websocket,
                user_id,
                project_id,
                connection_id,
            )
        except RuntimeError as e:
            await websocket.close(code=1008, reason=str(e))
            return

        logger.info(f"Collaboration WebSocket connected: {connection_id} for user {user_id} on project {project_id}")

        # Send welcome message with presence info
        await websocket.send_json(
            {
                "type": "acknowledgment",
                "message": "Connected to collaboration",
                "connectionId": connection_id,
                "project_id": project_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Broadcast user joined event to other collaborators
        await connection_manager.broadcast_to_project(
            project_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "connection_id": connection_id,
            },
            exclude_connection=connection_id,
        )

        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()

                message_type = data.get("type", "unknown")
                logger.debug(f"Received {message_type} from {user_id} in project {project_id}")

                # Handle heartbeat (keep-alive)
                if message_type == "heartbeat":
                    await websocket.send_json(
                        {
                            "type": "heartbeat_ack",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                # Handle activity events
                elif message_type == "activity":
                    activity_type = data.get("activity_type", "unknown")
                    activity_data = data.get("activity_data", {})

                    # Record activity in database
                    try:
                        activity = {
                            "id": f"act_{uuid.uuid4().hex[:12]}",
                            "project_id": project_id,
                            "user_id": user_id,
                            "activity_type": activity_type,
                            "activity_data": activity_data,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                        db.save_activity(activity)
                        logger.debug(f"Recorded activity: {activity_type}")
                    except Exception as e:
                        logger.debug("Error saving activity", exc_info=True)

                    # Broadcast activity to all collaborators
                    await connection_manager.broadcast_to_project(
                        project_id,
                        {
                            "type": "activity",
                            "user_id": user_id,
                            "activity_type": activity_type,
                            "activity_data": activity_data,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                # Handle typing indicators
                elif message_type == "typing":
                    is_typing = data.get("typing", False)

                    # Broadcast typing indicator to all collaborators
                    await connection_manager.broadcast_to_project(
                        project_id,
                        {
                            "type": "typing",
                            "user_id": user_id,
                            "typing": is_typing,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                        exclude_connection=connection_id,
                    )

                else:
                    logger.debug(f"Unknown message type: {message_type}")

            except json.JSONDecodeError as json_error:
                logger.warning(f"Invalid JSON received from {user_id}: {str(json_error)}")
                # Send error response to client
                try:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "errorCode": "INVALID_JSON",
                            "errorMessage": "Invalid JSON format",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                except Exception as send_error:
                    logger.error(
                        f"Failed to send JSON error response: {str(send_error)}", exc_info=True
                    )
                continue
            except Exception as e:
                logger.error(f"Error processing collaboration message: {str(e)}", exc_info=True)
                # Send error response to client
                try:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "errorCode": "PROCESSING_ERROR",
                            "errorMessage": f"Error processing message: {str(e)}",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                except Exception as send_error:
                    logger.error(f"Failed to send error response: {str(send_error)}", exc_info=True)
                continue

    except WebSocketDisconnect:
        logger.info(f"Collaboration WebSocket disconnected normally: {connection_id}")

        # Broadcast user left event
        try:
            await connection_manager.broadcast_to_project(
                project_id,
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "connection_id": connection_id,
                },
            )
        except Exception as broadcast_error:
            logger.warning(
                f"Failed to broadcast user_left event: {str(broadcast_error)}", exc_info=True
            )

        # Remove connection
        try:
            await connection_manager.disconnect(websocket, user_id, project_id, connection_id)
        except Exception as disconnect_error:
            logger.error(f"Error during disconnect cleanup: {str(disconnect_error)}", exc_info=True)

    except Exception as e:
        logger.error(f"WebSocket error in collaboration endpoint: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception as close_error:
            logger.error(
                f"Failed to close WebSocket in collaboration endpoint: {str(close_error)}",
                exc_info=True,
            )
