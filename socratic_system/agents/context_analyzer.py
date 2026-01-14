"""
Context analysis agent for Socrates AI
"""

import datetime
from typing import Any, Dict, List

from socratic_system.models import ProjectContext

from .base import Agent


class ContextAnalyzerAgent(Agent):
    """Analyzes project context and identifies patterns"""

    def __init__(self, orchestrator):
        super().__init__("ContextAnalyzer", orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process context analysis requests"""
        action = request.get("action")

        if action == "analyze_context":
            return self._analyze_context(request)
        elif action == "get_summary":
            return self._get_summary(request)
        elif action == "find_similar":
            return self._find_similar(request)
        elif action == "search_conversations":
            return self._search_conversations(request)
        elif action == "generate_summary":
            return self._generate_summary(request)
        elif action == "get_statistics":
            return self._get_statistics(request)

        return {"status": "error", "message": "Unknown action"}

    def _analyze_context(self, request: Dict) -> Dict:
        """Analyze project context and patterns"""
        project = request.get("project")
        conversation = request.get("conversation")

        # Use conversation from request if project not provided
        if project and project.conversation_history:
            history = project.conversation_history
        elif conversation:
            history = conversation
        else:
            return {"status": "error", "message": "project or conversation required"}

        # Analyze conversation patterns
        analysis = self._identify_patterns(history)

        # Get relevant knowledge if project is available
        relevant_knowledge = []
        if project and project.goals:
            relevant_knowledge = self.orchestrator.vector_db.search_similar(project.goals, top_k=5)

        return {"status": "success", "analysis": analysis, "relevant_knowledge": relevant_knowledge}

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
        project = request.get("project")
        summary = self.get_context_summary(project)
        return {"status": "success", "summary": summary}

    def _find_similar(self, request: Dict) -> Dict:
        """Find similar projects or knowledge"""
        query = request.get("query")
        results = self.orchestrator.vector_db.search_similar(query, top_k=3)
        return {"status": "success", "similar_projects": results}

    def _identify_patterns(self, history: List[Dict]) -> Dict:
        """Analyze conversation history for patterns"""
        patterns = {
            "question_count": len([msg for msg in history if msg.get("type") == "assistant"]),
            "response_count": len([msg for msg in history if msg.get("type") == "user"]),
            "topics_covered": [],
            "engagement_level": (
                "high" if len(history) > 10 else "medium" if len(history) > 5 else "low"
            ),
        }

        return patterns

    def _search_conversations(self, request: Dict) -> Dict:
        """Search conversation history for a query"""
        try:
            project = request.get("project")
            query = request.get("query", "").lower()

            if not project or not query:
                return {"status": "error", "message": "project and query required"}

            results = []
            for i, msg in enumerate(project.conversation_history):
                if query in msg.get("content", "").lower():
                    results.append(
                        {
                            "index": i,
                            "timestamp": msg.get("timestamp", "unknown"),
                            "role": msg.get("role", "unknown"),
                            "content": msg.get("content", ""),
                            "phase": msg.get("phase", "unknown"),
                        }
                    )

            self.log(f'Found {len(results)} conversation matches for "{query}"')
            return {"status": "success", "results": results, "count": len(results), "query": query}

        except Exception as e:
            self.log(f"Error searching conversations: {str(e)}", level="ERROR")
            return {"status": "error", "message": f"Error searching conversations: {str(e)}"}

    def _generate_summary(self, request: Dict) -> Dict:
        """Generate AI-powered conversation summary"""
        try:
            project = request.get("project")
            limit = request.get("limit", 10)

            if not project:
                return {"status": "error", "message": "project required"}

            # Get recent conversation
            recent = (
                project.conversation_history[-limit:] if limit else project.conversation_history
            )

            # Format conversation for summarization
            conv_text = ""
            for msg in reversed(recent):  # Reverse to get chronological order
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")
                conv_text += f"{role}: {content}\n\n"

            if not conv_text.strip():
                return {"status": "success", "summary": "No conversation history to summarize."}

            # Generate summary using Claude
            prompt = f"""Summarize the following conversation about the project '{project.name}'.
Focus on:
- Key decisions made
- Requirements identified
- Progress made
- Open questions

Conversation:
{conv_text}

Provide a concise, focused summary."""

            # Get user's auth method
            user_auth_method = "api_key"
            if self.current_user:
                user_obj = self.orchestrator.database.load_user(self.current_user)
                if user_obj and hasattr(user_obj, 'claude_auth_method'):
                    user_auth_method = user_obj.claude_auth_method or "api_key"
            summary = self.orchestrator.claude_client.generate_response(
                prompt, user_auth_method=user_auth_method, user_id=self.current_user
            )

            self.log(f"Generated summary for project {project.name}")
            return {"status": "success", "summary": summary}

        except Exception as e:
            self.log(f"Error generating summary: {str(e)}", level="ERROR")
            return {"status": "error", "message": f"Error generating summary: {str(e)}"}

    def _get_statistics(self, request: Dict) -> Dict:
        """Generate project statistics"""
        try:
            project = request.get("project")

            if not project:
                return {"status": "error", "message": "project required"}

            # Get note count
            notes = self.orchestrator.database.get_project_notes(project.project_id)
            notes_count = len(notes)

            # Calculate days active
            days_active = (datetime.datetime.now() - project.created_at).days

            # Count conversation types
            questions = len(
                [m for m in project.conversation_history if m.get("role") == "assistant"]
            )
            responses = len([m for m in project.conversation_history if m.get("role") == "user"])

            stats = {
                "project_name": project.name,
                "owner": project.owner,
                "current_phase": project.phase,
                "progress": getattr(project, "progress", 0),
                "status": getattr(project, "status", "active"),
                "created_at": (
                    project.created_at.strftime("%Y-%m-%d %H:%M")
                    if hasattr(project.created_at, "strftime")
                    else str(project.created_at)
                ),
                "updated_at": (
                    project.updated_at.strftime("%Y-%m-%d %H:%M")
                    if hasattr(project.updated_at, "strftime")
                    else str(project.updated_at)
                ),
                "days_active": days_active,
                "collaborators": len(project.collaborators),
                "requirements": len(project.requirements),
                "tech_stack": len(project.tech_stack),
                "constraints": len(project.constraints),
                "total_conversations": len(project.conversation_history),
                "questions_asked": questions,
                "responses_given": responses,
                "notes": notes_count,
            }

            self.log(f"Generated statistics for project {project.name}")
            return {"status": "success", "statistics": stats}

        except Exception as e:
            self.log(f"Error generating statistics: {str(e)}", level="ERROR")
            return {"status": "error", "message": f"Error generating statistics: {str(e)}"}
