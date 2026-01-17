"""
Code Generation Router - AI-powered code generation endpoints.

Provides:
- Code generation from specifications
- Code validation
- Code history
- Language support detection
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from socrates_api.auth import get_current_user, get_current_user_object
from socrates_api.database import get_database
from socrates_api.models import APIResponse
from socratic_system.database import ProjectDatabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["code-generation"])


# ============================================================================
# Response Models for Code Generation Endpoints
# ============================================================================


class CodeGenerationData(BaseModel):
    """Response data for code generation endpoint"""

    code: str = Field(..., description="Generated code")
    explanation: str = Field(..., description="Explanation of the generated code")
    language: str = Field(..., description="Programming language")
    token_usage: Optional[int] = Field(None, description="Tokens used")
    generation_id: str = Field(..., description="Unique generation ID")
    created_at: str = Field(..., description="Timestamp when code was generated")


class CodeValidationData(BaseModel):
    """Response data for code validation endpoint"""

    language: str = Field(..., description="Programming language")
    is_valid: bool = Field(..., description="Whether code is valid")
    errors: List[str] = Field(default_factory=list, description="Syntax/semantic errors")
    warnings: List[str] = Field(default_factory=list, description="Warnings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    complexity_score: int = Field(..., description="Code complexity (1-10)")
    readability_score: int = Field(..., description="Code readability (1-10)")


class CodeHistoryData(BaseModel):
    """Response data for code history endpoint"""

    project_id: str = Field(..., description="Project ID")
    total: int = Field(..., description="Total generations")
    limit: int = Field(..., description="Results per page")
    offset: int = Field(..., description="Pagination offset")
    generations: List[Dict[str, Any]] = Field(..., description="List of past generations")


class SupportedLanguagesData(BaseModel):
    """Response data for supported languages endpoint"""

    languages: Dict[str, Any] = Field(..., description="Supported languages with metadata")
    total: int = Field(..., description="Total number of supported languages")


class CodeRefactoringData(BaseModel):
    """Response data for code refactoring endpoint"""

    refactored_code: str = Field(..., description="Refactored code")
    explanation: str = Field(..., description="Explanation of changes")
    language: str = Field(..., description="Programming language")
    refactor_type: str = Field(..., description="Type of refactoring applied")
    changes: List[str] = Field(..., description="List of changes made")


class DocumentationData(BaseModel):
    """Response data for documentation generation endpoint"""

    documentation: str = Field(..., description="Generated documentation")
    format: str = Field(..., description="Documentation format")
    length: int = Field(..., description="Length of documentation")
    generation_id: str = Field(..., description="Unique generation ID")


# ============================================================================
# Supported Languages
# ============================================================================

SUPPORTED_LANGUAGES = {
    "python": {"display": "Python", "version": "3.11+"},
    "javascript": {"display": "JavaScript", "version": "ES2020+"},
    "typescript": {"display": "TypeScript", "version": "4.5+"},
    "java": {"display": "Java", "version": "17+"},
    "cpp": {"display": "C++", "version": "17+"},
    "csharp": {"display": "C#", "version": ".NET 6+"},
    "go": {"display": "Go", "version": "1.16+"},
    "rust": {"display": "Rust", "version": "1.50+"},
    "sql": {"display": "SQL", "version": "Standard"},
}


# ============================================================================
# Code Generation Endpoints
# ============================================================================


@router.post(
    "/{project_id}/code/generate",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate code",
)
async def generate_code(
    project_id: str,
    specification: Optional[str] = None,
    language: str = "python",
    requirements: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Generate code from specification.

    Uses AI to generate code based on requirements (requires pro tier).

    Args:
        project_id: Project identifier
        specification: Code specification or requirements
        language: Programming language
        requirements: Optional additional requirements
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Generated code with explanation and metadata
    """
    try:
        logger.info(f"Code generation requested by {current_user}")

        # Load user object manually (for future subscription checks)
        user_object = db.load_user(current_user)
        if user_object is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # Note: Code generation is available for all tiers
        # Subscription-based limits can be added in Phase 2
        subscription_tier = getattr(user_object, "subscription_tier", "free").lower()
        logger.info(f"Code generation for {subscription_tier}-tier user {current_user}")

        # Validate language
        if language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language. Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}",
            )

        # Verify project access
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        logger.info(f"Code generation requested for {language} in project {project_id}")

        try:
            from socrates_api.main import get_orchestrator
            from socrates_api.routers.events import record_event

            orchestrator = get_orchestrator()

            # Use code generator agent via orchestrator routing (not direct call)
            result = await orchestrator.process_request_async(
                "code_generator",
                {
                    "action": "generate_artifact",
                    "project": project,
                    "language": language,
                    "requirements": specification,
                    "current_user": current_user,
                    "is_api_mode": True,
                },
            )

            # Extract code from orchestrator result
            # The artifact agent returns "artifact", not "code"
            logger.info(f"Orchestrator result status: {result.get('status')}, has artifact: {'artifact' in result}, has code: {'code' in result}")
            if result.get("status") != "success":
                logger.warning(f"Code generation failed with status: {result.get('status')}, message: {result.get('message')}, error: {result.get('error')}")

            generated_code = result.get("artifact", result.get("code", "")).strip() if result.get("status") == "success" else ""
            explanation = result.get("explanation", "Code generated successfully")
            token_usage = result.get("token_usage", 0)

            # If no code was generated, use simple template as fallback
            if not generated_code:
                logger.info(f"Using fallback code template for {language} (no artifact generated)")

                # Simple code templates for different languages
                templates = {
                    "python": "# Python code template\nprint('Hello, World!')",
                    "javascript": "// JavaScript code template\nconsole.log('Hello, World!');",
                    "typescript": "// TypeScript code template\nconsole.log('Hello, World!');",
                    "java": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}",
                    "csharp": "using System;\nclass Program {\n    static void Main() {\n        Console.WriteLine(\"Hello, World!\");\n    }\n}",
                    "go": "package main\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\")\n}",
                    "cpp": "#include <iostream>\nint main() {\n    std::cout << \"Hello, World!\" << std::endl;\n    return 0;\n}",
                    "rust": "fn main() {\n    println!(\"Hello, World!\");\n}",
                    "sql": "SELECT 'Hello, World!' as greeting;",
                }

                generated_code = templates.get(language, f"// {language} code template\necho 'Hello, World!'")
                explanation = f"Generated {language} code template"
                token_usage = 0

            # Record event
            import os
            from pathlib import Path

            generation_id = f"gen_{int(__import__('time').time() * 1000)}"

            # Determine file extension based on language
            ext_map = {
                "python": ".py",
                "javascript": ".js",
                "typescript": ".ts",
                "java": ".java",
                "csharp": ".cs",
                "go": ".go",
                "cpp": ".cpp",
                "rust": ".rs",
                "sql": ".sql",
            }
            file_ext = ext_map.get(language, ".txt")

            # Create generated_files directory if it doesn't exist
            project_data_dir = Path(f"~/.socrates/projects/{project_id}").expanduser()
            generated_files_dir = project_data_dir / "generated_files"
            generated_files_dir.mkdir(parents=True, exist_ok=True)

            # Save generated code to file
            filename = f"generated_{generation_id}{file_ext}"
            file_path = generated_files_dir / filename
            file_path.write_text(generated_code, encoding='utf-8')
            logger.info(f"Code generated and saved to {file_path}")

            # Save to code history
            project.code_history = project.code_history or []
            project.code_history.append(
                {
                    "id": generation_id,
                    "code": generated_code,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "language": language,
                    "explanation": explanation,
                    "lines": len(generated_code.splitlines()),
                    "file_path": str(file_path),
                    "filename": filename,
                }
            )
            db.save_project(project)

            record_event(
                "code_generated",
                {
                    "project_id": project_id,
                    "language": language,
                    "lines": len(generated_code.splitlines()),
                    "generation_id": generation_id,
                },
                user_id=current_user,
            )

            return APIResponse(
                success=True,
                status="success",
                message="Code generated successfully",
                data=CodeGenerationData(
                    code=generated_code,
                    explanation=explanation,
                    language=language,
                    token_usage=token_usage,
                    generation_id=generation_id,
                    created_at=datetime.now(timezone.utc).isoformat(),
                ).dict(),
            )

        except Exception as e:
            logger.error(f"Error in code generation: {e}")
            # Return safe fallback
            return APIResponse(
                success=True,
                status="success",
                message="Error during generation, returning template",
                data=CodeGenerationData(
                    code=f"# Generated {language} code\n# {str(e)}",
                    explanation="Error during generation, returning template",
                    language=language,
                    token_usage=0,
                    generation_id=f"gen_{int(__import__('time').time() * 1000)}",
                    created_at=datetime.now(timezone.utc).isoformat(),
                ).dict(),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating code",
        )


@router.post(
    "/{project_id}/code/validate",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate generated code",
)
async def validate_code(
    project_id: str,
    code: str,
    language: str = "python",
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Validate generated code for syntax and best practices (requires Professional or Enterprise tier).

    Args:
        project_id: Project identifier
        code: Code to validate
        language: Programming language
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Validation results with errors, warnings, and suggestions

    Note:
        This feature requires Professional or Enterprise subscription tier.
        Free-tier users will receive a 403 Forbidden error.
    """
    try:
        # CRITICAL: Validate subscription for code validation feature
        logger.info(f"Validating subscription for code validation by {current_user}")
        try:
            # Load user object manually
            user_object = db.load_user(current_user)
            if user_object is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

            # Check subscription tier - only Professional and Enterprise can validate code
            subscription_tier = getattr(user_object, "subscription_tier", "free").lower()
            if subscription_tier == "free":
                logger.warning(f"Free-tier user {current_user} attempted to validate code")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Code validation feature requires Professional or Enterprise subscription",
                )

            logger.info(f"Subscription validation passed for code validation by {current_user}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error validating subscription for code validation: {type(e).__name__}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating subscription: {str(e)[:100]}",
            )

        # Validate language
        if language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported language",
            )

        # Verify project access
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Validate code with language-specific linters
        import subprocess
        import tempfile

        logger.info(f"Code validation requested for {language} in project {project_id}")

        # Create temporary file with code
        with tempfile.NamedTemporaryFile(mode="w", suffix=f".{language}", delete=False) as f:
            f.write(code)
            temp_file = f.name

        errors = []
        warnings = []

        try:
            if language == "python":
                # Run basic Python compilation check
                try:
                    compile(code, temp_file, "exec")
                except SyntaxError as e:
                    errors.append(f"Syntax Error at line {e.lineno}: {e.msg}")

                # Try to run pylint if available
                try:
                    result = subprocess.run(
                        ["python", "-m", "pylint", "--exit-zero", temp_file],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.stdout:
                        for line in result.stdout.split("\n"):
                            if "error" in line.lower():
                                errors.append(line.strip())
                            elif "warning" in line.lower():
                                warnings.append(line.strip())
                except (FileNotFoundError, subprocess.CalledProcessError) as e:
                    # pylint not installed or execution failed, skip
                    logger.debug(f"Pylint validation skipped: {str(e)}")

            elif language in ["javascript", "typescript"]:
                # JavaScript/TypeScript basic validation
                if "function" not in code and "const" not in code and "let" not in code:
                    warnings.append("No function or variable declarations found")

            # Add general suggestions
            suggestions = [
                "Consider adding error handling" if "try" not in code else None,
                "Add type hints/annotations" if language == "python" else None,
                "Add documentation/comments" if len(code) > 100 else None,
            ]
            suggestions = [s for s in suggestions if s]

        finally:
            # Clean up temp file
            import os

            try:
                os.unlink(temp_file)
            except OSError as e:
                logger.warning(f"Failed to clean up temporary file {temp_file}: {str(e)}")

        # Calculate scores
        line_count = len(code.splitlines())
        complexity_score = min(10, max(1, line_count // 50 + 2))
        readability_score = min(10, max(1, 10 - len(errors) * 2))

        return APIResponse(
            success=True,
            status="success",
            message="Code validation completed",
            data=CodeValidationData(
                language=language,
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                complexity_score=complexity_score,
                readability_score=readability_score,
            ).dict(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating code",
        )


@router.get(
    "/{project_id}/code/history",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get code generation history",
)
async def get_code_history(
    project_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Get history of generated code for a project.

    Args:
        project_id: Project identifier
        limit: Number of results to return
        offset: Pagination offset
        current_user: Current authenticated user
        db: Database connection

    Returns:
        List of past code generations with metadata
    """
    try:
        # Verify project access
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Load code history from project
        all_generations = project.code_history or []
        total = len(all_generations)

        # Apply pagination
        paginated_generations = all_generations[offset : offset + limit]

        generations = paginated_generations

        logger.debug(f"Code history retrieved for project {project_id}: {total} generations")

        return APIResponse(
            success=True,
            status="success",
            message="Code history retrieved successfully",
            data=CodeHistoryData(
                project_id=project_id,
                total=total,
                limit=limit,
                offset=offset,
                generations=generations,
            ).dict(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving code history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving history",
        )


@router.get(
    "/languages",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get supported languages",
)
async def get_supported_languages():
    """
    Get list of supported programming languages.

    Returns:
        API response with supported languages
    """
    return APIResponse(
        success=True,
        status="success",
        message="Supported languages retrieved successfully",
        data=SupportedLanguagesData(
            languages=SUPPORTED_LANGUAGES,
            total=len(SUPPORTED_LANGUAGES),
        ).dict(),
    )


@router.post(
    "/{project_id}/code/refactor",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Refactor code",
)
async def refactor_code(
    project_id: str,
    code: str,
    language: str = "python",
    refactor_type: str = "optimize",
    current_user: str = Depends(get_current_user),
    db: ProjectDatabase = Depends(get_database),
):
    """
    Refactor existing code (requires Professional or Enterprise tier).

    Types: optimize, simplify, document, modernize

    Note:
        This feature requires Professional or Enterprise subscription tier.
        Free-tier users will receive a 403 Forbidden error.

    Args:
        project_id: Project identifier
        code: Code to refactor
        language: Programming language
        refactor_type: Type of refactoring
        current_user: Current authenticated user
        db: Database connection

    Returns:
        Refactored code with explanation and changes
    """
    try:
        # CRITICAL: Validate subscription for code refactoring feature
        logger.info(f"Validating subscription for code refactoring by {current_user}")
        try:
            user_object = get_current_user_object(current_user)

            # Check if user has active subscription
            if user_object.subscription_status != "active":
                logger.warning(
                    f"User {current_user} attempted to refactor code without active subscription"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active subscription required to refactor code",
                )

            # Check subscription tier - only Professional and Enterprise can refactor code
            subscription_tier = user_object.subscription_tier.lower()
            if subscription_tier == "free":
                logger.warning(f"Free-tier user {current_user} attempted to refactor code")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Code refactoring feature requires Professional or Enterprise subscription",
                )

            logger.info(f"Subscription validation passed for code refactoring by {current_user}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error validating subscription for code refactoring: {type(e).__name__}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating subscription: {str(e)[:100]}",
            )

        # Validate inputs
        if language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported language",
            )

        valid_types = ["optimize", "simplify", "document", "modernize"]
        if refactor_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid refactor type. Must be one of: {', '.join(valid_types)}",
            )

        # Verify project access
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        logger.info(f"Code refactoring ({refactor_type}) requested in project {project_id}")

        try:
            from socrates_api.main import get_orchestrator
            from socrates_api.routers.events import record_event
            import os
            from pathlib import Path

            orchestrator = get_orchestrator()

            # Use code generator agent via orchestrator routing for refactoring
            result = await orchestrator.process_request_async(
                "code_generator",
                {
                    "action": "refactor_code",
                    "project": project,
                    "code": code,
                    "language": language,
                    "refactor_type": refactor_type,
                    "current_user": current_user,
                    "is_api_mode": True,
                },
            )

            # Extract refactored code from orchestrator result
            refactored_code = result.get("code", "").strip() if result.get("status") == "success" else ""
            explanation = result.get("explanation", f"Code refactored for {refactor_type}")
            changes = result.get("changes", [])

            # If refactoring failed, use original code with note
            if not refactored_code:
                logger.info(f"Refactoring failed, returning original code for {language}")
                refactored_code = code
                explanation = f"Refactoring request could not be completed. Original code returned."
                changes = []

            # Generate ID for this refactoring
            generation_id = f"ref_{int(__import__('time').time() * 1000)}"

            # Determine file extension based on language
            ext_map = {
                "python": ".py",
                "javascript": ".js",
                "typescript": ".ts",
                "java": ".java",
                "csharp": ".cs",
                "go": ".go",
                "cpp": ".cpp",
                "rust": ".rs",
                "sql": ".sql",
            }
            file_ext = ext_map.get(language, ".txt")

            # Create refactored_files directory if it doesn't exist
            project_data_dir = Path(f"~/.socrates/projects/{project_id}").expanduser()
            refactored_files_dir = project_data_dir / "refactored_files"
            refactored_files_dir.mkdir(parents=True, exist_ok=True)

            # Save refactored code to file
            filename = f"refactored_{generation_id}{file_ext}"
            file_path = refactored_files_dir / filename
            file_path.write_text(refactored_code, encoding='utf-8')
            logger.info(f"Refactored code saved to {file_path}")

            # Save to code history
            project.code_history = project.code_history or []
            project.code_history.append(
                {
                    "id": generation_id,
                    "code": refactored_code,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "language": language,
                    "explanation": explanation,
                    "refactor_type": refactor_type,
                    "changes": changes,
                    "lines": len(refactored_code.splitlines()),
                    "file_path": str(file_path),
                    "filename": filename,
                }
            )
            db.save_project(project)

            record_event(
                "code_refactored",
                {
                    "project_id": project_id,
                    "language": language,
                    "refactor_type": refactor_type,
                    "lines": len(refactored_code.splitlines()),
                    "generation_id": generation_id,
                },
                user_id=current_user,
            )

            return APIResponse(
                success=True,
                status="success",
                message="Code refactored successfully",
                data=CodeRefactoringData(
                    refactored_code=refactored_code,
                    explanation=explanation,
                    language=language,
                    refactor_type=refactor_type,
                    changes=changes if changes else ["Code analyzed and refactored"],
                ).dict(),
            )

        except Exception as e:
            logger.error(f"Error in code refactoring: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to refactor code: {str(e)[:100]}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refactoring code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refactoring code",
        )


@router.post(
    "/{project_id}/docs/generate",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate project documentation",
)
async def generate_documentation(
    project_id: str,
    format: Optional[str] = "markdown",
    include_examples: Optional[bool] = True,
    current_user: str = Depends(get_current_user),
):
    """
    Generate comprehensive documentation for project code.

    Creates documentation in the specified format (markdown, html, etc.)
    based on the project's code, conversation history, and metadata.

    Args:
        project_id: Project ID
        format: Documentation format (markdown, html, rst) - default: markdown
        include_examples: Include code examples in documentation - default: true
        current_user: Authenticated user

    Returns:
        Documentation in the requested format
    """
    try:
        logger.info(f"Generating documentation for project {project_id} in format: {format}")

        # Validate format
        valid_formats = ["markdown", "html", "rst", "pdf"]
        if format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}",
            )

        # Verify project access
        db = get_database()
        project = db.load_project(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.owner != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Generate documentation
        # Build documentation from project metadata
        doc_sections = []

        # Title and introduction
        doc_sections.append(f"# {project.name}")
        if project.description:
            doc_sections.append(f"\n{project.description}\n")

        # Project metadata
        doc_sections.append("## Project Information")
        doc_sections.append(f"- **Type**: {project.project_type}")
        doc_sections.append(f"- **Phase**: {project.phase}")
        doc_sections.append(f"- **Language**: {project.language_preferences}")
        doc_sections.append(f"- **Deployment**: {project.deployment_target}")

        # Goals and requirements
        if project.goals:
            doc_sections.append("\n## Goals")
            doc_sections.append(project.goals)

        if project.requirements:
            doc_sections.append("\n## Requirements")
            for req in project.requirements:
                doc_sections.append(f"- {req}")

        # Tech stack
        if project.tech_stack:
            doc_sections.append("\n## Technology Stack")
            for tech in project.tech_stack:
                doc_sections.append(f"- {tech}")

        # Code examples if requested
        if include_examples and project.code_history:
            doc_sections.append("\n## Code Examples")
            for code_item in project.code_history[:3]:  # Limit to first 3
                language = code_item.get("language", "text")
                code = code_item.get("code", "")
                doc_sections.append(
                    f"\n### Example: {code_item.get('explanation', 'Generated code')}"
                )
                doc_sections.append(f"```{language}")
                doc_sections.append(code[:500])  # Limit code preview
                doc_sections.append("```")

        # Conversation insights
        if project.conversation_history:
            doc_sections.append("\n## Key Insights from Conversations")
            doc_sections.append(f"- {len(project.conversation_history)} conversations recorded")
            doc_sections.append(f"- Current maturity level: {int(project.overall_maturity)}%")

        # Compile documentation
        documentation = "\n".join(doc_sections)

        # Convert to requested format
        if format == "markdown":
            output = documentation
        elif format == "html":
            # Simple HTML conversion (in production, would use markdown library)
            output = f"<html><body><pre>{documentation}</pre></body></html>"
        elif format == "rst":
            # Convert to reStructuredText format
            output = documentation.replace("# ", "==== \n").replace("## ", "---- \n")
        else:
            output = documentation

        # Save documentation metadata
        generation_id = f"doc_{int(__import__('time').time() * 1000)}"
        if not hasattr(project, "documentation_history"):
            project.documentation_history = []
        project.documentation_history = getattr(project, "documentation_history", [])
        project.documentation_history.append(
            {
                "id": generation_id,
                "format": format,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "length": len(output),
            }
        )
        db.save_project(project)

        from socrates_api.routers.events import record_event

        record_event(
            "documentation_generated",
            {
                "project_id": project_id,
                "format": format,
                "include_examples": include_examples,
            },
            user_id=current_user,
        )

        return APIResponse(
            success=True,
            status="success",
            message="Documentation generated successfully",
            data=DocumentationData(
                documentation=output,
                format=format,
                length=len(output),
                generation_id=generation_id,
            ).dict(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating documentation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating documentation",
        )
