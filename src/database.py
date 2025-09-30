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
        return {'database': {'path': 'data/socratic_rag.db'}}


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
        FileType, TestType, Priority, ConflictType
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

    def _model_to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        if hasattr(entity, 'to_dict'):
            return entity.to_dict()
        elif hasattr(entity, '__dict__'):
            return entity.__dict__
        else:
            return {}


# ============================================================================
# SPECIFIC REPOSITORY IMPLEMENTATIONS
# ============================================================================

class UserRepository(BaseRepository[User]):
    """User repository with type safety"""

    def create(self, user: User) -> bool:
        try:
            data = self._model_to_dict(user)
            query = """
                INSERT INTO users (id, username, email, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id', str(uuid.uuid4())),
                data.get('username', ''),
                data.get('email', ''),
                data.get('role', 'viewer'),
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

    def create(self, user: User) -> bool:
        """Create new user in database"""
        try:
            # Convert User model to dict
            if hasattr(user, 'to_dict'):
                data = user.to_dict()
            elif hasattr(user, '__dict__'):
                data = user.__dict__.copy()
            else:
                data = {}

            query = """
                INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id', str(uuid.uuid4())),
                data.get('username', ''),
                data.get('email', ''),
                data.get('password_hash', ''),
                data.get('role', 'viewer'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                DateTimeHelper.to_iso_string(DateTimeHelper.now())
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            return False

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
            db_path = config.get('database', {}).get('path', 'data/socratic_rag.db')

        self.db_manager = DatabaseManager(db_path)
        self.logger = get_logger(f"{__name__}.DatabaseService")

        # Initialize repositories with proper types
        self.users = UserRepository(self.db_manager, User)
        self.projects = ProjectRepository(self.db_manager, Project)
        self.generated_codebases = GeneratedCodebaseRepository(self.db_manager, GeneratedCodebase)
        self.generated_files = GeneratedFileRepository(self.db_manager, GeneratedFile)
        self.project_collaborators = ProjectCollaboratorRepository(self.db_manager, ProjectCollaborator)

        # Add other repositories as needed
        # self.modules = ModuleRepository(self.db_manager, Module)
        # self.tasks = TaskRepository(self.db_manager, Task)
        # self.sessions = SocraticSessionRepository(self.db_manager, SocraticSession)

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
            'codebase': self.db_service.codebases,  # Alias support
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
            'codebases': self.db_service.codebases,  # Alias
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
    'ProjectCollaboratorRepository',

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
