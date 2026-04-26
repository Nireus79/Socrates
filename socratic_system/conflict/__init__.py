"""Conflict detection and resolution - imported from socratic-conflict library."""

from socratic_conflict import (
    ConflictChecker,
    TechStackConflictChecker,
    RequirementsConflictChecker,
    GoalsConflictChecker,
    ConstraintsConflictChecker,
    ConflictInfo,
    CONFLICT_RULES,
    find_conflict_category,
)

__all__ = [
    "ConflictChecker",
    "TechStackConflictChecker",
    "RequirementsConflictChecker",
    "GoalsConflictChecker",
    "ConstraintsConflictChecker",
    "ConflictInfo",
    "CONFLICT_RULES",
    "find_conflict_category",
]
