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
from socrates_api.database import get_database
from socrates_api.models import (
    APIResponse,
    ChatMessage,
    ChatMessageRequest,
    ChatSessionResponse,
    CreateChatSessionRequest,
    GetChatMessagesResponse,
    ListChatSessionsResponse,
)


class ChatModeRequest(BaseModel):
    """Request body for switching chat mode"""

    mode: str


class SearchRequest(BaseModel):
    """Request body for searching conversations"""

    query: str


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
            detail=f"Failed to create chat session: {str(e)}",
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
            detail=f"Failed to list chat sessions: {str(e)}",
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
            detail=f"Failed to get chat session: {str(e)}",
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
            detail=f"Failed to delete chat session: {str(e)}",
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
            detail=f"Failed to send chat message: {str(e)}",
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
            detail=f"Failed to get chat messages: {str(e)}",
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

        # Call socratic_counselor to generate question
        # Question caching happens internally to avoid redundant Claude calls
        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "generate_question",
                "project": project,
                "current_user": current_user,
            },
        )

        if result.get("status") != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to generate question")
            )

        # Persist any project state changes (including conversation history)
        db.save_project(project)
        if project.conversation_history:
            db.save_conversation_history(project_id, project.conversation_history)

        return APIResponse(
            success=True,
            status="success",
            data={
                "question": result.get("question", ""),
                "phase": project.phase,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get question: {str(e)}",
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

        # Call socratic_counselor to process response
        # Pre-extracted insights caching and async processing happen internally
        orchestrator = get_orchestrator()
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
        if project.conversation_history:
            db.save_conversation_history(project_id, project.conversation_history)

        # Check if conflicts detected - if so, return them for frontend resolution
        if result.get("conflicts_pending") and result.get("conflicts"):
            logger.info(f"Conflicts detected: {len(result['conflicts'])} conflict(s)")
            return APIResponse(
                success=True,
                status="success",
                data={
                    "message": {
                        "id": f"msg_{id(result)}",
                        "role": "assistant",
                        "content": "Conflict detected. Please resolve the conflict to proceed.",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    "conflicts_pending": True,
                    "conflicts": result.get("conflicts", []),
                },
            )

        # Format insights for response
        insights = result.get("insights", {})
        if insights:
            # Format insights as a readable string for the frontend
            content_parts = []
            if insights.get("goals"):
                content_parts.append(f"Goals: {insights.get('goals')}")
            if insights.get("requirements"):
                content_parts.append(f"Requirements: {', '.join(insights.get('requirements', []))}")
            if insights.get("tech_stack"):
                content_parts.append(f"Tech Stack: {', '.join(insights.get('tech_stack', []))}")
            if insights.get("constraints"):
                content_parts.append(f"Constraints: {', '.join(insights.get('constraints', []))}")
            if insights.get("team_structure"):
                content_parts.append(f"Team: {insights.get('team_structure')}")
            if insights.get("note"):
                content_parts.append(f"Note: {insights.get('note')}")
            content = "\n".join(content_parts) if content_parts else "Insights recorded."

            # Return insights message
            response_data = {
                "message": {
                    "id": f"msg_{id(result)}",
                    "role": "assistant",
                    "content": content,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            }
        else:
            # No insights - don't return a message, just return empty data
            # Frontend will handle moving to next question without adding extra message
            response_data = {}

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
            detail=f"Failed to send message: {str(e)}",
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
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get conversation history from project
        history = project.conversation_history or []

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
            detail=f"Failed to get history: {str(e)}",
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
            detail=f"Failed to switch mode: {str(e)}",
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
        result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "generate_hint",
                "project": project,
            },
        )

        if result.get("status") != "success":
            # Fallback to a generic hint if hint generation fails
            logger.warning(f"Failed to generate hint: {result.get('message', 'Unknown error')}")
            return APIResponse(
                success=True,
                status="success",
                data={"hint": "Review the project requirements and consider what step comes next in your learning journey."},
            )

        return APIResponse(
            success=True,
            status="success",
            data={"hint": result.get("hint", "Continue working on your project.")},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hint: {str(e)}",
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
        db.save_conversation_history(project_id, [])

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
            detail=f"Failed to clear history: {str(e)}",
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
        result = orchestrator.process_request(
            "context_analyzer",
            {
                "action": "generate_summary",
                "project": project,
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
            detail=f"Failed to generate summary: {str(e)}",
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
            detail=f"Failed to search conversations: {str(e)}",
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
        if project.conversation_history:
            db.save_conversation_history(project_id, project.conversation_history)

        return APIResponse(
            success=True,
            status="success",
            data={
                "session_summary": {
                    "total_messages": conversation_count,
                    "current_phase": current_phase,
                    "overall_maturity": current_maturity,
                    "phase_maturity": phase_maturity,
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
            detail=f"Failed to finish session: {str(e)}",
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
):
    """
    Get historical maturity tracking for a project.

    Returns a timeline of maturity changes over time, showing how the project's
    understanding has evolved through different phases.

    Args:
        project_id: Project ID
        limit: Maximum number of history entries to return (optional)
        current_user: Authenticated user

    Returns:
        SuccessResponse with maturity history
    """
    try:
        logger.info(f"Getting maturity history for project: {project_id}")

        # Load project
        db = get_database()
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
                "current_overall_maturity": project.overall_maturity,
                "current_phase_maturity": (project.phase_maturity_scores or {}).get(project.phase, 0.0),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting maturity history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get maturity history: {str(e)}",
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
):
    """
    Get detailed maturity status for all project phases.

    Shows completion percentage for each phase and identifies areas needing
    more learning/development.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with phase maturity breakdown
    """
    try:
        logger.info(f"Getting maturity status for project: {project_id}")

        # Load project
        db = get_database()
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
                "overall_maturity": project.overall_maturity,
                "phase_maturity": {
                    "discovery": phase_scores.get("discovery", 0.0),
                    "analysis": phase_scores.get("analysis", 0.0),
                    "design": phase_scores.get("design", 0.0),
                    "implementation": phase_scores.get("implementation", 0.0),
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
            detail=f"Failed to get maturity status: {str(e)}",
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
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        questions = project.pending_questions or []

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
            detail=f"Failed to get questions: {str(e)}",
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
            detail=f"Failed to reopen question: {str(e)}",
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
):
    """
    Mark the current unanswered question as skipped.
    """
    try:
        logger.info(f"Skipping question for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Find the current unanswered question and mark it as skipped
        skipped_count = 0
        if project.pending_questions:
            logger.info(f"Total questions in project: {len(project.pending_questions)}")
            for question in project.pending_questions:
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
            detail=f"Failed to skip question: {str(e)}",
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

        # Find current question from pending_questions
        current_question = None
        if project.pending_questions:
            unanswered = [q for q in project.pending_questions if q.get("status") == "unanswered"]
            if unanswered:
                current_question = unanswered[0].get("question")

        if not current_question:
            return APIResponse(
                success=True,
                status="success",
                data={
                    "suggestions": [
                        "Review your project goals and requirements",
                        "Consider the next logical step in your plan",
                        "Think about potential challenges and solutions",
                        "Reflect on your target audience or users",
                        "Consider how this relates to your tech stack"
                    ],
                    "question": "No active question",
                    "phase": project.phase,
                },
            )

        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "generate_answer_suggestions",
                "project": project,
                "current_question": current_question,
            },
        )

        if result.get("status") != "success":
            # Return generic suggestions if generation failed
            return APIResponse(
                success=True,
                status="success",
                data={
                    "suggestions": [
                        "Consider the problem from your target audience's perspective",
                        "Think about the technical constraints you mentioned",
                        "Review the project goals and how this relates to them",
                        "Consider existing solutions and what makes your approach unique",
                        "Think about potential challenges and how to address them"
                    ],
                    "question": current_question,
                    "phase": project.phase,
                },
            )

        return APIResponse(
            success=True,
            status="success",
            data={
                "suggestions": result.get("suggestions", []),
                "question": current_question,
                "phase": project.phase,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}",
        )
