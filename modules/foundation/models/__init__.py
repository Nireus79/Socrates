"""
Foundation models for Socrates platform
"""

from .learning import KnowledgeBaseDocument, QuestionEffectiveness, UserBehaviorPattern

__all__ = [
    "QuestionEffectiveness",
    "UserBehaviorPattern",
    "KnowledgeBaseDocument",
]
