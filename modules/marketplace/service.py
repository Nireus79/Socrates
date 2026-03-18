"""
SkillMarketplace - Central skill catalog and discovery service.

Provides:
- Skill registration and cataloging
- Search and filtering capabilities
- Skill discovery by type, effectiveness, usage
- Marketplace metrics and analytics
- Event publishing for skill lifecycle
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from core.base_service import BaseService
from core.event_bus import EventBus


class SkillMarketplace(BaseService):
    """Service for managing centralized skill marketplace."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize skill marketplace."""
        super().__init__("marketplace", config)
        self.catalog: Dict[str, Dict[str, Any]] = {}  # skill_id -> metadata
        self.index_by_type: Dict[str, List[str]] = {}  # type -> [skill_ids]
        self.index_by_agent: Dict[str, List[str]] = {}  # agent -> [skill_ids]
        self.index_by_tag: Dict[str, List[str]] = {}  # tag -> [skill_ids]
        self.skill_metadata: Dict[str, Dict[str, Any]] = {}  # skill_id -> metadata
        self.skill_adoption: Dict[str, Dict[str, Any]] = {}  # skill_id -> adoption data
        self.event_bus: Optional[EventBus] = None
        self.logger = logging.getLogger(f"socrates.{self.service_name}")

    async def initialize(self) -> None:
        """Initialize the skill marketplace."""
        try:
            self.logger.info("SkillMarketplace initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize marketplace: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the skill marketplace."""
        try:
            self.catalog.clear()
            self.index_by_type.clear()
            self.index_by_agent.clear()
            self.index_by_tag.clear()
            self.skill_metadata.clear()
            self.skill_adoption.clear()
            self.logger.info("SkillMarketplace shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during marketplace shutdown: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        return {
            "skills_in_catalog": len(self.catalog),
            "skill_types": len(self.index_by_type),
            "agents_with_skills": len(self.index_by_agent),
            "total_tags": len(self.index_by_tag),
        }

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus for publishing events."""
        self.event_bus = event_bus
        self.logger.debug("Event bus set for marketplace")

    async def register_skill(self, skill_id: str, skill_data: Dict[str, Any]) -> bool:
        """
        Register a skill in the marketplace catalog.

        Args:
            skill_id: Unique skill identifier
            skill_data: Skill information (name, type, effectiveness, agent, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            if skill_id in self.catalog:
                self.logger.warning(f"Skill {skill_id} already registered")
                return False

            # Store in catalog
            self.catalog[skill_id] = skill_data.copy()

            # Create metadata
            metadata = {
                "skill_id": skill_id,
                "name": skill_data.get("name", "unknown"),
                "type": skill_data.get("type", "unknown"),
                "agent": skill_data.get("agent", "unknown"),
                "effectiveness": skill_data.get("effectiveness", 0.5),
                "usage_count": skill_data.get("usage_count", 0),
                "created_at": skill_data.get("created_at", datetime.utcnow().isoformat()),
                "registered_at": datetime.utcnow().isoformat(),
                "tags": skill_data.get("tags", []),
            }
            self.skill_metadata[skill_id] = metadata

            # Initialize adoption tracking
            self.skill_adoption[skill_id] = {
                "registrations": 1,
                "adoptions": 0,
                "distribution_count": 0,
                "adopting_agents": [skill_data.get("agent", "unknown")],
            }

            # Index by type
            skill_type = skill_data.get("type", "unknown")
            if skill_type not in self.index_by_type:
                self.index_by_type[skill_type] = []
            self.index_by_type[skill_type].append(skill_id)

            # Index by agent
            agent = skill_data.get("agent", "unknown")
            if agent not in self.index_by_agent:
                self.index_by_agent[agent] = []
            self.index_by_agent[agent].append(skill_id)

            # Index by tags
            for tag in skill_data.get("tags", []):
                if tag not in self.index_by_tag:
                    self.index_by_tag[tag] = []
                self.index_by_tag[tag].append(skill_id)

            # Publish event
            if self.event_bus:
                try:
                    await self.event_bus.publish(
                        "skill_registered",
                        self.service_name,
                        {
                            "skill_id": skill_id,
                            "name": metadata["name"],
                            "type": metadata["type"],
                            "agent": metadata["agent"],
                            "effectiveness": metadata["effectiveness"],
                        },
                    )
                except Exception as e:
                    self.logger.error(f"Error publishing skill_registered event: {e}")

            self.logger.info(f"Registered skill {skill_id} ({metadata['name']}) in marketplace")
            return True
        except Exception as e:
            self.logger.error(f"Error registering skill: {e}")
            return False

    async def discover_skills(
        self,
        skill_type: Optional[str] = None,
        min_effectiveness: float = 0.0,
        min_usage: int = 0,
        tags: Optional[List[str]] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Discover skills matching criteria.

        Args:
            skill_type: Filter by skill type
            min_effectiveness: Minimum effectiveness (0.0-1.0)
            min_usage: Minimum usage count
            tags: Filter by tags (all must match)
            max_results: Maximum results to return

        Returns:
            List of matching skill metadata sorted by effectiveness
        """
        try:
            matching_skills = []

            # Start with all skills or filtered by type
            if skill_type:
                skill_ids = self.index_by_type.get(skill_type, [])
            else:
                skill_ids = list(self.catalog.keys())

            # Filter by criteria
            for skill_id in skill_ids:
                metadata = self.skill_metadata.get(skill_id)
                if not metadata:
                    continue

                # Check effectiveness
                if metadata["effectiveness"] < min_effectiveness:
                    continue

                # Check usage
                if metadata["usage_count"] < min_usage:
                    continue

                # Check tags (all must match)
                if tags:
                    skill_tags = set(metadata.get("tags", []))
                    required_tags = set(tags)
                    if not required_tags.issubset(skill_tags):
                        continue

                matching_skills.append(metadata.copy())

            # Sort by effectiveness (descending)
            matching_skills.sort(key=lambda x: x["effectiveness"], reverse=True)

            # Apply limit
            result = matching_skills[:max_results]

            self.logger.debug(f"Discovered {len(result)} skills (type={skill_type}, eff>={min_effectiveness})")
            return result
        except Exception as e:
            self.logger.error(f"Error discovering skills: {e}")
            return []

    async def search_skills(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for skills by name or description.

        Args:
            query: Search query (skill name or partial match)
            max_results: Maximum results to return

        Returns:
            List of matching skill metadata
        """
        try:
            query_lower = query.lower()
            matching_skills = []

            for metadata in self.skill_metadata.values():
                name = metadata.get("name", "").lower()
                skill_type = metadata.get("type", "").lower()

                # Match on name or type
                if query_lower in name or query_lower in skill_type:
                    matching_skills.append(metadata.copy())

            # Sort by effectiveness
            matching_skills.sort(key=lambda x: x["effectiveness"], reverse=True)

            result = matching_skills[:max_results]
            self.logger.debug(f"Searched for '{query}': found {len(result)} skills")
            return result
        except Exception as e:
            self.logger.error(f"Error searching skills: {e}")
            return []

    async def get_skill_metadata(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed metadata for a skill."""
        try:
            if skill_id not in self.skill_metadata:
                return None

            metadata = self.skill_metadata[skill_id].copy()
            adoption = self.skill_adoption.get(skill_id, {})
            metadata["adoption_stats"] = adoption

            return metadata
        except Exception as e:
            self.logger.error(f"Error getting skill metadata: {e}")
            return None

    async def get_skills_by_agent(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get all skills created by or associated with an agent."""
        try:
            skill_ids = self.index_by_agent.get(agent_name, [])
            skills = [
                self.skill_metadata[sid].copy()
                for sid in skill_ids
                if sid in self.skill_metadata
            ]
            return skills
        except Exception as e:
            self.logger.error(f"Error getting skills for agent {agent_name}: {e}")
            return []

    async def get_skills_by_type(self, skill_type: str) -> List[Dict[str, Any]]:
        """Get all skills of a specific type."""
        try:
            skill_ids = self.index_by_type.get(skill_type, [])
            skills = [
                self.skill_metadata[sid].copy()
                for sid in skill_ids
                if sid in self.skill_metadata
            ]
            # Sort by effectiveness
            skills.sort(key=lambda x: x["effectiveness"], reverse=True)
            return skills
        except Exception as e:
            self.logger.error(f"Error getting skills by type {skill_type}: {e}")
            return []

    async def get_top_skills(
        self,
        skill_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get top performing skills."""
        try:
            if skill_type:
                skills = await self.get_skills_by_type(skill_type)
            else:
                skills = list(self.skill_metadata.values())

            # Sort by effectiveness
            skills.sort(key=lambda x: x["effectiveness"], reverse=True)

            return skills[:limit]
        except Exception as e:
            self.logger.error(f"Error getting top skills: {e}")
            return []

    async def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics."""
        try:
            total_skills = len(self.catalog)
            total_adoptions = sum(
                adoption.get("adoptions", 0) for adoption in self.skill_adoption.values()
            )
            avg_effectiveness = (
                sum(m["effectiveness"] for m in self.skill_metadata.values()) / total_skills
                if total_skills > 0
                else 0
            )

            return {
                "total_skills": total_skills,
                "total_skill_types": len(self.index_by_type),
                "total_agents": len(self.index_by_agent),
                "total_adoptions": total_adoptions,
                "average_effectiveness": avg_effectiveness,
                "total_tags": len(self.index_by_tag),
                "most_adopted": self._get_most_adopted_skill(),
                "highest_effectiveness": self._get_highest_effectiveness_skill(),
            }
        except Exception as e:
            self.logger.error(f"Error getting marketplace stats: {e}")
            return {}

    def _get_most_adopted_skill(self) -> Optional[str]:
        """Get the most adopted skill."""
        if not self.skill_adoption:
            return None

        most_adopted = max(
            self.skill_adoption.items(),
            key=lambda x: x[1].get("adoptions", 0),
        )
        return most_adopted[0]

    def _get_highest_effectiveness_skill(self) -> Optional[str]:
        """Get the highest effectiveness skill."""
        if not self.skill_metadata:
            return None

        highest = max(
            self.skill_metadata.items(),
            key=lambda x: x[1].get("effectiveness", 0),
        )
        return highest[0]

    async def update_skill_in_marketplace(self, skill_id: str, updates: Dict[str, Any]) -> bool:
        """Update skill metadata in marketplace."""
        try:
            if skill_id not in self.skill_metadata:
                return False

            # Update metadata
            for key, value in updates.items():
                if key in self.skill_metadata[skill_id]:
                    self.skill_metadata[skill_id][key] = value

            # Update catalog
            if skill_id in self.catalog:
                for key, value in updates.items():
                    self.catalog[skill_id][key] = value

            self.logger.debug(f"Updated skill {skill_id} in marketplace")
            return True
        except Exception as e:
            self.logger.error(f"Error updating skill {skill_id}: {e}")
            return False
