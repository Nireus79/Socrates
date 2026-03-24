"""
Data models for Socrates AI

Uses published libraries for core models:
- socrates_maturity: CategoryScore, PhaseMaturity, MaturityEvent
- socratic_learning: KnowledgeBaseDocument, QuestionEffectiveness, UserBehaviorPattern
"""

from .conflict import ConflictInfo
from .knowledge import KnowledgeEntry
from .llm_provider import (
    APIKeyRecord,
    LLMProviderConfig,
    LLMUsageRecord,
    ProviderMetadata,
    get_provider_metadata,
    list_available_providers,
)
from .monitoring import TokenUsage
from .note import ProjectNote
from .project import ProjectContext
from .role import ROLE_FOCUS_AREAS, VALID_ROLES, TeamMemberRole
from .user import User

# Import maturity models from published library
try:
    from socrates_maturity import CategoryScore, MaturityEvent, PhaseMaturity
except ImportError:
    # Fallback if socrates_maturity not installed
    CategoryScore = None  # type: ignore
    MaturityEvent = None  # type: ignore
    PhaseMaturity = None  # type: ignore

# Import learning models from published library
try:
    from socratic_learning import (
        KnowledgeBaseDocument,
        QuestionEffectiveness,
        UserBehaviorPattern,
    )
except ImportError:
    # socratic_learning is optional - provide graceful fallback
    QuestionEffectiveness = None  # type: ignore
    UserBehaviorPattern = None  # type: ignore
    KnowledgeBaseDocument = None  # type: ignore

__all__ = [
    "User",
    "ProjectContext",
    "KnowledgeEntry",
    "TokenUsage",
    "ConflictInfo",
    "ProjectNote",
    "CategoryScore",
    "PhaseMaturity",
    "MaturityEvent",
    # Learning models (re-exported from modules/foundation/models/learning)
    "QuestionEffectiveness",
    "UserBehaviorPattern",
    "KnowledgeBaseDocument",
    "LLMProviderConfig",
    "APIKeyRecord",
    "LLMUsageRecord",
    "ProviderMetadata",
    "get_provider_metadata",
    "list_available_providers",
    "TeamMemberRole",
    "ROLE_FOCUS_AREAS",
    "VALID_ROLES",
]
