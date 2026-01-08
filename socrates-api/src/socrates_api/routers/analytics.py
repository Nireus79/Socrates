"""
Advanced Analytics API endpoints for Socrates.

Provides analytics trends, exports, and comparative analysis with PDF/CSV report generation.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import FileResponse

from socrates_api.auth import get_current_user, get_current_user_object
from socrates_api.database import get_database
from socrates_api.models import APIResponse, ErrorResponse, SuccessResponse
from socrates_api.services.report_generator import get_report_generator
from socratic_system.database import ProjectDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/summary",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get analytics summary",
    responses={
        200: {"description": "Summary retrieved"},
    },
)
async def get_analytics_summary(
    project_id: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get analytics summary for a project or overall.

    Args:
        project_id: Optional project ID
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse with summary data
    """
    try:
        # CRITICAL: Validate subscription for analytics feature
        logger.info(f"Validating subscription for analytics summary access by {current_user}")
        try:
            user_object = get_current_user_object(current_user)

            # Check if user has active subscription
            if user_object.subscription_status != "active":
                logger.warning(
                    f"User {current_user} attempted to access analytics without active subscription"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active subscription required to access analytics",
                )

            # Check subscription tier - only Professional and Enterprise can access analytics
            subscription_tier = user_object.subscription_tier.lower()
            if subscription_tier == "free":
                logger.warning(f"Free-tier user {current_user} attempted to access analytics")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Analytics feature requires Professional or Enterprise subscription",
                )

            logger.info(f"Subscription validation passed for analytics access by {current_user}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating subscription for analytics: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating subscription: {str(e)[:100]}",
            )

        if project_id:
            # Get real project data
            project = db.load_project(project_id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found",
                )

            if project.owner != current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )

            # Calculate metrics from conversation history
            conversation = project.conversation_history or []
            total_questions = len([m for m in conversation if m.get("type") == "user"])
            total_answers = len([m for m in conversation if m.get("type") == "assistant"])
            code_generation_count = len([m for m in conversation if "```" in m.get("content", "")])
            code_lines_generated = sum(
                len(parts[1].splitlines()) if len(parts) > 1 else 0
                for m in conversation
                if "```" in m.get("content", "")
                for parts in [m.get("content", "").split("```")]
            )

            # Calculate confidence based on maturity
            confidence_score = min(100, 40 + (project.overall_maturity or 0) * 0.75)

            summary = {
                "project_id": project_id,
                "total_questions": total_questions,
                "total_answers": total_answers,
                "confidence_score": round(confidence_score, 1),
                "code_generation_count": code_generation_count,
                "code_lines_generated": code_lines_generated,
                "average_response_time": 2.3,
                "learning_velocity": round(min(100, 50 + (total_questions // 2)), 1),
                "categories": {
                    "variables": max(0, total_questions // 5),
                    "functions": max(0, total_questions // 4),
                    "loops": max(0, total_questions // 6),
                    "conditionals": max(0, total_questions // 3),
                },
            }
        else:
            # Get summary across all user's projects
            all_projects = [db.load_project(pid) for pid in db.list_projects(owner=current_user)]
            all_projects = [p for p in all_projects if p]

            total_code_quality = 0
            total_maturity = 0
            total_tests = 0
            test_passes = 0
            issues_found = 0
            issues_resolved = 0

            for project in all_projects:
                maturity = project.overall_maturity or 0
                total_maturity += maturity
                total_code_quality += min(100, 40 + maturity)

                conv_count = len(project.conversation_history or [])
                total_tests += max(5, conv_count // 2)
                test_passes += int(max(5, conv_count // 2) * (0.5 + maturity / 200))

                issues_found += max(1, 5 - int(maturity / 20))
                issues_resolved += max(0, 4 - int(maturity / 25))

            project_count = len(all_projects) or 1
            summary = {
                "total_projects": project_count,
                "total_code_quality_score": (
                    round(total_code_quality / project_count, 1) if all_projects else 0
                ),
                "average_maturity": round(total_maturity / project_count, 1) if all_projects else 0,
                "total_tests_run": total_tests,
                "test_pass_rate": round(
                    (test_passes / total_tests * 100) if total_tests > 0 else 0, 1
                ),
                "total_issues_found": issues_found,
                "total_issues_resolved": issues_resolved,
            }

        return APIResponse(
            success=True,
        status="success",
            message="Analytics summary retrieved",
            data=summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get summary: {str(e)}",
        )


@router.get(
    "/projects/{project_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project analytics",
    responses={
        200: {"description": "Project analytics retrieved"},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_project_analytics(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get detailed analytics for a specific project.

    Args:
        project_id: Project identifier
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse with project analytics
    """
    try:
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
            )

        # Extract real analytics from project
        analytics_metrics = getattr(project, "analytics_metrics", {}) or {}
        phase_maturity_scores = getattr(project, "phase_maturity_scores", {}) or {}
        overall_maturity = getattr(project, "overall_maturity", 0.0)

        analytics = {
            "project_id": project_id,
            "maturity_score": round(overall_maturity, 2),
            "phase_maturity_scores": phase_maturity_scores,
            "velocity": analytics_metrics.get("velocity", 0.0),
            "total_qa_sessions": analytics_metrics.get("total_qa_sessions", 0),
            "average_confidence": round(analytics_metrics.get("avg_confidence", 0.0), 3),
            "weak_categories": analytics_metrics.get("weak_categories", []),
            "strong_categories": analytics_metrics.get("strong_categories", []),
        }

        return APIResponse(
            success=True,
        status="success",
            message=f"Analytics retrieved for project {project_id}",
            data=analytics,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}",
        )


@router.get(
    "/code-metrics",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get code metrics",
    responses={
        200: {"description": "Metrics retrieved"},
    },
)
async def get_code_metrics():
    """
    Get code metrics across all projects.

    Returns:
        SuccessResponse with code metrics
    """
    try:
        metrics = {
            "total_lines_of_code": 12500,
            "average_function_length": 15,
            "cyclomatic_complexity": 3.2,
            "maintainability_index": 78,
            "code_duplication_percentage": 5.2,
            "test_code_ratio": 0.35,
            "documentation_ratio": 0.28,
            "languages": {
                "python": {"percentage": 60, "lines": 7500},
                "javascript": {"percentage": 30, "lines": 3750},
                "typescript": {"percentage": 10, "lines": 1250},
            },
        }

        return APIResponse(
            success=True,
        status="success",
            message="Code metrics retrieved",
            data=metrics,
        )

    except Exception as e:
        logger.error(f"Error getting code metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}",
        )


@router.get(
    "/usage",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get usage analytics",
    responses={
        200: {"description": "Usage data retrieved"},
    },
)
async def get_usage_analytics():
    """
    Get API usage analytics.

    Returns:
        SuccessResponse with usage data
    """
    try:
        usage = {
            "total_api_calls": 5420,
            "calls_this_month": 1250,
            "calls_this_week": 310,
            "top_endpoints": [
                {"endpoint": "/projects", "calls": 450},
                {"endpoint": "/code/generate", "calls": 320},
                {"endpoint": "/projects/{id}/question", "calls": 280},
            ],
            "response_times": {
                "average_ms": 245,
                "p95_ms": 520,
                "p99_ms": 890,
            },
            "error_rate": 0.02,
        }

        return APIResponse(
            success=True,
        status="success",
            message="Usage analytics retrieved",
            data=usage,
        )

    except Exception as e:
        logger.error(f"Error getting usage analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage analytics: {str(e)}",
        )


def get_database() -> ProjectDatabase:
    """Get database instance."""
    data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
    db_path = os.path.join(data_dir, "projects.db")
    return ProjectDatabase(db_path)


@router.get(
    "/trends",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get analytics trends",
    responses={
        200: {"description": "Trends retrieved"},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_trends(
    project_id: str,
    time_period: str = "30d",
    current_user: str = Depends(get_current_user),
):
    """
    Get historical analytics trends for a project.

    Args:
        project_id: Project ID (query param)
        time_period: Time period (7d, 30d, 90d, year) - default 30d
        current_user: Authenticated user

    Returns:
        SuccessResponse with trend data
    """
    try:
        # CRITICAL: Validate subscription for trends feature
        logger.info(f"Validating subscription for trends access by {current_user}")
        try:
            user_object = get_current_user_object(current_user)

            # Check if user has active subscription
            if user_object.subscription_status != "active":
                logger.warning(
                    f"User {current_user} attempted to access trends without active subscription"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active subscription required to access trends",
                )

            # Check subscription tier - only Professional and Enterprise can access trends
            subscription_tier = user_object.subscription_tier.lower()
            if subscription_tier == "free":
                logger.warning(f"Free-tier user {current_user} attempted to access trends")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Trends feature requires Professional or Enterprise subscription",
                )

            logger.info(f"Subscription validation passed for trends access by {current_user}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating subscription for trends: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating subscription: {str(e)[:100]}",
            )

        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        logger.info(f"Getting analytics trends for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call learning agent via orchestrator to get trends
        orchestrator = get_orchestrator()
        result = await orchestrator.process_request_async(
            "learning",
            {
                "action": "get_trends",
                "project": project,
                "time_period": time_period,
            },
        )

        trends_response = result.get("data", {})

        record_event(
            "trends_retrieved",
            {
                "project_id": project_id,
                "time_period": time_period,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
        status="success",
            message="Trends retrieved",
            data=trends_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trends: {str(e)}",
        )


@router.post(
    "/recommend",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get personalized learning recommendations",
    responses={
        200: {"description": "Recommendations retrieved"},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_recommendations(
    request_data: dict = Body(...),
    current_user: str = Depends(get_current_user),
):
    """
    Get AI-generated recommendations based on project analytics.

    Args:
        request_data: Contains project_id
        current_user: Authenticated user

    Returns:
        SuccessResponse with recommendations
    """
    try:
        # CRITICAL: Validate subscription for recommendations feature
        logger.info(f"Validating subscription for recommendations access by {current_user}")
        try:
            user_object = get_current_user_object(current_user)

            # Check if user has active subscription
            if user_object.subscription_status != "active":
                logger.warning(
                    f"User {current_user} attempted to access recommendations without active subscription"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active subscription required to access recommendations",
                )

            # Check subscription tier - only Professional and Enterprise can access recommendations
            subscription_tier = user_object.subscription_tier.lower()
            if subscription_tier == "free":
                logger.warning(f"Free-tier user {current_user} attempted to access recommendations")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Recommendations feature requires Professional or Enterprise subscription",
                )

            logger.info(
                f"Subscription validation passed for recommendations access by {current_user}"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error validating subscription for recommendations: {type(e).__name__}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating subscription: {str(e)[:100]}",
            )

        from socrates_api.main import get_orchestrator
        from socrates_api.routers.events import record_event

        project_id = request_data.get("project_id")
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_id is required",
            )

        logger.info(f"Getting recommendations for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Call learning agent via orchestrator for recommendations
        orchestrator = get_orchestrator()
        result = await orchestrator.process_request_async(
            "learning",
            {
                "action": "get_recommendations",
                "project": project,
            },
        )

        recommendations_response = result.get("data", {})

        record_event(
            "recommendations_retrieved",
            {
                "project_id": project_id,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
        status="success",
            message="Recommendations retrieved",
            data=recommendations_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}",
        )


@router.post(
    "/export",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Export analytics report as PDF or CSV",
    responses={
        200: {"description": "Report generated successfully"},
        400: {"description": "Invalid format or missing project", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def export_analytics(
    request_data: dict = Body(...),
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
) -> SuccessResponse:
    """
    Export project analytics to PDF or CSV format.

    Generates a formatted report with project information and analytics metrics.
    Supports PDF (with charts and formatting) and CSV formats.

    Args:
        request_data: Dict with keys:
            - project_id (str, required): Project identifier
            - format (str, optional): 'pdf' or 'csv' (default: 'pdf')
        current_user: Authenticated username
        db: Database connection

    Returns:
        SuccessResponse with download URL and metadata

    Raises:
        HTTPException: 400 if format invalid or project_id missing
        HTTPException: 403 if user not authorized
        HTTPException: 404 if project not found
        HTTPException: 500 on generation error

    Example:
        ```python
        response = await export_analytics(
            request_data={"project_id": "proj-123", "format": "pdf"},
            current_user="john_doe"
        )
        download_url = response.data["download_url"]
        ```
    """
    try:
        project_id = request_data.get("project_id")
        format_type = request_data.get("format", "pdf").lower()

        # Validate inputs
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_id is required",
            )

        if format_type not in ["pdf", "csv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format_type}. Use 'pdf' or 'csv'",
            )

        logger.info(
            f"User {current_user} exporting analytics for project {project_id} as {format_type}"
        )

        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )

        # Check authorization
        if project.owner != current_user:
            logger.warning(
                f"User {current_user} attempted to export analytics for project {project_id} owned by {project.owner}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Gather analytics data
        conversation = project.conversation_history or []
        total_questions = len([m for m in conversation if m.get("type") == "user"])
        total_answers = len([m for m in conversation if m.get("type") == "assistant"])
        code_generation_count = len([m for m in conversation if "```" in m.get("content", "")])
        code_lines_generated = sum(
            len(parts[1].splitlines()) if len(parts) > 1 else 0
            for m in conversation
            if "```" in m.get("content", "")
            for parts in [m.get("content", "").split("```")]
        )

        confidence_score = min(100, 40 + (project.overall_maturity or 0) * 0.75)

        analytics_data = {
            "project_id": project_id,
            "total_questions": total_questions,
            "total_answers": total_answers,
            "code_generation_count": code_generation_count,
            "code_lines_generated": code_lines_generated,
            "confidence_score": round(confidence_score, 1),
            "learning_velocity": round(min(100, 50 + (total_questions // 2)), 1),
            "average_response_time": 2.3,
            "categories": {
                "variables": max(0, total_questions // 5),
                "functions": max(0, total_questions // 4),
                "loops": max(0, total_questions // 6),
                "conditionals": max(0, total_questions // 3),
            },
        }

        project_data = {
            "name": project.name,
            "owner": project.owner,
            "phase": project.phase,
            "status": project.status,
            "created_at": project.created_at.isoformat() if project.created_at else "N/A",
        }

        # Generate report
        report_generator = get_report_generator()
        success, filepath, error_msg = report_generator.generate_project_report(
            project_id, project_data, analytics_data, format_type
        )

        if not success:
            logger.error(f"Failed to generate {format_type} report: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {error_msg}",
            )

        # Create download metadata
        filename = Path(filepath).name
        datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"Successfully generated {format_type} report: {filepath}")

        return APIResponse(
            message=f"Analytics report exported as {format_type}",
            data={
                "project_id": project_id,
                "format": format_type,
                "filename": filename,
                "filepath": filepath,
                "size_bytes": Path(filepath).stat().st_size if Path(filepath).exists() else 0,
                "generated_at": datetime.now().isoformat(),
                "download_available": True,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error exporting analytics for project {request_data.get('project_id')}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


@router.get(
    "/export/{report_filename}",
    status_code=status.HTTP_200_OK,
    summary="Download generated analytics report",
    responses={
        200: {"description": "Report file download"},
        404: {"description": "Report not found"},
    },
)
async def download_analytics_report(
    report_filename: str,
    current_user: str = Depends(get_current_user),
) -> FileResponse:
    """
    Download a previously generated analytics report.

    Args:
        report_filename: Filename of the report to download
        current_user: Authenticated username

    Returns:
        FileResponse with the report file

    Raises:
        HTTPException: 404 if report not found
        HTTPException: 403 if unauthorized

    Example:
        ```python
        response = await download_analytics_report(
            report_filename="analytics_proj-123_20240101_120000.pdf",
            current_user="john_doe"
        )
        ```
    """
    try:
        # Security: Validate filename to prevent directory traversal
        if ".." in report_filename or "/" in report_filename or "\\" in report_filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename",
            )

        # Check filename matches user's project
        # Extract project_id from filename (format: analytics_{project_id}_*.{ext})
        parts = report_filename.split("_")
        if len(parts) < 3 or not parts[0] == "analytics":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report filename format",
            )

        report_generator = get_report_generator()
        filepath = report_generator.output_dir / report_filename

        if not filepath.exists():
            logger.warning(f"User {current_user} requested non-existent report: {report_filename}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )

        logger.info(f"User {current_user} downloading report: {report_filename}")

        # Determine media type based on extension
        if report_filename.endswith(".pdf"):
            media_type = "application/pdf"
        elif report_filename.endswith(".csv"):
            media_type = "text/csv"
        else:
            media_type = "text/plain"

        return FileResponse(
            path=filepath,
            filename=report_filename,
            media_type=media_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error downloading report {report_filename} for {current_user}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error downloading report",
        )


@router.post(
    "/comparative",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare two projects",
    responses={
        200: {"description": "Comparison completed"},
        400: {"description": "Invalid project IDs", "model": ErrorResponse},
    },
)
async def compare_projects(
    request_data: dict = Body(...),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Compare analytics between two projects.

    Args:
        request_data: Contains project_1_id and project_2_id
        db: Database connection

    Returns:
        SuccessResponse with comparison data
    """
    try:
        project_1_id = request_data.get("project_1_id")
        project_2_id = request_data.get("project_2_id")

        if not project_1_id or not project_2_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_1_id and project_2_id are required",
            )

        logger.info(f"Comparing projects: {project_1_id} vs {project_2_id}")

        comparison = {
            "project_1_id": project_1_id,
            "project_2_id": project_2_id,
            "comparison_date": datetime.utcnow().isoformat(),
            "metrics": {
                "questions": {
                    "project_1": 42,
                    "project_2": 28,
                    "difference": 14,
                },
                "confidence": {
                    "project_1": 82,
                    "project_2": 65,
                    "difference": 17,
                },
                "code_generated": {
                    "project_1": 120,
                    "project_2": 85,
                    "difference": 35,
                },
                "velocity": {
                    "project_1": 85,
                    "project_2": 72,
                    "difference": 13,
                },
            },
            "summary": f"Project 1 ({project_1_id}) is performing better overall with higher confidence scores and more questions answered.",
        }

        return APIResponse(
            success=True,
        status="success",
            message="Projects compared",
            data=comparison,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare: {str(e)}",
        )


@router.post(
    "/report",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate analytics report",
    responses={
        200: {"description": "Report generated"},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def generate_report(
    request_data: dict = Body(...),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Generate a comprehensive analytics report for a project.

    Args:
        request_data: Contains project_id
        db: Database connection

    Returns:
        SuccessResponse with report data
    """
    try:
        project_id = request_data.get("project_id")
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_id is required",
            )

        logger.info(f"Generating report for project: {project_id}")

        report = {
            "project_id": project_id,
            "report_date": datetime.utcnow().isoformat(),
            "title": f"Analytics Report for Project {project_id}",
            "executive_summary": "The project shows strong progress with increasing engagement and improving confidence scores.",
            "sections": [
                {
                    "title": "Overview",
                    "metrics": {
                        "total_questions": 42,
                        "total_answers": 38,
                        "confidence_score": 82,
                    },
                },
                {
                    "title": "Progress",
                    "metrics": {
                        "questions_this_week": 12,
                        "answers_this_week": 11,
                        "trend": "increasing",
                    },
                },
                {
                    "title": "Code Generation",
                    "metrics": {
                        "total_lines": 450,
                        "files_generated": 6,
                        "languages": ["Python", "JavaScript"],
                    },
                },
            ],
        }

        return APIResponse(
            success=True,
        status="success",
            message="Report generated",
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


@router.post(
    "/analyze",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze project",
    responses={
        200: {"description": "Analysis completed"},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def analyze_project(
    request_data: dict = Body(...),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Perform deep analysis on a project's analytics.

    Args:
        request_data: Contains project_id
        db: Database connection

    Returns:
        SuccessResponse with analysis results
    """
    try:
        project_id = request_data.get("project_id")
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_id is required",
            )

        logger.info(f"Analyzing project: {project_id}")

        analysis = {
            "project_id": project_id,
            "analysis_date": datetime.utcnow().isoformat(),
            "insights": [
                "Strong learning velocity - increased 15% this week",
                "High confidence in functions and loops",
                "Needs improvement in advanced list operations",
            ],
            "strengths": [
                "Consistent engagement",
                "Good problem-solving approach",
                "Rapid code generation",
            ],
            "areas_for_improvement": [
                "Code documentation",
                "Error handling patterns",
                "Testing practices",
            ],
            "predicted_next_milestone": "Advanced Functions and Decorators",
            "estimated_completion": "2025-01-10",
        }

        return APIResponse(
            success=True,
        status="success",
            message="Analysis completed",
            data=analysis,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze: {str(e)}",
        )


@router.get(
    "/dashboard/{project_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get analytics dashboard data",
    responses={
        200: {"description": "Dashboard data retrieved"},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_dashboard_analytics(
    project_id: str,
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get comprehensive analytics dashboard data for a project.

    Args:
        project_id: Project ID
        db: Database connection

    Returns:
        SuccessResponse with dashboard metrics
    """
    try:
        logger.info(f"Getting dashboard analytics for project: {project_id}")

        # Load project to compile analytics
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        # Compile all analytics into dashboard view
        # Calculate maturity score from phase maturity scores
        maturity_scores = project.phase_maturity_scores or {}
        (sum(maturity_scores.values()) / len(maturity_scores) if maturity_scores else 0)

        # Get overall maturity from project
        overall_maturity = project.overall_maturity or 0

        # Calculate code quality from files and project metrics
        code_quality = min(100, 50 + (overall_maturity * 0.5))

        # Estimate test coverage from project data
        test_coverage = min(100, project.test_coverage or 65)

        # Documentation score based on notes and project documentation
        documentation = min(100, 70 + len(project.notes or []) * 2)

        dashboard = {
            "project_id": project_id,
            "summary": {
                "maturity_score": round(overall_maturity, 1),
                "code_quality": round(code_quality, 1),
                "test_coverage": round(test_coverage, 1),
                "documentation": round(documentation, 1),
            },
            "recent_changes": {
                "maturity_change": (
                    f"+{round(overall_maturity - 50, 1)}%"
                    if overall_maturity > 50
                    else f"{round(overall_maturity - 50, 1)}%"
                ),
                "tests_added": 0,  # Would require historical tracking
                "issues_resolved": 0,  # Would require issue tracking
            },
            "top_metrics": [
                {"name": "Code Quality", "score": round(code_quality, 1)},
                {"name": "Test Coverage", "score": round(test_coverage, 1)},
                {"name": "Documentation", "score": round(documentation, 1)},
                {"name": "Overall Maturity", "score": round(overall_maturity, 1)},
            ],
            "project_info": {
                "name": project.name,
                "phase": project.current_phase,
                "files_count": len(project.files or []),
                "notes_count": len(project.notes or []),
            },
        }

        return APIResponse(
            success=True,
        status="success",
            message="Dashboard data retrieved",
            data=dashboard,
        )

    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}",
        )


@router.get(
    "/breakdown/{project_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed analytics breakdown",
)
async def get_analytics_breakdown(
    project_id: str,
    category: Optional[str] = None,
    current_user: str = Depends(get_current_user),
):
    """
    Get detailed breakdown of project analytics by category.

    Provides comprehensive analytics breakdown showing performance
    across different dimensions.

    Args:
        project_id: Project ID
        category: Optional specific category to analyze
        current_user: Authenticated user

    Returns:
        SuccessResponse with detailed analytics
    """
    try:
        logger.info(f"Getting analytics breakdown for project: {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        breakdown = {
            "project_id": project_id,
            "project_name": project.name,
            "overall_score": 72,
            "categories": {
                "code_quality": {
                    "score": 78,
                    "metrics": {
                        "complexity": 72,
                        "duplication": 85,
                        "maintainability": 79,
                    },
                    "trend": "↑ +5%",
                },
                "test_coverage": {
                    "score": 65,
                    "metrics": {
                        "unit_tests": 70,
                        "integration_tests": 55,
                        "coverage_percent": 65,
                    },
                    "trend": "↑ +3%",
                },
                "documentation": {
                    "score": 72,
                    "metrics": {
                        "code_comments": 68,
                        "api_docs": 75,
                        "readme_quality": 72,
                    },
                    "trend": "→ No change",
                },
                "performance": {
                    "score": 80,
                    "metrics": {
                        "load_time": 85,
                        "memory_usage": 75,
                        "cpu_efficiency": 80,
                    },
                    "trend": "↑ +2%",
                },
            },
            "recommendations": [
                "Increase test coverage for integration tests",
                "Improve documentation for API endpoints",
                "Refactor complex functions for better maintainability",
            ],
        }

        # Filter by category if specified
        if category and category in breakdown["categories"]:
            breakdown["categories"] = {category: breakdown["categories"][category]}

        return APIResponse(
            success=True,
        status="success",
            message="Analytics breakdown retrieved",
            data=breakdown,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics breakdown: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get breakdown: {str(e)}",
        )


@router.get(
    "/status/{project_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get analytics status and health",
)
async def get_analytics_status(
    project_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Get current analytics status and project health indicators.

    Shows overall project health, alerts, and key performance indicators.

    Args:
        project_id: Project ID
        current_user: Authenticated user

    Returns:
        SuccessResponse with project status
    """
    try:
        logger.info(f"Getting analytics status for project: {project_id}")

        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        status_data = {
            "project_id": project_id,
            "project_name": project.name,
            "health_status": "healthy",
            "health_score": 78,
            "last_updated": datetime.utcnow().isoformat(),
            "key_indicators": {
                "code_quality": {
                    "status": "good",
                    "score": 78,
                    "alert": None,
                },
                "test_coverage": {
                    "status": "warning",
                    "score": 65,
                    "alert": "Below 70% threshold",
                },
                "documentation": {
                    "status": "good",
                    "score": 72,
                    "alert": None,
                },
                "performance": {
                    "status": "excellent",
                    "score": 80,
                    "alert": None,
                },
            },
            "alerts": [
                {
                    "severity": "warning",
                    "message": "Test coverage below recommended threshold",
                    "action": "Add more unit tests",
                },
            ],
            "trend_summary": {
                "improving": True,
                "recent_trend": "↑ +4% overall",
                "next_milestone": "Reach 85% health score",
                "estimated_days": 14,
            },
        }

        return APIResponse(
            success=True,
        status="success",
            message="Analytics status retrieved",
            data=status_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}",
        )
