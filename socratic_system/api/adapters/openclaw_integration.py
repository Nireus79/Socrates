"""OpenClaw integration for Socrates agents.

Provides OpenClaw-compatible action handlers and event listeners for
incorporating Socrates capabilities into OpenClaw workflows.

Example:
    ```python
    from socratic_system.api.adapters.openclaw_integration import (
        SocratesClawAdapter, ClawActionHandler
    )

    # Create adapter
    adapter = SocratesClawAdapter(api_url="http://localhost:8000")

    # Register as action handler
    claw_engine.register_handler("socrates_code", adapter.code_handler)
    claw_engine.register_handler("socrates_validate", adapter.validation_handler)

    # Use in OpenClaw rules
    result = claw_engine.execute_action(
        action="socrates_code",
        params={"project_id": "proj_123", "spec": "Generate login form"}
    )
    ```
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from collections.abc import Callable

from socratic_system.clients.socrates_agent_client import (
    SocratesAgentClient,
    SocratesAgentClientSync,
)

logger = logging.getLogger(__name__)


class ClawAction(ABC):
    """Base class for OpenClaw actions backed by Socrates agents."""

    def __init__(
        self,
        agent_name: str,
        action: str = "process",
        api_url: str = "http://localhost:8000",
        auth_token: str | None = None,
    ):
        """Initialize action.

        Args:
            agent_name: Name of Socrates agent to invoke
            action: Action to perform
            api_url: Base URL of Socrates API
            auth_token: Optional authentication token
        """
        self.agent_name = agent_name
        self.action = action
        self.client = SocratesAgentClientSync(api_url, auth_token)

    @abstractmethod
    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the action.

        Args:
            params: Action parameters

        Returns:
            Action result
        """
        pass

    def _invoke_agent(self, **kwargs) -> dict[str, Any]:
        """Invoke the Socrates agent.

        Args:
            **kwargs: Parameters to pass to agent

        Returns:
            Agent response
        """
        return self.client.invoke_agent(
            self.agent_name,
            action=self.action,
            **kwargs,
        )


class CodeGenerationAction(ClawAction):
    """OpenClaw action for code generation via Socrates."""

    def __init__(self, api_url: str = "http://localhost:8000", auth_token: str | None = None):
        super().__init__("code_generator", "process", api_url, auth_token)

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Generate code.

        Args:
            params: Must include:
                - spec: Code specification/description
                - project_id: Optional project context
                - language: Optional target language

        Returns:
            Code generation result with 'code' key
        """
        spec = params.get("spec", "")
        project_id = params.get("project_id")
        language = params.get("language", "python")

        logger.info(f"[ClawAction] Generating code: {spec[:100]}...")

        result = self._invoke_agent(
            project_id=project_id,
            spec=spec,
            language=language,
            query=spec,
        )

        return {
            "success": "error" not in str(result).lower(),
            "code": result.get("data") or result.get("result") or result,
            "raw_response": result,
        }


class ValidationAction(ClawAction):
    """OpenClaw action for code validation via Socrates."""

    def __init__(self, api_url: str = "http://localhost:8000", auth_token: str | None = None):
        super().__init__("code_validation", "process", api_url, auth_token)

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Validate code.

        Args:
            params: Must include:
                - project_id: Project to validate
                - code: Optional code snippet to validate

        Returns:
            Validation result with 'passed' and 'total' keys
        """
        project_id = params.get("project_id")
        code = params.get("code")

        logger.info(f"[ClawAction] Validating project: {project_id}")

        result = self._invoke_agent(
            project_id=project_id,
            code=code,
            query=f"Validate project {project_id}",
        )

        return {
            "success": "error" not in str(result).lower(),
            "passed": result.get("passed", 0),
            "total": result.get("total", 0),
            "raw_response": result,
        }


class QualityAction(ClawAction):
    """OpenClaw action for quality assessment via Socrates."""

    def __init__(self, api_url: str = "http://localhost:8000", auth_token: str | None = None):
        super().__init__("quality_controller", "process", api_url, auth_token)

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Assess quality.

        Args:
            params: Must include:
                - project_id: Project to assess

        Returns:
            Quality assessment with 'maturity', 'score' keys
        """
        project_id = params.get("project_id")

        logger.info(f"[ClawAction] Assessing quality: {project_id}")

        result = self._invoke_agent(
            project_id=project_id,
            query=f"Assess quality of project {project_id}",
        )

        return {
            "success": "error" not in str(result).lower(),
            "maturity": result.get("maturity"),
            "score": result.get("overall_maturity"),
            "raw_response": result,
        }


class ConflictDetectionAction(ClawAction):
    """OpenClaw action for conflict detection via Socrates."""

    def __init__(self, api_url: str = "http://localhost:8000", auth_token: str | None = None):
        super().__init__("conflict_detector", "process", api_url, auth_token)

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Detect conflicts.

        Args:
            params: Must include:
                - project_id: Project to analyze

        Returns:
            Conflict report with 'conflicts', 'count' keys
        """
        project_id = params.get("project_id")

        logger.info(f"[ClawAction] Detecting conflicts: {project_id}")

        result = self._invoke_agent(
            project_id=project_id,
            query=f"Detect conflicts in project {project_id}",
        )

        return {
            "success": "error" not in str(result).lower(),
            "conflicts": result.get("conflicts", []),
            "count": len(result.get("conflicts", [])),
            "raw_response": result,
        }


class SocratesClawAdapter:
    """Adapter for integrating Socrates into OpenClaw.

    Provides action handlers for common Socrates capabilities that can be
    registered with an OpenClaw engine.
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        auth_token: str | None = None,
    ):
        """Initialize adapter.

        Args:
            api_url: Base URL of Socrates API
            auth_token: Optional authentication token
        """
        self.api_url = api_url
        self.auth_token = auth_token

        # Initialize action handlers
        self.code_handler = CodeGenerationAction(api_url, auth_token)
        self.validation_handler = ValidationAction(api_url, auth_token)
        self.quality_handler = QualityAction(api_url, auth_token)
        self.conflict_handler = ConflictDetectionAction(api_url, auth_token)

    def get_actions(self) -> dict[str, ClawAction]:
        """Get all registered actions.

        Returns:
            Dictionary mapping action names to handlers
        """
        return {
            "socrates_code": self.code_handler,
            "socrates_validate": self.validation_handler,
            "socrates_quality": self.quality_handler,
            "socrates_conflict": self.conflict_handler,
        }

    def register_with_engine(self, engine: Any) -> None:
        """Register all actions with an OpenClaw engine.

        Args:
            engine: OpenClaw engine instance with register_handler method
        """
        for action_name, handler in self.get_actions().items():
            logger.info(f"[Adapter] Registering action: {action_name}")
            engine.register_handler(action_name, handler.execute)

    def execute_action(
        self,
        action_name: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an action directly.

        Args:
            action_name: Name of action to execute
            params: Action parameters

        Returns:
            Action result

        Raises:
            ValueError: If action not found
        """
        actions = self.get_actions()
        if action_name not in actions:
            raise ValueError(f"Unknown action: {action_name}")

        return actions[action_name].execute(params)

    async def execute_action_async(
        self,
        action_name: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an action asynchronously.

        Args:
            action_name: Name of action to execute
            params: Action parameters

        Returns:
            Action result
        """
        # For async, we need to use the async client
        actions = self.get_actions()
        if action_name not in actions:
            raise ValueError(f"Unknown action: {action_name}")

        action = actions[action_name]
        agent_name = action.agent_name

        client = SocratesAgentClient(self.api_url, self.auth_token)
        try:
            result = await client.invoke_agent_sync(
                agent_name,
                action=action.action,
                **params,
            )
            return {
                "success": "error" not in str(result).lower(),
                "result": result,
            }
        finally:
            await client.close()


class ClawEventListener:
    """Listener for OpenClaw events backed by Socrates agents.

    Listens for OpenClaw events and triggers Socrates agent actions.
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        auth_token: str | None = None,
    ):
        """Initialize listener.

        Args:
            api_url: Base URL of Socrates API
            auth_token: Optional authentication token
        """
        self.adapter = SocratesClawAdapter(api_url, auth_token)
        self.handlers: dict[str, Callable] = {}

    def on(self, event_name: str, action_name: str) -> Callable:
        """Register handler for an OpenClaw event.

        Args:
            event_name: OpenClaw event name
            action_name: Socrates action to trigger

        Returns:
            Handler function
        """

        def handler(params: dict[str, Any]) -> dict[str, Any]:
            logger.info(
                f"[EventListener] Event '{event_name}' triggered, executing '{action_name}'"
            )
            return self.adapter.execute_action(action_name, params)

        self.handlers[event_name] = handler
        return handler

    def register_with_engine(self, engine: Any) -> None:
        """Register all event listeners with an OpenClaw engine.

        Args:
            engine: OpenClaw engine instance with add_listener or subscribe method
        """
        for event_name, handler in self.handlers.items():
            logger.info(f"[EventListener] Registering listener for event: {event_name}")
            if hasattr(engine, "add_listener"):
                engine.add_listener(event_name, handler)
            elif hasattr(engine, "subscribe"):
                engine.subscribe(event_name, handler)
            else:
                logger.warning(f"Engine does not support event registration for {event_name}")
