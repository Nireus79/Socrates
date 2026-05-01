"""Learning service - encapsulates learning system and user tracking."""

from typing import TYPE_CHECKING, Dict, Any, Optional

from .base import Service

if TYPE_CHECKING:
    from socratic_system.orchestration import AgentOrchestrator


class LearningService(Service):
    """Service for tracking user learning and effectiveness metrics."""

    def __init__(self, config, orchestrator: "AgentOrchestrator"):
        """Initialize learning service.

        Args:
            config: Socrates configuration
            orchestrator: Agent orchestrator
        """
        super().__init__(config)
        self.orchestrator = orchestrator

    def track_question_effectiveness(
        self,
        user_id: str,
        question_id: str,
        role: str,
        answer_length: int,
        specs_extracted: int,
    ) -> None:
        """Track effectiveness of a question.

        Args:
            user_id: User identifier
            question_id: Question template ID
            role: User role
            answer_length: Length of user's answer
            specs_extracted: Number of specs extracted from answer
        """
        self.logger.debug(f"Tracking question effectiveness for user {user_id}")

        self.orchestrator.process_request(
            "learning",
            {
                "action": "track_question_effectiveness",
                "user_id": user_id,
                "question_template_id": question_id,
                "role": role,
                "answer_length": answer_length,
                "specs_extracted": specs_extracted,
            },
        )

    def get_learning_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get learning metrics for user.

        Args:
            user_id: User identifier

        Returns:
            Learning metrics dict
        """
        self.logger.debug(f"Getting learning metrics for user {user_id}")

        result = self.orchestrator.process_request(
            "learning",
            {
                "action": "get_metrics",
                "user_id": user_id,
            },
        )

        return result.get("metrics", {})
