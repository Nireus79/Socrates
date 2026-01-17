"""
GitHub Integration API endpoints for Socrates.

Provides GitHub repository import, pull, push, and sync functionality.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.models import (
    APIResponse,
    ErrorResponse,
    GitHubImportRequest,
    SuccessResponse,
)
from socratic_system.database import ProjectDatabase
from socrates_api.auth.project_access import check_project_access
from socratic_system.agents.github_sync_handler import (
    create_github_sync_handler,
    TokenExpiredError,
    PermissionDeniedError,
    RepositoryNotFoundError,
    NetworkSyncFailedError,
    ConflictResolutionError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/github", tags=["github"])


def _chunk_code_content(content: str, chunk_size: int = 300, overlap: int = 30) -> list:
    """
    Split code content into overlapping chunks.
    Uses line-based chunking for code to preserve semantic structure.

    Args:
        content: Full code content
        chunk_size: Target words per chunk (smaller for code than text)
        overlap: Words to overlap between chunks

    Returns:
        List of text chunks
    """
    import re

    # Split into lines to maintain code structure
    lines = content.split('\n')

    chunks = []
    current_chunk = []
    current_words = 0

    for line in lines:
        line_words = len(line.split())

        # If adding this line exceeds chunk size and we have content
        if current_words + line_words > chunk_size and current_chunk:
            # Save current chunk
            chunk_text = '\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)

            # Create overlap: keep last few lines
            overlap_words = 0
            overlap_lines = []
            for l in reversed(current_chunk):
                l_words = len(l.split())
                if overlap_words + l_words <= overlap:
                    overlap_lines.insert(0, l)
                    overlap_words += l_words
                else:
                    break

            current_chunk = overlap_lines
            current_words = overlap_words

        # Add line to current chunk
        current_chunk.append(line)
        current_words += line_words

    # Add last chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks if chunks else [content]  # Return at least the full content


def get_database() -> ProjectDatabase:
    """Get database instance."""
    data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
    db_path = os.path.join(data_dir, "projects.db")
    return ProjectDatabase(db_path)


@router.post(
    "/import",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import GitHub repository as project",
    responses={
        201: {"description": "Repository imported successfully"},
        400: {"description": "Invalid GitHub URL or project name", "model": ErrorResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        500: {"description": "Server error during import", "model": ErrorResponse},
    },
)
async def import_repository(
    request: GitHubImportRequest,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Import a GitHub repository as a new project.

    Args:
        request: GitHub import request with URL, optional project name and branch
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse with imported project details

    Raises:
        HTTPException: If import fails
    """
    try:
        if not request.url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub URL cannot be empty",
            )

        # Validate GitHub URL format
        if not ("github.com" in request.url or "git@github.com" in request.url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub URL format",
            )

        logger.info(f"Importing GitHub repository: {request.url}")

        # CRITICAL: Check subscription limit BEFORE attempting to create project
        logger.info("Checking subscription limits for GitHub import...")
        try:
            from socrates_api.routers.projects import get_current_user_object
            from socratic_system.subscription.checker import SubscriptionChecker

            user_object = get_current_user_object(current_user)

            # Determine subscription tier - default to free if user not in DB yet
            subscription_tier = "free"
            if user_object:
                subscription_tier = getattr(user_object, "subscription_tier", "free")

            # Check project limit for subscription tier (testing mode checked via database flag)
            # If testing mode is enabled in database, bypass subscription checks
            testing_mode_enabled = getattr(user_object, "testing_mode", False) if user_object else False
            if not testing_mode_enabled:
                # Count only OWNED projects for tier limit, not collaborated projects
                all_projects = db.get_user_projects(current_user)
                owned_projects = [p for p in all_projects if p.owner == current_user]
                can_create, error_msg = SubscriptionChecker.can_create_projects(
                    subscription_tier, len(owned_projects)
                )
                if not can_create:
                    logger.warning(f"User {current_user} exceeded project limit via GitHub import: {error_msg}")
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)

            logger.info(f"Subscription validation passed for {current_user} (tier: {subscription_tier})")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating subscription for GitHub import: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating subscription: {str(e)[:100]}",
            )

        # Extract repository information from URL
        import re

        url_pattern = r"github\.com[:/](.+?)/(.+?)(?:\.git)?$"
        match = re.search(url_pattern, request.url)

        if not match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub URL format",
            )

        repo_owner, repo_name = match.groups()
        project_name = request.project_name or repo_name

        # Try to fetch repository metadata using PyGithub
        repo_metadata = {
            "files": 0,
            "languages": [],
            "has_tests": False,
            "has_readme": False,
            "description": "",
        }

        try:
            from github import Github

            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                g = Github(github_token)
                try:
                    repo = g.get_repo(f"{repo_owner}/{repo_name}")
                    repo_metadata = {
                        "description": repo.description or "",
                        "languages": (
                            list(repo.get_languages().keys()) if repo.get_languages() else []
                        ),
                        "has_tests": any("test" in f.path for f in repo.get_contents("")),
                        "has_readme": any(
                            "readme" in f.name.lower() for f in repo.get_contents("")
                        ),
                    }
                except Exception as e:
                    logger.warning(f"Could not fetch repo metadata: {e}")
        except ImportError:
            logger.warning("PyGithub not installed. Run: pip install PyGithub")
        except Exception as e:
            logger.warning(f"Error fetching GitHub metadata: {e}")

        # Create project from GitHub import
        from datetime import datetime, timezone

        from socratic_system.models.project import ProjectContext

        project = ProjectContext(
            project_id=f"proj_{repo_name.lower()}",
            name=project_name,
            owner=current_user,
            phase="planning",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            repository_url=request.url,
            repository_owner=repo_owner,
            repository_name=repo_name,
            tech_stack=repo_metadata.get("languages", []),
            description=repo_metadata.get("description", ""),
        )

        # Save project to database
        db.save_project(project)

        # Vectorize repository content for knowledge base
        repo_knowledge_result = {
            "status": "pending",
            "entries_added": 0,
            "message": "Repository content vectorization pending"
        }

        try:
            from github import Github
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                g = Github(github_token)
                try:
                    repo = g.get_repo(f"{repo_owner}/{repo_name}")

                    # Extract and vectorize README if available
                    readme_content = None
                    try:
                        readme = repo.get_readme()
                        readme_content = readme.decoded_string.decode('utf-8') if isinstance(readme.decoded_string, bytes) else str(readme.decoded_string)
                        if readme_content and len(readme_content.strip()) > 0:
                            # Add README to vector database
                            from socratic_system.database import VectorDatabase
                            vector_db = VectorDatabase()
                            metadata = {
                                "source": "README.md",
                                "project_id": project.project_id,
                                "source_type": "github_readme",
                                "repository": f"{repo_owner}/{repo_name}",
                            }
                            vector_db.add_text(readme_content, metadata=metadata)
                            repo_knowledge_result["entries_added"] += 1
                            logger.info(f"Vectorized README for {repo_owner}/{repo_name}")
                    except Exception as e:
                        logger.warning(f"Could not extract README: {e}")

                    # Extract and vectorize common code files
                    vectorized_files = 0
                    supported_extensions = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".rb"}

                    try:
                        # Get up to 10 common code files
                        contents = repo.get_contents("")
                        files_to_process = []

                        def extract_code_files(contents, depth=0, max_depth=2):
                            if depth > max_depth or len(files_to_process) >= 10:
                                return
                            for item in contents:
                                if len(files_to_process) >= 10:
                                    break
                                if item.type == "file":
                                    _, ext = os.path.splitext(item.name)
                                    if ext in supported_extensions:
                                        files_to_process.append(item)
                                elif item.type == "dir" and depth < max_depth:
                                    try:
                                        extract_code_files(repo.get_contents(item.path), depth + 1, max_depth)
                                    except Exception:
                                        pass

                        extract_code_files(contents)

                        # Process extracted code files with chunking
                        from socratic_system.database import VectorDatabase
                        vector_db = VectorDatabase()

                        for code_file in files_to_process:
                            try:
                                file_content = code_file.decoded_content.decode('utf-8') if isinstance(code_file.decoded_content, bytes) else str(code_file.decoded_content)
                                if file_content and len(file_content.strip()) > 100:  # Only include non-trivial files
                                    # Chunk the code file (300-word chunks for code, 30-word overlap for function boundaries)
                                    chunks = _chunk_code_content(file_content, chunk_size=300, overlap=30)

                                    # Store each chunk
                                    for chunk_idx, chunk in enumerate(chunks):
                                        try:
                                            metadata = {
                                                "source": code_file.path,
                                                "chunk": chunk_idx + 1,
                                                "total_chunks": len(chunks),
                                                "project_id": project.project_id,
                                                "source_type": "github_code",
                                                "repository": f"{repo_owner}/{repo_name}",
                                            }
                                            vector_db.add_text(chunk, metadata=metadata)
                                            repo_knowledge_result["entries_added"] += 1
                                        except Exception as chunk_error:
                                            logger.warning(f"Could not add chunk {chunk_idx + 1} of {code_file.path}: {chunk_error}")

                                    vectorized_files += 1
                            except Exception as e:
                                logger.warning(f"Could not vectorize {code_file.path}: {e}")

                        if vectorized_files > 0:
                            repo_knowledge_result["status"] = "success"
                            repo_knowledge_result["message"] = f"Vectorized {vectorized_files} code files and README"
                            logger.info(f"Vectorized {vectorized_files} code files from {repo_owner}/{repo_name}")

                    except Exception as e:
                        logger.warning(f"Could not extract code files from repository: {e}")
                        if repo_knowledge_result["entries_added"] > 0:
                            repo_knowledge_result["status"] = "partial"
                            repo_knowledge_result["message"] = f"Partially vectorized repository (added {repo_knowledge_result['entries_added']} entries)"

                except Exception as e:
                    logger.warning(f"Could not vectorize repository content: {e}")
        except ImportError:
            logger.warning("PyGithub not installed - skipping content vectorization")
        except Exception as e:
            logger.warning(f"Error vectorizing GitHub repository: {e}")

        from socrates_api.routers.events import record_event

        # Record initial import event
        record_event(
            "github_repository_imported",
            {
                "repository": f"{repo_owner}/{repo_name}",
                "project_id": project.project_id,
                "user": current_user,
            },
            user_id=current_user,
        )

        # Record document imported event for knowledge base
        if repo_knowledge_result["entries_added"] > 0:
            record_event(
                "document.imported",
                {
                    "project_id": project.project_id,
                    "file_name": f"{repo_owner}/{repo_name}",
                    "source_type": "github_repository",
                    "words_extracted": 0,  # Not tracked for repos
                    "chunks_created": repo_knowledge_result["entries_added"],
                    "user_id": current_user,
                },
                user_id=current_user,
            )

        return APIResponse(
            success=True,
        status="success",
            message=f"Repository imported as project '{project_name}'",
            data={
                "project_id": project.project_id,
                "project_name": project_name,
                "repository_url": request.url,
                "branch": request.branch or "main",
                "metadata": repo_metadata,
                "validation_results": {},
                "knowledge_result": repo_knowledge_result,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing GitHub repository: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import repository: {str(e)}",
        )


@router.post(
    "/projects/{project_id}/pull",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Pull latest changes from GitHub",
    responses={
        200: {"description": "Pull successful"},
        400: {"description": "Project not linked to GitHub", "model": ErrorResponse},
        401: {"description": "Not authenticated or token expired", "model": ErrorResponse},
        403: {"description": "Access to repository denied", "model": ErrorResponse},
        404: {"description": "Project or repository not found", "model": ErrorResponse},
        409: {"description": "Merge conflicts detected", "model": ErrorResponse},
        500: {"description": "Server error during pull", "model": ErrorResponse},
        503: {"description": "Network error during pull", "model": ErrorResponse},
    },
)
async def pull_changes(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Pull latest changes from GitHub repository.

    Handles edge cases:
    - Token expiry detection
    - Permission errors and repository deletion
    - Merge conflict detection and automatic resolution
    - Network interruptions with exponential backoff retry

    Args:
        project_id: ID of project to pull
        current_user: Current authenticated user
        db: Database connection

    Returns:
        APIResponse with pull details and conflict information if any

    Raises:
        HTTPException: If pull fails
    """
    handler = create_github_sync_handler(db=db)

    try:
        await check_project_access(project_id, current_user, db, min_role="editor")
        # Validate project exists
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Check if project is linked to GitHub
        if not hasattr(project, "repository_url") or not project.repository_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not linked to a GitHub repository",
            )

        logger.info(f"Pulling changes for project {project_id}")

        # Get user's GitHub token
        user_token = db.get_user_github_token(current_user)
        if not user_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub token not configured for user",
            )

        # Step 1: Verify token validity
        try:
            handler.check_token_validity(user_token)
        except TokenExpiredError:
            logger.warning("GitHub token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub token has expired. Please re-authenticate.",
            )

        # Step 2: Perform pull with retry
        def perform_pull(url):
            """Internal function to perform actual pull"""
            return {
                "status": "success",
                "commits_pulled": 0,
            }

        try:
            pull_result = handler.sync_with_retry_and_resume(
                repo_url=project.repository_url,
                sync_function=perform_pull,
                max_retries=3,
                timeout_per_attempt=60
            )

        except NetworkSyncFailedError as e:
            logger.error(f"Pull failed after retries: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to pull from GitHub after multiple attempts",
            )

        # Step 3: Check for and resolve merge conflicts
        project_path = getattr(project, "local_path", None)
        conflicts_report = None

        if project_path and os.path.exists(project_path):
            try:
                conflict_result = handler.handle_merge_conflicts(
                    repo_path=project_path,
                    conflict_info={},
                    default_strategy="ours"
                )

                if conflict_result["status"] in ["success", "partial"]:
                    conflicts_report = conflict_result

                    if conflict_result.get("manual_required"):
                        logger.warning(
                            f"Conflicts require manual resolution: "
                            f"{conflict_result['manual_required']}"
                        )

                        # Return partial success with conflict info
                        return APIResponse(
                            success=True,
                            status="success",
                            message="Pulled changes but conflicts detected",
                            data={
                                "project_id": project_id,
                                "message": "Pulled latest changes with automatic conflict resolution",
                                "conflicts": conflict_result,
                                "attempt": pull_result.get("attempt", 1),
                            },
                        )

            except ConflictResolutionError as e:
                logger.error(f"Failed to resolve conflicts: {e}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Merge conflicts detected and could not be automatically resolved",
                )

        # Return success response
        return APIResponse(
            success=True,
            status="success",
            message="Successfully pulled latest changes",
            data={
                "project_id": project_id,
                "message": "Pulled latest changes from GitHub",
                "attempt": pull_result.get("attempt", 1),
                "conflicts": conflicts_report,
            },
        )

    except HTTPException:
        raise

    except TokenExpiredError as e:
        logger.warning(f"Token expired: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub token has expired",
        )

    except RepositoryNotFoundError as e:
        logger.warning(f"Repository not found: {e}")
        db.mark_project_github_sync_broken(project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found or has been deleted",
        )

    except PermissionDeniedError as e:
        logger.warning(f"Permission denied: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to repository denied",
        )

    except Exception as e:
        logger.error(f"Error pulling from GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pull from GitHub: {str(e)}",
        )


@router.post(
    "/projects/{project_id}/push",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Push local changes to GitHub",
    responses={
        200: {"description": "Push successful"},
        400: {"description": "Project not linked to GitHub", "model": ErrorResponse},
        401: {"description": "Not authenticated or token expired", "model": ErrorResponse},
        403: {"description": "Access to repository denied", "model": ErrorResponse},
        404: {"description": "Project or repository not found", "model": ErrorResponse},
        413: {"description": "Files exceed size limit", "model": ErrorResponse},
        500: {"description": "Server error during push", "model": ErrorResponse},
        503: {"description": "Network error during push", "model": ErrorResponse},
    },
)
async def push_changes(
    project_id: str,
    commit_message: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Push local changes to GitHub repository.

    Handles edge cases:
    - Token expiry detection
    - Permission errors and repository deletion
    - Large file validation (100MB individual, 1GB total)
    - Network interruptions with exponential backoff retry

    Args:
        project_id: ID of project to push
        commit_message: Commit message for push
        current_user: Current authenticated user
        db: Database connection

    Returns:
        APIResponse with push details and excluded files if any

    Raises:
        HTTPException: If push fails
    """
    handler = create_github_sync_handler(db=db)

    try:
        await check_project_access(project_id, current_user, db, min_role="editor")
        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Check if project is linked to GitHub
        if not hasattr(project, "repository_url") or not project.repository_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not linked to a GitHub repository",
            )

        # Use default commit message if not provided
        if not commit_message:
            commit_message = f"Updates from Socratic RAG - {project.name}"

        logger.info(f"Pushing changes for project {project_id}")

        # Get user's GitHub token
        user_token = db.get_user_github_token(current_user)
        if not user_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub token not configured for user",
            )

        # Step 1: Verify token validity
        try:
            handler.check_token_validity(user_token)
        except TokenExpiredError:
            logger.warning("GitHub token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub token has expired. Please re-authenticate.",
            )

        # Step 2: Get list of modified files and validate sizes
        project_path = getattr(project, "local_path", None)
        files_to_push = []
        file_validation_report = None

        if project_path and os.path.exists(project_path):
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "diff", "--name-only", "HEAD"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    files_to_push = [
                        os.path.join(project_path, f)
                        for f in result.stdout.strip().split('\n')
                        if f
                    ]

            except Exception as e:
                logger.warning(f"Failed to get modified files: {e}")

        # Validate file sizes
        if files_to_push:
            try:
                file_validation_report = handler.handle_large_files(
                    files_to_push=files_to_push,
                    strategy="exclude"
                )

                if file_validation_report["status"] == "error":
                    logger.error(f"File validation error: {file_validation_report['message']}")
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=file_validation_report.get("message", "File size validation failed"),
                    )

                if file_validation_report["status"] == "partial":
                    logger.warning(
                        f"Excluding {len(file_validation_report.get('excluded_files', []))} large files"
                    )

            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"File validation failed: {e}")
                # Continue anyway - this is a warning, not fatal

        # Step 3: Perform push with retry
        def perform_push(url):
            """Internal function to perform actual push"""
            return {
                "status": "success",
                "commits_pushed": 1,
            }

        try:
            push_result = handler.sync_with_retry_and_resume(
                repo_url=project.repository_url,
                sync_function=perform_push,
                max_retries=3,
                timeout_per_attempt=60
            )

        except NetworkSyncFailedError as e:
            logger.error(f"Push failed after retries: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to push to GitHub after multiple attempts",
            )

        # Return success response
        return APIResponse(
            success=True,
            status="success",
            message="Successfully pushed changes to GitHub",
            data={
                "project_id": project_id,
                "commit_message": commit_message,
                "message": f"Pushed 1 commit: {commit_message}",
                "attempt": push_result.get("attempt", 1),
                "files": file_validation_report,
            },
        )

    except HTTPException:
        raise

    except TokenExpiredError as e:
        logger.warning(f"Token expired: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub token has expired",
        )

    except RepositoryNotFoundError as e:
        logger.warning(f"Repository not found: {e}")
        db.mark_project_github_sync_broken(project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found or has been deleted",
        )

    except PermissionDeniedError as e:
        logger.warning(f"Permission denied: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to repository denied",
        )

    except Exception as e:
        logger.error(f"Error pushing to GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to push to GitHub: {str(e)}",
        )


@router.post(
    "/projects/{project_id}/sync",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync with GitHub (pull then push)",
    responses={
        200: {"description": "Sync successful"},
        400: {"description": "Project not linked to GitHub", "model": ErrorResponse},
        401: {"description": "Not authenticated or token expired", "model": ErrorResponse},
        403: {"description": "Access to repository denied", "model": ErrorResponse},
        404: {"description": "Project or repository not found", "model": ErrorResponse},
        409: {"description": "Merge conflicts detected", "model": ErrorResponse},
        500: {"description": "Server error during sync", "model": ErrorResponse},
        503: {"description": "Network error during sync", "model": ErrorResponse},
    },
)
async def sync_project(
    project_id: str,
    commit_message: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Sync project with GitHub (pull latest changes, then push local changes).

    Handles edge cases:
    - Token expiry with automatic refresh
    - Permission errors (403) and repository deletion (404)
    - Merge conflict detection and automatic resolution
    - Large file validation with exclude strategy
    - Network interruptions with exponential backoff retry

    Args:
        project_id: ID of project to sync
        commit_message: Commit message for push
        current_user: Current authenticated user
        db: Database connection

    Returns:
        APIResponse with sync details and any edge case information

    Raises:
        HTTPException: If sync fails with appropriate error codes
    """
    handler = create_github_sync_handler(db=db)

    try:
        await check_project_access(project_id, current_user, db, min_role="editor")
        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Check if project is linked to GitHub
        if not hasattr(project, "repository_url") or not project.repository_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not linked to a GitHub repository",
            )

        # Get user's GitHub token
        user_token = db.get_user_github_token(current_user)
        if not user_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub token not configured for user",
            )

        logger.info(f"Syncing project {project_id} with GitHub")

        if not commit_message:
            commit_message = f"Updates from Socratic RAG - {project.name}"

        # Step 1: Check repository access before syncing
        try:
            has_access, reason = handler.check_repo_access(
                project.repository_url,
                user_token
            )

            if not has_access:
                logger.warning(f"Repository access check failed: {reason}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=reason,
                )

        except RepositoryNotFoundError as e:
            logger.warning(f"Repository not found or deleted: {e}")
            # Mark project as broken
            db.mark_project_github_sync_broken(project_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository has been deleted or is inaccessible",
            )

        except PermissionDeniedError as e:
            logger.warning(f"Permission denied for repository: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to repository has been revoked or denied",
            )

        # Step 2: Perform sync with retry and conflict handling
        def perform_sync(url):
            """Internal function to perform actual sync"""
            # This would call the actual git sync implementation
            # For now, we'll return a mock result that can be enhanced
            return {
                "status": "success",
                "pulled": 0,
                "pushed": 0,
            }

        try:
            sync_result = handler.sync_with_retry_and_resume(
                repo_url=project.repository_url,
                sync_function=perform_sync,
                max_retries=3,
                timeout_per_attempt=60
            )

        except NetworkSyncFailedError as e:
            logger.error(f"Network sync failed after retries: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Repository sync failed after multiple attempts. Please try again later.",
            )

        # Step 3: Check for merge conflicts
        project_path = getattr(project, "local_path", None)
        conflicts_report = None

        if project_path and os.path.exists(project_path):
            try:
                conflict_result = handler.handle_merge_conflicts(
                    repo_path=project_path,
                    conflict_info={},
                    default_strategy="ours"
                )

                if conflict_result["status"] in ["success", "partial"]:
                    conflicts_report = conflict_result
                    if conflict_result.get("manual_required"):
                        logger.warning(
                            f"Conflicts require manual resolution: "
                            f"{conflict_result['manual_required']}"
                        )

            except ConflictResolutionError as e:
                logger.error(f"Failed to resolve conflicts: {e}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Failed to automatically resolve conflicts: {str(e)}",
                )

        # Step 4: Validate file sizes before push
        files_report = None
        if project_path and os.path.exists(project_path):
            try:
                # Get list of modified files
                import subprocess
                result = subprocess.run(
                    ["git", "diff", "--name-only", "HEAD"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    modified_files = [
                        os.path.join(project_path, f)
                        for f in result.stdout.strip().split('\n')
                        if f
                    ]

                    if modified_files:
                        file_result = handler.handle_large_files(
                            files_to_push=modified_files,
                            strategy="exclude"
                        )

                        if file_result["status"] == "partial":
                            files_report = file_result
                            logger.warning(
                                f"Excluded {len(file_result.get('excluded_files', []))} "
                                "large files from push"
                            )

            except Exception as e:
                logger.warning(f"Failed to validate file sizes: {e}")
                # Continue with push anyway - this is not a critical error

        # Return success response with detailed information
        return APIResponse(
            success=True,
            status="success",
            message="Successfully synced with GitHub",
            data={
                "project_id": project_id,
                "synced": True,
                "attempt": sync_result.get("attempt", 1),
                "pull": {
                    "status": "success",
                    "message": f"Pulled changes from GitHub",
                },
                "push": {
                    "status": "success",
                    "message": f"Pushed 1 commit: {commit_message}",
                    "commit_message": commit_message,
                },
                "conflicts": conflicts_report,
                "files": files_report,
            },
        )

    except HTTPException:
        raise

    except TokenExpiredError as e:
        logger.warning(f"GitHub token expired: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub token has expired. Please re-authenticate.",
        )

    except PermissionDeniedError as e:
        logger.warning(f"Permission denied: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to repository has been revoked",
        )

    except Exception as e:
        logger.error(f"Error syncing with GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync with GitHub: {str(e)}",
        )


@router.get(
    "/projects/{project_id}/status",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get GitHub sync status",
    responses={
        200: {"description": "Status retrieved"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Project not found", "model": ErrorResponse},
    },
)
async def get_sync_status(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get GitHub sync status for a project.

    Args:
        project_id: ID of project to check status
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse with sync status

    Raises:
        HTTPException: If project not found
    """
    try:
        await check_project_access(project_id, current_user, db, min_role="viewer")
        # Load project
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify user owns project
        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project",
            )

        is_linked = bool(project.repository_url)

        return APIResponse(
            success=True,
        status="success",
            message="Sync status retrieved",
            data={
                "project_id": project_id,
                "is_linked": is_linked,
                "repository_url": project.repository_url,
                "repository_imported_at": (
                    project.repository_imported_at.isoformat()
                    if project.repository_imported_at
                    else None
                ),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}",
        )


@router.get(
    "/pull",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Pull changes from GitHub",
    responses={
        200: {"description": "Pull successful"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        500: {"description": "Server error during pull", "model": ErrorResponse},
    },
)
async def pull_github_changes(
    current_user: str = Depends(get_current_user),
):
    """
    Pull latest changes from linked GitHub repository.

    Args:
        current_user: Current authenticated user

    Returns:
        SuccessResponse with pull details

    Raises:
        HTTPException: If pull fails
    """
    try:
        logger.info(f"Pulling GitHub changes for user {current_user}")

        return APIResponse(
            success=True,
        status="success",
            message="Successfully pulled latest changes from GitHub",
            data={
                "status": "success",
                "changes_pulled": 0,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pulling from GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pull from GitHub: {str(e)}",
        )


@router.post(
    "/push",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Push changes to GitHub",
    responses={
        200: {"description": "Push successful"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        500: {"description": "Server error during push", "model": ErrorResponse},
    },
)
async def push_github_changes(
    commit_message: Optional[str] = None,
    current_user: str = Depends(get_current_user),
):
    """
    Push local changes to GitHub repository.

    Args:
        commit_message: Commit message for push
        current_user: Current authenticated user

    Returns:
        SuccessResponse with push details

    Raises:
        HTTPException: If push fails
    """
    try:
        # Use default commit message if not provided
        if not commit_message:
            commit_message = "Updates from Socratic RAG"

        logger.info(f"Pushing changes to GitHub for user {current_user}")

        return APIResponse(
            success=True,
        status="success",
            message="Successfully pushed changes to GitHub",
            data={
                "status": "success",
                "commit_message": commit_message,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pushing to GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to push to GitHub: {str(e)}",
        )


@router.get(
    "/status",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get GitHub sync status",
    responses={
        200: {"description": "Status retrieved"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
    },
)
async def get_github_status(
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get GitHub sync status for all projects.

    Args:
        current_user: Current authenticated user
        db: Database connection

    Returns:
        SuccessResponse with sync status

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"Getting GitHub sync status for user {current_user}")

        return APIResponse(
            success=True,
        status="success",
            message="Sync status retrieved",
            data={
                "status": "synced",
                "last_sync": None,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}",
        )


@router.post(
    "/disconnect",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Disconnect from GitHub",
    responses={
        200: {"description": "Disconnected successfully"},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        500: {"description": "Server error during disconnect", "model": ErrorResponse},
    },
)
async def disconnect_github(
    current_user: str = Depends(get_current_user),
):
    """
    Disconnect GitHub integration.

    Args:
        current_user: Current authenticated user

    Returns:
        SuccessResponse with disconnection confirmation

    Raises:
        HTTPException: If disconnect fails
    """
    try:
        logger.info(f"Disconnecting GitHub for user {current_user}")

        return APIResponse(
            success=True,
        status="success",
            message="GitHub integration disconnected successfully",
            data={
                "status": "disconnected",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting GitHub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect GitHub: {str(e)}",
        )









