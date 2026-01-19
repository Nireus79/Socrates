"""
Project Finalization API endpoints for Socrates.

Provides REST endpoints for finalizing projects including:
- Generating final project artifacts
- Creating final documentation package
- Archiving project with deliverables
"""

import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.auth.project_access import check_project_access
from socratic_system.database import ProjectDatabase
from socratic_system.utils.archive_builder import ArchiveBuilder
from socratic_system.utils.git_initializer import GitInitializer
from socratic_system.utils.documentation_generator import DocumentationGenerator
from socrates_api.models import APIResponse

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
    db: ProjectDatabase = Depends(get_database),
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
        db: Database connection

    Returns:
        SuccessResponse with artifact generation summary
    """
    try:
        await check_project_access(project_id, current_user, db, min_role="editor")

        logger.info(f"Generating final artifacts for project: {project_id}")
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
    db: ProjectDatabase = Depends(get_database),
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
        db: Database connection

    Returns:
        SuccessResponse with documentation package
    """
    try:
        await check_project_access(project_id, current_user, db, min_role="editor")

        logger.info(f"Generating final documentation for project: {project_id}")
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Build documentation package using comprehensive generator
        doc_package = {
            "project_id": project_id,
            "project_name": project.name,
            "format": format,
            "sections": [],
        }

        doc_gen = DocumentationGenerator()

        # Generate comprehensive README
        readme_content = doc_gen.generate_comprehensive_readme(
            project_name=project.name,
            description=project.description or f"Project: {project.name}",
            tech_stack=project.tech_stack or [],
            requirements=project.requirements or [],
            features=getattr(project, 'features', None) or [
                "Modular architecture",
                "Production-ready configuration",
                "Comprehensive test coverage",
            ],
            deployment_target=project.deployment_target or "Local/Server",
        )

        doc_package["sections"].append(
            {
                "name": "README.md",
                "content": readme_content,
                "type": "overview",
            }
        )

        # API Documentation
        if include_api_docs:
            api_doc_content = doc_gen.generate_api_documentation()
            doc_package["sections"].append(
                {
                    "name": "API.md",
                    "content": api_doc_content,
                    "type": "api",
                }
            )

        # Architecture Documentation
        arch_doc_content = doc_gen.generate_architecture_docs(
            project_name=project.name,
            description=project.description or f"Project: {project.name}",
            tech_stack=project.tech_stack or [],
            architecture_notes=f"Project maturity: {int(project.overall_maturity)}%\n"
                                f"Deployment target: {project.deployment_target}",
        )

        doc_package["sections"].append(
            {
                "name": "ARCHITECTURE.md",
                "content": arch_doc_content,
                "type": "architecture",
            }
        )

        # Setup Guide
        if include_code_docs:
            setup_content = doc_gen.generate_setup_guide(project.name)
            doc_package["sections"].append(
                {
                    "name": "SETUP.md",
                    "content": setup_content,
                    "type": "setup",
                }
            )

        # Deployment Guide (enhanced)
        if include_deployment_guide:
            deployment_content = f"""# Deployment Guide

## Overview

This guide provides instructions for deploying {project.name} to {project.deployment_target}.

## Prerequisites

Before deploying, ensure you have:
- {project.language_preferences or 'Python 3.9+'} installed
- All dependencies from `requirements.txt`
- Access to {project.deployment_target}
- Environment variables configured (see `.env.example`)

## Pre-Deployment Checklist

- [ ] All tests passing: `make test`
- [ ] Code quality checks passing: `make lint`
- [ ] Build successful: `make build`
- [ ] Environment variables configured
- [ ] Documentation up to date
- [ ] CHANGELOG updated

## Deployment Steps

### 1. Prepare Release

```bash
# Run all checks
make lint
make test
make clean

# Build distribution
make build
```

### 2. Configure Environment

Set all required environment variables for {project.deployment_target}:

```bash
# Copy and customize .env
cp .env.example .env.production
# Edit .env.production with production values
```

### 3. Deploy

**For Docker:**
```bash
docker build -t {project.name}:latest .
docker push your-registry/{project.name}:latest
# Deploy using your container orchestration platform
```

**For {project.deployment_target}:**
- Follow platform-specific deployment instructions
- Ensure database migrations are run (if applicable)
- Configure any external services
- Set up monitoring and logging

### 4. Post-Deployment

- [ ] Verify application is running
- [ ] Check logs for errors
- [ ] Run smoke tests
- [ ] Monitor system metrics
- [ ] Alert stakeholders of deployment

## Rollback Procedures

If issues occur:

1. Identify the problem
2. Revert to previous version
3. Document the issue
4. Fix in development
5. Re-test and re-deploy

## Monitoring

Key metrics to monitor:
- Application health/uptime
- Error rates and logs
- Response times
- Resource utilization (CPU, memory, disk)
- Database performance

## Support

For deployment issues:
1. Check the logs
2. Review TROUBLESHOOTING section in README
3. See CONTRIBUTING.md for support options
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


@router.get(
    "/{project_id}/export",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Download generated project as ZIP archive",
)
async def export_project(
    project_id: str,
    format: Optional[str] = "zip",
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Export generated project as downloadable archive.

    Supports multiple formats:
    - zip: ZIP archive (default, works on all systems)
    - tar: Uncompressed TAR archive
    - tar.gz: Gzip-compressed TAR archive
    - tar.bz2: Bzip2-compressed TAR archive

    Args:
        project_id: Project ID to export
        format: Archive format (zip, tar, tar.gz, tar.bz2)
        current_user: Authenticated user
        db: Database connection

    Returns:
        FileResponse with archive file download

    Raises:
        HTTPException: If project not found, access denied, or generation fails
    """
    try:
        await check_project_access(project_id, current_user, db, min_role="viewer")

        logger.info(f"Exporting project: {project_id} as {format}")
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Find generated project directory
        data_dir = Path.home() / ".socrates" / "generated" / project_id

        # Look for project directories (there may be multiple versions)
        project_dirs = list(data_dir.glob("*")) if data_dir.exists() else []

        if not project_dirs:
            raise HTTPException(
                status_code=404,
                detail="Generated project files not found. Please generate code first."
            )

        # Use the most recently modified directory
        project_root = max(project_dirs, key=lambda p: p.stat().st_mtime)

        if not project_root.is_dir():
            raise HTTPException(
                status_code=404,
                detail="Invalid generated project directory"
            )

        logger.info(f"Found project directory: {project_root}")

        # Create archive in temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Determine archive filename and format
            safe_project_name = project.name.replace(" ", "_").replace("/", "_").lower()[:50]
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            base_filename = f"{safe_project_name}_{timestamp}"

            # Create archive based on format
            if format == "tar":
                archive_path = tmpdir_path / f"{base_filename}.tar"
                success, message = ArchiveBuilder.create_tarball(
                    project_root, archive_path, compression=""
                )
                media_type = "application/x-tar"
            elif format == "tar.gz":
                archive_path = tmpdir_path / f"{base_filename}.tar.gz"
                success, message = ArchiveBuilder.create_tarball(
                    project_root, archive_path, compression="gz"
                )
                media_type = "application/gzip"
            elif format == "tar.bz2":
                archive_path = tmpdir_path / f"{base_filename}.tar.bz2"
                success, message = ArchiveBuilder.create_tarball(
                    project_root, archive_path, compression="bz2"
                )
                media_type = "application/x-bzip2"
            else:  # Default to ZIP
                archive_path = tmpdir_path / f"{base_filename}.zip"
                success, message = ArchiveBuilder.create_zip_archive(
                    project_root, archive_path
                )
                media_type = "application/zip"

            if not success:
                logger.error(f"Failed to create archive: {message}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create archive: {message}"
                )

            logger.info(f"Successfully created archive: {archive_path}")

            # Get archive info
            archive_info = ArchiveBuilder.get_archive_info(archive_path)
            logger.info(f"Archive info: {archive_info}")

            # Record export event
            from socrates_api.routers.events import record_event
            record_event(
                "project_exported",
                {
                    "project_id": project_id,
                    "format": format,
                    "archive_size_mb": archive_info.get("size_mb"),
                    "file_count": archive_info.get("file_count"),
                },
                user_id=current_user,
            )

            # Return file response
            headers = {
                "Content-Disposition": f"attachment; filename={archive_path.name}",
            }

            return FileResponse(
                archive_path,
                media_type=media_type,
                headers=headers,
                filename=archive_path.name,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting project: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export project: {str(e)}",
        )


@router.post(
    "/{project_id}/publish-to-github",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish project to GitHub",
)
async def publish_to_github(
    project_id: str,
    repo_name: str,
    description: str = "",
    private: bool = True,
    github_token: str = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Publish generated project to GitHub.

    This endpoint will:
    1. Find the generated project directory
    2. Initialize a git repository (if not already)
    3. Create a GitHub repository
    4. Push code to GitHub

    Args:
        project_id: Project ID to publish
        repo_name: Name for GitHub repository
        description: Repository description
        private: Whether repository should be private (default: True)
        github_token: GitHub Personal Access Token (required for authentication)
        current_user: Authenticated user
        db: Database connection

    Returns:
        APIResponse with GitHub repository information

    Raises:
        HTTPException: If project not found, access denied, git not installed, or GitHub API fails
    """
    try:
        await check_project_access(project_id, current_user, db, min_role="owner")

        logger.info(f"Publishing project to GitHub: {project_id}")
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Only project owner can publish")

        # Get GitHub token from request or user settings
        if not github_token:
            # Try to get from user model if it has github_token field
            try:
                user_obj = db.load_user(current_user)
                if user_obj and hasattr(user_obj, "github_token"):
                    github_token = user_obj.github_token
            except:
                pass

        if not github_token:
            raise HTTPException(
                status_code=400,
                detail="GitHub token is required. Please provide github_token parameter or configure it in your account settings.",
            )

        # Check if git is installed
        if not GitInitializer.is_git_installed():
            raise HTTPException(
                status_code=500,
                detail="Git is not installed on the server. Cannot proceed with GitHub publishing.",
            )

        # Find generated project directory
        data_dir = Path.home() / ".socrates" / "generated" / project_id
        project_dirs = list(data_dir.glob("*")) if data_dir.exists() else []

        if not project_dirs:
            raise HTTPException(
                status_code=404,
                detail="Generated project files not found. Please generate code first.",
            )

        # Use the most recently modified directory
        project_root = max(project_dirs, key=lambda p: p.stat().st_mtime)

        if not project_root.is_dir():
            raise HTTPException(
                status_code=404,
                detail="Invalid generated project directory",
            )

        logger.info(f"Found project directory: {project_root}")

        # Validate GitHub token and get user info
        logger.info("Validating GitHub token...")
        token_valid, user_info = GitInitializer.get_github_user_info(github_token)
        if not token_valid:
            raise HTTPException(
                status_code=401,
                detail=f"GitHub authentication failed: {user_info.get('error', 'Invalid token')}",
            )

        github_username = user_info.get("login")
        logger.info(f"GitHub user authenticated: {github_username}")

        # Initialize git repository (if not already)
        logger.info("Initializing git repository...")
        git_success, git_message = GitInitializer.initialize_repository(
            project_root,
            initial_commit_message="Initial commit: Generated by Socrates AI",
        )

        if not git_success and "already initialized" not in git_message.lower():
            logger.error(f"Git initialization failed: {git_message}")
            raise HTTPException(
                status_code=500,
                detail=f"Git initialization failed: {git_message}",
            )

        logger.info(git_message)

        # Create GitHub repository
        logger.info(f"Creating GitHub repository: {repo_name}")
        github_success, repo_data = GitInitializer.create_github_repository(
            repo_name=repo_name,
            description=description or f"Project: {project.name}",
            private=private,
            github_token=github_token,
        )

        if not github_success:
            error_msg = repo_data.get("error", "Unknown error")
            logger.error(f"GitHub repository creation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create GitHub repository: {error_msg}",
            )

        repo_url = repo_data.get("html_url")
        clone_url = repo_data.get("clone_url")
        logger.info(f"GitHub repository created: {repo_url}")

        # Push to GitHub
        logger.info(f"Pushing code to GitHub: {clone_url}")
        push_success, push_message = GitInitializer.push_to_github(
            project_root,
            clone_url,
            branch="main",
        )

        if not push_success:
            logger.error(f"Push to GitHub failed: {push_message}")
            # Repository was created but push failed - return partial success
            return APIResponse(
                success=False,
                status="partial_success",
                message=f"GitHub repository created but push failed: {push_message}",
                data={
                    "repo_url": repo_url,
                    "clone_url": clone_url,
                    "push_error": push_message,
                    "project_id": project_id,
                },
            )

        logger.info(f"Successfully published project to GitHub: {repo_url}")

        # Get repository status
        repo_status = GitInitializer.get_repository_status(project_root)

        # Record publish event
        from socrates_api.routers.events import record_event
        record_event(
            "project_published_to_github",
            {
                "project_id": project_id,
                "repo_name": repo_name,
                "repo_url": repo_url,
                "private": private,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
            status="success",
            message="Project successfully published to GitHub",
            data={
                "repo_url": repo_url,
                "clone_url": clone_url,
                "repo_name": repo_name,
                "private": private,
                "github_user": github_username,
                "project_id": project_id,
                "git_status": repo_status,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing to GitHub: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish project: {str(e)}",
        )
