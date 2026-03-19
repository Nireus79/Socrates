"""Learning models - re-exported from socratic-learning for compatibility."""

# Import from socratic-learning (fixes reverse dependency)
try:
    from socratic_learning import QuestionEffectiveness, UserBehaviorPattern, KnowledgeBaseDocument
except ImportError:
    QuestionEffectiveness = None  # type: ignore
    UserBehaviorPattern = None  # type: ignore
    KnowledgeBaseDocument = None  # type: ignore

__all__ = [
    "QuestionEffectiveness",
    "UserBehaviorPattern",
    "KnowledgeBaseDocument",
]
