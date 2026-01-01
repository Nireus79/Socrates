"""
Conflict detection and resolution agent for Socratic RAG System
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict

from socratic_system.conflict_resolution import (
    ConstraintsConflictChecker,
    GoalsConflictChecker,
    RequirementsConflictChecker,
    TechStackConflictChecker,
)

from .base import Agent


class ConflictDetectorAgent(Agent):
    """Detects and resolves conflicts in project specifications"""

    def __init__(self, orchestrator):
        super().__init__("ConflictDetector", orchestrator)

        # Initialize pluggable conflict checkers
        self.checkers = [
            TechStackConflictChecker(orchestrator),
            RequirementsConflictChecker(orchestrator),
            GoalsConflictChecker(orchestrator),
            ConstraintsConflictChecker(orchestrator),
        ]

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process conflict detection requests"""
        action = request.get("action")

        if action == "detect_conflicts":
            return self._detect_conflicts(request)
        elif action == "resolve_conflict":
            return self._resolve_conflict(request)
        elif action == "get_suggestions":
            return self._get_conflict_suggestions(request)

        return {"status": "error", "message": "Unknown action"}

    def _detect_conflicts(self, request: Dict) -> Dict:
        """Detect conflicts in new insights using pluggable checkers in parallel"""
        project = request.get("project")
        new_insights = request.get("new_insights")
        current_user = request.get("current_user")

        if not new_insights or not isinstance(new_insights, dict):
            return {"status": "success", "conflicts": []}

        all_conflicts = []

        # Run checkers in parallel using ThreadPoolExecutor for I/O-bound operations
        # This significantly speeds up conflict detection for large insight payloads
        with ThreadPoolExecutor(max_workers=len(self.checkers)) as executor:
            # Submit all checker tasks
            futures = {
                executor.submit(
                    checker.check_conflicts, project, new_insights, current_user
                ): checker
                for checker in self.checkers
            }

            # Collect results as they complete
            for future in as_completed(futures):
                checker = futures[future]
                try:
                    conflicts = future.result()
                    all_conflicts.extend(conflicts)
                except Exception as e:
                    self.log(f"Error in checker {checker.__class__.__name__}: {e}", "ERROR")

        return {"status": "success", "conflicts": all_conflicts}

    def _resolve_conflict(self, request: Dict) -> Dict:
        """Resolve a detected conflict"""
        conflict = request.get("conflict")

        return {"status": "success", "conflict_id": conflict.conflict_id, "resolved": True}

    def _get_conflict_suggestions(self, request: Dict) -> Dict:
        """Get suggestions for resolving a conflict"""
        conflict = request.get("conflict")

        return {"status": "success", "suggestions": conflict.suggestions}
