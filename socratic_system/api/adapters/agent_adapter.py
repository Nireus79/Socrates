"""Agent adapter - converts REST/gRPC requests to agent format.

Serializes/deserializes requests and responses for external API access.
"""

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from socratic_system.orchestration import AgentOrchestrator

logger = logging.getLogger(__name__)


class AgentAdapter:
    """Adapter for converting external API requests to agent format.

    Handles:
    - Request validation and schema checking
    - Request routing to agents
    - Response serialization
    - Error handling
    """

    # Supported agents and their expected request fields
    AGENT_SCHEMAS = {
        "socratic_counselor": ["action", "project_id"],
        "project_manager": ["action", "name"],
        "code_generator": ["action", "project_id"],
        "code_validation": ["action", "project_id"],
        "quality_controller": ["action", "project_id"],
        "conflict_detector": ["action", "project_id"],
    }

    def __init__(self, orchestrator: "AgentOrchestrator"):
        """Initialize agent adapter.

        Args:
            orchestrator: AgentOrchestrator instance
        """
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)

    def get_schema(self, agent_name: str) -> Dict[str, Any]:
        """Get request schema for agent.

        Args:
            agent_name: Name of agent

        Returns:
            Schema dict with required fields
        """
        return {
            "agent_name": agent_name,
            "required_fields": self.AGENT_SCHEMAS.get(agent_name, []),
        }

    def validate_request(self, agent_name: str, request_data: Dict) -> bool:
        """Validate request against agent schema.

        Args:
            agent_name: Name of agent
            request_data: Request data dict

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        required_fields = self.AGENT_SCHEMAS.get(agent_name, [])

        for field in required_fields:
            if field not in request_data:
                raise ValueError(f"Missing required field: {field}")

        return True

    def serialize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize agent response for API.

        Args:
            response: Agent response dict

        Returns:
            Serialized response
        """
        return {
            "status": response.get("status", "success"),
            "data": response,
            "timestamp": self._get_timestamp(),
        }

    def serialize_error(self, error_code: str, message: str) -> Dict[str, Any]:
        """Serialize error response for API.

        Args:
            error_code: Error code
            message: Error message

        Returns:
            Error response dict
        """
        return {
            "status": "error",
            "error": error_code,
            "message": message,
            "timestamp": self._get_timestamp(),
        }

    async def handle_request(
        self, agent_name: str, request_data: Dict
    ) -> Dict[str, Any]:
        """Handle external API request.

        Args:
            agent_name: Name of agent
            request_data: Request data dict

        Returns:
            Serialized response

        Raises:
            ValueError: If validation fails
        """
        try:
            self.logger.info(
                f"[APIAdapter] Handling request for agent: {agent_name}"
            )

            # Validate request
            self.validate_request(agent_name, request_data)

            # Route to agent using agent bus
            response = self.orchestrator.agent_bus.send_request_sync(agent_name, request_data)

            # Serialize response
            return self.serialize_response(response)

        except ValueError as e:
            self.logger.warning(f"[APIAdapter] Validation error: {str(e)}")
            return self.serialize_error("invalid_request", str(e))

        except Exception as e:
            self.logger.error(f"[APIAdapter] Agent error: {str(e)}")
            return self.serialize_error("agent_error", str(e))

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()
