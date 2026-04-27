"""
Data models for Socrates AI
"""

try:
    from socratic_system.conflict import ConflictInfo
except ImportError:
    ConflictInfo = None

try:
    from socratic_system.knowledge import KnowledgeEntry
except ImportError:
    KnowledgeEntry = None

try:
    from socratic_system.learning import (
        KnowledgeBaseDocument,
        QuestionEffectiveness,
        UserBehaviorPattern,
    )
except ImportError:
    KnowledgeBaseDocument = None
    QuestionEffectiveness = None
    UserBehaviorPattern = None

try:
    from socratic_system.maturity import CategoryScore, MaturityEvent, PhaseMaturity
except ImportError:
    CategoryScore = None
    MaturityEvent = None
    PhaseMaturity = None

try:
    from socratic_system.workflow import (
        WorkflowApprovalRequest,
        WorkflowDefinition,
        WorkflowExecutionState,
    )
except ImportError:
    WorkflowApprovalRequest = None
    WorkflowDefinition = None
    WorkflowExecutionState = None

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

# Build __all__ dynamically, excluding None values (failed imports)
__all__ = [
    "User",
    "ProjectContext",
    "TokenUsage",
    "ProjectNote",
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

# Add optional items that were successfully imported
if ConflictInfo is not None:
    __all__.append("ConflictInfo")
if KnowledgeEntry is not None:
    __all__.append("KnowledgeEntry")
if CategoryScore is not None:
    __all__.extend(["CategoryScore", "PhaseMaturity", "MaturityEvent"])
if QuestionEffectiveness is not None:
    __all__.extend(["QuestionEffectiveness", "UserBehaviorPattern", "KnowledgeBaseDocument"])
if WorkflowApprovalRequest is not None:
    __all__.extend(["WorkflowApprovalRequest", "WorkflowDefinition", "WorkflowExecutionState"])
