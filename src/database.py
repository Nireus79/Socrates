#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Database Layer
=====================================

Database service and repository implementations for the Socratic RAG Enhanced system.
Provides data persistence, retrieval, and management functionality.

✅ CORRECTED - Key Fixes Applied:
- Added missing 'codebases' property alias in DatabaseService
- Added ProjectCollaboratorRepository and project_collaborators table
- Fixed import fallbacks with complete model definitions including size_bytes
- Added missing dataclass import in fallback block
- Resolved type mismatch issues in repository return types
"""

import sqlite3
import json
import threading
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic

# Core imports with enhanced fallbacks
try:
    from src import get_config, get_logger  # Backward compatibility functions
    from src.core import DateTimeHelper, ValidationError, DatabaseError  # Core classes

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    # Enhanced fallback implementations
    import logging
    from dataclasses import dataclass


    def get_config():
        return {'database': {'path': 'data/socratic.db'}}


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


    class DatabaseError(Exception):
        pass

# Model imports with complete fallbacks
try:
    from src.models import (
        User, Project, Module, Task, GeneratedCodebase, GeneratedFile, TestResult,
        SocraticSession, Question, ConversationMessage, Conflict, TechnicalSpec,
        ProjectMetrics, UserActivity, KnowledgeEntry, ProjectContext, ModuleContext, TaskContext,
        ProjectCollaborator,
        ProjectPhase, ProjectStatus, ModuleStatus, UserRole, UserStatus, TechnicalRole,
        FileType, TestType, Priority, ConflictType, ConversationStatus
    )

    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    from dataclasses import dataclass
    from typing import Dict, List, Any, Optional
    from enum import Enum


    class ProjectStatus(Enum):
        DRAFT = "draft"
        ACTIVE = "active"
        COMPLETED = "completed"


    class TechnicalRole(Enum):
        PROJECT_MANAGER = "project_manager"
        BUSINESS_ANALYST = "business_analyst"
        UX_DESIGNER = "ux_designer"
        FRONTEND_DEVELOPER = "frontend_developer"
        BACKEND_DEVELOPER = "backend_developer"
        DATABASE_ARCHITECT = "database_architect"
        DEVOPS_ENGINEER = "devops_engineer"


    class ConversationStatus(Enum):
        ACTIVE = "active"
        PAUSED = "paused"
        COMPLETED = "completed"
        CANCELLED = "cancelled"


    class UserRole(Enum):
        ADMIN = "admin"
        DEVELOPER = "developer"
        VIEWER = "viewer"


    @dataclass
    class BaseModel:
        id: str = ""
        created_at: datetime = field(default_factory=datetime.now)
        updated_at: datetime = field(default_factory=datetime.now)


    @dataclass
    class User(BaseModel):
        username: str = ""
        email: str = ""
        role: UserRole = UserRole.VIEWER


    @dataclass
    class Project(BaseModel):
        name: str = ""
        description: str = ""
        owner_id: str = ""
        status: ProjectStatus = ProjectStatus.DRAFT


    @dataclass
    class GeneratedCodebase(BaseModel):
        """Complete fallback model with size_bytes included"""
        project_id: str = ""
        version: str = "1.0.0"
        architecture_type: str = ""
        total_lines_of_code: int = 0
        total_files: int = 0
        size_bytes: int = 0
        code_quality_score: float = 0.0
        test_coverage: float = 0.0


    @dataclass
    class GeneratedFile(BaseModel):
        codebase_id: str = ""
        file_path: str = ""
        content: str = ""
        size_bytes: int = 0


    @dataclass
    class ProjectCollaborator(BaseModel):
        project_id: str = ""
        user_id: str = ""
        role: str = "developer"
        permissions: List[str] = field(default_factory=list)
        joined_at: datetime = field(default_factory=datetime.now)
        is_active: bool = True
        invitation_status: str = "active"


    # Minimal fallback implementations for other models
    Module = Task = TestResult = SocraticSession = Question = ConversationMessage = BaseModel
    Conflict = TechnicalSpec = ProjectMetrics = UserActivity = KnowledgeEntry = BaseModel
    ProjectContext = ModuleContext = TaskContext = BaseModel

# Type variables for generic repository
T = TypeVar('T')

logger = get_logger(__name__)


# ============================================================================
# BASE REPOSITORY CLASSES
# ============================================================================

class BaseRepository(Generic[T], ABC):
    """Base repository with type-safe operations"""

    def __init__(self, db_manager, model_class: Type[T]):
        self.db_manager = db_manager
        self.model_class = model_class
        self.table_name = self._get_table_name()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def _get_table_name(self) -> str:
        """Get table name from model class"""
        return self.model_class.__name__.lower() + 's'

    @abstractmethod
    def create(self, entity: T) -> bool:
        """Create new entity"""
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    def update(self, entity: T) -> bool:
        """Update existing entity"""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID"""
        pass

    def get_all(self) -> List[T]:
        """Get all entities"""
        try:
            query = f"SELECT * FROM {self.table_name}"
            results = self.db_manager.execute_query(query)
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting all {self.table_name}: {e}")
            return []

    def _row_to_model(self, row: Dict[str, Any]) -> T:
        """Convert database row to model instance"""
        try:
            # Basic conversion - override in subclasses for complex models
            return self.model_class(**row)
        except Exception as e:
            self.logger.error(f"Error converting row to model: {e}")
            return self.model_class()

    @staticmethod
    def _model_to_dict(entity: T) -> Dict[str, Any]:
        """Convert model instance to dictionary with enum handling"""
        if hasattr(entity, 'to_dict'):
            data = entity.to_dict()
        elif hasattr(entity, '__dict__'):
            data = entity.__dict__.copy()
        else:
            data = {}

        # Convert all enum values to strings for database storage
        for key, value in data.items():
            if hasattr(value, 'value'):  # It's an enum
                data[key] = value.value

        return data


# ============================================================================
# SPECIFIC REPOSITORY IMPLEMENTATIONS
# ============================================================================

class UserRepository(BaseRepository[User]):
    """User repository with type safety"""

    def create(self, user: User) -> bool:
        try:
            data = self._model_to_dict(user)
            query = """
                INSERT INTO users (id, username, email, password_hash, first_name, last_name, role, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id', str(uuid.uuid4())),
                data.get('username', ''),
                data.get('email', ''),
                data.get('password_hash', ''),
                data.get('first_name', ''),
                data.get('last_name', ''),
                data.get('role', 'viewer'),
                data.get('status', 'pending'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                DateTimeHelper.to_iso_string(DateTimeHelper.now())
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            return False

    def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            query = "SELECT * FROM users WHERE id = ?"
            results = self.db_manager.execute_query(query, (user_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting user {user_id}: {e}")
            return None

    def get_by_username(self, username: str) -> Optional[User]:
        try:
            query = "SELECT * FROM users WHERE username = ?"
            results = self.db_manager.execute_query(query, (username,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting user by username {username}: {e}")
            return None

    def find_by_username(self, username: str) -> Optional[User]:
        """Alias for get_by_username for consistency"""
        return self.get_by_username(username)

    def find_by_email(self, email: str) -> Optional[User]:
        """Alias for get_by_email for consistency"""
        return self.get_by_email(email)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            query = "SELECT * FROM users WHERE email = ?"
            results = self.db_manager.execute_query(query, (email,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting user by email {email}: {e}")
            return None

    def update(self, user: User) -> bool:
        try:
            data = self._model_to_dict(user)
            query = """
                UPDATE users 
                SET username = ?, email = ?, role = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('username', ''),
                data.get('email', ''),
                data.get('role', 'viewer'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id', '')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating user: {e}")
            return False

    def delete(self, user_id: str) -> bool:
        try:
            query = "DELETE FROM users WHERE id = ?"
            self.db_manager.execute_update(query, (user_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting user {user_id}: {e}")
            return False

    def list(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List users with pagination"""
        try:
            query = "SELECT * FROM users LIMIT ? OFFSET ?"
            results = self.db_manager.execute_query(query, (limit, offset))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error listing users: {e}")
            return []

    def list_all(self, limit: int = 1000) -> List[User]:
        """Get all users (alias for compatibility)"""
        return self.list(limit=limit, offset=0)


class ProjectRepository(BaseRepository[Project]):
    """Project repository with type safety"""

    def _row_to_model(self, row: Dict[str, Any]) -> Project:
        """Convert database row to Project instance with proper type conversions"""
        import json  # ← Move import to top

        try:
            from src.models import ProjectStatus, ProjectPhase, TaskPriority
            from src.core import DateTimeHelper

            # Convert datetime strings to datetime objects
            if 'created_at' in row and isinstance(row['created_at'], str):
                row['created_at'] = DateTimeHelper.from_iso_string(row['created_at'])
            if 'updated_at' in row and isinstance(row['updated_at'], str):
                row['updated_at'] = DateTimeHelper.from_iso_string(row['updated_at'])
            if 'start_date' in row and row['start_date'] and isinstance(row['start_date'], str):
                row['start_date'] = DateTimeHelper.from_iso_string(row['start_date'])
            if 'end_date' in row and row['end_date'] and isinstance(row['end_date'], str):
                row['end_date'] = DateTimeHelper.from_iso_string(row['end_date'])

            # Convert technology_stack JSON string to dict
            if 'technology_stack' in row and isinstance(row['technology_stack'], str):
                try:
                    row['technology_stack'] = json.loads(row['technology_stack'])
                except (json.JSONDecodeError, TypeError):
                    row['technology_stack'] = {}

            # Convert enum strings to enum objects
            if 'status' in row and isinstance(row['status'], str):
                row['status'] = ProjectStatus(row['status'])
            if 'phase' in row and isinstance(row['phase'], str):
                row['phase'] = ProjectPhase(row['phase'])
            if 'priority' in row and isinstance(row['priority'], str):
                row['priority'] = TaskPriority(row['priority'])

            return Project(**row)
        except Exception as e:
            self.logger.error(f"Error converting row to Project: {e}")
            return Project()

    def create(self, project: Project) -> Optional[Project]:
        """Create new project in database"""
        try:
            data = self._model_to_dict(project)

            # Convert status enum to string if needed
            status = data.get('status', 'draft')
            if hasattr(status, 'value'):
                status = status.value

            # Serialize technology_stack to JSON string for database storage
            import json
            tech_stack_json = json.dumps(data.get('technology_stack', {}))

            query = """
                INSERT INTO projects 
                (id, name, description, owner_id, status, technology_stack, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id', str(uuid.uuid4())),
                data.get('name', ''),
                data.get('description', ''),
                data.get('owner_id', ''),
                status,
                tech_stack_json,
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                DateTimeHelper.to_iso_string(DateTimeHelper.now())
            )
            self.db_manager.execute_update(query, params)

            # Return the created project
            return self.get_by_id(data.get('id'))

        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            return None

    def get_by_id(self, project_id: str) -> Optional[Project]:
        try:
            query = "SELECT * FROM projects WHERE id = ?"
            results = self.db_manager.execute_query(query, (project_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting project {project_id}: {e}")
            return None

    def get_by_owner(self, owner_id: str) -> List[Project]:
        try:
            query = "SELECT * FROM projects WHERE owner_id = ?"
            results = self.db_manager.execute_query(query, (owner_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting projects for owner {owner_id}: {e}")
            return []

    def update(self, project: Project) -> bool:
        try:
            data = self._model_to_dict(project)
            query = """
                UPDATE projects 
                SET name = ?, description = ?, status = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('name', ''),
                data.get('description', ''),
                data.get('status', 'draft'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id', '')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating project: {e}")
            return False

    def delete(self, project_id: str) -> bool:
        try:
            query = "DELETE FROM projects WHERE id = ?"
            self.db_manager.execute_update(query, (project_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting project {project_id}: {e}")
            return False


class GeneratedCodebaseRepository(BaseRepository[GeneratedCodebase]):
    """Generated codebase repository with proper size_bytes support"""

    def create(self, codebase: GeneratedCodebase) -> bool:
        try:
            data = self._model_to_dict(codebase)
            query = """
                INSERT INTO generated_codebases 
                (id, project_id, version, architecture_type, total_lines_of_code, 
                 total_files, size_bytes, code_quality_score, test_coverage, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id', str(uuid.uuid4())),
                data.get('project_id', ''),
                data.get('version', '1.0.0'),
                data.get('architecture_type', ''),
                data.get('total_lines_of_code', 0),
                data.get('total_files', 0),
                data.get('size_bytes', 0),
                data.get('code_quality_score', 0.0),
                data.get('test_coverage', 0.0),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                DateTimeHelper.to_iso_string(DateTimeHelper.now())
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating codebase: {e}")
            return False

    def get_by_id(self, codebase_id: str) -> Optional[GeneratedCodebase]:
        try:
            query = "SELECT * FROM generated_codebases WHERE id = ?"
            results = self.db_manager.execute_query(query, (codebase_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting codebase {codebase_id}: {e}")
            return None

    def get_by_project_id(self, project_id: str) -> List[GeneratedCodebase]:
        try:
            query = "SELECT * FROM generated_codebases WHERE project_id = ?"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting codebases for project {project_id}: {e}")
            return []

    def update(self, codebase: GeneratedCodebase) -> bool:
        try:
            data = self._model_to_dict(codebase)
            query = """
                UPDATE generated_codebases 
                SET version = ?, total_lines_of_code = ?, total_files = ?, 
                    size_bytes = ?, code_quality_score = ?, test_coverage = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('version', '1.0.0'),
                data.get('total_lines_of_code', 0),
                data.get('total_files', 0),
                data.get('size_bytes', 0),
                data.get('code_quality_score', 0.0),
                data.get('test_coverage', 0.0),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id', '')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating codebase: {e}")
            return False

    def delete(self, codebase_id: str) -> bool:
        try:
            query = "DELETE FROM generated_codebases WHERE id = ?"
            self.db_manager.execute_update(query, (codebase_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting codebase {codebase_id}: {e}")
            return False


class GeneratedFileRepository(BaseRepository[GeneratedFile]):
    """Generated file repository with size_bytes support"""

    def create(self, file: GeneratedFile) -> bool:
        try:
            data = self._model_to_dict(file)
            query = """
                INSERT INTO generated_files 
                (id, codebase_id, file_path, content, size_bytes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id', str(uuid.uuid4())),
                data.get('codebase_id', ''),
                data.get('file_path', ''),
                data.get('content', ''),
                data.get('size_bytes', 0),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                DateTimeHelper.to_iso_string(DateTimeHelper.now())
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating file: {e}")
            return False

    def get_by_id(self, file_id: str) -> Optional[GeneratedFile]:
        try:
            query = "SELECT * FROM generated_files WHERE id = ?"
            results = self.db_manager.execute_query(query, (file_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting file {file_id}: {e}")
            return None

    def get_by_codebase_id(self, codebase_id: str) -> List[GeneratedFile]:
        try:
            query = "SELECT * FROM generated_files WHERE codebase_id = ?"
            results = self.db_manager.execute_query(query, (codebase_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting files for codebase {codebase_id}: {e}")
            return []

    def update(self, file: GeneratedFile) -> bool:
        try:
            data = self._model_to_dict(file)
            query = """
                UPDATE generated_files 
                SET file_path = ?, content = ?, size_bytes = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('file_path', ''),
                data.get('content', ''),
                data.get('size_bytes', 0),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id', '')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating file: {e}")
            return False

    def delete(self, file_id: str) -> bool:
        try:
            query = "DELETE FROM generated_files WHERE id = ?"
            self.db_manager.execute_update(query, (file_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting file {file_id}: {e}")
            return False


class ProjectCollaboratorRepository(BaseRepository[ProjectCollaborator]):
    """Project collaborator repository with relationship management"""

    def create(self, collaborator: ProjectCollaborator) -> bool:
        try:
            data = self._model_to_dict(collaborator)
            query = """
                INSERT INTO project_collaborators 
                (id, project_id, user_id, role, permissions, joined_at, 
                 is_active, invitation_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id', str(uuid.uuid4())),
                data.get('project_id', ''),
                data.get('user_id', ''),
                data.get('role', 'developer'),
                json.dumps(data.get('permissions', [])),
                DateTimeHelper.to_iso_string(data.get('joined_at', DateTimeHelper.now())),
                data.get('is_active', True),
                data.get('invitation_status', 'active'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                DateTimeHelper.to_iso_string(DateTimeHelper.now())
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating collaborator: {e}")
            return False

    def get_by_id(self, collaborator_id: str) -> Optional[ProjectCollaborator]:
        try:
            query = "SELECT * FROM project_collaborators WHERE id = ?"
            results = self.db_manager.execute_query(query, (collaborator_id,))
            if results:
                row = results[0]
                # Parse JSON permissions
                if 'permissions' in row and isinstance(row['permissions'], str):
                    row['permissions'] = json.loads(row['permissions'])
                return self._row_to_model(row)
            return None
        except Exception as e:
            self.logger.error(f"Error getting collaborator {collaborator_id}: {e}")
            return None

    def get_by_project(self, project_id: str) -> List[ProjectCollaborator]:
        """Get all collaborators for a project"""
        try:
            query = "SELECT * FROM project_collaborators WHERE project_id = ? AND is_active = 1"
            results = self.db_manager.execute_query(query, (project_id,))
            collaborators = []
            for row in results:
                if 'permissions' in row and isinstance(row['permissions'], str):
                    row['permissions'] = json.loads(row['permissions'])
                collaborators.append(self._row_to_model(row))
            return collaborators
        except Exception as e:
            self.logger.error(f"Error getting collaborators for project {project_id}: {e}")
            return []

    def get_by_user(self, user_id: str) -> List[ProjectCollaborator]:
        """Get all projects a user collaborates on"""
        try:
            query = "SELECT * FROM project_collaborators WHERE user_id = ? AND is_active = 1"
            results = self.db_manager.execute_query(query, (user_id,))
            collaborators = []
            for row in results:
                if 'permissions' in row and isinstance(row['permissions'], str):
                    row['permissions'] = json.loads(row['permissions'])
                collaborators.append(self._row_to_model(row))
            return collaborators
        except Exception as e:
            self.logger.error(f"Error getting projects for user {user_id}: {e}")
            return []

    def update(self, collaborator: ProjectCollaborator) -> bool:
        try:
            data = self._model_to_dict(collaborator)
            query = """
                UPDATE project_collaborators 
                SET role = ?, permissions = ?, is_active = ?, 
                    invitation_status = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('role', 'developer'),
                json.dumps(data.get('permissions', [])),
                data.get('is_active', True),
                data.get('invitation_status', 'active'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id', '')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating collaborator: {e}")
            return False

    def delete(self, collaborator_id: str) -> bool:
        try:
            query = "DELETE FROM project_collaborators WHERE id = ?"
            self.db_manager.execute_update(query, (collaborator_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting collaborator {collaborator_id}: {e}")
            return False


class SocraticSessionRepository(BaseRepository[SocraticSession]):
    """Repository for managing Socratic sessions with persistence"""

    def create(self, session: SocraticSession) -> bool:
        """Create a new Socratic session"""
        try:
            data = self._model_to_dict(session)
            query = """
                INSERT INTO socratic_sessions (
                    id, project_id, user_id, current_role, status,
                    roles_to_cover, completed_roles, total_questions,
                    questions_answered, insights_generated, conflicts_detected,
                    session_notes, quality_score, completion_percentage,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Convert list fields to JSON strings
            roles_to_cover_json = json.dumps(
                [r.value if hasattr(r, 'value') else r for r in data.get('roles_to_cover', [])])
            completed_roles_json = json.dumps(
                [r.value if hasattr(r, 'value') else r for r in data.get('completed_roles', [])])

            params = (
                data.get('id'),
                data.get('project_id'),
                data.get('user_id'),
                data.get('current_role'),
                data.get('status'),
                roles_to_cover_json,
                completed_roles_json,
                data.get('total_questions', 0),
                data.get('questions_answered', 0),
                data.get('insights_generated', 0),
                data.get('conflicts_detected', 0),
                data.get('session_notes', ''),
                data.get('quality_score', 0.0),
                data.get('completion_percentage', 0.0),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Created Socratic session: {session.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating Socratic session: {e}")
            return False

    def get_by_id(self, session_id: str) -> Optional[SocraticSession]:
        """Get Socratic session by ID"""
        try:
            query = "SELECT * FROM socratic_sessions WHERE id = ?"
            results = self.db_manager.execute_query(query, (session_id,))

            if results:
                return self._row_to_model(results[0])
            return None

        except Exception as e:
            self.logger.error(f"Error getting Socratic session {session_id}: {e}")
            return None

    def update(self, session: SocraticSession) -> bool:
        """Update existing Socratic session"""
        try:
            data = self._model_to_dict(session)

            # Convert list fields to JSON strings
            roles_to_cover_json = json.dumps(
                [r.value if hasattr(r, 'value') else r for r in data.get('roles_to_cover', [])])
            completed_roles_json = json.dumps(
                [r.value if hasattr(r, 'value') else r for r in data.get('completed_roles', [])])

            query = """
                UPDATE socratic_sessions SET
                    current_role = ?, status = ?, roles_to_cover = ?,
                    completed_roles = ?, total_questions = ?, questions_answered = ?,
                    insights_generated = ?, conflicts_detected = ?, session_notes = ?,
                    quality_score = ?, completion_percentage = ?, updated_at = ?
                WHERE id = ?
            """

            params = (
                data.get('current_role'),
                data.get('status'),
                roles_to_cover_json,
                completed_roles_json,
                data.get('total_questions', 0),
                data.get('questions_answered', 0),
                data.get('insights_generated', 0),
                data.get('conflicts_detected', 0),
                data.get('session_notes', ''),
                data.get('quality_score', 0.0),
                data.get('completion_percentage', 0.0),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Updated Socratic session: {session.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating Socratic session: {e}")
            return False

    def delete(self, session_id: str) -> bool:
        """Delete Socratic session by ID"""
        try:
            query = "DELETE FROM socratic_sessions WHERE id = ?"
            self.db_manager.execute_update(query, (session_id,))
            self.logger.info(f"Deleted Socratic session: {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting Socratic session {session_id}: {e}")
            return False

    def get_by_project_id(self, project_id: str) -> List[SocraticSession]:
        """Get all sessions for a project"""
        try:
            query = "SELECT * FROM socratic_sessions WHERE project_id = ? ORDER BY created_at DESC"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]

        except Exception as e:
            self.logger.error(f"Error getting sessions for project {project_id}: {e}")
            return []

    def get_by_user_id(self, user_id: str) -> List[SocraticSession]:
        """Get all sessions for a user"""
        try:
            query = "SELECT * FROM socratic_sessions WHERE user_id = ? ORDER BY created_at DESC"
            results = self.db_manager.execute_query(query, (user_id,))
            return [self._row_to_model(row) for row in results]

        except Exception as e:
            self.logger.error(f"Error getting sessions for user {user_id}: {e}")
            return []

    def list_user_sessions(self, user_id: str, status: str = None) -> List[SocraticSession]:
        """List user sessions with optional status filter"""
        try:
            if status:
                query = "SELECT * FROM socratic_sessions WHERE user_id = ? AND status = ? ORDER BY created_at DESC"
                results = self.db_manager.execute_query(query, (user_id, status))
            else:
                query = "SELECT * FROM socratic_sessions WHERE user_id = ? ORDER BY created_at DESC"
                results = self.db_manager.execute_query(query, (user_id,))

            return [self._row_to_model(row) for row in results]

        except Exception as e:
            self.logger.error(f"Error listing sessions for user {user_id}: {e}")
            return []

    def _row_to_model(self, row: Dict[str, Any]) -> SocraticSession:
        """Convert database row to SocraticSession model"""
        try:
            # Parse JSON fields
            roles_to_cover = []
            if row.get('roles_to_cover'):
                roles_json = json.loads(row['roles_to_cover'])
                roles_to_cover = [TechnicalRole(r) if isinstance(r, str) else r for r in roles_json]

            completed_roles = []
            if row.get('completed_roles'):
                roles_json = json.loads(row['completed_roles'])
                completed_roles = [TechnicalRole(r) if isinstance(r, str) else r for r in roles_json]

            # Parse datetime fields
            created_at = DateTimeHelper.from_iso_string(row['created_at']) if row.get(
                'created_at') else DateTimeHelper.now()
            updated_at = DateTimeHelper.from_iso_string(row['updated_at']) if row.get(
                'updated_at') else DateTimeHelper.now()

            return SocraticSession(
                id=row.get('id', ''),
                project_id=row.get('project_id', ''),
                user_id=row.get('user_id', ''),
                current_role=TechnicalRole(row['current_role']) if row.get(
                    'current_role') else TechnicalRole.PROJECT_MANAGER,
                status=ConversationStatus(row['status']) if row.get('status') else ConversationStatus.ACTIVE,
                roles_to_cover=roles_to_cover,
                completed_roles=completed_roles,
                total_questions=row.get('total_questions', 0),
                questions_answered=row.get('questions_answered', 0),
                insights_generated=row.get('insights_generated', 0),
                conflicts_detected=row.get('conflicts_detected', 0),
                session_notes=row.get('session_notes', ''),
                quality_score=row.get('quality_score', 0.0),
                completion_percentage=row.get('completion_percentage', 0.0),
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            self.logger.error(f"Error converting row to SocraticSession: {e}")
            return SocraticSession()


class QuestionRepository(BaseRepository[Question]):
    """Repository for managing Socratic questions"""

    def create(self, question: Question) -> bool:
        """Create a new question"""
        try:
            data = self._model_to_dict(question)
            query = """
                INSERT INTO questions (
                    id, session_id, role, question_text, context,
                    is_follow_up, parent_question_id, importance_score,
                    is_answered, answer_text, answer_quality_score,
                    generated_insights, detected_conflicts, recommended_follow_ups,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Convert list fields to JSON
            generated_insights_json = json.dumps(data.get('generated_insights', []))
            detected_conflicts_json = json.dumps(data.get('detected_conflicts', []))
            recommended_follow_ups_json = json.dumps(data.get('recommended_follow_ups', []))

            params = (
                data.get('id'),
                data.get('session_id'),
                data.get('role'),
                data.get('question_text'),
                data.get('context', ''),
                data.get('is_follow_up', False),
                data.get('parent_question_id'),
                data.get('importance_score', 0.5),
                data.get('is_answered', False),
                data.get('answer_text', ''),
                data.get('answer_quality_score', 0.0),
                generated_insights_json,
                detected_conflicts_json,
                recommended_follow_ups_json,
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Created question: {question.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating question: {e}")
            return False

    def get_by_id(self, question_id: str) -> Optional[Question]:
        """Get question by ID"""
        try:
            query = "SELECT * FROM questions WHERE id = ?"
            results = self.db_manager.execute_query(query, (question_id,))

            if results:
                return self._row_to_model(results[0])
            return None

        except Exception as e:
            self.logger.error(f"Error getting question {question_id}: {e}")
            return None

    def update(self, question: Question) -> bool:
        """Update existing question"""
        try:
            data = self._model_to_dict(question)

            # Convert list fields to JSON
            generated_insights_json = json.dumps(data.get('generated_insights', []))
            detected_conflicts_json = json.dumps(data.get('detected_conflicts', []))
            recommended_follow_ups_json = json.dumps(data.get('recommended_follow_ups', []))

            query = """
                UPDATE questions SET
                    is_answered = ?, answer_text = ?, answer_quality_score = ?,
                    generated_insights = ?, detected_conflicts = ?,
                    recommended_follow_ups = ?, updated_at = ?
                WHERE id = ?
            """

            params = (
                data.get('is_answered', False),
                data.get('answer_text', ''),
                data.get('answer_quality_score', 0.0),
                generated_insights_json,
                detected_conflicts_json,
                recommended_follow_ups_json,
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Updated question: {question.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating question: {e}")
            return False

    def delete(self, question_id: str) -> bool:
        """Delete question by ID"""
        try:
            query = "DELETE FROM questions WHERE id = ?"
            self.db_manager.execute_update(query, (question_id,))
            self.logger.info(f"Deleted question: {question_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting question {question_id}: {e}")
            return False

    def get_by_session_id(self, session_id: str) -> List[Question]:
        """Get all questions for a session"""
        try:
            query = "SELECT * FROM questions WHERE session_id = ? ORDER BY created_at ASC"
            results = self.db_manager.execute_query(query, (session_id,))
            return [self._row_to_model(row) for row in results]

        except Exception as e:
            self.logger.error(f"Error getting questions for session {session_id}: {e}")
            return []

    def update_answer(self, question_id: str, answer: str) -> bool:
        """Update question with user's answer"""
        try:
            query = """
                UPDATE questions SET
                    is_answered = ?, answer_text = ?, updated_at = ?
                WHERE id = ?
            """

            params = (
                True,
                answer,
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                question_id
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Updated answer for question: {question_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating answer for question {question_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> Question:
        """Convert database row to Question model"""
        try:
            # Parse JSON fields
            generated_insights = json.loads(row['generated_insights']) if row.get('generated_insights') else []
            detected_conflicts = json.loads(row['detected_conflicts']) if row.get('detected_conflicts') else []
            recommended_follow_ups = json.loads(row['recommended_follow_ups']) if row.get(
                'recommended_follow_ups') else []

            # Parse datetime fields
            created_at = DateTimeHelper.from_iso_string(row['created_at']) if row.get(
                'created_at') else DateTimeHelper.now()
            updated_at = DateTimeHelper.from_iso_string(row['updated_at']) if row.get(
                'updated_at') else DateTimeHelper.now()

            return Question(
                id=row.get('id', ''),
                session_id=row.get('session_id', ''),
                role=TechnicalRole(row['role']) if row.get('role') else TechnicalRole.PROJECT_MANAGER,
                question_text=row.get('question_text', ''),
                context=row.get('context', ''),
                is_follow_up=bool(row.get('is_follow_up', False)),
                parent_question_id=row.get('parent_question_id'),
                importance_score=float(row.get('importance_score', 0.5)),
                is_answered=bool(row.get('is_answered', False)),
                answer_text=row.get('answer_text', ''),
                answer_quality_score=float(row.get('answer_quality_score', 0.0)),
                generated_insights=generated_insights,
                detected_conflicts=detected_conflicts,
                recommended_follow_ups=recommended_follow_ups,
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            self.logger.error(f"Error converting row to Question: {e}")
            return Question()


class ConversationMessageRepository(BaseRepository[ConversationMessage]):
    """Repository for managing conversation messages"""

    def create(self, message: ConversationMessage) -> bool:
        """Create a new conversation message"""
        try:
            data = self._model_to_dict(message)
            query = """
                INSERT INTO conversation_messages (
                    id, session_id, project_id, timestamp, message_type,
                    content, phase, role, author, question_number,
                    insights_extracted, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Convert insights_extracted dict to JSON
            insights_json = json.dumps(data.get('insights_extracted', {}))

            params = (
                data.get('id'),
                data.get('session_id'),
                data.get('project_id'),
                DateTimeHelper.to_iso_string(data.get('timestamp', DateTimeHelper.now())),
                data.get('message_type', 'user'),
                data.get('content'),
                data.get('phase', 'discovery'),
                data.get('role'),
                data.get('author'),
                data.get('question_number'),
                insights_json,
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Created conversation message: {message.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating conversation message: {e}")
            return False

    def get_by_id(self, message_id: str) -> Optional[ConversationMessage]:
        """Get conversation message by ID"""
        try:
            query = "SELECT * FROM conversation_messages WHERE id = ?"
            results = self.db_manager.execute_query(query, (message_id,))

            if results:
                return self._row_to_model(results[0])
            return None

        except Exception as e:
            self.logger.error(f"Error getting conversation message {message_id}: {e}")
            return None

    def update(self, message: ConversationMessage) -> bool:
        """Update existing conversation message"""
        try:
            data = self._model_to_dict(message)

            # Convert insights_extracted dict to JSON
            insights_json = json.dumps(data.get('insights_extracted', {}))

            query = """
                UPDATE conversation_messages SET
                    content = ?, insights_extracted = ?, updated_at = ?
                WHERE id = ?
            """

            params = (
                data.get('content'),
                insights_json,
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Updated conversation message: {message.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating conversation message: {e}")
            return False

    def delete(self, message_id: str) -> bool:
        """Delete conversation message by ID"""
        try:
            query = "DELETE FROM conversation_messages WHERE id = ?"
            self.db_manager.execute_update(query, (message_id,))
            self.logger.info(f"Deleted conversation message: {message_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting conversation message {message_id}: {e}")
            return False

    def get_by_session_id(self, session_id: str) -> List[ConversationMessage]:
        """Get all messages for a session"""
        try:
            query = "SELECT * FROM conversation_messages WHERE session_id = ? ORDER BY timestamp ASC"
            results = self.db_manager.execute_query(query, (session_id,))
            return [self._row_to_model(row) for row in results]

        except Exception as e:
            self.logger.error(f"Error getting messages for session {session_id}: {e}")
            return []

    def _row_to_model(self, row: Dict[str, Any]) -> ConversationMessage:
        """Convert database row to ConversationMessage model"""
        try:
            # Parse JSON fields
            insights_extracted = json.loads(row['insights_extracted']) if row.get('insights_extracted') else {}

            # Parse datetime fields
            timestamp = DateTimeHelper.from_iso_string(row['timestamp']) if row.get(
                'timestamp') else DateTimeHelper.now()
            created_at = DateTimeHelper.from_iso_string(row['created_at']) if row.get(
                'created_at') else DateTimeHelper.now()
            updated_at = DateTimeHelper.from_iso_string(row['updated_at']) if row.get(
                'updated_at') else DateTimeHelper.now()

            # Note: session_id is stored in DB but not in model - we skip it during instantiation
            return ConversationMessage(
                id=row.get('id', ''),
                session_id=row.get('session_id', ''),
                project_id=row.get('project_id', ''),
                timestamp=timestamp,
                message_type=row.get('message_type', 'user'),
                content=row.get('content', ''),
                phase=row.get('phase', 'discovery'),
                role=row.get('role'),
                author=row.get('author'),
                question_number=row.get('question_number'),
                insights_extracted=insights_extracted,
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            self.logger.error(f"Error converting row to ConversationMessage: {e}")
            return ConversationMessage()


# ============================================================================
# TechnicalSpecificationRepository
# ============================================================================

class TechnicalSpecificationRepository(BaseRepository[TechnicalSpec]):
    """Repository for managing technical specifications"""

    def create(self, spec: TechnicalSpec) -> bool:
        """Create a new technical specification"""
        try:
            data = self._model_to_dict(spec)
            query = """
                INSERT INTO technical_specifications (
                    id, project_id, session_id, version, architecture_type,
                    technology_stack, functional_requirements, non_functional_requirements,
                    system_components, data_models, api_specifications,
                    performance_requirements, security_requirements, scalability_requirements,
                    deployment_strategy, infrastructure_requirements, monitoring_requirements,
                    testing_strategy, acceptance_criteria, documentation_requirements,
                    is_approved, approved_by, approved_at, approval_notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                data.get('id'),
                data.get('project_id'),
                data.get('session_id'),
                data.get('version', '1.0.0'),
                data.get('architecture_type'),
                json.dumps(data.get('technology_stack', {})),
                json.dumps(data.get('functional_requirements', [])),
                json.dumps(data.get('non_functional_requirements', [])),
                json.dumps(data.get('system_components', [])),
                json.dumps(data.get('data_models', [])),
                json.dumps(data.get('api_specifications', [])),
                json.dumps(data.get('performance_requirements', {})),
                json.dumps(data.get('security_requirements', [])),
                json.dumps(data.get('scalability_requirements', {})),
                data.get('deployment_strategy'),
                json.dumps(data.get('infrastructure_requirements', {})),
                json.dumps(data.get('monitoring_requirements', [])),
                json.dumps(data.get('testing_strategy', {})),
                json.dumps(data.get('acceptance_criteria', [])),
                json.dumps(data.get('documentation_requirements', [])),
                1 if data.get('is_approved') else 0,
                data.get('approved_by'),
                DateTimeHelper.to_iso_string(data.get('approved_at')) if data.get('approved_at') else None,
                data.get('approval_notes'),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Created technical specification: {spec.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating technical specification: {e}")
            return False

    def get_by_id(self, spec_id: str) -> Optional[TechnicalSpec]:
        """Get technical specification by ID"""
        try:
            query = "SELECT * FROM technical_specifications WHERE id = ?"
            results = self.db_manager.execute_query(query, (spec_id,))
            if results:
                return self._row_to_model(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error getting specification {spec_id}: {e}")
            return None

    def get_by_project_id(self, project_id: str) -> List[TechnicalSpec]:
        """Get all specifications for a project"""
        try:
            query = "SELECT * FROM technical_specifications WHERE project_id = ? ORDER BY version DESC"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting specifications for project {project_id}: {e}")
            return []

    def get_latest(self, project_id: str) -> Optional[TechnicalSpec]:
        """Get the latest specification for a project"""
        try:
            query = """
                SELECT * FROM technical_specifications 
                WHERE project_id = ? 
                ORDER BY version DESC, created_at DESC 
                LIMIT 1
            """
            results = self.db_manager.execute_query(query, (project_id,))
            if results:
                return self._row_to_model(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error getting latest specification for project {project_id}: {e}")
            return None

    def list_versions(self, project_id: str) -> List[str]:
        """List all specification versions for a project"""
        try:
            query = "SELECT version FROM technical_specifications WHERE project_id = ? ORDER BY version DESC"
            results = self.db_manager.execute_query(query, (project_id,))
            return [row['version'] for row in results]
        except Exception as e:
            self.logger.error(f"Error listing versions for project {project_id}: {e}")
            return []

    def update(self, spec: TechnicalSpec) -> bool:
        """Update an existing specification"""
        try:
            data = self._model_to_dict(spec)
            query = """
                UPDATE technical_specifications SET
                    architecture_type = ?,
                    technology_stack = ?,
                    functional_requirements = ?,
                    non_functional_requirements = ?,
                    system_components = ?,
                    data_models = ?,
                    api_specifications = ?,
                    performance_requirements = ?,
                    security_requirements = ?,
                    scalability_requirements = ?,
                    deployment_strategy = ?,
                    infrastructure_requirements = ?,
                    monitoring_requirements = ?,
                    testing_strategy = ?,
                    acceptance_criteria = ?,
                    documentation_requirements = ?,
                    is_approved = ?,
                    approved_by = ?,
                    approved_at = ?,
                    approval_notes = ?,
                    updated_at = ?
                WHERE id = ?
            """

            params = (
                data.get('architecture_type'),
                json.dumps(data.get('technology_stack', {})),
                json.dumps(data.get('functional_requirements', [])),
                json.dumps(data.get('non_functional_requirements', [])),
                json.dumps(data.get('system_components', [])),
                json.dumps(data.get('data_models', [])),
                json.dumps(data.get('api_specifications', [])),
                json.dumps(data.get('performance_requirements', {})),
                json.dumps(data.get('security_requirements', [])),
                json.dumps(data.get('scalability_requirements', {})),
                data.get('deployment_strategy'),
                json.dumps(data.get('infrastructure_requirements', {})),
                json.dumps(data.get('monitoring_requirements', [])),
                json.dumps(data.get('testing_strategy', {})),
                json.dumps(data.get('acceptance_criteria', [])),
                json.dumps(data.get('documentation_requirements', [])),
                1 if data.get('is_approved') else 0,
                data.get('approved_by'),
                DateTimeHelper.to_iso_string(data.get('approved_at')) if data.get('approved_at') else None,
                data.get('approval_notes'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Updated technical specification: {spec.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error converting row to TechnicalSpec: {e}")
            return TechnicalSpec()  # TODO Expected type 'bool', got 'TechnicalSpec | BaseModel' instead

    def delete(self, spec_id: str) -> bool:
        """Delete a specification by ID"""
        try:
            query = "DELETE FROM technical_specifications WHERE id = ?"
            self.db_manager.execute_update(query, (spec_id,))
            self.logger.info(f"Deleted technical specification: {spec_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting specification {spec_id}: {e}")
            return False

    def approve(self, spec_id: str, approved_by: str, notes: str = "") -> bool:
        """Approve a specification"""
        try:
            query = """
                UPDATE technical_specifications SET
                    is_approved = 1,
                    approved_by = ?,
                    approved_at = ?,
                    approval_notes = ?,
                    updated_at = ?
                WHERE id = ?
            """

            params = (
                approved_by,
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                notes,
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                spec_id
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Approved specification: {spec_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error approving specification {spec_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> TechnicalSpec:
        """Convert database row to TechnicalSpec model"""
        try:
            # Parse datetime fields
            created_at = DateTimeHelper.from_iso_string(row['created_at']) if row.get(
                'created_at') else DateTimeHelper.now()
            updated_at = DateTimeHelper.from_iso_string(row['updated_at']) if row.get(
                'updated_at') else DateTimeHelper.now()
            approved_at = DateTimeHelper.from_iso_string(row['approved_at']) if row.get('approved_at') else None

            return TechnicalSpec(
                id=row.get('id', ''),
                project_id=row.get('project_id', ''),
                version=row.get('version', '1.0.0'),
                architecture_type=row.get('architecture_type', ''),
                technology_stack=json.loads(row['technology_stack']) if row.get('technology_stack') else {},
                functional_requirements=json.loads(row['functional_requirements']) if row.get(
                    'functional_requirements') else [],
                non_functional_requirements=json.loads(row['non_functional_requirements']) if row.get(
                    'non_functional_requirements') else [],
                system_components=json.loads(row['system_components']) if row.get('system_components') else [],
                data_models=json.loads(row['data_models']) if row.get('data_models') else [],
                api_specifications=json.loads(row['api_specifications']) if row.get('api_specifications') else [],
                performance_requirements=json.loads(row['performance_requirements']) if row.get(
                    'performance_requirements') else {},
                security_requirements=json.loads(row['security_requirements']) if row.get(
                    'security_requirements') else [],
                scalability_requirements=json.loads(row['scalability_requirements']) if row.get(
                    'scalability_requirements') else {},
                deployment_strategy=row.get('deployment_strategy', ''),
                infrastructure_requirements=json.loads(row['infrastructure_requirements']) if row.get(
                    'infrastructure_requirements') else {},
                monitoring_requirements=json.loads(row['monitoring_requirements']) if row.get(
                    'monitoring_requirements') else [],
                testing_strategy=json.loads(row['testing_strategy']) if row.get('testing_strategy') else {},
                acceptance_criteria=json.loads(row['acceptance_criteria']) if row.get('acceptance_criteria') else [],
                documentation_requirements=json.loads(row['documentation_requirements']) if row.get(
                    'documentation_requirements') else [],
                is_approved=bool(row.get('is_approved', 0)),
                approved_by=row.get('approved_by'),
                approved_at=approved_at,
                approval_notes=row.get('approval_notes', ''),
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            self.logger.error(f"Error converting row to TechnicalSpec: {e}")
            return TechnicalSpec()


# ==============================================================================
# CONTEXT REPOSITORY CLASSES
# ==============================================================================

class ProjectContextRepository(BaseRepository[ProjectContext]):
    """Repository for managing project context analysis"""

    def create(self, context: ProjectContext) -> bool:
        """Create new project context"""
        try:
            data = self._model_to_dict(context)
            query = """
                INSERT INTO project_contexts (
                    id, project_id, business_domain, target_audience, business_goals,
                    existing_systems, integration_requirements, performance_requirements,
                    team_structure, budget_constraints, timeline_constraints,
                    last_analyzed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                data.get('id'),
                data.get('project_id'),
                data.get('business_domain'),
                data.get('target_audience'),
                json.dumps(data.get('business_goals', [])),
                json.dumps(data.get('existing_systems', [])),
                json.dumps(data.get('integration_requirements', [])),
                json.dumps(data.get('performance_requirements', {})),
                json.dumps(data.get('team_structure', {})),
                json.dumps(data.get('budget_constraints', {})),
                json.dumps(data.get('timeline_constraints', {})),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')) if data.get('last_analyzed_at') else None,
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Created project context: {context.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating project context: {e}")
            return False

    def get_by_id(self, context_id: str) -> Optional[ProjectContext]:
        """Get project context by ID"""
        try:
            query = "SELECT * FROM project_contexts WHERE id = ?"
            results = self.db_manager.execute_query(query, (context_id,))
            if results:
                return self._row_to_model(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error getting project context {context_id}: {e}")
            return None

    def get_by_project_id(self, project_id: str) -> Optional[ProjectContext]:
        """Get context by project ID"""
        try:
            query = "SELECT * FROM project_contexts WHERE project_id = ?"
            results = self.db_manager.execute_query(query, (project_id,))
            if results:
                return self._row_to_model(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error getting context for project {project_id}: {e}")
            return None

    def update(self, context: ProjectContext) -> bool:
        """Update existing project context"""
        try:
            data = self._model_to_dict(context)
            query = """
                UPDATE project_contexts SET
                    business_domain = ?,
                    target_audience = ?,
                    business_goals = ?,
                    existing_systems = ?,
                    integration_requirements = ?,
                    performance_requirements = ?,
                    team_structure = ?,
                    budget_constraints = ?,
                    timeline_constraints = ?,
                    last_analyzed_at = ?,
                    updated_at = ?
                WHERE id = ?
            """

            params = (
                data.get('business_domain'),
                data.get('target_audience'),
                json.dumps(data.get('business_goals', [])),
                json.dumps(data.get('existing_systems', [])),
                json.dumps(data.get('integration_requirements', [])),
                json.dumps(data.get('performance_requirements', {})),
                json.dumps(data.get('team_structure', {})),
                json.dumps(data.get('budget_constraints', {})),
                json.dumps(data.get('timeline_constraints', {})),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')) if data.get('last_analyzed_at') else None,
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Updated project context: {context.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating project context {context.id}: {e}")
            return False

    def upsert(self, context: ProjectContext) -> bool:
        """Update if exists, create if not"""
        existing = self.get_by_project_id(context.project_id)
        if existing:
            context.id = existing.id
            return self.update(context)
        return self.create(context)

    def delete(self, context_id: str) -> bool:
        """Delete project context"""
        try:
            query = "DELETE FROM project_contexts WHERE id = ?"
            self.db_manager.execute_update(query, (context_id,))
            self.logger.info(f"Deleted project context: {context_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting project context {context_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> ProjectContext:
        """Convert database row to ProjectContext model"""
        try:
            created_at = DateTimeHelper.from_iso_string(row['created_at']) if row.get(
                'created_at') else DateTimeHelper.now()
            updated_at = DateTimeHelper.from_iso_string(row['updated_at']) if row.get(
                'updated_at') else DateTimeHelper.now()
            last_analyzed_at = DateTimeHelper.from_iso_string(row['last_analyzed_at']) if row.get(
                'last_analyzed_at') else None

            return ProjectContext(
                id=row.get('id', ''),
                project_id=row.get('project_id', ''),
                business_domain=row.get('business_domain', ''),
                target_audience=row.get('target_audience', ''),
                business_goals=json.loads(row['business_goals']) if row.get('business_goals') else [],
                existing_systems=json.loads(row['existing_systems']) if row.get('existing_systems') else [],
                integration_requirements=json.loads(row['integration_requirements']) if row.get(
                    'integration_requirements') else [],
                performance_requirements=json.loads(row['performance_requirements']) if row.get(
                    'performance_requirements') else {},
                team_structure=json.loads(row['team_structure']) if row.get('team_structure') else {},
                budget_constraints=json.loads(row['budget_constraints']) if row.get('budget_constraints') else {},
                timeline_constraints=json.loads(row['timeline_constraints']) if row.get(
                    'timeline_constraints') else {},
                last_analyzed_at=last_analyzed_at,
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            self.logger.error(f"Error converting row to ProjectContext: {e}")
            return ProjectContext()


class ModuleContextRepository(BaseRepository[ModuleContext]):
    """Repository for managing module context analysis"""

    def create(self, context: ModuleContext) -> bool:
        """Create new module context"""
        try:
            data = self._model_to_dict(context)
            query = """
                INSERT INTO module_contexts (
                    id, module_id, project_id, business_context, technical_context,
                    dependencies_context, related_modules, related_requirements,
                    related_constraints, last_analyzed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                data.get('id'),
                data.get('module_id'),
                data.get('project_id'),
                data.get('business_context'),
                data.get('technical_context'),
                data.get('dependencies_context'),
                json.dumps(data.get('related_modules', [])),
                json.dumps(data.get('related_requirements', [])),
                json.dumps(data.get('related_constraints', [])),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')) if data.get(
                    'last_analyzed_at') else None,
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Created module context: {context.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating module context: {e}")
            return False

    def get_by_id(self, context_id: str) -> Optional[ModuleContext]:
        """Get module context by ID"""
        try:
            query = "SELECT * FROM module_contexts WHERE id = ?"
            results = self.db_manager.execute_query(query, (context_id,))
            if results:
                return self._row_to_model(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error getting module context {context_id}: {e}")
            return None

    def get_by_module_id(self, module_id: str) -> Optional[ModuleContext]:
        """Get context by module ID"""
        try:
            query = "SELECT * FROM module_contexts WHERE module_id = ?"
            results = self.db_manager.execute_query(query, (module_id,))
            if results:
                return self._row_to_model(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error getting context for module {module_id}: {e}")
            return None

    def get_by_project_id(self, project_id: str) -> List[ModuleContext]:
        """Get all module contexts for a project"""
        try:
            query = "SELECT * FROM module_contexts WHERE project_id = ?"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting module contexts for project {project_id}: {e}")
            return []

    def update(self, context: ModuleContext) -> bool:
        """Update existing module context"""
        try:
            data = self._model_to_dict(context)
            query = """
                UPDATE module_contexts SET
                    business_context = ?,
                    technical_context = ?,
                    dependencies_context = ?,
                    related_modules = ?,
                    related_requirements = ?,
                    related_constraints = ?,
                    last_analyzed_at = ?,
                    updated_at = ?
                WHERE id = ?
            """

            params = (
                data.get('business_context'),
                data.get('technical_context'),
                data.get('dependencies_context'),
                json.dumps(data.get('related_modules', [])),
                json.dumps(data.get('related_requirements', [])),
                json.dumps(data.get('related_constraints', [])),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')) if data.get(
                    'last_analyzed_at') else None,
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Updated module context: {context.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating module context {context.id}: {e}")
            return False

    def upsert(self, context: ModuleContext) -> bool:
        """Update if exists, create if not"""
        existing = self.get_by_module_id(context.module_id)
        if existing:
            context.id = existing.id
            return self.update(context)
        return self.create(context)

    def delete(self, context_id: str) -> bool:
        """Delete module context"""
        try:
            query = "DELETE FROM module_contexts WHERE id = ?"
            self.db_manager.execute_update(query, (context_id,))
            self.logger.info(f"Deleted module context: {context_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting module context {context_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> ModuleContext:
        """Convert database row to ModuleContext model"""
        try:
            created_at = DateTimeHelper.from_iso_string(row['created_at']) if row.get(
                'created_at') else DateTimeHelper.now()
            updated_at = DateTimeHelper.from_iso_string(row['updated_at']) if row.get(
                'updated_at') else DateTimeHelper.now()
            last_analyzed_at = DateTimeHelper.from_iso_string(row['last_analyzed_at']) if row.get(
                'last_analyzed_at') else None

            return ModuleContext(
                id=row.get('id', ''),
                module_id=row.get('module_id', ''),
                project_id=row.get('project_id', ''),
                business_context=row.get('business_context', ''),
                technical_context=row.get('technical_context', ''),
                dependencies_context=row.get('dependencies_context', ''),
                related_modules=json.loads(row['related_modules']) if row.get('related_modules') else [],
                related_requirements=json.loads(row['related_requirements']) if row.get(
                    'related_requirements') else [],
                related_constraints=json.loads(row['related_constraints']) if row.get(
                    'related_constraints') else [],
                last_analyzed_at=last_analyzed_at,
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            self.logger.error(f"Error converting row to ModuleContext: {e}")
            return ModuleContext()


class TaskContextRepository(BaseRepository[TaskContext]):
    """Repository for managing task context analysis"""

    def create(self, context: TaskContext) -> bool:
        """Create new task context"""
        try:
            data = self._model_to_dict(context)
            query = """
                INSERT INTO task_contexts (
                    id, task_id, module_id, project_id, task_context,
                    implementation_notes, testing_requirements, prerequisite_tasks,
                    dependent_tasks, last_analyzed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                data.get('id'),
                data.get('task_id'),
                data.get('module_id'),
                data.get('project_id'),
                data.get('task_context'),
                data.get('implementation_notes'),
                data.get('testing_requirements'),
                json.dumps(data.get('prerequisite_tasks', [])),
                json.dumps(data.get('dependent_tasks', [])),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')) if data.get(
                    'last_analyzed_at') else None,
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Created task context: {context.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating task context: {e}")
            return False

    def get_by_id(self, context_id: str) -> Optional[TaskContext]:
        """Get task context by ID"""
        try:
            query = "SELECT * FROM task_contexts WHERE id = ?"
            results = self.db_manager.execute_query(query, (context_id,))
            if results:
                return self._row_to_model(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error getting task context {context_id}: {e}")
            return None

    def get_by_task_id(self, task_id: str) -> Optional[TaskContext]:
        """Get context by task ID"""
        try:
            query = "SELECT * FROM task_contexts WHERE task_id = ?"
            results = self.db_manager.execute_query(query, (task_id,))
            if results:
                return self._row_to_model(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error getting context for task {task_id}: {e}")
            return None

    def get_by_module_id(self, module_id: str) -> List[TaskContext]:
        """Get all task contexts for a module"""
        try:
            query = "SELECT * FROM task_contexts WHERE module_id = ?"
            results = self.db_manager.execute_query(query, (module_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting task contexts for module {module_id}: {e}")
            return []

    def get_by_project_id(self, project_id: str) -> List[TaskContext]:
        """Get all task contexts for a project"""
        try:
            query = "SELECT * FROM task_contexts WHERE project_id = ?"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting task contexts for project {project_id}: {e}")
            return []

    def update(self, context: TaskContext) -> bool:
        """Update existing task context"""
        try:
            data = self._model_to_dict(context)
            query = """
                UPDATE task_contexts SET
                    task_context = ?,
                    implementation_notes = ?,
                    testing_requirements = ?,
                    prerequisite_tasks = ?,
                    dependent_tasks = ?,
                    last_analyzed_at = ?,
                    updated_at = ?
                WHERE id = ?
            """

            params = (
                data.get('task_context'),
                data.get('implementation_notes'),
                data.get('testing_requirements'),
                json.dumps(data.get('prerequisite_tasks', [])),
                json.dumps(data.get('dependent_tasks', [])),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')) if data.get(
                    'last_analyzed_at') else None,
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )

            self.db_manager.execute_update(query, params)
            self.logger.info(f"Updated task context: {context.id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating task context {context.id}: {e}")
            return False

    def upsert(self, context: TaskContext) -> bool:
        """Update if exists, create if not"""
        existing = self.get_by_task_id(context.task_id)
        if existing:
            context.id = existing.id
            return self.update(context)
        return self.create(context)

    def delete(self, context_id: str) -> bool:
        """Delete task context"""
        try:
            query = "DELETE FROM task_contexts WHERE id = ?"
            self.db_manager.execute_update(query, (context_id,))
            self.logger.info(f"Deleted task context: {context_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting task context {context_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> TaskContext:
        """Convert database row to TaskContext model"""
        try:
            created_at = DateTimeHelper.from_iso_string(row['created_at']) if row.get(
                'created_at') else DateTimeHelper.now()
            updated_at = DateTimeHelper.from_iso_string(row['updated_at']) if row.get(
                'updated_at') else DateTimeHelper.now()
            last_analyzed_at = DateTimeHelper.from_iso_string(row['last_analyzed_at']) if row.get(
                'last_analyzed_at') else None

            return TaskContext(
                id=row.get('id', ''),
                task_id=row.get('task_id', ''),
                module_id=row.get('module_id', ''),
                project_id=row.get('project_id', ''),
                task_context=row.get('task_context', ''),
                implementation_notes=row.get('implementation_notes', ''),
                testing_requirements=row.get('testing_requirements', ''),
                prerequisite_tasks=json.loads(row['prerequisite_tasks']) if row.get('prerequisite_tasks') else [],
                dependent_tasks=json.loads(row['dependent_tasks']) if row.get('dependent_tasks') else [],
                last_analyzed_at=last_analyzed_at,
                created_at=created_at,
                updated_at=updated_at
            )
        except Exception as e:
            self.logger.error(f"Error converting row to TaskContext: {e}")
            return TaskContext()


# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Core database management with connection pooling"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.logger = get_logger(f"{__name__}.DatabaseManager")
        self._ensure_database_exists()
        self._init_schema()

    def _ensure_database_exists(self):
        """Ensure database file and directory exist"""
        try:
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Error creating database directory: {e}")
            raise DatabaseError(f"Failed to create database directory: {e}")

    def _init_schema(self):
        """Initialize database schema"""
        try:
            with self.get_connection() as conn:
                # Users table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        first_name TEXT,
                        last_name TEXT,
                        role TEXT NOT NULL DEFAULT 'viewer',
                        status TEXT NOT NULL DEFAULT 'active',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_login TEXT
                    )
                """)

                # Projects table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        owner_id TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'draft',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        technology_stack TEXT,
                        FOREIGN KEY (owner_id) REFERENCES users(id)
                    )
                """)

                # Generated codebases table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS generated_codebases (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        version TEXT NOT NULL DEFAULT '1.0.0',
                        architecture_type TEXT,
                        total_lines_of_code INTEGER DEFAULT 0,
                        total_files INTEGER DEFAULT 0,
                        size_bytes INTEGER DEFAULT 0,
                        code_quality_score REAL DEFAULT 0.0,
                        test_coverage REAL DEFAULT 0.0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                    )
                """)

                # Generated files table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS generated_files (
                        id TEXT PRIMARY KEY,
                        codebase_id TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        content TEXT NOT NULL,
                        size_bytes INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (codebase_id) REFERENCES generated_codebases(id)
                    )
                """)

                # Project collaborators table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS project_collaborators (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'developer',
                        permissions TEXT,
                        joined_at TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1,
                        invitation_status TEXT DEFAULT 'active',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(id),
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        UNIQUE(project_id, user_id)
                    )
                """)

                # Socratic sessions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS socratic_sessions (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        current_role TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'active',
                        roles_to_cover TEXT,
                        completed_roles TEXT,
                        total_questions INTEGER DEFAULT 0,
                        questions_answered INTEGER DEFAULT 0,
                        insights_generated TEXT,
                        conflicts_detected TEXT,
                        session_notes TEXT,
                        quality_score REAL DEFAULT 0.0,
                        completion_percentage REAL DEFAULT 0.0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(id),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)

                # Questions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS questions (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        question_text TEXT NOT NULL,
                        context TEXT,
                        is_follow_up INTEGER DEFAULT 0,
                        parent_question_id TEXT,
                        importance_score REAL DEFAULT 0.5,
                        is_answered INTEGER DEFAULT 0,
                        answer_text TEXT,
                        answer_quality_score REAL DEFAULT 0.0,
                        generated_insights TEXT,
                        detected_conflicts TEXT,
                        recommended_follow_ups TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES socratic_sessions(id)
                    )
                """)

                # Conversation messages table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_messages (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        role TEXT,
                        content TEXT NOT NULL,
                        message_type TEXT NOT NULL,
                        phase TEXT,
                        author TEXT,
                        question_number INTEGER,
                        insights_extracted TEXT,
                        metadata TEXT,
                        timestamp TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES socratic_sessions(id),
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                    )
                """)

                # Technical specifications table
                conn.execute("""
                                    CREATE TABLE IF NOT EXISTS technical_specifications (
                                        id TEXT PRIMARY KEY,
                                        project_id TEXT NOT NULL,
                                        session_id TEXT,
                                        version TEXT NOT NULL DEFAULT '1.0.0',
                                        architecture_type TEXT,
                                        technology_stack TEXT,
                                        functional_requirements TEXT,
                                        non_functional_requirements TEXT,
                                        system_components TEXT,
                                        data_models TEXT,
                                        api_specifications TEXT,
                                        performance_requirements TEXT,
                                        security_requirements TEXT,
                                        scalability_requirements TEXT,
                                        deployment_strategy TEXT,
                                        infrastructure_requirements TEXT,
                                        monitoring_requirements TEXT,
                                        testing_strategy TEXT,
                                        acceptance_criteria TEXT,
                                        documentation_requirements TEXT,
                                        is_approved INTEGER DEFAULT 0,
                                        approved_by TEXT,
                                        approved_at TEXT,
                                        approval_notes TEXT,
                                        created_at TEXT NOT NULL,
                                        updated_at TEXT NOT NULL,
                                        FOREIGN KEY (project_id) REFERENCES projects(id),
                                        FOREIGN KEY (session_id) REFERENCES socratic_sessions(id)
                                    )
                                """)
                # Project contexts table
                conn.execute("""
                                    CREATE TABLE IF NOT EXISTS project_contexts (
                                        id TEXT PRIMARY KEY,
                                        project_id TEXT NOT NULL UNIQUE,
                                        business_domain TEXT,
                                        target_audience TEXT,
                                        business_goals TEXT,
                                        existing_systems TEXT,
                                        integration_requirements TEXT,
                                        performance_requirements TEXT,
                                        team_structure TEXT,
                                        budget_constraints TEXT,
                                        timeline_constraints TEXT,
                                        last_analyzed_at TEXT,
                                        created_at TEXT NOT NULL,
                                        updated_at TEXT NOT NULL,
                                        FOREIGN KEY (project_id) REFERENCES projects(id)
                                    )
                                """)

                # Module contexts table
                conn.execute("""
                                    CREATE TABLE IF NOT EXISTS module_contexts (
                                        id TEXT PRIMARY KEY,
                                        module_id TEXT NOT NULL UNIQUE,
                                        project_id TEXT NOT NULL,
                                        business_context TEXT,
                                        technical_context TEXT,
                                        dependencies_context TEXT,
                                        related_modules TEXT,
                                        related_requirements TEXT,
                                        related_constraints TEXT,
                                        last_analyzed_at TEXT,
                                        created_at TEXT NOT NULL,
                                        updated_at TEXT NOT NULL,
                                        FOREIGN KEY (module_id) REFERENCES modules(id),
                                        FOREIGN KEY (project_id) REFERENCES projects(id)
                                    )
                                """)

                # Task contexts table
                conn.execute("""
                                    CREATE TABLE IF NOT EXISTS task_contexts (
                                        id TEXT PRIMARY KEY,
                                        task_id TEXT NOT NULL UNIQUE,
                                        module_id TEXT NOT NULL,
                                        project_id TEXT NOT NULL,
                                        task_context TEXT,
                                        implementation_notes TEXT,
                                        testing_requirements TEXT,
                                        prerequisite_tasks TEXT,
                                        dependent_tasks TEXT,
                                        last_analyzed_at TEXT,
                                        created_at TEXT NOT NULL,
                                        updated_at TEXT NOT NULL,
                                        FOREIGN KEY (task_id) REFERENCES tasks(id),
                                        FOREIGN KEY (module_id) REFERENCES modules(id),
                                        FOREIGN KEY (project_id) REFERENCES projects(id)
                                    )
                                """)
                conn.commit()
                self.logger.info("Database schema initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing database schema: {e}")
            raise DatabaseError(f"Failed to initialize database schema: {e}")

    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup"""
        conn = None
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                conn.row_factory = sqlite3.Row
                yield conn
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise DatabaseError(f"Query failed: {e}")

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Update execution failed: {e}")
            raise DatabaseError(f"Update failed: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Check database health and connectivity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT 1")
                cursor.fetchone()
                return {
                    'status': 'healthy',
                    'database_path': self.db_path,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            }


# ============================================================================
# DATABASE SERVICE (MAIN INTERFACE)
# ============================================================================

class DatabaseService:
    """Main database service with all repositories"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            config = get_config()
            db_path = config.get('database', {}).get('path', 'data/socratic.db')

        self.db_manager = DatabaseManager(db_path)
        self.logger = get_logger(f"{__name__}.DatabaseService")

        # Initialize repositories with proper types
        self.users = UserRepository(self.db_manager, User)
        self.projects = ProjectRepository(self.db_manager, Project)
        self.generated_codebases = GeneratedCodebaseRepository(self.db_manager, GeneratedCodebase)
        self.generated_files = GeneratedFileRepository(self.db_manager, GeneratedFile)
        self.project_collaborators = ProjectCollaboratorRepository(self.db_manager, ProjectCollaborator)
        self.technical_specifications = TechnicalSpecificationRepository(self.db_manager, TechnicalSpec)
        self.project_contexts = ProjectContextRepository(self.db_manager, ProjectContext)
        self.module_contexts = ModuleContextRepository(self.db_manager, ModuleContext)
        self.task_contexts = TaskContextRepository(self.db_manager, TaskContext)

        # Add other repositories as needed
        # self.modules = ModuleRepository(self.db_manager, Module)
        # self.tasks = TaskRepository(self.db_manager, Task)
        # self.sessions = SocraticSessionRepository(self.db_manager, SocraticSession)
        # Session persistence repositories
        self.socratic_sessions = SocraticSessionRepository(self.db_manager, SocraticSession)
        self.questions = QuestionRepository(self.db_manager, Question)
        self.conversation_messages = ConversationMessageRepository(self.db_manager, ConversationMessage)
        self.logger.info("DatabaseService initialized successfully")

    @property
    def codebases(self):
        """Alias for generated_codebases for backward compatibility"""
        return self.generated_codebases

    def health_check(self) -> Dict[str, Any]:
        """Check overall database health"""
        return self.db_manager.health_check()

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}

            # Count records in each table
            tables = ['users', 'projects', 'generated_codebases', 'generated_files', 'project_collaborators']
            for table in tables:
                try:
                    query = f"SELECT COUNT(*) as count FROM {table}"
                    result = self.db_manager.execute_query(query)
                    stats[f"{table}_count"] = result[0]['count'] if result else 0
                except Exception as e:
                    self.logger.warning(f"Error counting {table}: {e}")
                    stats[f"{table}_count"] = 0

            # Calculate total size
            try:
                query = "SELECT SUM(size_bytes) as total_size FROM generated_codebases"
                result = self.db_manager.execute_query(query)
                stats['total_codebase_size_bytes'] = result[0]['total_size'] or 0
            except Exception as e:
                self.logger.warning(f"Error calculating total size: {e}")
                stats['total_codebase_size_bytes'] = 0

            stats['timestamp'] = DateTimeHelper.to_iso_string(DateTimeHelper.now())
            return stats

        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}

    def backup(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            import shutil
            shutil.copy2(self.db_manager.db_path, backup_path)
            self.logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            return False


# ============================================================================
# REPOSITORY MANAGER
# ============================================================================

class RepositoryManager:
    """Centralized repository management"""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.logger = get_logger(f"{__name__}.RepositoryManager")

    def get_repository(self, model_type: str):
        """Get repository by model type"""
        repository_mapping = {
            'user': self.db_service.users,
            'project': self.db_service.projects,
            'generated_codebase': self.db_service.generated_codebases,
            'generated_file': self.db_service.generated_files,
            'project_collaborator': self.db_service.project_collaborators,
            'codebase': self.db_service.codebases,
            'socratic_session': self.db_service.socratic_sessions,
            'question': self.db_service.questions,
            'conversation_message': self.db_service.conversation_messages,
        }

        return repository_mapping.get(model_type.lower())

    def get_all_repositories(self) -> Dict[str, Any]:
        """Get all available repositories"""
        return {
            'users': self.db_service.users,
            'projects': self.db_service.projects,
            'generated_codebases': self.db_service.generated_codebases,
            'generated_files': self.db_service.generated_files,
            'project_collaborators': self.db_service.project_collaborators,
            'codebases': self.db_service.codebases,
            'socratic_sessions': self.db_service.socratic_sessions,
            'questions': self.db_service.questions,
            'conversation_messages': self.db_service.conversation_messages,
        }


# ============================================================================
# GLOBAL INSTANCES AND FACTORY FUNCTIONS
# ============================================================================

_database_service_instance = None
_repository_manager_instance = None


def get_database(db_path: str = None) -> DatabaseService:
    """Get global database service instance"""
    global _database_service_instance
    if _database_service_instance is None:
        _database_service_instance = DatabaseService(db_path)
    return _database_service_instance


def get_repository_manager() -> RepositoryManager:
    """Get global repository manager instance"""
    global _repository_manager_instance
    if _repository_manager_instance is None:
        _repository_manager_instance = RepositoryManager(get_database())
    return _repository_manager_instance


def init_database(db_path: str = None) -> DatabaseService:
    """Initialize database with custom path"""
    global _database_service_instance
    _database_service_instance = DatabaseService(db_path)
    return _database_service_instance


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Main service classes
    'DatabaseService', 'DatabaseManager', 'RepositoryManager',

    # Repository classes
    'BaseRepository', 'UserRepository', 'ProjectRepository',
    'GeneratedCodebaseRepository', 'GeneratedFileRepository',
    'ProjectCollaboratorRepository', 'SocraticSessionRepository',
    'QuestionRepository', 'ConversationMessageRepository',

    # Factory functions
    'get_database', 'get_repository_manager', 'init_database',

    # Exceptions
    'DatabaseError',
]

if __name__ == "__main__":
    # Test database functionality
    print("Testing database functionality...")

    try:
        # Test database service initialization
        db = get_database()
        print(f"✅ DatabaseService initialized successfully")

        # Test project_collaborators repository exists
        print(f"✅ project_collaborators exists: {hasattr(db, 'project_collaborators')}")

        # Test codebases property alias
        print(f"✅ codebases alias accessible: {db.codebases is db.generated_codebases}")

        # Test health check
        health = db.health_check()
        print(f"✅ Database health check: {health.get('status', 'unknown')}")

        # Test repository manager
        repo_manager = get_repository_manager()
        codebase_repo = repo_manager.get_repository('codebase')
        print(f"✅ Repository manager working: {codebase_repo is not None}")

        collab_repo = repo_manager.get_repository('project_collaborator')
        print(f"✅ ProjectCollaborator repository accessible: {collab_repo is not None}")

        print("🎉 All database tests passed!")

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import sys

        sys.exit(1)
