"""
Workflow optimization and approval API endpoints for Socrates.

Provides workflow approval, path selection, and optimization functionality.
Handles the blocking workflow optimization flow during question generation.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import APIResponse, ErrorResponse, SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/workflow", tags=["workflow"])


@router.get(
    "/pending-approvals/{project_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get pending workflow approvals",
    responses={
        200: {"description": "Pending approvals retrieved"},
        404: {"description": "Project not found", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def get_pending_approvals(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get list of pending workflow approval requests for a project.

    Returns all approval requests currently awaiting user decision.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with list of pending approvals
    """
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()
        db = get_database()

        # Load project to verify it exists
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get pending approvals from QC
        result = orchestrator.process_request(
            "quality_controller",
            {
                "action": "get_pending_approvals",
                "project_id": project_id,
            },
        )

        if result.get("status") != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to retrieve approvals")
            )

        return APIResponse(
            success=True,
            data={
                "pending_approvals": result.get("pending_approvals", []),
                "total_count": result.get("total_count", 0),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pending approvals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending approvals",
        )


@router.post(
    "/approve",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve a workflow path",
    responses={
        200: {"description": "Workflow approved"},
        400: {"description": "Invalid input", "model": ErrorResponse},
        404: {"description": "Approval request not found", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def approve_workflow(
    request_id: str,
    approved_path_id: str,
    project_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
):
    """
    Approve a workflow path and resume execution.

    Approves a pending workflow approval request by selecting one of the
    available paths. Execution resumes after approval.

    Args:
        request_id: Approval request ID
        approved_path_id: ID of path to approve
        project_id: Optional project ID for logging
        current_user: Authenticated user

    Returns:
        SuccessResponse with approved path information
    """
    try:
        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        orchestrator = get_orchestrator()

        if not request_id or not approved_path_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="request_id and approved_path_id required",
            )

        # Approve workflow
        result = orchestrator.process_request(
            "quality_controller",
            {
                "action": "approve_workflow",
                "request_id": request_id,
                "approved_path_id": approved_path_id,
            },
        )

        if result.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to approve workflow"),
            )

        # Record event
        record_event(
            "workflow_approved",
            {
                "request_id": request_id,
                "approved_path_id": approved_path_id,
                "project_id": project_id,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
            data={
                "request_id": request_id,
                "approved_path_id": approved_path_id,
                "message": "Workflow approved and execution may proceed",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve workflow",
        )


@router.post(
    "/reject",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject a workflow approval",
    responses={
        200: {"description": "Workflow rejected"},
        400: {"description": "Invalid input", "model": ErrorResponse},
        404: {"description": "Approval request not found", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def reject_workflow(
    request_id: str,
    reason: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
):
    """
    Reject a workflow approval.

    Rejects a pending workflow approval request and optionally provides
    a reason for the rejection. Alternative workflows may be requested.

    Args:
        request_id: Approval request ID
        reason: Optional rejection reason
        project_id: Optional project ID for logging
        current_user: Authenticated user

    Returns:
        SuccessResponse with rejection confirmation
    """
    try:
        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        orchestrator = get_orchestrator()

        if not request_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="request_id required",
            )

        rejection_reason = reason or "User rejection"

        # Reject workflow
        result = orchestrator.process_request(
            "quality_controller",
            {
                "action": "reject_workflow",
                "request_id": request_id,
                "reason": rejection_reason,
            },
        )

        if result.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to reject workflow"),
            )

        # Record event
        record_event(
            "workflow_rejected",
            {
                "request_id": request_id,
                "reason": rejection_reason,
                "project_id": project_id,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
            data={
                "request_id": request_id,
                "reason": rejection_reason,
                "message": "Workflow rejected - alternatives may be requested",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject workflow",
        )


@router.get(
    "/info/{request_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workflow approval details",
    responses={
        200: {"description": "Approval details retrieved"},
        404: {"description": "Approval not found", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def get_workflow_info(
    request_id: str,
    project_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
):
    """
    Get detailed workflow approval information.

    Displays full details about a specific pending workflow approval
    including all paths, metrics, and recommendations.

    Args:
        request_id: Approval request ID
        project_id: Optional project ID to filter by
        current_user: Authenticated user

    Returns:
        SuccessResponse with approval details
    """
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()

        # Get pending approvals
        result = orchestrator.process_request(
            "quality_controller",
            {
                "action": "get_pending_approvals",
                "project_id": project_id,
            },
        )

        if result.get("status") != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to retrieve approvals")
            )

        # Find matching approval
        pending_approvals = result.get("pending_approvals", [])
        approval = next(
            (a for a in pending_approvals if a.get("request_id") == request_id),
            None,
        )

        if not approval:
            raise HTTPException(
                status_code=404, detail=f"Approval request not found: {request_id}"
            )

        return APIResponse(
            success=True,
            data=approval,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving workflow info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow information",
        )
