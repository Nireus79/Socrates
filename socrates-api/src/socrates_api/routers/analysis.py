"""
Project Analysis API endpoints for Socrates.

Provides code validation, testing, review, and analysis functionality.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends

from socrates_api.models import SuccessResponse, ErrorResponse
from socrates_api.auth import get_current_user
from socrates_api.database import get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post(
    "/validate",
    response_model=SuccessResponse,
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
            db = get_database()
            project = db.load_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Call code validation agent - same as CLI uses
            result = orchestrator.process_request(
                "code_validation",
                {
                    "action": "validate_project",
                    "project": project,
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

        return SuccessResponse(
            success=True,
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
    "/maturity",
    response_model=SuccessResponse,
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
):
    """
    Assess project maturity for current or specified phase.

    Args:
        project_id: Project ID (required)
        phase: Phase to assess (discovery, analysis, design, implementation)
        current_user: Authenticated user

    Returns:
        SuccessResponse with maturity metrics from quality_controller
    """
    try:
        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Assessing maturity for project: {project_id}")

        # Load project
        db = get_database()
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
        result = orchestrator.process_request(
            "quality_controller",
            {
                "action": "calculate_maturity",
                "project": project,
                "phase": phase,
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

        return SuccessResponse(
            success=True,
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
    response_model=SuccessResponse,
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
):
    """
    Run tests for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with test results from code_validation agent
    """
    try:
        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Running tests for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call code_validation agent - same as CLI uses
        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "code_validation",
            {
                "action": "run_tests",
                "project": project,
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

        return SuccessResponse(
            success=True,
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
    response_model=SuccessResponse,
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
):
    """
    Analyze the project context and structure.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with structure/context analysis
    """
    try:
        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Analyzing structure for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call context analyzer - same as CLI uses
        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "context_analyzer",
            {
                "action": "analyze_context",
                "project": project,
            },
        )

        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to analyze"))

        structure_data = result

        record_event(
            "structure_analyzed",
            {
                "project_id": project_id,
            },
            user_id=current_user,
        )

        return SuccessResponse(
            success=True,
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
    response_model=SuccessResponse,
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
):
    """
    Get code statistics and quality summary for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with project statistics
    """
    try:
        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Getting code statistics for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call context analyzer to get project statistics
        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "context_analyzer",
            {
                "action": "get_statistics",
                "project": project,
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

        return SuccessResponse(
            success=True,
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
    response_model=SuccessResponse,
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
):
    """
    Generate improved code for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with generated code
    """
    try:
        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Auto-fixing issues for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call code generator to generate improved code
        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
            "code_generator",
            {
                "action": "generate_script",
                "project": project,
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

        return SuccessResponse(
            success=True,
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
    response_model=SuccessResponse,
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
):
    """
    Get comprehensive analysis report for a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with analysis report
    """
    try:
        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Generating analysis report for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call context analyzer to generate report/summary
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

        return SuccessResponse(
            success=True,
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
