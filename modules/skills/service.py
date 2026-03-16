"""
SkillService - Service for skill generation and management.

Integrates SkillGeneratorAgent from ecosystem and provides:
- Skill generation from learning data
- Skill storage and retrieval
- Agent-skill associations
- Effectiveness tracking
- Skill recommendations
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from core.base_service import BaseService
from core.event_bus import EventBus


class SkillService(BaseService):
    """Service for managing skills and skill generation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize skill service."""
        super().__init__("skills", config)
        self.skill_generator = None
        self.skills: Dict[str, Dict[str, Any]] = {}  # skill_id -> skill_data
        self.agent_skills: Dict[str, List[str]] = {}  # agent_name -> [skill_ids]
        self.skill_effectiveness: Dict[str, float] = {}  # skill_id -> effectiveness_score
        self.skill_usage: Dict[str, int] = {}  # skill_id -> usage_count
        self.event_bus: Optional[EventBus] = None
        self.logger = logging.getLogger(f"socrates.{self.service_name}")

    async def initialize(self) -> None:
        """Initialize the skill service."""
        try:
            # Import SkillGeneratorAgent from ecosystem
            try:
                from socratic_agents.agents.skill_generator_agent import SkillGeneratorAgent
                self.skill_generator = SkillGeneratorAgent()
                self.logger.info("SkillGeneratorAgent loaded from ecosystem")
            except ImportError:
                self.logger.warning("SkillGeneratorAgent not available, using mock")
                self.skill_generator = None

            self.logger.info("SkillService initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize skill service: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the skill service."""
        try:
            self.skills.clear()
            self.agent_skills.clear()
            self.skill_effectiveness.clear()
            self.skill_usage.clear()
            self.logger.info("SkillService shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during skills shutdown: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        return {
            "skills_stored": len(self.skills),
            "agents_with_skills": len(self.agent_skills),
            "skill_generator": "available" if self.skill_generator else "unavailable",
        }

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus for publishing events."""
        self.event_bus = event_bus
        self.logger.debug("Event bus set for skill service")

    async def generate_skills(
        self,
        agent_name: str,
        maturity_data: Optional[Dict[str, Any]] = None,
        learning_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate skills for an agent using SkillGeneratorAgent.

        Args:
            agent_name: Name of the agent
            maturity_data: Agent maturity information
            learning_data: Learning metrics
            context: Additional context

        Returns:
            Dictionary with generated skills
        """
        try:
            if not self.skill_generator:
                self.logger.warning("SkillGeneratorAgent not available")
                return {
                    "agent": agent_name,
                    "skills_generated": 0,
                    "skills": [],
                    "reason": "skill_generator_unavailable",
                }

            # Call SkillGeneratorAgent
            result = self.skill_generator.process({
                "action": "generate",
                "maturity_data": maturity_data or {},
                "learning_data": learning_data or {},
                "context": context or {"agent": agent_name},
            })

            # Process results and store skills
            generated_skills = []
            for skill_data in result.get("skills", []):
                skill_id = f"skill_{agent_name}_{len(self.skills)}"
                skill = {
                    "id": skill_id,
                    "agent": agent_name,
                    "name": skill_data.get("name", "unknown"),
                    "type": skill_data.get("type", "optimization"),
                    "effectiveness": skill_data.get("effectiveness", 0.5),
                    "created_at": datetime.utcnow().isoformat(),
                    "usage_count": 0,
                    "parameters": skill_data.get("parameters", {}),
                }

                self.skills[skill_id] = skill
                self.skill_effectiveness[skill_id] = skill["effectiveness"]
                self.skill_usage[skill_id] = 0

                generated_skills.append(skill)

            # Track agent-skill association
            if agent_name not in self.agent_skills:
                self.agent_skills[agent_name] = []
            self.agent_skills[agent_name].extend([s["id"] for s in generated_skills])

            # Publish event
            if self.event_bus and len(generated_skills) > 0:
                try:
                    await self.event_bus.publish(
                        "skills_generated",
                        self.service_name,
                        {
                            "agent": agent_name,
                            "skills_count": len(generated_skills),
                            "skills": generated_skills,
                        }
                    )
                except Exception as e:
                    self.logger.error(f"Error publishing skills_generated event: {e}")

            self.logger.info(f"Generated {len(generated_skills)} skills for {agent_name}")
            return {
                "agent": agent_name,
                "skills_generated": len(generated_skills),
                "skills": generated_skills,
            }
        except Exception as e:
            self.logger.error(f"Error generating skills: {e}")
            return {
                "agent": agent_name,
                "skills_generated": 0,
                "skills": [],
                "error": str(e),
            }

    async def get_agent_skills(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get all skills for an agent."""
        skill_ids = self.agent_skills.get(agent_name, [])
        return [self.skills[sid] for sid in skill_ids if sid in self.skills]

    async def apply_skill(self, skill_id: str) -> bool:
        """
        Apply/use a skill and update usage count.

        Returns:
            True if successful, False otherwise
        """
        try:
            if skill_id not in self.skills:
                self.logger.warning(f"Skill {skill_id} not found")
                return False

            self.skill_usage[skill_id] = self.skill_usage.get(skill_id, 0) + 1
            return True
        except Exception as e:
            self.logger.error(f"Error applying skill: {e}")
            return False

    async def update_skill_effectiveness(self, skill_id: str, effectiveness_score: float) -> bool:
        """Update effectiveness score for a skill."""
        try:
            if skill_id not in self.skills:
                return False

            # Update skill effectiveness (weighted average)
            current_eff = self.skill_effectiveness.get(skill_id, 0.5)
            usage_count = self.skill_usage.get(skill_id, 0)

            new_eff = (current_eff * usage_count + effectiveness_score) / (usage_count + 1)
            self.skill_effectiveness[skill_id] = new_eff
            self.skills[skill_id]["effectiveness"] = new_eff

            self.logger.debug(f"Updated skill {skill_id} effectiveness to {new_eff}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating skill effectiveness: {e}")
            return False

    async def get_skill_recommendations(self, agent_name: str) -> Dict[str, Any]:
        """Get skill recommendations for an agent."""
        try:
            if not self.skill_generator:
                return {
                    "agent": agent_name,
                    "recommendations": [],
                    "reason": "skill_generator_unavailable",
                }

            # Call SkillGeneratorAgent for recommendations
            result = self.skill_generator.process({
                "action": "evaluate",
                "agent_name": agent_name,
            })

            recommendations = result.get("recommendations", [])

            self.logger.info(f"Generated {len(recommendations)} recommendations for {agent_name}")
            return {
                "agent": agent_name,
                "recommendations": recommendations,
                "count": len(recommendations),
            }
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
            return {
                "agent": agent_name,
                "recommendations": [],
                "error": str(e),
            }

    async def list_skills(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """List skills, optionally filtered by agent."""
        if agent_name:
            skills = await self.get_agent_skills(agent_name)
            return {
                "agent": agent_name,
                "skills": skills,
                "count": len(skills),
            }
        else:
            return {
                "total_skills": len(self.skills),
                "skills": list(self.skills.values()),
            }

    async def get_skill_stats(self, skill_id: str) -> Dict[str, Any]:
        """Get statistics for a skill."""
        if skill_id not in self.skills:
            return {"error": "Skill not found"}

        skill = self.skills[skill_id]
        return {
            "skill_id": skill_id,
            "name": skill["name"],
            "agent": skill["agent"],
            "effectiveness": self.skill_effectiveness.get(skill_id, 0),
            "usage_count": self.skill_usage.get(skill_id, 0),
            "created_at": skill["created_at"],
        }
