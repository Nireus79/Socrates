"""REST handlers for agent API endpoints.

Exposes agents as REST endpoints for external library access.
"""

import logging
from typing import Any, Dict

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError:
    # FastAPI optional - only needed if using REST API
    FastAPI = None
    BaseModel = object

logger = logging.getLogger(__name__)


if BaseModel != object:

    class AgentRequest(BaseModel):
        """Agent request model."""

        class Config:
            extra = "allow"

    class AgentResponse(BaseModel):
        """Agent response model."""

        status: str
        data: Dict[str, Any]
        timestamp: str

    def create_agent_router(orchestrator):
        """Create FastAPI router for agent endpoints.

        Args:
            orchestrator: AgentOrchestrator instance

        Returns:
            FastAPI router
        """
        from fastapi import APIRouter

        from socratic_system.api.adapters.agent_adapter import AgentAdapter

        router = APIRouter(prefix="/agents", tags=["agents"])
        adapter = AgentAdapter(orchestrator)

        @router.post("/{agent_name}/process", response_model=AgentResponse)
        async def process_agent_request(agent_name: str, request: Dict[str, Any]):
            """Process request for specific agent.

            Args:
                agent_name: Name of agent
                request: Request data

            Returns:
                Response from agent
            """
            result = await adapter.handle_request(agent_name, request)

            if result["status"] == "error":
                raise HTTPException(status_code=400, detail=result)

            return result

        @router.get("/available")
        async def list_available_agents():
            """List available agents.

            Returns:
                List of agent names
            """
            available = list(adapter.AGENT_SCHEMAS.keys())
            return {"agents": available}

        @router.get("/{agent_name}/schema")
        async def get_agent_schema(agent_name: str):
            """Get request schema for agent.

            Args:
                agent_name: Name of agent

            Returns:
                Schema dict
            """
            schema = adapter.get_schema(agent_name)
            return schema

        return router

else:

    def create_agent_router(orchestrator):
        """Placeholder when FastAPI not available."""
        logger.warning("FastAPI not installed - REST API endpoints unavailable")
        return None
