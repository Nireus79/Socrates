"""
REST API routers for Phase 4: Skills Distribution

Provides endpoints for:
- Skill distribution and broadcasting
- Adoption tracking
- Performance comparison
- Distribution history
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from socrates_api.models import (
    APIResponse,
    BroadcastSkillRequest,
    DistributeSkillRequest,
    RecordAdoptionRequest,
)

# Router
router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/distribute",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Distribute skill to an agent",
    tags=["Distribution"]
)
async def distribute_skill(
    request: DistributeSkillRequest,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Distribute a skill from one agent to another.

    - **source_skill_id**: ID of the skill to distribute
    - **source_agent**: Agent that created the skill
    - **target_agent**: Agent receiving the skill
    - **skill_data**: Skill metadata and implementation
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Distribution service not initialized")

    try:
        distribution = await service_orchestrator.get_service("distribution")
        if distribution is None:
            raise HTTPException(status_code=503, detail="Distribution service not available")

        new_skill_id = await distribution.distribute_skill_to_agent(
            source_skill_id=request.source_skill_id,
            source_agent=request.source_agent,
            target_agent=request.target_agent,
            skill_data=request.skill_data
        )

        if new_skill_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to distribute skill"
            )

        return APIResponse(
            success=True,
            status="created",
            message="Skill distributed successfully",
            data={
                "source_skill_id": request.source_skill_id,
                "new_skill_id": new_skill_id,
                "target_agent": request.target_agent
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error distributing skill: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/broadcast",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Broadcast skill to multiple agents",
    tags=["Distribution"]
)
async def broadcast_skill(
    request: BroadcastSkillRequest,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Broadcast a skill to multiple agents simultaneously.

    - **source_skill_id**: ID of the skill to broadcast
    - **source_agent**: Agent that created the skill
    - **target_agents**: List of agents to receive the skill
    - **skill_data**: Skill metadata and implementation
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Distribution service not initialized")

    try:
        distribution = await service_orchestrator.get_service("distribution")
        if distribution is None:
            raise HTTPException(status_code=503, detail="Distribution service not available")

        results = await distribution.broadcast_skill_to_agents(
            source_skill_id=request.source_skill_id,
            source_agent=request.source_agent,
            target_agents=request.target_agents,
            skill_data=request.skill_data
        )

        successful = len([v for v in results.values() if v is not None])

        return APIResponse(
            success=True,
            status="created",
            message=f"Broadcast to {len(request.target_agents)} agents, {successful} successful",
            data={
                "source_skill_id": request.source_skill_id,
                "target_count": len(request.target_agents),
                "successful_count": successful,
                "results": results
            }
        )
    except Exception as e:
        logger.error(f"Error broadcasting skill: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{skill_id}/status",
    response_model=APIResponse,
    summary="Get skill adoption status",
    tags=["Distribution"]
)
async def get_adoption_status(
    skill_id: str,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get adoption status for a distributed skill."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Distribution service not initialized")

    try:
        distribution = await service_orchestrator.get_service("distribution")
        if distribution is None:
            raise HTTPException(status_code=503, detail="Distribution service not available")

        status = await distribution.get_adoption_status(skill_id)

        if status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No adoption data for skill {skill_id}"
            )

        return APIResponse(
            success=True,
            status="success",
            message=f"Adoption status for {skill_id}",
            data=status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adoption status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agent/{agent_name}/adoptions",
    response_model=APIResponse,
    summary="Get agent's adoptions",
    tags=["Distribution"]
)
async def get_agent_adoptions(
    agent_name: str,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get all skills adopted by a specific agent."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Distribution service not initialized")

    try:
        distribution = await service_orchestrator.get_service("distribution")
        if distribution is None:
            raise HTTPException(status_code=503, detail="Distribution service not available")

        adoptions = await distribution.get_agent_adoptions(agent_name)

        return APIResponse(
            success=True,
            status="success",
            message=f"Retrieved {len(adoptions)} adoptions for {agent_name}",
            data={
                "agent": agent_name,
                "adoption_count": len(adoptions),
                "adoptions": adoptions
            }
        )
    except Exception as e:
        logger.error(f"Error getting agent adoptions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/adoption/record",
    response_model=APIResponse,
    summary="Record adoption result",
    tags=["Distribution"]
)
async def record_adoption(
    request: RecordAdoptionRequest,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Record the result of a skill adoption attempt.

    - **source_skill_id**: ID of the skill being adopted
    - **target_agent**: Agent adopting the skill
    - **effectiveness**: Effectiveness score after adoption
    - **success**: Whether adoption was successful
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Distribution service not initialized")

    try:
        distribution = await service_orchestrator.get_service("distribution")
        if distribution is None:
            raise HTTPException(status_code=503, detail="Distribution service not available")

        success = await distribution.record_adoption_result(
            source_skill_id=request.source_skill_id,
            target_agent=request.target_agent,
            effectiveness=request.effectiveness,
            success=request.success
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to record adoption"
            )

        return APIResponse(
            success=True,
            status="success",
            message="Adoption recorded successfully",
            data={
                "skill_id": request.source_skill_id,
                "agent": request.target_agent,
                "effectiveness": request.effectiveness
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording adoption: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{skill_id}/performance",
    response_model=APIResponse,
    summary="Compare skill performance",
    tags=["Distribution"]
)
async def get_performance_comparison(
    skill_id: str,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Compare skill performance between original and distributed versions."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Distribution service not initialized")

    try:
        distribution = await service_orchestrator.get_service("distribution")
        if distribution is None:
            raise HTTPException(status_code=503, detail="Distribution service not available")

        comparison = await distribution.get_adoption_performance_comparison(skill_id)

        if comparison is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No performance data for skill {skill_id}"
            )

        return APIResponse(
            success=True,
            status="success",
            message=f"Performance comparison for {skill_id}",
            data=comparison
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance comparison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{skill_id}/lineage",
    response_model=APIResponse,
    summary="Get skill lineage",
    tags=["Distribution"]
)
async def get_skill_lineage(
    skill_id: str,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get the version history and lineage of a skill."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Distribution service not initialized")

    try:
        distribution = await service_orchestrator.get_service("distribution")
        if distribution is None:
            raise HTTPException(status_code=503, detail="Distribution service not available")

        lineage = await distribution.get_skill_lineage(skill_id)

        if not lineage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No lineage data for skill {skill_id}"
            )

        return APIResponse(
            success=True,
            status="success",
            message=f"Lineage for {skill_id}",
            data={
                "skill_id": skill_id,
                "version_count": len(lineage),
                "lineage": lineage
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill lineage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/history",
    response_model=APIResponse,
    summary="Get distribution history",
    tags=["Distribution"]
)
async def get_distribution_history(
    skill_id: str = Query(None, description="Filter by skill ID"),
    agent_name: str = Query(None, description="Filter by agent name"),
    limit: int = Query(100, description="Maximum results"),
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Get distribution history with optional filtering.

    - **skill_id**: Optional filter by skill ID
    - **agent_name**: Optional filter by agent name
    - **limit**: Maximum results to return
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Distribution service not initialized")

    try:
        distribution = await service_orchestrator.get_service("distribution")
        if distribution is None:
            raise HTTPException(status_code=503, detail="Distribution service not available")

        history = await distribution.get_distribution_history(
            skill_id=skill_id,
            agent_name=agent_name,
            limit=limit
        )

        return APIResponse(
            success=True,
            status="success",
            message=f"Retrieved {len(history)} distribution records",
            data={
                "count": len(history),
                "filters": {
                    "skill_id": skill_id,
                    "agent_name": agent_name
                },
                "history": history
            }
        )
    except Exception as e:
        logger.error(f"Error getting distribution history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/metrics",
    response_model=APIResponse,
    summary="Get distribution metrics",
    tags=["Distribution"]
)
async def get_distribution_metrics(
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get overall distribution metrics."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Distribution service not initialized")

    try:
        distribution = await service_orchestrator.get_service("distribution")
        if distribution is None:
            raise HTTPException(status_code=503, detail="Distribution service not available")

        metrics = await distribution.get_distribution_metrics()

        return APIResponse(
            success=True,
            status="success",
            message="Distribution metrics",
            data=metrics
        )
    except Exception as e:
        logger.error(f"Error getting distribution metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
