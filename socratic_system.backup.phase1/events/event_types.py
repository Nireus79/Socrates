"""
Event type definitions for Socrates system
"""

from enum import Enum


class EventType(Enum):
    """Enumeration of all possible events in the Socrates system"""

    # Agent lifecycle events
    AGENT_START = "agent.start"
    AGENT_COMPLETE = "agent.complete"
    AGENT_ERROR = "agent.error"

    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_LOADED = "project.loaded"
    PROJECT_SAVED = "project.saved"
    PROJECT_UPDATED = "project.updated"
    PROJECT_ARCHIVED = "project.archived"
    PROJECT_RESTORED = "project.restored"
    PROJECT_DELETED = "project.deleted"

    # User events
    USER_CREATED = "user.created"
    USER_AUTHENTICATED = "user.authenticated"
    USER_LOGGED_OUT = "user.logged_out"
    USER_ARCHIVED = "user.archived"

    # Knowledge and learning events
    KNOWLEDGE_LOADED = "knowledge.loaded"
    KNOWLEDGE_SUGGESTION = "knowledge.suggestion"
    DOCUMENT_IMPORTED = "document.imported"
    DOCUMENTS_INDEXED = "documents.indexed"

    # Socratic dialogue events
    QUESTION_GENERATED = "question.generated"
    QUESTIONS_REGENERATED = "questions.regenerated"
    RESPONSE_RECEIVED = "response.received"
    RESPONSE_ANALYZED = "response.analyzed"
    PHASE_ADVANCED = "phase.advanced"
    HINT_PROVIDED = "hint.provided"

    # Code generation events
    CODE_GENERATED = "code.generated"
    CODE_DOCUMENTATION_GENERATED = "code.documentation.generated"
    CODE_ANALYSIS_COMPLETE = "code.analysis.complete"

    # Conflict and analysis events
    CONFLICT_DETECTED = "conflict.detected"
    CONFLICT_RESOLVED = "conflict.resolved"
    CONTEXT_ANALYZED = "context.analyzed"

    # Quality and maturity events
    PHASE_MATURITY_UPDATED = "phase.maturity.updated"
    PHASE_READY_TO_ADVANCE = "phase.ready.to.advance"
    QUALITY_CHECK_PASSED = "quality.check.passed"
    QUALITY_CHECK_WARNING = "quality.check.warning"
    MATURITY_MILESTONE = "maturity.milestone"
    LEARNING_METRICS_UPDATED = "learning.metrics.updated"

    # Workflow optimization events
    WORKFLOW_APPROVAL_REQUESTED = "workflow.approval.requested"
    WORKFLOW_APPROVED = "workflow.approved"
    WORKFLOW_REJECTED = "workflow.rejected"
    WORKFLOW_NODE_ENTERED = "workflow.node.entered"
    WORKFLOW_NODE_COMPLETED = "workflow.node.completed"

    # Note events
    NOTE_ADDED = "note.added"
    NOTE_UPDATED = "note.updated"
    NOTE_DELETED = "note.deleted"

    # System events
    TOKEN_USAGE = "token.usage"
    PROGRESS_UPDATE = "progress.update"
    SYSTEM_INITIALIZED = "system.initialized"
    SYSTEM_SHUTDOWN = "system.shutdown"

    # Logging events
    LOG_DEBUG = "log.debug"
    LOG_INFO = "log.info"
    LOG_WARNING = "log.warning"
    LOG_ERROR = "log.error"

    # Collaboration events
    COLLABORATOR_ADDED = "collaborator.added"
    COLLABORATOR_REMOVED = "collaborator.removed"

    # Custom events
    CUSTOM = "custom"
