"""
Application-wide constants for Socrates AI system.

This module defines all magic strings and configuration constants
to avoid duplication and enable easy refactoring.
"""

# Project Status Constants
class ProjectStatus:
    """Project lifecycle status values."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on-hold"
    ARCHIVED = "archived"
    DRAFT = "draft"

    ALL = [ACTIVE, COMPLETED, ON_HOLD, ARCHIVED, DRAFT]


# API Response Constants
class APIResponse:
    """Standard API response statuses."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PENDING = "pending"


# Database Role Constants
class DatabaseRole:
    """Database replication role designations."""
    PRIMARY = "primary"
    REPLICA = "replica"
    STANDBY = "standby"


# Project Phase Constants
class ProjectPhase:
    """Project development phases."""
    DISCOVERY = "discovery"
    PLANNING = "planning"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"

    ALL = [DISCOVERY, PLANNING, DESIGN, DEVELOPMENT, TESTING, DEPLOYMENT, MAINTENANCE]


# User Roles and Permissions
class UserRole:
    """User role designations in the system."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    VIEWER = "viewer"

    ALL = [ADMIN, DEVELOPER, REVIEWER, VIEWER]


# Team Member Roles
class TeamMemberRole:
    """Roles for team members on projects."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    REVIEWER = "reviewer"
    ADVISOR = "advisor"


# Knowledge Base Categories
class KnowledgeCategory:
    """Categories for knowledge base entries."""
    BEST_PRACTICE = "best_practice"
    PITFALL = "pitfall"
    PATTERN = "pattern"
    ANTI_PATTERN = "anti_pattern"
    DOCUMENTATION = "documentation"


# Timeout Constants (in seconds)
class Timeouts:
    """Standard timeout values for various operations."""
    GIT_OPERATION = 30
    API_CALL = 30
    SUBPROCESS_DEFAULT = 60
    SUBPROCESS_LONG = 300
    DATABASE_QUERY = 10
    FILE_OPERATION = 30


# Performance Constants
class Performance:
    """Performance and tuning constants."""
    CONNECTION_POOL_SIZE = 10
    QUERY_CACHE_SIZE = 1000
    EMBEDDING_CACHE_SIZE = 5000
    SLOW_QUERY_THRESHOLD_MS = 100.0
    MAX_RETRIES = 3


# File and Path Constants
class FilePaths:
    """Standard file and directory paths."""
    LEARNING_LOGS = "./learning_logs"
    CACHE_DIR = "./.cache"
    TEMP_DIR = "./.tmp"
    DATABASE_DIR = "./data"


# Error Message Constants
class ErrorMessages:
    """Standard error messages."""
    NO_PROJECT_LOADED = "No project loaded"
    ORCHESTRATOR_NOT_AVAILABLE = "Orchestrator not available"
    INVALID_INPUT = "Invalid input"
    OPERATION_FAILED = "Operation failed"
    UNSUPPORTED_OPERATION = "Unsupported operation"


__all__ = [
    "ProjectStatus",
    "APIResponse",
    "DatabaseRole",
    "ProjectPhase",
    "UserRole",
    "TeamMemberRole",
    "KnowledgeCategory",
    "Timeouts",
    "Performance",
    "FilePaths",
    "ErrorMessages",
]
