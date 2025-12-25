"""
Project Analysis API endpoints for Socrates.

Provides code validation, testing, review, and analysis functionality.
"""

import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends

from socratic_system.database import ProjectDatabaseV2
from socrates_api.models import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])


def get_database() -> ProjectDatabaseV2:
    """Get database instance."""
    data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
    db_path = os.path.join(data_dir, "projects.db")
    return ProjectDatabaseV2(db_path)


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

        if code and language:
            logger.info(f"Validating inline code ({language})")
            # Call code validation agent via orchestrator
            result = await orchestrator.process_request_async(
                "code_validation",
                {
                    "action": "validate",
                    "code": code,
                    "language": language,
                }
            )
            validation_results = result.get("data", {})

        elif project_id:
            logger.info(f"Validating code for project: {project_id}")
            # Load project from database
            db = get_database()
            project = db.load_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Call code validation agent via orchestrator
            result = await orchestrator.process_request_async(
                "code_validation",
                {
                    "action": "validate_project",
                    "project": project,
                }
            )
            validation_results = result.get("data", {})

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either code+language or project_id",
            )

        # Record event for analytics
        record_event("code_validated", {
            "project_id": project_id,
            "language": language,
        }, user_id=current_user)

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
    code: Optional[str] = None,
    language: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
):
    """
    Assess code maturity and quality metrics.

    Args:
        code: Code to assess
        language: Programming language
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with maturity assessment
    """
    try:
        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info("Assessing code maturity")
        orchestrator = get_orchestrator()

        if project_id:
            # Load project and assess maturity
            db = get_database()
            project = db.load_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            result = await orchestrator.process_request_async(
                "quality_controller",
                {
                    "action": "assess_maturity",
                    "project": project,
                }
            )
            maturity_assessment = result.get("data", {})
        elif code and language:
            # Assess inline code maturity
            result = await orchestrator.process_request_async(
                "quality_controller",
                {
                    "action": "assess_code",
                    "code": code,
                    "language": language,
                }
            )
            maturity_assessment = result.get("data", {})
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either code+language or project_id",
            )

        # Record event
        record_event("maturity_assessed", {
            "project_id": project_id,
            "language": language,
        }, user_id=current_user)

        return SuccessResponse(
            success=True,
            message="Maturity assessment completed",
            data=maturity_assessment,
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
    test_type: str = "all",
    current_user: str = Depends(get_current_user),
):
    """
    Run tests for a project.

    Args:
        project_id: Project ID
        test_type: Type of tests (unit, integration, all)
        current_user: Authenticated user

    Returns:
        SuccessResponse with test results
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

        # Call code validation agent to run tests via orchestrator
        orchestrator = get_orchestrator()
        result = await orchestrator.process_request_async(
            "code_validation",
            {
                "action": "run_tests",
                "project": project,
                "test_type": test_type,
            }
        )

        test_results = result.get("data", {})

        record_event("tests_executed", {
            "project_id": project_id,
            "test_type": test_type,
            "passed": test_results.get("passed", 0),
            "failed": test_results.get("failed", 0),
        }, user_id=current_user)

        return SuccessResponse(
            success=True,
            message=f"{test_type} tests completed",
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
    Analyze the code structure and architecture of a project.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with structure analysis
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

        # Call context analyzer via orchestrator
        orchestrator = get_orchestrator()
        result = await orchestrator.process_request_async(
            "context_analyzer",
            {
                "action": "analyze_structure",
                "project": project,
            }
        )

        structure_analysis = result.get("data", {})

        record_event("structure_analyzed", {
            "project_id": project_id,
        }, user_id=current_user)

        return SuccessResponse(
            success=True,
            message="Code structure analysis completed",
            data=structure_analysis,
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
    review_type: str = "full",
    current_user: str = Depends(get_current_user),
):
    """
    Perform automated code review on project.

    Args:
        project_id: Project ID
        review_type: Type of review (full, quick, security, performance)
        current_user: Authenticated user

    Returns:
        SuccessResponse with review findings
    """
    try:
        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Reviewing code for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call quality controller via orchestrator for code review
        orchestrator = get_orchestrator()
        result = await orchestrator.process_request_async(
            "quality_controller",
            {
                "action": "review_code",
                "project": project,
                "review_type": review_type,
            }
        )

        review_findings = result.get("data", {})

        record_event("code_reviewed", {
            "project_id": project_id,
            "review_type": review_type,
        }, user_id=current_user)

        return SuccessResponse(
            success=True,
            message=f"Code review completed ({review_type})",
            data=review_findings,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review code: {str(e)}",
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
    issue_types: Optional[List[str]] = None,
    apply_changes: bool = False,
    current_user: str = Depends(get_current_user),
):
    """
    Automatically fix common code issues.

    Args:
        project_id: Project ID
        issue_types: List of issue types to fix (formatting, naming, etc)
        apply_changes: Whether to apply changes or just preview
        current_user: Authenticated user

    Returns:
        SuccessResponse with fix results
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

        # Default issue types if not specified
        issues = issue_types or ["error_handling", "documentation", "type_hints"]

        # Call code generator via orchestrator to generate fixes
        orchestrator = get_orchestrator()
        result = await orchestrator.process_request_async(
            "code_generator",
            {
                "action": "fix_issues",
                "project": project,
                "issue_types": issues,
                "apply_changes": apply_changes,
            }
        )

        fix_results = result.get("data", {})

        record_event("issues_fixed", {
            "project_id": project_id,
            "issue_types": len(issues),
            "apply_changes": apply_changes,
        }, user_id=current_user)

        return SuccessResponse(
            success=True,
            message=f"Auto-fix completed ({'Applied' if apply_changes else 'Preview'})",
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

        # Call orchestrator to generate comprehensive report
        orchestrator = get_orchestrator()
        result = await orchestrator.process_request_async(
            "quality_controller",
            {
                "action": "generate_report",
                "project": project,
            }
        )

        report = result.get("data", {})

        record_event("report_generated", {
            "project_id": project_id,
        }, user_id=current_user)

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
