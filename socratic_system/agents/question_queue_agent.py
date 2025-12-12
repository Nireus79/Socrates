"""
Question Queue Agent - Manages question assignment and tracking for team projects.

Capabilities:
- add_question: Add question to queue with role-based assignment
- get_user_questions: Get pending questions for a specific user
- answer_question: Mark question as answered
- skip_question: Skip a question
- get_queue_status: Get overall queue status
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from socratic_system.agents.base import Agent


class QuestionQueueAgent(Agent):
    """Manages question queue for team projects with role-based assignment."""

    def __init__(self, orchestrator):
        """Initialize question queue agent."""
        super().__init__("QuestionQueue", orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process question queue requests."""
        action = request.get("action")

        handlers = {
            "add_question": self._add_question,
            "get_user_questions": self._get_user_questions,
            "answer_question": self._answer_question,
            "skip_question": self._skip_question,
            "get_queue_status": self._get_queue_status,
        }

        handler = handlers.get(action)
        if handler:
            try:
                return handler(request)
            except Exception as e:
                self.logger.error(f"Error in {action}: {str(e)}", exc_info=True)
                return {"status": "error", "message": f"Failed to {action}: {str(e)}"}

        return {"status": "error", "message": f"Unknown action: {action}"}

    def _add_question(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Add question to queue with role-based assignment."""
        project_id = request.get("project_id")
        question = request.get("question")
        phase = request.get("phase")
        project = request.get("project")

        if not project:
            project = self.orchestrator.database.load_project(project_id)

        if not project:
            return {"status": "error", "message": "Project not found"}

        # Determine which roles should answer this question
        assigned_roles = self._determine_roles(question, project)

        # Map roles to actual users
        assigned_users = []
        for member in project.team_members or []:
            if member.role in assigned_roles:
                assigned_users.append(member.username)

        # Create question entry
        question_entry = {
            "id": f"q_{uuid.uuid4().hex[:8]}",
            "question": question,
            "phase": phase,
            "assigned_to_roles": assigned_roles,
            "assigned_to_users": assigned_users,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "answered_by": None,
            "answer": None,
        }

        # Add to queue
        if project.pending_questions is None:
            project.pending_questions = []
        project.pending_questions.append(question_entry)

        # Save project
        self.orchestrator.database.save_project(project)

        self.logger.info(
            f"Added question to queue: {question_entry['id']} "
            f"assigned to roles {assigned_roles}"
        )

        return {
            "status": "success",
            "question_id": question_entry["id"],
            "assigned_to": assigned_users,
            "message": f"Question assigned to {len(assigned_users)} team member(s)",
        }

    def _determine_roles(self, question: str, project) -> List[str]:
        """Use Claude to determine which roles should answer question."""

        available_roles = list({m.role for m in project.team_members or []})

        if not available_roles:
            return ["lead"]

        # For simple heuristic, use question keywords to determine roles
        # In production, this could be more sophisticated
        question_lower = question.lower()
        role_keywords = {
            "lead": ["strategy", "vision", "goal", "decision", "plan", "overall"],
            "creator": ["build", "implement", "create", "develop", "code", "develop"],
            "specialist": ["technical", "expert", "quality", "best practice", "standard"],
            "analyst": ["research", "analyze", "requirement", "validation", "data"],
            "coordinator": ["timeline", "schedule", "depend", "milestone", "task"],
        }

        suggested_roles = []
        for role, keywords in role_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                if role in available_roles:
                    suggested_roles.append(role)

        # Fallback to all available roles if no keyword matches
        if not suggested_roles:
            suggested_roles = available_roles

        return suggested_roles

    def _get_user_questions(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get pending questions for a specific user."""
        project_id = request.get("project_id")
        username = request.get("username")
        project = request.get("project")

        if not project:
            project = self.orchestrator.database.load_project(project_id)

        if not project:
            return {"status": "error", "message": "Project not found"}

        # Filter questions assigned to this user
        user_questions = [
            q
            for q in (project.pending_questions or [])
            if username in q["assigned_to_users"] and q["status"] == "pending"
        ]

        return {"status": "success", "questions": user_questions, "total": len(user_questions)}

    def _answer_question(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Mark question as answered."""
        project_id = request.get("project_id")
        question_id = request.get("question_id")
        username = request.get("username")
        answer = request.get("answer")
        project = request.get("project")

        if not project:
            project = self.orchestrator.database.load_project(project_id)

        if not project:
            return {"status": "error", "message": "Project not found"}

        # Find and update question
        found = False
        for q in project.pending_questions or []:
            if q["id"] == question_id:
                q["status"] = "answered"
                q["answered_by"] = username
                q["answer"] = answer
                q["answered_at"] = datetime.now().isoformat()
                found = True
                break

        if not found:
            return {"status": "error", "message": "Question not found"}

        # Save project
        self.orchestrator.database.save_project(project)

        self.logger.info(f"Question {question_id} answered by {username}")

        return {"status": "success", "message": "Question marked as answered"}

    def _skip_question(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Skip a question."""
        project_id = request.get("project_id")
        question_id = request.get("question_id")
        project = request.get("project")

        if not project:
            project = self.orchestrator.database.load_project(project_id)

        if not project:
            return {"status": "error", "message": "Project not found"}

        # Find and update question
        found = False
        for q in project.pending_questions or []:
            if q["id"] == question_id:
                q["status"] = "skipped"
                q["skipped_at"] = datetime.now().isoformat()
                found = True
                break

        if not found:
            return {"status": "error", "message": "Question not found"}

        # Save project
        self.orchestrator.database.save_project(project)

        self.logger.info(f"Question {question_id} skipped")

        return {"status": "success", "message": "Question skipped"}

    def _get_queue_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get overall queue status."""
        project_id = request.get("project_id")
        project = request.get("project")

        if not project:
            project = self.orchestrator.database.load_project(project_id)

        if not project:
            return {"status": "error", "message": "Project not found"}

        questions = project.pending_questions or []
        pending = [q for q in questions if q["status"] == "pending"]
        answered = [q for q in questions if q["status"] == "answered"]
        skipped = [q for q in questions if q["status"] == "skipped"]

        return {
            "status": "success",
            "total_questions": len(questions),
            "pending": len(pending),
            "answered": len(answered),
            "skipped": len(skipped),
            "completion_rate": (len(answered) / len(questions) * 100) if questions else 0,
        }
