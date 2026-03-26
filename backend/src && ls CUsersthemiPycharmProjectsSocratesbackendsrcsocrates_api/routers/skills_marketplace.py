"""
REST API routers for Phase 4: Skills Marketplace

Provides endpoints for:
- Skill registration and discovery
- Text search
- Marketplace statistics
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from socrates_api.models import (
    APIResponse,
    DiscoverSkillsRequest,
    MarketplaceStatsResponse,
    RegisterSkillRequest,
    SearchSkillsRequest,
    SkillMetadataResponse,
)

# Router
router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/register",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a skill in the marketplace",
    tags=["Marketplace"]
)
async def register_skill(
    request: RegisterSkillRequest,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Register a new skill in the marketplace.

    - **skill_id**: Unique identifier for the skill
    - **name**: Display name of the skill
    - **type**: Category/type of the skill
    - **effectiveness**: Performance score (0.0-1.0)
    - **agent**: Agent that created the skill
    - **tags**: Optional tags for categorization
    - **description**: Optional description
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Marketplace service not initialized")

    try:
        marketplace = await service_orchestrator.get_service("marketplace")
        if marketplace is None:
            raise HTTPException(status_code=503, detail="Marketplace service not available")

        skill_data = {
            "name": request.name,
            "type": request.type,
            "effectiveness": request.effectiveness,
            "agent": request.agent,
        }
        if request.tags:
            skill_data["tags"] = request.tags
        if request.description:
            skill_data["description"] = request.description

        success = await marketplace.register_skill(request.skill_id, skill_data)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register skill"
            )

        return APIResponse(
            success=True,
            status="created",
            message="Skill registered successfully",
            data={"skill_id": request.skill_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering skill: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/discover",
    response_model=APIResponse,
    summary="Discover skills in the marketplace",
    tags=["Marketplace"]
)
async def discover_skills(
    skill_type: Optional[str] = Query(None, description="Filter by skill type"),
    min_effectiveness: float = Query(0.0, description="Minimum effectiveness"),
    min_usage: int = Query(0, description="Minimum usage count"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    max_results: int = Query(10, description="Maximum results to return"),
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Discover skills matching criteria.

    Query parameters:
    - **skill_type**: Optional skill type filter
    - **min_effectiveness**: Minimum effectiveness score (0.0-1.0)
    - **tags**: Comma-separated list of tags
    - **max_results**: Maximum results to return (default: 10)
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Marketplace service not initialized")

    try:
        marketplace = await service_orchestrator.get_service("marketplace")
        if marketplace is None:
            raise HTTPException(status_code=503, detail="Marketplace service not available")

        tag_list = [t.strip() for t in tags.split(",")] if tags else None

        skills = await marketplace.discover_skills(
            skill_type=skill_type,
            min_effectiveness=min_effectiveness,
            min_usage=min_usage,
            tags=tag_list,
            max_results=max_results
        )

        return APIResponse(
            success=True,
            status="success",
            message=f"Found {len(skills)} skills",
            data={
                "count": len(skills),
                "skills": skills,
                "filters": {
                    "skill_type": skill_type,
                    "min_effectiveness": min_effectiveness,
                    "tags": tag_list
                }
            }
        )
    except Exception as e:
        logger.error(f"Error discovering skills: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/search",
    response_model=APIResponse,
    summary="Search skills by text",
    tags=["Marketplace"]
)
async def search_skills(
    q: str = Query(..., description="Search query"),
    max_results: int = Query(10, description="Maximum results"),
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Search for skills by name or description.

    - **q**: Search query (required)
    - **max_results**: Maximum results to return
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Marketplace service not initialized")

    try:
        marketplace = await service_orchestrator.get_service("marketplace")
        if marketplace is None:
            raise HTTPException(status_code=503, detail="Marketplace service not available")

        results = await marketplace.search_skills(q, max_results)

        return APIResponse(
            success=True,
            status="success",
            message=f"Found {len(results)} matching skills",
            data={
                "query": q,
                "count": len(results),
                "skills": results
            }
        )
    except Exception as e:
        logger.error(f"Error searching skills: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{skill_id}",
    response_model=APIResponse,
    summary="Get skill metadata",
    tags=["Marketplace"]
)
async def get_skill(
    skill_id: str,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get detailed metadata for a specific skill."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Marketplace service not initialized")

    try:
        marketplace = await service_orchestrator.get_service("marketplace")
        if marketplace is None:
            raise HTTPException(status_code=503, detail="Marketplace service not available")

        metadata = await marketplace.get_skill_metadata(skill_id)

        if metadata is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill {skill_id} not found"
            )

        return APIResponse(
            success=True,
            status="success",
            data=metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill metadata: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/by-agent/{agent_name}",
    response_model=APIResponse,
    summary="Get skills by agent",
    tags=["Marketplace"]
)
async def get_skills_by_agent(
    agent_name: str,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get all skills created by a specific agent."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Marketplace service not initialized")

    try:
        marketplace = await service_orchestrator.get_service("marketplace")
        if marketplace is None:
            raise HTTPException(status_code=503, detail="Marketplace service not available")

        skills = await marketplace.get_skills_by_agent(agent_name)

        return APIResponse(
            success=True,
            status="success",
            message=f"Found {len(skills)} skills by {agent_name}",
            data={
                "agent": agent_name,
                "count": len(skills),
                "skills": skills
            }
        )
    except Exception as e:
        logger.error(f"Error getting skills by agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/by-type/{skill_type}",
    response_model=APIResponse,
    summary="Get skills by type",
    tags=["Marketplace"]
)
async def get_skills_by_type(
    skill_type: str,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get all skills of a specific type."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Marketplace service not initialized")

    try:
        marketplace = await service_orchestrator.get_service("marketplace")
        if marketplace is None:
            raise HTTPException(status_code=503, detail="Marketplace service not available")

        skills = await marketplace.get_skills_by_type(skill_type)

        return APIResponse(
            success=True,
            status="success",
            message=f"Found {len(skills)} skills of type {skill_type}",
            data={
                "skill_type": skill_type,
                "count": len(skills),
                "skills": skills
            }
        )
    except Exception as e:
        logger.error(f"Error getting skills by type: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/top",
    response_model=APIResponse,
    summary="Get top-performing skills",
    tags=["Marketplace"]
)
async def get_top_skills(
    limit: int = Query(10, description="Number of top skills to return"),
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get the top-performing skills in the marketplace."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Marketplace service not initialized")

    try:
        marketplace = await service_orchestrator.get_service("marketplace")
        if marketplace is None:
            raise HTTPException(status_code=503, detail="Marketplace service not available")

        skills = await marketplace.get_top_skills(limit=limit)

        return APIResponse(
            success=True,
            status="success",
            message=f"Retrieved top {len(skills)} skills",
            data={
                "count": len(skills),
                "skills": skills
            }
        )
    except Exception as e:
        logger.error(f"Error getting top skills: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stats",
    response_model=APIResponse,
    summary="Get marketplace statistics",
    tags=["Marketplace"]
)
async def get_marketplace_stats(
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """Get comprehensive marketplace statistics."""
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Marketplace service not initialized")

    try:
        marketplace = await service_orchestrator.get_service("marketplace")
        if marketplace is None:
            raise HTTPException(status_code=503, detail="Marketplace service not available")

        stats = await marketplace.get_marketplace_stats()

        return APIResponse(
            success=True,
            status="success",
            message="Marketplace statistics retrieved",
            data=stats
        )
    except Exception as e:
        logger.error(f"Error getting marketplace stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
