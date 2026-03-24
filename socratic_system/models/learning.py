"""
Learning-related data models for user behavior tracking and personalization.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from socratic_core.utils import serialize_datetime, deserialize_datetime


@dataclass
class QuestionEffectiveness:
    """
    Tracks how effective a question is for a specific user.

    Metrics track question performance over time and help recommend
    the most effective questions for future interactions.
    """

    id: str
    user_id: str
    question_template_id: str
    role: str  # PM, BA, UX, etc.
    times_asked: int = 0
    times_answered_well: int = 0
    average_answer_length: int = 0
    average_spec_extraction_count: Decimal = field(default_factory=lambda: Decimal("0.0"))
    effectiveness_score: Decimal = field(default_factory=lambda: Decimal("0.5"))
    last_asked_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert Decimal to float for JSON
        data["average_spec_extraction_count"] = float(self.average_spec_extraction_count)
        data["effectiveness_score"] = float(self.effectiveness_score)
        # Convert datetime to ISO string
        data["last_asked_at"] = serialize_datetime(self.last_asked_at) if self.last_asked_at else None
        data["created_at"] = serialize_datetime(self.created_at)
        data["updated_at"] = serialize_datetime(self.updated_at)
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "QuestionEffectiveness":
        """Create from dictionary (reverse of to_dict)."""
        # Convert float back to Decimal
        data["average_spec_extraction_count"] = Decimal(
            str(data.get("average_spec_extraction_count", 0))
        )
        data["effectiveness_score"] = Decimal(str(data.get("effectiveness_score", 0.5)))

        # Convert ISO strings back to datetime
        if data.get("last_asked_at"):
            data["last_asked_at"] = datetime.fromisoformat(data["last_asked_at"])
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        return QuestionEffectiveness(**data)


@dataclass
class UserBehaviorPattern:
    """
    Stores learned behavior patterns about a user.

    Patterns capture consistent behaviors observed across multiple projects
    (e.g., communication style, detail preferences, learning pace).
    """

    id: str
    user_id: str
    pattern_type: str  # communication_style, detail_level, learning_pace, etc.
    pattern_data: Dict[str, Any] = field(default_factory=dict)
    confidence: Decimal = field(default_factory=lambda: Decimal("0.5"))
    learned_from_projects: List[str] = field(default_factory=list)
    learned_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "pattern_type": self.pattern_type,
            "pattern_data": self.pattern_data,
            "confidence": float(self.confidence),
            "learned_from_projects": self.learned_from_projects,
            "learned_at": self.learned_atserialize_datetime() if isinstance(..., datetime) else ...,
            "updated_at": self.updated_atserialize_datetime() if isinstance(..., datetime) else ...,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "UserBehaviorPattern":
        """Create from dictionary (reverse of to_dict)."""
        # Convert float back to Decimal
        data["confidence"] = Decimal(str(data.get("confidence", 0.5)))

        # Convert ISO strings back to datetime
        if data.get("learned_at"):
            data["learned_at"] = datetime.fromisoformat(data["learned_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        return UserBehaviorPattern(**data)
