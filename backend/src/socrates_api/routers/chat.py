"""
Chat and Dialogue API endpoints for Socrates.

Provides REST endpoints for chat operations including:
- Getting next Socratic question
- Fetching conversation history
- Getting conversation summary
"""

import logging
from socrates_api.models_local import ProjectContext
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.database import get_database, LocalDatabase
from socrates_api.auth.project_access import check_project_access
# Database import replaced with local module
from socrates_api.models import APIResponse, ErrorResponse
from socrates_api.models_local import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.get(
    "/question/{project_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get next Socratic question",
    responses={
        200: {"description": "Question retrieved"},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_next_question(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Get the next Socratic question for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with the next question
    """
    try:
        await check_project_access(project_id, current_user, db, min_role="editor")

        from socrates_api.async_orchestrator import get_async_orchestrator
        from socrates_api.orchestrator import get_orchestrator

        logger.info(f"Getting next question for project: {project_id}")
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # CRITICAL FIX #1: Build complete context with conversation history
        orchestrator = get_orchestrator()
        context = orchestrator._build_agent_context(project)

        # Call socratic_counselor asynchronously to generate question
        async_orch = get_async_orchestrator()
        result = await async_orch.process_request_async(
            "socratic_counselor",
            {
                "action": "generate_question",
                "project": project,
                "conversation_history": context["conversation_history"],
                "conversation_summary": context["conversation_summary"],
                "current_user": current_user,
            },
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to generate question")
            )

        # CRITICAL FIX #2: Include debug logs in response
        wrapped_response = orchestrator._wrap_agent_response(result, context.get("debug_logs"))

        return APIResponse(
            success=True,
            status="success",
            message="Next question generated",
            data=wrapped_response,
            debug_logs=context.get("debug_logs"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/history/{project_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation history",
    responses={
        200: {"description": "History retrieved"},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_conversation_history(
    project_id: str,
    limit: Optional[int] = None,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Get conversation history for a project.

    Args:
        project_id: Project ID
        limit: Maximum number of messages to return
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with conversation history
    """
    try:
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.orchestrator import get_orchestrator

        logger.info(f"Getting conversation history for project: {project_id}")
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # CRITICAL FIX #1: Build complete context to extract debug logs
        orchestrator = get_orchestrator()
        context = orchestrator._build_agent_context(project)

        # Get conversation history from project
        history = context.get("conversation_history", []) or []

        # Apply limit if specified
        if limit and limit > 0:
            history = history[-limit:]

        # CRITICAL FIX #2: Include debug logs in response
        return APIResponse(
            success=True,
            status="success",
            message="Conversation history retrieved",
            data={"history": history, "count": len(history)},
            debug_logs=context.get("debug_logs"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.get(
    "/summary/{project_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation summary",
    responses={
        200: {"description": "Summary retrieved"},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_conversation_summary(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    """
    Get AI-generated summary of conversation.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with summary
    """
    try:
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.async_orchestrator import get_async_orchestrator
        from socrates_api.orchestrator import get_orchestrator

        logger.info(f"Generating summary for project: {project_id}")
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # CRITICAL FIX #1: Build complete context with conversation history
        orchestrator = get_orchestrator()
        context = orchestrator._build_agent_context(project)

        # Call context analyzer asynchronously to generate summary
        async_orch = get_async_orchestrator()
        result = await async_orch.process_request_async(
            "context_analyzer",
            {
                "action": "generate_summary",
                "project": project,
                "conversation_history": context["conversation_history"],
                "conversation_summary": context["conversation_summary"],
            },
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to generate summary")
            )

        # CRITICAL FIX #2: Include debug logs in response
        wrapped_response = orchestrator._wrap_agent_response(result, context.get("debug_logs"))

        return APIResponse(
            success=True,
            status="success",
            message="Conversation summary generated",
            data=wrapped_response,
            debug_logs=context.get("debug_logs"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )
