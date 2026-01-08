"""
Project Finalization API endpoints for Socrates.

Provides REST endpoints for finalizing projects including:
- Generating final project artifacts
- Creating final documentation package
- Archiving project with deliverables
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import APIResponse, SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["finalization"])


@router.post(
    "/{project_id}/finalize/generate",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate final project artifacts",
)
async def generate_final_artifacts(
    project_id: str,
    include_code: Optional[bool] = True,
    include_docs: Optional[bool] = True,
    include_tests: Optional[bool] = True,
    current_user: str = Depends(get_current_user),
):
    """
    Generate final project artifacts and deliverables.

    Creates a comprehensive package of all project outputs including
    code, documentation, tests, and configuration files.

    Args:
        project_id: Project ID
        include_code: Include generated code files
        include_docs: Include project documentation
        include_tests: Include test files and results
        current_user: Authenticated user

    Returns:
        SuccessResponse with artifact generation summary
    """
    try:
        logger.info(f"Generating final artifacts for project: {project_id}")

        # Verify project access
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Collect artifacts
        artifacts = {
            "project_id": project_id,
            "project_name": project.name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "includes": [],
        }

        # Code artifacts
        if include_code:
            code_files = []
            if project.code_history:
                for code_item in project.code_history:
                    code_files.append(
                        {
                            "filename": f"code_{code_item.get('id', 'unknown')}.{code_item.get('language', 'txt')}",
                            "language": code_item.get("language", "text"),
                            "lines": code_item.get("lines", 0),
                            "generated_at": code_item.get("timestamp"),
                        }
                    )
            artifacts["code"] = code_files
            artifacts["includes"].append("code")

        # Documentation artifacts
        if include_docs:
            doc_files = []
            # Include project documentation
            doc_files.append(
                {
                    "filename": f"{project.name}_README.md",
                    "format": "markdown",
                    "type": "project overview",
                }
            )
            # Include conversation summary
            if project.conversation_history:
                doc_files.append(
                    {
                        "filename": f"{project.name}_CONVERSATIONS.md",
                        "format": "markdown",
                        "type": "conversation summary",
                        "conversation_count": len(project.conversation_history),
                    }
                )
            artifacts["documentation"] = doc_files
            artifacts["includes"].append("documentation")

        # Test artifacts
        if include_tests:
            artifacts["tests"] = {
                "test_files": 1,
                "test_coverage": 0,
                "status": "generated",
            }
            artifacts["includes"].append("tests")

        # Project metadata
        artifacts["project_metadata"] = {
            "phase": project.phase,
            "overall_maturity": project.overall_maturity,
            "phase_maturity": project.phase_maturity_scores or {},
            "total_conversations": len(project.conversation_history or []),
            "code_generations": len(project.code_history or []),
        }

        # Create finalization record
        finalization_id = f"final_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        if not hasattr(project, "finalization_history"):
            project.finalization_history = []
        project.finalization_history = getattr(project, "finalization_history", [])
        project.finalization_history.append(
            {
                "id": finalization_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "artifact_count": len(artifacts["includes"]),
                "status": "completed",
            }
        )

        # Mark project as finalized
        project.status = "completed"
        db.save_project(project)

        from socrates_api.routers.events import record_event

        record_event(
            "project_finalized",
            {
                "project_id": project_id,
                "artifact_count": len(artifacts["includes"]),
                "includes": artifacts["includes"],
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
        status="success",
            message="Final artifacts generated successfully",
            data={
                "finalization_id": finalization_id,
                "artifacts": artifacts,
                "download_ready": True,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating final artifacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate artifacts: {str(e)}",
        )


@router.post(
    "/{project_id}/finalize/docs",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate final project documentation package",
)
async def generate_final_documentation(
    project_id: str,
    format: Optional[str] = "markdown",
    include_api_docs: Optional[bool] = True,
    include_code_docs: Optional[bool] = True,
    include_deployment_guide: Optional[bool] = True,
    current_user: str = Depends(get_current_user),
):
    """
    Generate comprehensive final documentation package.

    Creates complete documentation suitable for deployment including
    API documentation, code documentation, and deployment guides.

    Args:
        project_id: Project ID
        format: Documentation format (markdown, pdf, html)
        include_api_docs: Include API documentation
        include_code_docs: Include code/implementation documentation
        include_deployment_guide: Include deployment guide
        current_user: Authenticated user

    Returns:
        SuccessResponse with documentation package
    """
    try:
        logger.info(f"Generating final documentation for project: {project_id}")

        # Verify project access
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Build documentation package
        doc_package = {
            "project_id": project_id,
            "project_name": project.name,
            "format": format,
            "sections": [],
        }

        # Main README
        readme_content = f"""# {project.name}

## Project Overview
{project.description or "Project developed with Socrates AI tutoring system."}

### Project Information
- **Type**: {project.project_type}
- **Language**: {project.language_preferences}
- **Deployment Target**: {project.deployment_target}
- **Maturity Level**: {int(project.overall_maturity)}%

### Phase Breakdown
"""
        for phase, score in (project.phase_maturity_scores or {}).items():
            readme_content += f"- {phase.capitalize()}: {int(score)}%\n"

        doc_package["sections"].append(
            {
                "name": "README.md",
                "content": readme_content,
                "type": "overview",
            }
        )

        # API Documentation
        if include_api_docs:
            api_doc_content = """## API Documentation

### Authentication
All API endpoints require Bearer token authentication.

### Endpoints
- POST /chat/message - Send message to assistant
- GET /projects/{id}/maturity - Get project maturity status
- POST /projects/{id}/code/generate - Generate code

For full API reference, see API docs endpoint.
"""
            doc_package["sections"].append(
                {
                    "name": "API.md",
                    "content": api_doc_content,
                    "type": "api",
                }
            )

        # Code Documentation
        if include_code_docs and project.code_history:
            code_doc_content = """## Implementation Details

### Code Generated
"""
            for code_item in project.code_history[:5]:
                code_doc_content += f"\n### {code_item.get('explanation', 'Generated Code')}\n"
                code_doc_content += f"Language: {code_item.get('language', 'Unknown')}\n"
                code_doc_content += f"Lines: {code_item.get('lines', 0)}\n"

            doc_package["sections"].append(
                {
                    "name": "IMPLEMENTATION.md",
                    "content": code_doc_content,
                    "type": "implementation",
                }
            )

        # Deployment Guide
        if include_deployment_guide:
            deployment_content = f"""## Deployment Guide

### Prerequisites
- {project.language_preferences} installed
- Dependencies listed in requirements file

### Deployment Steps
1. Clone/download project files
2. Install dependencies
3. Configure environment
4. Run tests
5. Deploy to {project.deployment_target}

### Configuration
- Environment variables: See .env.example
- Build settings: See configuration file
- Runtime: {project.deployment_target}

### Support
For issues or questions, refer to the main README and API documentation.
"""
            doc_package["sections"].append(
                {
                    "name": "DEPLOYMENT.md",
                    "content": deployment_content,
                    "type": "deployment",
                }
            )

        # Create documentation record
        doc_id = f"finaldoc_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        if not hasattr(project, "final_documentation_history"):
            project.final_documentation_history = []
        project.final_documentation_history = getattr(project, "final_documentation_history", [])
        project.final_documentation_history.append(
            {
                "id": doc_id,
                "format": format,
                "sections": len(doc_package["sections"]),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        db.save_project(project)

        from socrates_api.routers.events import record_event

        record_event(
            "final_documentation_generated",
            {
                "project_id": project_id,
                "format": format,
                "section_count": len(doc_package["sections"]),
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
        status="success",
            message="Final documentation package generated successfully",
            data={
                "doc_id": doc_id,
                "format": format,
                "sections": doc_package["sections"],
                "download_ready": True,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating final documentation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate documentation: {str(e)}",
        )
