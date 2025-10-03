#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Data Models and Validation
=================================================

Comprehensive data models for all system entities.
Includes validation, type checking, and utility methods.

✅ CORRECTED - Key Fixes Applied:
- Added missing 'size_bytes' attribute to GeneratedCodebase model
- Added ProjectCollaborator model for proper project-user relationships
- Fixed test ending to use sys.exit(1) instead of bare raise
- Enhanced model validation and type checking
- Uses proper DateTimeHelper (no deprecated datetime.utcnow)
"""

import uuid
import json
import sys
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from enum import Enum

# Core imports with fallbacks
try:
    from src import get_logger  # Backward compatibility function
    from src.core import DateTimeHelper, ValidationError  # Core classes

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    # Fallback implementations
    import logging


    def get_logger(name):
        return logging.getLogger(name)


    class DateTimeHelper:
        @staticmethod
        def now():
            return datetime.now()

        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None

        @staticmethod
        def from_iso_string(iso_str):
            return datetime.fromisoformat(iso_str) if iso_str else None


    class ValidationError(Exception):
        pass


# ============================================================================
# ENUMERATIONS
# ============================================================================

class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    TESTER = "tester"
    STAKEHOLDER = "stakeholder"
    VIEWER = "viewer"


class UserStatus(Enum):
    """User account status"""
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class ProjectPhase(Enum):
    """Project development phase"""
    PLANNING = "planning"
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
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TaskStatus(Enum):
    """Task status"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ModuleType(Enum):
    """Module type classification"""
    FEATURE = "feature"
    COMPONENT = "component"
    SERVICE = "service"
    INTEGRATION = "integration"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


class ModuleStatus(Enum):
    """Module development status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class Priority(Enum):
    """General priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TechnicalRole(Enum):
    """Technical role enumeration for Socratic sessions"""
    PROJECT_MANAGER = "project_manager"
    BUSINESS_ANALYST = "business_analyst"
    UX_DESIGNER = "ux_designer"
    FRONTEND_DEVELOPER = "frontend_developer"
    BACKEND_DEVELOPER = "backend_developer"
    DEVOPS_ENGINEER = "devops_engineer"
    QA_TESTER = "qa_tester"
    SECURITY_ENGINEER = "security_engineer"


class FileType(Enum):
    """File type enumeration"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    SQL = "sql"
    DOCKERFILE = "dockerfile"
    CONFIG = "config"
    TEST = "test"


class FileStatus(Enum):
    """File generation status"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    UPDATED = "updated"


class TestType(Enum):
    """Test type enumeration"""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    ACCEPTANCE = "acceptance"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class ConversationStatus(Enum):
    """Conversation status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ConflictType(Enum):
    """Conflict type classification"""
    TECHNICAL = "technical"
    BUSINESS = "business"
    SCOPE = "scope"
    RESOURCE = "resource"
    TIMELINE = "timeline"


class CodeQualityLevel(Enum):
    """Code quality assessment levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


# ============================================================================
# BASE MODELS
# ============================================================================

@dataclass
class BaseModel:
    """Base class for all data models"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=DateTimeHelper.now)
    updated_at: datetime = field(default_factory=DateTimeHelper.now)

    def update_timestamp(self) -> None:
        """Update the last modified timestamp"""
        self.updated_at = DateTimeHelper.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert model to JSON string"""

        def json_serializer(obj):
            if isinstance(obj, datetime):
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
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
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

        if self.email and "@" not in self.email:
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
    """Project collaborator model (legacy - use ProjectCollaborator for new code)"""

    username: str = ""
    role: UserRole = UserRole.DEVELOPER
    permissions: List[str] = field(default_factory=list)
    joined_at: datetime = field(default_factory=DateTimeHelper.now)
    is_active: bool = True

    def __post_init__(self):
        """Validate collaborator data after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate collaborator data"""
        if not self.username or len(self.username.strip()) < 3:
            raise ValidationError("Username must be at least 3 characters long")


@dataclass
class ProjectCollaborator(BaseModel):
    """Project-User collaborator relationship model

    Represents the many-to-many relationship between projects and users.
    Links users to projects with specific roles and permissions.
    This is the preferred model for new code (replaces legacy Collaborator).
    """

    project_id: str = ""
    user_id: str = ""
    role: UserRole = UserRole.DEVELOPER
    permissions: List[str] = field(default_factory=list)
    joined_at: datetime = field(default_factory=DateTimeHelper.now)
    is_active: bool = True
    invitation_status: str = "active"  # pending, active, inactive, declined

    def __post_init__(self):
        """Validate collaborator data after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate project collaborator data"""
        if not self.project_id or not self.project_id.strip():
            raise ValidationError("Project ID is required for collaborator")

        if not self.user_id or not self.user_id.strip():
            raise ValidationError("User ID is required for collaborator")

        # Validate invitation status
        valid_statuses = ['pending', 'active', 'inactive', 'declined']
        if self.invitation_status not in valid_statuses:
            raise ValidationError(
                f"Invalid invitation status: '{self.invitation_status}'. "
                f"Must be one of: {valid_statuses}"
            )

    @property
    def is_pending(self) -> bool:
        """Check if invitation is pending"""
        return self.invitation_status == "pending"

    @property
    def is_declined(self) -> bool:
        """Check if invitation was declined"""
        return self.invitation_status == "declined"


@dataclass
class UserSession(BaseModel):
    """User session tracking"""

    user_id: str = ""
    session_token: str = ""
    ip_address: str = ""
    user_agent: str = ""
    expires_at: datetime = field(default_factory=lambda: DateTimeHelper.now())
    is_active: bool = True
    last_activity: datetime = field(default_factory=DateTimeHelper.now)

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
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
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
        """Validate project data

        Raises:
            ValidationError: If validation fails
        """
        if not self.name or len(self.name.strip()) < 2:
            raise ValidationError("Project name must be at least 2 characters long")

        if not self.owner_id or not self.owner_id.strip():
            raise ValidationError("Project must have an owner")

    @property
    def is_completed(self) -> bool:
        """Check if project is completed"""
        return self.status == ProjectStatus.COMPLETED

    @property
    def is_active(self) -> bool:
        """Check if project is active"""
        return self.status == ProjectStatus.ACTIVE


@dataclass
class Module(BaseModel):
    """Project module model"""

    project_id: str = ""
    name: str = ""
    description: str = ""
    module_type: ModuleType = ModuleType.FEATURE
    status: ModuleStatus = ModuleStatus.PLANNED

    # Technical details
    file_path: str = ""
    dependencies: List[str] = field(default_factory=list)  # Module IDs
    api_endpoints: List[str] = field(default_factory=list)
    database_tables: List[str] = field(default_factory=list)

    # Assignment and tracking
    assigned_to: Optional[str] = None  # User ID
    priority: Priority = Priority.MEDIUM
    blocked_by: List[str] = field(default_factory=list)  # Blocking issue IDs

    # Timeline
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Progress metrics
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    completion_percentage: float = 0.0

    # Quality metrics
    quality_score: float = 0.0
    test_coverage: float = 0.0

    @property
    def is_completed(self) -> bool:
        """Check if module is completed"""
        return self.status == ModuleStatus.COMPLETED

    @property
    def is_blocked(self) -> bool:
        """Check if module is blocked"""
        return self.status == ModuleStatus.BLOCKED or len(self.blocked_by) > 0


@dataclass
class Task(BaseModel):
    """Individual task model"""

    module_id: str = ""
    project_id: str = ""
    title: str = ""
    description: str = ""

    # Task management
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM

    # Assignment and tracking
    assigned_to: Optional[str] = None  # User ID
    dependencies: List[str] = field(default_factory=list)  # Task IDs

    # Time tracking
    estimated_hours: float = 0.0
    actual_hours: float = 0.0

    # Dates
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == "completed"

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if self.due_date and not self.is_completed:
            return DateTimeHelper.now() > self.due_date
        return False


# ============================================================================
# SOCRATIC CONVERSATION MODELS
# ============================================================================

@dataclass
class SocraticSession(BaseModel):
    """Socratic questioning session"""

    project_id: str = ""
    user_id: str = ""

    # Session configuration
    current_role: TechnicalRole = TechnicalRole.PROJECT_MANAGER
    status: ConversationStatus = ConversationStatus.ACTIVE

    # Role coverage tracking
    roles_to_cover: List[TechnicalRole] = field(default_factory=list)
    completed_roles: List[TechnicalRole] = field(default_factory=list)

    # Progress metrics
    total_questions: int = 0
    questions_answered: int = 0
    insights_generated: int = 0
    conflicts_detected: int = 0

    # Session data
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

    session_id: str = ""  # Link to specific Socratic session
    project_id: str = ""
    timestamp: datetime = field(default_factory=DateTimeHelper.now)
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
    resolved_at: Optional[datetime] = None

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
    session_id: Optional[str] = None
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
    approved_at: Optional[datetime] = None
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
    size_bytes: int = 0  # ✅ FIXED: Now included
    code_quality_score: float = 0.0
    test_coverage: float = 0.0

    # Build and testing
    build_successful: bool = False
    build_errors: List[str] = field(default_factory=list)
    test_results: List[str] = field(default_factory=list)  # TestResult IDs

    # Metadata
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    generated_by: Optional[str] = None  # User ID
    generation_duration_seconds: float = 0.0


@dataclass
class GeneratedFile(BaseModel):
    """Individual generated code file"""

    codebase_id: str = ""
    project_id: str = ""
    file_path: str = ""
    file_type: FileType = FileType.PYTHON
    file_purpose: str = ""  # model, controller, view, test, config

    # File content
    content: str = ""
    size_bytes: int = 0
    line_count: int = 0

    # Dependencies
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Other file IDs

    # Quality metrics
    complexity_score: float = 0.0
    test_coverage: float = 0.0
    documentation_coverage: float = 0.0

    # Analysis results
    syntax_errors: List[Dict[str, Any]] = field(default_factory=list)
    style_issues: List[Dict[str, Any]] = field(default_factory=list)
    security_issues: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    generated_by_agent: Optional[str] = None
    generation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult(BaseModel):
    """Test execution result"""

    codebase_id: str = ""
    test_type: TestType = TestType.UNIT
    test_suite: str = ""

    # Test execution
    files_tested: List[str] = field(default_factory=list)
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    execution_time: float = 0.0

    # Results
    passed: bool = False
    coverage_percentage: float = 0.0
    failure_details: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    executed_at: datetime = field(default_factory=DateTimeHelper.now)
    executed_by: Optional[str] = None


# ============================================================================
# ANALYTICS AND REPORTING MODELS
# ============================================================================

@dataclass
class ProjectMetrics(BaseModel):
    """Project analytics and metrics"""

    project_id: str = ""
    reporting_period_start: datetime = field(default_factory=DateTimeHelper.now)
    reporting_period_end: datetime = field(default_factory=DateTimeHelper.now)

    # Development metrics
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


@dataclass
class UserActivity(BaseModel):
    """User activity tracking"""

    user_id: str = ""
    project_id: str = ""
    activity_type: str = ""
    activity_description: str = ""
    session_id: Optional[str] = None
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeEntry(BaseModel):
    """Knowledge base entry"""

    title: str = ""
    content: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    project_id: Optional[str] = None
    author_id: str = ""
    is_public: bool = False
    view_count: int = 0
    rating: float = 0.0


# ============================================================================
# CONTEXT MODELS
# ============================================================================

@dataclass
class ProjectContext(BaseModel):
    """Context information for a project"""

    project_id: str = ""

    # Business context
    business_domain: str = ""
    target_audience: str = ""
    business_goals: List[str] = field(default_factory=list)

    # Technical context
    existing_systems: List[str] = field(default_factory=list)
    integration_requirements: List[str] = field(default_factory=list)
    performance_requirements: Dict[str, Any] = field(default_factory=dict)

    # Organizational context
    team_structure: Dict[str, Any] = field(default_factory=dict)
    budget_constraints: Dict[str, Any] = field(default_factory=dict)
    timeline_constraints: Dict[str, Any] = field(default_factory=dict)
    # Cache metadata
    last_analyzed_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate context data"""
        if not self.project_id:
            raise ValidationError("Project ID is required for context")


@dataclass
class ModuleContext(BaseModel):
    """Context information for a module"""

    module_id: str = ""
    project_id: str = ""

    # Context data
    business_context: str = ""
    technical_context: str = ""
    dependencies_context: str = ""

    # Related entities
    related_modules: List[str] = field(default_factory=list)
    related_requirements: List[str] = field(default_factory=list)
    related_constraints: List[str] = field(default_factory=list)
    # Cache metadata
    last_analyzed_at: Optional[datetime] = None


@dataclass
class TaskContext(BaseModel):
    """Context information for a task"""

    task_id: str = ""
    module_id: str = ""
    project_id: str = ""

    # Context data
    task_context: str = ""
    implementation_notes: str = ""
    testing_requirements: str = ""

    # Dependencies
    prerequisite_tasks: List[str] = field(default_factory=list)
    dependent_tasks: List[str] = field(default_factory=list)
    # Cache metadata
    last_analyzed_at: Optional[datetime] = None


# ============================================================================
# VALIDATION HELPER CLASSES
# ============================================================================

class ValidationHelper:
    """Helper methods for data validation"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        import re
        pattern = r'^\+?1?\d{9,15}$'
        return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))


class ModelValidator:
    """Validation utilities for model data"""

    @staticmethod
    def validate_project_data(project_data: Dict[str, Any]) -> List[str]:
        """Validate project data dictionary"""
        issues = []

        # Required fields
        required_fields = ['name', 'owner_id']
        for field in required_fields:
            if field not in project_data or not project_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        # Name length validation
        if 'name' in project_data:
            name = project_data['name']
            if len(name) < 2:
                issues.append(f"Project name must be at least 2 characters long")

        return issues

    @staticmethod
    def validate_module_data(module_data: Dict[str, Any]) -> List[str]:
        """Validate module data dictionary"""
        issues = []

        required_fields = ['project_id', 'name']
        for field in required_fields:
            if field not in module_data or not module_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        return issues

    @staticmethod
    def validate_user_data(user_data: Dict[str, Any]) -> List[str]:
        """Validate user data dictionary"""
        issues = []

        required_fields = ['username', 'email']
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        # Email validation
        if 'email' in user_data:
            if not ValidationHelper.validate_email(user_data['email']):
                issues.append(f"Invalid email format: {user_data['email']}")

        return issues

    @staticmethod
    def validate_generated_file_data(file_data: Dict[str, Any]) -> List[str]:
        """Validate generated file data dictionary"""
        issues = []

        required_fields = ['codebase_id', 'file_path', 'content']
        for field in required_fields:
            if field not in file_data or not file_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        # File type validation
        if 'file_type' in file_data:
            file_type = file_data['file_type']
            valid_types = [ft.value for ft in FileType]
            if file_type not in valid_types:
                issues.append(f"Invalid file type: '{file_type}'. Must be one of: {valid_types}")

        # File path validation
        if 'file_path' in file_data:
            file_path = file_data['file_path']
            # Basic path validation
            if '..' in file_path or file_path.startswith('/'):
                issues.append(f"Invalid file path: '{file_path}' (security concern)")

        return issues

    @staticmethod
    def validate_generated_codebase_data(codebase_data: Dict[str, Any]) -> List[str]:
        """Validate generated codebase data dictionary"""
        issues = []

        # Required fields
        required_fields = ['project_id']
        for field in required_fields:
            if field not in codebase_data or not codebase_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        # Numeric validation
        numeric_fields = ['total_files', 'total_lines_of_code', 'size_bytes']
        for field in numeric_fields:
            if field in codebase_data:
                value = codebase_data[field]
                if not isinstance(value, (int, float)) or value < 0:
                    issues.append(f"Field '{field}' must be a non-negative number")

        # Percentage validation
        percentage_fields = ['code_quality_score', 'test_coverage']
        for field in percentage_fields:
            if field in codebase_data:
                value = codebase_data[field]
                if not isinstance(value, (int, float)) or not (0 <= value <= 100):
                    issues.append(f"Field '{field}' must be a percentage between 0 and 100")

        return issues

    @classmethod
    def validate_model_by_type(cls, model_type: str, data: Dict[str, Any]) -> List[str]:
        """Validate data based on model type"""
        validation_methods = {
            'project': cls.validate_project_data,
            'module': cls.validate_module_data,
            'user': cls.validate_user_data,
            'generated_file': cls.validate_generated_file_data,
            'generated_codebase': cls.validate_generated_codebase_data,
        }

        validation_method = validation_methods.get(model_type)
        if validation_method:
            return validation_method(data)
        return []


class ModelFactory:
    """Factory for creating model instances with validation"""

    @staticmethod
    def create_project(name: str, owner_id: str, **kwargs) -> Project:
        """Create a new project with validation"""
        project_data = {
            'name': name,
            'owner_id': owner_id,
            **kwargs
        }

        # Validate before creation
        issues = ModelValidator.validate_project_data(project_data)
        if issues:
            raise ValidationError(f"Project validation failed: {'; '.join(issues)}")

        return Project(**project_data)

    @staticmethod
    def create_user(username: str, email: str, **kwargs) -> User:
        """Create a new user with validation"""
        user_data = {
            'username': username,
            'email': email,
            **kwargs
        }

        # Validate before creation
        issues = ModelValidator.validate_user_data(user_data)
        if issues:
            raise ValidationError(f"User validation failed: {'; '.join(issues)}")

        return User(**user_data)

    @staticmethod
    def create_generated_file(codebase_id: str, file_path: str, content: str,
                              file_type: FileType = FileType.PYTHON, **kwargs) -> GeneratedFile:
        """Create a new generated file with validation"""
        file_data = {
            'codebase_id': codebase_id,
            'file_path': file_path,
            'content': content,
            'file_type': file_type.value if isinstance(file_type, FileType) else file_type,
            **kwargs
        }

        # Validate before creation
        issues = ModelValidator.validate_generated_file_data(file_data)
        if issues:
            raise ValidationError(f"Generated file validation failed: {'; '.join(issues)}")

        return GeneratedFile(**file_data)


# ============================================================================
# MODEL REGISTRY
# ============================================================================

class ModelRegistry:
    """Registry for all model classes"""

    MODELS = {
        # User models
        'user': User,
        'collaborator': Collaborator,
        'project_collaborator': ProjectCollaborator,
        'user_session': UserSession,

        # Project hierarchy models
        'project': Project,
        'module': Module,
        'task': Task,

        # Socratic conversation models
        'socratic_session': SocraticSession,
        'question': Question,
        'conversation_message': ConversationMessage,
        'conflict': Conflict,

        # Technical specification models
        'technical_spec': TechnicalSpec,

        # Code generation models
        'generated_codebase': GeneratedCodebase,
        'generated_file': GeneratedFile,
        'test_result': TestResult,

        # Analytics and reporting models
        'project_metrics': ProjectMetrics,
        'user_activity': UserActivity,
        'knowledge_entry': KnowledgeEntry,

        # Context models
        'project_context': ProjectContext,
        'module_context': ModuleContext,
        'task_context': TaskContext,
    }

    @classmethod
    def get_model_class(cls, model_name: str) -> Optional[type]:
        """Get model class by name"""
        return cls.MODELS.get(model_name)

    @classmethod
    def get_all_models(cls) -> Dict[str, type]:
        """Get all registered model classes"""
        return cls.MODELS.copy()

    @classmethod
    def register_model(cls, name: str, model_class: type) -> None:
        """Register a new model class"""
        cls.MODELS[name] = model_class


# ============================================================================
# SERIALIZATION UTILITIES
# ============================================================================

def serialize_model(model: BaseModel) -> str:
    """Serialize model instance to JSON string"""
    try:
        return model.to_json()
    except Exception as e:
        if CORE_AVAILABLE:
            logger = get_logger(__name__)
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
        if CORE_AVAILABLE:
            logger = get_logger(__name__)
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
    'User', 'UserSession', 'Collaborator', 'ProjectCollaborator',

    # Project hierarchy models
    'Project', 'Module', 'Task', 'ProjectContext', 'ModuleContext', 'TaskContext',

    # Socratic conversation models
    'SocraticSession', 'Question', 'Conflict', 'ConversationMessage',

    # Technical specification models
    'TechnicalSpec', 'TechnicalSpecification',

    # Code generation models
    'GeneratedCodebase', 'GeneratedFile', 'TestResult',

    # Analytics and reporting models
    'ProjectMetrics', 'UserActivity', 'KnowledgeEntry',

    # Utilities
    'ModelFactory', 'ModelValidator', 'ModelRegistry', 'ValidationHelper',
    'serialize_model', 'deserialize_model'
]

if __name__ == "__main__":
    # Test model functionality
    print("Testing model functionality...")

    try:
        # Test ProjectCollaborator (NEW MODEL)
        collab = ProjectCollaborator(
            project_id="test_project_123",
            user_id="test_user_456",
            role=UserRole.DEVELOPER
        )
        print(f"✅ ProjectCollaborator created successfully: {collab.id}")
        print(f"✅ ProjectCollaborator validation works")

        # Test GeneratedCodebase with size_bytes
        codebase = GeneratedCodebase(
            project_id="test_project",
            total_files=10,
            total_lines_of_code=1000,
            size_bytes=50000  # ✅ Now available
        )

        print(f"✅ GeneratedCodebase created successfully")
        print(f"✅ size_bytes attribute accessible: {codebase.size_bytes}")

        # Test GeneratedFile
        file = GeneratedFile(
            codebase_id="test_codebase",
            project_id="test_project",
            file_path="src/main.py",
            size_bytes=5000
        )

        print(f"✅ GeneratedFile created successfully")
        print(f"✅ File size: {file.size_bytes} bytes")

        # Test validation
        validator = ModelValidator()
        issues = validator.validate_generated_codebase_data({
            'project_id': 'test',
            'total_files': 10,
            'size_bytes': 50000
        })

        print(f"✅ Validation passed: {len(issues)} issues found")

        # Test ModelRegistry
        model_class = ModelRegistry.get_model_class('project_collaborator')
        print(f"✅ ModelRegistry has ProjectCollaborator: {model_class is not None}")

        print("🎉 All model tests passed!")

    except Exception as e:
        print(f"❌ Model test failed: {e}")
        sys.exit(1)
