"""Answer Processing Workflow for Monolithic Socrates Pattern.

This module provides the answer processing orchestration following the monolithic
Socrates pattern: extract specs → filter by confidence → merge → detect conflicts
→ update maturity → auto-generate follow-up.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class AnswerProcessingWorkflow:
    """Implements the complete answer processing workflow for monolithic pattern."""

    def __init__(self, logger):
        """Initialize with logger."""
        self.logger = logger

    def process_answer(
        self,
        project: Any,
        user_response: str,
        current_user: str,
        counselor: Any,
        detector: Any,
    ) -> Dict[str, Any]:
        """
        Process user answer following monolithic pattern.

        Workflow:
        1. Extract specs from response with confidence scores
        2. Filter by confidence >= 0.7 (high quality only)
        3. Merge into project fields
        4. Detect conflicts
        5. Update maturity
        6. Auto-generate follow-up question
        7. Store follow-up in conversation history

        Args:
            project: ProjectContext object
            user_response: User's answer text
            current_user: User ID
            counselor: SocraticCounselor agent instance
            detector: ConflictDetector agent instance

        Returns:
            Dictionary with specs, conflicts, maturity, next_question
        """
        try:
            # Step 1: Extract specs
            extract_result = counselor.process(
                {
                    "action": "extract_insights_only",
                    "response": user_response,
                    "project": project,
                }
            )

            extracted_specs = extract_result.get("data", {}).get("insights", {})
            self.logger.info(f"Extracted specs: {list(extracted_specs.keys())}")

            # Step 2: Filter by confidence >= 0.7
            high_confidence = self._filter_specs(extracted_specs, 0.7)
            self.logger.info(f"High-confidence specs: {list(high_confidence.keys())}")

            # Step 3: Merge into project
            self._merge_specs(project, high_confidence)

            # Step 4: Detect conflicts
            conflicts = (
                detector.process({"new_specs": high_confidence, "project": project})
                .get("data", {})
                .get("conflicts", [])
            )

            # Step 5: Update maturity
            maturity = getattr(project, "maturity_scores", {})

            # Step 6: Auto-generate follow-up
            phase = getattr(project, "phase", "discovery")
            recently_asked = self._extract_recently_asked(project, phase)
            last_q = self._get_last_question(project)
            if last_q:
                recently_asked.append(last_q)

            followup_result = counselor.process(
                {
                    "action": "generate_question",
                    "project": project,
                    "user_id": current_user,
                    "recently_asked": recently_asked,
                    "force_refresh": True,
                }
            )

            followup_question = followup_result.get("data", {}).get("question", "")

            # Step 7: Store in conversation history
            if followup_question:
                if not hasattr(project, "conversation_history"):
                    project.conversation_history = []

                response_turn = (
                    len([m for m in project.conversation_history if m.get("type") == "assistant"])
                    + 1
                )

                project.conversation_history.append(
                    {
                        "type": "assistant",
                        "content": followup_question,
                        "phase": phase,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "response_turn": response_turn,
                    }
                )

            return {
                "status": "success",
                "specs": high_confidence,
                "conflicts": conflicts,
                "maturity": maturity,
                "next_question": followup_question,
            }

        except Exception as e:
            self.logger.error(f"Answer processing failed: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _filter_specs(
        self, specs: Dict[str, List[Any]], min_confidence: float = 0.7
    ) -> Dict[str, List[Any]]:
        """Filter specs by confidence >= min_confidence."""
        filtered = {}
        for key, spec_list in specs.items():
            if isinstance(spec_list, list):
                filtered[key] = [
                    s
                    for s in spec_list
                    if (isinstance(s, dict) and s.get("confidence_score", 1.0) >= min_confidence)
                    or isinstance(s, str)
                ]
            else:
                filtered[key] = spec_list
        return filtered

    def _merge_specs(self, project: Any, specs: Dict[str, List[Any]]) -> None:
        """Merge high-confidence specs into project fields."""
        if not hasattr(project, "goals"):
            project.goals = []
        if not hasattr(project, "requirements"):
            project.requirements = []
        if not hasattr(project, "tech_stack"):
            project.tech_stack = []
        if not hasattr(project, "constraints"):
            project.constraints = []

        for goal in specs.get("goals", []):
            text = goal if isinstance(goal, str) else goal.get("text", "")
            if text and text not in project.goals:
                project.goals.append(text)

        for req in specs.get("requirements", []):
            text = req if isinstance(req, str) else req.get("text", "")
            if text and text not in project.requirements:
                project.requirements.append(text)

        for tech in specs.get("tech_stack", []):
            text = tech if isinstance(tech, str) else tech.get("text", "")
            if text and text not in project.tech_stack:
                project.tech_stack.append(text)

        for constraint in specs.get("constraints", []):
            text = constraint if isinstance(constraint, str) else constraint.get("text", "")
            if text and text not in project.constraints:
                project.constraints.append(text)

    def _extract_recently_asked(self, project: Any, phase: str) -> List[str]:
        """Extract previously asked questions (MONOLITHIC PATTERN)."""
        recently_asked = []
        for msg in getattr(project, "conversation_history", []):
            if msg.get("type") == "assistant" and msg.get("phase") == phase:
                recently_asked.append(msg.get("content", ""))
        return [q for q in recently_asked if q]

    def _get_last_question(self, project: Any) -> str:
        """Get the most recent question from conversation history."""
        for msg in reversed(getattr(project, "conversation_history", [])):
            if msg.get("type") == "assistant":
                return msg.get("content", "")
        return ""
