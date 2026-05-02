"""
Project Analysis API endpoints for Socrates.

Provides code validation, testing, review, and analysis functionality.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.auth.project_access import check_project_access
from socrates_api.database import get_database
from socrates_api.models import APIResponse, ErrorResponse
from socratic_system.database import ProjectDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post(
    "/validate",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate code",
    responses={
        200: {"description": "Validation completed"},
        400: {"description": "Invalid input", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def validate_code(
    code: Optional[str] = None,
    language: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Validate code for syntax and style issues.

    Can validate either:
    - Inline code (provide code and language)
    - Project code (provide project_id)

    Args:
        code: Code to validate
        language: Programming language
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with validation results
    """
    try:
        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        orchestrator = get_orchestrator()

        if project_id:
            logger.info(f"Validating code for project: {project_id}")
            # Load project from database
            project = db.load_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Check if project has source files (from GitHub import)
            if not project.repository_url:
                raise HTTPException(
                    status_code=400,
                    detail="Project must be imported from GitHub or have source files for code validation",
                )

            # For now, get project path from repository if available
            # In the future, this can export project files for analysis
            project_path = project.repository_url or project_id

            # Call code validation agent - same as CLI uses
            result = await orchestrator.agent_bus.send_request(
                "code_validation",
                {
                    "action": "validate_project",
                    "project_path": project_path,
                },
            )

            if result["status"] != "success":
                raise HTTPException(
                    status_code=500, detail=result.get("message", "Failed to validate")
                )

            validation_results = result

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either code+language or project_id",
            )

        # Record event for analytics
        record_event(
            "code_validated",
            {
                "project_id": project_id,
                "language": language,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
            status="success",
            message="Code validation completed",
            data=validation_results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate code: {str(e)}",
        )


@router.post(
    "/{project_id}/maturity",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess code maturity",
    responses={
        200: {"description": "Maturity assessment completed"},
        400: {"description": "Invalid input", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def assess_maturity(
    project_id: str,
    phase: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Assess project maturity for current or specified phase.

    Args:
        project_id: Project ID (required)
        phase: Phase to assess (discovery, analysis, design, implementation)
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with maturity metrics from quality_controller
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Assessing maturity for project: {project_id}")

        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Determine phase
        if not phase:
            phase = project.phase

        # Validate phase
        valid_phases = ["discovery", "analysis", "design", "implementation"]
        if phase not in valid_phases:
            raise HTTPException(
                status_code=400, detail=f"Invalid phase. Must be one of: {', '.join(valid_phases)}"
            )

        orchestrator = get_orchestrator()

        # Call quality_controller to calculate maturity - same as CLI does
        result = await orchestrator.agent_bus.send_request(
            "quality_controller",
            {
                "action": "calculate_maturity",
                "project": project,
                "phase": phase,
                "current_user": current_user,
            },
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to calculate maturity")
            )

        maturity_data = result.get("maturity", {})

        # Record event
        record_event(
            "maturity_assessed",
            {
                "project_id": project_id,
                "phase": phase,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
            status="success",
            message=f"Maturity assessment for {phase} phase",
            data=maturity_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing maturity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess maturity: {str(e)}",
        )


@router.post(
    "/test",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Run tests for project",
    responses={
        200: {"description": "Tests completed"},
        400: {"description": "Invalid project ID", "model": ErrorResponse},
    },
)
async def run_tests(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Run tests for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with test results from code_validation agent
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Running tests for project: {project_id}")

        # Load project
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if project has source files (from GitHub import)
        if not project.repository_url:
            raise HTTPException(
                status_code=400,
                detail="Project must be imported from GitHub or have source files for testing",
            )

        project_path = project.repository_url or project_id

        # Call code_validation agent - same as CLI uses
        orchestrator = get_orchestrator()
        result = await orchestrator.agent_bus.send_request(
            "code_validation",
            {
                "action": "run_tests",
                "project_path": project_path,
            },
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to run tests")
            )

        test_results = result

        record_event(
            "tests_executed",
            {
                "project_id": project_id,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
            status="success",
            message="Tests completed",
            data=test_results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run tests: {str(e)}",
        )


@router.post(
    "/structure",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze project structure",
    responses={
        200: {"description": "Analysis completed"},
        400: {"description": "Invalid project ID", "model": ErrorResponse},
    },
)
async def analyze_structure(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Analyze the project context and structure.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with structure/context analysis
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Analyzing structure for project: {project_id}")

        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call context analyzer - same as CLI uses
        orchestrator = get_orchestrator()
        result = await orchestrator.agent_bus.send_request(
            "context_analyzer",
            {
                "action": "analyze_context",
                "project": project,
                "current_user": current_user,
            },
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to analyze structure")
            )

        structure_data = result

        record_event(
            "structure_analyzed",
            {
                "project_id": project_id,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
            status="success",
            message="Context analysis completed",
            data=structure_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing structure: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze structure: {str(e)}",
        )


@router.post(
    "/review",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform code review",
    responses={
        200: {"description": "Code review completed"},
        400: {"description": "Invalid project ID", "model": ErrorResponse},
    },
)
async def review_code(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get code statistics and quality summary for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with project statistics
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Getting code statistics for project: {project_id}")

        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call context analyzer to get project statistics
        orchestrator = get_orchestrator()
        result = await orchestrator.agent_bus.send_request(
            "context_analyzer",
            {
                "action": "analyze_context",
                "project": project,
                "current_user": current_user,
            },
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to get statistics")
            )

        stats = result

        record_event(
            "code_statistics_requested",
            {
                "project_id": project_id,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
            status="success",
            message="Code statistics retrieved",
            data=stats,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting code statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get code statistics: {str(e)}",
        )


@router.post(
    "/fix",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Auto-fix code issues",
    responses={
        200: {"description": "Auto-fix completed"},
        400: {"description": "Invalid project ID", "model": ErrorResponse},
    },
)
async def auto_fix_issues(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Generate improved code for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with generated code
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Auto-fixing issues for project: {project_id}")

        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call code generator to generate improved code
        orchestrator = get_orchestrator()
        result = await orchestrator.agent_bus.send_request(
            "code_generator",
            {
                "action": "generate_script",
                "project": project,
                "current_user": current_user,
            },
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to generate fixes")
            )

        fix_results = result

        record_event(
            "code_generated",
            {
                "project_id": project_id,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
            status="success",
            message="Code generation completed",
            data=fix_results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying fixes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply fixes: {str(e)}",
        )


@router.get(
    "/report/{project_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get analysis report",
    responses={
        200: {"description": "Report retrieved"},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_analysis_report(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get comprehensive analysis report for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with analysis report
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Generating analysis report for project: {project_id}")

        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call context analyzer to generate report/summary
        orchestrator = get_orchestrator()
        result = await orchestrator.agent_bus.send_request(
            "context_analyzer",
            {
                "action": "generate_summary",
                "project": project,
                "current_user": current_user,
            },
        )

        if result["status"] != "success":
            raise HTTPException(
                status_code=500, detail=result.get("message", "Failed to generate report")
            )

        report = result

        record_event(
            "report_generated",
            {
                "project_id": project_id,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
            status="success",
            message="Analysis report generated",
            data=report,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        )


# Phase 3: Event-driven background processing polling endpoints
# Clients poll these endpoints to retrieve cached analysis results


@router.get(
    "/{project_id}/background/status",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get background analysis status",
    responses={
        200: {"description": "Status retrieved"},
        202: {"description": "Analysis still processing"},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_background_analysis_status(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get the status of background analyses (quality, conflicts, insights).

    Returns status for each analysis type without full results.
    Use this for polling to check if analysis is complete.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with status dict containing:
        - quality: "pending" | "processing" | "completed" | "failed"
        - conflicts: "pending" | "processing" | "completed" | "failed"
        - insights: "pending" | "processing" | "completed" | "failed"
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.main import get_orchestrator

        logger.info(f"Getting background analysis status for project: {project_id}")

        # Load project to verify it exists
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        orchestrator = get_orchestrator()

        # Get status from cache
        cache = orchestrator.cache
        job_tracker = orchestrator.job_tracker

        # Check status of each analysis
        status_dict = {
            "quality": "pending",
            "conflicts": "pending",
            "insights": "pending",
        }

        # Get jobs for this project
        project_jobs = job_tracker.get_project_jobs(project_id)

        # Map job types to analysis names
        for job in project_jobs:
            if "quality" in job.job_id:
                status_dict["quality"] = job.status.value
            elif "conflict" in job.job_id:
                status_dict["conflicts"] = job.status.value
            elif "insight" in job.job_id:
                status_dict["insights"] = job.status.value

        # Check if any are still processing
        any_processing = any(s == "processing" for s in status_dict.values())
        response_status = 202 if any_processing else 200

        return APIResponse(
            success=True,
            status="success",
            message="Background analysis status retrieved",
            data=status_dict,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting background analysis status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get background analysis status: {str(e)}",
        )


@router.get(
    "/{project_id}/background/quality",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get cached quality analysis",
    responses={
        200: {"description": "Quality analysis retrieved"},
        202: {"description": "Analysis still processing"},
        404: {"description": "Project or analysis not found", "model": ErrorResponse},
    },
)
async def get_cached_quality_analysis(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get cached quality analysis results for a project.

    Returns HTTP 202 if analysis is still processing.
    Returns HTTP 200 if analysis is complete.
    Returns HTTP 404 if project not found or analysis never started.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with quality analysis results
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.main import get_orchestrator

        logger.info(f"Getting cached quality analysis for project: {project_id}")

        # Load project to verify it exists
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        orchestrator = get_orchestrator()
        cache = orchestrator.cache

        # Try to get cached result
        cache_key = f"analysis:quality:{project_id}"
        quality_result = cache.get(cache_key)

        if quality_result is None:
            # Check if job is still processing
            project_jobs = orchestrator.job_tracker.get_project_jobs(project_id)
            quality_job = next((j for j in project_jobs if "quality" in j.job_id), None)

            if quality_job and quality_job.status.value == "processing":
                return APIResponse(
                    success=False,
                    status="processing",
                    message="Quality analysis still processing",
                    data={"status": "processing", "progress": quality_job.progress},
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Quality analysis not found. No cached results available.",
                )

        return APIResponse(
            success=True,
            status="success",
            message="Quality analysis retrieved from cache",
            data=quality_result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cached quality analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality analysis: {str(e)}",
        )


@router.get(
    "/{project_id}/background/conflicts",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get cached conflict analysis",
    responses={
        200: {"description": "Conflict analysis retrieved"},
        202: {"description": "Analysis still processing"},
        404: {"description": "Project or analysis not found", "model": ErrorResponse},
    },
)
async def get_cached_conflict_analysis(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get cached conflict analysis results for a project.

    Returns HTTP 202 if analysis is still processing.
    Returns HTTP 200 if analysis is complete.
    Returns HTTP 404 if project not found or analysis never started.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with conflict analysis results
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.main import get_orchestrator

        logger.info(f"Getting cached conflict analysis for project: {project_id}")

        # Load project to verify it exists
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        orchestrator = get_orchestrator()
        cache = orchestrator.cache

        # Try to get cached result
        cache_key = f"analysis:conflicts:{project_id}"
        conflicts_result = cache.get(cache_key)

        if conflicts_result is None:
            # Check if job is still processing
            project_jobs = orchestrator.job_tracker.get_project_jobs(project_id)
            conflict_job = next((j for j in project_jobs if "conflict" in j.job_id), None)

            if conflict_job and conflict_job.status.value == "processing":
                return APIResponse(
                    success=False,
                    status="processing",
                    message="Conflict analysis still processing",
                    data={"status": "processing", "progress": conflict_job.progress},
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Conflict analysis not found. No cached results available.",
                )

        return APIResponse(
            success=True,
            status="success",
            message="Conflict analysis retrieved from cache",
            data=conflicts_result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cached conflict analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conflict analysis: {str(e)}",
        )


@router.get(
    "/{project_id}/background/insights",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get cached insight analysis",
    responses={
        200: {"description": "Insight analysis retrieved"},
        202: {"description": "Analysis still processing"},
        404: {"description": "Project or analysis not found", "model": ErrorResponse},
    },
)
async def get_cached_insight_analysis(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get cached insight analysis results for a project.

    Returns HTTP 202 if analysis is still processing.
    Returns HTTP 200 if analysis is complete.
    Returns HTTP 404 if project not found or analysis never started.

    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database connection

    Returns:
        SuccessResponse with insight analysis results
    """
    try:
        # Check project access - requires viewer or better
        await check_project_access(project_id, current_user, db, min_role="viewer")

        from socrates_api.main import get_orchestrator

        logger.info(f"Getting cached insight analysis for project: {project_id}")

        # Load project to verify it exists
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        orchestrator = get_orchestrator()
        cache = orchestrator.cache

        # Try to get cached result
        cache_key = f"analysis:insights:{project_id}"
        insights_result = cache.get(cache_key)

        if insights_result is None:
            # Check if job is still processing
            project_jobs = orchestrator.job_tracker.get_project_jobs(project_id)
            insight_job = next((j for j in project_jobs if "insight" in j.job_id), None)

            if insight_job and insight_job.status.value == "processing":
                return APIResponse(
                    success=False,
                    status="processing",
                    message="Insight analysis still processing",
                    data={"status": "processing", "progress": insight_job.progress},
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Insight analysis not found. No cached results available.",
                )

        return APIResponse(
            success=True,
            status="success",
            message="Insight analysis retrieved from cache",
            data=insights_result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cached insight analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insight analysis: {str(e)}",
        )
