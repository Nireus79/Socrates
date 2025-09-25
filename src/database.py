#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Database Layer
======================================

Database management with SQLite backend, repositories for all models,
and migration system. Provides clean abstraction over database operations.

Uses repository pattern for each core model with proper transaction support.
"""

import sqlite3
import json
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from dataclasses import asdict

from src.core import (
    get_logger, get_db_manager, DateTimeHelper,
    DatabaseError, ValidationError
)
from src.models import (
    Project, Module, GeneratedFile, TestResult, User,
    Collaborator, ProjectPhase, ProjectStatus,
    ModuleStatus, ModuleType, FileStatus, FileType, TestStatus, TestType,
    UserRole, Priority, RiskLevel
)


# ============================================================================
# DATABASE SCHEMA MANAGEMENT
# ============================================================================

class DatabaseSchema:
    """Manages database schema creation and migrations"""

    def __init__(self):
        self.logger = get_logger('database.schema')
        self.current_version = 1

    def initialize_schema(self, conn: sqlite3.Connection) -> None:
        """Initialize database schema with all tables"""
        cursor = conn.cursor()

        try:
            # Create schema version table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL,
                    description TEXT
                )
            ''')

            # Check current schema version
            cursor.execute('SELECT MAX(version) FROM schema_version')
            current_version = cursor.fetchone()[0] or 0

            if current_version < self.current_version:
                self._create_initial_schema(cursor)

                # Record schema version
                cursor.execute('''
                    INSERT OR REPLACE INTO schema_version (version, applied_at, description)
                    VALUES (?, ?, ?)
                ''', (self.current_version, DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                      "Initial schema"))

                conn.commit()
                self.logger.info(f"Database schema initialized to version {self.current_version}")

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to initialize schema: {e}")
            raise DatabaseError(f"Schema initialization failed: {e}")

    def _create_initial_schema(self, cursor: sqlite3.Cursor) -> None:
        """Create all initial database tables"""

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                full_name TEXT,
                passcode_hash TEXT NOT NULL,
                roles TEXT NOT NULL, -- JSON array
                projects TEXT NOT NULL DEFAULT '[]', -- JSON array of project IDs
                preferences TEXT NOT NULL DEFAULT '{}', -- JSON object
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_login TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_archived BOOLEAN DEFAULT 0,
                archived_at TEXT
            )
        ''')

        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                owner TEXT NOT NULL,
                phase TEXT NOT NULL DEFAULT 'discovery',
                status TEXT NOT NULL DEFAULT 'active',
                priority TEXT NOT NULL DEFAULT 'medium',
                goals TEXT DEFAULT '',
                requirements TEXT DEFAULT '[]', -- JSON array
                constraints TEXT DEFAULT '[]', -- JSON array
                tech_stack TEXT DEFAULT '[]', -- JSON array
                language_preferences TEXT DEFAULT '[]', -- JSON array
                deployment_target TEXT DEFAULT 'local',
                architecture_pattern TEXT DEFAULT '',
                generated_codebase_id TEXT,
                file_structure TEXT DEFAULT '{}', -- JSON object
                progress_percentage REAL DEFAULT 0.0,
                quality_score REAL DEFAULT 0.0,
                estimated_hours INTEGER DEFAULT 0,
                actual_hours INTEGER DEFAULT 0,
                risk_level TEXT DEFAULT 'low',
                risk_indicators TEXT DEFAULT '[]', -- JSON array
                issues TEXT DEFAULT '[]', -- JSON array
                context_summary TEXT DEFAULT '{}', -- JSON object
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                archived_at TEXT,
                is_archived BOOLEAN DEFAULT 0,
                FOREIGN KEY (owner) REFERENCES users(username)
            )
        ''')

        # Project collaborators table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_collaborators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                permissions TEXT DEFAULT '[]', -- JSON array
                joined_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                FOREIGN KEY (username) REFERENCES users(username),
                UNIQUE(project_id, username)
            )
        ''')

        # Modules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                module_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                module_type TEXT NOT NULL DEFAULT 'backend',
                phase TEXT NOT NULL DEFAULT 'discovery',
                status TEXT NOT NULL DEFAULT 'not_started',
                priority TEXT NOT NULL DEFAULT 'medium',
                tasks TEXT DEFAULT '[]', -- JSON array
                assigned_roles TEXT DEFAULT '[]', -- JSON array
                assigned_users TEXT DEFAULT '[]', -- JSON array
                dependencies TEXT DEFAULT '[]', -- JSON array
                blocks TEXT DEFAULT '[]', -- JSON array
                generated_files TEXT DEFAULT '[]', -- JSON array of file IDs
                progress_percentage REAL DEFAULT 0.0,
                estimated_hours INTEGER DEFAULT 0,
                actual_hours INTEGER DEFAULT 0,
                risk_level TEXT DEFAULT 'low',
                code_quality_score REAL DEFAULT 0.0,
                test_coverage REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            )
        ''')

        # Generated files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_files (
                file_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                module_id TEXT,
                codebase_id TEXT,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_purpose TEXT DEFAULT '',
                content TEXT DEFAULT '',
                content_hash TEXT DEFAULT '',
                size_bytes INTEGER DEFAULT 0,
                generated_by_agent TEXT DEFAULT '',
                generation_prompt TEXT DEFAULT '',
                generation_context TEXT DEFAULT '{}', -- JSON object
                dependencies TEXT DEFAULT '[]', -- JSON array
                dependents TEXT DEFAULT '[]', -- JSON array
                related_files TEXT DEFAULT '[]', -- JSON array
                status TEXT NOT NULL DEFAULT 'generating',
                has_errors BOOLEAN DEFAULT 0,
                error_messages TEXT DEFAULT '[]', -- JSON array
                warnings TEXT DEFAULT '[]', -- JSON array
                complexity_score REAL DEFAULT 0.0,
                maintainability_score REAL DEFAULT 0.0,
                test_coverage REAL DEFAULT 0.0,
                lines_of_code INTEGER DEFAULT 0,
                documentation TEXT DEFAULT '',
                comments_ratio REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_generated TEXT NOT NULL,
                last_tested TEXT,
                deployed_at TEXT,
                version TEXT DEFAULT '1.0',
                git_hash TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                FOREIGN KEY (module_id) REFERENCES modules(module_id) ON DELETE SET NULL
            )
        ''')

        # Test results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                test_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                module_id TEXT,
                codebase_id TEXT,
                test_type TEXT NOT NULL DEFAULT 'unit',
                test_suite TEXT DEFAULT '',
                test_framework TEXT DEFAULT 'pytest',
                files_tested TEXT DEFAULT '[]', -- JSON array
                test_files TEXT DEFAULT '[]', -- JSON array
                status TEXT NOT NULL DEFAULT 'pending',
                passed BOOLEAN DEFAULT 0,
                total_tests INTEGER DEFAULT 0,
                passed_tests INTEGER DEFAULT 0,
                failed_tests INTEGER DEFAULT 0,
                skipped_tests INTEGER DEFAULT 0,
                error_tests INTEGER DEFAULT 0,
                coverage_percentage REAL DEFAULT 0.0,
                line_coverage REAL DEFAULT 0.0,
                branch_coverage REAL DEFAULT 0.0,
                function_coverage REAL DEFAULT 0.0,
                execution_time_seconds REAL DEFAULT 0.0,
                memory_usage_mb REAL DEFAULT 0.0,
                cpu_usage_percent REAL DEFAULT 0.0,
                test_cases TEXT DEFAULT '[]', -- JSON array
                failure_details TEXT DEFAULT '[]', -- JSON array
                error_details TEXT DEFAULT '[]', -- JSON array
                code_quality_score REAL DEFAULT 0.0,
                maintainability_score REAL DEFAULT 0.0,
                complexity_warnings TEXT DEFAULT '[]', -- JSON array
                security_issues TEXT DEFAULT '[]', -- JSON array
                performance_issues TEXT DEFAULT '[]', -- JSON array
                optimization_suggestions TEXT DEFAULT '[]', -- JSON array
                test_environment TEXT DEFAULT '{}', -- JSON object
                python_version TEXT DEFAULT '',
                node_version TEXT DEFAULT '',
                browser_info TEXT DEFAULT '{}', -- JSON object
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                exit_code INTEGER DEFAULT 0,
                stdout TEXT DEFAULT '',
                stderr TEXT DEFAULT '',
                command_line TEXT DEFAULT '',
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                FOREIGN KEY (module_id) REFERENCES modules(module_id) ON DELETE SET NULL
            )
        ''')

        # Conversation messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_messages (
                message_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'user',
                content TEXT NOT NULL,
                phase TEXT NOT NULL DEFAULT 'discovery',
                role TEXT,
                author TEXT,
                question_number INTEGER,
                insights_extracted TEXT DEFAULT '{}', -- JSON object
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            )
        ''')

        # Technical specifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS technical_specifications (
                project_id TEXT PRIMARY KEY,
                database_schema TEXT DEFAULT '{}', -- JSON object
                api_design TEXT DEFAULT '{}', -- JSON object
                file_structure TEXT DEFAULT '{}', -- JSON object
                component_architecture TEXT DEFAULT '{}', -- JSON object
                implementation_plan TEXT DEFAULT '[]', -- JSON array
                test_requirements TEXT DEFAULT '[]', -- JSON array
                deployment_config TEXT DEFAULT '{}', -- JSON object
                dependencies TEXT DEFAULT '[]', -- JSON array
                environment_variables TEXT DEFAULT '{}', -- JSON object
                security_requirements TEXT DEFAULT '[]', -- JSON array
                performance_requirements TEXT DEFAULT '{}', -- JSON object
                architecture_pattern TEXT DEFAULT '',
                code_style_guide TEXT DEFAULT '{}', -- JSON object
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                version TEXT DEFAULT '1.0',
                FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
            )
        ''')

        # Create indexes for performance
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner)',
            'CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)',
            'CREATE INDEX IF NOT EXISTS idx_modules_project ON modules(project_id)',
            'CREATE INDEX IF NOT EXISTS idx_modules_status ON modules(status)',
            'CREATE INDEX IF NOT EXISTS idx_files_project ON generated_files(project_id)',
            'CREATE INDEX IF NOT EXISTS idx_files_module ON generated_files(module_id)',
            'CREATE INDEX IF NOT EXISTS idx_files_status ON generated_files(status)',
            'CREATE INDEX IF NOT EXISTS idx_tests_project ON test_results(project_id)',
            'CREATE INDEX IF NOT EXISTS idx_tests_status ON test_results(status)',
            'CREATE INDEX IF NOT EXISTS idx_messages_project ON conversation_messages(project_id)',
            'CREATE INDEX IF NOT EXISTS idx_collaborators_project ON project_collaborators(project_id)',
            'CREATE INDEX IF NOT EXISTS idx_collaborators_user ON project_collaborators(username)',
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)


# ============================================================================
# BASE REPOSITORY CLASS
# ============================================================================

class BaseRepository:
    """Base repository class with common database operations"""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.logger = get_logger(f'db.{table_name}')
        self.db_manager = get_db_manager()

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        with self.db_manager.get_db_session() as conn:
            yield conn

    def _serialize_json_field(self, value: Any) -> str:
        """Serialize Python object to JSON string"""
        if value is None:
            return '[]' if isinstance(value, list) else '{}'
        return json.dumps(value, default=str, ensure_ascii=False)

    def _deserialize_json_field(self, value: str, default_type: type = dict) -> Any:
        """Deserialize JSON string to Python object"""
        if not value:
            return [] if default_type == list else {}
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return [] if default_type == list else {}

    def _convert_datetime_fields(self, data: Dict[str, Any], datetime_fields: List[str]) -> None:
        """Convert datetime objects to ISO strings for database storage"""
        for field in datetime_fields:
            if field in data and data[field] is not None:
                if hasattr(data[field], 'isoformat'):
                    data[field] = DateTimeHelper.to_iso_string(data[field])


# ============================================================================
# USER REPOSITORY
# ============================================================================

class UserRepository(BaseRepository):
    """Repository for user management"""

    def __init__(self):
        super().__init__('users')

    def create(self, user: User) -> bool:
        """Create a new user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                user_data = asdict(user)
                self._convert_datetime_fields(user_data, ['created_at', 'updated_at', 'last_login', 'archived_at'])

                cursor.execute('''
                    INSERT INTO users (username, email, full_name, passcode_hash, roles, projects,
                                     preferences, created_at, updated_at, last_login, is_active, 
                                     is_archived, archived_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_data['username'], user_data['email'], user_data['full_name'],
                    user_data['passcode_hash'], self._serialize_json_field([role.value for role in user.roles]),
                    self._serialize_json_field(user_data['projects']),
                    self._serialize_json_field(user_data['preferences']),
                    user_data['created_at'], user_data['updated_at'], user_data['last_login'],
                    user_data['is_active'], user_data['is_archived'], user_data['archived_at']
                ))

                self.logger.info(f"Created user: {user.username}")
                return True

        except sqlite3.IntegrityError as e:
            self.logger.error(f"User creation failed - integrity error: {e}")
            raise ValidationError(f"User {user.username} already exists")
        except Exception as e:
            self.logger.error(f"Failed to create user {user.username}: {e}")
            raise DatabaseError(f"User creation failed: {e}")

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                row = cursor.fetchone()

                if row:
                    return self._row_to_user(row)
                return None

        except Exception as e:
            self.logger.error(f"Failed to get user {username}: {e}")
            raise DatabaseError(f"User lookup failed: {e}")

    def update(self, user: User) -> bool:
        """Update existing user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                user_data = asdict(user)
                user_data['updated_at'] = DateTimeHelper.to_iso_string(DateTimeHelper.now())
                self._convert_datetime_fields(user_data, ['created_at', 'updated_at', 'last_login', 'archived_at'])

                cursor.execute('''
                    UPDATE users SET email=?, full_name=?, passcode_hash=?, roles=?, projects=?,
                                    preferences=?, updated_at=?, last_login=?, is_active=?, 
                                    is_archived=?, archived_at=?
                    WHERE username=?
                ''', (
                    user_data['email'], user_data['full_name'], user_data['passcode_hash'],
                    self._serialize_json_field([role.value for role in user.roles]),
                    self._serialize_json_field(user_data['projects']),
                    self._serialize_json_field(user_data['preferences']),
                    user_data['updated_at'], user_data['last_login'], user_data['is_active'],
                    user_data['is_archived'], user_data['archived_at'], user_data['username']
                ))

                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to update user {user.username}: {e}")
            raise DatabaseError(f"User update failed: {e}")

    def delete(self, username: str) -> bool:
        """Delete user (hard delete)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE username = ?', (username,))
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to delete user {username}: {e}")
            raise DatabaseError(f"User deletion failed: {e}")

    def exists(self, username: str) -> bool:
        """Check if user exists"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
                return cursor.fetchone() is not None

        except Exception as e:
            self.logger.error(f"Failed to check user existence {username}: {e}")
            return False

    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convert database row to User object"""
        roles = [UserRole(role) for role in self._deserialize_json_field(row['roles'], list)]

        return User(
            username=row['username'],
            email=row['email'],
            full_name=row['full_name'],
            passcode_hash=row['passcode_hash'],
            roles=roles,
            projects=self._deserialize_json_field(row['projects'], list),
            preferences=self._deserialize_json_field(row['preferences']),
            created_at=DateTimeHelper.from_iso_string(row['created_at']) if row['created_at'] else DateTimeHelper.now(),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at']) if row['updated_at'] else DateTimeHelper.now(),
            last_login=DateTimeHelper.from_iso_string(row['last_login']) if row['last_login'] else None,
            is_active=bool(row['is_active']),
            is_archived=bool(row['is_archived']),
            archived_at=DateTimeHelper.from_iso_string(row['archived_at']) if row['archived_at'] else None
        )


# ============================================================================
# PROJECT REPOSITORY
# ============================================================================

class ProjectRepository(BaseRepository):
    """Repository for project management"""

    def __init__(self):
        super().__init__('projects')
        self.collaborator_repo = ProjectCollaboratorRepository()

    def create(self, project: Project) -> bool:
        """Create a new project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                project_data = asdict(project)
                self._convert_datetime_fields(project_data,
                                              ['created_at', 'updated_at', 'completed_at', 'archived_at'])

                cursor.execute('''
                    INSERT INTO projects (project_id, name, description, owner, phase, status, priority,
                                        goals, requirements, constraints, tech_stack, language_preferences,
                                        deployment_target, architecture_pattern, generated_codebase_id,
                                        file_structure, progress_percentage, quality_score, estimated_hours,
                                        actual_hours, risk_level, risk_indicators, issues, context_summary,
                                        created_at, updated_at, completed_at, archived_at, is_archived)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_data['project_id'], project_data['name'], project_data['description'],
                    project_data['owner'], project.phase.value, project.status.value, project.priority.value,
                    project_data['goals'], self._serialize_json_field(project_data['requirements']),
                    self._serialize_json_field(project_data['constraints']),
                    self._serialize_json_field(project_data['tech_stack']),
                    self._serialize_json_field(project_data['language_preferences']), project_data['deployment_target'],
                    project_data['architecture_pattern'], project_data['generated_codebase_id'],
                    self._serialize_json_field(project_data['file_structure']), project_data['progress_percentage'],
                    project_data['quality_score'], project_data['estimated_hours'], project_data['actual_hours'],
                    project.risk_level.value, self._serialize_json_field(project_data['risk_indicators']),
                    self._serialize_json_field(project_data['issues']),
                    self._serialize_json_field(project_data['context_summary']),
                    project_data['created_at'], project_data['updated_at'], project_data['completed_at'],
                    project_data['archived_at'], project_data['is_archived']
                ))

                # Create collaborator entries
                for collaborator in project.collaborators:
                    self.collaborator_repo.add_collaborator(project.project_id, collaborator)

                self.logger.info(f"Created project: {project.name} ({project.project_id})")
                return True

        except Exception as e:
            self.logger.error(f"Failed to create project {project.name}: {e}")
            raise DatabaseError(f"Project creation failed: {e}")

    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM projects WHERE project_id = ?', (project_id,))
                row = cursor.fetchone()

                if row:
                    project = self._row_to_project(row)
                    # Load collaborators
                    project.collaborators = self.collaborator_repo.get_project_collaborators(project_id)
                    return project
                return None

        except Exception as e:
            self.logger.error(f"Failed to get project {project_id}: {e}")
            raise DatabaseError(f"Project lookup failed: {e}")

    def get_user_projects(self, username: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Get projects where user is owner or collaborator"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Build WHERE clause
                where_clause = "WHERE (p.owner = ? OR pc.username = ?)"
                params = [username, username]

                if not include_archived:
                    where_clause += " AND p.is_archived = 0"

                cursor.execute(f'''
                    SELECT DISTINCT p.project_id, p.name, p.phase, p.status, p.updated_at, p.is_archived
                    FROM projects p
                    LEFT JOIN project_collaborators pc ON p.project_id = pc.project_id
                    {where_clause}
                    ORDER BY p.updated_at DESC
                ''', params)

                projects = []
                for row in cursor.fetchall():
                    projects.append({
                        'project_id': row['project_id'],
                        'name': row['name'],
                        'phase': row['phase'],
                        'status': 'archived' if row['is_archived'] else row['status'],
                        'updated_at': row['updated_at']
                    })

                return projects

        except Exception as e:
            self.logger.error(f"Failed to get user projects for {username}: {e}")
            raise DatabaseError(f"User projects lookup failed: {e}")

    def update(self, project: Project) -> bool:
        """Update existing project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                project_data = asdict(project)
                project_data['updated_at'] = DateTimeHelper.to_iso_string(DateTimeHelper.now())
                self._convert_datetime_fields(project_data,
                                              ['created_at', 'updated_at', 'completed_at', 'archived_at'])

                cursor.execute('''
                    UPDATE projects SET name=?, description=?, owner=?, phase=?, status=?, priority=?,
                                      goals=?, requirements=?, constraints=?, tech_stack=?, language_preferences=?,
                                      deployment_target=?, architecture_pattern=?, generated_codebase_id=?,
                                      file_structure=?, progress_percentage=?, quality_score=?, estimated_hours=?,
                                      actual_hours=?, risk_level=?, risk_indicators=?, issues=?, context_summary=?,
                                      updated_at=?, completed_at=?, archived_at=?, is_archived=?
                    WHERE project_id=?
                ''', (
                    project_data['name'], project_data['description'], project_data['owner'],
                    project.phase.value, project.status.value, project.priority.value,
                    project_data['goals'], self._serialize_json_field(project_data['requirements']),
                    self._serialize_json_field(project_data['constraints']),
                    self._serialize_json_field(project_data['tech_stack']),
                    self._serialize_json_field(project_data['language_preferences']), project_data['deployment_target'],
                    project_data['architecture_pattern'], project_data['generated_codebase_id'],
                    self._serialize_json_field(project_data['file_structure']), project_data['progress_percentage'],
                    project_data['quality_score'], project_data['estimated_hours'], project_data['actual_hours'],
                    project.risk_level.value, self._serialize_json_field(project_data['risk_indicators']),
                    self._serialize_json_field(project_data['issues']),
                    self._serialize_json_field(project_data['context_summary']),
                    project_data['updated_at'], project_data['completed_at'], project_data['archived_at'],
                    project_data['is_archived'], project_data['project_id']
                ))

                # Update collaborators
                self.collaborator_repo.update_project_collaborators(project.project_id, project.collaborators)

                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to update project {project.project_id}: {e}")
            raise DatabaseError(f"Project update failed: {e}")

    def delete(self, project_id: str) -> bool:
        """Delete project (cascades to related records)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM projects WHERE project_id = ?', (project_id,))
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to delete project {project_id}: {e}")
            raise DatabaseError(f"Project deletion failed: {e}")

    def _row_to_project(self, row: sqlite3.Row) -> Project:
        """Convert database row to Project object"""
        return Project(
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'] or '',
            owner=row['owner'],
            collaborators=[],  # Loaded separately
            phase=ProjectPhase(row['phase']),
            status=ProjectStatus(row['status']),
            priority=Priority(row['priority']),
            goals=row['goals'] or '',
            requirements=self._deserialize_json_field(row['requirements'], list),
            constraints=self._deserialize_json_field(row['constraints'], list),
            tech_stack=self._deserialize_json_field(row['tech_stack'], list),
            language_preferences=self._deserialize_json_field(row['language_preferences'], list),
            deployment_target=row['deployment_target'] or 'local',
            architecture_pattern=row['architecture_pattern'] or '',
            technical_specification=None,  # Loaded separately if needed
            conversation_history=[],  # Loaded separately if needed
            context_summary=self._deserialize_json_field(row['context_summary']),
            generated_codebase_id=row['generated_codebase_id'],
            file_structure=self._deserialize_json_field(row['file_structure']),
            progress_percentage=row['progress_percentage'] or 0.0,
            quality_score=row['quality_score'] or 0.0,
            estimated_hours=row['estimated_hours'] or 0,
            actual_hours=row['actual_hours'] or 0,
            risk_level=RiskLevel(row['risk_level']),
            risk_indicators=self._deserialize_json_field(row['risk_indicators'], list),
            issues=self._deserialize_json_field(row['issues'], list),
            created_at=DateTimeHelper.from_iso_string(row['created_at']) if row['created_at'] else DateTimeHelper.now(),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at']) if row['updated_at'] else DateTimeHelper.now(),
            completed_at=DateTimeHelper.from_iso_string(row['completed_at']) if row['completed_at'] else None,
            archived_at=DateTimeHelper.from_iso_string(row['archived_at']) if row['archived_at'] else None,
            is_archived=bool(row['is_archived'])
        )


# ============================================================================
# PROJECT COLLABORATOR REPOSITORY
# ============================================================================

class ProjectCollaboratorRepository(BaseRepository):
    """Repository for project collaborator management"""

    def __init__(self):
        super().__init__('project_collaborators')

    def add_collaborator(self, project_id: str, collaborator: Collaborator) -> bool:
        """Add collaborator to project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO project_collaborators 
                    (project_id, username, role, permissions, joined_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    project_id, collaborator.username, collaborator.role.value,
                    self._serialize_json_field(collaborator.permissions),
                    DateTimeHelper.to_iso_string(collaborator.joined_at),
                    collaborator.is_active
                ))

                return True

        except Exception as e:
            self.logger.error(f"Failed to add collaborator {collaborator.username} to {project_id}: {e}")
            return False

    def get_project_collaborators(self, project_id: str) -> List[Collaborator]:
        """Get all collaborators for a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM project_collaborators 
                    WHERE project_id = ? AND is_active = 1
                    ORDER BY joined_at
                ''', (project_id,))

                collaborators = []
                for row in cursor.fetchall():
                    collaborators.append(Collaborator(
                        username=row['username'],
                        role=UserRole(row['role']),
                        permissions=self._deserialize_json_field(row['permissions'], list),
                        joined_at=DateTimeHelper.from_iso_string(row['joined_at']) if row[
                            'joined_at'] else DateTimeHelper.now(),
                        is_active=bool(row['is_active'])
                    ))

                return collaborators

        except Exception as e:
            self.logger.error(f"Failed to get collaborators for project {project_id}: {e}")
            return []

    def update_project_collaborators(self, project_id: str, collaborators: List[Collaborator]) -> bool:
        """Update all collaborators for a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Remove existing collaborators
                cursor.execute('DELETE FROM project_collaborators WHERE project_id = ?', (project_id,))

                # Add new collaborators
                for collaborator in collaborators:
                    self.add_collaborator(project_id, collaborator)

                return True

        except Exception as e:
            self.logger.error(f"Failed to update collaborators for project {project_id}: {e}")
            return False


# ============================================================================
# MODULE REPOSITORY
# ============================================================================

class ModuleRepository(BaseRepository):
    """Repository for module management"""

    def __init__(self):
        super().__init__('modules')

    def create(self, module: Module) -> bool:
        """Create a new module"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                module_data = asdict(module)
                self._convert_datetime_fields(module_data,
                                              ['created_at', 'updated_at', 'started_at', 'completed_at'])

                cursor.execute('''
                    INSERT INTO modules (module_id, project_id, name, description, module_type, phase,
                                       status, priority, tasks, assigned_roles, assigned_users, dependencies,
                                       blocks, generated_files, progress_percentage, estimated_hours,
                                       actual_hours, risk_level, code_quality_score, test_coverage,
                                       created_at, updated_at, started_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    module_data['module_id'], module_data['project_id'], module_data['name'],
                    module_data['description'], module.module_type.value, module.phase.value,
                    module.status.value, module.priority.value, self._serialize_json_field(module_data['tasks']),
                    self._serialize_json_field([role.value for role in module.assigned_roles]),
                    self._serialize_json_field(module_data['assigned_users']),
                    self._serialize_json_field(module_data['dependencies']),
                    self._serialize_json_field(module_data['blocks']),
                    self._serialize_json_field(module_data['generated_files']),
                    module_data['progress_percentage'], module_data['estimated_hours'], module_data['actual_hours'],
                    module.risk_level.value, module_data['code_quality_score'], module_data['test_coverage'],
                    module_data['created_at'], module_data['updated_at'], module_data['started_at'],
                    module_data['completed_at']
                ))

                self.logger.info(f"Created module: {module.name} ({module.module_id})")
                return True

        except Exception as e:
            self.logger.error(f"Failed to create module {module.name}: {e}")
            raise DatabaseError(f"Module creation failed: {e}")

    def get_by_id(self, module_id: str) -> Optional[Module]:
        """Get module by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM modules WHERE module_id = ?', (module_id,))
                row = cursor.fetchone()

                if row:
                    return self._row_to_module(row)
                return None

        except Exception as e:
            self.logger.error(f"Failed to get module {module_id}: {e}")
            raise DatabaseError(f"Module lookup failed: {e}")

    def get_project_modules(self, project_id: str) -> List[Module]:
        """Get all modules for a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM modules WHERE project_id = ? 
                    ORDER BY created_at
                ''', (project_id,))

                modules = []
                for row in cursor.fetchall():
                    modules.append(self._row_to_module(row))

                return modules

        except Exception as e:
            self.logger.error(f"Failed to get modules for project {project_id}: {e}")
            return []

    def update(self, module: Module) -> bool:
        """Update existing module"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                module_data = asdict(module)
                module_data['updated_at'] = DateTimeHelper.to_iso_string(DateTimeHelper.now())
                self._convert_datetime_fields(module_data,
                                              ['created_at', 'updated_at', 'started_at', 'completed_at'])

                cursor.execute('''
                    UPDATE modules SET name=?, description=?, module_type=?, phase=?, status=?, priority=?,
                                     tasks=?, assigned_roles=?, assigned_users=?, dependencies=?, blocks=?,
                                     generated_files=?, progress_percentage=?, estimated_hours=?, actual_hours=?,
                                     risk_level=?, code_quality_score=?, test_coverage=?, updated_at=?,
                                     started_at=?, completed_at=?
                    WHERE module_id=?
                ''', (
                    module_data['name'], module_data['description'], module.module_type.value,
                    module.phase.value, module.status.value, module.priority.value,
                    self._serialize_json_field(module_data['tasks']),
                    self._serialize_json_field([role.value for role in module.assigned_roles]),
                    self._serialize_json_field(module_data['assigned_users']),
                    self._serialize_json_field(module_data['dependencies']),
                    self._serialize_json_field(module_data['blocks']),
                    self._serialize_json_field(module_data['generated_files']),
                    module_data['progress_percentage'], module_data['estimated_hours'], module_data['actual_hours'],
                    module.risk_level.value, module_data['code_quality_score'], module_data['test_coverage'],
                    module_data['updated_at'], module_data['started_at'], module_data['completed_at'],
                    module_data['module_id']
                ))

                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to update module {module.module_id}: {e}")
            raise DatabaseError(f"Module update failed: {e}")

    def delete(self, module_id: str) -> bool:
        """Delete module"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM modules WHERE module_id = ?', (module_id,))
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to delete module {module_id}: {e}")
            raise DatabaseError(f"Module deletion failed: {e}")

    def _row_to_module(self, row: sqlite3.Row) -> Module:
        """Convert database row to Module object"""
        assigned_roles = [UserRole(role) for role in self._deserialize_json_field(row['assigned_roles'], list)]

        return Module(
            module_id=row['module_id'],
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'] or '',
            module_type=ModuleType(row['module_type']),
            phase=ProjectPhase(row['phase']),
            status=ModuleStatus(row['status']),
            priority=Priority(row['priority']),
            tasks=self._deserialize_json_field(row['tasks'], list),
            assigned_roles=assigned_roles,
            assigned_users=self._deserialize_json_field(row['assigned_users'], list),
            dependencies=self._deserialize_json_field(row['dependencies'], list),
            blocks=self._deserialize_json_field(row['blocks'], list),
            generated_files=self._deserialize_json_field(row['generated_files'], list),
            progress_percentage=row['progress_percentage'] or 0.0,
            estimated_hours=row['estimated_hours'] or 0,
            actual_hours=row['actual_hours'] or 0,
            risk_level=RiskLevel(row['risk_level']),
            code_quality_score=row['code_quality_score'] or 0.0,
            test_coverage=row['test_coverage'] or 0.0,
            created_at=DateTimeHelper.from_iso_string(row['created_at']) if row['created_at'] else DateTimeHelper.now(),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at']) if row['updated_at'] else DateTimeHelper.now(),
            started_at=DateTimeHelper.from_iso_string(row['started_at']) if row['started_at'] else None,
            completed_at=DateTimeHelper.from_iso_string(row['completed_at']) if row['completed_at'] else None
        )


# ============================================================================
# GENERATED FILE REPOSITORY
# ============================================================================

class GeneratedFileRepository(BaseRepository):
    """Repository for generated file management"""

    def __init__(self):
        super().__init__('generated_files')

    def create(self, file: GeneratedFile) -> bool:
        """Create a new generated file"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                file_data = asdict(file)
                self._convert_datetime_fields(file_data,
                                              ['created_at', 'updated_at', 'last_generated', 'last_tested',
                                               'deployed_at'])

                cursor.execute('''
                    INSERT INTO generated_files (file_id, project_id, module_id, codebase_id, file_path,
                                               file_name, file_type, file_purpose, content, content_hash,
                                               size_bytes, generated_by_agent, generation_prompt, generation_context,
                                               dependencies, dependents, related_files, status, has_errors,
                                               error_messages, warnings, complexity_score, maintainability_score,
                                               test_coverage, lines_of_code, documentation, comments_ratio,
                                               created_at, updated_at, last_generated, last_tested, deployed_at,
                                               version, git_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_data['file_id'], file_data['project_id'], file_data['module_id'], file_data['codebase_id'],
                    file_data['file_path'], file_data['file_name'], file.file_type.value, file_data['file_purpose'],
                    file_data['content'], file_data['content_hash'], file_data['size_bytes'],
                    file_data['generated_by_agent'], file_data['generation_prompt'],
                    self._serialize_json_field(file_data['generation_context']),
                    self._serialize_json_field(file_data['dependencies']),
                    self._serialize_json_field(file_data['dependents']),
                    self._serialize_json_field(file_data['related_files']), file.status.value, file_data['has_errors'],
                    self._serialize_json_field(file_data['error_messages']),
                    self._serialize_json_field(file_data['warnings']),
                    file_data['complexity_score'], file_data['maintainability_score'], file_data['test_coverage'],
                    file_data['lines_of_code'], file_data['documentation'], file_data['comments_ratio'],
                    file_data['created_at'], file_data['updated_at'], file_data['last_generated'],
                    file_data['last_tested'], file_data['deployed_at'], file_data['version'], file_data['git_hash']
                ))

                self.logger.info(f"Created generated file: {file.file_path} ({file.file_id})")
                return True

        except Exception as e:
            self.logger.error(f"Failed to create generated file {file.file_path}: {e}")
            raise DatabaseError(f"Generated file creation failed: {e}")

    def get_by_id(self, file_id: str) -> Optional[GeneratedFile]:
        """Get generated file by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM generated_files WHERE file_id = ?', (file_id,))
                row = cursor.fetchone()

                if row:
                    return self._row_to_generated_file(row)
                return None

        except Exception as e:
            self.logger.error(f"Failed to get generated file {file_id}: {e}")
            raise DatabaseError(f"Generated file lookup failed: {e}")

    def get_project_files(self, project_id: str) -> List[GeneratedFile]:
        """Get all generated files for a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM generated_files WHERE project_id = ? 
                    ORDER BY file_path
                ''', (project_id,))

                files = []
                for row in cursor.fetchall():
                    files.append(self._row_to_generated_file(row))

                return files

        except Exception as e:
            self.logger.error(f"Failed to get files for project {project_id}: {e}")
            return []

    def update(self, file: GeneratedFile) -> bool:
        """Update existing generated file"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                file_data = asdict(file)
                file_data['updated_at'] = DateTimeHelper.to_iso_string(DateTimeHelper.now())
                self._convert_datetime_fields(file_data,
                                              ['created_at', 'updated_at', 'last_generated', 'last_tested',
                                               'deployed_at'])

                cursor.execute('''
                    UPDATE generated_files SET project_id=?, module_id=?, codebase_id=?, file_path=?,
                                             file_name=?, file_type=?, file_purpose=?, content=?, content_hash=?,
                                             size_bytes=?, generated_by_agent=?, generation_prompt=?, generation_context=?,
                                             dependencies=?, dependents=?, related_files=?, status=?, has_errors=?,
                                             error_messages=?, warnings=?, complexity_score=?, maintainability_score=?,
                                             test_coverage=?, lines_of_code=?, documentation=?, comments_ratio=?,
                                             updated_at=?, last_generated=?, last_tested=?, deployed_at=?,
                                             version=?, git_hash=?
                    WHERE file_id=?
                ''', (
                    file_data['project_id'], file_data['module_id'], file_data['codebase_id'],
                    file_data['file_path'], file_data['file_name'], file.file_type.value, file_data['file_purpose'],
                    file_data['content'], file_data['content_hash'], file_data['size_bytes'],
                    file_data['generated_by_agent'], file_data['generation_prompt'],
                    self._serialize_json_field(file_data['generation_context']),
                    self._serialize_json_field(file_data['dependencies']),
                    self._serialize_json_field(file_data['dependents']),
                    self._serialize_json_field(file_data['related_files']), file.status.value, file_data['has_errors'],
                    self._serialize_json_field(file_data['error_messages']),
                    self._serialize_json_field(file_data['warnings']),
                    file_data['complexity_score'], file_data['maintainability_score'], file_data['test_coverage'],
                    file_data['lines_of_code'], file_data['documentation'], file_data['comments_ratio'],
                    file_data['updated_at'], file_data['last_generated'], file_data['last_tested'],
                    file_data['deployed_at'],
                    file_data['version'], file_data['git_hash'], file_data['file_id']
                ))

                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to update generated file {file.file_id}: {e}")
            raise DatabaseError(f"Generated file update failed: {e}")

    def delete(self, file_id: str) -> bool:
        """Delete generated file"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM generated_files WHERE file_id = ?', (file_id,))
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to delete generated file {file_id}: {e}")
            raise DatabaseError(f"Generated file deletion failed: {e}")

    def _row_to_generated_file(self, row: sqlite3.Row) -> GeneratedFile:
        """Convert database row to GeneratedFile object"""
        return GeneratedFile(
            file_id=row['file_id'],
            project_id=row['project_id'],
            module_id=row['module_id'],
            codebase_id=row['codebase_id'],
            file_path=row['file_path'],
            file_name=row['file_name'],
            file_type=FileType(row['file_type']),
            file_purpose=row['file_purpose'] or '',
            content=row['content'] or '',
            content_hash=row['content_hash'] or '',
            size_bytes=row['size_bytes'] or 0,
            generated_by_agent=row['generated_by_agent'] or '',
            generation_prompt=row['generation_prompt'] or '',
            generation_context=self._deserialize_json_field(row['generation_context']),
            dependencies=self._deserialize_json_field(row['dependencies'], list),
            dependents=self._deserialize_json_field(row['dependents'], list),
            related_files=self._deserialize_json_field(row['related_files'], list),
            status=FileStatus(row['status']),
            has_errors=bool(row['has_errors']),
            error_messages=self._deserialize_json_field(row['error_messages'], list),
            warnings=self._deserialize_json_field(row['warnings'], list),
            complexity_score=row['complexity_score'] or 0.0,
            maintainability_score=row['maintainability_score'] or 0.0,
            test_coverage=row['test_coverage'] or 0.0,
            lines_of_code=row['lines_of_code'] or 0,
            documentation=row['documentation'] or '',
            comments_ratio=row['comments_ratio'] or 0.0,
            created_at=DateTimeHelper.from_iso_string(row['created_at']) if row['created_at'] else DateTimeHelper.now(),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at']) if row['updated_at'] else DateTimeHelper.now(),
            last_generated=DateTimeHelper.from_iso_string(row['last_generated']) if row[
                'last_generated'] else DateTimeHelper.now(),
            last_tested=DateTimeHelper.from_iso_string(row['last_tested']) if row['last_tested'] else None,
            deployed_at=DateTimeHelper.from_iso_string(row['deployed_at']) if row['deployed_at'] else None,
            version=row['version'] or '1.0',
            git_hash=row['git_hash']
        )


# ============================================================================
# TEST RESULT REPOSITORY
# ============================================================================

class TestResultRepository(BaseRepository):
    """Repository for test result management"""

    def __init__(self):
        super().__init__('test_results')

    def create(self, test_result: TestResult) -> bool:
        """Create a new test result"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                test_data = asdict(test_result)
                self._convert_datetime_fields(test_data, ['created_at', 'started_at', 'completed_at'])

                cursor.execute('''
                    INSERT INTO test_results (test_id, project_id, module_id, codebase_id, test_type, test_suite,
                                            test_framework, files_tested, test_files, status, passed, total_tests,
                                            passed_tests, failed_tests, skipped_tests, error_tests, coverage_percentage,
                                            line_coverage, branch_coverage, function_coverage, execution_time_seconds,
                                            memory_usage_mb, cpu_usage_percent, test_cases, failure_details,
                                            error_details, code_quality_score, maintainability_score, complexity_warnings,
                                            security_issues, performance_issues, optimization_suggestions, test_environment,
                                            python_version, node_version, browser_info, created_at, started_at,
                                            completed_at, exit_code, stdout, stderr, command_line)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_data['test_id'], test_data['project_id'], test_data['module_id'], test_data['codebase_id'],
                    test_result.test_type.value, test_data['test_suite'], test_data['test_framework'],
                    self._serialize_json_field(test_data['files_tested']),
                    self._serialize_json_field(test_data['test_files']),
                    test_result.status.value, test_data['passed'], test_data['total_tests'], test_data['passed_tests'],
                    test_data['failed_tests'], test_data['skipped_tests'], test_data['error_tests'],
                    test_data['coverage_percentage'], test_data['line_coverage'], test_data['branch_coverage'],
                    test_data['function_coverage'], test_data['execution_time_seconds'], test_data['memory_usage_mb'],
                    test_data['cpu_usage_percent'], self._serialize_json_field(test_data['test_cases']),
                    self._serialize_json_field(test_data['failure_details']),
                    self._serialize_json_field(test_data['error_details']),
                    test_data['code_quality_score'], test_data['maintainability_score'],
                    self._serialize_json_field(test_data['complexity_warnings']),
                    self._serialize_json_field(test_data['security_issues']),
                    self._serialize_json_field(test_data['performance_issues']),
                    self._serialize_json_field(test_data['optimization_suggestions']),
                    self._serialize_json_field(test_data['test_environment']), test_data['python_version'],
                    test_data['node_version'], self._serialize_json_field(test_data['browser_info']),
                    test_data['created_at'], test_data['started_at'], test_data['completed_at'],
                    test_data['exit_code'], test_data['stdout'], test_data['stderr'], test_data['command_line']
                ))

                self.logger.info(f"Created test result: {test_result.test_type.value} ({test_result.test_id})")
                return True

        except Exception as e:
            self.logger.error(f"Failed to create test result {test_result.test_id}: {e}")
            raise DatabaseError(f"Test result creation failed: {e}")

    def get_by_id(self, test_id: str) -> Optional[TestResult]:
        """Get test result by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM test_results WHERE test_id = ?', (test_id,))
                row = cursor.fetchone()

                if row:
                    return self._row_to_test_result(row)
                return None

        except Exception as e:
            self.logger.error(f"Failed to get test result {test_id}: {e}")
            raise DatabaseError(f"Test result lookup failed: {e}")

    def get_project_test_results(self, project_id: str) -> List[TestResult]:
        """Get all test results for a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM test_results WHERE project_id = ? 
                    ORDER BY created_at DESC
                ''', (project_id,))

                results = []
                for row in cursor.fetchall():
                    results.append(self._row_to_test_result(row))

                return results

        except Exception as e:
            self.logger.error(f"Failed to get test results for project {project_id}: {e}")
            return []

    def update(self, test_result: TestResult) -> bool:
        """Update existing test result"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                test_data = asdict(test_result)
                self._convert_datetime_fields(test_data, ['created_at', 'started_at', 'completed_at'])

                cursor.execute('''
                    UPDATE test_results SET project_id=?, module_id=?, codebase_id=?, test_type=?, test_suite=?,
                                          test_framework=?, files_tested=?, test_files=?, status=?, passed=?, total_tests=?,
                                          passed_tests=?, failed_tests=?, skipped_tests=?, error_tests=?, coverage_percentage=?,
                                          line_coverage=?, branch_coverage=?, function_coverage=?, execution_time_seconds=?,
                                          memory_usage_mb=?, cpu_usage_percent=?, test_cases=?, failure_details=?,
                                          error_details=?, code_quality_score=?, maintainability_score=?, complexity_warnings=?,
                                          security_issues=?, performance_issues=?, optimization_suggestions=?, test_environment=?,
                                          python_version=?, node_version=?, browser_info=?, started_at=?, completed_at=?,
                                          exit_code=?, stdout=?, stderr=?, command_line=?
                    WHERE test_id=?
                ''', (
                    test_data['project_id'], test_data['module_id'], test_data['codebase_id'],
                    test_result.test_type.value, test_data['test_suite'], test_data['test_framework'],
                    self._serialize_json_field(test_data['files_tested']),
                    self._serialize_json_field(test_data['test_files']),
                    test_result.status.value, test_data['passed'], test_data['total_tests'], test_data['passed_tests'],
                    test_data['failed_tests'], test_data['skipped_tests'], test_data['error_tests'],
                    test_data['coverage_percentage'], test_data['line_coverage'], test_data['branch_coverage'],
                    test_data['function_coverage'], test_data['execution_time_seconds'], test_data['memory_usage_mb'],
                    test_data['cpu_usage_percent'], self._serialize_json_field(test_data['test_cases']),
                    self._serialize_json_field(test_data['failure_details']),
                    self._serialize_json_field(test_data['error_details']),
                    test_data['code_quality_score'], test_data['maintainability_score'],
                    self._serialize_json_field(test_data['complexity_warnings']),
                    self._serialize_json_field(test_data['security_issues']),
                    self._serialize_json_field(test_data['performance_issues']),
                    self._serialize_json_field(test_data['optimization_suggestions']),
                    self._serialize_json_field(test_data['test_environment']), test_data['python_version'],
                    test_data['node_version'], self._serialize_json_field(test_data['browser_info']),
                    test_data['started_at'], test_data['completed_at'], test_data['exit_code'],
                    test_data['stdout'], test_data['stderr'], test_data['command_line'], test_data['test_id']
                ))

                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to update test result {test_result.test_id}: {e}")
            raise DatabaseError(f"Test result update failed: {e}")

    def delete(self, test_id: str) -> bool:
        """Delete test result"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM test_results WHERE test_id = ?', (test_id,))
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to delete test result {test_id}: {e}")
            raise DatabaseError(f"Test result deletion failed: {e}")

    def _row_to_test_result(self, row: sqlite3.Row) -> TestResult:
        """Convert database row to TestResult object"""
        return TestResult(
            test_id=row['test_id'],
            project_id=row['project_id'],
            module_id=row['module_id'],
            codebase_id=row['codebase_id'],
            test_type=TestType(row['test_type']),
            test_suite=row['test_suite'] or '',
            test_framework=row['test_framework'] or 'pytest',
            files_tested=self._deserialize_json_field(row['files_tested'], list),
            test_files=self._deserialize_json_field(row['test_files'], list),
            status=TestStatus(row['status']),
            passed=bool(row['passed']),
            total_tests=row['total_tests'] or 0,
            passed_tests=row['passed_tests'] or 0,
            failed_tests=row['failed_tests'] or 0,
            skipped_tests=row['skipped_tests'] or 0,
            error_tests=row['error_tests'] or 0,
            coverage_percentage=row['coverage_percentage'] or 0.0,
            line_coverage=row['line_coverage'] or 0.0,
            branch_coverage=row['branch_coverage'] or 0.0,
            function_coverage=row['function_coverage'] or 0.0,
            execution_time_seconds=row['execution_time_seconds'] or 0.0,
            memory_usage_mb=row['memory_usage_mb'] or 0.0,
            cpu_usage_percent=row['cpu_usage_percent'] or 0.0,
            test_cases=self._deserialize_json_field(row['test_cases'], list),
            failure_details=self._deserialize_json_field(row['failure_details'], list),
            error_details=self._deserialize_json_field(row['error_details'], list),
            code_quality_score=row['code_quality_score'] or 0.0,
            maintainability_score=row['maintainability_score'] or 0.0,
            complexity_warnings=self._deserialize_json_field(row['complexity_warnings'], list),
            security_issues=self._deserialize_json_field(row['security_issues'], list),
            performance_issues=self._deserialize_json_field(row['performance_issues'], list),
            optimization_suggestions=self._deserialize_json_field(row['optimization_suggestions'], list),
            test_environment=self._deserialize_json_field(row['test_environment']),
            python_version=row['python_version'] or '',
            node_version=row['node_version'] or '',
            browser_info=self._deserialize_json_field(row['browser_info']),
            created_at=DateTimeHelper.from_iso_string(row['created_at']) if row['created_at'] else DateTimeHelper.now(),
            started_at=DateTimeHelper.from_iso_string(row['started_at']) if row['started_at'] else None,
            completed_at=DateTimeHelper.from_iso_string(row['completed_at']) if row['completed_at'] else None,
            exit_code=row['exit_code'] or 0,
            stdout=row['stdout'] or '',
            stderr=row['stderr'] or '',
            command_line=row['command_line'] or ''
        )


# ============================================================================
# DATABASE SERVICE (MAIN INTERFACE)
# ============================================================================

class DatabaseService:
    """Main database service providing unified access to all repositories"""

    def __init__(self):
        self.logger = get_logger('database.service')
        self.schema = DatabaseSchema()

        # Initialize repositories
        self.users = UserRepository()
        self.projects = ProjectRepository()
        self.modules = ModuleRepository()
        self.files = GeneratedFileRepository()
        self.tests = TestResultRepository()

        # Initialize database schema
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize database schema"""
        try:
            with get_db_manager().get_db_session() as conn:
                self.schema.initialize_schema(conn)

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Check database health and connectivity"""
        try:
            with get_db_manager().get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM projects')
                project_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM users')
                user_count = cursor.fetchone()[0]

                cursor.execute('SELECT version FROM schema_version ORDER BY version DESC LIMIT 1')
                schema_version = cursor.fetchone()

                return {
                    'status': 'healthy',
                    'project_count': project_count,
                    'user_count': user_count,
                    'schema_version': schema_version[0] if schema_version else 0,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                }

        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with get_db_manager().get_db_session() as conn:
                cursor = conn.cursor()

                stats = {}

                # Count all entities
                tables = ['users', 'projects', 'modules', 'generated_files', 'test_results']
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    stats[f'{table}_count'] = cursor.fetchone()[0]

                # Active vs archived projects
                cursor.execute('SELECT COUNT(*) FROM projects WHERE is_archived = 0')
                stats['active_projects'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM projects WHERE is_archived = 1')
                stats['archived_projects'] = cursor.fetchone()[0]

                # Recent activity
                cursor.execute('''
                    SELECT COUNT(*) FROM projects 
                    WHERE updated_at > datetime('now', '-7 days')
                ''')
                stats['projects_updated_last_week'] = cursor.fetchone()[0]

                return stats

        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}


# ============================================================================
# GLOBAL DATABASE INSTANCE
# ============================================================================

# Global database service instance
_database_service: Optional[DatabaseService] = None


def get_database() -> DatabaseService:
    """Get the global database service instance"""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service


if __name__ == "__main__":
    # Test the database system
    db = get_database()

    # Health check
    health = db.health_check()
    print(f"✅ Database health: {health}")

    # Statistics
    stats = db.get_statistics()
    print(f"📊 Database stats: {stats}")

"""What src/database.py Provides:
🗄️ Complete Database Schema:

7 main tables with proper relationships and foreign keys
Indexes for performance optimization
JSON fields for complex data (arrays, objects)
Migration system for future schema changes

📊 Repository Pattern:
Database Repositories:
├── UserRepository - User management & authentication
├── ProjectRepository - Project lifecycle & collaboration
├── ModuleRepository - Module organization & tracking  
├── GeneratedFileRepository - File content & metadata
├── TestResultRepository - Test execution & results
└── ProjectCollaboratorRepository - Team management
🔧 Key Features:
Transaction Support:

Context managers for safe database operations
Automatic rollback on errors
Connection pooling through core DatabaseManager

Data Handling:

JSON serialization for complex fields (arrays, objects)
DateTime conversion using DateTimeHelper (no deprecated functions)
Type-safe enum conversions
Validation integration

Performance:

Indexed queries for common operations
Optimized SQLite settings (WAL mode, foreign keys)
Efficient connection reuse

Schema Management:
sqlTables Created:
├── users (authentication, roles, preferences)
├── projects (full project data with JSON fields) 
├── project_collaborators (team relationships)
├── modules (hierarchical organization)
├── generated_files (complete file tracking)
├── test_results (comprehensive testing data)
├── conversation_messages (Socratic sessions)
└── technical_specifications (detailed specs)
🎯 Usage Examples:
pythonfrom src.database import get_database

db = get_database()

# Create project
project = ModelFactory.create_project("My App", "john_doe")
db.projects.create(project)

# Get user's projects
projects = db.projects.get_user_projects("john_doe")

# Create and track generated file
file = ModelFactory.create_generated_file(project.project_id, "app.py", FileType.PYTHON)
db.files.create(file)
✅ Integration:

Uses core.py DatabaseManager for connections
Uses models.py data structures directly
Uses core.py logging and exception system
Thread-safe operations where needed"""
