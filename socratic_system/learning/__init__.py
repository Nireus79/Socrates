"""Learning engine and pattern detection - imported from socratic-learning library."""

try:
    from socratic_learning import (
        KnowledgeBaseDocument,
        LearningEngine,
        QuestionEffectiveness,
        UserBehaviorPattern,
    )

    __all__ = [
        "LearningEngine",
        "QuestionEffectiveness",
        "UserBehaviorPattern",
        "KnowledgeBaseDocument",
    ]
except ImportError:
    # socratic-learning library not installed
    __all__ = []
