"""
Context analysis agent for Socratic RAG System
"""

from typing import Dict, Any, List

from socratic_system.models import ProjectContext
from .base import Agent


class ContextAnalyzerAgent(Agent):
    """Analyzes project context and identifies patterns"""

    def __init__(self, orchestrator):
        super().__init__("ContextAnalyzer", orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process context analysis requests"""
        action = request.get('action')

        if action == 'analyze_context':
            return self._analyze_context(request)
        elif action == 'get_summary':
            return self._get_summary(request)
        elif action == 'find_similar':
            return self._find_similar(request)

        return {'status': 'error', 'message': 'Unknown action'}

    def _analyze_context(self, request: Dict) -> Dict:
        """Analyze project context and patterns"""
        project = request.get('project')

        # Analyze conversation patterns
        patterns = self._identify_patterns(project.conversation_history)

        # Get relevant knowledge
        relevant_knowledge = self.orchestrator.vector_db.search_similar(
            project.goals, top_k=5
        )

        return {
            'status': 'success',
            'patterns': patterns,
            'relevant_knowledge': relevant_knowledge
        }

    def get_context_summary(self, project: ProjectContext) -> str:
        """Generate comprehensive project summary"""
        summary_parts = []

        if project.goals:
            summary_parts.append(f"Goals: {project.goals}")
        if project.requirements:
            summary_parts.append(f"Requirements: {', '.join(project.requirements)}")
        if project.tech_stack:
            summary_parts.append(f"Tech Stack: {', '.join(project.tech_stack)}")
        if project.constraints:
            summary_parts.append(f"Constraints: {', '.join(project.constraints)}")

        return "\n".join(summary_parts)

    def _get_summary(self, request: Dict) -> Dict:
        """Get project summary"""
        project = request.get('project')
        summary = self.get_context_summary(project)
        return {'status': 'success', 'summary': summary}

    def _find_similar(self, request: Dict) -> Dict:
        """Find similar projects or knowledge"""
        query = request.get('query')
        results = self.orchestrator.vector_db.search_similar(query, top_k=3)
        return {'status': 'success', 'similar_projects': results}

    def _identify_patterns(self, history: List[Dict]) -> Dict:
        """Analyze conversation history for patterns"""
        patterns = {
            'question_count': len([msg for msg in history if msg.get('type') == 'assistant']),
            'response_count': len([msg for msg in history if msg.get('type') == 'user']),
            'topics_covered': [],
            'engagement_level': 'high' if len(history) > 10 else 'medium' if len(history) > 5 else 'low'
        }

        return patterns
