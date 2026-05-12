"""
Integration of Socratic-Morality governance framework with Socrates.

Provides seamless integration between Socrates' agent orchestration
and Socratic-Morality's constitutional AI governance.
"""

import logging
from typing import Any, Dict, Optional

from socratic_morality.api.governance_api import GovernanceAPI
from socratic_morality.governance.constitutional_enforcer import (
    ConstitutionalEnforcer,
)
from socratic_morality.reasoning.semantic_precedent_engine import (
    SemanticPrecedentEngine,
)
from socratic_morality.reasoning.socratic_dialogue_engine import SocraticDialogueEngine

logger = logging.getLogger(__name__)


class MoralityGovernanceIntegration:
    """
    Integrates Socratic-Morality governance framework with Socrates.

    Provides:
    - Constitutional principle enforcement for agent actions
    - Unified governance API for all agent decisions
    - Interactive Socratic dialogue during ethical reasoning
    - Semantic precedent matching for decision consistency
    """

    def __init__(
        self,
        constitution_path: str | None = None,
        llm_provider: str = "anthropic",
        enable_dialogue: bool = True,
    ):
        """
        Initialize morality governance integration.

        Args:
            constitution_path: Path to constitution.yaml (optional, uses default)
            llm_provider: LLM provider for ethical reasoning (default: anthropic)
            enable_dialogue: Enable interactive Socratic dialogue (default: True)
        """
        self.llm_provider = llm_provider
        self.enable_dialogue = enable_dialogue

        # Initialize governance components
        self.governance_api = GovernanceAPI()
        self.constitutional_enforcer = ConstitutionalEnforcer(constitution_path=constitution_path)
        self.socratic_dialogue = (
            SocraticDialogueEngine(llm_provider=llm_provider) if enable_dialogue else None
        )
        self.semantic_precedent = SemanticPrecedentEngine()

        logger.info(
            f"Initialized Socratic-Morality integration "
            f"(provider={llm_provider}, dialogue={enable_dialogue})"
        )

    async def evaluate_agent_action(
        self,
        action: str,
        agent_name: str,
        context: dict[str, Any] | None = None,
        purpose: str | None = None,
        interactive: bool = False,
    ) -> dict[str, Any]:
        """
        Evaluate agent action against constitutional principles.

        This is the main governance decision point for all agent actions.

        Args:
            action: Description of the action to evaluate
            agent_name: Name of the agent proposing the action
            context: Additional context (data being accessed, users affected, etc.)
            purpose: Purpose of the action
            interactive: Enable interactive Socratic dialogue

        Returns:
            GovernanceDecision with:
            - allowed: Whether action is permitted
            - decision_type: ALLOWED, BLOCKED, ESCALATE, or CONDITIONAL
            - reasoning: Full reasoning trace
            - violations: Constitutional principle violations (if any)
            - recommendations: Suggested remediation
        """
        if context is None:
            context = {}

        # Add purpose to context if provided
        if purpose:
            context["purpose"] = purpose

        logger.info(f"Evaluating action: {action} " f"(agent={agent_name}, purpose={purpose})")

        # Use interactive dialogue if requested and available
        use_dialogue = interactive and self.enable_dialogue

        try:
            decision = await self.governance_api.evaluate_with_dialogue(
                action=action,
                context=context,
                actor=agent_name,
                interactive=use_dialogue,
            )

            # Log decision
            log_level = logging.WARNING if not decision.allowed else logging.INFO
            logger.log(
                log_level,
                f"Decision: {decision.decision_type} " f"(confidence={decision.confidence:.2f})",
            )

            return {
                "allowed": decision.allowed,
                "decision_type": decision.decision_type,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning_trace,
                "violations": [str(v) for v in decision.violations],
                "dialogue_transcript": getattr(decision, "dialogue_transcript", None),
            }

        except Exception as e:
            logger.error(f"Error during governance evaluation: {e}", exc_info=True)
            raise

    async def check_constitutional_principles(self, action: str) -> dict[str, Any]:
        """
        Quick check of action against constitutional principles.

        Faster than full governance evaluation - only checks principles,
        not ethical frameworks or precedents.

        Args:
            action: Action description to check

        Returns:
            ConstitutionalCheck with:
            - allowed: Passes constitutional check
            - violations: Specific principle violations
            - severity: Overall severity level
        """
        check = self.constitutional_enforcer.check_principles(action)

        return {
            "allowed": check.allowed,
            "violations": [v.principle for v in check.violations],
            "severity_levels": [v.severity for v in check.violations],
            "reasoning": check.reasoning,
            "confidence": check.confidence,
        }

    async def get_agent_capabilities(self, agent_name: str) -> dict[str, Any]:
        """
        Get authorized capabilities for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Authorized capabilities and resource limits
        """
        constitution = self.constitutional_enforcer.constitution

        if not constitution:
            logger.warning("Constitution not loaded, cannot check capabilities")
            return {}

        if not hasattr(constitution, "agent_capabilities"):
            logger.warning("Constitution does not define agent capabilities")
            return {}

        caps = constitution.agent_capabilities.get(agent_name, {})

        return {
            "agent": agent_name,
            "authorized": bool(caps),
            "permissions": caps.get("permissions", []),
            "resources": caps.get("resources", {}),
            "restrictions": caps.get("restrictions", []),
        }

    async def store_decision_precedent(self, action: str, decision: dict[str, Any]) -> None:
        """
        Store a governance decision as a precedent for future reference.

        Args:
            action: Action description
            decision: Governance decision result
        """
        try:
            await self.semantic_precedent.add_precedent_case(
                {
                    "action": action,
                    "conclusion": decision.get("decision_type"),
                    "reasoning": decision.get("reasoning"),
                    "confidence": decision.get("confidence"),
                }
            )
            logger.debug(f"Stored precedent for action: {action}")
        except Exception as e:
            logger.warning(f"Failed to store precedent: {e}")

    async def get_decision_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent governance decisions.

        Args:
            limit: Maximum number of recent decisions to return

        Returns:
            List of recent governance decisions
        """
        return await self.governance_api.get_evaluation_history(limit=limit)


# Global integration instance
_morality_integration: MoralityGovernanceIntegration | None = None


async def initialize_morality_governance(
    constitution_path: str | None = None,
    llm_provider: str = "anthropic",
    enable_dialogue: bool = True,
) -> MoralityGovernanceIntegration:
    """
    Initialize the global morality governance integration.

    Args:
        constitution_path: Path to constitution.yaml
        llm_provider: LLM provider for ethical reasoning
        enable_dialogue: Enable interactive Socratic dialogue

    Returns:
        Initialized MoralityGovernanceIntegration instance
    """
    global _morality_integration

    _morality_integration = MoralityGovernanceIntegration(
        constitution_path=constitution_path,
        llm_provider=llm_provider,
        enable_dialogue=enable_dialogue,
    )

    return _morality_integration


def get_morality_governance() -> MoralityGovernanceIntegration:
    """
    Get the global morality governance integration instance.

    Returns:
        MoralityGovernanceIntegration instance

    Raises:
        RuntimeError: If integration not yet initialized
    """
    if _morality_integration is None:
        raise RuntimeError(
            "Morality governance not initialized. " "Call initialize_morality_governance() first."
        )

    return _morality_integration
