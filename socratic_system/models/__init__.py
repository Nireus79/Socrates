"""
Data models for Socrates AI
"""

from .conflict import ConflictInfo
from .knowledge import KnowledgeEntry

# Learning models moved to modules/foundation/models/learning.py
try:
    from modules.foundation.models.learning import (
        QuestionEffectiveness,
        UserBehaviorPattern,
        KnowledgeBaseDocument,
    )
except ImportError:
    QuestionEffectiveness = None  # type: ignore
    UserBehaviorPattern = None  # type: ignore
    KnowledgeBaseDocument = None  # type: ignore

from .llm_provider import (
    APIKeyRecord,
    LLMProviderConfig,
    LLMUsageRecord,
    ProviderMetadata,
    get_provider_metadata,
    list_available_providers,
)
from .maturity import CategoryScore, MaturityEvent, PhaseMaturity
from .monitoring import TokenUsage
from .note import ProjectNote
from .project import ProjectContext
from .role import ROLE_FOCUS_AREAS, VALID_ROLES, TeamMemberRole
from .user import User

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
