"""Conflict detection and resolution - imported from socratic-conflict library."""

try:
    from socratic_conflict import (
        CONFLICT_RULES,
        ConflictChecker,
        ConflictInfo,
        ConstraintsConflictChecker,
        GoalsConflictChecker,
        RequirementsConflictChecker,
        TechStackConflictChecker,
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
except ImportError:
    # socratic-conflict library not installed
    __all__ = []
