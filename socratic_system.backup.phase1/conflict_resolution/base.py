"""
Base class for conflict detection in Socrates AI
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from socratic_system.models import ConflictInfo, ProjectContext


class ConflictChecker(ABC):
    """
    Abstract base class for conflict checkers using Template Method pattern.

    Subclasses implement specific conflict detection logic by overriding
    _extract_values, _get_existing_values, and _find_conflict methods.
    """

    def __init__(self, orchestrator):
        """Initialize checker with orchestrator for Claude API access"""
        self.orchestrator = orchestrator

    def check_conflicts(
        self, project: ProjectContext, new_insights: Dict[str, Any], current_user: str
    ) -> List[ConflictInfo]:
        """
        Template method defining the conflict checking algorithm.

        Returns a list of ConflictInfo objects for detected conflicts.
        """
        # Step 1: Extract relevant field from insights
        new_values = self._extract_values(new_insights)
        if not new_values:
            return []

        # Step 2: Normalize values to list of strings
        new_values = self._normalize_values(new_values)
        if not new_values:
            return []

        # Step 3: Get existing values from project
        existing_values = self._get_existing_values(project)

        # Step 4: Check each new value against existing values
        conflicts = []
        for new_value in new_values:
            conflict = self._find_conflict(new_value, existing_values, project, current_user)
            if conflict:
                conflicts.append(conflict)

        return conflicts

    @staticmethod
    def _normalize_values(values: Any) -> List[str]:
        """
        Normalize values to list of strings - SHARED LOGIC.

        Handles various input types (string, list, etc.) and returns
        a clean list of non-empty strings.
        """
        if not values:
            return []
        elif isinstance(values, str):
            return [values.strip()] if values.strip() else []
        elif isinstance(values, list):
            return [str(item).strip() for item in values if item and str(item).strip()]
        else:
            result = str(values).strip()
            return [result] if result else []

    @abstractmethod
    def _extract_values(self, insights: Dict[str, Any]) -> Any:
        """
        Extract the relevant field from insights.

        Subclasses should implement this to extract their specific field.
        """
        pass

    @abstractmethod
    def _get_existing_values(self, project: ProjectContext) -> List[str]:
        """
        Get existing values from project context.

        Subclasses should implement this to return values of their specific type.
        """
        pass

    @abstractmethod
    def _find_conflict(
        self, new_value: str, existing_values: List[str], project: ProjectContext, current_user: str
    ) -> Optional[ConflictInfo]:
        """
        Determine if new_value conflicts with any existing_values.

        Returns ConflictInfo if conflict found, None otherwise.
        Subclasses implement their specific conflict detection logic.
        """
        pass

    def _build_conflict_info(
        self,
        conflict_type: str,
        old_value: str,
        new_value: str,
        project: ProjectContext,
        current_user: str,
        severity: str = "medium",
        suggestions: Optional[List[str]] = None,
    ) -> ConflictInfo:
        """Helper to create ConflictInfo object"""
        import datetime
        import uuid

        conflict_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()

        return ConflictInfo(
            conflict_id=conflict_id,
            conflict_type=conflict_type,
            old_value=old_value,
            new_value=new_value,
            old_author=project.owner,
            new_author=current_user,
            old_timestamp=now,
            new_timestamp=now,
            severity=severity,
            suggestions=suggestions or [],
        )
