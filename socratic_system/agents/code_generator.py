"""
Code generation agent for Socratic RAG System
"""

from typing import Any, Dict

from socratic_system.models import ProjectContext

from .base import Agent


class CodeGeneratorAgent(Agent):
    """Generates code and documentation based on project context"""

    def __init__(self, orchestrator):
        super().__init__("CodeGenerator", orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process artifact generation requests"""
        action = request.get("action")

        if action == "generate_artifact":
            return self._generate_artifact(request)
        elif action == "generate_documentation":
            return self._generate_documentation(request)
        # Legacy support
        elif action == "generate_script":
            return self._generate_artifact(request)

        return {"status": "error", "message": "Unknown action"}

    def _generate_artifact(self, request: Dict) -> Dict:
        """Generate project-type-appropriate artifact"""
        project = request.get("project")

        # Build comprehensive context
        context = self._build_generation_context(project)

        # Generate artifact based on project type
        artifact = self.orchestrator.claude_client.generate_artifact(context, project.project_type)

        # Determine artifact type for documentation
        artifact_type_map = {
            "software": "code",
            "business": "business_plan",
            "research": "research_protocol",
            "creative": "creative_brief",
            "marketing": "marketing_plan",
            "educational": "curriculum",
        }
        artifact_type = artifact_type_map.get(project.project_type, "code")

        self.log(f"Generated {artifact_type} for {project.project_type} project '{project.name}'")

        return {
            "status": "success",
            "artifact": artifact,
            "artifact_type": artifact_type,
            "script": artifact,  # Legacy compatibility
            "context_used": context,
        }

    def _generate_documentation(self, request: Dict) -> Dict:
        """Generate documentation for project artifact"""
        project = request.get("project")
        artifact = request.get("artifact") or request.get("script")  # Support both

        if not project or not artifact:
            return {"status": "error", "message": "Project and artifact are required"}

        # Determine artifact type
        artifact_type_map = {
            "software": "code",
            "business": "business_plan",
            "research": "research_protocol",
            "creative": "creative_brief",
            "marketing": "marketing_plan",
            "educational": "curriculum",
        }
        artifact_type = artifact_type_map.get(project.project_type, "code")

        documentation = self.orchestrator.claude_client.generate_documentation(
            project, artifact, artifact_type
        )

        self.log(f"Generated documentation for {artifact_type}")

        return {
            "status": "success",
            "documentation": documentation,
        }

    def _build_generation_context(self, project: ProjectContext) -> str:
        """Build comprehensive context for code generation"""
        context_parts = [
            f"Project: {project.name}",
            f"Phase: {project.phase}",
            f"Goals: {project.goals}",
            f"Tech Stack: {', '.join(project.tech_stack)}",
            f"Requirements: {', '.join(project.requirements)}",
            f"Constraints: {', '.join(project.constraints)}",
            f"Target: {project.deployment_target}",
            f"Style: {project.code_style}",
        ]

        # Add conversation insights
        if project.conversation_history:
            recent_responses = project.conversation_history[-5:]
            context_parts.append("Recent Discussion:")
            for msg in recent_responses:
                if msg.get("type") == "user":
                    context_parts.append(f"- {msg['content']}")

        return "\n".join(context_parts)
