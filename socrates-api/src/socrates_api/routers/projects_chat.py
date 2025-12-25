"""
Projects Chat API endpoints for Socrates.

Provides REST endpoints for chat operations on projects including:
- Sending and receiving messages
- Managing conversation history
- Switching chat modes
- Getting hints and summaries
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends

from socrates_api.models import SuccessResponse, ErrorResponse
from socrates_api.auth import get_current_user
from socrates_api.database import get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["chat"])


@router.post(
    "/{project_id}/chat/message",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message",
)
async def send_message(
    project_id: str,
    message: str,
    mode: str = "socratic",
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

        logger.info(f"Sending message to project {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call socratic_counselor to process response
        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "process_response",
                "project": project,
                "response": message,
                "current_user": current_user,
            }
        )

        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to process message"))

        # Format response
        return SuccessResponse(
            success=True,
            message="Message processed",
            data={
                "message": {
                    "id": f"msg_{id(result)}",
                    "role": "assistant",
                    "content": result.get("message", ""),
                    "timestamp": "",
                }
            },
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
    response_model=SuccessResponse,
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

        return SuccessResponse(
            success=True,
            message="Conversation history retrieved",
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
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Switch chat mode",
)
async def switch_mode(
    project_id: str,
    mode: str,
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
        logger.info(f"Switching chat mode to {mode} for project {project_id}")

        if mode not in ["socratic", "direct"]:
            raise HTTPException(status_code=400, detail="Invalid chat mode")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Update project mode
        project.chat_mode = mode
        db.save_project(project)

        return SuccessResponse(
            success=True,
            message=f"Chat mode switched to {mode}",
            data={"mode": mode},
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
    response_model=SuccessResponse,
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

        # For now, return a static hint
        # In a real implementation, this would generate context-aware hints
        return SuccessResponse(
            success=True,
            message="Hint retrieved",
            data={
                "hint": "Think about the project requirements and how they relate to the current phase."
            },
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
    response_model=SuccessResponse,
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

        return SuccessResponse(
            success=True,
            message="Chat history cleared",
            data={"success": True},
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
    response_model=SuccessResponse,
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
            }
        )

        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to generate summary"))

        return SuccessResponse(
            success=True,
            message="Conversation summary generated",
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
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Search conversations",
)
async def search_conversations(
    project_id: str,
    query: str,
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
        results = [
            msg for msg in history
            if query.lower() in str(msg).lower()
        ]

        return SuccessResponse(
            success=True,
            message="Search completed",
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
