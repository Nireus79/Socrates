"""
Project Analysis API endpoints for Socrates.

Provides code validation, testing, review, and analysis functionality.
"""

import logging
from socrates_api.models_local import ProjectContext, AnalyzerIntegration
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.auth.project_access import check_project_access
from socrates_api.database import get_database, LocalDatabase
from socrates_api.models import APIResponse, ErrorResponse
from socrates_api.models_local import User
# Database import replaced with local module

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

            # Check if project has source files (from GitHub import)
            if not project.repository_url:
                raise HTTPException(
                    status_code=400,
                    detail="Project must be imported from GitHub or have source files for code validation"
                )

            # For now, get project path from repository if available
            # In the future, this can export project files for analysis
            project_path = project.repository_url or project_id

            # Call code validation agent - same as CLI uses
            result = orchestrator.process_request(
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
            detail="Operation failed. Please try again later.",
        )


@router.post(
    "/maturity",
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
    db: LocalDatabase = Depends(get_database),
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
        result = orchestrator.process_request(
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
            detail="Operation failed. Please try again later.",
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
    db: LocalDatabase = Depends(get_database),
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
                detail="Project must be imported from GitHub or have source files for testing"
            )

        project_path = project.repository_url or project_id

        # Call code_validation agent - same as CLI uses
        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
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
            detail="Operation failed. Please try again later.",
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
    db: LocalDatabase = Depends(get_database),
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
                "current_user": current_user,
            },
        )

        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to analyze structure"))

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
            detail="Operation failed. Please try again later.",
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
    db: LocalDatabase = Depends(get_database),
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
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call context analyzer to get project statistics
        orchestrator = get_orchestrator()
        result = orchestrator.process_request(
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
            detail="Operation failed. Please try again later.",
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
    db: LocalDatabase = Depends(get_database),
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
        result = orchestrator.process_request(
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
            detail="Operation failed. Please try again later.",
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
    db: LocalDatabase = Depends(get_database),
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
            detail="Operation failed. Please try again later.",
        )


@router.post(
    "/code",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze code",
    responses={
        200: {"description": "Code analysis completed"},
        400: {"description": "Invalid input", "model": ErrorResponse},
        503: {"description": "Analyzer unavailable", "model": ErrorResponse},
    },
)
async def analyze_code(
    code: str,
    language: str = "python",
    current_user: str = Depends(get_current_user),
):
    """
    Perform comprehensive code analysis.

    Analyzes code for quality, security issues, and performance problems using
    the socratic-analyzer library.

    Args:
        code: Source code to analyze
        language: Programming language (python, javascript, typescript, etc.)
        current_user: Authenticated user

    Returns:
        SuccessResponse with analysis results including:
        - Overall quality score (0-100)
        - Quality metrics (complexity, maintainability, etc.)
        - Security issues found
        - Performance issues and recommendations
        - Architecture insights
    """
    try:
        from socrates_api.routers.events import record_event

        logger.info(f"Analyzing {language} code for user: {current_user}")

        # Initialize analyzer and run comprehensive analysis using socratic-analyzer library
        analyzer = AnalyzerIntegration()
        analysis_result = analyzer.analyze_code(code, language=language)

        # Record event
        try:
            record_event(
                "code_analyzed",
                {
                    "language": language,
                    "score": analysis_result.get("overall_score", 0),
                },
                user_id=current_user,
            )
        except Exception as e:
            logger.warning(f"Failed to record event: {e}")

        return APIResponse(
            success=True,
            status="success",
            message=f"Code analysis completed (Score: {analysis_result.get('overall_score', 0):.1f}/100)",
            data=analysis_result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Operation failed. Please try again later.",
        )


@router.post(
    "/metrics",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate code metrics",
    responses={
        200: {"description": "Metrics calculated"},
        400: {"description": "Invalid code", "model": ErrorResponse},
        503: {"description": "Analyzer not available", "model": ErrorResponse},
    },
)
async def calculate_metrics(
    code: str,
    language: str = "python",
    current_user: str = Depends(get_current_user),
) -> APIResponse:
    """
    Calculate detailed code metrics.

    Analyzes code for complexity, maintainability, coverage, and duplication.

    Args:
        code: Source code to analyze
        language: Programming language

    Returns:
        APIResponse with detailed metrics
    """
    try:
        analyzer = AnalyzerIntegration()
        if not analyzer.available:
            raise HTTPException(status_code=503, detail="Analyzer not available")

        metrics = analyzer.analyze_metrics(code, language)

        return APIResponse(
            success=True,
            status="success",
            message="Code metrics calculated",
            data=metrics,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        raise HTTPException(status_code=500, detail="Operation failed")


@router.post(
    "/health",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate project health score",
    responses={
        200: {"description": "Health score calculated"},
        400: {"description": "Invalid code", "model": ErrorResponse},
        503: {"description": "Analyzer not available", "model": ErrorResponse},
    },
)
async def calculate_health_score(
    code: str,
    language: str = "python",
    current_user: str = Depends(get_current_user),
) -> APIResponse:
    """
    Calculate overall project health score.

    Combines metrics, security, and performance analysis into a health grade.

    Args:
        code: Project code to analyze
        language: Primary language

    Returns:
        APIResponse with health score (0-100) and grade (A-F)
    """
    try:
        analyzer = AnalyzerIntegration()
        health = analyzer.calculate_health_score(code, language)

        return APIResponse(
            success=True,
            status="success",
            message=f"Project health: {health.get('grade')} ({health.get('score')}/100)",
            data=health,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating health: {e}")
        raise HTTPException(status_code=500, detail="Operation failed")


@router.post(
    "/improvements",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get improvement suggestions",
    responses={
        200: {"description": "Suggestions generated"},
        400: {"description": "Invalid code", "model": ErrorResponse},
        503: {"description": "Analyzer not available", "model": ErrorResponse},
    },
)
async def get_improvements(
    code: str,
    language: str = "python",
    current_user: str = Depends(get_current_user),
) -> APIResponse:
    """
    Get actionable code improvement suggestions.

    Analyzes code and provides specific recommendations for improvement.

    Args:
        code: Code to analyze
        language: Programming language

    Returns:
        APIResponse with improvement suggestions
    """
    try:
        analyzer = AnalyzerIntegration()
        suggestions = analyzer.get_improvement_suggestions(code, language)

        return APIResponse(
            success=True,
            status="success",
            message=f"Found {len(suggestions)} improvement opportunities",
            data={"suggestions": suggestions, "count": len(suggestions)},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting improvements: {e}")
        raise HTTPException(status_code=500, detail="Operation failed")
