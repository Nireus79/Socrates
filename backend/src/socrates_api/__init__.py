"""Socrates API package.

This package contains the FastAPI application, database models, and routes
for the Socrates platform backend.
"""

from .database import (
    Database,
    DatabaseConfig,
    get_async_session,
    get_database,
    get_sync_session,
    init_database,
)
from .models import (
    APIKey,
    APIToken,
    Base,
    CategoryScore,
    CategorizedSpec,
    ChatMessage,
    ChatSession,
    ConversationHistory,
    KnowledgeDocument,
    LLMProviderConfig,
    LLMUsage,
    MaturityHistory,
    PendingQuestion,
    PhaseMaturitScore,
    Project,
    ProjectConstraint,
    ProjectNote,
    ProjectRequirement,
    ProjectTechStack,
    RefreshToken,
    TeamMember,
    User,
)

__version__ = "1.3.3"

__all__ = [
    # Database
    "DatabaseConfig",
    "Database",
    "init_database",
    "get_database",
    "get_sync_session",
    "get_async_session",
    "Base",
    # Models
    "User",
    "Project",
    "ProjectRequirement",
    "ProjectTechStack",
    "ProjectConstraint",
    "ConversationHistory",
    "TeamMember",
    "PhaseMaturitScore",
    "CategoryScore",
    "CategorizedSpec",
    "MaturityHistory",
    "PendingQuestion",
    "ProjectNote",
    "KnowledgeDocument",
    "LLMProviderConfig",
    "APIKey",
    "LLMUsage",
    "RefreshToken",
    "APIToken",
    "ChatSession",
    "ChatMessage",
]
