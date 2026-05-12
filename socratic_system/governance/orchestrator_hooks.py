"""
Hooks to integrate Socratic-Morality governance with agent orchestrator.

Provides middleware-style governance checks for all agent actions.
"""

import logging
from typing import Any, Dict, Optional

from socratic_system.governance.morality_integration import (
    get_morality_governance,
)

logger = logging.getLogger(__name__)


class GovernanceAwareOrchestrator:
    """
    Wrapper to add governance checks to agent orchestration.

    Ensures all agent actions are evaluated against constitutional
    principles before execution.
    """

    def __init__(self, orchestrator: Any):
        """
        Initialize governance-aware orchestrator wrapper.

        Args:
            orchestrator: The underlying agent orchestrator
        """
        self.orchestrator = orchestrator
        self.governance = get_morality_governance()

    async def process_request_with_governance(
        self,
        agent_name: str,
        request: dict[str, Any],
        interactive_dialogue: bool = False,
    ) -> dict[str, Any]:
        """
        Process agent request with governance evaluation.

        Args:
            agent_name: Name of the agent
            request: Agent request dict
            interactive_dialogue: Enable interactive Socratic dialogue

        Returns:
            Agent response or governance block

        Raises:
            PermissionError: If action violates constitutional principles
        """
        # Extract action description from request
        action = self._extract_action_description(agent_name, request)

        logger.info(f"Processing {agent_name} request with governance check: {action}")

        # Check constitutional compliance
        decision = await self.governance.evaluate_agent_action(
            action=action,
            agent_name=agent_name,
            context=request,
            interactive=interactive_dialogue,
        )

        # Block if not allowed
        if not decision["allowed"]:
            error_msg = (
                f"Action blocked by governance: {action}. " f"Violations: {decision['violations']}"
            )
            logger.warning(error_msg)

            raise PermissionError(
                {
                    "action": action,
                    "decision_type": decision["decision_type"],
                    "violations": decision["violations"],
                    "reasoning": decision["reasoning"],
                }
            )

        # Log decision
        logger.info(
            f"Action approved ({decision['decision_type']}, "
            f"confidence={decision['confidence']:.2f})"
        )

        # Store precedent
        await self.governance.store_decision_precedent(action, decision)

        # Process with orchestrator
        try:
            response = await self.orchestrator.process_request(agent_name, request)
            return response

        except Exception as e:
            logger.error(f"Error during orchestration: {e}", exc_info=True)
            raise

    async def check_capability(self, agent_name: str, action: str) -> bool:
        """
        Check if agent has capability to perform action.

        Args:
            agent_name: Name of the agent
            action: Action description

        Returns:
            True if action is allowed, False otherwise
        """
        try:
            decision = await self.governance.evaluate_agent_action(
                action=action,
                agent_name=agent_name,
            )
            return decision["allowed"]

        except Exception as e:
            logger.error(
                f"Error checking capability: {e}",
                exc_info=True,
            )
            return False

    @staticmethod
    def _extract_action_description(agent_name: str, request: dict[str, Any]) -> str:
        """
        Extract human-readable action description from request.

        Args:
            agent_name: Agent name
            request: Request dict

        Returns:
            Action description string
        """
        if "action" in request:
            return request["action"]

        if "description" in request:
            return request["description"]

        # Fallback: construct from common request fields
        parts = [agent_name]

        if "task" in request:
            parts.append(f"task: {request['task']}")

        if "target" in request:
            parts.append(f"target: {request['target']}")

        if "method" in request:
            parts.append(f"method: {request['method']}")

        return " - ".join(parts)


def wrap_orchestrator_with_governance(
    orchestrator: Any,
) -> GovernanceAwareOrchestrator:
    """
    Wrap an orchestrator with governance checks.

    Args:
        orchestrator: The agent orchestrator to wrap

    Returns:
        Governance-aware orchestrator wrapper
    """
    return GovernanceAwareOrchestrator(orchestrator)


async def evaluate_action_governance(
    action: str,
    agent: str,
    context: dict[str, Any] | None = None,
    purpose: str | None = None,
) -> dict[str, Any]:
    """
    Evaluate an action for governance compliance.

    Convenience function for checking if an action is allowed.

    Args:
        action: Action description
        agent: Agent name
        context: Optional context dict
        purpose: Optional purpose statement

    Returns:
        Governance decision
    """
    governance = get_morality_governance()

    return await governance.evaluate_agent_action(
        action=action,
        agent_name=agent,
        context=context,
        purpose=purpose,
    )
