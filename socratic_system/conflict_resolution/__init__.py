"""Conflict detection and resolution for Socrates AI"""

# Import ConflictDetector from local implementation
from .detector import ConflictDetector

# Import conflict checkers and utilities from socratic-conflict PyPI package
try:
    from socratic_conflict import (
        ConflictChecker,
        ConstraintsConflictChecker,
        GoalsConflictChecker,
        RequirementsConflictChecker,
        TechStackConflictChecker,
        CONFLICT_RULES,
        find_conflict_category,
    )
except ImportError:
    # Fallback: define empty implementations if socratic-conflict not available
    ConflictChecker = None
    ConstraintsConflictChecker = None
    GoalsConflictChecker = None
    RequirementsConflictChecker = None
    TechStackConflictChecker = None
    CONFLICT_RULES = {}
    find_conflict_category = None

__all__ = [
    "ConflictChecker",
    "ConflictDetector",
    "TechStackConflictChecker",
    "RequirementsConflictChecker",
    "GoalsConflictChecker",
    "ConstraintsConflictChecker",
    "CONFLICT_RULES",
    "find_conflict_category",
]
