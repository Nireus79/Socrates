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

        # Check goals conflicts (decision type)
        if "goals" in new_insights and project.goals:
            try:
                conflict = self.detector.detect_decision_conflict(
                    decision_name="project_goals",
                    proposals={
                        "existing": (
                            ", ".join(project.goals)
                            if isinstance(project.goals, list)
                            else str(project.goals)
                        ),
                        current_user: (
                            ", ".join(new_insights["goals"])
                            if isinstance(new_insights["goals"], list)
                            else str(new_insights["goals"])
                        ),
                    },
                    agents=["existing", current_user],
                )
                if conflict:
                    conflicts.append(
                        self._convert_to_conflict_info(conflict, "goals", project, current_user)
                    )
            except Exception as e:
                self.logger.debug(f"Goals conflict detection failed: {e}")

        # Check requirements conflicts (data type)
        if "requirements" in new_insights and project.requirements:
            try:
                conflict = self.detector.detect_data_conflict(
                    field_name="requirements",
                    values={
                        "existing": project.requirements,
                        current_user: new_insights["requirements"],
                    },
                    agents=["existing", current_user],
                )
                if conflict:
                    conflicts.append(
                        self._convert_to_conflict_info(
                            conflict, "requirements", project, current_user
                        )
                    )
            except Exception as e:
                self.logger.debug(f"Requirements conflict detection failed: {e}")

        # Check tech stack conflicts (data type)
        if "tech_stack" in new_insights and project.tech_stack:
            try:
                conflict = self.detector.detect_data_conflict(
                    field_name="tech_stack",
                    values={
                        "existing": project.tech_stack,
                        current_user: new_insights["tech_stack"],
                    },
                    agents=["existing", current_user],
                )
                if conflict:
                    conflicts.append(
                        self._convert_to_conflict_info(
                            conflict, "tech_stack", project, current_user
                        )
                    )
            except Exception as e:
                self.logger.debug(f"Tech stack conflict detection failed: {e}")

        # Check constraints conflicts (data type)
        if "constraints" in new_insights and project.constraints:
            try:
                conflict = self.detector.detect_data_conflict(
                    field_name="constraints",
                    values={
                        "existing": project.constraints,
                        current_user: new_insights["constraints"],
                    },
                    agents=["existing", current_user],
                )
                if conflict:
                    conflicts.append(
                        self._convert_to_conflict_info(
                            conflict, "constraints", project, current_user
                        )
                    )
            except Exception as e:
                self.logger.debug(f"Constraints conflict detection failed: {e}")

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
            conflict = self.detector.detect_workflow_conflict(
                workflow_id=workflow_id, conflicting_steps=steps, context=context or {}
            )
            return conflict
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
            conflict = self.detector.detect_decision_conflict(
                decision_name=decision_name, proposals=proposals, agents=agents
            )
            return conflict
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
