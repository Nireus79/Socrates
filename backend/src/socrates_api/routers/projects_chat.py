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
from socrates_api.services.query_cache import get_query_cache
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
# PHASE 2.1: Helper Functions for UX Improvements
# ============================================================================


def _generate_conflict_explanation(conflicts: list) -> str:
    """
    Generate a user-friendly explanation of detected conflicts.

    Converts technical conflict data into clear, actionable messages for users.

    Args:
        conflicts: List of conflict dicts from ConflictDetector

    Returns:
        User-friendly conflict explanation message
    """
    if not conflicts:
        return "No conflicts detected."

    # Build explanation with details about each conflict
    lines = [f"I detected {len(conflicts)} conflict(s) in your specifications that need resolution:\n"]

    for i, conflict in enumerate(conflicts, 1):
        conflict_type = conflict.get("conflict_type", "unknown").replace("_", " ").title()
        severity = conflict.get("severity", "medium").upper()
        description = conflict.get("description", "No details available")

        lines.append(f"**{i}. {conflict_type}** [{severity}]")
        lines.append(f"   {description}")

        # Show old vs new values if available
        old_value = conflict.get("old_value")
        new_value = conflict.get("new_value")

        if old_value and new_value:
            old_str = str(old_value) if not isinstance(old_value, list) else ", ".join(str(v) for v in old_value)
            new_str = str(new_value) if not isinstance(new_value, list) else ", ".join(str(v) for v in new_value)
            lines.append(f"   Previous: {old_str}")
            lines.append(f"   New: {new_str}")

        lines.append("")

    lines.append("Please review these conflicts and decide how to resolve them:")
    lines.append("- **Keep** the original value")
    lines.append("- **Replace** with the new value")
    lines.append("- **Merge** both values")
    lines.append("- **Custom** - manually edit the value")

    return "\n".join(lines)


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
    force_refresh: bool = False,
):
    """
    Get the next Socratic question for a project.

    PHASE 2: Redesigned endpoint using orchestration methods.

    Flow:
    1. Load project (validate exists)
    2. Call orchestrator._orchestrate_question_generation()
    3. Save project with new pending question
    4. Return question to frontend

    Args:
        project_id: Project ID
        current_user: Authenticated user
        force_refresh: Force new generation (skip pending)

    Returns:
        APIResponse with single question
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"PHASE 2: Getting question for project {project_id}, user {current_user}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate project has context
        if not project.description and not getattr(project, "context", None):
            raise HTTPException(
                status_code=400,
                detail="Project must have a description or context. Please edit your project.",
            )

        logger.debug(f"Project loaded: id={project_id}, phase={project.phase}")

        # Initialize orchestrator
        try:
            orchestrator = get_orchestrator()
            logger.debug("Orchestrator initialized for Phase 2")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize orchestrator: {str(e)}"
            )

        # PHASE 2: Call new orchestration method
        # This handles:
        # - Checking for pending unanswered questions
        # - Gathering full context (KB, documents, previous questions, role)
        # - Generating single dynamic question
        # - Storing in pending_questions
        logger.info(f"Calling _orchestrate_question_generation for project {project_id}")

        result = orchestrator._orchestrate_question_generation(
            project=project,
            user_id=current_user,
            force_refresh=force_refresh
        )

        if result.get("status") != "success":
            logger.error(f"Question generation failed: {result.get('message', 'Unknown error')}")
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to generate question")
            )

        # Extract question from orchestration result
        question_data = result.get("question", {})
        question_text = question_data.get("question", "")
        question_id = question_data.get("id", "")

        if not question_text or not question_id:
            logger.error(f"Orchestration returned invalid question: {question_data}")
            raise HTTPException(
                status_code=500,
                detail="Generated question is invalid"
            )

        logger.info(f"Generated question {question_id}: '{question_text[:80]}...'")

        # Update project current question tracking (for context in suggestions/hints)
        project.current_question_id = question_id
        project.current_question_text = question_text

        # Save project with updated pending questions
        db.save_project(project)

        # CRITICAL FIX #2: Build context for debug logs
        context = orchestrator._build_agent_context(project)

        # CRITICAL FIX #2: Wrap response with debug logs
        wrapped_response = orchestrator._wrap_agent_response(result, context.get("debug_logs"))

        return APIResponse(
            success=True,
            status="success",
            data={
                "question": question_text,
                "question_id": question_id,
                "phase": project.phase,
                "context": result.get("context", {}),
                **wrapped_response,
            },
            debug_logs=context.get("debug_logs"),
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

            # CRITICAL FIX #2: Invalidate relevant caches after conversation update
            cache = get_query_cache()
            cache.invalidate(f"metrics:{project_id}")
            cache.invalidate(f"readiness:{project_id}")
            cache.invalidate(f"conversation_history:{project_id}")
            cache.invalidate(f"project_detail:{project_id}")
            logger.debug(f"Invalidated caches for project {project_id} after conversation update")

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

            # CRITICAL FIX #8: RECONNECT PIPELINE #5 - LEARNING ANALYTICS (Direct Mode)
            # Emit learning events for direct mode interactions
            try:
                from socrates_api.routers.events import record_event

                record_event(
                    "question_answered",
                    {
                        "project_id": project_id,
                        "phase": project.phase,
                        "response_length": len(request.message),
                        "specs_extracted": specs_count,
                        "mode": "direct",
                    },
                    user_id=current_user,
                )

                if specs_count > 0:
                    record_event(
                        "response_quality_assessed",
                        {
                            "project_id": project_id,
                            "specs_extracted": specs_count,
                            "quality_indicator": "specs_extraction_success",
                            "phase": project.phase,
                            "mode": "direct",
                        },
                        user_id=current_user,
                    )

                logger.debug(f"✓ Learning events emitted for direct mode ({specs_count} specs)")

            except Exception as learning_err:
                logger.debug(f"Failed to emit learning events (non-critical): {learning_err}")

            return APIResponse(
                success=True,
                status="success",
                data=response_data,
            )
        else:
            # Socratic mode: PHASE 2 - Use new orchestration method
            logger.info("PHASE 2: Processing message in SOCRATIC mode")

            # Get current question ID from request or project context
            question_id = getattr(request, "question_id", None) or getattr(project, "current_question_id", None)

            if not question_id:
                raise HTTPException(
                    status_code=400,
                    detail="No active question. Please request a new question first."
                )

            # PHASE 2: Call new orchestration method for answer processing
            # This handles:
            # - Adding to conversation history
            # - Extracting specifications
            # - Marking question as answered (BEFORE conflict detection)
            # - Detecting conflicts (non-blocking)
            # - Updating phase maturity
            # - Tracking question effectiveness
            logger.info(f"Calling _orchestrate_answer_processing for question {question_id}")

            result = orchestrator._orchestrate_answer_processing(
                project=project,
                user_id=current_user,
                question_id=question_id,
                answer_text=request.message
            )

            if result.get("status") != "success":
                raise HTTPException(
                    status_code=500,
                    detail=result.get("message", "Failed to process message")
                )

            # Persist project changes to database
            db.save_project(project)

            # PHASE 2: Orchestration method already handles all of the following:
            # - Adding to conversation_history
            # - Extracting specs
            # - Marking question as answered (in both pending_questions and asked_questions)
            # - Detecting conflicts
            # - Updating phase maturity
            # So we don't need to do these manually anymore

            # Invalidate caches after conversation update
            cache = get_query_cache()
            cache.invalidate(f"metrics:{project_id}")
            cache.invalidate(f"readiness:{project_id}")
            cache.invalidate(f"conversation_history:{project_id}")
            cache.invalidate(f"project_detail:{project_id}")
            logger.debug(f"Invalidated caches for project {project_id} after socratic response")

            # Extract data from new orchestration method response
            extracted_specs = result.get("specs_extracted", {})
            conflicts = result.get("conflicts", [])
            phase_maturity = result.get("phase_maturity", 0)
            phase_complete = result.get("phase_complete", False)
            feedback = result_data.get("feedback", "")

            # CRITICAL FIX #4: Emit debug logs in real-time when debug mode enabled
            if is_debug_mode(current_user):
                try:
                    from socrates_api.websocket.connection_manager import get_connection_manager
                    from socrates_api.models_local import EventType
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
                            user_id=current_user,
                            project_id=project_id,
                            message={
                                "type": "event",
                                "eventType": "DEBUG_LOG",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "data": {
                                    "level": log_entry["level"],
                                    "message": log_entry["message"],
                                }
                            }
                        )

                    logger.debug(f"Emitted {len(debug_logs)} debug log events for project {project_id}")
                except Exception as e:
                    logger.warning(f"Failed to emit debug logs: {e}")

            # Check if conflicts detected - if so, return them for frontend resolution
            if conflicts:
                logger.info(f"Conflicts detected in Socratic mode: {len(conflicts)} conflict(s)")

                # CRITICAL FIX #4: Emit CONFLICT_DETECTED event for real-time UI notification
                if is_debug_mode(current_user) or True:  # Always emit conflict event, even if debug off
                    try:
                        from socrates_api.websocket.connection_manager import get_connection_manager

                        conn_manager = get_connection_manager()
                        await conn_manager.broadcast_to_project(
                            user_id=current_user,
                            project_id=project_id,
                            message={
                                "type": "event",
                                "eventType": "CONFLICT_DETECTED",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "data": {
                                    "conflict_count": len(conflicts),
                                    "conflicts": conflicts,
                                    "project_id": project_id,
                                }
                            }
                        )
                        logger.debug(f"Emitted CONFLICT_DETECTED event with {len(conflicts)} conflict(s)")
                    except Exception as e:
                        logger.warning(f"Failed to emit conflict detected event: {e}")

                # PHASE 2.1: Generate user-friendly conflict explanation
                conflict_explanation = _generate_conflict_explanation(conflicts)

                return APIResponse(
                    success=True,
                    status="success",
                    data={
                        "message": {
                            "id": f"msg_{id(result)}",
                            "role": "assistant",
                            "content": conflict_explanation,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                        "conflicts_pending": True,
                        "conflicts": conflicts,
                        "conflict_summary": {
                            "count": len(conflicts),
                            "explanation": conflict_explanation,
                        },
                    },
                )

            # In Socratic mode: Specs/insights are automatically extracted but NOT shown to user
            # They are silently extracted and stored in the project without dialogue interference
            if extracted_specs:
                logger.debug(f"Specs extracted from Socratic response: {extracted_specs}")

            # Prepare response data with debug mode annotations
            response_data = {}

            # CRITICAL FIX: Always include debug_logs in response
            debug_logs = getattr(project, "debug_logs", []) or []
            if debug_logs:
                response_data["debug_logs"] = debug_logs
                logger.debug(f"Included {len(debug_logs)} debug logs in response")

            # Include conflicts in response if any were detected
            # Transform backend conflict format to frontend format
            if conflicts:
                formatted_conflicts = []
                for i, conflict in enumerate(conflicts):
                    # Map backend field names to frontend field names
                    conflict_type = conflict.get("field") or conflict.get("type", "unknown")
                    conflict_type = conflict_type.replace("_change", "").lower()

                    # Determine old_value and new_value based on what changed
                    added_items = conflict.get("added", [])
                    removed_items = conflict.get("removed", [])

                    # If items were added, the new_value is what was added
                    # If items were removed, the old_value is what was removed
                    if added_items:
                        new_value = ", ".join(str(item) for item in added_items)
                        old_value = "None" if not removed_items else ", ".join(str(item) for item in removed_items)
                    elif removed_items:
                        old_value = ", ".join(str(item) for item in removed_items)
                        new_value = "None"
                    else:
                        old_value = conflict.get("old_value", "Unknown")
                        new_value = conflict.get("new_value", "Unknown")

                    # Format conflict for frontend
                    formatted_conflict = {
                        "conflict_id": f"conflict_{i}",
                        "conflict_type": conflict_type,
                        "old_value": old_value,
                        "new_value": new_value,
                        "old_author": "existing specs",
                        "new_author": "your response",
                        "severity": conflict.get("severity", "medium"),
                        "suggestions": conflict.get("suggestions", []) or [
                            f"Review the proposed change in {conflict_type}"
                        ],
                    }
                    formatted_conflicts.append(formatted_conflict)

                response_data["conflicts"] = formatted_conflicts
                response_data["conflicts_pending"] = True
                logger.debug(f"Included {len(formatted_conflicts)} formatted conflicts in response")

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
                    "debug_logs_count": len(debug_logs),
                }

                if specs_count > 0:
                    response_data["debugInfo"]["inline_annotations"] = {
                        "goals": extracted_specs.get("goals", []),
                        "requirements": extracted_specs.get("requirements", []),
                        "tech_stack": extracted_specs.get("tech_stack", []),
                        "constraints": extracted_specs.get("constraints", []),
                    }

                logger.debug(f"Debug info with {specs_count} spec categories and {len(debug_logs)} logs: {response_data['debugInfo']}")

            # In Socratic mode, don't return extracted specs as a message to the frontend
            # The frontend will proceed directly to generate the next question
            # This keeps the Socratic dialogue clean and uninterrupted
            # (Unless debug mode is enabled, specs are returned in debugInfo field)

            # PHASE 4: Check phase readiness and add readiness status with advancement prompt
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

                    # PHASE 4: Generate advancement prompt when phase is complete or ready
                    if phase_readiness.get("is_complete"):
                        # Phase is 100% complete - ready to advance
                        maturity_pct = phase_readiness.get("maturity_percentage", 100)
                        current_phase = project.phase or "discovery"

                        # Get next phase in sequence (phase order is fixed)
                        phases = ["discovery", "analysis", "design", "implementation"]
                        try:
                            current_idx = phases.index(current_phase)
                            next_phase = phases[current_idx + 1] if current_idx < len(phases) - 1 else phases[-1]
                        except (ValueError, IndexError):
                            next_phase = phases[-1]  # Default to last phase

                        response_data["phase_complete"] = True
                        response_data["current_phase"] = current_phase
                        response_data["next_phase"] = next_phase
                        response_data["maturity"] = {
                            "percentage": maturity_pct,
                            "formatted": f"{int(maturity_pct)}%",
                        }
                        response_data["advancement_prompt"] = (
                            f"Congratulations! Your {current_phase.title()} phase is now 100% complete "
                            f"with all specifications defined. Ready to advance to the {next_phase.title()} phase?"
                        )
                        response_data["can_advance"] = True

                        logger.info(
                            f"Phase {project.phase} is COMPLETE for project {project_id} "
                            f"({maturity_pct}% maturity) - advancement available"
                        )
                    elif phase_readiness.get("is_ready"):
                        # Phase is near complete (80%+) - encourage completion
                        maturity_pct = phase_readiness.get("maturity_percentage", 0)
                        current_phase = project.phase or "discovery"

                        response_data["phase_ready"] = True
                        response_data["current_phase"] = current_phase
                        response_data["maturity"] = {
                            "percentage": maturity_pct,
                            "formatted": f"{int(maturity_pct)}%",
                        }
                        response_data["advancement_prompt"] = (
                            f"Great progress! Your {current_phase.title()} phase is {int(maturity_pct)}% complete. "
                            f"Keep answering questions to reach 100% and unlock phase advancement."
                        )
                        response_data["can_advance"] = False

                        logger.info(
                            f"Phase {project.phase} is READY for project {project_id} "
                            f"({maturity_pct}% maturity) - approaching completion"
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
                            except Exception as cache_err:
                                logger.debug(f"Failed to clear question cache during auto-advance: {cache_err}")

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

            # CRITICAL FIX #8: RECONNECT PIPELINE #5 - LEARNING ANALYTICS
            # Emit learning events so UserLearningAgent can track user interactions
            try:
                logger.info("Emitting learning analytics events...")

                # Emit QUESTION_ANSWERED event
                from socrates_api.routers.events import record_event

                specs_count = sum([
                    len(extracted_specs.get("goals", [])) if extracted_specs else 0,
                    len(extracted_specs.get("requirements", [])) if extracted_specs else 0,
                    len(extracted_specs.get("tech_stack", [])) if extracted_specs else 0,
                    len(extracted_specs.get("constraints", [])) if extracted_specs else 0,
                ])

                # Record learning interaction
                record_event(
                    "question_answered",
                    {
                        "project_id": project_id,
                        "phase": project.phase,
                        "response_length": len(request.message),
                        "specs_extracted": specs_count,
                        "has_conflicts": len(conflicts) > 0,
                        "mode": "socratic",
                    },
                    user_id=current_user,
                )

                # If specs were extracted, emit RESPONSE_QUALITY_ASSESSED event
                if extracted_specs:
                    record_event(
                        "response_quality_assessed",
                        {
                            "project_id": project_id,
                            "specs_extracted": specs_count,
                            "quality_indicator": "specs_extraction_success" if specs_count > 0 else "no_specs",
                            "phase": project.phase,
                        },
                        user_id=current_user,
                    )

                logger.info(f"✓ Learning events emitted for project {project_id}")

            except Exception as learning_err:
                logger.debug(f"Failed to emit learning events (non-critical): {learning_err}")
                # Learning event emission is non-critical, don't fail the request

            # CRITICAL FIX #2: Build context for debug logs
            context = orchestrator._build_agent_context(project)

            return APIResponse(
                success=True,
                status="success",
                data=response_data,
                debug_logs=context.get("debug_logs"),
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
        from socrates_api.orchestrator import get_orchestrator

        logger.info(f"Getting chat history for project: {project_id}")

        # Load project
        db = get_database()
        project_dict = db.load_project(project_id)
        if not project_dict:
            raise HTTPException(status_code=404, detail="Project not found")

        # Convert dict to ProjectContext if needed
        project = project_dict

        # CRITICAL FIX #1: Build complete context
        orchestrator = get_orchestrator()
        context = orchestrator._build_agent_context(project)

        # Get conversation history from project
        history = context.get("conversation_history", []) or []

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
            debug_logs=context.get("debug_logs"),
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

        # CRITICAL FIX #1: Build complete context with conversation history
        context = orchestrator._build_agent_context(project)

        # Ensure project has 'topic' attribute for orchestrator
        project = _ensure_project_topic(project)

        result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "generate_hint",
                "project": project,
                "conversation_history": context["conversation_history"],
                "conversation_summary": context["conversation_summary"],
                "current_user": current_user,
                "question_id": getattr(project, "current_question_id", None),
                "question_text": getattr(project, "current_question_text", None),
            },
        )

        if result.get("status") != "success":
            # Fallback to a generic hint if hint generation fails
            logger.warning(f"Failed to generate hint: {result.get('message', 'Unknown error')}")

            # Check if there's an active question
            if not getattr(project, "current_question_id", None):
                fallback_hint = "No active question. Please get a question first to receive hints."
            else:
                fallback_hint = "Review the project requirements and consider what step comes next in your learning journey."

            response_data = {"hint": fallback_hint}

            if is_debug_mode(current_user):
                response_data["debugInfo"] = {
                    "hint_source": "fallback",
                    "phase": project.phase if project else "unknown",
                }

            # CRITICAL FIX #2: Include debug logs
            return APIResponse(
                success=True,
                status="success",
                data=response_data,
                debug_logs=context.get("debug_logs"),
            )

        hint = result.get("data", {}).get("hint") or result.get("hint", "Continue working on your project.")
        response_data = {"hint": hint}

        # Emit HINT_GENERATED event
        from socrates_api.models_local import EventType
        from socrates_api.websocket.event_bridge import get_event_bridge

        event_bridge = get_event_bridge()
        await event_bridge.broadcast_message(
            current_user,
            project_id,
            f"Hint: {hint}",
        )

        # Log event for analytics
        event_data = {
            "user_id": current_user,
            "project_id": project_id,
            "hint": hint,
            "question_id": getattr(project, "current_question_id", None),
        }
        orchestrator.event_emitter.emit(EventType.HINT_GENERATED, event_data)

        # Add debug info if debug mode is enabled
        if is_debug_mode(current_user):
            logger.debug("Debug mode enabled - returning hint debug info")
            response_data["debugInfo"] = {
                "hint_source": result.get("message", "SkillGeneratorAgent"),
                "phase": project.phase if project else "unknown",
                "has_goals": bool(project.goals if project else False),
            }
            logger.debug(f"Hint generated from {response_data['debugInfo']['hint_source']}")

        # CRITICAL FIX #2: Include debug logs
        return APIResponse(
            success=True,
            status="success",
            data=response_data,
            debug_logs=context.get("debug_logs"),
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

        # CRITICAL FIX #2: Invalidate caches after clearing conversation history
        cache = get_query_cache()
        cache.invalidate(f"metrics:{project_id}")
        cache.invalidate(f"readiness:{project_id}")
        cache.invalidate(f"conversation_history:{project_id}")
        cache.invalidate(f"project_detail:{project_id}")
        logger.debug(f"Invalidated caches for project {project_id} after clearing history")

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
    Mark the current unanswered question as skipped and generate next question.
    """
    try:
        # Check project access - requires editor or better
        await check_project_access(project_id, current_user, db, min_role="editor")

        logger.info(f"Skipping question for project {project_id}")

        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Find the LAST (most recent) unanswered question
        skipped_question_id = None
        if project.pending_questions:
            logger.info(f"Total questions in project: {len(project.pending_questions)}")
            # Iterate in reverse to find the LAST unanswered question
            for question in reversed(project.pending_questions):
                current_status = question.get("status", "unanswered")
                logger.info(f"Question {question.get('id')} status: {current_status}")
                if current_status == "unanswered":
                    question_id = question.get("id")
                    question["status"] = "skipped"
                    question["skipped_at"] = datetime.now(timezone.utc).isoformat()
                    logger.info(f"Marked question as skipped: {question_id}")
                    skipped_question_id = question_id

                    # CRITICAL FIX #11: Track skipped question in new asked_questions list
                    if project.skipped_questions is None:
                        project.skipped_questions = []
                    if question_id and question_id not in project.skipped_questions:
                        project.skipped_questions.append(question_id)
                        logger.info(f"Added {question_id} to skipped_questions list")
                    break
        else:
            logger.warning(f"No pending questions found for project {project_id}")

        # Save the project
        db.save_project(project)
        logger.info(f"Saved project. Skipped question {skipped_question_id}")

        return APIResponse(
            success=True,
            status="success",
            message="Question marked as skipped",
            data={"skipped_question_id": skipped_question_id},
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
    Uses CRITICAL FIX #11: Orchestrator _generate_suggestions() method
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"Getting answer suggestions for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Find current question from persisted question metadata
        # This is set when a question is generated (in GET /question endpoint)
        current_question = getattr(project, "current_question_text", None)

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

        # CRITICAL FIX #11: Use orchestrator._generate_suggestions() instead of undefined action
        orchestrator = get_orchestrator()
        logger.info(f"Generating contextual suggestions for question: {current_question}")

        try:
            suggestions = orchestrator._generate_suggestions(current_question, project)
            logger.info(f"Generated {len(suggestions)} suggestions using orchestrator")

            # CRITICAL FIX: Include debug logs in response
            debug_logs = getattr(project, "debug_logs", []) or []

            return APIResponse(
                success=True,
                status="success",
                data={
                    "suggestions": suggestions,
                    "question": current_question,
                    "phase": project.phase,
                    "generated": True,
                    "debug_logs": debug_logs,
                },
            )
        except Exception as orch_error:
            # Log the error for debugging
            error_message = f"Orchestrator error: {str(orch_error)}"
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

            # CRITICAL FIX: Include debug logs in fallback response too
            debug_logs = getattr(project, "debug_logs", []) or []

            return APIResponse(
                success=True,
                status="success",
                data={
                    "suggestions": suggestions,
                    "question": current_question,
                    "phase": project.phase,
                    "generated": False,
                    "error": error_message,
                    "debug_logs": debug_logs,
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

        # FIX #11: Broadcast conflict resolution to all connected users in real-time
        try:
            from socrates_api.websocket import get_connection_manager
            conn_manager = get_connection_manager()
            await conn_manager.broadcast_to_project(
                user_id=current_user,
                project_id=project_id,
                message={
                    "type": "event",
                    "eventType": "CONFLICTS_RESOLVED",
                    "data": {
                        "project_id": project_id,
                        "resolved_count": len(conflicts),
                        "updated_specs": {
                            "goals": project.goals,
                            "requirements": project.requirements,
                            "tech_stack": project.tech_stack,
                            "constraints": project.constraints,
                        },
                        "resolutions": [
                            {
                                "conflict_type": c.conflict_type,
                                "resolution": c.resolution,
                            }
                            for c in conflicts
                        ],
                    },
                }
            )
            logger.debug(f"Broadcasted CONFLICTS_RESOLVED event to project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to broadcast conflict resolution: {e}")

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


# ================== PHASE 2: NEW ENDPOINTS ==================

@router.post(
    "/{project_id}/chat/suggestions",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get answer suggestions for current question",
)
async def get_suggestions(
    project_id: str,
    request: Dict[str, str],
    current_user: str = Depends(get_current_user),
):
    """
    Get diverse answer suggestions for the current question.

    PHASE 2: Uses new orchestration method to generate suggestions.

    Returns 3-5 DIVERSE suggestions with different approaches:
    - Different methodologies
    - Different perspectives
    - Different scopes
    - Different strategies

    NOT variations on the same answer - truly different angles.

    Args:
        project_id: Project ID
        request: Dict containing question_id
        current_user: Authenticated user

    Returns:
        APIResponse with diverse suggestions
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"PHASE 2: Getting suggestions for project {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get orchestrator
        orchestrator = get_orchestrator()

        # Call orchestration method
        result = orchestrator._orchestrate_answer_suggestions(
            project=project,
            user_id=current_user,
            question_id=request.get("question_id", "")
        )

        if result.get("status") != "success":
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to generate suggestions")
            )

        return APIResponse(
            success=True,
            status="success",
            data={
                "suggestions": result.get("suggestions", [])
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions",
        )


@router.post(
    "/{project_id}/chat/skip",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Skip current question",
)
async def skip_question(
    project_id: str,
    request: Dict[str, str],
    current_user: str = Depends(get_current_user),
):
    """
    Skip the current unanswered question.

    PHASE 2: Marks question as skipped and moves to next question.

    User can reopen the skipped question later to answer it.

    Args:
        project_id: Project ID
        request: Dict containing question_id
        current_user: Authenticated user

    Returns:
        APIResponse with next question
    """
    try:
        from socrates_api.main import get_orchestrator
        from datetime import datetime, timezone

        logger.info(f"PHASE 2: Skipping question in project {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        question_id = request.get("question_id", "")
        if not question_id:
            raise HTTPException(status_code=400, detail="question_id required")

        # Find and mark question as skipped
        found = False
        for q in project.pending_questions or []:
            if q.get("id") == question_id:
                q["status"] = "skipped"
                q["skipped_at"] = datetime.now(timezone.utc).isoformat()
                found = True
                logger.info(f"Marked question {question_id} as skipped")
                break

        if not found:
            raise HTTPException(status_code=404, detail="Question not found")

        # Save project
        db.save_project(project)

        # Get next question
        orchestrator = get_orchestrator()
        next_result = orchestrator._orchestrate_question_generation(
            project=project,
            user_id=current_user,
            force_refresh=False
        )

        if next_result.get("status") != "success":
            raise HTTPException(
                status_code=500,
                detail="Failed to get next question"
            )

        question_data = next_result.get("question", {})

        return APIResponse(
            success=True,
            status="success",
            data={
                "message": f"Question skipped",
                "next_question": question_data.get("question", ""),
                "next_question_id": question_data.get("id", ""),
                "phase": project.phase,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error skipping question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to skip question",
        )


@router.post(
    "/{project_id}/chat/reopen",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Reopen previously skipped question",
)
async def reopen_question(
    project_id: str,
    request: Dict[str, str],
    current_user: str = Depends(get_current_user),
):
    """
    Reopen a previously skipped question for answering.

    PHASE 2: Reverts question from skipped to unanswered state.

    User can now answer the reopened question.

    Args:
        project_id: Project ID
        request: Dict containing question_id
        current_user: Authenticated user

    Returns:
        APIResponse with reopened question
    """
    try:
        from socrates_api.main import get_orchestrator

        logger.info(f"PHASE 2: Reopening question in project {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        question_id = request.get("question_id", "")
        if not question_id:
            raise HTTPException(status_code=400, detail="question_id required")

        # Find and reopen question
        found = False
        reopened_question = None
        for q in project.pending_questions or []:
            if q.get("id") == question_id:
                if q.get("status") != "skipped":
                    raise HTTPException(status_code=400, detail="Question is not skipped")

                q["status"] = "unanswered"
                q["skipped_at"] = None
                reopened_question = q
                found = True
                logger.info(f"Marked question {question_id} as unanswered (reopened)")
                break

        if not found:
            raise HTTPException(status_code=404, detail="Question not found")

        # Save project
        db.save_project(project)

        return APIResponse(
            success=True,
            status="success",
            data={
                "message": f"Question reopened",
                "question": reopened_question.get("question", ""),
                "question_id": reopened_question.get("id", ""),
                "phase": project.phase,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reopening question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reopen question",
        )
