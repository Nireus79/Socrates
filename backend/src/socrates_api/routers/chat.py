"""
Chat and Dialogue API endpoints for Socrates.

Provides REST endpoints for chat operations including:
- Getting next Socratic question
- Fetching conversation history
- Getting conversation summary

MONOLITHIC PATTERN:
All endpoints delegate completely to orchestrator.process_request() which routes to agents.
Agents handle: context building, response wrapping, debug logging, data transformation.
Routers only handle: auth, DB access, error handling, API response wrapping.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.database import get_database, LocalDatabase
from socrates_api.auth.project_access import check_project_access
from socrates_api.models import APIResponse, ErrorResponse

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

    MONOLITHIC PATTERN:
    - Validate access
    - Load project
    - Delegate to orchestrator.process_request_async("socratic_counselor", {...})
    - Agent handles ALL internal logic: context gathering, generation, storage, wrapping
    - Return wrapped response

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

        logger.info(f"Getting next question for project: {project_id}")
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # MONOLITHIC PATTERN: Single orchestrator call
        # Agent handles: context building, conversation history, generation, wrapping, debug logs
        async_orch = get_async_orchestrator()
        result = await async_orch.process_request_async(
            "socratic_counselor",
            {
                "action": "generate_question",
                "project": project,
                "current_user": current_user,
                "db": db,
            },
        )

        if result.get("status") != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to generate question")
            )

        # Agent response already includes all necessary data and wrapping
        return APIResponse(
            success=True,
            status="success",
            message="Next question generated",
            data=result.get("data", result),
            debug_logs=result.get("debug_logs", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next question: {str(e)}", exc_info=True)
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

    MONOLITHIC PATTERN:
    - Simple retrieval, no agent delegation needed
    - Load project, extract history from project context, apply limit
    - Return as-is

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

        logger.info(f"Getting conversation history for project: {project_id}")
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Simple retrieval - no agent needed
        # Extract conversation history from project
        history = getattr(project, "conversation_history", []) or []

        # Apply limit if specified
        if limit and limit > 0:
            history = history[-limit:]

        logger.debug(f"Returning {len(history)} conversation messages")

        return APIResponse(
            success=True,
            status="success",
            message="Conversation history retrieved",
            data={"history": history, "count": len(history)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}", exc_info=True)
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

    MONOLITHIC PATTERN:
    - Validate access
    - Load project
    - Delegate to orchestrator.process_request_async("context_analyzer", {...})
    - Agent generates summary and handles all wrapping
    - Return wrapped response

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

        logger.info(f"Generating summary for project: {project_id}")
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # MONOLITHIC PATTERN: Single orchestrator call to context_analyzer agent
        # Agent handles: building full context, generating summary, wrapping response, debug logs
        async_orch = get_async_orchestrator()
        result = await async_orch.process_request_async(
            "context_analyzer",
            {
                "action": "generate_summary",
                "project": project,
                "current_user": current_user,
            },
        )

        if result.get("status") != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to generate summary")
            )

        # Agent response already includes all necessary data and wrapping
        return APIResponse(
            success=True,
            status="success",
            message="Conversation summary generated",
            data=result.get("data", result),
            debug_logs=result.get("debug_logs", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )
