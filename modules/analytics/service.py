"""
SkillAnalytics - Track metrics and optimize skill ecosystem.

Provides:
- Cross-agent skill metrics
- Performance analysis
- Skill recommendations
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from core.base_service import BaseService
from core.event_bus import EventBus


class SkillAnalytics(BaseService):
    """Service for analyzing skill ecosystem metrics."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize skill analytics."""
        super().__init__("analytics", config)
        self.metrics_cache: Dict[str, Dict[str, Any]] = {}
        self.agent_metrics: Dict[str, Dict[str, Any]] = {}
        self.event_bus: Optional[EventBus] = None
        self.logger = logging.getLogger(f"socrates.{self.service_name}")

    async def initialize(self) -> None:
        """Initialize analytics service."""
        try:
            self.logger.info("SkillAnalytics initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize analytics: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown analytics service."""
        try:
            self.metrics_cache.clear()
            self.agent_metrics.clear()
            self.logger.info("SkillAnalytics shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during analytics shutdown: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        return {
            "skills_tracked": len(self.metrics_cache),
            "agents_analyzed": len(self.agent_metrics),
        }

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set event bus."""
        self.event_bus = event_bus
        self.logger.debug("Event bus set for analytics")

    async def track_skill_metric(
        self,
        skill_id: str,
        agent_name: str,
        metric_name: str,
        metric_value: float,
    ) -> bool:
        """Track a skill metric."""
        try:
            if skill_id not in self.metrics_cache:
                self.metrics_cache[skill_id] = {
                    "skill_id": skill_id,
                    "agents_using": set(),
                    "metrics": {},
                }

            self.metrics_cache[skill_id]["agents_using"].add(agent_name)
            if metric_name not in self.metrics_cache[skill_id]["metrics"]:
                self.metrics_cache[skill_id]["metrics"][metric_name] = []

            self.metrics_cache[skill_id]["metrics"][metric_name].append(metric_value)
            return True
        except Exception as e:
            self.logger.error(f"Error tracking metric: {e}")
            return False

    async def analyze_skill_performance(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Analyze performance of a specific skill."""
        try:
            if skill_id not in self.metrics_cache:
                return None

            metrics = self.metrics_cache[skill_id]
            analysis = {
                "skill_id": skill_id,
                "agents_using": len(metrics["agents_using"]),
                "metric_summaries": {},
                "performance_score": 0.0,
            }

            for metric_name, values in metrics.get("metrics", {}).items():
                if values:
                    analysis["metric_summaries"][metric_name] = {
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values),
                    }

            return analysis
        except Exception as e:
            self.logger.error(f"Error analyzing skill performance: {e}")
            return None

    async def identify_high_performing_skills(
        self,
        min_effectiveness: float = 0.75,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Identify high-performing skills."""
        try:
            candidates = []

            for skill_id, metrics in self.metrics_cache.items():
                effectiveness_scores = metrics.get("metrics", {}).get("effectiveness", [])
                if not effectiveness_scores:
                    continue

                avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores)
                if avg_effectiveness < min_effectiveness:
                    continue

                adoption_count = len(metrics["agents_using"])
                candidates.append({
                    "skill_id": skill_id,
                    "effectiveness": avg_effectiveness,
                    "adoption": adoption_count,
                })

            candidates.sort(key=lambda x: x["effectiveness"], reverse=True)
            return candidates[:limit]
        except Exception as e:
            self.logger.error(f"Error identifying high-performing skills: {e}")
            return []

    async def get_ecosystem_health(self) -> Dict[str, Any]:
        """Get overall ecosystem health metrics."""
        try:
            total_skills = len(self.metrics_cache)
            if total_skills == 0:
                return {
                    "total_skills": 0,
                    "total_agents": 0,
                    "average_effectiveness": 0.0,
                    "ecosystem_health": "no_data",
                }

            total_agents = len(self.agent_metrics)
            avg_effectiveness = 0.0
            total_effectiveness = 0.0
            count = 0

            for metrics in self.metrics_cache.values():
                effectiveness_scores = metrics.get("metrics", {}).get("effectiveness", [])
                if effectiveness_scores:
                    total_effectiveness += sum(effectiveness_scores)
                    count += len(effectiveness_scores)

            if count > 0:
                avg_effectiveness = total_effectiveness / count

            if avg_effectiveness > 0.8:
                health = "excellent"
            elif avg_effectiveness > 0.6:
                health = "good"
            elif avg_effectiveness > 0.4:
                health = "fair"
            else:
                health = "poor"

            return {
                "total_skills": total_skills,
                "total_agents": total_agents,
                "average_effectiveness": avg_effectiveness,
                "ecosystem_health": health,
            }
        except Exception as e:
            self.logger.error(f"Error calculating ecosystem health: {e}")
            return {}

    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        try:
            ecosystem_health = await self.get_ecosystem_health()
            high_performers = await self.identify_high_performing_skills()

            return {
                "report_type": "ecosystem_performance",
                "generated_at": datetime.utcnow().isoformat(),
                "ecosystem_health": ecosystem_health,
                "high_performers": high_performers[:5],
            }
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {}
