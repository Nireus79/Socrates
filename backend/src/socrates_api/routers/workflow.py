"""Workflow automation router for Socrates."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth_utils import get_current_user
from socrates_api.database import LocalDatabase, get_database
from socrates_api.models import APIResponse, ErrorResponse
from socrates_api.models_local import WorkflowIntegration
from socrates_api.routers.projects import check_project_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/create", response_model=APIResponse, status_code=status.HTTP_201_CREATED, summary="Create a new workflow")
async def create_workflow(
    project_id: str,
    name: str,
    workflow_type: str,
    steps: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
) -> APIResponse:
    try:
        await check_project_access(project_id, current_user, db, min_role="editor")
        valid_types = ["phase_advancement", "code_review", "learning_assessment", "custom"]
        if workflow_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid workflow_type")
        if not steps or not isinstance(steps, list):
            raise HTTPException(status_code=400, detail="Workflow must have at least one step")
        workflow_integration = WorkflowIntegration()
        workflow_id = f"wf_{project_id}_{datetime.now(timezone.utc).timestamp()}"
        workflow_data = {
            "id": workflow_id,
            "project_id": project_id,
            "name": name,
            "type": workflow_type,
            "steps": steps,
            "metadata": metadata or {},
            "created_by": current_user,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "created",
        }
        success = workflow_integration.create_workflow(workflow_id=workflow_id, name=name, steps=steps, metadata=workflow_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create workflow")
        logger.info(f"Created workflow {workflow_id} for project {project_id}")
        return APIResponse(success=True, status="created", message=f"Workflow {name} created", data={"workflow_id": workflow_id, "name": name, "type": workflow_type, "step_count": len(steps), "status": "created"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create workflow")


@router.post("/execute", response_model=APIResponse)
async def execute_workflow(workflow_id: str, context: Optional[Dict[str, Any]] = None, current_user: str = Depends(get_current_user)) -> APIResponse:
    try:
        workflow_integration = WorkflowIntegration()
        workflow_status = workflow_integration.get_workflow_status(workflow_id)
        if not workflow_status:
            raise HTTPException(status_code=404, detail=f"Workflow not found")
        result = workflow_integration.execute_workflow(workflow_id=workflow_id, context=context or {})
        if not result:
            raise HTTPException(status_code=500, detail="Failed to execute workflow")
        logger.info(f"Executed workflow {workflow_id}")
        return APIResponse(success=True, status="success", message="Workflow executed", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to execute workflow")


@router.get("/status/{workflow_id}", response_model=APIResponse)
async def get_workflow_status(workflow_id: str, current_user: str = Depends(get_current_user)) -> APIResponse:
    try:
        workflow_integration = WorkflowIntegration()
        status_result = workflow_integration.get_workflow_status(workflow_id)
        if not status_result:
            raise HTTPException(status_code=404, detail="Workflow not found")
        logger.debug(f"Retrieved status for workflow {workflow_id}")
        return APIResponse(success=True, status="success", message="Workflow status retrieved", data=status_result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow status")


@router.get("/history/{workflow_id}", response_model=APIResponse)
async def get_workflow_history(workflow_id: str, limit: int = 10, current_user: str = Depends(get_current_user)) -> APIResponse:
    try:
        if limit < 1 or limit > 100:
            limit = min(100, max(1, limit))
        workflow_integration = WorkflowIntegration()
        workflow_status = workflow_integration.get_workflow_status(workflow_id)
        if not workflow_status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        history = workflow_integration.get_workflow_history(workflow_id=workflow_id, limit=limit)
        logger.debug(f"Retrieved {len(history)} history entries")
        return APIResponse(success=True, status="success", message=f"Retrieved {len(history)} records", data={"workflow_id": workflow_id, "history_count": len(history), "executions": history})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow history")


@router.delete("/{workflow_id}", response_model=APIResponse)
async def delete_workflow(workflow_id: str, current_user: str = Depends(get_current_user)) -> APIResponse:
    try:
        workflow_integration = WorkflowIntegration()
        workflow_status = workflow_integration.get_workflow_status(workflow_id)
        if not workflow_status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        success = workflow_integration.delete_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete workflow")
        logger.info(f"Deleted workflow {workflow_id}")
        return APIResponse(success=True, status="success", message="Workflow deleted", data={"workflow_id": workflow_id, "deleted": True})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete workflow")


@router.get("/list", response_model=APIResponse)
async def list_workflows(current_user: str = Depends(get_current_user)) -> APIResponse:
    try:
        workflow_integration = WorkflowIntegration()
        workflows = workflow_integration.list_workflows()
        logger.debug(f"Retrieved {len(workflows)} workflows")
        return APIResponse(success=True, status="success", message=f"Retrieved {len(workflows)} workflows", data={"count": len(workflows), "workflows": workflows})
    except Exception as e:
        logger.error(f"Error listing workflows: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list workflows")
