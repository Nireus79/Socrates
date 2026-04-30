"""
Generic Agent Invocation Router - Phase 4 API Adapter

Provides unified REST endpoints for invoking any agent registered with the orchestrator.
Supports both synchronous and asynchronous invocation patterns.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import APIResponse
from socratic_system.database import ProjectDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get(
    "/list",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="List available agents",
)
async def list_agents(
    current_user: str = Depends(get_current_user),
) -> APIResponse:
    """List all available agents in the system."""
    try:
        from socrates_api.main import get_orchestrator

        orchestrator = get_orchestrator()

        # Available agents with descriptions
        available_agents = {
            "project_manager": "Manages project creation, updates, and lifecycle",
            "socratic_counselor": "Generates Socratic questions and guidance",
            "context_analyzer": "Analyzes context and extracts key information",
            "code_generator": "Generates code based on specifications",
            "system_monitor": "Monitors system health and performance",
            "conflict_detector": "Detects and reports conflicting information",
            "document_processor": "Processes and analyzes documents",
            "user_manager": "Manages user accounts and settings",
            "note_manager": "Manages notes and annotations",
            "knowledge_manager": "Manages knowledge base and search",
            "quality_controller": "Performs quality control and maturity assessment",
            "learning_agent": "Tracks and manages user learning progress",
            "multi_llm": "Coordinates multiple LLM providers",
            "question_queue": "Manages question queue and ordering",
            "code_validation": "Validates code quality and correctness",
        }

        return APIResponse(
            success=True,
            status="success",
            data={"agents": available_agents},
            message=f"Found {len(available_agents)} available agents",
        )
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{agent_name}/process",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Invoke agent synchronously",
)
async def invoke_agent_sync(
    agent_name: str,
    request_payload: Dict[str, Any] = Body(...),
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
) -> APIResponse:
    """
    Invoke an agent synchronously and wait for response.

    Request format:
    ```json
    {
        "action": "method_name",
        "project_id": "optional_project_id",
        "additional_param": "value",
        ...
    }
    ```

    Response:
    ```json
    {
        "success": true,
        "status": "success",
        "data": {...agent_result...},
        "message": "Description of what happened"
    }
    ```
    """
    try:
        from socrates_api.main import get_orchestrator

        # Validate agent name
        valid_agents = {
            "project_manager", "socratic_counselor", "context_analyzer",
            "code_generator", "system_monitor", "conflict_detector",
            "document_processor", "user_manager", "note_manager",
            "knowledge_manager", "quality_controller", "learning_agent",
            "multi_llm", "question_queue", "code_validation",
        }

        if agent_name not in valid_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent: {agent_name}. Valid agents: {', '.join(valid_agents)}",
            )

        orchestrator = get_orchestrator()

        # Prepare request with user context
        request = {
            "current_user": current_user,
            **request_payload,
        }

        # Add project context if project_id provided
        project_id = request_payload.get("project_id")
        if project_id:
            try:
                project = db.load_project(project_id)
                request["project"] = project
            except Exception as e:
                logger.warning(f"Could not load project {project_id}: {e}")

        # Invoke agent
        result = await orchestrator.process_request_async(agent_name, request)

        # Wrap result in standard response
        success = result.get("status") == "success"
        return APIResponse(
            success=success,
            status=result.get("status", "error"),
            data=result.get("data", result),
            message=result.get("message", f"Agent {agent_name} completed"),
            error_code=result.get("error_code"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invoking agent {agent_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent invocation failed: {str(e)}")


@router.post(
    "/{agent_name}/process-async",
    response_model=APIResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Invoke agent asynchronously with job queue",
)
async def invoke_agent_async(
    agent_name: str,
    request_payload: Dict[str, Any] = Body(...),
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
) -> APIResponse:
    """
    Submit an async job to invoke an agent.
    Returns immediately with job_id for polling.

    Response includes job_id to poll status later via GET /api/v1/agents/jobs/{job_id}/status
    """
    try:
        from socrates_api.main import get_orchestrator
        from socratic_system.events import JobQueue

        # Validate agent name
        valid_agents = {
            "project_manager", "socratic_counselor", "context_analyzer",
            "code_generator", "system_monitor", "conflict_detector",
            "document_processor", "user_manager", "note_manager",
            "knowledge_manager", "quality_controller", "learning_agent",
            "multi_llm", "question_queue", "code_validation",
        }

        if agent_name not in valid_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent: {agent_name}",
            )

        orchestrator = get_orchestrator()
        job_queue = JobQueue()  # Get global job queue

        # Prepare request
        request = {
            "current_user": current_user,
            **request_payload,
        }

        # Add project context if provided
        project_id = request_payload.get("project_id")
        if project_id:
            try:
                project = db.load_project(project_id)
                request["project"] = project
            except Exception as e:
                logger.warning(f"Could not load project {project_id}: {e}")

        # Submit async job
        async def run_agent_job():
            return await orchestrator.process_request_async(agent_name, request)

        job_id = await job_queue.submit(
            run_agent_job,
            name=f"{agent_name}_{request_payload.get('action', 'process')}",
            timeout=300.0,
        )

        return APIResponse(
            success=True,
            status="pending",
            data={
                "job_id": job_id,
                "agent": agent_name,
                "action": request_payload.get("action", "process"),
                "status_url": f"/api/v1/agents/jobs/{job_id}/status",
            },
            message=f"Job {job_id} submitted to {agent_name} agent",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting async job for {agent_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@router.get(
    "/jobs/{job_id}/status",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Poll async job status",
)
async def get_job_status(
    job_id: str,
    current_user: str = Depends(get_current_user),
) -> APIResponse:
    """
    Poll the status of an async job.

    Returns:
    - status: "pending", "completed", "failed", or "timeout"
    - result: Agent result when status="completed"
    - error: Error message when status="failed"
    """
    try:
        from socratic_system.events import JobQueue

        job_queue = JobQueue()
        job_result = job_queue.get_job_status(job_id)

        if job_result is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        is_complete = job_result.status.value in ("completed", "failed", "timeout")

        response_data = {
            "job_id": job_id,
            "status": job_result.status.value,
            "complete": is_complete,
            "started_at": job_result.started_at.isoformat() if job_result.started_at else None,
            "completed_at": job_result.completed_at.isoformat() if job_result.completed_at else None,
            "duration_ms": job_result.duration_ms,
        }

        # Add result or error if available
        if job_result.status.value == "completed":
            response_data["result"] = job_result.result
        elif job_result.status.value == "failed":
            response_data["error"] = job_result.error

        return APIResponse(
            success=job_result.status.value == "completed",
            status="success",
            data=response_data,
            message=f"Job status: {job_result.status.value}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get(
    "/jobs/batch",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get batch job statuses",
)
async def get_batch_job_status(
    job_ids: str = None,  # Comma-separated list
    current_user: str = Depends(get_current_user),
) -> APIResponse:
    """
    Get status for multiple jobs at once (comma-separated job_ids).

    Example: GET /api/v1/agents/jobs/batch?job_ids=job1,job2,job3
    """
    try:
        if not job_ids:
            raise HTTPException(status_code=400, detail="job_ids parameter required")

        from socratic_system.events import JobQueue

        job_queue = JobQueue()
        job_id_list = [jid.strip() for jid in job_ids.split(",")]

        statuses = {}
        for job_id in job_id_list:
            job_result = job_queue.get_job_status(job_id)
            if job_result:
                statuses[job_id] = {
                    "status": job_result.status.value,
                    "complete": job_result.status.value in ("completed", "failed", "timeout"),
                }

        return APIResponse(
            success=True,
            status="success",
            data={"jobs": statuses, "total": len(job_id_list), "found": len(statuses)},
            message=f"Retrieved status for {len(statuses)}/{len(job_id_list)} jobs",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch job status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
