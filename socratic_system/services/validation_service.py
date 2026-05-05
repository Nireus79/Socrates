"""Validation service - encapsulates code and project validation."""

from typing import TYPE_CHECKING, Dict, Any, Optional

from .base import Service

if TYPE_CHECKING:
    from socratic_agents import SocraticAgentsSystem


class ValidationService(Service):
    """Service for validating code and projects.

    Phase 3: Refactored to use SocraticAgentsSystem instead of orchestrator.
    """

    def __init__(self, config, system: "SocraticAgentsSystem"):
        """Initialize validation service.

        Args:
            config: Socrates configuration
            system: SocraticAgentsSystem instance
        """
        super().__init__(config)
        self.system = system

    def run_tests(
        self,
        project_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run tests for a project.

        Args:
            project_id: Project identifier
            user_id: User identifier

        Returns:
            Test results
        """
        self.logger.info(f"Running tests for project {project_id}")

        result = self.system.process_request(
            "code_validation",
            {
                "action": "run_tests",
                "project_id": project_id,
                "user_id": user_id,
            },
        )

        return result

    def validate_syntax(
        self,
        code: str,
        language: str,
    ) -> Dict[str, Any]:
        """Validate code syntax.

        Args:
            code: Code to validate
            language: Programming language

        Returns:
            Validation results
        """
        self.logger.info(f"Validating {language} syntax")

        result = self.system.process_request(
            "code_validation",
            {
                "action": "validate_code",
                "code": code,
                "language": language,
            },
        )

        return result
