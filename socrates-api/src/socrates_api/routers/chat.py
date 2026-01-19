"""
Chat and Dialogue API endpoints for Socrates.

Provides REST endpoints for chat operations including:
- Getting next Socratic question
- Fetching conversation history
- Getting conversation summary
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.auth.project_access import check_project_access
from socratic_system.database import ProjectDatabase
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
    db: ProjectDatabase = Depends(get_database),
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

        from socrates_api.main import get_orchestrator

        logger.info(f"Getting next question for project: {project_id}")
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call socratic_counselor to generate question
        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "socratic_counselor",
            {
                "action": "generate_question",
                "project": project,
                "current_user": current_user,
            },
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to generate question")
            )

        return APIResponse(
            success=True,
        status="success",
            message="Next question generated",
            data=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get next question: {str(e)}",
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
    db: ProjectDatabase = Depends(get_database),
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

        logger.info(f"Getting conversation history for project: {project_id}")
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
            message="Conversation history retrieved",
            data={"history": history, "count": len(history)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}",
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
    db: ProjectDatabase = Depends(get_database),
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

        from socrates_api.main import get_orchestrator

        logger.info(f"Generating summary for project: {project_id}")
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

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to generate summary")
            )

        return APIResponse(
            success=True,
        status="success",
            message="Conversation summary generated",
            data=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}",
        )





