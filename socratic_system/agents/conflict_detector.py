"""
Conflict detection and resolution agent for Socrates AI

Phase 2B Migration: Async-first implementation with agent bus support
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict

try:
    from socratic_conflict import (
        ConstraintsConflictChecker,
        GoalsConflictChecker,
        RequirementsConflictChecker,
        TechStackConflictChecker,
    )

    CONFLICT_CHECKERS_AVAILABLE = True
except ImportError:
    CONFLICT_CHECKERS_AVAILABLE = False
    ConstraintsConflictChecker = None
    GoalsConflictChecker = None
    RequirementsConflictChecker = None
    TechStackConflictChecker = None

from .base import Agent


class ConflictDetectorAgent(Agent):
    """Detects and resolves conflicts in project specifications

    Phase 2B Migration: Async-first CRUD implementation
    - Supports both sync (process) and async (process_async) interfaces
    - Registers with agent bus for discovery
    - All blocking operations run in thread pool (non-blocking)
    """

    def __init__(self, orchestrator):
        super().__init__("ConflictDetector", orchestrator, auto_register=True)

        # Initialize pluggable conflict checkers if available
        if CONFLICT_CHECKERS_AVAILABLE:
            self.checkers = [
                TechStackConflictChecker(orchestrator),
                RequirementsConflictChecker(orchestrator),
                GoalsConflictChecker(orchestrator),
                ConstraintsConflictChecker(orchestrator),
            ]
        else:
            self.checkers = []

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process conflict detection requests (sync wrapper for backward compatibility).

        Phase 2B: Delegates to sync helper methods
        """
        action = request.get("action")

        if action == "detect_conflicts":
            return self._detect_conflicts_sync(request)
        elif action == "resolve_conflict":
            return self._resolve_conflict_sync(request)
        elif action == "get_suggestions":
            return self._get_conflict_suggestions_sync(request)

        return {"status": "error", "message": "Unknown action"}

    async def process_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process conflict detection requests asynchronously (Phase 2B).

        Primary implementation - true async processing with thread pool
        """
        action = request.get("action")

        if action == "detect_conflicts":
            return await self._detect_conflicts_async(request)
        elif action == "resolve_conflict":
            return await self._resolve_conflict_async(request)
        elif action == "get_suggestions":
            return await self._get_conflict_suggestions_async(request)

        return {"status": "error", "message": "Unknown action"}

    def get_capabilities(self) -> list:
        """Declare agent capabilities for bus discovery (Phase 2B)"""
        return [
            "conflict_detection",
            "conflict_resolution",
            "suggestion_generation",
        ]

    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata for registration (Phase 2B)"""
        return {
            "version": "2.0",
            "description": "Conflict detection and resolution in project specifications",
            "capabilities_count": 3,
        }

    def _detect_conflicts_sync(self, request: Dict) -> Dict:
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

    async def _detect_conflicts_async(self, request: Dict) -> Dict:
        """Detect conflicts asynchronously (Phase 2B)."""
        return await asyncio.to_thread(self._detect_conflicts_sync, request)

    def _resolve_conflict_sync(self, request: Dict) -> Dict:
        """Resolve a detected conflict"""
        conflict = request.get("conflict")

        return {"status": "success", "conflict_id": conflict.conflict_id, "resolved": True}

    async def _resolve_conflict_async(self, request: Dict) -> Dict:
        """Resolve conflict asynchronously (Phase 2B)."""
        return await asyncio.to_thread(self._resolve_conflict_sync, request)

    def _get_conflict_suggestions_sync(self, request: Dict) -> Dict:
        """Get suggestions for resolving a conflict"""
        conflict = request.get("conflict")

        return {"status": "success", "suggestions": conflict.suggestions}

    async def _get_conflict_suggestions_async(self, request: Dict) -> Dict:
        """Get conflict suggestions asynchronously (Phase 2B)."""
        return await asyncio.to_thread(self._get_conflict_suggestions_sync, request)
