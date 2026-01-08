"""
Chat Sessions Router - Phase 2 implementation

Provides REST endpoints for session-based chat operations including:
- Creating and managing chat sessions
- Sending and retrieving messages within sessions
- Session lifecycle management
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import (
    ChatMessage,
    ChatMessageRequest,
    ChatSessionResponse,
    CreateChatSessionRequest,
    GetChatMessagesResponse,
    ListChatSessionsResponse,
    UpdateMessageRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["chat-sessions"])


@router.post(
    "/{project_id}/chat/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session",
)
async def create_chat_session(
    project_id: str,
    request: CreateChatSessionRequest = Body(...),
    current_user: str = Depends(get_current_user),
):
    """Create a new chat session for a project."""
    logger.debug(f"Creating chat session for project {project_id}")
    try:
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify project ownership
        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        if not hasattr(project, "chat_sessions"):
            project.chat_sessions = {}

        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        session = {
            "session_id": session_id,
            "project_id": project_id,
            "user_id": current_user,
            "title": request.title or f"Session {now.strftime('%Y-%m-%d %H:%M')}",
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
    archived: Optional[bool] = None,
    search: Optional[str] = None,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    current_user: str = Depends(get_current_user),
):
    """List chat sessions for a project with optional filtering and pagination.

    Query parameters:
    - archived: Filter by archive status (True/False/None for all)
    - search: Search session titles (case-insensitive substring match)
    - limit: Maximum sessions to return (default 50)
    - offset: Number of sessions to skip for pagination (default 0)
    """
    try:
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify project ownership
        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        sessions_dict = getattr(project, "chat_sessions", {})
        sessions_list = []

        for _session_id, session in sessions_dict.items():
            # Apply archive filter
            if archived is not None and session.get("archived", False) != archived:
                continue

            # Apply search filter
            if search is not None:
                title = session.get("title", "").lower()
                if search.lower() not in title:
                    continue

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

        # Sort by created_at descending
        sessions_list.sort(key=lambda s: s.created_at, reverse=True)

        # Apply pagination
        total = len(sessions_list)
        start = offset if offset else 0
        end = start + (limit if limit else 50)
        paginated = sessions_list[start:end]

        return ListChatSessionsResponse(sessions=paginated, total=total)

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
    """Get details of a specific chat session."""
    try:
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify project ownership
        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

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


@router.post(
    "/{project_id}/chat/sessions/{session_id}/message",
    response_model=ChatMessage,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message in chat session",
)
async def send_chat_message(
    project_id: str,
    session_id: str,
    request: ChatMessageRequest = Body(...),
    current_user: str = Depends(get_current_user),
):
    """Send a message in a chat session."""
    try:
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        sessions_dict = getattr(project, "chat_sessions", {})
        session = sessions_dict.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

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
    "/{project_id}/chat/sessions/{session_id}/messages",
    response_model=GetChatMessagesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chat session messages",
)
async def get_chat_messages(
    project_id: str,
    session_id: str,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    order: str = "asc",
    current_user: str = Depends(get_current_user),
):
    """Get messages from a chat session with pagination and ordering.

    Query parameters:
    - limit: Maximum messages to return (default 50)
    - offset: Number of messages to skip for pagination (default 0)
    - order: Sort order 'asc' (oldest first) or 'desc' (newest first) (default asc)
    """
    try:
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        sessions_dict = getattr(project, "chat_sessions", {})
        session = sessions_dict.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        all_messages = session.get("messages", [])
        total_count = len(all_messages)

        # Apply ordering
        ordered_messages = all_messages if order == "asc" else reversed(all_messages)
        ordered_messages = list(ordered_messages)

        # Apply pagination
        start = offset if offset and offset >= 0 else 0
        end = start + (limit if limit and limit > 0 else 50)
        paginated_messages = ordered_messages[start:end]

        messages_list = []
        for msg in paginated_messages:
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
            messages=messages_list, total=total_count, session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat messages: {str(e)}",
        )


@router.put(
    "/{project_id}/chat/sessions/{session_id}/messages/{message_id}",
    response_model=ChatMessage,
    status_code=status.HTTP_200_OK,
    summary="Update a chat message",
)
async def update_chat_message(
    project_id: str,
    session_id: str,
    message_id: str,
    request: UpdateMessageRequest = Body(...),
    current_user: str = Depends(get_current_user),
):
    """Update a chat message's content and metadata."""
    try:
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        sessions_dict = getattr(project, "chat_sessions", {})
        session = sessions_dict.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        messages = session.get("messages", [])
        message_idx = None
        target_message = None

        for idx, msg in enumerate(messages):
            if msg.get("message_id") == message_id:
                message_idx = idx
                target_message = msg
                break

        if message_idx is None:
            raise HTTPException(status_code=404, detail="Message not found")

        # Verify ownership
        if target_message.get("user_id") != current_user:
            raise HTTPException(status_code=403, detail="Cannot update message of another user")

        # Update message
        now = datetime.now(timezone.utc)
        target_message["content"] = request.content
        target_message["metadata"] = request.metadata
        target_message["updated_at"] = now.isoformat()
        session["updated_at"] = now.isoformat()

        db.save_project(project)

        created_at = datetime.fromisoformat(target_message.get("created_at"))
        return ChatMessage(
            message_id=target_message.get("message_id"),
            session_id=session_id,
            user_id=target_message.get("user_id"),
            content=target_message.get("content"),
            role=target_message.get("role"),
            created_at=created_at,
            updated_at=now,
            metadata=target_message.get("metadata"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update chat message: {str(e)}",
        )


@router.delete(
    "/{project_id}/chat/sessions/{session_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat message",
)
async def delete_chat_message(
    project_id: str,
    session_id: str,
    message_id: str,
    current_user: str = Depends(get_current_user),
):
    """Delete a chat message."""
    try:
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        sessions_dict = getattr(project, "chat_sessions", {})
        session = sessions_dict.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        messages = session.get("messages", [])
        message_idx = None

        for idx, msg in enumerate(messages):
            if msg.get("message_id") == message_id:
                message_idx = idx
                break

        if message_idx is None:
            raise HTTPException(status_code=404, detail="Message not found")

        # Verify ownership
        if messages[message_idx].get("user_id") != current_user:
            raise HTTPException(status_code=403, detail="Cannot delete message of another user")

        # Remove message
        messages.pop(message_idx)
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        db.save_project(project)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat message: {str(e)}",
        )


@router.put(
    "/{project_id}/chat/sessions/{session_id}/archive",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive a chat session",
)
async def archive_chat_session(
    project_id: str,
    session_id: str,
    current_user: str = Depends(get_current_user),
):
    """Archive a chat session."""
    try:
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        sessions_dict = getattr(project, "chat_sessions", {})
        session = sessions_dict.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        now = datetime.now(timezone.utc)
        session["archived"] = True
        session["updated_at"] = now.isoformat()
        db.save_project(project)

        created_at = datetime.fromisoformat(session.get("created_at"))
        updated_at = datetime.fromisoformat(session.get("updated_at"))

        return ChatSessionResponse(
            session_id=session.get("session_id"),
            project_id=session.get("project_id"),
            user_id=session.get("user_id"),
            title=session.get("title"),
            created_at=created_at,
            updated_at=updated_at,
            archived=True,
            message_count=len(session.get("messages", [])),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive chat session: {str(e)}",
        )


@router.put(
    "/{project_id}/chat/sessions/{session_id}/restore",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Restore an archived chat session",
)
async def restore_chat_session(
    project_id: str,
    session_id: str,
    current_user: str = Depends(get_current_user),
):
    """Restore an archived chat session."""
    try:
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        sessions_dict = getattr(project, "chat_sessions", {})
        session = sessions_dict.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        now = datetime.now(timezone.utc)
        session["archived"] = False
        session["updated_at"] = now.isoformat()
        db.save_project(project)

        created_at = datetime.fromisoformat(session.get("created_at"))
        updated_at = datetime.fromisoformat(session.get("updated_at"))

        return ChatSessionResponse(
            session_id=session.get("session_id"),
            project_id=session.get("project_id"),
            user_id=session.get("user_id"),
            title=session.get("title"),
            created_at=created_at,
            updated_at=updated_at,
            archived=False,
            message_count=len(session.get("messages", [])),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring chat session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore chat session: {str(e)}",
        )
