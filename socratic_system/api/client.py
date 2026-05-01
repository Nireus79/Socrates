"""SocratesAgentClient - Library client for accessing Socrates agents.

Enables external applications to use Socrates agents without Socrates internals.
No dependency on orchestrator, services, or agent implementations.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


class SocratesAgentClient:
    """Library client for accessing Socrates agents.

    Provides async interface to agent APIs without requiring Socrates internals.
    Can be used as a library in external applications.

    Example:
        ```python
        client = SocratesAgentClient("http://localhost:8000")

        # Create project
        project = await client.project_manager({
            "action": "create",
            "name": "My Project",
            "user_id": "user_123"
        })

        # Ask question
        question = await client.socratic_counselor({
            "action": "get_question",
            "project_id": project["id"],
            "user_id": "user_123"
        })
        ```
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize Socrates agent client.

        Args:
            api_url: API base URL
            auth_token: Optional authentication token
            timeout: Request timeout in seconds
        """
        if not httpx:
            raise ImportError(
                "httpx is required for SocratesAgentClient. "
                "Install with: pip install httpx"
            )

        self.api_url = api_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

        # Initialize async client
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            headers=headers,
            timeout=timeout,
        )

    async def project_manager(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call ProjectManager agent.

        Args:
            request: Request dict with action and parameters

        Returns:
            Agent response
        """
        return await self._call_agent("project_manager", request)

    async def socratic_counselor(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call SocraticCounselor agent.

        Args:
            request: Request dict with action and parameters

        Returns:
            Agent response
        """
        return await self._call_agent("socratic_counselor", request)

    async def code_generator(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call CodeGenerator agent.

        Args:
            request: Request dict with action and parameters

        Returns:
            Agent response
        """
        return await self._call_agent("code_generator", request)

    async def code_validation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call CodeValidation agent.

        Args:
            request: Request dict with action and parameters

        Returns:
            Agent response
        """
        return await self._call_agent("code_validation", request)

    async def quality_controller(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call QualityController agent.

        Args:
            request: Request dict with action and parameters

        Returns:
            Agent response
        """
        return await self._call_agent("quality_controller", request)

    async def conflict_detector(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call ConflictDetector agent.

        Args:
            request: Request dict with action and parameters

        Returns:
            Agent response
        """
        return await self._call_agent("conflict_detector", request)

    async def _call_agent(
        self, agent_name: str, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call agent via REST API.

        Args:
            agent_name: Name of agent
            request: Request data

        Returns:
            Agent response

        Raises:
            httpx.HTTPError: If API call fails
        """
        self.logger.debug(f"Calling agent: {agent_name}")

        response = await self.client.post(
            f"/agents/{agent_name}/process",
            json=request,
        )

        response.raise_for_status()
        return response.json()

    async def get_available_agents(self) -> Dict[str, Any]:
        """Get list of available agents.

        Returns:
            Dict with agents list
        """
        response = await self.client.get("/agents/available")
        response.raise_for_status()
        return response.json()

    async def get_agent_schema(self, agent_name: str) -> Dict[str, Any]:
        """Get request schema for agent.

        Args:
            agent_name: Name of agent

        Returns:
            Schema dict
        """
        response = await self.client.get(f"/agents/{agent_name}/schema")
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close HTTP client connection."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Synchronous wrapper for blocking usage
class SocratesAgentClientSync:
    """Synchronous wrapper for SocratesAgentClient.

    Allows blocking usage patterns for applications that don't use async.
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize synchronous client."""
        self.client = SocratesAgentClient(api_url, auth_token, timeout)
        self.loop = asyncio.new_event_loop()

    def project_manager(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call ProjectManager agent (blocking)."""
        return self.loop.run_until_complete(self.client.project_manager(request))

    def socratic_counselor(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call SocraticCounselor agent (blocking)."""
        return self.loop.run_until_complete(self.client.socratic_counselor(request))

    def code_generator(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call CodeGenerator agent (blocking)."""
        return self.loop.run_until_complete(self.client.code_generator(request))

    def code_validation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call CodeValidation agent (blocking)."""
        return self.loop.run_until_complete(self.client.code_validation(request))

    def quality_controller(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call QualityController agent (blocking)."""
        return self.loop.run_until_complete(self.client.quality_controller(request))

    def conflict_detector(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Call ConflictDetector agent (blocking)."""
        return self.loop.run_until_complete(self.client.conflict_detector(request))

    def __del__(self):
        """Cleanup event loop."""
        if self.loop:
            self.loop.close()
