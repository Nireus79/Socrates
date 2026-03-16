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
        self.skill_performance: Dict[str, List[float]] = {}  # skill_id -> [performance_scores]
        self.skill_last_applied: Dict[str, str] = {}  # skill_id -> last_applied_timestamp
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
            self.skill_performance.clear()
            self.skill_last_applied.clear()
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
        performance_history = self.skill_performance.get(skill_id, [])

        return {
            "skill_id": skill_id,
            "name": skill["name"],
            "agent": skill["agent"],
            "effectiveness": self.skill_effectiveness.get(skill_id, 0),
            "usage_count": self.skill_usage.get(skill_id, 0),
            "created_at": skill["created_at"],
            "last_applied": self.skill_last_applied.get(skill_id),
            "performance_history_length": len(performance_history),
            "performance_trend": self._calculate_trend(performance_history),
        }

    def _calculate_trend(self, performance_history: List[float]) -> str:
        """Calculate trend from performance history."""
        if len(performance_history) < 2:
            return "insufficient_data"

        recent = performance_history[-5:] if len(performance_history) >= 5 else performance_history
        avg_recent = sum(recent) / len(recent)

        older = performance_history[:-5] if len(performance_history) > 5 else recent
        avg_older = sum(older) / len(older)

        if avg_recent > avg_older + 0.1:
            return "improving"
        elif avg_recent < avg_older - 0.1:
            return "declining"
        else:
            return "stable"

    async def track_skill_execution(
        self,
        skill_id: str,
        execution_result: Dict[str, Any],
        performance_score: Optional[float] = None,
    ) -> bool:
        """
        Track skill execution and update effectiveness based on result.

        Args:
            skill_id: ID of skill executed
            execution_result: Result from agent execution
            performance_score: Optional explicit performance score (0.0-1.0)

        Returns:
            True if successful, False otherwise
        """
        try:
            if skill_id not in self.skills:
                self.logger.warning(f"Skill {skill_id} not found for tracking")
                return False

            # Calculate performance score if not provided
            if performance_score is None:
                performance_score = self._calculate_performance_score(execution_result)

            # Track performance history
            if skill_id not in self.skill_performance:
                self.skill_performance[skill_id] = []
            self.skill_performance[skill_id].append(performance_score)

            # Update effectiveness with weighted average
            current_eff = self.skill_effectiveness.get(skill_id, 0.5)
            usage_count = self.skill_usage.get(skill_id, 0)

            new_eff = (current_eff * usage_count + performance_score) / (usage_count + 1)
            self.skill_effectiveness[skill_id] = new_eff
            self.skills[skill_id]["effectiveness"] = new_eff

            # Update last applied timestamp
            self.skill_last_applied[skill_id] = datetime.utcnow().isoformat()

            self.logger.debug(
                f"Tracked skill {skill_id}: score={performance_score:.2f}, "
                f"effectiveness={new_eff:.2f}, usage={usage_count + 1}"
            )

            # Publish event
            if self.event_bus:
                try:
                    await self.event_bus.publish(
                        "skill_executed",
                        self.service_name,
                        {
                            "skill_id": skill_id,
                            "performance_score": performance_score,
                            "effectiveness": new_eff,
                            "usage_count": usage_count + 1,
                        },
                    )
                except Exception as e:
                    self.logger.error(f"Error publishing skill_executed event: {e}")

            return True
        except Exception as e:
            self.logger.error(f"Error tracking skill execution: {e}")
            return False

    def _calculate_performance_score(self, execution_result: Dict[str, Any]) -> float:
        """
        Calculate performance score from execution result.

        Scoring logic:
        - success: 0.9
        - partial_success: 0.6
        - error: 0.1
        - Custom score if provided: use directly
        """
        # Check for explicit performance score in result
        if "performance_score" in execution_result:
            score = execution_result["performance_score"]
            if isinstance(score, (int, float)) and 0 <= score <= 1:
                return float(score)

        # Infer from execution status
        status = execution_result.get("status", "unknown")
        if status == "success":
            return 0.9
        elif status == "partial_success":
            return 0.6
        elif status == "error":
            return 0.1
        else:
            return 0.5  # Default for unknown status

    async def optimize_skills(self, agent_name: str) -> Dict[str, Any]:
        """
        Optimize skills for an agent by analyzing effectiveness.

        Returns:
            Dictionary with optimization results
        """
        try:
            agent_skills = self.agent_skills.get(agent_name, [])
            if not agent_skills:
                return {
                    "agent": agent_name,
                    "optimized_skills": [],
                    "removed_skills": [],
                    "reason": "no_skills",
                }

            optimized = []
            removed = []

            for skill_id in agent_skills:
                effectiveness = self.skill_effectiveness.get(skill_id, 0.5)
                usage_count = self.skill_usage.get(skill_id, 0)

                # Remove skills with very low effectiveness and limited usage
                if effectiveness < 0.3 and usage_count >= 5:
                    removed.append(skill_id)
                    self.logger.info(f"Removed ineffective skill {skill_id} for {agent_name}")
                # Flag skills for improvement
                elif effectiveness < 0.5:
                    optimized.append({
                        "skill_id": skill_id,
                        "action": "improve",
                        "current_effectiveness": effectiveness,
                        "recommendation": "needs_parameters_tuning",
                    })

            # Update agent skills list
            self.agent_skills[agent_name] = [
                s for s in agent_skills if s not in removed
            ]

            self.logger.info(
                f"Optimized skills for {agent_name}: "
                f"{len(optimized)} to improve, {len(removed)} removed"
            )

            return {
                "agent": agent_name,
                "optimized_skills": optimized,
                "removed_skills": removed,
                "total_skills": len(self.agent_skills[agent_name]),
            }
        except Exception as e:
            self.logger.error(f"Error optimizing skills: {e}")
            return {
                "agent": agent_name,
                "error": str(e),
                "optimized_skills": [],
                "removed_skills": [],
            }

    async def get_effectiveness_report(
        self,
        agent_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get effectiveness report for skills."""
        try:
            if agent_name:
                # Report for specific agent
                agent_skills = self.agent_skills.get(agent_name, [])
                skills_report = []
                for skill_id in agent_skills:
                    if skill_id in self.skills:
                        skills_report.append({
                            "skill_id": skill_id,
                            "name": self.skills[skill_id]["name"],
                            "effectiveness": self.skill_effectiveness.get(skill_id, 0),
                            "usage_count": self.skill_usage.get(skill_id, 0),
                            "performance_avg": (
                                sum(self.skill_performance.get(skill_id, [0])) /
                                len(self.skill_performance.get(skill_id, [1]))
                            ),
                        })

                avg_effectiveness = (
                    sum(s["effectiveness"] for s in skills_report) / len(skills_report)
                    if skills_report
                    else 0
                )

                return {
                    "agent": agent_name,
                    "skills": skills_report,
                    "average_effectiveness": avg_effectiveness,
                    "total_skills": len(skills_report),
                }
            else:
                # Report for all skills
                all_skills_report = []
                for skill_id, skill_data in self.skills.items():
                    all_skills_report.append({
                        "skill_id": skill_id,
                        "name": skill_data["name"],
                        "agent": skill_data["agent"],
                        "effectiveness": self.skill_effectiveness.get(skill_id, 0),
                        "usage_count": self.skill_usage.get(skill_id, 0),
                    })

                return {
                    "total_skills": len(all_skills_report),
                    "skills": all_skills_report,
                    "avg_system_effectiveness": (
                        sum(s["effectiveness"] for s in all_skills_report) /
                        len(all_skills_report)
                        if all_skills_report
                        else 0
                    ),
                }
        except Exception as e:
            self.logger.error(f"Error generating effectiveness report: {e}")
            return {
                "error": str(e),
                "agent": agent_name,
                "skills": [],
            }
