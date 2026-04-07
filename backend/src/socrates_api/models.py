"""SQLAlchemy ORM models for Socrates database schema.

This module defines the complete data models for the Socrates platform,
including users, projects, analytics, LLM configs, and related entities.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User account model."""
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    passcode_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    subscription_tier: Mapped[str] = mapped_column(String(50), default="free")
    subscription_status: Mapped[str] = mapped_column(String(50), default="active")
    subscription_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    subscription_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    testing_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    claude_auth_method: Mapped[str] = mapped_column(String(50), default="api_key")

    # Relationships
    projects: Mapped[List["Project"]] = relationship(back_populates="owner")
    team_memberships: Mapped[List["TeamMember"]] = relationship(back_populates="user")
    api_keys: Mapped[List["APIKey"]] = relationship(back_populates="user")
    llm_configs: Mapped[List["LLMProviderConfig"]] = relationship(back_populates="user")
    llm_usage: Mapped[List["LLMUsage"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user")
    api_tokens: Mapped[List["APIToken"]] = relationship(back_populates="user")
    chat_sessions: Mapped[List["ChatSession"]] = relationship(back_populates="user")
    chat_messages: Mapped[List["ChatMessage"]] = relationship(back_populates="user")

    __table_args__ = (
        Index("idx_users_archived", "is_archived"),
        Index("idx_users_subscription_tier", "subscription_tier"),
        Index("idx_users_subscription_status", "subscription_status"),
        Index("idx_users_subscription", "subscription_tier", "subscription_status"),
    )


class Project(Base):
    """Project model for tracking software projects."""
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    owner: Mapped[str] = mapped_column(String(255), ForeignKey("users.username"), nullable=False)
    phase: Mapped[str] = mapped_column(String(50), default="discovery")
    project_type: Mapped[str] = mapped_column(String(100), default="software")
    team_structure: Mapped[str] = mapped_column(String(50), default="individual")
    language_preferences: Mapped[str] = mapped_column(String(100), default="python")
    deployment_target: Mapped[str] = mapped_column(String(100), default="local")
    code_style: Mapped[str] = mapped_column(String(50), default="standard")
    chat_mode: Mapped[str] = mapped_column(String(50), default="socratic")
    goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # JSONB columns for flexible data
    team_members_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default={})
    analytics_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default={})
    llm_configuration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default={})
    phase_maturity_scores: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default={})

    # Array columns
    tech_stack: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    requirements: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    constraints: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])

    # Relationships
    owner_user: Mapped["User"] = relationship(back_populates="projects")
    requirements_list: Mapped[List["ProjectRequirement"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    tech_stack_list: Mapped[List["ProjectTechStack"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    constraints_list: Mapped[List["ProjectConstraint"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    conversation_history: Mapped[List["ConversationHistory"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    team: Mapped[List["TeamMember"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    phase_maturity: Mapped[List["PhaseMaturitScore"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    category_scores: Mapped[List["CategoryScore"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    categorized_specs: Mapped[List["CategorizedSpec"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    maturity_history: Mapped[List["MaturityHistory"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    pending_questions: Mapped[List["PendingQuestion"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    notes: Mapped[List["ProjectNote"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    chat_sessions: Mapped[List["ChatSession"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    knowledge_documents: Mapped[List["KnowledgeDocument"]] = relationship(back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_projects_owner", "owner"),
        Index("idx_projects_phase", "phase"),
        Index("idx_projects_archived", "is_archived"),
        Index("idx_projects_updated_desc", "updated_at"),
        Index("idx_projects_owner_archived", "owner", "is_archived"),
        Index("idx_projects_status", "status"),
    )


class ProjectRequirement(Base):
    """Project requirements (normalized from array)."""
    __tablename__ = "project_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    project: Mapped["Project"] = relationship(back_populates="requirements_list")

    __table_args__ = (
        Index("idx_project_requirements_project", "project_id"),
    )


class ProjectTechStack(Base):
    """Project tech stack (normalized from array)."""
    __tablename__ = "project_tech_stack"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    technology: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    project: Mapped["Project"] = relationship(back_populates="tech_stack_list")

    __table_args__ = (
        Index("idx_project_tech_stack_project", "project_id"),
    )


class ProjectConstraint(Base):
    """Project constraints (normalized from array)."""
    __tablename__ = "project_constraints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    constraint_text: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    project: Mapped["Project"] = relationship(back_populates="constraints_list")

    __table_args__ = (
        Index("idx_project_constraints_project", "project_id"),
    )


class ConversationHistory(Base):
    """Conversation history (separated for lazy loading)."""
    __tablename__ = "conversation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="conversation_history")

    __table_args__ = (
        Index("idx_conversation_project_timestamp", "project_id", "timestamp"),
        Index("idx_conversation_project", "project_id"),
    )


class TeamMember(Base):
    """Team members (normalized from array)."""
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    username: Mapped[str] = mapped_column(String(255), ForeignKey("users.username"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    skills: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    project: Mapped["Project"] = relationship(back_populates="team")
    user: Mapped["User"] = relationship(back_populates="team_memberships")

    __table_args__ = (
        UniqueConstraint("project_id", "username", name="uq_team_members"),
        Index("idx_team_members_project", "project_id"),
        Index("idx_team_members_user", "username"),
    )


class PhaseMaturitScore(Base):
    """Phase maturity scores (normalized from dict)."""
    __tablename__ = "phase_maturity_scores"

    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), primary_key=True)
    phase: Mapped[str] = mapped_column(String(50), primary_key=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="phase_maturity")

    __table_args__ = (
        Index("idx_phase_maturity_project", "project_id"),
    )


class CategoryScore(Base):
    """Category scores by phase (normalized from nested dict)."""
    __tablename__ = "category_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="category_scores")

    __table_args__ = (
        UniqueConstraint("project_id", "phase", "category", name="uq_category_scores"),
        Index("idx_category_scores_project_phase", "project_id", "phase"),
    )


class CategorizedSpec(Base):
    """Categorized specifications."""
    __tablename__ = "categorized_specs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    spec_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    project: Mapped["Project"] = relationship(back_populates="categorized_specs")

    __table_args__ = (
        Index("idx_categorized_specs_project_phase", "project_id", "phase"),
    )


class MaturityHistory(Base):
    """Maturity history tracking."""
    __tablename__ = "maturity_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    old_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    event_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="maturity_history")

    __table_args__ = (
        Index("idx_maturity_history_project", "project_id"),
    )


class PendingQuestion(Base):
    """Pending questions (normalized from array)."""
    __tablename__ = "pending_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    question_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped["Project"] = relationship(back_populates="pending_questions")

    __table_args__ = (
        Index("idx_pending_questions_project", "project_id"),
    )


class ProjectNote(Base):
    """Project notes."""
    __tablename__ = "project_notes"

    note_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    note_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="notes")

    __table_args__ = (
        Index("idx_project_notes_project", "project_id"),
        Index("idx_project_notes_created", "created_at"),
    )


class KnowledgeDocument(Base):
    """Knowledge documents."""
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.username"), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    document_type: Mapped[str] = mapped_column(String(50), default="document")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    project: Mapped[Optional["Project"]] = relationship(back_populates="knowledge_documents")

    __table_args__ = (
        Index("idx_knowledge_documents_project", "project_id"),
        Index("idx_knowledge_documents_type", "document_type"),
    )


class LLMProviderConfig(Base):
    """LLM Provider configurations."""
    __tablename__ = "llm_provider_configs"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.username"), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    config_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="llm_configs")

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_llm_configs"),
        Index("idx_llm_configs_user", "user_id"),
        Index("idx_llm_configs_provider", "provider"),
    )


class APIKey(Base):
    """API keys for external services."""
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.username"), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    encrypted_key: Mapped[str] = mapped_column(String(500), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="api_keys")

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_api_keys"),
        Index("idx_api_keys_user", "user_id"),
        Index("idx_api_keys_provider", "provider"),
        Index("idx_api_keys_user_provider", "user_id", "provider"),
    )


class LLMUsage(Base):
    """LLM usage tracking."""
    __tablename__ = "llm_usage"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.username"), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="llm_usage")

    __table_args__ = (
        Index("idx_llm_usage_user", "user_id"),
        Index("idx_llm_usage_timestamp", "timestamp"),
        Index("idx_llm_usage_user_timestamp", "user_id", "timestamp"),
        Index("idx_llm_usage_provider", "provider"),
    )


class RefreshToken(Base):
    """Refresh tokens for JWT authentication."""
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_tokens_user", "user_id"),
        Index("idx_refresh_tokens_expires", "expires_at"),
        Index("idx_refresh_tokens_revoked", "revoked_at"),
    )


class APIToken(Base):
    """API tokens for programmatic access."""
    __tablename__ = "api_tokens"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(500), nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="api_tokens")

    __table_args__ = (
        Index("idx_api_tokens_user", "user_id"),
        Index("idx_api_tokens_expires", "expires_at"),
        Index("idx_api_tokens_revoked", "revoked_at"),
    )


class ChatSession(Base):
    """Chat sessions (session-based conversations)."""
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(255), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.username"), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    archived: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped["Project"] = relationship(back_populates="chat_sessions")
    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_chat_sessions_project", "project_id"),
        Index("idx_chat_sessions_user", "user_id"),
        Index("idx_chat_sessions_archived", "archived"),
        Index("idx_chat_sessions_created", "created_at"),
    )


class ChatMessage(Base):
    """Chat messages (messages within sessions)."""
    __tablename__ = "chat_messages"

    message_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.username"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
    user: Mapped["User"] = relationship(back_populates="chat_messages")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="check_chat_messages_role"),
        Index("idx_chat_messages_session", "session_id"),
        Index("idx_chat_messages_user", "user_id"),
        Index("idx_chat_messages_created", "created_at"),
    )


__all__ = [
    "Base",
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
