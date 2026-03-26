"""
REST API routers for Phase 4: Skills Analytics

Provides endpoints for:
- Metric tracking
- Performance analysis
- Ecosystem health monitoring
- Performance reports
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from socrates_api.models import (
    APIResponse,
    EcosystemHealthResponse,
    TrackMetricRequest,
)

# Router
router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/track",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Track a skill metric",
    tags=["Analytics"]
)
async def track_metric(
    request: TrackMetricRequest,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Track a metric for a skill.

    - **skill_id**: The skill being tracked
    - **agent_name**: Agent using the skill
    - **metric_name**: Name of the metric (e.g., "effectiveness", "usage_count")
    - **metric_value**: Numeric value of the metric
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Analytics service not initialized")

    try:
        analytics = await service_orchestrator.get_service("analytics")
        if analytics is None:
            raise HTTPException(status_code=503, detail="Analytics service not available")

        success = await analytics.track_skill_metric(
            skill_id=request.skill_id,
            agent_name=request.agent_name,
            metric_name=request.metric_name,
            metric_value=request.metric_value
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to track metric"
            )

        return APIResponse(
            success=True,
            status="created",
            message="Metric tracked successfully",
            data={
                "skill_id": request.skill_id,
                "metric_name": request.metric_name,
                "metric_value": request.metric_value
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking metric: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{skill_id}/performance",
    response_model=APIResponse,
    summary="Analyze skill performance",
    tags=["Analytics"]
)
async def analyze_performance(
    skill_id: str,
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Analyze performance metrics for a skill.

    Returns statistical summaries (average, min, max) for all tracked metrics.
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Analytics service not initialized")

    try:
        analytics = await service_orchestrator.get_service("analytics")
        if analytics is None:
            raise HTTPException(status_code=503, detail="Analytics service not available")

        analysis = await analytics.analyze_skill_performance(skill_id)

        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analytics data for skill {skill_id}"
            )

        return APIResponse(
            success=True,
            status="success",
            message=f"Performance analysis for {skill_id}",
            data=analysis
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/high-performers",
    response_model=APIResponse,
    summary="Get high-performing skills",
    tags=["Analytics"]
)
async def get_high_performers(
    min_effectiveness: float = Query(0.75, description="Minimum effectiveness threshold"),
    limit: int = Query(10, description="Maximum results to return"),
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Identify high-performing skills in the ecosystem.

    - **min_effectiveness**: Minimum effectiveness score (0.0-1.0)
    - **limit**: Maximum number of results to return
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Analytics service not initialized")

    try:
        analytics = await service_orchestrator.get_service("analytics")
        if analytics is None:
            raise HTTPException(status_code=503, detail="Analytics service not available")

        high_performers = await analytics.identify_high_performing_skills(
            min_effectiveness=min_effectiveness,
            limit=limit
        )

        return APIResponse(
            success=True,
            status="success",
            message=f"Found {len(high_performers)} high-performing skills",
            data={
                "count": len(high_performers),
                "min_effectiveness": min_effectiveness,
                "high_performers": high_performers
            }
        )
    except Exception as e:
        logger.error(f"Error getting high performers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ecosystem-health",
    response_model=APIResponse,
    summary="Get ecosystem health",
    tags=["Analytics"]
)
async def get_ecosystem_health(
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Get overall ecosystem health metrics.

    Returns:
    - **total_skills**: Number of skills in ecosystem
    - **average_effectiveness**: Average effectiveness score
    - **ecosystem_health**: Health status (excellent, good, fair, poor, no_data)
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Analytics service not initialized")

    try:
        analytics = await service_orchestrator.get_service("analytics")
        if analytics is None:
            raise HTTPException(status_code=503, detail="Analytics service not available")

        health = await analytics.get_ecosystem_health()

        return APIResponse(
            success=True,
            status="success",
            message=f"Ecosystem health: {health.get('ecosystem_health', 'unknown')}",
            data=health
        )
    except Exception as e:
        logger.error(f"Error getting ecosystem health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/report",
    response_model=APIResponse,
    summary="Get performance report",
    tags=["Analytics"]
)
async def get_performance_report(
    service_orchestrator = Depends(lambda: __import__("socrates_api.main", fromlist=["app_state"]).app_state.get("service_orchestrator"))
):
    """
    Get comprehensive performance report.

    Includes ecosystem health, high performers, and recommendations.
    """
    if service_orchestrator is None:
        raise HTTPException(status_code=503, detail="Analytics service not initialized")

    try:
        analytics = await service_orchestrator.get_service("analytics")
        if analytics is None:
            raise HTTPException(status_code=503, detail="Analytics service not available")

        report = await analytics.get_performance_report()

        return APIResponse(
            success=True,
            status="success",
            message="Performance report generated",
            data=report
        )
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
