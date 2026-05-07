"""Code service - encapsulates code generation and management."""

from typing import TYPE_CHECKING, Any, Dict, Optional

from .base import Service

if TYPE_CHECKING:
    from socratic_agents import SocraticAgentsSystem

    from socratic_system.models import ProjectContext


class CodeService(Service):
    """Service for code generation and project artifact management.

    Phase 3: Refactored to use SocraticAgentsSystem instead of orchestrator.
    """

    def __init__(self, config, system: "SocraticAgentsSystem"):
        """Initialize code service.

        Args:
            config: Socrates configuration
            system: SocraticAgentsSystem instance
        """
        super().__init__(config)
        self.system = system

    def generate_code(
        self,
        project: "ProjectContext",
        language: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate code for project.

        Args:
            project: ProjectContext
            language: Programming language
            user_id: User identifier

        Returns:
            Generated code dict
        """
        self.logger.info(f"Generating code for project {project.project_id}")

        result = self.system.process_request(
            "code_generator",
            {
                "action": "generate_script",
                "project": project,
                "language": language,
                "user_id": user_id,
            },
        )

        return result

    def validate_code(
        self,
        project: "ProjectContext",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate project code.

        Args:
            project: ProjectContext
            user_id: User identifier

        Returns:
            Validation results
        """
        self.logger.info(f"Validating code for project {project.project_id}")

        result = self.system.process_request(
            "code_validation",
            {
                "action": "validate_project",
                "project": project,
                "user_id": user_id,
            },
        )

        return result
