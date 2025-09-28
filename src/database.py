#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Data Models and Validation
=================================================

Comprehensive data models for all system entities.
Includes validation, type checking, and utility methods.

✅ CORRECTED - Key Fixes Applied:
- Added missing 'size_bytes' attribute to GeneratedCodebase model
- Enhanced model validation and type checking
- Improved import handling with proper fallbacks
- Added comprehensive model factory and validation utilities
"""

import uuid
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union
from enum import Enum

# Core imports with fallbacks
try:
    from src.core import DateTimeHelper, ValidationError, get_logger

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
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ModuleStatus(Enum):
    """Module development status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ModuleType(Enum):
    """Module type classification"""
    FEATURE = "feature"
    COMPONENT = "component"
    SERVICE = "service"
    INTEGRATION = "integration"
    TESTING = "testing"
    DOCUMENTATION = "documentation"


class Priority(Enum):
    """Priority levels"""
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


class FileType(Enum):
    """Supported file types"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    TEXT = "text"
    BINARY = "binary"


class FileStatus(Enum):
    """File processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TestType(Enum):
    """Test type classification"""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    END_TO_END = "end_to_end"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class UserRole(Enum):
    """User role definitions"""
    ADMIN = "admin"
    MANAGER = "manager"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    VIEWER = "viewer"


class UserStatus(Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class TechnicalRole(Enum):
    """Technical roles for Socratic questioning"""
    BUSINESS_ANALYST = "business_analyst"
    SYSTEM_ARCHITECT = "system_architect"
    UI_UX_DESIGNER = "ui_ux_designer"
    BACKEND_DEVELOPER = "backend_developer"
    FRONTEND_DEVELOPER = "frontend_developer"
    DATABASE_ARCHITECT = "database_architect"
    DEVOPS_ENGINEER = "devops_engineer"
    QA_ENGINEER = "qa_engineer"
    SECURITY_SPECIALIST = "security_specialist"
    PROJECT_MANAGER = "project_manager"


class ConversationStatus(Enum):
    """Socratic conversation status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


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
    questions_answered: int = 0

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_active(self) -> bool:
        """Check if user account is active"""
        return self.status == UserStatus.ACTIVE

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked"""
        if self.locked_until:
            return DateTimeHelper.now() < self.locked_until
        return False


@dataclass
class Collaborator(BaseModel):
    """Project collaborator model"""

    project_id: str = ""
    user_id: str = ""
    username: str = ""
    role: str = "viewer"
    joined_at: datetime = field(default_factory=DateTimeHelper.now)
    is_active: bool = True
    permissions: List[str] = field(default_factory=list)


# ============================================================================
# PROJECT MANAGEMENT MODELS
# ============================================================================

@dataclass
class Project(BaseModel):
    """Main project model"""

    name: str = ""
    description: str = ""
    domain: str = ""

    # Project status and management
    phase: ProjectPhase = ProjectPhase.PLANNING
    status: ProjectStatus = ProjectStatus.ACTIVE
    priority: Priority = Priority.MEDIUM
    risk_level: RiskLevel = RiskLevel.LOW

    # Project details
    target_audience: str = ""
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    business_goals: List[str] = field(default_factory=list)
    technical_requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)

    # Technology stack
    technology_stack: Dict[str, str] = field(default_factory=dict)
    architecture_pattern: str = ""

    # Management
    created_by: str = ""  # User ID
    assigned_to: Optional[str] = None  # User ID
    collaborators: List[str] = field(default_factory=list)  # User IDs

    # Dates
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None

    # Progress tracking
    completion_percentage: float = 0.0
    modules_count: int = 0
    completed_modules: int = 0

    # Quality metrics
    quality_score: float = 0.0
    test_coverage: float = 0.0

    @property
    def is_completed(self) -> bool:
        """Check if project is completed"""
        return self.status == ProjectStatus.COMPLETED

    @property
    def is_overdue(self) -> bool:
        """Check if project is overdue"""
        if self.target_date and not self.is_completed:
            return DateTimeHelper.now() > self.target_date
        return False


@dataclass
class Module(BaseModel):
    """Project module model"""

    project_id: str = ""
    name: str = ""
    description: str = ""

    # Module classification
    module_type: ModuleType = ModuleType.FEATURE
    status: ModuleStatus = ModuleStatus.PLANNED
    priority: Priority = Priority.MEDIUM

    # Dependencies and relationships
    dependencies: List[str] = field(default_factory=list)  # Module IDs
    blocked_by: List[str] = field(default_factory=list)  # Module IDs

    # Requirements and acceptance criteria
    requirements: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)

    # Assignment and tracking
    assigned_to: Optional[str] = None  # User ID
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
    status: str = "todo"  # todo, in_progress, completed, cancelled
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
    current_role: TechnicalRole = TechnicalRole.BUSINESS_ANALYST
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

    @property
    def is_completed(self) -> bool:
        """Check if session is completed"""
        return self.status == ConversationStatus.COMPLETED

    @property
    def remaining_roles(self) -> List[TechnicalRole]:
        """Get remaining roles to cover"""
        return [role for role in self.roles_to_cover if role not in self.completed_roles]


@dataclass
class Question(BaseModel):
    """Individual Socratic question"""

    session_id: str = ""
    project_id: str = ""
    role: TechnicalRole = TechnicalRole.BUSINESS_ANALYST

    # Question content
    question_text: str = ""
    context: str = ""
    answer: str = ""

    # Quality metrics
    confidence_score: float = 0.0
    follow_up_questions: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    conflicts_detected: List[str] = field(default_factory=list)

    # Timing
    answered_at: Optional[datetime] = None

    @property
    def is_answered(self) -> bool:
        """Check if question has been answered"""
        return bool(self.answer and self.answer.strip())


@dataclass
class ConversationMessage(BaseModel):
    """Individual conversation message"""

    session_id: str = ""
    question_id: Optional[str] = None

    # Message content
    role: str = "user"  # user, assistant, system
    content: str = ""

    # Metadata
    token_count: int = 0
    confidence_score: float = 0.0
    context_used: List[str] = field(default_factory=list)


@dataclass
class Conflict(BaseModel):
    """Detected specification conflict"""

    project_id: str = ""
    session_id: Optional[str] = None

    # Conflict details
    conflict_type: str = ""
    severity: str = "medium"  # low, medium, high, critical
    description: str = ""

    # Conflicting elements
    source_element: str = ""
    target_element: str = ""
    conflicting_values: Dict[str, Any] = field(default_factory=dict)

    # Resolution
    resolution_status: str = "pending"  # pending, resolved, ignored
    resolution_notes: str = ""
    resolved_by: Optional[str] = None  # User ID
    resolved_at: Optional[datetime] = None

    @property
    def is_resolved(self) -> bool:
        """Check if conflict is resolved"""
        return self.resolution_status == "resolved"


# ============================================================================
# TECHNICAL SPECIFICATION MODELS
# ============================================================================

@dataclass
class TechnicalSpecification(BaseModel):
    """Technical specification document"""

    project_id: str = ""
    title: str = ""
    description: str = ""

    # Specification content
    functional_requirements: List[str] = field(default_factory=list)
    non_functional_requirements: List[str] = field(default_factory=list)
    technical_constraints: List[str] = field(default_factory=list)
    architecture_decisions: Dict[str, Any] = field(default_factory=dict)

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
    size_bytes: int = 0  # ✅ ADDED: Missing size_bytes attribute
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

    # File content
    content: str = ""
    dependencies: List[str] = field(default_factory=list)
    documentation: str = ""

    # Generation metadata
    generated_by_agent: str = ""
    version: str = "1.0.0"

    # Quality metrics
    size_bytes: int = 0
    complexity_score: float = 0.0
    test_coverage: float = 0.0

    @property
    def size_mb(self) -> float:
        """Get file size in megabytes"""
        return self.size_bytes / (1024 * 1024) if self.size_bytes > 0 else 0.0

    @property
    def line_count(self) -> int:
        """Get number of lines in file"""
        return len(self.content.split('\n')) if self.content else 0


@dataclass
class TestResult(BaseModel):
    """Test execution result"""

    codebase_id: str = ""
    project_id: str = ""

    # Test information
    test_name: str = ""
    test_type: TestType = TestType.UNIT
    status: TestStatus = TestStatus.PENDING

    # Execution details
    passed: bool = False
    execution_time: float = 0.0
    error_message: str = ""
    coverage_percentage: float = 0.0

    @property
    def is_successful(self) -> bool:
        """Check if test passed"""
        return self.status == TestStatus.PASSED and self.passed


# ============================================================================
# ANALYTICS AND METRICS MODELS
# ============================================================================

@dataclass
class ProjectMetrics(BaseModel):
    """Project analytics and metrics"""

    project_id: str = ""

    # Time metrics
    total_development_time: float = 0.0
    estimated_completion_time: float = 0.0
    actual_completion_time: float = 0.0

    # Code metrics
    total_lines_of_code: int = 0
    total_files_generated: int = 0
    code_quality_average: float = 0.0
    test_coverage_average: float = 0.0

    # Productivity metrics
    questions_per_hour: float = 0.0
    insights_per_session: float = 0.0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0

    # Quality metrics
    overall_quality_score: float = 0.0
    user_satisfaction_score: float = 0.0


@dataclass
class UserActivity(BaseModel):
    """User activity tracking"""

    user_id: str = ""

    # Activity metrics
    sessions_started: int = 0
    sessions_completed: int = 0
    questions_answered: int = 0
    projects_created: int = 0

    # Time metrics
    total_active_time: float = 0.0
    average_session_duration: float = 0.0

    # Last activity
    last_login: Optional[datetime] = None
    last_project_id: Optional[str] = None


@dataclass
class KnowledgeEntry(BaseModel):
    """Knowledge base entry for RAG system"""

    # Content identification
    title: str = ""
    content: str = ""
    content_type: str = "text"  # text, code, documentation

    # Categorization
    domain: str = ""
    tags: List[str] = field(default_factory=list)

    # Source information
    source_type: str = ""  # conversation, document, code, external
    source_id: Optional[str] = None
    project_id: Optional[str] = None

    # Vector embeddings and search
    embedding_vector: Optional[List[float]] = None
    search_keywords: List[str] = field(default_factory=list)

    # Quality and relevance
    relevance_score: float = 0.0
    usage_count: int = 0
    last_accessed: Optional[datetime] = None


# ============================================================================
# CONTEXT MODELS
# ============================================================================

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


# ============================================================================
# MODEL FACTORY AND UTILITIES
# ============================================================================

class ModelFactory:
    """Factory for creating model instances"""

    MODELS = {
        'user': User,
        'collaborator': Collaborator,
        'project': Project,
        'module': Module,
        'task': Task,
        'socratic_session': SocraticSession,
        'question': Question,
        'conversation_message': ConversationMessage,
        'conflict': Conflict,
        'technical_spec': TechnicalSpecification,
        'generated_codebase': GeneratedCodebase,
        'generated_file': GeneratedFile,
        'test_result': TestResult,
        'project_metrics': ProjectMetrics,
        'user_activity': UserActivity,
        'knowledge_entry': KnowledgeEntry,
        'module_context': ModuleContext,
        'task_context': TaskContext,
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
        required_fields = ['name', 'created_by']
        for field in required_fields:
            if field not in project_data or not project_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        # Name validation
        if 'name' in project_data:
            name = project_data['name']
            if not name or len(name.strip()) < 2:
                issues.append("Project name must be at least 2 characters long")

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
    def validate_user_data(user_data: Dict[str, Any]) -> List[str]:
        """Validate user data dictionary"""
        issues = []

        # Required fields
        required_fields = ['username', 'email']
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        # Email validation (basic)
        if 'email' in user_data:
            email = user_data['email']
            if email and '@' not in email:
                issues.append("Invalid email format")

        # Username validation
        if 'username' in user_data:
            username = user_data['username']
            if username and len(username.strip()) < 3:
                issues.append("Username must be at least 3 characters long")

        # Role validation
        if 'role' in user_data:
            role = user_data['role']
            valid_roles = [r.value for r in UserRole]
            if role not in valid_roles:
                issues.append(f"Invalid role: '{role}'. Must be one of: {valid_roles}")

        return issues

    @staticmethod
    def validate_generated_codebase_data(codebase_data: Dict[str, Any]) -> List[str]:
        """Validate generated codebase data"""
        issues = []

        # Required fields
        required_fields = ['project_id']
        for field in required_fields:
            if field not in codebase_data or not codebase_data[field]:
                issues.append(f"Required field '{field}' is missing or empty")

        # Numeric validations
        numeric_fields = ['total_files', 'total_lines_of_code', 'size_bytes']
        for field in numeric_fields:
            if field in codebase_data:
                value = codebase_data[field]
                if not isinstance(value, (int, float)) or value < 0:
                    issues.append(f"Field '{field}' must be a non-negative number")

        # Percentage validations
        percentage_fields = ['code_quality_score', 'test_coverage']
        for field in percentage_fields:
            if field in codebase_data:
                value = codebase_data[field]
                if not isinstance(value, (int, float)) or not (0 <= value <= 100):
                    issues.append(f"Field '{field}' must be a percentage between 0 and 100")

        return issues


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Enumerations
    'ProjectPhase', 'ProjectStatus', 'ModuleStatus', 'ModuleType', 'Priority', 'RiskLevel',
    'FileType', 'FileStatus', 'TestType', 'TestStatus', 'UserRole', 'UserStatus',
    'TechnicalRole', 'ConversationStatus',

    # Base models
    'BaseModel',

    # User models
    'User', 'Collaborator',

    # Project models
    'Project', 'Module', 'Task',

    # Socratic models
    'SocraticSession', 'Question', 'ConversationMessage', 'Conflict',

    # Technical models
    'TechnicalSpecification',

    # Code generation models
    'GeneratedCodebase', 'GeneratedFile', 'TestResult',

    # Analytics models
    'ProjectMetrics', 'UserActivity', 'KnowledgeEntry',

    # Context models
    'ModuleContext', 'TaskContext',

    # Utilities
    'ModelFactory', 'ModelValidator'
]

if __name__ == "__main__":
    # Test model functionality
    print("Testing model functionality...")

    try:
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
        print(f"✅ File size: {file.size_bytes} bytes ({file.size_mb:.2f} MB)")

        # Test validation
        validator = ModelValidator()
        issues = validator.validate_generated_codebase_data({
            'project_id': 'test',
            'total_files': 10,
            'size_bytes': 50000
        })

        print(f"✅ Validation passed: {len(issues)} issues found")
        print("🎉 All model tests passed!")

    except Exception as e:
        print(f"❌ Model test failed: {e}")
        import sys

        sys.exit(1)
