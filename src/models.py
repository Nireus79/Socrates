#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Data Models
==================================

Complete data model definitions for the Socratic RAG Enhanced system.
Defines all entities, relationships, and data structures used throughout the system.

This module establishes the core data foundation that all other components depend on.
"""

import datetime
import json
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# Import from core system
from .core import (
    SocraticException, ValidationError, DateTimeHelper,
    ValidationHelper, get_logger
)

# Get logger for this module
logger = get_logger('models')


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class UserRole(Enum):
    """User roles in the system"""
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    TESTER = "tester"
    BUSINESS_ANALYST = "business_analyst"
    DEVOPS = "devops"
    VIEWER = "viewer"


class UserStatus(Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class ProjectPhase(Enum):
    """Project development phases"""
    PLANNING = "planning"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectStatus(Enum):
    """Project status"""
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TaskStatus(Enum):
    """Task completion status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModuleType(Enum):
    """Types of project modules"""
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATABASE = "database"
    API = "api"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    INTEGRATION = "integration"


class TechnicalRole(Enum):
    """Technical roles for Socratic questioning"""
    PROJECT_MANAGER = "project_manager"
    TECHNICAL_LEAD = "technical_lead"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    QA_TESTER = "qa_tester"
    BUSINESS_ANALYST = "business_analyst"
    DEVOPS_ENGINEER = "devops_engineer"


class FileType(Enum):
    """Generated file types"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    YAML = "yaml"
    JSON = "json"
    MARKDOWN = "markdown"
    DOCKERFILE = "dockerfile"
    CONFIG = "config"
    TEST = "test"
    DOCUMENTATION = "documentation"


class TestType(Enum):
    """Types of tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    END_TO_END = "end_to_end"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ACCEPTANCE = "acceptance"


class ConversationStatus(Enum):
    """Status of Socratic conversations"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CONFLICTED = "conflicted"
    ARCHIVED = "archived"


class ConflictType(Enum):
    """Types of specification conflicts"""
    TECHNICAL = "technical"
    BUSINESS = "business"
    RESOURCE = "resource"
    TIMELINE = "timeline"
    STAKEHOLDER = "stakeholder"


class CodeQualityLevel(Enum):
    """Code quality assessment levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Priority(Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModuleStatus(Enum):
    """Module status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    ON_HOLD = "on_hold"


class FileStatus(Enum):
    """Generated file status"""
    GENERATING = "generating"
    GENERATED = "generated"
    TESTED = "tested"
    DEPLOYED = "deployed"
    ERROR = "error"
    OUTDATED = "outdated"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


# ============================================================================
# BASE MODELS
# ============================================================================

@dataclass
class BaseModel:
    """Base class for all data models"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    updated_at: datetime.datetime = field(default_factory=DateTimeHelper.now)

    def update_timestamp(self) -> None:
        """Update the last modified timestamp"""
        self.updated_at = DateTimeHelper.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert model to JSON string"""

        def json_serializer(obj):
            if isinstance(obj, datetime.datetime):
                return DateTimeHelper.to_iso_string(obj)
            elif isinstance(obj, Enum):
                return obj.value
            return str(obj)

        return json.dumps(self.to_dict(), default=json_serializer, indent=2)


# ============================================================================
# USER MANAGEMENT MODELS
# ============================================================================

@dataclass
class User(BaseModel):
    """User account model"""

    username: str = ""
    email: str = ""
    password_hash: str = ""
    first_name: str = ""
    last_name: str = ""
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.PENDING

    # Profile information
    avatar_url: Optional[str] = None
    bio: str = ""
    skills: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)

    # Authentication
    last_login: Optional[datetime.datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime.datetime] = None
    api_key: Optional[str] = None

    # Statistics
    projects_created: int = 0
    sessions_completed: int = 0
    code_generated_lines: int = 0

    def __post_init__(self):
        """Validate user data after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate user data"""
        if not self.username or len(self.username.strip()) < 3:
            raise ValidationError("Username must be at least 3 characters long")

        if not ValidationHelper.validate_email(self.email):
            raise ValidationError("Invalid email address")

        if not self.password_hash and self.status == UserStatus.ACTIVE:
            raise ValidationError("Active users must have a password")

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked"""
        return (self.locked_until is not None and
                self.locked_until > DateTimeHelper.now())


@dataclass
class Collaborator(BaseModel):
    """Project collaborator model"""

    username: str = ""
    role: UserRole = UserRole.DEVELOPER
    permissions: List[str] = field(default_factory=list)
    joined_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    is_active: bool = True

    def __post_init__(self):
        """Validate collaborator data after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate collaborator data"""
        if not self.username or len(self.username.strip()) < 3:
            raise ValidationError("Username must be at least 3 characters long")


@dataclass
class UserSession(BaseModel):
    """User session tracking"""

    user_id: str = ""
    session_token: str = ""
    ip_address: str = ""
    user_agent: str = ""
    expires_at: datetime.datetime = field(default_factory=lambda:
    DateTimeHelper.now() + datetime.timedelta(hours=1))
    is_active: bool = True
    last_activity: datetime.datetime = field(default_factory=DateTimeHelper.now)

    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return DateTimeHelper.now() > self.expires_at


# ============================================================================
# PROJECT HIERARCHY MODELS
# ============================================================================

@dataclass
class Project(BaseModel):
    """Main project entity"""

    name: str = ""
    description: str = ""
    owner_id: str = ""
    status: ProjectStatus = ProjectStatus.DRAFT
    phase: ProjectPhase = ProjectPhase.PLANNING

    # Technical specifications
    technology_stack: Dict[str, str] = field(default_factory=dict)
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)

    # Timeline and resources
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None
    estimated_hours: Optional[int] = None
    budget: Optional[float] = None

    # Team and collaboration
    team_members: List[str] = field(default_factory=list)  # User IDs
    stakeholders: List[str] = field(default_factory=list)

    # Progress tracking
    progress_percentage: float = 0.0
    completed_modules: int = 0
    total_modules: int = 0

    # Generated content
    generated_codebase_id: Optional[str] = None
    repository_url: Optional[str] = None
    deployment_url: Optional[str] = None

    # Metadata
    tags: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM

    def __post_init__(self):
        """Validate project data after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate project data"""
        if not ValidationHelper.validate_project_name(self.name):
            raise ValidationError("Invalid project name")

        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date")

        if self.progress_percentage < 0 or self.progress_percentage > 100:
            raise ValidationError("Progress percentage must be between 0 and 100")

    @property
    def is_active(self) -> bool:
        """Check if project is active"""
        return self.status == ProjectStatus.ACTIVE

    @property
    def duration_days(self) -> Optional[int]:
        """Get project duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None


@dataclass
class Module(BaseModel):
    """Project module/component"""

    project_id: str = ""
    name: str = ""
    description: str = ""
    module_type: ModuleType = ModuleType.BACKEND

    # Hierarchy
    parent_module_id: Optional[str] = None
    order: int = 0

    # Technical specifications
    dependencies: List[str] = field(default_factory=list)  # Other module IDs
    technologies: List[str] = field(default_factory=list)
    apis_provided: List[str] = field(default_factory=list)
    apis_consumed: List[str] = field(default_factory=list)

    # Progress tracking
    status: TaskStatus = TaskStatus.PENDING
    progress_percentage: float = 0.0
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None

    # Assignment
    assigned_to: Optional[str] = None  # User ID
    reviewer: Optional[str] = None  # User ID

    # Generated content
    generated_files: List[str] = field(default_factory=list)  # File IDs

    def __post_init__(self):
        """Validate module data after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate module data"""
        if not self.name or len(self.name.strip()) < 2:
            raise ValidationError("Module name must be at least 2 characters long")

        if self.progress_percentage < 0 or self.progress_percentage > 100:
            raise ValidationError("Progress percentage must be between 0 and 100")


@dataclass
class Task(BaseModel):
    """Individual task within a module"""

    module_id: str = ""
    project_id: str = ""
    title: str = ""
    description: str = ""

    # Task properties
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: str = ""  # development, testing, review, etc.

    # Assignment and timing
    assigned_to: Optional[str] = None  # User ID
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    due_date: Optional[datetime.datetime] = None
    completed_date: Optional[datetime.datetime] = None

    # Task relationships
    depends_on: List[str] = field(default_factory=list)  # Other task IDs
    blocks: List[str] = field(default_factory=list)  # Other task IDs

    # Progress tracking
    progress_percentage: float = 0.0
    notes: str = ""

    # Generated content
    related_files: List[str] = field(default_factory=list)  # Generated file IDs

    def __post_init__(self):
        """Validate task data after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate task data"""
        if not self.title or len(self.title.strip()) < 3:
            raise ValidationError("Task title must be at least 3 characters long")

        if self.progress_percentage < 0 or self.progress_percentage > 100:
            raise ValidationError("Progress percentage must be between 0 and 100")

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        return (self.due_date is not None and
                self.status != TaskStatus.COMPLETED and
                DateTimeHelper.now() > self.due_date)


@dataclass
class ProjectContext(BaseModel):
    """Project context information"""

    project_id: str = ""
    summary: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate context data"""
        if not self.project_id:
            raise ValidationError("Project ID is required for context")


@dataclass
class ModuleContext(BaseModel):
    """Module context information"""

    module_id: str = ""
    project_id: str = ""
    summary: Dict[str, Any] = field(default_factory=dict)
    dependencies_analysis: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate context data"""
        if not self.module_id:
            raise ValidationError("Module ID is required for context")


@dataclass
class TaskContext(BaseModel):
    """Task context information"""

    task_id: str = ""
    project_id: str = ""
    module_id: str = ""
    summary: Dict[str, Any] = field(default_factory=dict)
    dependencies_analysis: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    estimated_effort: Optional[int] = None
    actual_effort: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate context data"""
        if not self.task_id:
            raise ValidationError("Task ID is required for context")


@dataclass
class KnowledgeEntry(BaseModel):
    """Knowledge base entry for document processing"""

    project_id: str = ""
    document_id: str = ""
    title: str = ""
    content: str = ""
    document_type: str = ""  # pdf, docx, txt, markdown, etc.
    source_file: str = ""

    # Content analysis
    summary: str = ""
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)

    # Processing metadata
    chunk_index: int = 0
    total_chunks: int = 1
    confidence_score: float = 0.0
    processing_status: str = "processed"  # pending, processing, processed, failed

    # Vector embeddings
    embedding: Optional[List[float]] = None
    embedding_model: str = ""

    # Relationships
    related_entries: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Usage tracking
    access_count: int = 0
    last_accessed: Optional[datetime.datetime] = None

    def __post_init__(self):
        """Validate knowledge entry data"""
        if not self.title and not self.content:
            raise ValidationError("Knowledge entry must have either title or content")


# ============================================================================
# SOCRATIC CONVERSATION MODELS
# ============================================================================

@dataclass
class SocraticSession(BaseModel):
    """Socratic questioning session"""

    project_id: str = ""
    user_id: str = ""
    current_role: TechnicalRole = TechnicalRole.PROJECT_MANAGER
    status: ConversationStatus = ConversationStatus.ACTIVE

    # Session configuration
    roles_to_cover: List[TechnicalRole] = field(default_factory=list)
    completed_roles: List[TechnicalRole] = field(default_factory=list)

    # Progress tracking
    total_questions: int = 0
    questions_answered: int = 0
    insights_generated: int = 0
    conflicts_detected: int = 0

    # Session metadata
    session_notes: str = ""
    quality_score: float = 0.0
    completion_percentage: float = 0.0

    def __post_init__(self):
        """Initialize default roles if not provided"""
        if not self.roles_to_cover:
            self.roles_to_cover = list(TechnicalRole)

    @property
    def remaining_roles(self) -> List[TechnicalRole]:
        """Get roles that haven't been covered yet"""
        return [role for role in self.roles_to_cover if role not in self.completed_roles]

    @property
    def is_complete(self) -> bool:
        """Check if session is complete"""
        return len(self.remaining_roles) == 0


@dataclass
class Question(BaseModel):
    """Individual Socratic question"""

    session_id: str = ""
    role: TechnicalRole = TechnicalRole.PROJECT_MANAGER
    question_text: str = ""
    context: str = ""

    # Question properties
    is_follow_up: bool = False
    parent_question_id: Optional[str] = None
    importance_score: float = 0.5

    # Response tracking
    is_answered: bool = False
    answer_text: str = ""
    answer_quality_score: float = 0.0

    # Analysis results
    generated_insights: List[str] = field(default_factory=list)
    detected_conflicts: List[str] = field(default_factory=list)
    recommended_follow_ups: List[str] = field(default_factory=list)


@dataclass
class ConversationMessage(BaseModel):
    """Individual conversation message"""

    project_id: str = ""
    timestamp: datetime.datetime = field(default_factory=DateTimeHelper.now)
    message_type: str = "user"  # user, agent, system
    content: str = ""
    phase: str = "discovery"
    role: Optional[str] = None
    author: Optional[str] = None
    question_number: Optional[int] = None
    insights_extracted: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate message data"""
        if not self.content.strip():
            raise ValidationError("Message content cannot be empty")


@dataclass
class Conflict(BaseModel):
    """Detected specification conflict"""

    project_id: str = ""
    session_id: str = ""
    conflict_type: ConflictType = ConflictType.TECHNICAL

    # Conflict details
    description: str = ""
    severity: str = "medium"  # low, medium, high, critical

    # Conflicting elements
    first_requirement: str = ""
    second_requirement: str = ""
    conflicting_roles: List[TechnicalRole] = field(default_factory=list)

    # Resolution
    is_resolved: bool = False
    resolution_strategy: str = ""
    resolution_notes: str = ""
    resolved_by: Optional[str] = None  # User ID
    resolved_at: Optional[datetime.datetime] = None

    # Impact analysis
    affected_modules: List[str] = field(default_factory=list)
    estimated_impact_hours: Optional[int] = None


# ============================================================================
# TECHNICAL SPECIFICATION MODELS
# ============================================================================

@dataclass
class TechnicalSpec(BaseModel):
    """Complete technical specification for a project"""

    project_id: str = ""
    version: str = "1.0.0"

    # Architecture specification
    architecture_type: str = ""  # MVC, microservices, layered, etc.
    technology_stack: Dict[str, str] = field(default_factory=dict)

    # Functional requirements
    functional_requirements: List[str] = field(default_factory=list)
    non_functional_requirements: List[str] = field(default_factory=list)

    # System design
    system_components: List[str] = field(default_factory=list)
    data_models: List[str] = field(default_factory=list)
    api_specifications: List[str] = field(default_factory=list)

    # Quality requirements
    performance_requirements: Dict[str, Any] = field(default_factory=dict)
    security_requirements: List[str] = field(default_factory=list)
    scalability_requirements: Dict[str, Any] = field(default_factory=dict)

    # Deployment and operations
    deployment_strategy: str = ""
    infrastructure_requirements: Dict[str, Any] = field(default_factory=dict)
    monitoring_requirements: List[str] = field(default_factory=list)

    # Testing strategy
    testing_strategy: Dict[str, Any] = field(default_factory=dict)
    acceptance_criteria: List[str] = field(default_factory=list)

    # Documentation requirements
    documentation_requirements: List[str] = field(default_factory=list)

    # Approval and validation
    is_approved: bool = False
    approved_by: Optional[str] = None  # User ID
    approved_at: Optional[datetime.datetime] = None
    approval_notes: str = ""


# ============================================================================
# CODE GENERATION MODELS
# ============================================================================

@dataclass
class GeneratedCodebase(BaseModel):
    """Complete generated codebase"""

    project_id: str = ""
    spec_id: str = ""
    version: str = "1.0.0"

    # Architecture information
    architecture_type: str = ""
    technology_stack: Dict[str, str] = field(default_factory=dict)

    # File structure
    file_structure: Dict[str, Any] = field(default_factory=dict)
    generated_files: List[str] = field(default_factory=list)  # GeneratedFile IDs

    # Quality metrics
    total_lines_of_code: int = 0
    total_files: int = 0
    code_quality_score: float = 0.0
    test_coverage: float = 0.0

    # Performance metrics
    generation_time_seconds: float = 0.0
    compilation_successful: bool = False
    tests_passing: bool = False

    # Security analysis
    security_scan_results: Dict[str, Any] = field(default_factory=dict)
    security_issues_count: int = 0
    critical_issues_count: int = 0

    # Deployment information
    deployment_config: Dict[str, Any] = field(default_factory=dict)
    deployment_status: str = "not_deployed"  # not_deployed, staging, production

    # Validation results
    validation_results: List[str] = field(default_factory=list)  # TestResult IDs
    error_count: int = 0
    warning_count: int = 0


@dataclass
class GeneratedFile(BaseModel):
    """Individual generated file"""

    codebase_id: str = ""
    project_id: str = ""

    # File information
    file_path: str = ""
    file_type: FileType = FileType.PYTHON
    file_purpose: str = ""  # model, controller, view, test, config, etc.

    # Content
    content: str = ""
    dependencies: List[str] = field(default_factory=list)
    documentation: str = ""

    # Generation metadata
    generated_by_agent: str = ""
    version: str = "1.0.0"
    size_bytes: int = 0
    complexity_score: float = 0.0
    test_coverage: float = 0.0


@dataclass
class TestResult(BaseModel):
    """Test execution result"""

    codebase_id: str = ""
    project_id: str = ""

    # Test information
    test_type: TestType = TestType.UNIT
    test_suite: str = ""
    files_tested: List[str] = field(default_factory=list)

    # Execution results
    passed: bool = False
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0

    # Coverage information
    coverage_percentage: float = 0.0
    failure_details: List[Dict] = field(default_factory=list)
    stack_traces: List[str] = field(default_factory=list)

    # Performance metrics
    memory_usage_mb: float = 0.0
    cpu_usage_percentage: float = 0.0

    # Test environment
    test_environment: Dict[str, str] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate test success rate"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100


# ============================================================================
# ANALYTICS AND REPORTING MODELS
# ============================================================================

@dataclass
class ProjectMetrics(BaseModel):
    """Project analytics and metrics"""

    project_id: str = ""

    # Development metrics
    total_development_hours: float = 0.0
    code_generation_time: float = 0.0
    testing_time: float = 0.0
    review_time: float = 0.0

    # Quality metrics
    average_code_quality: float = 0.0
    test_coverage: float = 0.0
    bug_count: int = 0
    security_issues: int = 0

    # Productivity metrics
    lines_of_code_generated: int = 0
    files_generated: int = 0
    tests_generated: int = 0
    documentation_pages: int = 0

    # Collaboration metrics
    team_members_active: int = 0
    sessions_completed: int = 0
    conflicts_resolved: int = 0
    insights_generated: int = 0

    # Timeline metrics
    planned_duration_days: Optional[int] = None
    actual_duration_days: Optional[int] = None
    delays_count: int = 0

    # Success metrics
    client_satisfaction: float = 0.0
    deployment_success: bool = False
    post_deployment_issues: int = 0


@dataclass
class UserActivity(BaseModel):
    """User activity tracking"""

    user_id: str = ""

    # Activity metrics
    sessions_started: int = 0
    sessions_completed: int = 0
    questions_answered: int = 0
    projects_created: int = 0

    # Time tracking
    total_active_time_hours: float = 0.0
    last_activity: datetime.datetime = field(default_factory=DateTimeHelper.now)

    # Productivity metrics
    code_lines_generated: int = 0
    tests_created: int = 0
    bugs_found: int = 0
    insights_provided: int = 0

    # Collaboration metrics
    conflicts_mediated: int = 0
    reviews_completed: int = 0
    mentoring_sessions: int = 0


# ============================================================================
# MODEL COLLECTIONS AND UTILITIES
# ============================================================================

class ModelRegistry:
    """Registry for all model types"""

    MODELS = {
        'user': User,
        'user_session': UserSession,
        'collaborator': Collaborator,
        'project': Project,
        'module': Module,
        'task': Task,
        'project_context': ProjectContext,
        'module_context': ModuleContext,
        'socratic_session': SocraticSession,
        'question': Question,
        'conversation_message': ConversationMessage,
        'conflict': Conflict,
        'technical_spec': TechnicalSpec,
        'generated_codebase': GeneratedCodebase,
        'generated_file': GeneratedFile,
        'test_result': TestResult,
        'project_metrics': ProjectMetrics,
        'user_activity': UserActivity,
    }

    @classmethod
    def get_model_class(cls, model_name: str) -> type:
        """Get model class by name"""
        return cls.MODELS.get(model_name)

    @classmethod
    def get_all_models(cls) -> Dict[str, type]:
        """Get all registered models"""
        return cls.MODELS.copy()

    @classmethod
    def create_instance(cls, model_name: str, **kwargs) -> BaseModel:
        """Create model instance by name"""
        model_class = cls.get_model_class(model_name)
        if not model_class:
            raise ValidationError(f"Unknown model type: {model_name}")
        return model_class(**kwargs)


class ModelValidator:
    """Advanced model validation utilities"""

    @staticmethod
    def validate_project_data(project_data: Dict[str, Any]) -> List[str]:
        """Validate project data dictionary"""
        issues = []

        # Required fields
        required_fields = ['name', 'owner_id']
        for field in required_fields:
            if field not in project_data or not project_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        # Name validation
        if 'name' in project_data:
            name = project_data['name']
            if not ValidationHelper.validate_project_name(name):
                issues.append(f"Invalid project name: '{name}'")

        # Technology stack validation
        if 'technology_stack' in project_data:
            tech_stack = project_data['technology_stack']
            if not isinstance(tech_stack, dict):
                issues.append("Technology stack must be a dictionary")

        # Status validation
        if 'status' in project_data:
            status = project_data['status']
            valid_statuses = [s.value for s in ProjectStatus]
            if status not in valid_statuses:
                issues.append(f"Invalid status: '{status}'. Must be one of: {valid_statuses}")

        # Phase validation
        if 'phase' in project_data:
            phase = project_data['phase']
            valid_phases = [p.value for p in ProjectPhase]
            if phase not in valid_phases:
                issues.append(f"Invalid phase: '{phase}'. Must be one of: {valid_phases}")

        return issues

    @staticmethod
    def validate_module_data(module_data: Dict[str, Any]) -> List[str]:
        """Validate module data dictionary"""
        issues = []

        # Required fields
        required_fields = ['name', 'project_id']
        for field in required_fields:
            if field not in module_data or not module_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        # Module type validation
        if 'module_type' in module_data:
            module_type = module_data['module_type']
            valid_types = [t.value for t in ModuleType]
            if module_type not in valid_types:
                issues.append(f"Invalid module type: '{module_type}'. Must be one of: {valid_types}")

        return issues

    @staticmethod
    def validate_user_data(user_data: Dict[str, Any]) -> List[str]:
        """Validate user data dictionary"""
        issues = []

        # Required fields
        required_fields = ['username', 'email']
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        # Email validation
        if 'email' in user_data:
            email = user_data['email']
            if not ValidationHelper.validate_email(email):
                issues.append(f"Invalid email format: '{email}'")

        # Username validation
        if 'username' in user_data:
            username = user_data['username']
            if not ValidationHelper.validate_username(username):
                issues.append(f"Invalid username format: '{username}'")

        # Role validation
        if 'role' in user_data:
            role = user_data['role']
            valid_roles = [r.value for r in UserRole]
            if role not in valid_roles:
                issues.append(f"Invalid role: '{role}'. Must be one of: {valid_roles}")

        return issues

    @staticmethod
    def validate_generated_file_data(file_data: Dict[str, Any]) -> List[str]:
        """Validate generated file data dictionary"""
        issues = []

        # Required fields
        required_fields = ['file_path', 'content', 'file_type']
        for field in required_fields:
            if field not in file_data or not file_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        # File type validation
        if 'file_type' in file_data:
            file_type = file_data['file_type']
            valid_types = [t.value for t in FileType]
            if file_type not in valid_types:
                issues.append(f"Invalid file type: '{file_type}'. Must be one of: {valid_types}")

        # File path validation
        if 'file_path' in file_data:
            file_path = file_data['file_path']
            # Basic path validation
            if '..' in file_path or file_path.startswith('/'):
                issues.append(f"Invalid file path: '{file_path}' (security concern)")

        return issues

    @classmethod
    def validate_model_by_type(cls, model_type: str, data: Dict[str, Any]) -> List[str]:
        """Validate data based on model type"""
        validation_methods = {
            'project': cls.validate_project_data,
            'module': cls.validate_module_data,
            'user': cls.validate_user_data,
            'generated_file': cls.validate_generated_file_data,
        }

        validator = validation_methods.get(model_type)
        if validator:
            return validator(data)
        else:
            return [f"No validator available for model type: '{model_type}'"]


def validate_model_data(model: BaseModel) -> List[str]:
    """Validate model data and return list of issues"""
    issues = []

    try:
        if hasattr(model, 'validate'):
            model.validate()
    except ValidationError as e:
        issues.append(str(e))
    except Exception as e:
        issues.append(f"Validation error: {str(e)}")

    return issues


def serialize_model(model: BaseModel) -> str:
    """Serialize model to JSON string"""
    try:
        return model.to_json()
    except Exception as e:
        logger.error(f"Failed to serialize model {type(model).__name__}: {e}")
        raise ValidationError(f"Serialization failed: {e}")


def deserialize_model(model_name: str, json_data: str) -> BaseModel:
    """Deserialize JSON string to model instance"""
    try:
        model_class = ModelRegistry.get_model_class(model_name)
        if not model_class:
            raise ValidationError(f"Unknown model type: {model_name}")

        data = json.loads(json_data)

        # Convert datetime strings back to datetime objects
        for key, value in data.items():
            if key.endswith('_at') or key.endswith('_date'):
                if isinstance(value, str):
                    try:
                        data[key] = DateTimeHelper.from_iso_string(value)
                    except (ValueError, AttributeError):
                        pass

        return model_class(**data)

    except Exception as e:
        logger.error(f"Failed to deserialize model {model_name}: {e}")
        raise ValidationError(f"Deserialization failed: {e}")


# Legacy aliases for backwards compatibility
TechnicalSpecification = TechnicalSpec

# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Enums
    'UserRole', 'UserStatus', 'ProjectPhase', 'ProjectStatus', 'TaskStatus',
    'TaskPriority', 'ModuleType', 'TechnicalRole', 'FileType', 'TestType',
    'ConversationStatus', 'ConflictType', 'CodeQualityLevel', 'ModuleStatus',
    'Priority', 'RiskLevel', 'FileStatus', 'TestStatus',

    # Base models
    'BaseModel',

    # User models
    'User', 'UserSession', 'Collaborator',

    # Project hierarchy models
    'Project', 'Module', 'Task', 'ProjectContext', 'ModuleContext', 'TaskContext',

    # Socratic conversation models
    'SocraticSession', 'Question', 'Conflict', 'ConversationMessage',

    # Technical specification models
    'TechnicalSpec', 'TechnicalSpecification',

    # Code generation models
    'GeneratedCodebase', 'GeneratedFile', 'TestResult',

    # Analytics models
    'ProjectMetrics', 'UserActivity',

    # Utilities
    'ModelRegistry', 'ModelValidator', 'validate_model_data', 'serialize_model', 'deserialize_model'
]

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Log successful module initialization
logger.info("Data models module initialized successfully")

if __name__ == "__main__":
    # Test model creation and validation
    logger.info("Testing data models...")

    # Test user model
    try:
        user = User(
            username="test_user",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role=UserRole.DEVELOPER
        )
        logger.info(f"Created user: {user.full_name}")

        # Test project model
        project = Project(
            name="Test Project",
            description="A test project for validation",
            owner_id=user.id,
            technology_stack={"backend": "Python", "frontend": "React"},
            requirements=["Feature A", "Feature B"]
        )
        logger.info(f"Created project: {project.name}")

        # Test serialization
        json_data = serialize_model(project)
        logger.info("Model serialization successful")

        # Test deserialization
        restored_project = deserialize_model('project', json_data)
        logger.info("Model deserialization successful")

        logger.info("All model tests passed!")

    except Exception as e:
        logger.error(f"Model test failed: {e}")
        raise
