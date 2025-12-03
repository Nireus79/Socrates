"""Conflict detection and resolution for Socratic RAG System"""

from .base import ConflictChecker
from .checkers import (
    TechStackConflictChecker,
    RequirementsConflictChecker,
    GoalsConflictChecker,
    ConstraintsConflictChecker
)
from .rules import CONFLICT_RULES, find_conflict_category

__all__ = [
    'ConflictChecker',
    'TechStackConflictChecker',
    'RequirementsConflictChecker',
    'GoalsConflictChecker',
    'ConstraintsConflictChecker',
    'CONFLICT_RULES',
    'find_conflict_category'
]
