"""
Code generation agent for Socratic RAG System
"""

from typing import Dict, Any

from socratic_system.models import ProjectContext
from .base import Agent


class CodeGeneratorAgent(Agent):
    """Generates code and documentation based on project context"""

    def __init__(self, orchestrator):
        super().__init__("CodeGenerator", orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process code generation requests"""
        action = request.get('action')

        if action == 'generate_script':
            return self._generate_script(request)
        elif action == 'generate_documentation':
            return self._generate_documentation(request)

        return {'status': 'error', 'message': 'Unknown action'}

    def _generate_script(self, request: Dict) -> Dict:
        """Generate code for the project"""
        project = request.get('project')

        # Build comprehensive context
        context = self._build_generation_context(project)

        # Generate using Claude
        script = self.orchestrator.claude_client.generate_code(context)

        self.log(f"Generated script for project '{project.name}'")

        return {
            'status': 'success',
            'script': script,
            'context_used': context
        }

    def _generate_documentation(self, request: Dict) -> Dict:
        """Generate documentation for code"""
        project = request.get('project')
        script = request.get('script')

        documentation = self.orchestrator.claude_client.generate_documentation(
            project, script
        )

        return {
            'status': 'success',
            'documentation': documentation
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
            f"Style: {project.code_style}"
        ]

        # Add conversation insights
        if project.conversation_history:
            recent_responses = project.conversation_history[-5:]
            context_parts.append("Recent Discussion:")
            for msg in recent_responses:
                if msg.get('type') == 'user':
                    context_parts.append(f"- {msg['content']}")

        return "\n".join(context_parts)
