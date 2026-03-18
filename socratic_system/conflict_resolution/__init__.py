"""Conflict detection and resolution for Socrates AI"""

from .base import ConflictChecker
from .checkers import (
    ConstraintsConflictChecker,
    GoalsConflictChecker,
    RequirementsConflictChecker,
    TechStackConflictChecker,
)
from .detector import ConflictDetector
from .rules import CONFLICT_RULES, find_conflict_category

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
