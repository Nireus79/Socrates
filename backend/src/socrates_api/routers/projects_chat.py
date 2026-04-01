"""
Projects Chat API endpoints for Socrates.

Provides REST endpoints for chat operations on projects including:
- Sending and receiving messages
- Managing conversation history
- Switching chat modes
- Getting hints and summaries
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from socrates_api.auth import get_current_user
from socrates_api.auth.project_access import check_project_access
from socrates_api.database import get_database, LocalDatabase
from socrates_api.models import (
    APIResponse,
    ChatMessage,
    ChatMessageRequest,
    ChatSessionResponse,
    CreateChatSessionRequest,
    GetChatMessagesResponse,
    ListChatSessionsResponse,
)
from socrates_api.models_local import User, ProjectContext
# Import debug mode from system router (centralized)
from socrates_api.routers.system import is_debug_mode


class ChatModeRequest(BaseModel):
    """Request body for switching chat mode"""

    mode: str


class SearchRequest(BaseModel):
    """Request body for searching conversations"""

    query: str


class ConflictResolution(BaseModel):
    """Individual conflict resolution from orchestrator conflicts"""

    conflict_type: str  # "goals", "tech_stack", "requirements", "constraints"
    old_value: Optional[str | list] = None  # Can be None, string, or list for compatibility
    new_value: Optional[str | list] = None  # Can be None, string, or list for compatibility
    resolution: str  # "keep", "replace", "skip", or "manual"
    manual_value: Optional[str | list] = None  # Optional resolved value for manual resolution
    conflict_id: Optional[str] = None  # Unique ID from orchestrator for tracking


class SaveExtractedSpecsRequest(BaseModel):
    """Request to save extracted specs from dialogue"""

    goals: Optional[list | str] = None
    requirements: Optional[list | str] = None
    tech_stack: Optional[list | str] = None
    constraints: Optional[list | str] = None


class ConflictResolutionRequest(BaseModel):
    """Request body for resolving conflicts"""

    conflicts: list[ConflictResolution]


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["chat"])




# ============================================================================
# Chat Sessions Endpoints (Phase 2)
# ============================================================================


@router.post(
    "/{project_id}/chat/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session",
)
async def create_chat_session(
    project_id: str,
    request: CreateChatSessionRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Create a new chat session for a project.

    Args:
        project_id: Project ID
        request: Session creation request with optional title
        current_user: Authenticated user

    Returns:
        ChatSessionResponse with new session details
    """
    try:
        logger.info(f"Creating chat session for project {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Initialize sessions storage if needed
        if not hasattr(project, "chat_sessions"):
            project.chat_sessions = {}

        # Create new session
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        session = {
            "session_id": session_id,
            "project_id": project_id,
            "user_id": current_user,
            "title": request.title or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "archived": False,
            "messages": [],
        }

        project.chat_sessions[session_id] = session
        db.save_project(project)

        return ChatSessionResponse(
            session_id=session_id,
            project_id=project_id,
            user_id=current_user,
            title=session["title"],
            created_at=now,
            updated_at=now,
            archived=False,
            message_count=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/{project_id}/chat/sessions",
    response_model=ListChatSessionsResponse,
    status_code=status.HTTP_200_OK,
    summary="List chat sessions",
)
async def list_chat_sessions(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    List all chat sessions for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        ListChatSessionsResponse with all sessions
    """
    try:
        logger.info(f"Listing chat sessions for project {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get sessions
        sessions_dict = getattr(project, "chat_sessions", {})
        sessions_list = []

        for _session_id, session in sessions_dict.items():
            created_at = datetime.fromisoformat(
                session.get("created_at", datetime.now(timezone.utc).isoformat())
            )
            updated_at = datetime.fromisoformat(
                session.get("updated_at", datetime.now(timezone.utc).isoformat())
            )

            sessions_list.append(
                ChatSessionResponse(
                    session_id=session.get("session_id"),
                    project_id=session.get("project_id"),
                    user_id=session.get("user_id"),
                    title=session.get("title"),
                    created_at=created_at,
                    updated_at=updated_at,
                    archived=session.get("archived", False),
                    message_count=len(session.get("messages", [])),
                )
            )

        return ListChatSessionsResponse(sessions=sessions_list, total=len(sessions_list))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing chat sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/{project_id}/chat/sessions/{session_id}",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chat session details",
)
async def get_chat_session(
    project_id: str,
    session_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get details of a specific chat session.

    Args:
        project_id: Project ID
        session_id: Session ID
        current_user: Authenticated user

    Returns:
        ChatSessionResponse with session details
    """
    try:
        logger.info(f"Getting chat session {session_id} for project {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get session
        sessions_dict = getattr(project, "chat_sessions", {})
        session = sessions_dict.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        created_at = datetime.fromisoformat(
            session.get("created_at", datetime.now(timezone.utc).isoformat())
        )
        updated_at = datetime.fromisoformat(
            session.get("updated_at", datetime.now(timezone.utc).isoformat())
        )

        return ChatSessionResponse(
            session_id=session.get("session_id"),
            project_id=session.get("project_id"),
            user_id=session.get("user_id"),
            title=session.get("title"),
            created_at=created_at,
            updated_at=updated_at,
            archived=session.get("archived", False),
            message_count=len(session.get("messages", [])),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.delete(
    "/{project_id}/chat/sessions/{session_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a chat session",
)
async def delete_chat_session(
    project_id: str,
    session_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Delete a chat session.

    Args:
        project_id: Project ID
        session_id: Session ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with confirmation
    """
    try:
        logger.info(f"Deleting chat session {session_id} for project {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Delete session
        sessions_dict = getattr(project, "chat_sessions", {})
        if session_id not in sessions_dict:
            raise HTTPException(status_code=404, detail="Chat session not found")

        del sessions_dict[session_id]
        db.save_project(project)

        return APIResponse(
            success=True,
            status="deleted",
            message="Chat session deleted",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.post(
    "/{project_id}/chat/{session_id}/message",
    response_model=ChatMessage,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message in chat session",
)
async def send_chat_message(
    project_id: str,
    session_id: str,
    request: ChatMessageRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Send a message in a chat session.

    Args:
        project_id: Project ID
        session_id: Session ID
        request: Message request with content
        current_user: Authenticated user

    Returns:
        ChatMessage with the sent message details
    """
    try:
        logger.info(f"Sending message to session {session_id} in project {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get session
        sessions_dict = getattr(project, "chat_sessions", {})
        session = sessions_dict.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        # Create message
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        message = {
            "message_id": message_id,
            "session_id": session_id,
            "user_id": current_user,
            "content": request.message,
            "role": request.role,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "metadata": None,
        }

        session["messages"].append(message)
        session["updated_at"] = now.isoformat()
        db.save_project(project)

        return ChatMessage(
            message_id=message_id,
            session_id=session_id,
            user_id=current_user,
            content=request.message,
            role=request.role,
            created_at=now,
            updated_at=now,
            metadata=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/{project_id}/chat/{session_id}/messages",
    response_model=GetChatMessagesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chat session messages",
)
async def get_chat_messages(
    project_id: str,
    session_id: str,
    limit: Optional[int] = None,
    current_user: str = Depends(get_current_user),
):
    """
    Get all messages in a chat session.

    Args:
        project_id: Project ID
        session_id: Session ID
        limit: Maximum number of messages to return
        current_user: Authenticated user

    Returns:
        GetChatMessagesResponse with all session messages
    """
    try:
        logger.info(f"Getting messages for session {session_id} in project {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get session
        sessions_dict = getattr(project, "chat_sessions", {})
        session = sessions_dict.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        # Get messages
        messages_list = []
        messages = session.get("messages", [])

        # Apply limit if specified
        if limit and limit > 0:
            messages = messages[-limit:]

        for msg in messages:
            created_at = datetime.fromisoformat(
                msg.get("created_at", datetime.now(timezone.utc).isoformat())
            )
            updated_at = datetime.fromisoformat(
                msg.get("updated_at", datetime.now(timezone.utc).isoformat())
            )

            messages_list.append(
                ChatMessage(
                    message_id=msg.get("message_id"),
                    session_id=msg.get("session_id"),
                    user_id=msg.get("user_id"),
                    content=msg.get("content"),
                    role=msg.get("role"),
                    created_at=created_at,
                    updated_at=updated_at,
                    metadata=msg.get("metadata"),
                )
            )

        return GetChatMessagesResponse(
            messages=messages_list, total=len(session.get("messages", [])), session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/{project_id}/chat/question",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get next Socratic question",
)
async def get_question(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get the next Socratic question for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with question
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Getting question for project {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Project must have a description (enforced at creation time)
        if not project.description:
            raise HTTPException(
                status_code=400,
                detail="Project must have a description/topic. Please edit your project and add one.",
            )

        logger.debug(f"Project loaded: id={project.project_id}, name={project.name}, description={project.description[:50] if project.description else 'EMPTY'}...")

        # Call socratic_counselor to generate question
        # Question caching happens internally to avoid redundant Claude calls
        try:
            orchestrator = get_orchestrator()
            logger.debug("Orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize orchestrator: {str(e)}"
            )

        # Pass topic directly to orchestrator (SocraticCounselor expects it at top level)
        logger.info(f"Project topic from description: {project.description[:50] if project.description else 'EMPTY'}")

        result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "generate_question",
                "project": project,
                "topic": project.description,  # SocraticCounselor.process() expects topic at top level
                "current_user": current_user,
                "user_id": current_user,
                "force_refresh": False,  # Reuse unanswered questions to prevent accumulation
            },
        )
        logger.debug(f"Orchestrator result for {project_id}: {result}")

        if result.get("status") != "success":
            logger.error(f"Orchestrator returned non-success status: {result}")
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to generate question")
            )

        # Persist any project state changes (including conversation history)
        db.save_project(project)

        # Extract question from orchestrator result (nested in "data" key)
        question_data = result.get("data", {})

        # Check if data contains an error status (nested error in successful response)
        if question_data.get("status") == "error":
            logger.warning(f"Orchestrator returned error in data: {question_data.get('message', 'Unknown error')}")
            raise HTTPException(
                status_code=400,
                detail=question_data.get("message", "Failed to generate question"),
            )

        # Extract question from either 'question' (single) or 'questions' (array) field
        question = question_data.get("question", "").strip() if question_data.get("question") else ""

        # If no single question, try to get first question from questions array
        if not question:
            questions = question_data.get("questions", [])
            if questions and len(questions) > 0:
                question = questions[0].strip()
                logger.info(f"Extracted first question from questions array: {question[:50]}...")

        # CRITICAL: Validate question is non-empty
        if not question:
            logger.error(f"Orchestrator returned empty question. Result: {result}, Data: {question_data}, Question: '{question}'")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=question_data.get("message", "Failed to generate question"),
            )

        return APIResponse(
            success=True,
            status="success",
            data={
                "question": question,
                "phase": project.phase,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.post(
    "/{project_id}/chat/message",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message",
)
async def send_message(
    project_id: str,
    request: ChatMessageRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Send a chat message and get response.

    Args:
        project_id: Project ID
        message: Message content
        mode: Chat mode (socratic or direct)
        current_user: Authenticated user

    Returns:
        SuccessResponse with assistant's response
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Sending message to project {project_id}: {request.message[:50]}...")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get user's auth method
        user_auth_method = "api_key"
        user_obj = db.load_user(current_user)
        if user_obj and hasattr(user_obj, 'claude_auth_method'):
            user_auth_method = user_obj.claude_auth_method or "api_key"

        # Determine chat mode: prioritize request.mode if provided, else use project setting
        # This allows dynamic mode switching without updating the project
        chat_mode = request.mode if hasattr(request, 'mode') and request.mode else getattr(project, "chat_mode", "socratic")
        orchestrator = get_orchestrator()
        logger.info(f"Chat mode resolved to: {chat_mode} (request.mode: {getattr(request, 'mode', 'not provided')}, project.chat_mode: {getattr(project, 'chat_mode', 'not set')})")

        if chat_mode == "direct":
            # Direct mode: Generate a direct answer without Socratic questioning
            logger.info("Processing message in DIRECT mode")

            # Build context from project
            context_parts = []
            if project.goals:
                context_parts.append(f"Project Goal: {project.goals}")
            if project.requirements:
                context_parts.append(f"Requirements: {', '.join(project.requirements)}")
            if project.tech_stack:
                context_parts.append(f"Tech Stack: {', '.join(project.tech_stack)}")

            context = "\n".join(context_parts) if context_parts else "No project context"

            # Generate direct answer
            prompt = f"""You are a helpful coding assistant. Answer the user's question directly and concisely.

Project Context:
{context}

User Question: {request.message}

Provide a helpful, direct answer."""

            # Use orchestrator to generate direct answer
            result = orchestrator.process_request(
                "direct_chat",
                {
                    "action": "generate_answer",
                    "prompt": prompt,
                    "user_id": current_user,
                    "project": project,
                }
            )

            if result.get("status") != "success":
                raise HTTPException(
                    status_code=500,
                    detail=result.get("message", "Failed to generate answer")
                )

            answer = result.get("data", {}).get("answer", "")

            if not answer:
                raise HTTPException(
                    status_code=500,
                    detail="Generated empty answer"
                )

            # Save to conversation history
            project.conversation_history.append({
                "role": "user",
                "content": request.message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            project.conversation_history.append({
                "role": "assistant",
                "content": answer,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            db.save_project(project)

            # Extract specs from both user message and assistant answer
            insights = None
            insights_message = None
            try:
                # Extract potential specs from both the user's question and the assistant's answer
                # Combine both for more comprehensive spec extraction
                combined_text = f"User Input:\n{request.message}\n\nAssistant Answer:\n{answer}"

                # Use orchestrator to extract insights
                insights_result = orchestrator.process_request(
                    "direct_chat",
                    {
                        "action": "extract_insights",
                        "text": combined_text,
                        "project": project,
                        "user_id": current_user,
                    }
                )

                if insights_result.get("status") == "success":
                    insights = insights_result.get("data", {})
                    logger.debug(f"Extracted insights from user input and assistant answer: {insights}")
                else:
                    logger.debug(f"Insight extraction returned non-success status: {insights_result.get('message')}")

                # If there are any extracted specs, format debug message and prepare for modal
                if insights:
                    specs_count = sum([
                        len(insights.get("goals", [])),
                        len(insights.get("requirements", [])),
                        len(insights.get("tech_stack", [])),
                        len(insights.get("constraints", [])),
                    ])

                    if specs_count > 0:
                        # Always show debug message if specs found (not just in debug mode)
                        insights_message = f"\n\n📊 **Detected Specs**:\n"
                        if insights.get("goals"):
                            insights_message += f"- Goals: {', '.join(insights['goals'])}\n"
                        if insights.get("requirements"):
                            insights_message += f"- Requirements: {', '.join(insights['requirements'])}\n"
                        if insights.get("tech_stack"):
                            insights_message += f"- Tech Stack: {', '.join(insights['tech_stack'])}\n"
                        if insights.get("constraints"):
                            insights_message += f"- Constraints: {', '.join(insights['constraints'])}\n"
                        insights_message += "\n*Would you like to save these specs to your project?*"
                        logger.info(f"Detected {specs_count} specs in direct mode dialogue - modal will be shown to user")

            except Exception as e:
                logger.debug("Operation failed")
                logger.warning(f"Failed to extract insights in direct mode: {str(e)}")
                # Continue without insights if extraction fails
                insights = None

            # Prepare response data
            specs_count = sum([
                len(insights.get("goals", [])) if insights else 0,
                len(insights.get("requirements", [])) if insights else 0,
                len(insights.get("tech_stack", [])) if insights else 0,
                len(insights.get("constraints", [])) if insights else 0,
            ])

            response_data = {
                "message": {
                    "id": f"msg_{id(answer)}",
                    "role": "assistant",
                    "content": answer + (insights_message if insights_message else ""),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "mode": "direct",
                # Include extracted specs for user confirmation (not auto-saved)
                "extracted_specs": insights,
                "extracted_specs_count": specs_count,
            }

            # Add debug info if debug mode is enabled
            if is_debug_mode(current_user):
                logger.debug("Debug mode enabled - returning debug annotations to frontend")
                response_data["debugInfo"] = {
                    "specs_extracted": specs_count > 0,
                    "extracted_specs": insights,
                    "extracted_specs_count": specs_count,
                    "inline_annotations": {
                        "goals": insights.get("goals", []) if insights else [],
                        "requirements": insights.get("requirements", []) if insights else [],
                        "tech_stack": insights.get("tech_stack", []) if insights else [],
                        "constraints": insights.get("constraints", []) if insights else [],
                    } if specs_count > 0 else {},
                }
                logger.debug(f"Direct mode debug info: {specs_count} specs extracted")

            return APIResponse(
                success=True,
                status="success",
                data=response_data,
            )
        else:
            # Socratic mode: Use the existing Socratic questioning approach
            logger.info("Processing message in SOCRATIC mode")


            # Call socratic_counselor to process response
            # Pre-extracted insights caching and async processing happen internally
            result = orchestrator.process_request(
                "socratic_counselor",
                {
                    "action": "process_response",
                    "project": project,
                    "response": request.message,
                    "current_user": current_user,
                    "is_api_mode": True,  # Indicate API mode to handle conflicts differently
                },
            )

            if result.get("status") != "success":
                raise HTTPException(
                    status_code=500, detail=result.get("message", "Failed to process message")
                )

            # Persist project changes to database (conversation history, maturity, etc.)
            db.save_project(project)

            # Extract data from orchestrator response
            result_data = result.get("data", {})
            extracted_specs = result_data.get("extracted_specs", {})
            conflicts = result_data.get("conflicts", [])
            feedback = result_data.get("feedback", "")

            # CRITICAL FIX #4: Emit debug logs in real-time when debug mode enabled
            if is_debug_mode(current_user):
                try:
                    from socrates_api.websocket.connection_manager import get_connection_manager
                    from socrates_api.models_local import EventType
                    from datetime import datetime, timezone
                    import json

                    conn_manager = get_connection_manager()

                    # Emit background processing logs
                    debug_logs = [
                        {"level": "info", "message": f"[Background] Extracting specifications from response..."},
                        {"level": "debug", "message": f"[Background] Found {len(extracted_specs.get('goals', []))} goal(s)"},
                        {"level": "debug", "message": f"[Background] Found {len(extracted_specs.get('requirements', []))} requirement(s)"},
                        {"level": "debug", "message": f"[Background] Found {len(extracted_specs.get('tech_stack', []))} tech stack item(s)"},
                        {"level": "debug", "message": f"[Background] Found {len(extracted_specs.get('constraints', []))} constraint(s)"},
                        {"level": "info", "message": f"[Background] Checking for conflicts with existing specs..."},
                    ]

                    # If specs extracted, add success message
                    specs_count = sum([
                        len(extracted_specs.get("goals", [])),
                        len(extracted_specs.get("requirements", [])),
                        len(extracted_specs.get("tech_stack", [])),
                        len(extracted_specs.get("constraints", [])),
                    ])

                    if specs_count > 0:
                        debug_logs.append({"level": "success", "message": f"[Background] ✓ {specs_count} specs extracted and saved"})

                    if len(conflicts) > 0:
                        debug_logs.append({"level": "warning", "message": f"[Background] ⚠ {len(conflicts)} conflict(s) detected - user review needed"})
                    else:
                        debug_logs.append({"level": "success", "message": "[Background] ✓ No conflicts detected"})

                    # Emit each log as a DEBUG_LOG event
                    for log_entry in debug_logs:
                        await conn_manager.broadcast_to_project(
                            project_id=project_id,
                            event_type="DEBUG_LOG",
                            data={
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "level": log_entry["level"],
                                "message": log_entry["message"],
                            }
                        )

                    logger.debug(f"Emitted {len(debug_logs)} debug log events for project {project_id}")
                except Exception as e:
                    logger.warning(f"Failed to emit debug logs: {e}")

            # Check if conflicts detected - if so, return them for frontend resolution
            if conflicts:
                logger.info(f"Conflicts detected in Socratic mode: {len(conflicts)} conflict(s)}")

                # CRITICAL FIX #4: Emit CONFLICT_DETECTED event for real-time UI notification
                if is_debug_mode(current_user) or True:  # Always emit conflict event, even if debug off
                    try:
                        from socrates_api.websocket.connection_manager import get_connection_manager
                        from datetime import datetime, timezone

                        conn_manager = get_connection_manager()
                        await conn_manager.broadcast_to_project(
                            project_id=project_id,
                            event_type="CONFLICT_DETECTED",
                            data={
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "conflict_count": len(conflicts),
                                "conflicts": conflicts,
                                "project_id": project_id,
                            }
                        )
                        logger.debug(f"Emitted CONFLICT_DETECTED event with {len(conflicts)} conflict(s)")
                    except Exception as e:
                        logger.warning(f"Failed to emit conflict detected event: {e}")
                return APIResponse(
                    success=True,
                    status="success",
                    data={
                        "message": {
                            "id": f"msg_{id(result)}",
                            "role": "assistant",
                            "content": "Conflict detected in specifications. Please resolve before continuing.",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                        "conflicts_pending": True,
                        "conflicts": conflicts,
                    },
                )

            # In Socratic mode: Specs/insights are automatically extracted but NOT shown to user
            # They are silently extracted and stored in the project without dialogue interference
            if extracted_specs:
                logger.debug(f"Specs extracted from Socratic response: {extracted_specs}")

            # Prepare response data with debug mode annotations
            response_data = {}

            # Check if debug mode is enabled - if so, return debug info with inline annotations
            if is_debug_mode(current_user):
                logger.debug("Debug mode enabled - returning debug annotations to frontend")

                # Extract and format extracted specs for debugging
                specs_count = sum([
                    len(extracted_specs.get("goals", [])),
                    len(extracted_specs.get("requirements", [])),
                    len(extracted_specs.get("tech_stack", [])),
                    len(extracted_specs.get("constraints", [])),
                ])

                response_data["debugInfo"] = {
                    "specs_extracted": specs_count > 0,
                    "extracted_specs": extracted_specs,
                    "extracted_specs_count": specs_count,
                    "feedback": feedback,
                }

                if specs_count > 0:
                    response_data["debugInfo"]["inline_annotations"] = {
                        "goals": extracted_specs.get("goals", []),
                        "requirements": extracted_specs.get("requirements", []),
                        "tech_stack": extracted_specs.get("tech_stack", []),
                        "constraints": extracted_specs.get("constraints", []),
                    }

                logger.debug(f"Debug info with {specs_count} spec categories: {response_data['debugInfo']}")

            # In Socratic mode, don't return extracted specs as a message to the frontend
            # The frontend will proceed directly to generate the next question
            # This keeps the Socratic dialogue clean and uninterrupted
            # (Unless debug mode is enabled, specs are returned in debugInfo field)

            # Check phase readiness and add readiness status
            try:
                from socrates_api.main import get_orchestrator
                orchestrator = get_orchestrator()

                # Use new _check_phase_readiness method
                phase_readiness = orchestrator._check_phase_readiness(project)

                # Include readiness in debug info
                if is_debug_mode(current_user) and response_data.get("debugInfo"):
                    response_data["debugInfo"]["phase_readiness"] = phase_readiness

                # If phase becomes ready or complete, notify user
                if phase_readiness and (phase_readiness.get("is_complete") or phase_readiness.get("is_ready")):
                    response_data["phase_readiness"] = phase_readiness

                    if phase_readiness.get("is_complete"):
                        logger.info(
                            f"Phase {project.phase} is COMPLETE for project {project_id} "
                            f"({phase_readiness.get('maturity_percentage')}% maturity)"
                        )
                    else:
                        logger.info(
                            f"Phase {project.phase} is READY for project {project_id} "
                            f"({phase_readiness.get('maturity_percentage')}% maturity)"
                        )

                # Optional: Auto-advance if enabled and phase is complete
                if phase_readiness and phase_readiness.get("is_complete"):
                    auto_advance = getattr(project, "auto_advance_phases", False)
                    if auto_advance and phase_readiness.get("next_phase"):
                        try:
                            old_phase = project.phase
                            project.phase = phase_readiness.get("next_phase")
                            project.updated_at = datetime.now(timezone.utc)
                            db.save_project(project)

                            # Clear question cache for old phase
                            try:
                                db.clear_question_cache(project_id, phase=old_phase)
                            except:
                                pass

                            logger.info(
                                f"Auto-advanced project {project_id} from "
                                f"{old_phase} to {project.phase}"
                            )
                            response_data["auto_advanced"] = True
                            response_data["new_phase"] = project.phase
                        except Exception as e:
                            logger.error(f"Failed to auto-advance phase: {e}")

            except Exception as readiness_error:
                logger.warning(f"Failed to check phase readiness: {readiness_error}")
                # Don't fail the entire response if readiness check fails

            return APIResponse(
                success=True,
                status="success",
                data=response_data,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/{project_id}/chat/history",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chat history",
)
async def get_history(
    project_id: str,
    limit: Optional[int] = None,
    current_user: str = Depends(get_current_user),
):
    """
    Get conversation history for a project.

    Args:
        project_id: Project ID
        limit: Maximum number of messages to return
        current_user: Authenticated user

    Returns:
        SuccessResponse with conversation history
    """
    try:
        logger.info(f"Getting chat history for project: {project_id}")

        # Load project
        db = get_database()
        project_dict = db.load_project(project_id)
        if not project_dict:
            raise HTTPException(status_code=404, detail="Project not found")

        # Convert dict to ProjectContext if needed
        project = project_dict

        # Get conversation history from project
        history = getattr(project, "conversation_history", []) or []

        # Apply limit if specified
        if limit and limit > 0:
            history = history[-limit:]

        return APIResponse(
            success=True,
            status="success",
            data={
                "project_id": project_id,
                "messages": history,
                "mode": getattr(project, "chat_mode", "socratic"),
                "total": len(history),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.put(
    "/{project_id}/chat/mode",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Switch chat mode",
)
async def switch_mode(
    project_id: str,
    request: ChatModeRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Switch between socratic and direct chat modes.

    Args:
        project_id: Project ID
        mode: Chat mode (socratic or direct)
        current_user: Authenticated user

    Returns:
        SuccessResponse with confirmation
    """
    try:
        logger.info(f"Switching chat mode to {request.mode} for project {project_id}")

        if request.mode not in ["socratic", "direct"]:
            raise HTTPException(status_code=400, detail="Invalid chat mode")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Update project mode
        project.chat_mode = request.mode
        db.save_project(project)

        return APIResponse(
            success=True,
            status="success",
            data={"mode": request.mode},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching mode: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/{project_id}/chat/hint",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get hint",
)
async def get_hint(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get a hint for the current question.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with hint
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Getting hint for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call orchestrator to generate context-aware hint
        orchestrator = get_orchestrator()

        # Ensure project has 'topic' attribute for orchestrator
        project = _ensure_project_topic(project)

        result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "generate_hint",
                "project": project,
                "current_user": current_user,
            },
        )

        if result.get("status") != "success":
            # Fallback to a generic hint if hint generation fails
            logger.warning(f"Failed to generate hint: {result.get('message', 'Unknown error')}")
            fallback_hint = "Review the project requirements and consider what step comes next in your learning journey."
            response_data = {"hint": fallback_hint}

            if is_debug_mode(current_user):
                response_data["debugInfo"] = {
                    "hint_source": "fallback",
                    "phase": project.phase if project else "unknown",
                }

            return APIResponse(
                success=True,
                status="success",
                data=response_data,
            )

        hint = result.get("data", {}).get("hint") or result.get("hint", "Continue working on your project.")
        response_data = {"hint": hint}

        # Add debug info if debug mode is enabled
        if is_debug_mode(current_user):
            logger.debug("Debug mode enabled - returning hint debug info")
            response_data["debugInfo"] = {
                "hint_source": result.get("message", "SkillGeneratorAgent"),
                "phase": project.phase if project else "unknown",
                "has_goals": bool(project.goals if project else False),
            }
            logger.debug(f"Hint generated from {response_data['debugInfo']['hint_source']}")

        return APIResponse(
            success=True,
            status="success",
            data=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.delete(
    "/{project_id}/chat/clear",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear chat history",
)
async def clear_history(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Clear conversation history for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with confirmation
    """
    try:
        logger.info(f"Clearing chat history for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Clear history
        project.conversation_history = []
        db.save_project(project)

        return APIResponse(
            success=True,
            status="success",
            message="Chat history cleared",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/{project_id}/chat/summary",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation summary",
)
async def get_summary(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get AI-generated summary of conversation.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with summary
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Generating summary for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call context analyzer to generate summary
        orchestrator = get_orchestrator()

        # Ensure project has 'topic' attribute for orchestrator
        project = _ensure_project_topic(project)

        result = orchestrator.process_request(
            "context_analyzer",
            {
                "action": "generate_summary",
                "project": project,
                "user_id": current_user,
            },
        )

        if result.get("status") != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to generate summary")
            )

        return APIResponse(
            success=True,
            status="success",
            data={
                "summary": result.get("summary", ""),
                "key_points": result.get("key_points", []),
                "insights": result.get("insights", []),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.post(
    "/{project_id}/chat/search",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Search conversations",
)
async def search_conversations(
    project_id: str,
    request: SearchRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Search conversation history.

    Args:
        project_id: Project ID
        query: Search query
        current_user: Authenticated user

    Returns:
        SuccessResponse with search results
    """
    try:
        logger.info(f"Searching conversations for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Search in conversation history
        history = project.conversation_history or []
        results = [msg for msg in history if request.query.lower() in str(msg).lower()]

        return APIResponse(
            success=True,
            status="success",
            data={"results": results},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.post(
    "/{project_id}/chat/done",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Finish interactive session",
)
async def finish_session(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Finish the interactive session and finalize project state.

    This endpoint is called when user wants to end the current chat session.
    It ensures all conversation history and maturity data are persisted.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with session summary
    """
    try:
        logger.info(f"Finishing session for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Generate session summary with current state
        conversation_count = len(project.conversation_history or [])
        current_phase = project.phase
        current_maturity = project.overall_maturity
        phase_maturity = (project.phase_maturity_scores or {}).get(current_phase, 0.0)

        # Save final project state (including conversation history)
        db.save_project(project)

        return APIResponse(
            success=True,
            status="success",
            data={
                "session_summary": {
                    "total_messages": conversation_count,
                    "current_phase": current_phase,
                    "overall_maturity": round(current_maturity, 2),
                    "overall_maturity_formatted": f"{round(current_maturity, 2)}%",
                    "phase_maturity": round(phase_maturity, 2),
                    "phase_maturity_formatted": f"{round(phase_maturity, 2)}%",
                    "session_ended_at": None,
                },
                "project_id": project_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finishing session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/{project_id}/maturity/history",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get maturity history timeline",
)
async def get_maturity_history(
    project_id: str,
    limit: Optional[int] = None,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Get historical maturity tracking for a project.

    Returns a timeline of maturity changes over time, showing how the project's
    understanding has evolved through different phases.

    Args:
        project_id: Project ID
        limit: Maximum number of history entries to return (optional)
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with maturity history
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        logger.info(f"Getting maturity history for project: {project_id}")

        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get maturity history
        history = project.maturity_history or []

        # Apply limit if specified
        if limit and limit > 0:
            history = history[-limit:]

        return APIResponse(
            success=True,
            status="success",
            data={
                "project_id": project_id,
                "history": history,
                "total_events": len(project.maturity_history or []),
                "current_overall_maturity": round(project.overall_maturity, 2),
                "current_overall_maturity_formatted": f"{round(project.overall_maturity, 2)}%",
                "current_phase_maturity": round((project.phase_maturity_scores or {}).get(project.phase, 0.0), 2),
                "current_phase_maturity_formatted": f"{round((project.phase_maturity_scores or {}).get(project.phase, 0.0), 2)}%",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting maturity history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/{project_id}/maturity/status",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get maturity status and phase completion",
)
async def get_maturity_status(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Get detailed maturity status for all project phases.

    Shows completion percentage for each phase and identifies areas needing
    more learning/development.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with phase maturity breakdown
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        logger.info(f"Getting maturity status for project: {project_id}")

        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get phase maturity scores
        phase_scores = project.phase_maturity_scores or {}

        # Identify strong and weak categories
        strong_categories = []
        weak_categories = []

        if project.category_scores:
            for phase, categories in project.category_scores.items():
                for category, score in categories.items():
                    if score >= 75:
                        strong_categories.append(
                            {"phase": phase, "category": category, "score": score}
                        )
                    elif score < 25:
                        weak_categories.append(
                            {"phase": phase, "category": category, "score": score}
                        )

        return APIResponse(
            success=True,
            status="success",
            data={
                "project_id": project_id,
                "current_phase": project.phase,
                "overall_maturity": round(project.overall_maturity, 2),
                "overall_maturity_formatted": f"{round(project.overall_maturity, 2)}%",
                "phase_maturity": {
                    "discovery": round(phase_scores.get("discovery", 0.0), 2),
                    "analysis": round(phase_scores.get("analysis", 0.0), 2),
                    "design": round(phase_scores.get("design", 0.0), 2),
                    "implementation": round(phase_scores.get("implementation", 0.0), 2),
                },
                "phase_maturity_formatted": {
                    "discovery": f"{round(phase_scores.get('discovery', 0.0), 2)}%",
                    "analysis": f"{round(phase_scores.get('analysis', 0.0), 2)}%",
                    "design": f"{round(phase_scores.get('design', 0.0), 2)}%",
                    "implementation": f"{round(phase_scores.get('implementation', 0.0), 2)}%",
                },
                "strong_areas": strong_categories,
                "weak_areas": weak_categories,
                "analytics_metrics": project.analytics_metrics or {},
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting maturity status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


# ============================================================================
# Question Management Endpoints (Hybrid Approach - Phase 2.4, 3, 5)
# ============================================================================


@router.get(
    "/{project_id}/chat/questions",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all questions with status",
)
async def get_questions(
    project_id: str,
    status_filter: Optional[str] = None,  # unanswered, answered, skipped
    current_user: str = Depends(get_current_user),
):
    """
    Get all questions for a project, optionally filtered by status.
    """
    try:
        logger.info(f"Getting questions for project {project_id}, filter={status_filter}")

        db = get_database()
        project_dict = db.load_project(project_id)
        if not project_dict:
            raise HTTPException(status_code=404, detail="Project not found")

        # Convert dict to ProjectContext if needed
        project = project_dict

        questions = getattr(project, "pending_questions", []) or []

        # Ensure all questions have a status field (for backward compatibility)
        for q in questions:
            if "status" not in q:
                q["status"] = "unanswered"

        # Filter by status if specified
        if status_filter:
            questions = [q for q in questions if q.get("status") == status_filter]
            logger.info(f"Filtered {len(questions)} questions with status '{status_filter}' out of {len(project.pending_questions or [])} total")
        else:
            logger.info(f"Returning all {len(questions)} questions")

        return APIResponse(
            success=True,
            status="success",
            data={
                "questions": questions,
                "total": len(questions),
                "filtered_by": status_filter or "none",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.post(
    "/{project_id}/chat/questions/{question_id}/reopen",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Reopen a skipped question",
)
async def reopen_question(
    project_id: str,
    question_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Reopen a skipped question (mark as unanswered so user can answer it).
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Reopening question {question_id} for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        orchestrator = get_orchestrator()

        # Ensure project has 'topic' attribute for orchestrator
        project = _ensure_project_topic(project)

        result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "reopen_question",
                "project": project,
                "question_id": question_id,
            },
        )

        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to reopen question"))

        db.save_project(project)

        return APIResponse(
            success=True,
            status="success",
            data={
                "message": result.get("message", "Question reopened"),
                "question_id": question_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reopening question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.post(
    "/{project_id}/chat/skip",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark current question as skipped",
)
async def skip_question(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Mark the current unanswered question as skipped.
    """
    try:
        # Check project access - requires editor or better
        await check_project_access(project_id, current_user, db, min_role="editor")

        logger.info(f"Skipping question for project {project_id}")

        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Find the LAST (most recent) unanswered question and mark it as skipped
        skipped_count = 0
        if project.pending_questions:
            logger.info(f"Total questions in project: {len(project.pending_questions)}")
            # Iterate in reverse to find the LAST unanswered question
            for question in reversed(project.pending_questions):
                # Check if question is unanswered (default to unanswered if status missing)
                current_status = question.get("status", "unanswered")
                logger.info(f"Question {question.get('id')} status: {current_status}")
                if current_status == "unanswered":
                    question["status"] = "skipped"
                    question["skipped_at"] = datetime.now(timezone.utc).isoformat()
                    logger.info(f"Marked question as skipped: {question.get('id')}")
                    skipped_count += 1
                    break
        else:
            logger.warning(f"No pending questions found for project {project_id}")

        # Save the project
        db.save_project(project)
        logger.info(f"Saved project. Skipped {skipped_count} question(s)")

        return APIResponse(
            success=True,
            status="success",
            message="Question marked as skipped",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error skipping question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/{project_id}/chat/suggestions",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get answer suggestions for current question",
)
async def get_answer_suggestions(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get answer suggestions for the current question in the chat.
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Getting answer suggestions for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Find current question from pending_questions (use LAST unanswered, not first)
        current_question = None
        if project.pending_questions:
            unanswered = [q for q in project.pending_questions if q.get("status") == "unanswered"]
            if unanswered:
                current_question = unanswered[-1].get("question")

        if not current_question:
            # Generate phase-aware fallback suggestions
            phase_suggestions = {
                "discovery": [
                    "Review your project goals and requirements",
                    "Describe your target audience and their needs",
                    "What problem does this solve?",
                    "What alternatives have you considered?",
                    "What would success look like?"
                ],
                "analysis": [
                    "Break down your requirements into components",
                    "What are the key constraints and limitations?",
                    "How would you prioritize these requirements?",
                    "What dependencies exist?",
                    "What trade-offs are necessary?"
                ],
                "design": [
                    "Sketch the high-level system architecture",
                    "What design patterns apply here?",
                    "How would you organize the components?",
                    "What are the critical design decisions?",
                    "How would this handle edge cases?"
                ],
                "implementation": [
                    "What's the first feature to implement?",
                    "Which technologies would you use?",
                    "How would you test this?",
                    "What's your deployment strategy?",
                    "How would you measure success?"
                ],
            }
            suggestions = phase_suggestions.get(project.phase, phase_suggestions["discovery"])

            return APIResponse(
                success=True,
                status="success",
                data={
                    "suggestions": suggestions,
                    "question": "No active question",
                    "phase": project.phase,
                },
            )

        orchestrator = get_orchestrator()

        # Ensure project has 'topic' attribute for orchestrator
        project = _ensure_project_topic(project)

        result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "generate_answer_suggestions",
                "project": project,
                "current_question": current_question,
                "current_user": current_user,
            },
        )

        if result.get("status") != "success":
            # Log the error for debugging
            error_message = result.get("message", "Unknown error")
            logger.warning(f"Suggestion generation failed: {error_message}")

            # Return phase-aware fallback suggestions
            phase_suggestions = {
                "discovery": [
                    "Describe the problem you're trying to solve",
                    "Who are your target users?",
                    "What are the key challenges?",
                    "What existing solutions exist?",
                    "What would success look like?"
                ],
                "analysis": [
                    "Break down the requirements into components",
                    "What are the technical constraints?",
                    "How would you prioritize requirements?",
                    "What dependencies exist?",
                    "What trade-offs are needed?"
                ],
                "design": [
                    "Sketch the high-level architecture",
                    "What design patterns apply?",
                    "How would you organize components?",
                    "What are the key decisions?",
                    "How would this handle edge cases?"
                ],
                "implementation": [
                    "What feature would you implement first?",
                    "Which technologies would you use?",
                    "How would you test this?",
                    "What's the deployment strategy?",
                    "How would you measure success?"
                ],
            }
            suggestions = phase_suggestions.get(project.phase, phase_suggestions["discovery"])

            return APIResponse(
                success=True,
                status="success",
                data={
                    "suggestions": suggestions,
                    "question": current_question,
                    "phase": project.phase,
                    "generated": False,
                    "error": error_message,
                },
            )

        return APIResponse(
            success=True,
            status="success",
            data={
                "suggestions": result.get("suggestions", []),
                "question": current_question,
                "phase": project.phase,
                "generated": True,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


# ============================================================================
# SAVE EXTRACTED SPECS (from Direct Dialogue)
# ============================================================================


@router.post(
    "/{project_id}/chat/save-extracted-specs",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Save specs extracted from dialogue to project",
)
async def save_extracted_specs(
    project_id: str,
    request: SaveExtractedSpecsRequest,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Save extracted specs from direct dialogue after user confirmation.

    This endpoint receives extracted specs from dialogue and saves them to the project
    only after explicit user confirmation (not auto-saved).

    Args:
        project_id: The project ID
        request: Extracted specs to save (goals, requirements, tech_stack, constraints)

    Returns:
        APIResponse with saved specs summary
    """
    try:
        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check access
        # SECURITY FIX: Allow team members with viewer+ role
        await check_project_access(project_id, current_user, db, min_role="viewer")

        logger.info(f"User {current_user} is saving extracted specs to project {project_id}")

        # Track what was saved for reporting
        specs_saved = {
            "goals": [],
            "requirements": [],
            "tech_stack": [],
            "constraints": [],
        }

        # Save goals
        if request.goals:
            # If goals is a list, take first item or join
            if isinstance(request.goals, list):
                project.goals = request.goals[0] if len(request.goals) == 1 else ", ".join(str(g) for g in request.goals)
            else:
                project.goals = str(request.goals)
            specs_saved["goals"] = [project.goals]
            logger.info(f"Saved goals: {project.goals}")

        # Save requirements
        if request.requirements:
            if isinstance(request.requirements, list):
                for req in request.requirements:
                    if req not in (project.requirements or []):
                        if not project.requirements:
                            project.requirements = []
                        project.requirements.append(str(req))
                        specs_saved["requirements"].append(str(req))
            logger.info(f"Saved requirements: {specs_saved['requirements']}")

        # Save tech stack
        if request.tech_stack:
            if isinstance(request.tech_stack, list):
                for tech in request.tech_stack:
                    if tech not in (project.tech_stack or []):
                        if not project.tech_stack:
                            project.tech_stack = []
                        project.tech_stack.append(str(tech))
                        specs_saved["tech_stack"].append(str(tech))
            logger.info(f"Saved tech stack: {specs_saved['tech_stack']}")

        # Save constraints
        if request.constraints:
            if isinstance(request.constraints, list):
                for constraint in request.constraints:
                    if constraint not in (project.constraints or []):
                        if not project.constraints:
                            project.constraints = []
                        project.constraints.append(str(constraint))
                        specs_saved["constraints"].append(str(constraint))
            logger.info(f"Saved constraints: {specs_saved['constraints']}")

        # Persist to database
        db.save_project(project)
        logger.info(f"Saved extracted specs to project {project_id} after user confirmation")

        # Update maturity score for the project based on saved specs
        try:
            from socrates_api.main import get_orchestrator
            orchestrator = get_orchestrator()

            # Convert specs_saved to insights format for maturity calculation
            insights = {
                "goals": specs_saved.get("goals", []),
                "requirements": specs_saved.get("requirements", []),
                "tech_stack": specs_saved.get("tech_stack", []),
                "constraints": specs_saved.get("constraints", []),
            }

            # Only update maturity if specs were actually saved
            if any(specs_saved.values()):
                # Ensure project has 'topic' attribute for orchestrator
                project = _ensure_project_topic(project)

                maturity_result = orchestrator.process_request(
                    "quality_controller",
                    {
                        "action": "update_after_response",
                        "project": project,
                        "insights": insights,
                        "current_user": current_user,
                    },
                )

                if maturity_result.get("status") == "success":
                    maturity = maturity_result.get("maturity", {})
                    score = maturity.get("overall_score", 0.0)
                    logger.info(f"Maturity updated after specs save: {score:.1f}%")
                    # Re-save project with updated maturity
                    db.save_project(project)
        except Exception as e:
            logger.debug("Operation failed")
            logger.warning(f"Failed to update maturity after saving specs: {str(e)}")
            # Don't fail the spec save if maturity update fails

        # Return summary of what was saved
        return APIResponse(
            success=True,
            status="success",
            message="Extracted specs saved to project",
            data={
                "project_id": project_id,
                "specs_saved": specs_saved,
                "project_state": {
                    "goals": project.goals,
                    "requirements": project.requirements or [],
                    "tech_stack": project.tech_stack or [],
                    "constraints": project.constraints or [],
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving extracted specs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


# ============================================================================
# CONFLICT RESOLUTION
# ============================================================================


@router.post(
    "/{project_id}/chat/resolve-conflicts",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve detected conflicts and update project specifications",
)
async def resolve_conflicts(
    project_id: str,
    request: ConflictResolutionRequest,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Resolve specification conflicts detected during Socratic dialogue.

    When a user's response during Socratic questioning introduces specs that conflict
    with the project's existing specifications, this endpoint resolves those conflicts
    and updates the project accordingly.

    **Conflict Resolution Strategies:**
    - "keep": Keep existing spec, discard new value
    - "replace": Replace existing with new value
    - "skip": Discard new value, keep existing
    - "manual": Use a custom value provided in manual_value field

    Args:
        project_id: The project ID
        request: ConflictResolutionRequest body with list of conflict resolutions
            {
                "conflicts": [
                    {
                        "conflict_type": "goals|tech_stack|requirements|constraints",
                        "old_value": "existing_value",           # Can be string, list, or null
                        "new_value": "proposed_value",           # Can be string, list, or null
                        "resolution": "keep|replace|skip|manual",
                        "manual_value": "custom_value",          # Optional, for "manual" resolution
                        "conflict_id": "unique_id"               # Optional tracking ID
                    }
                ]
            }
        current_user: Current authenticated user (must have editor role)
        db: Database connection

    Returns:
        APIResponse with:
        - success: true on success
        - data: Updated project specs (goals, requirements, tech_stack, constraints)
        - message: Confirmation message

    Example:
        POST /projects/{project_id}/chat/resolve-conflicts
        {
            "conflicts": [
                {
                    "conflict_type": "tech_stack",
                    "old_value": "Python",
                    "new_value": "JavaScript",
                    "resolution": "replace"
                }
            ]
        }
    """
    try:
        # Check project access - requires editor or better
        await check_project_access(project_id, current_user, db, min_role="editor")

        # Load and verify project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        conflicts = request.conflicts
        logger.info(f"Resolving {len(conflicts)} conflicts for project {project_id}")

        # IMPORTANT: Preserve categorized_specs (which includes confidence info)
        # The conflict resolution only modifies the simple fields (tech_stack, requirements, etc.)
        # Confidence metadata from the original specs is preserved in categorized_specs
        logger.debug(f"Current categorized_specs before conflict resolution: {len(project.categorized_specs)} categories")

        # Apply each conflict resolution
        for conflict in conflicts:
            conflict_type = conflict.conflict_type
            old_value = conflict.old_value
            new_value = conflict.new_value
            resolution = conflict.resolution
            manual_value = conflict.manual_value

            logger.debug(
                f"Applying resolution for {conflict_type}: {resolution} "
                f"({old_value} vs {new_value})"
            )

            # Helper to safely check and remove from list
            def safe_remove(lst: list, value):
                if value and isinstance(value, str) and value in lst:
                    lst.remove(value)
                elif isinstance(value, list):
                    for v in value:
                        if v in lst:
                            lst.remove(v)

            # Helper to safely add to list
            def safe_append(lst: list, value):
                if isinstance(value, str) and value and value not in lst:
                    lst.append(value)
                elif isinstance(value, list):
                    for v in value:
                        if v and v not in lst:
                            lst.append(v)

            # Apply resolution based on choice
            if resolution == "keep":
                # Keep existing - remove new from project if it exists
                if conflict_type == "tech_stack":
                    safe_remove(project.tech_stack, new_value)
                elif conflict_type == "requirements":
                    safe_remove(project.requirements, new_value)
                elif conflict_type == "constraints":
                    safe_remove(project.constraints, new_value)

            elif resolution == "replace":
                # Replace existing with new
                if conflict_type == "tech_stack":
                    safe_remove(project.tech_stack, old_value)
                    safe_append(project.tech_stack, new_value)
                elif conflict_type == "requirements":
                    safe_remove(project.requirements, old_value)
                    safe_append(project.requirements, new_value)
                elif conflict_type == "constraints":
                    safe_remove(project.constraints, old_value)
                    safe_append(project.constraints, new_value)
                elif conflict_type == "goals":
                    # For goals, set directly (string value)
                    if isinstance(new_value, str):
                        project.goals = new_value
                    elif isinstance(new_value, list) and new_value:
                        project.goals = new_value[0]

            elif resolution == "skip":
                # Skip - remove new value
                if conflict_type == "tech_stack":
                    safe_remove(project.tech_stack, new_value)
                elif conflict_type == "requirements":
                    safe_remove(project.requirements, new_value)
                elif conflict_type == "constraints":
                    safe_remove(project.constraints, new_value)

            elif resolution == "manual" and manual_value:
                # Manual resolution - use the provided value
                if conflict_type == "tech_stack":
                    safe_remove(project.tech_stack, old_value)
                    safe_append(project.tech_stack, manual_value)
                elif conflict_type == "requirements":
                    safe_remove(project.requirements, old_value)
                    safe_append(project.requirements, manual_value)
                elif conflict_type == "constraints":
                    safe_remove(project.constraints, old_value)
                    safe_append(project.constraints, manual_value)
                elif conflict_type == "goals":
                    # For goals, set directly
                    if isinstance(manual_value, str):
                        project.goals = manual_value
                    elif isinstance(manual_value, list) and manual_value:
                        project.goals = manual_value[0]

            logger.debug(f"Applied {resolution} resolution for {conflict_type}")

        # Save updated project to database
        db.save_project(project)

        # Log confidence preservation info
        logger.info(
            f"Saved resolved project specifications for {project_id}. "
            f"Categorized specs with confidence metadata preserved: {len(project.categorized_specs)} categories"
        )

        # Prepare response data
        response_data = {
            "project_id": project_id,
            "goals": project.goals,
            "requirements": project.requirements,
            "tech_stack": project.tech_stack,
            "constraints": project.constraints,
            "next_action": "generate_question",  # Frontend should generate next Socratic question
        }

        # Add debug info if debug mode is enabled
        if is_debug_mode():
            logger.debug("Debug mode enabled - returning conflict resolution debug info")
            response_data["debugInfo"] = {
                "conflicts_resolved": len(conflicts),
                "resolved_specs": {
                    "goals": project.goals,
                    "requirements": project.requirements,
                    "tech_stack": project.tech_stack,
                    "constraints": project.constraints,
                },
                "resolutions_applied": [
                    {
                        "conflict_type": c.conflict_type,
                        "resolution": c.resolution,
                    }
                    for c in conflicts
                ],
            }
            logger.debug(f"Resolved {len(conflicts)} conflicts in debug mode")

        return APIResponse(
            success=True,
            status="success",
            message="Conflicts resolved and project updated",
            data=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving conflicts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )
