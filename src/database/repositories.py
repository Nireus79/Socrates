#!/usr/bin/env python3
"""
Repository Implementations
===========================
All concrete repository implementations for the Socratic RAG Enhanced system.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from .base import BaseRepository, parse_json_field, dump_json_field
from src.models import Conflict

try:
    from src.models import (
        User, Project, Module, Task, GeneratedCodebase, GeneratedFile,
        ProjectCollaborator, SocraticSession, Question, ConversationMessage,
        TechnicalSpec, ProjectContext, ModuleContext, TaskContext, Conflict,
        UserRole, ProjectStatus, ModuleType, ModuleStatus, TaskStatus, Priority,
        ConflictType
    )
    from src.core import DateTimeHelper

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    import logging


    def get_logger(name):
        return logging.getLogger(name)


    def parse_json_field(data, default=None):
        return default


    def dump_json_field(data):
        return None


    # Fallback DateTimeHelper
    class DateTimeHelper:
        @staticmethod
        def now():
            from datetime import datetime
            return datetime.now()

        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None

        @staticmethod
        def from_iso_string(iso_str):
            if not iso_str:
                return None
            from datetime import datetime
            return datetime.fromisoformat(iso_str)


    # Fallback model classes
    @dataclass
    class User:
        id: str = ""


    @dataclass
    class Project:
        id: str = ""


    @dataclass
    class Module:
        id: str = ""


    @dataclass
    class Task:
        id: str = ""


    @dataclass
    class GeneratedCodebase:
        id: str = ""


    @dataclass
    class GeneratedFile:
        id: str = ""


    @dataclass
    class ProjectCollaborator:
        id: str = ""


    @dataclass
    class SocraticSession:
        id: str = ""


    @dataclass
    class Question:
        id: str = ""


    @dataclass
    class ConversationMessage:
        id: str = ""


    @dataclass
    class TechnicalSpec:
        id: str = ""


    @dataclass
    class ProjectContext:
        id: str = ""


    @dataclass
    class ModuleContext:
        id: str = ""


    @dataclass
    class TaskContext:
        id: str = ""


    @dataclass
    class Conflict:
        id: str = ""

# Core imports with fallbacks
try:
    from src import get_logger
    from src.core import DateTimeHelper

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
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

# Model imports with fallbacks
try:
    from src.models import (
        User, Project, GeneratedCodebase, GeneratedFile, ProjectCollaborator,
        SocraticSession, Question, ConversationMessage, TechnicalSpec,
        ProjectContext, ModuleContext, TaskContext
    )

    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    from dataclasses import dataclass


    @dataclass
    class User:
        id: str = ""
        username: str = ""
        email: str = ""
        password_hash: str = ""


    @dataclass
    class Project:
        id: str = ""
        name: str = ""
        owner_id: str = ""


    @dataclass
    class GeneratedCodebase:
        id: str = ""
        project_id: str = ""
        version: str = "1.0.0"


    @dataclass
    class GeneratedFile:
        id: str = ""
        codebase_id: str = ""
        file_path: str = ""
        content: str = ""


    @dataclass
    class ProjectCollaborator:
        id: str = ""
        project_id: str = ""
        user_id: str = ""


    @dataclass
    class SocraticSession:
        id: str = ""
        project_id: str = ""


    @dataclass
    class Question:
        id: str = ""
        session_id: str = ""


    @dataclass
    class ConversationMessage:
        id: str = ""
        session_id: str = ""


    @dataclass
    class TechnicalSpec:
        id: str = ""
        project_id: str = ""


    @dataclass
    class ProjectContext:
        id: str = ""
        project_id: str = ""


    @dataclass
    class ModuleContext:
        id: str = ""
        module_id: str = ""


    @dataclass
    class TaskContext:
        id: str = ""
        task_id: str = ""


def load_json_field(json_str, default=None):
    """Load JSON field from database"""
    if json_str is None:
        return default if default is not None else []
    try:
        import json
        return json.loads(json_str)
    except:
        return default if default is not None else []


def dump_json_field(data):
    """Dump data to JSON string for database"""
    if data is None:
        return None
    try:
        import json
        return json.dumps(data)
    except:
        return None


# ==============================================================================
# USER REPOSITORY
# ==============================================================================

class UserRepository(BaseRepository[User]):
    """Repository for user management"""

    def create(self, user: User) -> bool:
        try:
            data = self._model_to_dict(user)
            query = """
                INSERT INTO users (id, username, email, password_hash, first_name, last_name, 
                                 role, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id'), data.get('username'), data.get('email'),
                data.get('password_hash'), data.get('first_name'), data.get('last_name'),
                data.get('role', 'viewer'), data.get('status', 'active'),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
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
            self.logger.error(f"Error getting user by username: {e}")
            return None

    def get_by_email(self, email: str) -> Optional[User]:
        try:
            query = "SELECT * FROM users WHERE email = ?"
            results = self.db_manager.execute_query(query, (email,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting user by email: {e}")
            return None

    def update(self, user: User) -> bool:
        try:
            data = self._model_to_dict(user)
            query = """
                UPDATE users SET username = ?, email = ?, first_name = ?, last_name = ?,
                               role = ?, status = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('username'), data.get('email'),
                data.get('first_name'), data.get('last_name'),
                data.get('role'), data.get('status'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
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


# ==============================================================================
# PROJECT REPOSITORY
# ==============================================================================

class ProjectRepository(BaseRepository[Project]):
    """Repository for project management"""

    def create(self, project: Project) -> bool:
        try:
            data = self._model_to_dict(project)
            query = """
                INSERT INTO projects (id, name, description, owner_id, status, 
                                    created_at, updated_at, technology_stack)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id'), data.get('name'), data.get('description'),
                data.get('owner_id'), data.get('status', 'draft'),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now())),
                dump_json_field(data.get('technology_stack'))
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
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

    def get_by_status(self, status: str) -> List[Project]:
        try:
            query = "SELECT * FROM projects WHERE status = ? ORDER BY created_at"
            results = self.db_manager.execute_query(query, (status,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting projects by status {status}: {e}")
            return []

    def update(self, project: Project) -> bool:
        try:
            data = self._model_to_dict(project)
            query = """
                UPDATE projects SET name = ?, description = ?, status = ?, 
                                  technology_stack = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('name'), data.get('description'), data.get('status'),
                dump_json_field(data.get('technology_stack')),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
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


# ==============================================================================
# MODULE REPOSITORY
# ==============================================================================

class ModuleRepository(BaseRepository[Module]):
    """Repository for module management"""

    def create(self, module: Module) -> bool:
        try:
            data = self._model_to_dict(module)
            query = """
                    INSERT INTO modules 
                    (id, project_id, name, description, module_type, status, file_path,
                     dependencies, api_endpoints, database_tables, assigned_to, priority,
                     blocked_by, start_date, due_date, completed_at, estimated_hours,
                     actual_hours, completion_percentage, quality_score, test_coverage,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            params = (
                data.get('id'), data.get('project_id'), data.get('name'),
                data.get('description'), data.get('module_type', 'feature'),
                data.get('status', 'planned'), data.get('file_path'),
                dump_json_field(data.get('dependencies')),
                dump_json_field(data.get('api_endpoints')),
                dump_json_field(data.get('database_tables')),
                data.get('assigned_to'), data.get('priority', 'medium'),
                dump_json_field(data.get('blocked_by')),
                DateTimeHelper.to_iso_string(data.get('start_date')),
                DateTimeHelper.to_iso_string(data.get('due_date')),
                DateTimeHelper.to_iso_string(data.get('completed_at')),
                data.get('estimated_hours', 0.0),
                data.get('actual_hours', 0.0),
                data.get('completion_percentage', 0.0),
                data.get('quality_score', 0.0),
                data.get('test_coverage', 0.0),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating module: {e}")
            return False

    def get_by_id(self, module_id: str) -> Optional[Module]:
        try:
            query = "SELECT * FROM modules WHERE id = ?"
            results = self.db_manager.execute_query(query, (module_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting module {module_id}: {e}")
            return None

    def get_by_project_id(self, project_id: str) -> List[Module]:
        try:
            query = "SELECT * FROM modules WHERE project_id = ? ORDER BY created_at"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting modules for project {project_id}: {e}")
            return []

    def get_by_status(self, status: str) -> List[Module]:
        try:
            query = "SELECT * FROM modules WHERE status = ? ORDER BY created_at"
            results = self.db_manager.execute_query(query, (status,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting modules by status {status}: {e}")
            return []

    def get_active_modules(self, project_id: str) -> List[Module]:
        try:
            query = "SELECT * FROM modules WHERE project_id = ? AND status = 'in_progress' ORDER BY created_at"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting active modules for project {project_id}: {e}")
            return []

    def update(self, module: Module) -> bool:
        try:
            data = self._model_to_dict(module)
            query = """
                    UPDATE modules 
                    SET name = ?, description = ?, module_type = ?, status = ?,
                        file_path = ?, dependencies = ?, api_endpoints = ?,
                        database_tables = ?, assigned_to = ?, priority = ?,
                        blocked_by = ?, start_date = ?, due_date = ?, completed_at = ?,
                        estimated_hours = ?, actual_hours = ?, completion_percentage = ?,
                        quality_score = ?, test_coverage = ?, updated_at = ?
                    WHERE id = ?
                """
            params = (
                data.get('name'), data.get('description'), data.get('module_type'),
                data.get('status'), data.get('file_path'),
                dump_json_field(data.get('dependencies')),
                dump_json_field(data.get('api_endpoints')),
                dump_json_field(data.get('database_tables')),
                data.get('assigned_to'), data.get('priority'),
                dump_json_field(data.get('blocked_by')),
                DateTimeHelper.to_iso_string(data.get('start_date')),
                DateTimeHelper.to_iso_string(data.get('due_date')),
                DateTimeHelper.to_iso_string(data.get('completed_at')),
                data.get('estimated_hours'), data.get('actual_hours'),
                data.get('completion_percentage'), data.get('quality_score'),
                data.get('test_coverage'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating module: {e}")
            return False

    def delete(self, module_id: str) -> bool:
        try:
            query = "DELETE FROM modules WHERE id = ?"
            self.db_manager.execute_update(query, (module_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting module {module_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> Module:
        """Convert database row to Module model"""
        try:
            return Module(
                id=row.get('id', ''),
                project_id=row.get('project_id', ''),
                name=row.get('name', ''),
                description=row.get('description', ''),
                module_type=ModuleType(row.get('module_type', 'feature')),
                status=ModuleStatus(row.get('status', 'planned')),
                file_path=row.get('file_path', ''),
                dependencies=parse_json_field(row.get('dependencies'), []),
                api_endpoints=parse_json_field(row.get('api_endpoints'), []),
                database_tables=parse_json_field(row.get('database_tables'), []),
                assigned_to=row.get('assigned_to'),
                priority=Priority(row.get('priority', 'medium')),
                blocked_by=parse_json_field(row.get('blocked_by'), []),
                start_date=DateTimeHelper.from_iso_string(row.get('start_date')),
                due_date=DateTimeHelper.from_iso_string(row.get('due_date')),
                completed_at=DateTimeHelper.from_iso_string(row.get('completed_at')),
                estimated_hours=row.get('estimated_hours', 0.0),
                actual_hours=row.get('actual_hours', 0.0),
                completion_percentage=row.get('completion_percentage', 0.0),
                quality_score=row.get('quality_score', 0.0),
                test_coverage=row.get('test_coverage', 0.0),
                created_at=DateTimeHelper.from_iso_string(row.get('created_at')),
                updated_at=DateTimeHelper.from_iso_string(row.get('updated_at'))
            )
        except Exception as e:
            self.logger.error(f"Error converting row to Module: {e}")
            return Module()

    # ==============================================================================
    # TASK REPOSITORY
    # ==============================================================================


class TaskRepository(BaseRepository[Task]):
    """Repository for task management"""

    def create(self, task: Task) -> bool:
        try:
            data = self._model_to_dict(task)
            query = """
                    INSERT INTO tasks 
                    (id, module_id, project_id, title, description, status, priority,
                     assigned_to, dependencies, estimated_hours, actual_hours,
                     due_date, completed_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            params = (
                data.get('id'), data.get('module_id'), data.get('project_id'),
                data.get('title'), data.get('description'),
                data.get('status', 'todo'), data.get('priority', 'medium'),
                data.get('assigned_to'),
                dump_json_field(data.get('dependencies')),
                data.get('estimated_hours', 0.0),
                data.get('actual_hours', 0.0),
                DateTimeHelper.to_iso_string(data.get('due_date')),
                DateTimeHelper.to_iso_string(data.get('completed_at')),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating task: {e}")
            return False

    def get_by_id(self, task_id: str) -> Optional[Task]:
        try:
            query = "SELECT * FROM tasks WHERE id = ?"
            results = self.db_manager.execute_query(query, (task_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting task {task_id}: {e}")
            return None

    def get_by_project_id(self, project_id: str) -> List[Task]:
        try:
            query = "SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting tasks for project {project_id}: {e}")
            return []

    def get_by_module_id(self, module_id: str) -> List[Task]:
        try:
            query = "SELECT * FROM tasks WHERE module_id = ? ORDER BY created_at"
            results = self.db_manager.execute_query(query, (module_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting tasks for module {module_id}: {e}")
            return []

    def get_by_status(self, status: str) -> List[Task]:
        try:
            query = "SELECT * FROM tasks WHERE status = ? ORDER BY created_at"
            results = self.db_manager.execute_query(query, (status,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting tasks by status {status}: {e}")
            return []

    def update(self, task: Task) -> bool:
        try:
            data = self._model_to_dict(task)
            query = """
                    UPDATE tasks 
                    SET title = ?, description = ?, status = ?, priority = ?,
                        assigned_to = ?, dependencies = ?, estimated_hours = ?,
                        actual_hours = ?, due_date = ?, completed_at = ?, updated_at = ?
                    WHERE id = ?
                """
            params = (
                data.get('title'), data.get('description'), data.get('status'),
                data.get('priority'), data.get('assigned_to'),
                dump_json_field(data.get('dependencies')),
                data.get('estimated_hours'), data.get('actual_hours'),
                DateTimeHelper.to_iso_string(data.get('due_date')),
                DateTimeHelper.to_iso_string(data.get('completed_at')),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating task: {e}")
            return False

    def delete(self, task_id: str) -> bool:
        try:
            query = "DELETE FROM tasks WHERE id = ?"
            self.db_manager.execute_update(query, (task_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting task {task_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> Task:
        """Convert database row to Task model"""
        try:
            return Task(
                id=row.get('id', ''),
                module_id=row.get('module_id', ''),
                project_id=row.get('project_id', ''),
                title=row.get('title', ''),
                description=row.get('description', ''),
                status=TaskStatus(row.get('status', 'todo')),
                priority=Priority(row.get('priority', 'medium')),
                assigned_to=row.get('assigned_to'),
                dependencies=parse_json_field(row.get('dependencies'), []),
                estimated_hours=row.get('estimated_hours', 0.0),
                actual_hours=row.get('actual_hours', 0.0),
                due_date=DateTimeHelper.from_iso_string(row.get('due_date')),
                completed_at=DateTimeHelper.from_iso_string(row.get('completed_at')),
                created_at=DateTimeHelper.from_iso_string(row.get('created_at')),
                updated_at=DateTimeHelper.from_iso_string(row.get('updated_at'))
            )
        except Exception as e:
            self.logger.error(f"Error converting row to Task: {e}")
            return Task()


# ==============================================================================
# GENERATED CODEBASE REPOSITORY
# ==============================================================================

class GeneratedCodebaseRepository(BaseRepository[GeneratedCodebase]):
    """Repository for generated codebase management"""

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
                data.get('id'), data.get('project_id'), data.get('version', '1.0.0'),
                data.get('architecture_type'), data.get('total_lines_of_code', 0),
                data.get('total_files', 0), data.get('size_bytes', 0),
                data.get('code_quality_score', 0.0), data.get('test_coverage', 0.0),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
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
            query = "SELECT * FROM generated_codebases WHERE project_id = ? ORDER BY created_at DESC"
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
                SET version = ?, architecture_type = ?, total_lines_of_code = ?,
                    total_files = ?, size_bytes = ?, code_quality_score = ?,
                    test_coverage = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('version'), data.get('architecture_type'),
                data.get('total_lines_of_code'), data.get('total_files'),
                data.get('size_bytes'), data.get('code_quality_score'),
                data.get('test_coverage'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
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


# ==============================================================================
# GENERATED FILE REPOSITORY
# ==============================================================================

class GeneratedFileRepository(BaseRepository[GeneratedFile]):
    """Repository for generated file management"""

    def create(self, file: GeneratedFile) -> bool:
        try:
            data = self._model_to_dict(file)
            query = """
                INSERT INTO generated_files 
                (id, codebase_id, file_path, content, size_bytes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id'), data.get('codebase_id'), data.get('file_path'),
                data.get('content'), data.get('size_bytes', 0),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
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
            query = "SELECT * FROM generated_files WHERE codebase_id = ? ORDER BY file_path"
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
                SET content = ?, size_bytes = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('content'), data.get('size_bytes'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
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

    def _row_to_model(self, row: Dict[str, Any]) -> GeneratedFile:
        """Convert row with enum handling"""
        try:
            # Import FileType enum
            try:
                from src.models import FileType
            except ImportError:
                # Fallback if enum not available
                class FileType:
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

            # ✅ FIX: Convert string file_type back to enum
            file_type_str = row.get('file_type', 'python')
            file_type_map = {
                'python': FileType.PYTHON,
                'javascript': FileType.JAVASCRIPT,
                'typescript': FileType.TYPESCRIPT,
                'html': FileType.HTML,
                'css': FileType.CSS,
                'json': FileType.JSON,
                'yaml': FileType.YAML,
                'markdown': FileType.MARKDOWN,
                'sql': FileType.SQL,
                'dockerfile': FileType.DOCKERFILE,
                'config': FileType.CONFIG,
                'test': FileType.TEST
            }
            file_type = file_type_map.get(file_type_str, FileType.PYTHON)

            return GeneratedFile(
                id=row.get('id', ''),
                codebase_id=row.get('codebase_id', ''),
                project_id=row.get('project_id', ''),
                file_path=row.get('file_path', ''),
                file_type=file_type,  # ✅ Use mapped enum instead of string
                file_purpose=row.get('file_purpose', ''),
                content=row.get('content', ''),
                size_bytes=row.get('size_bytes', 0),
                line_count=row.get('line_count', 0),
                imports=parse_json_field(row.get('imports'), []),
                dependencies=parse_json_field(row.get('dependencies'), []),
                complexity_score=row.get('complexity_score', 0.0),
                test_coverage=row.get('test_coverage', 0.0),
                documentation_coverage=row.get('documentation_coverage', 0.0),
                syntax_errors=parse_json_field(row.get('syntax_errors'), []),
                style_issues=parse_json_field(row.get('style_issues'), []),
                security_issues=parse_json_field(row.get('security_issues'), []),
                generated_by_agent=row.get('generated_by_agent'),
                generation_metadata=parse_json_field(row.get('generation_metadata'), {}),
                created_at=DateTimeHelper.from_iso_string(row.get('created_at')),
                updated_at=DateTimeHelper.from_iso_string(row.get('updated_at'))
            )
        except Exception as e:
            self.logger.error(f"Error converting row to GeneratedFile: {e}")
            return GeneratedFile()


# ==============================================================================
# PROJECT COLLABORATOR REPOSITORY
# ==============================================================================

class ProjectCollaboratorRepository(BaseRepository[ProjectCollaborator]):
    """Repository for project collaborator management"""

    def create(self, collaborator: ProjectCollaborator) -> bool:
        try:
            data = self._model_to_dict(collaborator)
            query = """
                INSERT INTO project_collaborators 
                (id, project_id, user_id, role, permissions, joined_at, is_active, 
                 invitation_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id'), data.get('project_id'), data.get('user_id'),
                data.get('role', 'developer'),
                dump_json_field(data.get('permissions', [])),
                DateTimeHelper.to_iso_string(data.get('joined_at', DateTimeHelper.now())),
                1 if data.get('is_active', True) else 0,
                data.get('invitation_status', 'active'),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
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
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting collaborator {collaborator_id}: {e}")
            return None

    def get_by_project_id(self, project_id: str) -> List[ProjectCollaborator]:
        try:
            query = "SELECT * FROM project_collaborators WHERE project_id = ?"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting collaborators for project {project_id}: {e}")
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
                data.get('role'),
                dump_json_field(data.get('permissions')),
                1 if data.get('is_active', True) else 0,
                data.get('invitation_status'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
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

    def _row_to_model(self, row: Dict[str, Any]) -> ProjectCollaborator:
        """Convert row with JSON parsing"""
        try:
            # Import UserRole enum
            try:
                from src.models import UserRole
            except ImportError:
                # Fallback if enum not available
                class UserRole:
                    @staticmethod
                    def from_string(s):
                        return s

            return ProjectCollaborator(
                id=row.get('id', ''),
                project_id=row.get('project_id', ''),
                user_id=row.get('user_id', ''),
                role=UserRole(row.get('role', 'developer')) if hasattr(UserRole, '__call__') else row.get('role',
                                                                                                          'developer'),
                permissions=parse_json_field(row.get('permissions'), []),
                joined_at=DateTimeHelper.from_iso_string(row.get('joined_at')),
                is_active=bool(row.get('is_active', 1)),
                invitation_status=row.get('invitation_status', 'active'),
                created_at=DateTimeHelper.from_iso_string(row.get('created_at')),
                updated_at=DateTimeHelper.from_iso_string(row.get('updated_at'))
            )
        except Exception as e:
            self.logger.error(f"Error converting row to ProjectCollaborator: {e}")
            return ProjectCollaborator()


# ==============================================================================
# SOCRATIC SESSION REPOSITORY
# ==============================================================================

class SocraticSessionRepository(BaseRepository[SocraticSession]):
    """Repository for Socratic session management"""

    def create(self, session: SocraticSession) -> bool:
        try:
            data = self._model_to_dict(session)

            # ✅ FIX: Map model field to database field
            # Model has 'user_id' but database expects 'initiated_by'
            initiated_by = data.get('user_id', '')

            query = """
                INSERT INTO socratic_sessions 
                (id, project_id, initiated_by, session_type, status, current_phase,
                 total_questions, answered_questions, session_data, 
                 created_at, updated_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id'),
                data.get('project_id'),
                initiated_by,  # ✅ Use mapped field instead of data.get('initiated_by')
                data.get('session_type', 'discovery'),
                data.get('status', 'active'),
                data.get('current_phase', 'discovery'),
                data.get('total_questions', 0),
                data.get('answered_questions', 0),
                dump_json_field(data.get('session_data', {})),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('completed_at'))
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            return False

    def get_by_id(self, session_id: str) -> Optional[SocraticSession]:
        try:
            query = "SELECT * FROM socratic_sessions WHERE id = ?"
            results = self.db_manager.execute_query(query, (session_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting session {session_id}: {e}")
            return None

    def get_by_project_id(self, project_id: str) -> List[SocraticSession]:
        try:
            query = "SELECT * FROM socratic_sessions WHERE project_id = ? ORDER BY created_at DESC"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting sessions for project {project_id}: {e}")
            return []

    def get_by_user_id(self, user_id: str) -> List[SocraticSession]:
        try:
            query = "SELECT * FROM socratic_sessions WHERE initiated_by = ? ORDER BY created_at DESC"
            results = self.db_manager.execute_query(query, (user_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting sessions for user {user_id}: {e}")
            return []

    def update(self, session: SocraticSession) -> bool:
        try:
            data = self._model_to_dict(session)
            query = """
                UPDATE socratic_sessions 
                SET status = ?, current_phase = ?, total_questions = ?, 
                    answered_questions = ?, session_data = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
            """
            params = (
                data.get('status'), data.get('current_phase'),
                data.get('total_questions'), data.get('answered_questions'),
                dump_json_field(data.get('session_data')),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                DateTimeHelper.to_iso_string(data.get('completed_at')),
                data.get('id')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating session: {e}")
            return False

    def delete(self, session_id: str) -> bool:
        try:
            query = "DELETE FROM socratic_sessions WHERE id = ?"
            self.db_manager.execute_update(query, (session_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> SocraticSession:
        """Convert row with JSON and datetime parsing"""
        try:
            # Import enums
            try:
                from src.models import TechnicalRole, ConversationStatus
            except ImportError:
                # Fallback if enums not available
                class TechnicalRole:
                    @staticmethod
                    def from_string(s):
                        return s

                class ConversationStatus:
                    @staticmethod
                    def from_string(s):
                        return s

            # ✅ FIX: Map database phase values to valid TechnicalRole enum values
            phase_to_role_map = {
                'discovery': TechnicalRole.BUSINESS_ANALYST,
                'design': TechnicalRole.UX_DESIGNER,
                'development': TechnicalRole.BACKEND_DEVELOPER,
                'testing': TechnicalRole.QA_TESTER,
                'deployment': TechnicalRole.DEVOPS_ENGINEER,
                'project_manager': TechnicalRole.PROJECT_MANAGER,
                'business_analyst': TechnicalRole.BUSINESS_ANALYST,
                'frontend_developer': TechnicalRole.FRONTEND_DEVELOPER,
                'backend_developer': TechnicalRole.BACKEND_DEVELOPER,
                'ux_designer': TechnicalRole.UX_DESIGNER,
                'qa_tester': TechnicalRole.QA_TESTER,
                'devops_engineer': TechnicalRole.DEVOPS_ENGINEER,
                'security_engineer': TechnicalRole.SECURITY_ENGINEER
            }

            phase_value = row.get('current_phase', 'discovery')
            current_role = phase_to_role_map.get(phase_value, TechnicalRole.PROJECT_MANAGER)

            # ✅ FIX: Map database status values to valid ConversationStatus enum values
            status_value = row.get('status', 'active')
            status_map = {
                'active': ConversationStatus.ACTIVE,
                'paused': ConversationStatus.PAUSED,
                'completed': ConversationStatus.COMPLETED,
                'cancelled': ConversationStatus.CANCELLED
            }
            conversation_status = status_map.get(status_value, ConversationStatus.ACTIVE)

            return SocraticSession(
                id=row.get('id', ''),
                project_id=row.get('project_id', ''),
                user_id=row.get('initiated_by', ''),  # Map initiated_by to user_id
                current_role=current_role,  # ✅ Use mapped role instead of direct conversion
                status=conversation_status,  # ✅ Use mapped status instead of direct conversion
                roles_to_cover=parse_json_field(row.get('session_data', '{}'), {}).get('roles_to_cover', []),
                completed_roles=parse_json_field(row.get('session_data', '{}'), {}).get('completed_roles', []),
                total_questions=row.get('total_questions', 0),
                questions_answered=row.get('answered_questions', 0),
                insights_generated=parse_json_field(row.get('session_data', '{}'), {}).get('insights_generated', 0),
                conflicts_detected=parse_json_field(row.get('session_data', '{}'), {}).get('conflicts_detected', 0),
                session_notes=row.get('session_data', ''),
                quality_score=parse_json_field(row.get('session_data', '{}'), {}).get('quality_score', 0.0),
                completion_percentage=parse_json_field(row.get('session_data', '{}'), {}).get('completion_percentage',
                                                                                              0.0),
                created_at=DateTimeHelper.from_iso_string(row.get('created_at')),
                updated_at=DateTimeHelper.from_iso_string(row.get('updated_at'))
            )
        except Exception as e:
            self.logger.error(f"Error converting row to SocraticSession: {e}")
            return SocraticSession()


# ==============================================================================
# QUESTION REPOSITORY
# ==============================================================================

class QuestionRepository(BaseRepository[Question]):
    """Repository for question management"""

    def create(self, question: Question) -> bool:
        try:
            data = self._model_to_dict(question)

            question_number = data.get('question_number')
            if question_number is None:
                session_id = data.get('session_id')
                if session_id:
                    try:
                        # Use MAX instead of COUNT to avoid issues
                        max_query = "SELECT COALESCE(MAX(question_number), 0) FROM questions WHERE session_id = ?"
                        result = self.db_manager.execute_query(max_query, (session_id,))
                        max_num = result[0][0] if result and result[0] and result[0][0] is not None else 0
                        question_number = max_num + 1
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"Could not get max question_number for session {session_id}: {e}")
                        # Fallback to random number to avoid conflicts
                        import random
                        question_number = random.randint(1000, 9999)
                else:
                    question_number = 1

            query = """
                INSERT INTO questions 
                (id, session_id, question_number, phase, question_text, answer_text,
                 is_answered, context, created_at, updated_at, answered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id'),
                data.get('session_id'),
                question_number,  # ✅ Use generated question_number
                data.get('phase', 'discovery'),  # ✅ Provide default phase
                data.get('question_text'),
                data.get('answer_text'),
                1 if data.get('is_answered', False) else 0,
                data.get('context'),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('answered_at'))
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating question: {e}")
            return False

    def get_by_id(self, question_id: str) -> Optional[Question]:
        try:
            query = "SELECT * FROM questions WHERE id = ?"
            results = self.db_manager.execute_query(query, (question_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting question {question_id}: {e}")
            return None

    def get_by_session_id(self, session_id: str) -> List[Question]:
        try:
            query = "SELECT * FROM questions WHERE session_id = ? ORDER BY question_number"
            results = self.db_manager.execute_query(query, (session_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting questions for session {session_id}: {e}")
            return []

    def update(self, question: Question) -> bool:
        try:
            data = self._model_to_dict(question)
            query = """
                UPDATE questions 
                SET answer_text = ?, is_answered = ?, updated_at = ?, answered_at = ?
                WHERE id = ?
            """
            params = (
                data.get('answer_text'),
                1 if data.get('is_answered', False) else 0,
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                DateTimeHelper.to_iso_string(data.get('answered_at')),
                data.get('id')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating question: {e}")
            return False

    def delete(self, question_id: str) -> bool:
        try:
            query = "DELETE FROM questions WHERE id = ?"
            self.db_manager.execute_update(query, (question_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting question {question_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> Question:
        """Convert row with datetime parsing"""
        try:
            # Import TechnicalRole enum
            try:
                from src.models import TechnicalRole
            except ImportError:
                class TechnicalRole:
                    @staticmethod
                    def from_string(s):
                        return s

            # ✅ FIX: Map database phase values to valid TechnicalRole enum values
            phase_to_role_map = {
                'discovery': TechnicalRole.BUSINESS_ANALYST,
                'design': TechnicalRole.UX_DESIGNER,
                'development': TechnicalRole.BACKEND_DEVELOPER,
                'testing': TechnicalRole.QA_TESTER,
                'deployment': TechnicalRole.DEVOPS_ENGINEER,
                'project_manager': TechnicalRole.PROJECT_MANAGER,
                'business_analyst': TechnicalRole.BUSINESS_ANALYST,
                'frontend_developer': TechnicalRole.FRONTEND_DEVELOPER,
                'backend_developer': TechnicalRole.BACKEND_DEVELOPER,
                'ux_designer': TechnicalRole.UX_DESIGNER,
                'qa_tester': TechnicalRole.QA_TESTER,
                'devops_engineer': TechnicalRole.DEVOPS_ENGINEER,
                'security_engineer': TechnicalRole.SECURITY_ENGINEER
            }

            phase_value = row.get('phase', 'discovery')
            role = phase_to_role_map.get(phase_value, TechnicalRole.PROJECT_MANAGER)

            return Question(
                id=row.get('id', ''),
                session_id=row.get('session_id', ''),
                role=role,  # ✅ Use mapped role instead of direct conversion
                question_text=row.get('question_text', ''),
                context=row.get('context', ''),
                is_follow_up=False,  # Not in old schema
                parent_question_id=None,  # Not in old schema
                importance_score=0.5,  # Default value
                is_answered=bool(row.get('is_answered', 0)),
                answer_text=row.get('answer_text', ''),
                answer_quality_score=0.0,  # Default value
                generated_insights=[],  # Not in old schema
                detected_conflicts=[],  # Not in old schema
                recommended_follow_ups=[],  # Not in old schema
                created_at=DateTimeHelper.from_iso_string(row.get('created_at')),
                updated_at=DateTimeHelper.from_iso_string(row.get('updated_at'))
            )
        except Exception as e:
            self.logger.error(f"Error converting row to Question: {e}")
            return Question()


# ==============================================================================
# CONVERSATION MESSAGE REPOSITORY
# ==============================================================================

class ConversationMessageRepository(BaseRepository[ConversationMessage]):
    """Repository for conversation message management"""

    def create(self, message: ConversationMessage) -> bool:
        try:
            data = self._model_to_dict(message)
            query = """
                INSERT INTO conversation_messages 
                (id, session_id, project_id, timestamp, message_type, content, phase,
                 role, author, question_number, insights_extracted, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id'), data.get('session_id'), data.get('project_id'),
                DateTimeHelper.to_iso_string(data.get('timestamp', DateTimeHelper.now())),
                data.get('message_type'), data.get('content'), data.get('phase'),
                data.get('role'), data.get('author'), data.get('question_number'),
                dump_json_field(data.get('insights_extracted', {})),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating message: {e}")
            return False

    def get_by_id(self, message_id: str) -> Optional[ConversationMessage]:
        try:
            query = "SELECT * FROM conversation_messages WHERE id = ?"
            results = self.db_manager.execute_query(query, (message_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting message {message_id}: {e}")
            return None

    def get_by_session_id(self, session_id: str) -> List[ConversationMessage]:
        try:
            query = "SELECT * FROM conversation_messages WHERE session_id = ? ORDER BY timestamp"
            results = self.db_manager.execute_query(query, (session_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting messages for session {session_id}: {e}")
            return []

    def update(self, message: ConversationMessage) -> bool:
        try:
            data = self._model_to_dict(message)
            query = """
                UPDATE conversation_messages 
                SET insights_extracted = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                dump_json_field(data.get('insights_extracted')),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating message: {e}")
            return False

    def delete(self, message_id: str) -> bool:
        try:
            query = "DELETE FROM conversation_messages WHERE id = ?"
            self.db_manager.execute_update(query, (message_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting message {message_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> ConversationMessage:
        """Convert row with JSON and datetime parsing"""
        try:
            return ConversationMessage(
                id=row.get('id', ''),
                session_id=row.get('session_id', ''),
                project_id=row.get('project_id', ''),
                timestamp=DateTimeHelper.from_iso_string(row.get('timestamp')),
                message_type=row.get('message_type', 'user'),
                content=row.get('content', ''),
                phase=row.get('phase'),
                role=row.get('role'),
                author=row.get('author'),
                question_number=row.get('question_number'),
                insights_extracted=parse_json_field(row.get('insights_extracted'), {}),
                created_at=DateTimeHelper.from_iso_string(row.get('created_at')),
                updated_at=DateTimeHelper.from_iso_string(row.get('updated_at'))
            )
        except Exception as e:
            self.logger.error(f"Error converting row to ConversationMessage: {e}")
            return ConversationMessage()


# ==============================================================================
# TECHNICAL SPECIFICATION REPOSITORY
# ==============================================================================

class TechnicalSpecificationRepository(BaseRepository[TechnicalSpec]):
    """Repository for technical specification management"""

    def create(self, spec: TechnicalSpec) -> bool:
        try:
            data = self._model_to_dict(spec)
            query = """
                INSERT INTO technical_specifications 
                (id, project_id, session_id, version, architecture_type, technology_stack,
                 functional_requirements, non_functional_requirements, system_components,
                 data_models, api_specifications, performance_requirements,
                 security_requirements, scalability_requirements, deployment_strategy,
                 infrastructure_requirements, monitoring_requirements, testing_strategy,
                 acceptance_criteria, documentation_requirements, constraints,
                 is_approved, approved_by, approved_at, approval_notes,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id'), data.get('project_id'), data.get('session_id'),
                data.get('version', '1.0.0'), data.get('architecture_type'),
                dump_json_field(data.get('technology_stack')),
                dump_json_field(data.get('functional_requirements')),
                dump_json_field(data.get('non_functional_requirements')),
                dump_json_field(data.get('system_components')),
                dump_json_field(data.get('data_models')),
                dump_json_field(data.get('api_specifications')),
                dump_json_field(data.get('performance_requirements')),
                dump_json_field(data.get('security_requirements')),
                dump_json_field(data.get('scalability_requirements')),
                dump_json_field(data.get('deployment_strategy')),
                dump_json_field(data.get('infrastructure_requirements')),
                dump_json_field(data.get('monitoring_requirements')),
                dump_json_field(data.get('testing_strategy')),
                dump_json_field(data.get('acceptance_criteria')),
                dump_json_field(data.get('documentation_requirements')),
                dump_json_field(data.get('constraints')),
                1 if data.get('is_approved', False) else 0,
                data.get('approved_by'),
                DateTimeHelper.to_iso_string(data.get('approved_at')),
                data.get('approval_notes'),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating specification: {e}")
            return False

    def get_by_id(self, spec_id: str) -> Optional[TechnicalSpec]:
        try:
            query = "SELECT * FROM technical_specifications WHERE id = ?"
            results = self.db_manager.execute_query(query, (spec_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting specification {spec_id}: {e}")
            return None

    def get_by_project_id(self, project_id: str) -> List[TechnicalSpec]:
        try:
            query = "SELECT * FROM technical_specifications WHERE project_id = ? ORDER BY created_at DESC"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting specifications for project {project_id}: {e}")
            return []

    def get_latest(self, project_id: str) -> Optional[TechnicalSpec]:
        try:
            query = "SELECT * FROM technical_specifications WHERE project_id = ? ORDER BY created_at DESC LIMIT 1"
            results = self.db_manager.execute_query(query, (project_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting latest specification for project {project_id}: {e}")
            return None

    def update(self, spec: TechnicalSpec) -> bool:
        try:
            data = self._model_to_dict(spec)
            query = """
                UPDATE technical_specifications 
                SET version = ?, architecture_type = ?, technology_stack = ?,
                    functional_requirements = ?, non_functional_requirements = ?,
                    is_approved = ?, approved_by = ?, approved_at = ?, approval_notes = ?,
                    updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('version'),
                data.get('architecture_type'),
                dump_json_field(data.get('technology_stack')),
                dump_json_field(data.get('functional_requirements')),
                dump_json_field(data.get('non_functional_requirements')),
                1 if data.get('is_approved', False) else 0,
                data.get('approved_by'),
                DateTimeHelper.to_iso_string(data.get('approved_at')),
                data.get('approval_notes'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating specification: {e}")
            return False

    def delete(self, spec_id: str) -> bool:
        try:
            query = "DELETE FROM technical_specifications WHERE id = ?"
            self.db_manager.execute_update(query, (spec_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting specification {spec_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> TechnicalSpec:
        """Convert row with comprehensive JSON and datetime parsing"""
        try:
            return TechnicalSpec(
                id=row.get('id', ''),
                project_id=row.get('project_id', ''),
                session_id=row.get('session_id'),
                version=row.get('version', '1.0.0'),
                architecture_type=row.get('architecture_type', ''),
                technology_stack=parse_json_field(row.get('technology_stack'), {}),
                functional_requirements=parse_json_field(row.get('functional_requirements'), []),
                non_functional_requirements=parse_json_field(row.get('non_functional_requirements'), []),
                system_components=parse_json_field(row.get('system_components'), []),
                data_models=parse_json_field(row.get('data_models'), []),
                api_specifications=parse_json_field(row.get('api_specifications'), []),
                performance_requirements=parse_json_field(row.get('performance_requirements'), {}),
                security_requirements=parse_json_field(row.get('security_requirements'), []),
                scalability_requirements=parse_json_field(row.get('scalability_requirements'), {}),
                deployment_strategy=row.get('deployment_strategy', ''),
                infrastructure_requirements=parse_json_field(row.get('infrastructure_requirements'), {}),
                monitoring_requirements=parse_json_field(row.get('monitoring_requirements'), []),
                testing_strategy=parse_json_field(row.get('testing_strategy'), {}),
                acceptance_criteria=parse_json_field(row.get('acceptance_criteria'), []),
                documentation_requirements=parse_json_field(row.get('documentation_requirements'), []),
                is_approved=bool(row.get('is_approved', 0)),
                approved_by=row.get('approved_by'),
                approved_at=DateTimeHelper.from_iso_string(row.get('approved_at')),
                approval_notes=row.get('approval_notes', ''),
                created_at=DateTimeHelper.from_iso_string(row.get('created_at')),
                updated_at=DateTimeHelper.from_iso_string(row.get('updated_at'))
            )
        except Exception as e:
            self.logger.error(f"Error converting row to TechnicalSpec: {e}")
            return TechnicalSpec()


# ==============================================================================
# PROJECT CONTEXT REPOSITORY
# ==============================================================================

class ProjectContextRepository(BaseRepository[ProjectContext]):
    """Repository for project context analysis"""

    def create(self, context: ProjectContext) -> bool:
        try:
            data = self._model_to_dict(context)
            query = """
                INSERT INTO project_contexts 
                (id, project_id, business_domain, target_audience, business_goals,
                 existing_systems, integration_requirements, performance_requirements,
                 team_structure, budget_constraints, timeline_constraints,
                 last_analyzed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id'), data.get('project_id'), data.get('business_domain'),
                data.get('target_audience'),
                dump_json_field(data.get('business_goals')),
                dump_json_field(data.get('existing_systems')),
                dump_json_field(data.get('integration_requirements')),
                dump_json_field(data.get('performance_requirements')),
                dump_json_field(data.get('team_structure')),
                dump_json_field(data.get('budget_constraints')),
                dump_json_field(data.get('timeline_constraints')),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating project context: {e}")
            return False

    def get_by_id(self, context_id: str) -> Optional[ProjectContext]:
        try:
            query = "SELECT * FROM project_contexts WHERE id = ?"
            results = self.db_manager.execute_query(query, (context_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting project context {context_id}: {e}")
            return None

    def get_by_project_id(self, project_id: str) -> Optional[ProjectContext]:
        try:
            query = "SELECT * FROM project_contexts WHERE project_id = ?"
            results = self.db_manager.execute_query(query, (project_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting context for project {project_id}: {e}")
            return None

    def update(self, context: ProjectContext) -> bool:
        try:
            data = self._model_to_dict(context)
            query = """
                UPDATE project_contexts 
                SET business_domain = ?, target_audience = ?, business_goals = ?,
                    existing_systems = ?, integration_requirements = ?,
                    performance_requirements = ?, team_structure = ?,
                    budget_constraints = ?, timeline_constraints = ?,
                    last_analyzed_at = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('business_domain'), data.get('target_audience'),
                dump_json_field(data.get('business_goals')),
                dump_json_field(data.get('existing_systems')),
                dump_json_field(data.get('integration_requirements')),
                dump_json_field(data.get('performance_requirements')),
                dump_json_field(data.get('team_structure')),
                dump_json_field(data.get('budget_constraints')),
                dump_json_field(data.get('timeline_constraints')),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating project context: {e}")
            return False

    def upsert(self, context: ProjectContext) -> bool:
        """Update if exists, create if not"""
        existing = self.get_by_project_id(context.project_id)
        if existing:
            context.id = existing.id
            return self.update(context)
        return self.create(context)

    def delete(self, context_id: str) -> bool:
        try:
            query = "DELETE FROM project_contexts WHERE id = ?"
            self.db_manager.execute_update(query, (context_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting project context {context_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> ProjectContext:
        """Convert row with JSON and datetime parsing"""
        try:
            return ProjectContext(
                id=row.get('id', ''),
                project_id=row.get('project_id', ''),
                business_domain=row.get('business_domain', ''),
                target_audience=row.get('target_audience', ''),
                business_goals=parse_json_field(row.get('business_goals'), []),
                existing_systems=parse_json_field(row.get('existing_systems'), []),
                integration_requirements=parse_json_field(row.get('integration_requirements'), []),
                performance_requirements=parse_json_field(row.get('performance_requirements'), {}),
                team_structure=parse_json_field(row.get('team_structure'), {}),
                budget_constraints=parse_json_field(row.get('budget_constraints'), {}),
                timeline_constraints=parse_json_field(row.get('timeline_constraints'), {}),
                last_analyzed_at=DateTimeHelper.from_iso_string(row.get('last_analyzed_at')),
                created_at=DateTimeHelper.from_iso_string(row.get('created_at')),
                updated_at=DateTimeHelper.from_iso_string(row.get('updated_at'))
            )
        except Exception as e:
            self.logger.error(f"Error converting row to ProjectContext: {e}")
            return ProjectContext()


# ==============================================================================
# MODULE CONTEXT REPOSITORY
# ==============================================================================

class ModuleContextRepository(BaseRepository[ModuleContext]):
    """Repository for module context analysis"""

    def create(self, context: ModuleContext) -> bool:
        try:
            data = self._model_to_dict(context)
            query = """
                INSERT INTO module_contexts 
                (id, module_id, project_id, business_context, technical_context,
                 dependencies_context, related_modules, related_requirements,
                 related_constraints, last_analyzed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id'), data.get('module_id'), data.get('project_id'),
                data.get('business_context'), data.get('technical_context'),
                data.get('dependencies_context'),
                dump_json_field(data.get('related_modules')),
                dump_json_field(data.get('related_requirements')),
                dump_json_field(data.get('related_constraints')),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating module context: {e}")
            return False

    def get_by_id(self, context_id: str) -> Optional[ModuleContext]:
        try:
            query = "SELECT * FROM module_contexts WHERE id = ?"
            results = self.db_manager.execute_query(query, (context_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting module context {context_id}: {e}")
            return None

    def get_by_module_id(self, module_id: str) -> Optional[ModuleContext]:
        try:
            query = "SELECT * FROM module_contexts WHERE module_id = ?"
            results = self.db_manager.execute_query(query, (module_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting context for module {module_id}: {e}")
            return None

    def get_by_project_id(self, project_id: str) -> List[ModuleContext]:
        try:
            query = "SELECT * FROM module_contexts WHERE project_id = ?"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting module contexts for project {project_id}: {e}")
            return []

    def update(self, context: ModuleContext) -> bool:
        try:
            data = self._model_to_dict(context)
            query = """
                UPDATE module_contexts 
                SET business_context = ?, technical_context = ?, dependencies_context = ?,
                    related_modules = ?, related_requirements = ?, related_constraints = ?,
                    last_analyzed_at = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('business_context'), data.get('technical_context'),
                data.get('dependencies_context'),
                dump_json_field(data.get('related_modules')),
                dump_json_field(data.get('related_requirements')),
                dump_json_field(data.get('related_constraints')),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating module context: {e}")
            return False

    def upsert(self, context: ModuleContext) -> bool:
        """Update if exists, create if not"""
        existing = self.get_by_module_id(context.module_id)
        if existing:
            context.id = existing.id
            return self.update(context)
        return self.create(context)

    def delete(self, context_id: str) -> bool:
        try:
            query = "DELETE FROM module_contexts WHERE id = ?"
            self.db_manager.execute_update(query, (context_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting module context {context_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> ModuleContext:
        """Convert row with JSON and datetime parsing"""
        try:
            return ModuleContext(
                id=row.get('id', ''),
                module_id=row.get('module_id', ''),
                project_id=row.get('project_id', ''),
                business_context=row.get('business_context', ''),
                technical_context=row.get('technical_context', ''),
                dependencies_context=row.get('dependencies_context', ''),
                related_modules=parse_json_field(row.get('related_modules'), []),
                related_requirements=parse_json_field(row.get('related_requirements'), []),
                related_constraints=parse_json_field(row.get('related_constraints'), []),
                last_analyzed_at=DateTimeHelper.from_iso_string(row.get('last_analyzed_at')),
                created_at=DateTimeHelper.from_iso_string(row.get('created_at')),
                updated_at=DateTimeHelper.from_iso_string(row.get('updated_at'))
            )
        except Exception as e:
            self.logger.error(f"Error converting row to ModuleContext: {e}")
            return ModuleContext()


# ==============================================================================
# TASK CONTEXT REPOSITORY
# ==============================================================================

class TaskContextRepository(BaseRepository[TaskContext]):
    """Repository for task context analysis"""

    def create(self, context: TaskContext) -> bool:
        try:
            data = self._model_to_dict(context)
            query = """
                INSERT INTO task_contexts 
                (id, task_id, module_id, project_id, task_context,
                 implementation_notes, testing_requirements, prerequisite_tasks,
                 dependent_tasks, last_analyzed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                data.get('id'), data.get('task_id'), data.get('module_id'),
                data.get('project_id'), data.get('task_context'),
                data.get('implementation_notes'), data.get('testing_requirements'),
                dump_json_field(data.get('prerequisite_tasks')),
                dump_json_field(data.get('dependent_tasks')),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating task context: {e}")
            return False

    def get_by_id(self, context_id: str) -> Optional[TaskContext]:
        try:
            query = "SELECT * FROM task_contexts WHERE id = ?"
            results = self.db_manager.execute_query(query, (context_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting task context {context_id}: {e}")
            return None

    def get_by_task_id(self, task_id: str) -> Optional[TaskContext]:
        try:
            query = "SELECT * FROM task_contexts WHERE task_id = ?"
            results = self.db_manager.execute_query(query, (task_id,))
            return self._row_to_model(results[0]) if results else None
        except Exception as e:
            self.logger.error(f"Error getting context for task {task_id}: {e}")
            return None

    def get_by_module_id(self, module_id: str) -> List[TaskContext]:
        try:
            query = "SELECT * FROM task_contexts WHERE module_id = ?"
            results = self.db_manager.execute_query(query, (module_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting task contexts for module {module_id}: {e}")
            return []

    def get_by_project_id(self, project_id: str) -> List[TaskContext]:
        try:
            query = "SELECT * FROM task_contexts WHERE project_id = ?"
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting task contexts for project {project_id}: {e}")
            return []

    def update(self, context: TaskContext) -> bool:
        try:
            data = self._model_to_dict(context)
            query = """
                UPDATE task_contexts 
                SET task_context = ?, implementation_notes = ?, testing_requirements = ?,
                    prerequisite_tasks = ?, dependent_tasks = ?,
                    last_analyzed_at = ?, updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('task_context'), data.get('implementation_notes'),
                data.get('testing_requirements'),
                dump_json_field(data.get('prerequisite_tasks')),
                dump_json_field(data.get('dependent_tasks')),
                DateTimeHelper.to_iso_string(data.get('last_analyzed_at')),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating task context: {e}")
            return False

    def upsert(self, context: TaskContext) -> bool:
        """Update if exists, create if not"""
        existing = self.get_by_task_id(context.task_id)
        if existing:
            context.id = existing.id
            return self.update(context)
        return self.create(context)

    def delete(self, context_id: str) -> bool:
        try:
            query = "DELETE FROM task_contexts WHERE id = ?"
            self.db_manager.execute_update(query, (context_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting task context {context_id}: {e}")
            return False

    def _row_to_model(self, row: Dict[str, Any]) -> TaskContext:
        """Convert row with JSON and datetime parsing"""
        try:
            return TaskContext(
                id=row.get('id', ''),
                task_id=row.get('task_id', ''),
                module_id=row.get('module_id', ''),
                project_id=row.get('project_id', ''),
                task_context=row.get('task_context', ''),
                implementation_notes=row.get('implementation_notes', ''),
                testing_requirements=row.get('testing_requirements', ''),
                prerequisite_tasks=parse_json_field(row.get('prerequisite_tasks'), []),
                dependent_tasks=parse_json_field(row.get('dependent_tasks'), []),
                last_analyzed_at=DateTimeHelper.from_iso_string(row.get('last_analyzed_at')),
                created_at=DateTimeHelper.from_iso_string(row.get('created_at')),
                updated_at=DateTimeHelper.from_iso_string(row.get('updated_at'))
            )
        except Exception as e:
            self.logger.error(f"Error converting row to TaskContext: {e}")
            return TaskContext()


# ==============================================================================
# CONFLICT REPOSITORY
# ==============================================================================

class ConflictRepository(BaseRepository[Conflict]):
    """Repository for conflict management"""

    def create(self, conflict: Conflict) -> bool:
        try:
            data = self._model_to_dict(conflict)
            query = """
                INSERT INTO conflicts 
                (id, project_id, session_id, conflict_type, description, severity,
                 first_requirement, second_requirement, conflicting_roles, is_resolved,
                 resolution_strategy, resolution_notes, resolved_by, resolved_at,
                 affected_modules, estimated_impact_hours, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Get conflict_type value properly
            conflict_type_value = data.get('conflict_type')
            if hasattr(conflict_type_value, 'value'):
                conflict_type_value = conflict_type_value.value
            elif conflict_type_value is None:
                conflict_type_value = 'TECHNICAL'

            params = (
                data.get('id'),
                data.get('project_id'),
                data.get('session_id'),
                conflict_type_value,  # CHANGED THIS LINE
                data.get('description', ''),
                data.get('severity', 'medium'),
                data.get('first_requirement', ''),
                data.get('second_requirement', ''),
                dump_json_field(data.get('conflicting_roles', [])),
                1 if data.get('is_resolved', False) else 0,
                data.get('resolution_strategy', ''),
                data.get('resolution_notes', ''),
                data.get('resolved_by'),
                DateTimeHelper.to_iso_string(data.get('resolved_at')) if data.get('resolved_at') else None,
                dump_json_field(data.get('affected_modules', [])),
                data.get('estimated_impact_hours'),
                DateTimeHelper.to_iso_string(data.get('created_at', DateTimeHelper.now())),
                DateTimeHelper.to_iso_string(data.get('updated_at', DateTimeHelper.now()))
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error creating conflict: {e}")
            return False

    def get_by_id(self, conflict_id: str) -> Optional[Conflict]:
        try:
            query = """
                SELECT id, project_id, session_id, conflict_type, description, severity,
                       first_requirement, second_requirement, conflicting_roles, is_resolved,
                       resolution_strategy, resolution_notes, resolved_by, resolved_at,
                       affected_modules, estimated_impact_hours, created_at, updated_at
                FROM conflicts WHERE id = ?
            """
            results = self.db_manager.execute_query(query, (conflict_id,))

            if not results:
                return None

            # Debug: Check what we got
            self.logger.info(f"Query returned {len(results)} results")
            self.logger.info(f"First result type: {type(results[0])}")
            self.logger.info(f"First result: {results[0]}")

            return self._row_to_model(results[0])
        except Exception as e:
            self.logger.error(f"Error getting conflict {conflict_id}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def get_by_project_id(self, project_id: str) -> List[Conflict]:
        try:
            query = """
                SELECT id, project_id, session_id, conflict_type, description, severity,
                       first_requirement, second_requirement, conflicting_roles, is_resolved,
                       resolution_strategy, resolution_notes, resolved_by, resolved_at,
                       affected_modules, estimated_impact_hours, created_at, updated_at
                FROM conflicts WHERE project_id = ? ORDER BY created_at DESC
            """
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting conflicts for project {project_id}: {e}")
            return []

    def get_by_session_id(self, session_id: str) -> List[Conflict]:
        try:
            query = """
                SELECT id, project_id, session_id, conflict_type, description, severity,
                       first_requirement, second_requirement, conflicting_roles, is_resolved,
                       resolution_strategy, resolution_notes, resolved_by, resolved_at,
                       affected_modules, estimated_impact_hours, created_at, updated_at
                FROM conflicts WHERE session_id = ? ORDER BY created_at DESC
            """
            results = self.db_manager.execute_query(query, (session_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting conflicts for session {session_id}: {e}")
            return []

    def get_unresolved(self, project_id: str) -> List[Conflict]:
        try:
            query = """
                SELECT id, project_id, session_id, conflict_type, description, severity,
                       first_requirement, second_requirement, conflicting_roles, is_resolved,
                       resolution_strategy, resolution_notes, resolved_by, resolved_at,
                       affected_modules, estimated_impact_hours, created_at, updated_at
                FROM conflicts WHERE project_id = ? AND is_resolved = 0 
                ORDER BY severity DESC, created_at DESC
            """
            results = self.db_manager.execute_query(query, (project_id,))
            return [self._row_to_model(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting unresolved conflicts for project {project_id}: {e}")
            return []

    def mark_resolved(self, conflict_id: str, resolution: str, resolved_by: str = None) -> bool:
        try:
            query = """
                UPDATE conflicts 
                SET is_resolved = 1, 
                    resolution_notes = ?,
                    resolved_by = ?,
                    resolved_at = ?,
                    updated_at = ?
                WHERE id = ?
            """
            params = (
                resolution,
                resolved_by,
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                conflict_id
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error marking conflict {conflict_id} as resolved: {e}")
            return False

    def update(self, conflict: Conflict) -> bool:
        try:
            data = self._model_to_dict(conflict)
            query = """
                UPDATE conflicts 
                SET description = ?,
                    severity = ?,
                    first_requirement = ?,
                    second_requirement = ?,
                    conflicting_roles = ?,
                    is_resolved = ?,
                    resolution_strategy = ?,
                    resolution_notes = ?,
                    resolved_by = ?,
                    resolved_at = ?,
                    affected_modules = ?,
                    estimated_impact_hours = ?,
                    updated_at = ?
                WHERE id = ?
            """
            params = (
                data.get('description'),
                data.get('severity'),
                data.get('first_requirement'),
                data.get('second_requirement'),
                dump_json_field(data.get('conflicting_roles', [])),
                1 if data.get('is_resolved', False) else 0,
                data.get('resolution_strategy'),
                data.get('resolution_notes'),
                data.get('resolved_by'),
                DateTimeHelper.to_iso_string(data.get('resolved_at')) if data.get('resolved_at') else None,
                dump_json_field(data.get('affected_modules', [])),
                data.get('estimated_impact_hours'),
                DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                data.get('id')
            )
            self.db_manager.execute_update(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Error updating conflict: {e}")
            return False

    def delete(self, conflict_id: str) -> bool:
        try:
            query = "DELETE FROM conflicts WHERE id = ?"
            self.db_manager.execute_update(query, (conflict_id,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting conflict {conflict_id}: {e}")
            return False

    def _row_to_model(self, row) -> Conflict:
        """Convert database row to Conflict model"""
        from dataclasses import dataclass
        if not CORE_AVAILABLE:
            # Fallback model
            @dataclass
            class Conflict:
                id: str = ""
                project_id: str = ""

        from src.models import Conflict, ConflictType

        # Handle both dict and tuple formats
        if isinstance(row, dict):
            return Conflict(
                id=row['id'],
                project_id=row['project_id'],
                session_id=row['session_id'] if row['session_id'] else "",
                conflict_type=ConflictType(row['conflict_type']) if row['conflict_type'] else ConflictType.TECHNICAL,
                description=row['description'] if row['description'] else "",
                severity=row['severity'] if row['severity'] else "medium",
                first_requirement=row['first_requirement'] if row['first_requirement'] else "",
                second_requirement=row['second_requirement'] if row['second_requirement'] else "",
                conflicting_roles=load_json_field(row['conflicting_roles'], []),
                is_resolved=bool(row['is_resolved']),
                resolution_strategy=row['resolution_strategy'] if row['resolution_strategy'] else "",
                resolution_notes=row['resolution_notes'] if row['resolution_notes'] else "",
                resolved_by=row['resolved_by'] if row['resolved_by'] else None,
                resolved_at=DateTimeHelper.from_iso_string(row['resolved_at']) if row['resolved_at'] else None,
                affected_modules=load_json_field(row['affected_modules'], []),
                estimated_impact_hours=row['estimated_impact_hours'] if row['estimated_impact_hours'] else None,
                created_at=DateTimeHelper.from_iso_string(row['created_at']),
                updated_at=DateTimeHelper.from_iso_string(row['updated_at'])
            )
        else:
            # Tuple format - access by index
            r = row  # Alias to make it clear this is tuple/list
            return Conflict(
                id=r[0],
                project_id=r[1],
                session_id=r[2] if r[2] else "",
                conflict_type=ConflictType(r[3]) if r[3] else ConflictType.TECHNICAL,
                description=r[4] if r[4] else "",
                severity=r[5] if r[5] else "medium",
                first_requirement=r[6] if r[6] else "",
                second_requirement=r[7] if r[7] else "",
                conflicting_roles=load_json_field(r[8], []),
                is_resolved=bool(r[9]),
                resolution_strategy=r[10] if r[10] else "",
                resolution_notes=r[11] if r[11] else "",
                resolved_by=r[12] if r[12] else None,
                resolved_at=DateTimeHelper.from_iso_string(r[13]) if r[13] else None,
                affected_modules=load_json_field(r[14], []),
                estimated_impact_hours=r[15] if r[15] else None,
                created_at=DateTimeHelper.from_iso_string(r[16]),
                updated_at=DateTimeHelper.from_iso_string(r[17])
            )
