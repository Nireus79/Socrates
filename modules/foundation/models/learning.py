"""Learning models - re-exported from socratic-learning for compatibility."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

# Try to import real implementations from socratic-learning if available
try:
    from socratic_learning import (
        QuestionEffectiveness,
        UserBehaviorPattern,
        KnowledgeBaseDocument
    )
except ImportError:
    # Stub implementations for when socratic_learning is not available
    @dataclass
    class QuestionEffectiveness:  # type: ignore[no-redef]
        """Stub: Tracks effectiveness of questions asked to users."""
        id: str
        user_id: str
        question_template_id: str
        role: str
        times_asked: int = 0
        times_answered_well: int = 0
        average_answer_length: int = 0
        effectiveness_score: Decimal = Decimal("0.0")
        created_at: datetime = field(default_factory=datetime.now)
        updated_at: datetime = field(default_factory=datetime.now)
        metadata: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class UserBehaviorPattern:  # type: ignore[no-redef]
        """Stub: Tracks user learning behavior patterns."""
        id: str
        user_id: str
        pattern_type: str = "general"
        communication_style: str = "analytical"
        detail_level: str = "medium"
        learning_pace: str = "steady"
        preferred_topics: List[str] = field(default_factory=list)
        strength_areas: List[str] = field(default_factory=list)
        improvement_areas: List[str] = field(default_factory=list)
        learned_at: datetime = field(default_factory=datetime.now)
        updated_at: datetime = field(default_factory=datetime.now)
        frequency: int = 1
        metadata: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class KnowledgeBaseDocument:  # type: ignore[no-redef]
        """Stub: Represents a document in the knowledge base."""
        id: str
        title: str
        content: str
        document_type: str = "general"
        source: Optional[str] = None
        tags: List[str] = field(default_factory=list)
        created_at: datetime = field(default_factory=datetime.now)
        updated_at: datetime = field(default_factory=datetime.now)
        metadata: Dict[str, Any] = field(default_factory=dict)

__all__ = [
    "QuestionEffectiveness",
    "UserBehaviorPattern",
    "KnowledgeBaseDocument",
]
