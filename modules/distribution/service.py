"""
SkillDistributionService - Enable skill sharing across agents.

Provides:
- Skill distribution and cloning
- Cross-agent skill adoption
- Adoption tracking and metrics
- Version management
- Distribution workflows
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from core.base_service import BaseService
from core.event_bus import EventBus


class SkillDistributionService(BaseService):
    """Service for managing skill distribution across agents."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize skill distribution service."""
        super().__init__("distribution", config)
        self.distributions: Dict[str, Dict[str, Any]] = {}  # distribution_id -> data
        self.skill_versions: Dict[str, List[Dict[str, Any]]] = {}  # skill_id -> versions
        self.adoption_tracking: Dict[str, Dict[str, Any]] = {}  # skill_id -> adoption_data
        self.distribution_history: List[Dict[str, Any]] = []  # track all distributions
        self.event_bus: Optional[EventBus] = None
        self.logger = logging.getLogger(f"socrates.{self.service_name}")

    async def initialize(self) -> None:
        """Initialize the distribution service."""
        try:
            self.logger.info("SkillDistributionService initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize distribution service: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the distribution service."""
        try:
            self.distributions.clear()
            self.skill_versions.clear()
            self.adoption_tracking.clear()
            self.distribution_history.clear()
            self.logger.info("SkillDistributionService shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during distribution shutdown: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        return {
            "total_distributions": len(self.distributions),
            "skills_with_versions": len(self.skill_versions),
            "skills_being_adopted": len(self.adoption_tracking),
            "distribution_history_count": len(self.distribution_history),
        }

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus for publishing events."""
        self.event_bus = event_bus
        self.logger.debug("Event bus set for distribution service")

    async def distribute_skill_to_agent(
        self,
        source_skill_id: str,
        source_agent: str,
        target_agent: str,
        skill_data: Dict[str, Any],
    ) -> Optional[str]:
        """
        Distribute a skill from source agent to target agent.

        Args:
            source_skill_id: ID of skill to distribute
            source_agent: Agent creating the skill
            target_agent: Agent receiving the skill
            skill_data: The skill data to distribute

        Returns:
            New skill ID if successful, None otherwise
        """
        try:
            # Create new skill ID for distributed copy
            dist_id = f"{source_skill_id}_dist_{target_agent}_{len(self.distributions)}"
            new_skill_id = f"skill_distributed_{target_agent}_{len(self.distributions)}"

            # Create distribution record
            distribution = {
                "distribution_id": dist_id,
                "source_skill_id": source_skill_id,
                "source_agent": source_agent,
                "target_agent": target_agent,
                "new_skill_id": new_skill_id,
                "distributed_at": datetime.utcnow().isoformat(),
                "original_skill_data": skill_data.copy(),
                "status": "distributed",
                "version": "1.0",
            }
            self.distributions[dist_id] = distribution

            # Track version
            if source_skill_id not in self.skill_versions:
                self.skill_versions[source_skill_id] = []

            version_info = {
                "version": "1.0",
                "skill_id": new_skill_id,
                "from_agent": source_agent,
                "to_agent": target_agent,
                "created_at": datetime.utcnow().isoformat(),
                "lineage": source_skill_id,
            }
            self.skill_versions[source_skill_id].append(version_info)

            # Initialize adoption tracking
            if source_skill_id not in self.adoption_tracking:
                self.adoption_tracking[source_skill_id] = {
                    "skill_id": source_skill_id,
                    "source_agent": source_agent,
                    "distributions": 1,
                    "adoptions": [
                        {
                            "agent": target_agent,
                            "status": "active",
                            "adopted_at": datetime.utcnow().isoformat(),
                            "skill_id": new_skill_id,
                        }
                    ],
                    "last_distribution": datetime.utcnow().isoformat(),
                }
            else:
                self.adoption_tracking[source_skill_id]["distributions"] += 1
                self.adoption_tracking[source_skill_id]["adoptions"].append({
                    "agent": target_agent,
                    "status": "active",
                    "adopted_at": datetime.utcnow().isoformat(),
                    "skill_id": new_skill_id,
                })

            # Record in history
            self.distribution_history.append({
                "distribution_id": dist_id,
                "timestamp": datetime.utcnow().isoformat(),
                "source": source_skill_id,
                "target_agent": target_agent,
                "result": "success",
            })

            # Publish event
            if self.event_bus:
                try:
                    await self.event_bus.publish(
                        "skill_distributed",
                        self.service_name,
                        {
                            "source_skill_id": source_skill_id,
                            "new_skill_id": new_skill_id,
                            "source_agent": source_agent,
                            "target_agent": target_agent,
                            "effectiveness": skill_data.get("effectiveness", 0.5),
                        },
                    )
                except Exception as e:
                    self.logger.error(f"Error publishing skill_distributed event: {e}")

            self.logger.info(
                f"Distributed skill {source_skill_id} from {source_agent} to {target_agent}"
            )
            return new_skill_id
        except Exception as e:
            self.logger.error(f"Error distributing skill: {e}")
            return None

    async def broadcast_skill_to_agents(
        self,
        source_skill_id: str,
        source_agent: str,
        target_agents: List[str],
        skill_data: Dict[str, Any],
    ) -> Dict[str, Optional[str]]:
        """
        Broadcast a skill to multiple agents.

        Args:
            source_skill_id: ID of skill to distribute
            source_agent: Agent creating the skill
            target_agents: List of agents to distribute to
            skill_data: The skill data to distribute

        Returns:
            Dictionary mapping agent names to new skill IDs
        """
        try:
            results = {}
            for target_agent in target_agents:
                new_skill_id = await self.distribute_skill_to_agent(
                    source_skill_id,
                    source_agent,
                    target_agent,
                    skill_data,
                )
                results[target_agent] = new_skill_id

            self.logger.info(
                f"Broadcast skill {source_skill_id} to {len(target_agents)} agents"
            )
            return results
        except Exception as e:
            self.logger.error(f"Error broadcasting skill: {e}")
            return {}

    async def get_adoption_status(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get adoption status for a skill."""
        try:
            if skill_id not in self.adoption_tracking:
                return None

            adoption_data = self.adoption_tracking[skill_id].copy()
            adoption_data["adoption_count"] = len(adoption_data.get("adoptions", []))
            adoption_data["adoption_rate"] = (
                adoption_data["adoption_count"] / max(1, adoption_data.get("distributions", 1))
            )

            return adoption_data
        except Exception as e:
            self.logger.error(f"Error getting adoption status: {e}")
            return None

    async def get_agent_adoptions(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get all skills adopted by an agent."""
        try:
            adoptions = []
            for skill_id, adoption_data in self.adoption_tracking.items():
                for adoption in adoption_data.get("adoptions", []):
                    if adoption.get("agent") == agent_name:
                        adoptions.append({
                            "adopted_skill_id": adoption.get("skill_id"),
                            "source_skill_id": skill_id,
                            "source_agent": adoption_data.get("source_agent"),
                            "adopted_at": adoption.get("adopted_at"),
                            "status": adoption.get("status"),
                        })

            return adoptions
        except Exception as e:
            self.logger.error(f"Error getting agent adoptions: {e}")
            return []

    async def get_skill_lineage(self, skill_id: str) -> List[Dict[str, Any]]:
        """Get the lineage/version history of a skill."""
        try:
            if skill_id not in self.skill_versions:
                return []

            return self.skill_versions[skill_id].copy()
        except Exception as e:
            self.logger.error(f"Error getting skill lineage: {e}")
            return []

    async def get_distribution_metrics(self) -> Dict[str, Any]:
        """Get overall distribution metrics."""
        try:
            total_distributions = len(self.distributions)
            total_adoptions = sum(
                len(adoption_data.get("adoptions", []))
                for adoption_data in self.adoption_tracking.values()
            )
            unique_adopting_agents = set()

            for adoption_data in self.adoption_tracking.values():
                for adoption in adoption_data.get("adoptions", []):
                    unique_adopting_agents.add(adoption.get("agent"))

            avg_adoption_rate = (
                sum(
                    len(adoption_data.get("adoptions", [])) /
                    max(1, adoption_data.get("distributions", 1))
                    for adoption_data in self.adoption_tracking.values()
                ) / max(1, len(self.adoption_tracking))
            )

            return {
                "total_distributions": total_distributions,
                "total_adoptions": total_adoptions,
                "unique_adopting_agents": len(unique_adopting_agents),
                "skills_with_adoptions": len(self.adoption_tracking),
                "average_adoption_rate": avg_adoption_rate,
            }
        except Exception as e:
            self.logger.error(f"Error getting distribution metrics: {e}")
            return {}

    async def get_distribution_history(
        self,
        skill_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get distribution history with optional filters."""
        try:
            history = self.distribution_history.copy()

            # Filter by skill
            if skill_id:
                history = [h for h in history if h.get("source") == skill_id]

            # Filter by agent
            if agent_name:
                history = [h for h in history if h.get("target_agent") == agent_name]

            # Limit results
            return history[-limit:]
        except Exception as e:
            self.logger.error(f"Error getting distribution history: {e}")
            return []

    async def record_adoption_result(
        self,
        source_skill_id: str,
        target_agent: str,
        effectiveness: float,
        success: bool = True,
    ) -> bool:
        """Record the result of an adoption attempt."""
        try:
            if source_skill_id not in self.adoption_tracking:
                return False

            adoption_data = self.adoption_tracking[source_skill_id]
            for adoption in adoption_data.get("adoptions", []):
                if adoption.get("agent") == target_agent:
                    adoption["effectiveness"] = effectiveness
                    adoption["success"] = success
                    adoption["result_recorded_at"] = datetime.utcnow().isoformat()
                    return True

            return False
        except Exception as e:
            self.logger.error(f"Error recording adoption result: {e}")
            return False

    async def get_adoption_performance_comparison(
        self,
        source_skill_id: str,
    ) -> Dict[str, Any]:
        """Compare performance of skill across adopting agents."""
        try:
            if source_skill_id not in self.adoption_tracking:
                return {}

            adoption_data = self.adoption_tracking[source_skill_id]
            adoptions = adoption_data.get("adoptions", [])

            comparison = {
                "skill_id": source_skill_id,
                "source_agent": adoption_data.get("source_agent"),
                "adoptions": len(adoptions),
                "agent_performance": [],
            }

            for adoption in adoptions:
                agent_perf = {
                    "agent": adoption.get("agent"),
                    "effectiveness": adoption.get("effectiveness", "not_recorded"),
                    "success": adoption.get("success"),
                    "adopted_at": adoption.get("adopted_at"),
                }
                comparison["agent_performance"].append(agent_perf)

            return comparison
        except Exception as e:
            self.logger.error(f"Error getting adoption performance: {e}")
            return {}
