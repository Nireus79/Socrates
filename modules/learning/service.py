"""
LearningService - Service for learning and skill generation.

Includes:
- Learning engine for tracking agent interactions
- Skill generation using SkillGeneratorAgent
- Recommendation generation
- Event publishing for skill generation and interactions
"""

import logging
from typing import Any, Dict, List, Optional
from core.base_service import BaseService
from core.event_bus import EventBus


class LearningService(BaseService):
    """Service for managing learning and skill generation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize learning service."""
        super().__init__("learning", config)
        self.learning_engine = None
        self.interaction_history: Dict[str, List[Dict]] = {}
        self.agent_metrics: Dict[str, Dict] = {}
        self.event_bus: Optional[EventBus] = None
        self.logger = logging.getLogger(f"socrates.{self.service_name}")

    async def initialize(self) -> None:
        """Initialize the learning service."""
        try:
            from modules.learning.learning_engine import LearningEngine
            self.learning_engine = LearningEngine()
            self.logger.info("Learning engine initialized")
            self.logger.info("Learning service fully initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize learning service: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the learning service."""
        try:
            self.interaction_history.clear()
            self.agent_metrics.clear()
            self.logger.info("Learning service shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during learning shutdown: {e}")

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus for publishing events."""
        self.event_bus = event_bus
        self.logger.debug("Event bus set for learning service")

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        health = {
            "learning_engine": "healthy" if self.learning_engine else "unavailable",
            "interaction_history_items": len(self.interaction_history),
            "tracked_agents": len(self.agent_metrics),
        }
        return health

    async def track_interaction(
        self,
        agent_name: str,
        interaction_data: Dict[str, Any]
    ) -> None:
        """Track an agent interaction for learning."""
        try:
            # Initialize agent history if first time
            if agent_name not in self.interaction_history:
                self.interaction_history[agent_name] = []
                self.agent_metrics[agent_name] = {
                    "total_interactions": 0,
                    "successful_tasks": 0,
                    "failed_tasks": 0,
                    "avg_response_time": 0.0,
                }

            # Add interaction to history
            self.interaction_history[agent_name].append(interaction_data)

            # Update metrics
            metrics = self.agent_metrics[agent_name]
            metrics["total_interactions"] += 1

            if interaction_data.get("status") == "success":
                metrics["successful_tasks"] += 1
            elif interaction_data.get("status") == "failed":
                metrics["failed_tasks"] += 1

            # Update average response time if available
            if "response_time" in interaction_data:
                total_time = metrics.get("total_time", 0) + interaction_data["response_time"]
                metrics["total_time"] = total_time
                metrics["avg_response_time"] = total_time / metrics["total_interactions"]

            self.logger.debug(f"Tracked interaction for {agent_name}")
        except Exception as e:
            self.logger.error(f"Error tracking interaction: {e}")

    async def generate_skills(
        self,
        agent_name: str
    ) -> Dict[str, Any]:
        """Generate skills for an agent based on learning data."""
        try:
            if agent_name not in self.interaction_history:
                return {
                    "agent": agent_name,
                    "skills_generated": 0,
                    "skills": [],
                    "reason": "insufficient_history"
                }

            history = self.interaction_history[agent_name]
            metrics = self.agent_metrics[agent_name]

            # Simple skill generation logic based on patterns
            skills = []

            # If agent has high success rate, generate optimization skill
            if metrics["total_interactions"] >= 5:
                success_rate = metrics["successful_tasks"] / max(1, metrics["total_interactions"])
                if success_rate > 0.8:
                    skills.append({
                        "name": f"{agent_name}_optimization",
                        "type": "optimization",
                        "effectiveness": success_rate,
                        "description": f"Agent {agent_name} has achieved high success rate"
                    })

            # If agent has many interactions, generate specialization skill
            if metrics["total_interactions"] >= 20:
                skills.append({
                    "name": f"{agent_name}_specialization",
                    "type": "specialization",
                    "effectiveness": 0.75,
                    "description": f"Agent {agent_name} has specialized through extensive practice"
                })

            # Publish skill_generated event
            if self.event_bus and len(skills) > 0:
                try:
                    await self.event_bus.publish(
                        "skill_generated",
                        self.service_name,
                        {
                            "agent": agent_name,
                            "skills_count": len(skills),
                            "skills": skills,
                        }
                    )
                except Exception as e:
                    self.logger.error(f"Error publishing skill_generated event: {e}")

            self.logger.info(f"Generated {len(skills)} skills for {agent_name}")
            return {
                "agent": agent_name,
                "skills_generated": len(skills),
                "skills": skills,
                "metrics": metrics
            }
        except Exception as e:
            self.logger.error(f"Error generating skills: {e}")
            return {
                "agent": agent_name,
                "skills_generated": 0,
                "skills": [],
                "error": str(e)
            }

    async def get_recommendations(
        self,
        agent_name: str
    ) -> Dict[str, Any]:
        """Get recommendations for agent improvement."""
        try:
            if agent_name not in self.agent_metrics:
                return {
                    "agent": agent_name,
                    "recommendations": [],
                    "reason": "no_data"
                }

            metrics = self.agent_metrics[agent_name]
            recommendations = []

            # Generate recommendations based on metrics
            total = metrics["total_interactions"]
            success = metrics["successful_tasks"]
            failed = metrics["failed_tasks"]

            if total == 0:
                return {
                    "agent": agent_name,
                    "recommendations": [],
                    "reason": "insufficient_history"
                }

            success_rate = success / max(1, total)

            # Recommend improvement if success rate is low
            if success_rate < 0.5:
                recommendations.append({
                    "priority": "high",
                    "title": "Improve Success Rate",
                    "description": f"Agent has {success_rate:.1%} success rate",
                    "action": "Review failed interactions and adjust strategy"
                })

            # Recommend skill generation if enough data
            if total >= 10:
                recommendations.append({
                    "priority": "medium",
                    "title": "Generate Skills",
                    "description": f"Agent has {total} interactions recorded",
                    "action": "Consider generating new skills from learned patterns"
                })

            # Recommend consistency monitoring if variable performance
            if failed > success:
                recommendations.append({
                    "priority": "high",
                    "title": "Improve Consistency",
                    "description": f"More failed ({failed}) than successful ({success}) interactions",
                    "action": "Review and standardize agent behavior"
                })

            self.logger.info(f"Generated {len(recommendations)} recommendations for {agent_name}")
            return {
                "agent": agent_name,
                "recommendations": recommendations,
                "metrics": metrics
            }
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
            return {
                "agent": agent_name,
                "recommendations": [],
                "error": str(e)
            }

    async def get_agent_metrics(self, agent_name: str) -> Dict[str, Any]:
        """Get learning metrics for an agent."""
        return self.agent_metrics.get(agent_name, {})

    async def call_agents_service(self, agent_name: str) -> Optional[List[Dict]]:
        """
        Call agents service to get execution history.

        Returns:
            Execution history if successful, None otherwise
        """
        if not self.orchestrator:
            self.logger.warning("Orchestrator not set, cannot call agents service")
            return None

        try:
            history = await self.orchestrator.call_service(
                "agents",
                "get_execution_history",
                agent_name,
                100
            )
            self.logger.debug(f"Called agents service for {agent_name}")
            return history
        except Exception as e:
            self.logger.error(f"Error calling agents service: {e}")
            return None

    async def call_knowledge_service(self, content: str) -> Optional[str]:
        """
        Call knowledge service to store learning insights.

        Returns:
            Document ID if successful, None otherwise
        """
        if not self.orchestrator:
            self.logger.warning("Orchestrator not set, cannot call knowledge service")
            return None

        try:
            doc_id = await self.orchestrator.call_service(
                "knowledge",
                "add_knowledge",
                content,
                {"type": "learning_insight"}
            )
            self.logger.debug(f"Called knowledge service, doc_id: {doc_id}")
            return doc_id
        except Exception as e:
            self.logger.error(f"Error calling knowledge service: {e}")
            return None
