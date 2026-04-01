"""
Conflict detection and resolution using socratic-conflict library.

Replaces internal conflict detection with socratic-conflict for more robust
multi-agent conflict detection and resolution.
"""

import logging
from typing import Any, Dict, List, Optional

try:
    from socratic_conflict import ConflictDetector as SKConflictDetector
except ImportError:
    # socratic_conflict is optional - provide graceful fallback
    SKConflictDetector = None  # type: ignore

from socratic_core.utils import ProjectIDGenerator, serialize_datetime
from socratic_system.models import ConflictInfo, ProjectContext


class ConflictDetector:
    """
    Unified conflict detection using socratic-conflict library.

    Supports:
    - Data conflicts: Different values for same field from different sources
    - Decision conflicts: Different proposals for same decision
    - Workflow conflicts: Incompatible workflow steps
    """

    def __init__(self, orchestrator: Optional[Any] = None):
        """
        Initialize conflict detector.

        Args:
            orchestrator: Optional orchestrator for context
        """
        self.orchestrator = orchestrator
        self.logger = logging.getLogger("socrates.conflict")
        self.detector = None

        if SKConflictDetector is None:
            self.logger.warning("socratic_conflict not available - conflict detection disabled")
            return

        try:
            self.detector = SKConflictDetector()
            self.logger.info("ConflictDetector initialized (socratic-conflict)")
        except Exception as e:
            self.logger.error(f"Failed to initialize ConflictDetector: {e}")
            # Allow graceful degradation

    def detect_project_conflicts(
        self, project: ProjectContext, new_insights: Dict[str, Any], current_user: str
    ) -> List[ConflictInfo]:
        """
        Detect conflicts between new insights and existing project values.

        Args:
            project: Current project context
            new_insights: New insights to check
            current_user: User making the change

        Returns:
            List of detected conflicts
        """
        if self.detector is None:
            self.logger.debug("Conflict detection unavailable - feature disabled")
            return []

        conflicts = []

        # Use the actual library method: detect_conflicts(agent_states)
        # Build agent states from project data
        agent_states = {
            "existing": {
                "goal": ", ".join(project.goals) if project.goals else "",
                "requirements": project.requirements or "",
                "tech_stack": project.tech_stack or "",
                "constraints": project.constraints or "",
            },
            current_user: {
                "goal": ", ".join(new_insights.get("goals", [])) if isinstance(new_insights.get("goals"), list) else str(new_insights.get("goals", "")),
                "requirements": new_insights.get("requirements", ""),
                "tech_stack": new_insights.get("tech_stack", ""),
                "constraints": new_insights.get("constraints", ""),
            }
        }

        try:
            # Call the actual library method
            library_conflicts = self.detector.detect_conflicts(agent_states)

            # Convert library conflicts to ConflictInfo
            for lib_conflict in library_conflicts:
                conflict_info = ConflictInfo(
                    id=lib_conflict.id,
                    field=lib_conflict.type,
                    existing_value=agent_states["existing"].get(lib_conflict.type, ""),
                    new_value=agent_states[current_user].get(lib_conflict.type, ""),
                    severity=lib_conflict.severity,
                    description=lib_conflict.description,
                    suggested_resolution=f"Review and reconcile {lib_conflict.type} conflict",
                    agents_involved=lib_conflict.agents,
                )
                conflicts.append(conflict_info)
        except Exception as e:
            self.logger.debug(f"Conflict detection using library failed: {e}")
            # Fallback: simple string comparison detection
            conflicts.extend(self._detect_conflicts_fallback(project, new_insights, current_user))

        return conflicts

    def detect_workflow_conflicts(
        self, workflow_id: str, steps: List[Dict[str, Any]], context: Optional[Dict] = None
    ) -> Optional[Any]:
        """
        Detect conflicts in workflow execution.

        Args:
            workflow_id: Workflow identifier
            steps: List of workflow steps
            context: Optional context

        Returns:
            Conflict if detected, None otherwise
        """
        if self.detector is None:
            return None

        try:
            # Convert workflow steps to agent states for the actual library method
            agent_states = {}
            for step in steps:
                agent_name = step.get("agent", f"step_{len(agent_states)}")
                agent_states[agent_name] = {
                    "goal": step.get("goal", ""),
                    "action": step.get("action", ""),
                }

            conflicts = self.detector.detect_conflicts(agent_states)
            # Return first conflict if any (for backward compatibility)
            return conflicts[0] if conflicts else None
        except Exception as e:
            self.logger.error(f"Workflow conflict detection failed: {e}")
            return None

    def detect_agent_conflicts(
        self,
        agents: List[str],
        proposals: Dict[str, str],
        decision_name: str = "multi_agent_decision",
    ) -> Optional[Any]:
        """
        Detect conflicts between agent proposals.

        Args:
            agents: List of agent names
            proposals: Dict of agent -> proposal
            decision_name: Name of the decision being made

        Returns:
            Conflict if detected, None otherwise
        """
        if self.detector is None:
            return None

        try:
            # Convert proposals to agent states for the actual library method
            agent_states = {}
            for agent, proposal in proposals.items():
                agent_states[agent] = {
                    "goal": decision_name,
                    "proposal": proposal,
                }

            conflicts = self.detector.detect_conflicts(agent_states)
            # Return first conflict if any (for backward compatibility)
            return conflicts[0] if conflicts else None
        except Exception as e:
            self.logger.error(f"Agent conflict detection failed: {e}")
            return None

    def resolve_conflict(self, conflict: Any, resolution_strategy: str = "consensus") -> Any:
        """
        Attempt to resolve a conflict.

        Args:
            conflict: Conflict object from detector
            resolution_strategy: Strategy to use ('consensus', 'voting', 'manual')

        Returns:
            Resolution result
        """
        # This would use socratic-conflict's resolution capabilities
        # when they are fully implemented
        self.logger.info(f"Resolving conflict {conflict.conflict_id} using {resolution_strategy}")
        return conflict

    def get_all_conflicts(self) -> List[Any]:
        """Get all detected conflicts"""
        if self.detector is None:
            return []

        try:
            return self.detector.get_conflicts()
        except Exception as e:
            self.logger.error(f"Failed to get conflicts: {e}")
            return []

    def clear_conflicts(self):
        """Clear all conflicts"""
        if self.detector is None:
            return

        try:
            self.detector.clear_conflicts()
            self.logger.info("All conflicts cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear conflicts: {e}")

    def _detect_conflicts_fallback(
        self, project: ProjectContext, new_insights: Dict[str, Any], current_user: str
    ) -> List[ConflictInfo]:
        """
        Fallback conflict detection using simple string comparison.

        Args:
            project: Current project context
            new_insights: New insights to check
            current_user: User making the change

        Returns:
            List of detected conflicts
        """
        conflicts = []

        # Simple string comparison for basic conflicts
        fields_to_check = ["goals", "requirements", "tech_stack", "constraints"]

        for field in fields_to_check:
            if field not in new_insights:
                continue

            existing = getattr(project, field, None)
            new = new_insights.get(field)

            if existing and new and str(existing).lower() != str(new).lower():
                conflict_info = ConflictInfo(
                    id=f"conflict_{field}_{ProjectIDGenerator.generate()}",
                    field=field,
                    existing_value=str(existing),
                    new_value=str(new),
                    severity="medium",
                    description=f"Different {field}: '{existing}' vs '{new}'",
                    suggested_resolution=f"Review and reconcile {field}",
                    agents_involved=["existing", current_user],
                )
                conflicts.append(conflict_info)

        return conflicts

    @staticmethod
    def _convert_to_conflict_info(
        conflict: Any, field_name: str, project: ProjectContext, current_user: str
    ) -> ConflictInfo:
        """
        Convert socratic-conflict Conflict to Socrates ConflictInfo.

        Args:
            conflict: Conflict object from socratic-conflict
            field_name: Name of field in conflict
            project: Project context
            current_user: User who triggered conflict

        Returns:
            ConflictInfo object
        """
        import datetime

        # Extract proposal values
        old_value = ""
        new_value = ""
        if conflict.proposals and len(conflict.proposals) >= 2:
            old_value = conflict.proposals[0].description
            new_value = conflict.proposals[1].description

        return ConflictInfo(
            conflict_id=ProjectIDGenerator.generate(),
            conflict_type=field_name,
            old_value=old_value,
            new_value=new_value,
            old_author=project.owner,
            new_author=current_user,
            old_timestamp=serialize_datetime(datetime.datetime.now()),
            new_timestamp=serialize_datetime(datetime.datetime.now()),
            severity=conflict.severity if hasattr(conflict, "severity") else "medium",
            suggestions=[
                f"Review {field_name} values",
                f"Propose consensus between {project.owner} and {current_user}",
            ],
        )
