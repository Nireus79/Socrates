"""
Knowledge Manager Agent for automatic knowledge enrichment

Manages project-specific knowledge enrichment through:
- Collecting knowledge suggestions from other agents
- Storing suggested knowledge for review
- Processing user-marked knowledge
- Enabling knowledge export/import
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

from socratic_system.agents.base import Agent
from socratic_system.events import EventType
from socratic_system.models.knowledge import KnowledgeEntry

if TYPE_CHECKING:
    from socratic_system.orchestration.orchestrator import AgentOrchestrator


class KnowledgeManagerAgent(Agent):
    """
    Manages knowledge enrichment for projects.

    Listens for knowledge suggestions, collects them, and provides
    mechanisms for storing and reviewing project-specific knowledge.
    """

    def __init__(self, name: str, orchestrator: "AgentOrchestrator"):
        """
        Initialize Knowledge Manager Agent.

        Args:
            name: Agent name
            orchestrator: Reference to the orchestrator
        """
        super().__init__(name, orchestrator)
        self.logger = logging.getLogger("socrates.agents.knowledge_manager")

        # Suggestion queue per project
        self.suggestions: Dict[str, List[Dict[str, Any]]] = {}

        # Register for knowledge suggestion events
        self.orchestrator.event_emitter.on(
            EventType.KNOWLEDGE_SUGGESTION, self._handle_knowledge_suggestion
        )

        self.logger.info("Knowledge Manager Agent initialized")

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process knowledge management requests.

        Args:
            request: Request dictionary with action and parameters

        Returns:
            Response dictionary with status and data
        """
        action = request.get("action")

        if action == "get_suggestions":
            return self._get_suggestions(request)
        elif action == "approve_suggestion":
            return self._approve_suggestion(request)
        elif action == "reject_suggestion":
            return self._reject_suggestion(request)
        elif action == "get_queue_status":
            return self._get_queue_status(request)
        elif action == "clear_suggestions":
            return self._clear_suggestions(request)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _handle_knowledge_suggestion(self, data: Dict[str, Any]) -> None:
        """
        Handle knowledge suggestion events from other agents.

        Args:
            data: Event data containing suggestion details
        """
        # Extract project context - in a real implementation, this would come
        # from the current context or be part of the event
        # For now, we store suggestions with context

        project_id = data.get("project_id", "default")
        suggestion = {
            "id": self._generate_suggestion_id(),
            "content": data.get("content"),
            "category": data.get("category"),
            "topic": data.get("topic"),
            "difficulty": data.get("difficulty", "intermediate"),
            "reason": data.get("reason", "insufficient_context"),
            "agent": data.get("agent", "unknown"),
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "status": "pending",
        }

        if project_id not in self.suggestions:
            self.suggestions[project_id] = []

        self.suggestions[project_id].append(suggestion)

        self.logger.debug(
            f"Knowledge suggestion collected from {suggestion['agent']}: "
            f"{suggestion['content'][:50]}..."
        )

        # Emit event for UI/logging
        self.emit_event(
            EventType.LOG_INFO,
            {"message": f"Knowledge suggestion from {suggestion['agent']}: {suggestion['topic']}"},
        )

    def _get_suggestions(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get pending suggestions for a project"""
        project_id = request.get("project_id", "default")
        status_filter = request.get("status", "pending")

        if project_id not in self.suggestions:
            return {"status": "success", "suggestions": [], "count": 0}

        suggestions = self.suggestions[project_id]

        if status_filter != "all":
            suggestions = [s for s in suggestions if s["status"] == status_filter]

        return {"status": "success", "suggestions": suggestions, "count": len(suggestions)}

    def _approve_suggestion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Approve and add suggestion to project knowledge"""
        project_id = request.get("project_id", "default")
        suggestion_id = request.get("suggestion_id")

        if project_id not in self.suggestions:
            return {"status": "error", "message": "Project not found"}

        # Find suggestion
        suggestion = None
        for s in self.suggestions[project_id]:
            if s["id"] == suggestion_id:
                suggestion = s
                break

        if not suggestion:
            return {"status": "error", "message": f"Suggestion not found: {suggestion_id}"}

        try:
            # Create knowledge entry
            entry = KnowledgeEntry(
                id=f"suggested_{suggestion_id}",
                content=suggestion["content"],
                category=suggestion["category"],
                metadata={
                    "topic": suggestion["topic"],
                    "difficulty": suggestion["difficulty"],
                    "source": f"agent_suggestion_from_{suggestion['agent']}",
                    "reason": suggestion["reason"],
                    "approved_at": datetime.now().isoformat(),
                },
            )

            # Add to project knowledge
            success = self.orchestrator.vector_db.add_project_knowledge(entry, project_id)

            if success:
                suggestion["status"] = "approved"
                self.logger.info(f"Suggestion approved and added: {suggestion_id}")
                return {"status": "success", "message": f'Knowledge added: {suggestion["topic"]}'}
            else:
                return {"status": "error", "message": "Failed to add knowledge"}

        except Exception as e:
            self.logger.error(f"Failed to approve suggestion: {str(e)}")
            return {"status": "error", "message": f"Approval failed: {str(e)}"}

    def _reject_suggestion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Reject a suggestion"""
        project_id = request.get("project_id", "default")
        suggestion_id = request.get("suggestion_id")

        if project_id not in self.suggestions:
            return {"status": "error", "message": "Project not found"}

        # Find and reject suggestion
        for s in self.suggestions[project_id]:
            if s["id"] == suggestion_id:
                s["status"] = "rejected"
                self.logger.info(f"Suggestion rejected: {suggestion_id}")
                return {"status": "success", "message": "Suggestion rejected"}

        return {"status": "error", "message": f"Suggestion not found: {suggestion_id}"}

    def _get_queue_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of knowledge suggestion queue"""
        project_id = request.get("project_id", "default")

        if project_id not in self.suggestions:
            return {"status": "success", "pending": 0, "approved": 0, "rejected": 0, "total": 0}

        suggestions = self.suggestions[project_id]

        return {
            "status": "success",
            "pending": len([s for s in suggestions if s["status"] == "pending"]),
            "approved": len([s for s in suggestions if s["status"] == "approved"]),
            "rejected": len([s for s in suggestions if s["status"] == "rejected"]),
            "total": len(suggestions),
        }

    def _clear_suggestions(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Clear processed suggestions for a project"""
        project_id = request.get("project_id", "default")
        keep_pending = request.get("keep_pending", True)

        if project_id not in self.suggestions:
            return {"status": "success", "cleared": 0}

        original_count = len(self.suggestions[project_id])

        if keep_pending:
            # Keep only pending suggestions
            self.suggestions[project_id] = [
                s for s in self.suggestions[project_id] if s["status"] == "pending"
            ]
        else:
            # Clear all
            self.suggestions[project_id] = []

        cleared_count = original_count - len(self.suggestions[project_id])

        self.logger.info(f"Cleared {cleared_count} processed suggestions")

        return {"status": "success", "cleared": cleared_count}

    def _generate_suggestion_id(self) -> str:
        """Generate unique suggestion ID"""
        import hashlib
        import time

        timestamp = str(time.time())
        # Using MD5 for non-security purposes (just timestamp hashing)
        # Safe for Python 3.8+ compatibility
        try:
            return hashlib.md5(timestamp.encode(), usedforsecurity=False).hexdigest()[:12]
        except TypeError:
            # Python 3.8 doesn't support usedforsecurity parameter
            return hashlib.md5(timestamp.encode()).hexdigest()[:12]  # nosec
