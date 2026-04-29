"""
Code Service - Encapsulates code generation and artifact management.

Handles:
- Code generation via Claude
- Code validation
- Artifact persistence
- Multi-file management

No orchestrator dependency - uses dependency injection for all external services.
"""

from typing import Any, Dict, List, Optional

from socratic_nexus.clients import ClaudeClient

from socratic_system.config import SocratesConfig
from socratic_system.models import ProjectContext
from socratic_system.services.base import Service


class CodeService(Service):
    """
    Service for code generation and artifact management.

    Centralizes code generation logic with proper error handling
    and multi-file support.
    """

    def __init__(
        self,
        config: SocratesConfig,
        claude_client: ClaudeClient,
    ):
        """
        Initialize code service.

        Args:
            config: SocratesConfig instance
            claude_client: ClaudeClient for code generation
        """
        super().__init__(config)
        self.claude_client = claude_client

    def generate_artifact(
        self,
        project: ProjectContext,
        artifact_type: str = "code",
        language: str = "python",
        user_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate code artifact for a project.

        Args:
            project: The ProjectContext
            artifact_type: Type of artifact (code, documentation, tests)
            language: Programming language
            user_id: Optional user ID
            **kwargs: Additional parameters

        Returns:
            Dictionary containing generated artifact
        """
        if not project:
            raise ValueError("Project is required")

        self.log_info(
            f"Generating {artifact_type} artifact for {project.project_id} "
            f"in {language}"
        )

        # Call Claude API for generation
        artifact = self.claude_client.generate_artifact(
            project=project,
            artifact_type=artifact_type,
            language=language,
            user_id=user_id,
            **kwargs,
        )

        self.log_info(f"Generated artifact of {len(str(artifact))} characters")
        return artifact

    def generate_code(
        self,
        project: ProjectContext,
        language: str = "python",
        user_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate code for a project.

        Args:
            project: The ProjectContext
            language: Programming language
            user_id: Optional user ID
            **kwargs: Additional parameters

        Returns:
            Generated code as string
        """
        artifact = self.generate_artifact(
            project=project,
            artifact_type="code",
            language=language,
            user_id=user_id,
            **kwargs,
        )

        return artifact.get("code", "")

    def generate_documentation(
        self,
        project: ProjectContext,
        doc_type: str = "readme",
        user_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate documentation for a project.

        Args:
            project: The ProjectContext
            doc_type: Type of documentation (readme, api, architecture)
            user_id: Optional user ID
            **kwargs: Additional parameters

        Returns:
            Generated documentation as string
        """
        artifact = self.generate_artifact(
            project=project,
            artifact_type="documentation",
            language="markdown",
            user_id=user_id,
            **kwargs,
        )

        return artifact.get("documentation", "")

    def generate_tests(
        self,
        project: ProjectContext,
        language: str = "python",
        framework: str = "pytest",
        user_id: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, str]]:
        """
        Generate test cases for a project.

        Args:
            project: The ProjectContext
            language: Programming language
            framework: Testing framework
            user_id: Optional user ID
            **kwargs: Additional parameters

        Returns:
            List of test files with content
        """
        artifact = self.generate_artifact(
            project=project,
            artifact_type="tests",
            language=language,
            user_id=user_id,
            framework=framework,
            **kwargs,
        )

        # Return as list of file dictionaries
        tests = artifact.get("tests", [])
        if isinstance(tests, str):
            return [{"filename": f"test_{project.project_id}.py", "content": tests}]

        return tests

    def validate_code(
        self,
        code: str,
        language: str = "python",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate generated code for syntax and basic errors.

        Args:
            code: Code to validate
            language: Programming language
            user_id: Optional user ID

        Returns:
            Dictionary containing validation results
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        self.log_info(f"Validating {language} code")

        # Basic syntax validation
        errors = []
        warnings = []

        # Language-specific validation
        if language == "python":
            errors.extend(self._validate_python(code))
        elif language == "javascript":
            errors.extend(self._validate_javascript(code))
        elif language == "java":
            errors.extend(self._validate_java(code))

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "language": language,
        }

    def split_code_into_files(
        self,
        code: str,
        project_structure: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Split monolithic code into multiple files based on structure.

        Args:
            code: The complete code
            project_structure: Optional structure template

        Returns:
            Dictionary mapping filenames to code content
        """
        # This would use a code splitter utility
        # For now, return as single file
        return {"main.py": code}

    # Private validation methods

    def _validate_python(self, code: str) -> List[str]:
        """Validate Python code."""
        errors = []

        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Compilation error: {e}")

        return errors

    def _validate_javascript(self, code: str) -> List[str]:
        """Validate JavaScript code (basic checks)."""
        errors = []

        # Basic checks for common JS issues
        if code.count("{") != code.count("}"):
            errors.append("Mismatched braces")
        if code.count("(") != code.count(")"):
            errors.append("Mismatched parentheses")

        return errors

    def _validate_java(self, code: str) -> List[str]:
        """Validate Java code (basic checks)."""
        errors = []

        if code.count("{") != code.count("}"):
            errors.append("Mismatched braces")
        if code.count("(") != code.count(")"):
            errors.append("Mismatched parentheses")

        return errors
