#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Data Models
===================================

Core data models for the Socratic RAG Enhanced system.
Simplified approach with 4 core models: Project, Module, GeneratedFile, TestResult.

All models use dataclasses for simplicity and include proper typing.
"""

import datetime
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from src.core import DateTimeHelper, ValidationHelper


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class ProjectPhase(Enum):
    """Project development phases"""
    DISCOVERY = "discovery"
    ANALYSIS = "analysis"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"


class ProjectStatus(Enum):
    """Project status options"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class ModuleStatus(Enum):
    """Module status options"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class ModuleType(Enum):
    """Module type categories"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
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


class FileType(Enum):
    """Generated file types"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    DOCKERFILE = "dockerfile"
    CONFIG = "config"
    TEST = "test"
    DOCUMENTATION = "documentation"


class FileStatus(Enum):
    """Generated file status"""
    GENERATING = "generating"
    GENERATED = "generated"
    TESTED = "tested"
    FAILED = "failed"
    DEPLOYED = "deployed"


class TestType(Enum):
    """Test types"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    QUALITY = "quality"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class UserRole(Enum):
    """User roles in the system"""
    PROJECT_MANAGER = "project_manager"
    TECHNICAL_LEAD = "technical_lead"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    QA_TESTER = "qa_tester"
    BUSINESS_ANALYST = "business_analyst"
    DEVOPS_ENGINEER = "devops_engineer"


# ============================================================================
# SUPPORTING DATA MODELS
# ============================================================================

@dataclass
class User:
    """System user model"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    passcode_hash: str = ""
    roles: List[UserRole] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)  # Project IDs
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    updated_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    last_login: Optional[datetime.datetime] = None
    is_active: bool = True
    is_archived: bool = False
    archived_at: Optional[datetime.datetime] = None

    def __post_init__(self):
        self.username = ValidationHelper.sanitize_input(self.username)
        if self.email:
            self.email = ValidationHelper.sanitize_input(self.email)
        if self.full_name:
            self.full_name = ValidationHelper.sanitize_input(self.full_name)


@dataclass
class Collaborator:
    """Project collaborator information"""
    username: str
    role: UserRole
    permissions: List[str] = field(default_factory=list)  # Specific permissions
    joined_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    is_active: bool = True


@dataclass
class ConversationMessage:
    """Socratic conversation message"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime.datetime = field(default_factory=DateTimeHelper.now)
    type: str = "user"  # "user" or "assistant"
    content: str = ""
    phase: ProjectPhase = ProjectPhase.DISCOVERY
    role: Optional[UserRole] = None
    author: Optional[str] = None  # Username
    question_number: Optional[int] = None
    insights_extracted: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TechnicalSpecification:
    """Project technical specifications"""
    project_id: str
    database_schema: Dict[str, Any] = field(default_factory=dict)
    api_design: Dict[str, Any] = field(default_factory=dict)
    file_structure: Dict[str, Any] = field(default_factory=dict)
    component_architecture: Dict[str, Any] = field(default_factory=dict)
    implementation_plan: List[Dict[str, Any]] = field(default_factory=list)
    test_requirements: List[str] = field(default_factory=list)
    deployment_config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    security_requirements: List[str] = field(default_factory=list)
    performance_requirements: Dict[str, Any] = field(default_factory=dict)
    architecture_pattern: str = ""  # MVC, microservices, layered, etc.
    code_style_guide: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    updated_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    version: str = "1.0"


# ============================================================================
# CORE DATA MODEL 1: PROJECT
# ============================================================================

@dataclass
class Project:
    """Core project model - basic info + specs + generated code"""

    # Basic Information
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    owner: str = ""
    collaborators: List[Collaborator] = field(default_factory=list)

    # Project Configuration
    phase: ProjectPhase = ProjectPhase.DISCOVERY
    status: ProjectStatus = ProjectStatus.ACTIVE
    priority: Priority = Priority.MEDIUM

    # Specifications
    goals: str = ""
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    tech_stack: List[str] = field(default_factory=list)
    language_preferences: List[str] = field(default_factory=list)
    deployment_target: str = "local"
    architecture_pattern: str = ""

    # Technical Details
    technical_specification: Optional[TechnicalSpecification] = None

    # Conversation & Context
    conversation_history: List[ConversationMessage] = field(default_factory=list)
    context_summary: Dict[str, Any] = field(default_factory=dict)

    # Generated Code
    generated_codebase_id: Optional[str] = None  # Links to generated files
    file_structure: Dict[str, Any] = field(default_factory=dict)

    # Progress & Metrics
    progress_percentage: float = 0.0
    quality_score: float = 0.0
    estimated_hours: int = 0
    actual_hours: int = 0

    # Risk & Issues
    risk_level: RiskLevel = RiskLevel.LOW
    risk_indicators: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)

    # Timestamps
    created_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    updated_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    completed_at: Optional[datetime.datetime] = None
    archived_at: Optional[datetime.datetime] = None

    # Status Flags
    is_archived: bool = False

    def __post_init__(self):
        """Validate and clean project data"""
        self.name = ValidationHelper.sanitize_input(self.name)
        self.description = ValidationHelper.sanitize_input(self.description)

        # Validate project name
        if self.name and not ValidationHelper.validate_project_name(self.name):
            raise ValueError(f"Invalid project name: {self.name}")

    def add_collaborator(self, username: str, role: UserRole, permissions: List[str] = None) -> bool:
        """Add a collaborator to the project"""
        if username == self.owner:
            return False  # Owner is not a collaborator

        # Check if already exists
        if any(c.username == username for c in self.collaborators):
            return False

        collaborator = Collaborator(
            username=username,
            role=role,
            permissions=permissions or []
        )
        self.collaborators.append(collaborator)
        self.updated_at = DateTimeHelper.now()
        return True

    def remove_collaborator(self, username: str) -> bool:
        """Remove a collaborator from the project"""
        initial_count = len(self.collaborators)
        self.collaborators = [c for c in self.collaborators if c.username != username]

        if len(self.collaborators) < initial_count:
            self.updated_at = DateTimeHelper.now()
            return True
        return False

    def get_all_team_members(self) -> List[str]:
        """Get all team members (owner + collaborators)"""
        return [self.owner] + [c.username for c in self.collaborators if c.is_active]

    def update_progress(self, percentage: float) -> None:
        """Update project progress"""
        self.progress_percentage = max(0.0, min(100.0, percentage))
        self.updated_at = DateTimeHelper.now()

        if self.progress_percentage >= 100.0 and self.status == ProjectStatus.ACTIVE:
            self.status = ProjectStatus.COMPLETED
            self.completed_at = DateTimeHelper.now()


# ============================================================================
# CORE DATA MODEL 2: MODULE
# ============================================================================

@dataclass
class Module:
    """Module model - simple task breakdown within projects"""

    # Basic Information
    module_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    name: str = ""
    description: str = ""

    # Module Configuration
    module_type: ModuleType = ModuleType.BACKEND
    phase: ProjectPhase = ProjectPhase.DISCOVERY
    status: ModuleStatus = ModuleStatus.NOT_STARTED
    priority: Priority = Priority.MEDIUM

    # Task Management
    tasks: List[str] = field(default_factory=list)  # Simple task descriptions
    assigned_roles: List[UserRole] = field(default_factory=list)
    assigned_users: List[str] = field(default_factory=list)  # Usernames

    # Dependencies
    dependencies: List[str] = field(default_factory=list)  # Other module IDs
    blocks: List[str] = field(default_factory=list)  # Modules this blocks

    # Generated Files
    generated_files: List[str] = field(default_factory=list)  # File IDs

    # Progress & Metrics
    progress_percentage: float = 0.0
    estimated_hours: int = 0
    actual_hours: int = 0

    # Quality & Risk
    risk_level: RiskLevel = RiskLevel.LOW
    code_quality_score: float = 0.0
    test_coverage: float = 0.0

    # Timestamps
    created_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    updated_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None

    def __post_init__(self):
        """Validate module data"""
        self.name = ValidationHelper.sanitize_input(self.name)
        self.description = ValidationHelper.sanitize_input(self.description)

    def add_task(self, task_description: str) -> None:
        """Add a task to the module"""
        task = ValidationHelper.sanitize_input(task_description)
        if task and task not in self.tasks:
            self.tasks.append(task)
            self.updated_at = DateTimeHelper.now()

    def mark_started(self) -> None:
        """Mark module as started"""
        if self.status == ModuleStatus.NOT_STARTED:
            self.status = ModuleStatus.IN_PROGRESS
            self.started_at = DateTimeHelper.now()
            self.updated_at = DateTimeHelper.now()

    def mark_completed(self) -> None:
        """Mark module as completed"""
        self.status = ModuleStatus.COMPLETED
        self.completed_at = DateTimeHelper.now()
        self.updated_at = DateTimeHelper.now()
        self.progress_percentage = 100.0

    def update_progress(self, percentage: float) -> None:
        """Update module progress"""
        self.progress_percentage = max(0.0, min(100.0, percentage))
        self.updated_at = DateTimeHelper.now()

        # Auto-update status based on progress
        if percentage > 0 and self.status == ModuleStatus.NOT_STARTED:
            self.mark_started()
        elif percentage >= 100.0:
            self.mark_completed()


# ============================================================================
# CORE DATA MODEL 3: GENERATED FILE
# ============================================================================

@dataclass
class GeneratedFile:
    """Generated file model - path + content + status"""

    # Basic Information
    file_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    module_id: Optional[str] = None
    codebase_id: Optional[str] = None

    # File Details
    file_path: str = ""  # Relative path within project
    file_name: str = ""
    file_type: FileType = FileType.PYTHON
    file_purpose: str = ""  # model, controller, view, test, config, etc.

    # Content
    content: str = ""
    content_hash: str = ""  # For change detection
    size_bytes: int = 0

    # Generation Details
    generated_by_agent: str = ""
    generation_prompt: str = ""
    generation_context: Dict[str, Any] = field(default_factory=dict)

    # Dependencies & Relationships
    dependencies: List[str] = field(default_factory=list)  # Other file IDs this depends on
    dependents: List[str] = field(default_factory=list)  # Files that depend on this
    related_files: List[str] = field(default_factory=list)  # Associated files (tests, etc.)

    # Status & Quality
    status: FileStatus = FileStatus.GENERATING
    has_errors: bool = False
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Metrics
    complexity_score: float = 0.0
    maintainability_score: float = 0.0
    test_coverage: float = 0.0
    lines_of_code: int = 0

    # Documentation
    documentation: str = ""
    comments_ratio: float = 0.0

    # Timestamps
    created_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    updated_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    last_generated: datetime.datetime = field(default_factory=DateTimeHelper.now)
    last_tested: Optional[datetime.datetime] = None
    deployed_at: Optional[datetime.datetime] = None

    # Version Control
    version: str = "1.0"
    git_hash: Optional[str] = None

    def __post_init__(self):
        """Validate and process file data"""
        self.file_path = ValidationHelper.sanitize_input(self.file_path)
        self.file_name = ValidationHelper.sanitize_input(self.file_name)

        if self.content:
            self.size_bytes = len(self.content.encode('utf-8'))
            self.lines_of_code = len([line for line in self.content.split('\n') if line.strip()])

            # Generate content hash for change detection
            import hashlib
            self.content_hash = hashlib.sha256(self.content.encode('utf-8')).hexdigest()

    def update_content(self, new_content: str, generated_by: str = "") -> bool:
        """Update file content and related metadata"""
        old_hash = self.content_hash

        self.content = new_content
        self.generated_by_agent = generated_by
        self.last_generated = DateTimeHelper.now()
        self.updated_at = DateTimeHelper.now()
        self.status = FileStatus.GENERATED

        # Update computed fields
        self.__post_init__()

        # Return True if content actually changed
        return self.content_hash != old_hash

    def mark_tested(self, coverage: float = 0.0) -> None:
        """Mark file as tested"""
        self.status = FileStatus.TESTED
        self.test_coverage = max(0.0, min(100.0, coverage))
        self.last_tested = DateTimeHelper.now()
        self.updated_at = DateTimeHelper.now()

    def mark_failed(self, error_messages: List[str]) -> None:
        """Mark file as failed with error messages"""
        self.status = FileStatus.FAILED
        self.has_errors = True
        self.error_messages.extend(error_messages)
        self.updated_at = DateTimeHelper.now()

    def add_dependency(self, file_id: str) -> None:
        """Add a file dependency"""
        if file_id not in self.dependencies:
            self.dependencies.append(file_id)
            self.updated_at = DateTimeHelper.now()

    def get_relative_path(self) -> str:
        """Get the relative file path for IDE integration"""
        return self.file_path.replace('\\', '/').lstrip('/')


# ============================================================================
# CORE DATA MODEL 4: TEST RESULT
# ============================================================================

@dataclass
class TestResult:
    """Test result model - pass/fail + basic metrics"""

    # Basic Information
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    module_id: Optional[str] = None
    codebase_id: Optional[str] = None

    # Test Configuration
    test_type: TestType = TestType.UNIT
    test_suite: str = ""
    test_framework: str = "pytest"  # pytest, jest, cypress, etc.

    # Files Under Test
    files_tested: List[str] = field(default_factory=list)  # File IDs
    test_files: List[str] = field(default_factory=list)  # Test file IDs

    # Test Results
    status: TestStatus = TestStatus.PENDING
    passed: bool = False
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0

    # Coverage Metrics
    coverage_percentage: float = 0.0
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    function_coverage: float = 0.0

    # Performance Metrics
    execution_time_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # Detailed Results
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    failure_details: List[Dict[str, Any]] = field(default_factory=list)
    error_details: List[Dict[str, Any]] = field(default_factory=list)

    # Quality Metrics
    code_quality_score: float = 0.0
    maintainability_score: float = 0.0
    complexity_warnings: List[str] = field(default_factory=list)

    # Security & Performance
    security_issues: List[Dict[str, Any]] = field(default_factory=list)
    performance_issues: List[Dict[str, Any]] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)

    # Environment
    test_environment: Dict[str, Any] = field(default_factory=dict)
    python_version: str = ""
    node_version: str = ""
    browser_info: Dict[str, str] = field(default_factory=dict)

    # Timestamps
    created_at: datetime.datetime = field(default_factory=DateTimeHelper.now)
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None

    # Execution Details
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    command_line: str = ""

    def mark_started(self) -> None:
        """Mark test as started"""
        self.status = TestStatus.RUNNING
        self.started_at = DateTimeHelper.now()

    def mark_completed(self, success: bool, execution_time: float = 0.0) -> None:
        """Mark test as completed"""
        self.status = TestStatus.PASSED if success else TestStatus.FAILED
        self.passed = success
        self.execution_time_seconds = execution_time
        self.completed_at = DateTimeHelper.now()

        # Calculate pass rate
        if self.total_tests > 0:
            self.passed_tests = self.total_tests - self.failed_tests - self.skipped_tests - self.error_tests

    def add_test_case(self, name: str, status: str, duration: float = 0.0,
                      error_message: str = "") -> None:
        """Add a test case result"""
        test_case = {
            'name': name,
            'status': status,
            'duration': duration,
            'error_message': error_message,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }
        self.test_cases.append(test_case)

        # Update counters
        self.total_tests += 1
        if status == 'passed':
            self.passed_tests += 1
        elif status == 'failed':
            self.failed_tests += 1
        elif status == 'skipped':
            self.skipped_tests += 1
        elif status == 'error':
            self.error_tests += 1

    def add_failure(self, test_name: str, message: str, traceback: str = "") -> None:
        """Add a test failure"""
        failure = {
            'test_name': test_name,
            'message': message,
            'traceback': traceback,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }
        self.failure_details.append(failure)

    def get_success_rate(self) -> float:
        """Get test success rate as percentage"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100.0

    def get_summary(self) -> Dict[str, Any]:
        """Get test result summary"""
        return {
            'test_id': self.test_id,
            'test_type': self.test_type.value,
            'status': self.status.value,
            'passed': self.passed,
            'total_tests': self.total_tests,
            'success_rate': self.get_success_rate(),
            'coverage': self.coverage_percentage,
            'execution_time': self.execution_time_seconds,
            'has_failures': len(self.failure_details) > 0,
            'has_security_issues': len(self.security_issues) > 0,
            'completed_at': DateTimeHelper.to_iso_string(self.completed_at) if self.completed_at else None
        }


# ============================================================================
# MODEL UTILITIES
# ============================================================================

class ModelValidator:
    """Utility class for model validation"""

    @staticmethod
    def validate_project(project: Project) -> List[str]:
        """Validate project model and return list of errors"""
        errors = []

        if not project.name:
            errors.append("Project name is required")
        elif not ValidationHelper.validate_project_name(project.name):
            errors.append("Invalid project name format")

        if not project.owner:
            errors.append("Project owner is required")

        if project.progress_percentage < 0 or project.progress_percentage > 100:
            errors.append("Progress percentage must be between 0 and 100")

        return errors

    @staticmethod
    def validate_module(module: Module) -> List[str]:
        """Validate module model and return list of errors"""
        errors = []

        if not module.name:
            errors.append("Module name is required")

        if not module.project_id:
            errors.append("Module must belong to a project")

        if module.progress_percentage < 0 or module.progress_percentage > 100:
            errors.append("Progress percentage must be between 0 and 100")

        return errors

    @staticmethod
    def validate_generated_file(file: GeneratedFile) -> List[str]:
        """Validate generated file model and return list of errors"""
        errors = []

        if not file.file_path:
            errors.append("File path is required")

        if not file.project_id:
            errors.append("File must belong to a project")

        if not file.content and file.status not in [FileStatus.GENERATING]:
            errors.append("File content is required for generated files")

        return errors


# ============================================================================
# MODEL FACTORY
# ============================================================================

class ModelFactory:
    """Factory class for creating model instances"""

    @staticmethod
    def create_project(name: str, owner: str, description: str = "") -> Project:
        """Create a new project instance"""
        project = Project(
            name=name,
            owner=owner,
            description=description
        )
        return project

    @staticmethod
    def create_module(project_id: str, name: str, module_type: ModuleType = ModuleType.BACKEND) -> Module:
        """Create a new module instance"""
        module = Module(
            project_id=project_id,
            name=name,
            module_type=module_type
        )
        return module

    @staticmethod
    def create_generated_file(project_id: str, file_path: str, file_type: FileType) -> GeneratedFile:
        """Create a new generated file instance"""
        file_name = file_path.split('/')[-1] if '/' in file_path else file_path

        generated_file = GeneratedFile(
            project_id=project_id,
            file_path=file_path,
            file_name=file_name,
            file_type=file_type
        )
        return generated_file

    @staticmethod
    def create_test_result(project_id: str, test_type: TestType = TestType.UNIT) -> TestResult:
        """Create a new test result instance"""
        test_result = TestResult(
            project_id=project_id,
            test_type=test_type
        )
        return test_result


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_models():
    """Export all model classes for easy importing"""
    return {
        # Enums
        'ProjectPhase': ProjectPhase,
        'ProjectStatus': ProjectStatus,
        'ModuleStatus': ModuleStatus,
        'ModuleType': ModuleType,
        'Priority': Priority,
        'RiskLevel': RiskLevel,
        'FileType': FileType,
        'FileStatus': FileStatus,
        'TestType': TestType,
        'TestStatus': TestStatus,
        'UserRole': UserRole,

        # Core Models
        'Project': Project,
        'Module': Module,
        'GeneratedFile': GeneratedFile,
        'TestResult': TestResult,

        # Supporting Models
        'User': User,
        'Collaborator': Collaborator,
        'ConversationMessage': ConversationMessage,
        'TechnicalSpecification': TechnicalSpecification,

        # Utilities
        'ModelValidator': ModelValidator,
        'ModelFactory': ModelFactory,
    }


if __name__ == "__main__":
    # Test the models
    project = ModelFactory.create_project("Test Project", "testuser", "A test project")
    module = ModelFactory.create_module(project.project_id, "Backend API", ModuleType.BACKEND)
    file = ModelFactory.create_generated_file(project.project_id, "backend/api.py", FileType.PYTHON)
    test = ModelFactory.create_test_result(project.project_id, TestType.UNIT)

    print("✅ All models created successfully!")
    print(f"Project: {project.name} ({project.project_id})")
    print(f"Module: {module.name} ({module.module_id})")
    print(f"File: {file.file_path} ({file.file_id})")
    print(f"Test: {test.test_type.value} ({test.test_id})")

"""What src/models.py Provides:
📊 4 Core Data Models:

Project - Basic info + specs + generated code

Project details, team collaboration, specifications
Technical specs, conversation history, progress tracking
Generated codebase linking, risk assessment


Module - Simple task breakdown

Module organization within projects
Task management, dependencies, assigned roles
Progress tracking, quality metrics


GeneratedFile - Path + content + status

Individual file tracking with full metadata
Content management, dependency relationships
Quality metrics, testing status, version control


TestResult - Pass/fail + basic metrics

Comprehensive test execution results
Coverage analysis, performance metrics
Security scanning, quality assessment



🔧 Supporting Features:

Complete enum definitions for all status values, types, phases
User and collaboration models for team management
Conversation tracking for Socratic sessions
Technical specifications for detailed project specs
Model validation utilities with error checking
Model factory for easy instance creation
Proper typing throughout with dataclass support

✅ Key Benefits:

Uses DateTimeHelper - No deprecated datetime functions
Validation integration - Uses core ValidationHelper
Thread-safe UUID generation for all IDs
Comprehensive but manageable - Full functionality without over-complexity
Method helpers - Common operations built-in (add_collaborator, update_progress, etc.)

Usage Example:
from src.models import ModelFactory, ProjectPhase, ModuleType, FileType

# Create project
project = ModelFactory.create_project("My App", "john_doe", "A web application")

# Create module  
module = ModelFactory.create_module(project.project_id, "Backend API", ModuleType.BACKEND)

# Create generated file
file = ModelFactory.create_generated_file(project.project_id, "backend/api.py", FileType.PYTHON)
"""
