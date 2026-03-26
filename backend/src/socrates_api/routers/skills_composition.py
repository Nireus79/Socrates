"""
REST API routers for Phase 4: Skills Composition

Provides endpoints for:
- Composition creation and management
- Composition execution (sequential, parallel, conditional)
- Parameter mapping
- Error handling
- Metrics and history
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from socrates_api.models import (
    APIResponse,
    AddParameterMappingRequest,
    CreateCompositionRequest,
    ExecuteCompositionRequest,
)

# Router
router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/create",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a skill composition",
    tags=["Composition"]
)
async def create_composition(
    request: CreateCompositionRequest,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Create a new skill composition.

    - **composition_id**: Unique identifier for the composition
    - **name**: Display name
    - **skills**: List of skill IDs in execution order
    - **execution_type**: "sequential", "parallel", or "conditional"
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Composition service not initialized")

    try:
        composer = await service_orchestrator.get_service("composition")
        if composer is None:
            raise HTTPException(status_code=503, detail="Composition service not available")

        success = await composer.create_composition(
            composition_id=request.composition_id,
            name=request.name,
            skills=request.skills,
            execution_type=request.execution_type
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create composition"
            )

        return APIResponse(
            success=True,
            status="created",
            message="Composition created successfully",
            data={
                "composition_id": request.composition_id,
                "name": request.name,
                "skill_count": len(request.skills)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating composition: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{composition_id}/mapping",
    response_model=APIResponse,
    summary="Add parameter mapping",
    tags=["Composition"]
)
async def add_parameter_mapping(
    composition_id: str,
    request: AddParameterMappingRequest,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Add parameter mapping between skills in a composition.

    Maps output from one skill to input of another.
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Composition service not initialized")

    try:
        composer = await service_orchestrator.get_service("composition")
        if composer is None:
            raise HTTPException(status_code=503, detail="Composition service not available")

        success = await composer.add_parameter_mapping(
            composition_id=composition_id,
            from_skill_index=request.from_skill_index,
            from_param=request.from_param,
            to_skill_index=request.to_skill_index,
            to_param=request.to_param
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add parameter mapping"
            )

        return APIResponse(
            success=True,
            status="success",
            message="Parameter mapping added",
            data={
                "composition_id": composition_id,
                "mapping": f"{request.from_skill_index}.{request.from_param} -> {request.to_skill_index}.{request.to_param}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding parameter mapping: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{composition_id}/condition",
    response_model=APIResponse,
    summary="Add execution condition",
    tags=["Composition"]
)
async def add_condition(
    composition_id: str,
    skill_index: int = Query(..., description="Index of skill to add condition to"),
    condition_type: str = Query(..., description="Type of condition: if_success, if_failure, etc"),
    condition_value: Any = Query(..., description="Condition value"),
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Add execution condition to a skill in the composition.

    Allows conditional execution based on results of previous skills.
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Composition service not initialized")

    try:
        composer = await service_orchestrator.get_service("composition")
        if composer is None:
            raise HTTPException(status_code=503, detail="Composition service not available")

        success = await composer.add_condition(
            composition_id=composition_id,
            skill_index=skill_index,
            condition_type=condition_type,
            condition_value=condition_value
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add condition"
            )

        return APIResponse(
            success=True,
            status="success",
            message="Condition added",
            data={
                "composition_id": composition_id,
                "skill_index": skill_index,
                "condition_type": condition_type
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding condition: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{composition_id}/error-handler",
    response_model=APIResponse,
    summary="Add error handler",
    tags=["Composition"]
)
async def add_error_handler(
    composition_id: str,
    skill_id: str = Query(..., description="Skill ID to add handler for"),
    handler: str = Query(..., description="Handler type: retry, fallback, skip"),
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Add error handler to a skill in the composition.

    Specifies what to do if a skill fails (retry, fallback, skip).
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Composition service not initialized")

    try:
        composer = await service_orchestrator.get_service("composition")
        if composer is None:
            raise HTTPException(status_code=503, detail="Composition service not available")

        success = await composer.add_error_handler(
            composition_id=composition_id,
            skill_id=skill_id,
            handler=handler
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add error handler"
            )

        return APIResponse(
            success=True,
            status="success",
            message="Error handler added",
            data={
                "composition_id": composition_id,
                "skill_id": skill_id,
                "handler": handler
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding error handler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{composition_id}/execute",
    response_model=APIResponse,
    summary="Execute composition",
    tags=["Composition"]
)
async def execute_composition(
    composition_id: str,
    request: ExecuteCompositionRequest,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Execute a skill composition.

    Executes all skills according to the composition's execution type.
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Composition service not initialized")

    try:
        composer = await service_orchestrator.get_service("composition")
        if composer is None:
            raise HTTPException(status_code=503, detail="Composition service not available")

        result = await composer.execute_composition(
            composition_id=composition_id,
            initial_context=request.initial_context,
            skill_executor=None  # API doesn't provide custom executor
        )

        return APIResponse(
            success=result.get("status") == "success",
            status=result.get("status", "error"),
            message=result.get("error") or "Composition executed successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error executing composition: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{composition_id}",
    response_model=APIResponse,
    summary="Get composition details",
    tags=["Composition"]
)
async def get_composition(
    composition_id: str,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get detailed information about a composition."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Composition service not initialized")

    try:
        composer = await service_orchestrator.get_service("composition")
        if composer is None:
            raise HTTPException(status_code=503, detail="Composition service not available")

        composition = await composer.get_composition(composition_id)

        if composition is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Composition {composition_id} not found"
            )

        return APIResponse(
            success=True,
            status="success",
            data=composition
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting composition: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{composition_id}/metrics",
    response_model=APIResponse,
    summary="Get composition metrics",
    tags=["Composition"]
)
async def get_composition_metrics(
    composition_id: str,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get execution metrics for a composition."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Composition service not initialized")

    try:
        composer = await service_orchestrator.get_service("composition")
        if composer is None:
            raise HTTPException(status_code=503, detail="Composition service not available")

        metrics = await composer.get_composition_metrics(composition_id)

        if metrics is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No metrics for composition {composition_id}"
            )

        return APIResponse(
            success=True,
            status="success",
            data=metrics
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting composition metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{composition_id}/history",
    response_model=APIResponse,
    summary="Get execution history",
    tags=["Composition"]
)
async def get_execution_history(
    composition_id: str,
    limit: int = Query(50, description="Maximum results"),
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get execution history for a composition."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Composition service not initialized")

    try:
        composer = await service_orchestrator.get_service("composition")
        if composer is None:
            raise HTTPException(status_code=503, detail="Composition service not available")

        history = await composer.get_execution_history(
            composition_id=composition_id,
            limit=limit
        )

        return APIResponse(
            success=True,
            status="success",
            data={
                "composition_id": composition_id,
                "count": len(history),
                "executions": history
            }
        )
    except Exception as e:
        logger.error(f"Error getting execution history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/list",
    response_model=APIResponse,
    summary="List all compositions",
    tags=["Composition"]
)
async def list_compositions(
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get list of all compositions."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Composition service not initialized")

    try:
        composer = await service_orchestrator.get_service("composition")
        if composer is None:
            raise HTTPException(status_code=503, detail="Composition service not available")

        compositions = await composer.list_compositions()

        return APIResponse(
            success=True,
            status="success",
            data={
                "count": len(compositions),
                "compositions": compositions
            }
        )
    except Exception as e:
        logger.error(f"Error listing compositions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stats",
    response_model=APIResponse,
    summary="Get composition statistics",
    tags=["Composition"]
)
async def get_composition_stats(
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get overall composition performance statistics."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Composition service not initialized")

    try:
        composer = await service_orchestrator.get_service("composition")
        if composer is None:
            raise HTTPException(status_code=503, detail="Composition service not available")

        stats = await composer.get_composition_performance_stats()

        return APIResponse(
            success=True,
            status="success",
            data=stats
        )
    except Exception as e:
        logger.error(f"Error getting composition stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
