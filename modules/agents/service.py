"""
AgentsService - Service wrapper for agent execution.

Provides unified interface for:
- Agent initialization
- Task execution
- Skill management
- Interaction tracking
- Event publishing for agent execution
"""

import logging
from typing import Any, Dict, List, Optional
from core.base_service import BaseService
from core.event_bus import EventBus
from modules.agents.base import Agent


class AgentsService(BaseService):
    """Service for managing and executing agents."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize agents service."""
        super().__init__("agents", config)
        self.agents: Dict[str, Agent] = {}
        self.execution_history: List[Dict] = []
        self.event_bus: Optional[EventBus] = None
        self.logger = logging.getLogger(f"socrates.{self.service_name}")

    async def initialize(self) -> None:
        """Initialize the agents service."""
        try:
            # Load all agents from modules/agents/agents/
            # For now, just initialize infrastructure
            self.logger.info("AgentsService initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize agents service: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the agents service."""
        try:
            self.agents.clear()
            self.execution_history.clear()
            self.logger.info("AgentsService shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during agents shutdown: {e}")

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus for publishing events."""
        self.event_bus = event_bus
        self.logger.debug("Event bus set for agents service")

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        return {
            "agents_loaded": len(self.agents),
            "executions_recorded": len(self.execution_history),
        }

    async def register_agent(self, agent: Agent) -> None:
        """Register an agent with the service."""
        self.agents[agent.name] = agent
        self.logger.debug(f"Registered agent: {agent.name}")

    async def get_agent(self, agent_name: str) -> Optional[Agent]:
        """Get an agent by name."""
        return self.agents.get(agent_name)

    async def execute_agent(
        self,
        agent_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an agent task."""
        try:
            agent = self.agents.get(agent_name)
            if not agent:
                return {
                    "status": "error",
                    "error": f"Agent {agent_name} not found",
                    "agent": agent_name
                }

            context = context or {}
            execution_id = f"{agent_name}_{len(self.execution_history)}"

            # Execute agent
            result = await agent.process_async({"task": task, **context})

            # Record execution
            execution_record = {
                "execution_id": execution_id,
                "agent": agent_name,
                "task": task,
                "result": result,
                "status": "success"
            }
            self.execution_history.append(execution_record)

            # Publish agent_executed event
            if self.event_bus:
                try:
                    await self.event_bus.publish(
                        "agent_executed",
                        self.service_name,
                        {
                            "agent": agent_name,
                            "task": task,
                            "execution_id": execution_id,
                            "status": "success",
                        }
                    )
                except Exception as e:
                    self.logger.error(f"Error publishing agent_executed event: {e}")

            self.logger.info(f"Executed agent {agent_name} for task: {task}")
            return execution_record
        except Exception as e:
            self.logger.error(f"Error executing agent {agent_name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "agent": agent_name
            }

    async def list_agents(self) -> Dict[str, str]:
        """List all registered agents."""
        return {name: agent.__class__.__name__ for name, agent in self.agents.items()}

    async def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """Get execution statistics for an agent."""
        executions = [
            e for e in self.execution_history
            if e.get("agent") == agent_name
        ]
        return {
            "agent": agent_name,
            "total_executions": len(executions),
            "successful": sum(1 for e in executions if e.get("status") == "success"),
            "failed": sum(1 for e in executions if e.get("status") == "error"),
        }

    async def get_execution_history(
        self,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get execution history."""
        history = self.execution_history
        if agent_name:
            history = [e for e in history if e.get("agent") == agent_name]
        return history[-limit:]
