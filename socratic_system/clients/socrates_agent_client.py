"""
SocratesAgentClient - Python library for invoking Socrates agents via REST API

Provides convenient interface for external applications to call agents hosted
in a Socrates API instance.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Union

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


class SocratesAgentClientError(Exception):
    """Base exception for SocratesAgentClient errors"""
    pass


class AgentNotFoundError(SocratesAgentClientError):
    """Raised when agent is not found"""
    pass


class AgentTimeoutError(SocratesAgentClientError):
    """Raised when agent invocation times out"""
    pass


class JobNotFoundError(SocratesAgentClientError):
    """Raised when job is not found"""
    pass


class SocratesAgentClient:
    """
    Python client for Socrates agents API.

    Provides synchronous and asynchronous methods for invoking agents.

    Example:
        ```python
        client = SocratesAgentClient("http://localhost:8000")

        # Synchronous invocation
        result = client.invoke_agent_sync(
            "socratic_counselor",
            action="generate_question",
            project_id="proj_123"
        )

        # Asynchronous invocation with polling
        job_id = await client.invoke_agent_async(
            "code_generator",
            action="generate_code",
            project_id="proj_123"
        )

        # Poll job status
        status = await client.get_job_status(job_id)

        # Wait for result with timeout
        result = await client.wait_for_result(job_id, timeout=300)
        ```
    """

    DEFAULT_API_BASE = "http://localhost:8000"
    DEFAULT_TIMEOUT = 300  # 5 minutes
    POLL_INTERVAL = 1.0  # seconds

    def __init__(
        self,
        api_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize SocratesAgentClient.

        Args:
            api_url: Base URL of Socrates API (default: http://localhost:8000)
            auth_token: Optional authentication token for API requests
            timeout: Default timeout for requests in seconds
        """
        if httpx is None:
            raise ImportError("httpx required for SocratesAgentClient. Install with: pip install httpx")

        self.api_url = api_url or self.DEFAULT_API_BASE
        self.auth_token = auth_token
        self.timeout = timeout
        self.base_headers = {"Content-Type": "application/json"}

        if auth_token:
            self.base_headers["Authorization"] = f"Bearer {auth_token}"

        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=self.base_headers,
                timeout=self.timeout,
            )
        return self._http_client

    async def list_agents(self) -> Dict[str, str]:
        """
        List all available agents.

        Returns:
            Dictionary of agent names to descriptions
        """
        try:
            response = await self.http_client.get("/api/v1/agents/list")
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise SocratesAgentClientError(f"API error: {data.get('message')}")

            return data.get("data", {}).get("agents", {})
        except httpx.HTTPError as e:
            raise SocratesAgentClientError(f"Failed to list agents: {e}")

    async def invoke_agent_async(
        self,
        agent_name: str,
        action: str = "process",
        project_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Submit asynchronous agent job.

        Args:
            agent_name: Name of agent to invoke
            action: Action/method to call on agent (default: "process")
            project_id: Optional project ID for context
            **kwargs: Additional parameters to pass to agent

        Returns:
            Job ID for polling status

        Raises:
            AgentNotFoundError: If agent doesn't exist
            SocratesAgentClientError: If request fails
        """
        payload = {
            "action": action,
            **kwargs,
        }

        if project_id:
            payload["project_id"] = project_id

        try:
            response = await self.http_client.post(
                f"/api/v1/agents/{agent_name}/process-async",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                if "Unknown agent" in data.get("message", ""):
                    raise AgentNotFoundError(f"Agent '{agent_name}' not found")
                raise SocratesAgentClientError(f"API error: {data.get('message')}")

            job_id = data.get("data", {}).get("job_id")
            if not job_id:
                raise SocratesAgentClientError("No job_id returned from server")

            return job_id

        except httpx.HTTPError as e:
            raise SocratesAgentClientError(f"Failed to invoke agent '{agent_name}': {e}")

    async def invoke_agent_sync(
        self,
        agent_name: str,
        action: str = "process",
        project_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Invoke agent synchronously and wait for response.

        Args:
            agent_name: Name of agent to invoke
            action: Action/method to call on agent (default: "process")
            project_id: Optional project ID for context
            **kwargs: Additional parameters to pass to agent

        Returns:
            Agent response data

        Raises:
            AgentNotFoundError: If agent doesn't exist
            AgentTimeoutError: If request times out
            SocratesAgentClientError: If request fails
        """
        payload = {
            "action": action,
            **kwargs,
        }

        if project_id:
            payload["project_id"] = project_id

        try:
            response = await self.http_client.post(
                f"/api/v1/agents/{agent_name}/process",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                if "Unknown agent" in data.get("message", ""):
                    raise AgentNotFoundError(f"Agent '{agent_name}' not found")
                raise SocratesAgentClientError(f"Agent error: {data.get('message')}")

            return data.get("data", data)

        except httpx.HTTPError as e:
            if "timeout" in str(e).lower():
                raise AgentTimeoutError(f"Agent '{agent_name}' request timed out")
            raise SocratesAgentClientError(f"Failed to invoke agent '{agent_name}': {e}")

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of an async job.

        Args:
            job_id: Job ID returned from invoke_agent_async()

        Returns:
            Job status information including:
                - status: "pending", "completed", "failed", or "timeout"
                - complete: Boolean whether job is complete
                - result: Agent result when complete
                - error: Error message if failed
                - duration_ms: Execution time in milliseconds

        Raises:
            JobNotFoundError: If job not found
            SocratesAgentClientError: If request fails
        """
        try:
            response = await self.http_client.get(f"/api/v1/agents/jobs/{job_id}/status")
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                if "not found" in data.get("message", "").lower():
                    raise JobNotFoundError(f"Job '{job_id}' not found")
                raise SocratesAgentClientError(f"Status check error: {data.get('message')}")

            return data.get("data", {})

        except httpx.HTTPError as e:
            if "404" in str(e):
                raise JobNotFoundError(f"Job '{job_id}' not found")
            raise SocratesAgentClientError(f"Failed to get job status: {e}")

    async def wait_for_result(
        self,
        job_id: str,
        timeout: Optional[int] = None,
        poll_interval: float = None,
    ) -> Dict[str, Any]:
        """
        Wait for async job to complete and return result.

        Args:
            job_id: Job ID returned from invoke_agent_async()
            timeout: Maximum time to wait in seconds (default: client timeout)
            poll_interval: Time between status checks in seconds (default: 1.0)

        Returns:
            Job result when completed

        Raises:
            AgentTimeoutError: If timeout exceeded before completion
            JobNotFoundError: If job not found
            SocratesAgentClientError: If job fails or request fails
        """
        timeout = timeout or self.timeout
        poll_interval = poll_interval or self.POLL_INTERVAL
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise AgentTimeoutError(
                    f"Job '{job_id}' did not complete within {timeout} seconds"
                )

            status_info = await self.get_job_status(job_id)
            status = status_info.get("status")

            if status == "completed":
                return status_info.get("result", status_info)

            if status == "failed":
                error = status_info.get("error", "Unknown error")
                raise SocratesAgentClientError(f"Job failed: {error}")

            if status == "timeout":
                raise AgentTimeoutError(f"Job execution timed out")

            # Still pending, wait before checking again
            await asyncio.sleep(min(poll_interval, timeout - elapsed))

    async def get_batch_job_status(self, job_ids: list) -> Dict[str, Dict[str, Any]]:
        """
        Get status for multiple jobs at once.

        Args:
            job_ids: List of job IDs to check

        Returns:
            Dictionary mapping job_ids to status information

        Raises:
            SocratesAgentClientError: If request fails
        """
        job_ids_str = ",".join(job_ids)

        try:
            response = await self.http_client.get(
                "/api/v1/agents/jobs/batch",
                params={"job_ids": job_ids_str},
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise SocratesAgentClientError(f"Batch status error: {data.get('message')}")

            return data.get("data", {}).get("jobs", {})

        except httpx.HTTPError as e:
            raise SocratesAgentClientError(f"Failed to get batch job status: {e}")

    async def close(self):
        """Close HTTP client and cleanup resources"""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Synchronous wrapper for convenience
class SocratesAgentClientSync:
    """
    Synchronous wrapper around SocratesAgentClient for non-async code.

    Example:
        ```python
        with SocratesAgentClientSync("http://localhost:8000") as client:
            result = client.invoke_agent(
                "socratic_counselor",
                action="generate_question",
                project_id="proj_123"
            )
            print(result)
        ```
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: int = SocratesAgentClient.DEFAULT_TIMEOUT,
    ):
        """Initialize synchronous client wrapper"""
        self._client = SocratesAgentClient(api_url, auth_token, timeout)
        self._loop = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop"""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def list_agents(self) -> Dict[str, str]:
        """Synchronously list available agents"""
        loop = self._get_loop()
        if loop.is_running():
            raise RuntimeError("Cannot use sync wrapper in async context")
        return loop.run_until_complete(self._client.list_agents())

    def invoke_agent(
        self,
        agent_name: str,
        action: str = "process",
        project_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Synchronously invoke agent and wait for response"""
        loop = self._get_loop()
        if loop.is_running():
            raise RuntimeError("Cannot use sync wrapper in async context")
        return loop.run_until_complete(
            self._client.invoke_agent_sync(agent_name, action, project_id, **kwargs)
        )

    def submit_job(
        self,
        agent_name: str,
        action: str = "process",
        project_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Synchronously submit async job"""
        loop = self._get_loop()
        if loop.is_running():
            raise RuntimeError("Cannot use sync wrapper in async context")
        return loop.run_until_complete(
            self._client.invoke_agent_async(agent_name, action, project_id, **kwargs)
        )

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Synchronously get job status"""
        loop = self._get_loop()
        if loop.is_running():
            raise RuntimeError("Cannot use sync wrapper in async context")
        return loop.run_until_complete(self._client.get_job_status(job_id))

    def wait_for_result(
        self,
        job_id: str,
        timeout: Optional[int] = None,
        poll_interval: float = None,
    ) -> Dict[str, Any]:
        """Synchronously wait for job result"""
        loop = self._get_loop()
        if loop.is_running():
            raise RuntimeError("Cannot use sync wrapper in async context")
        return loop.run_until_complete(
            self._client.wait_for_result(job_id, timeout, poll_interval)
        )

    def close(self):
        """Close client"""
        if self._loop and not self._loop.is_closed():
            self._loop.run_until_complete(self._client.close())

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
