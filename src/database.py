#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Database Layer
======================================

Complete database management system using repository pattern.
Integrates with core.py DatabaseManager and models.py data structures.

Provides:
- Schema management and migrations
- Repository pattern for all models
- Transaction support
- Proper integration with core infrastructure
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any, Type
from dataclasses import asdict
from pathlib import Path

# Core system imports
from .core import (
    DatabaseManager, get_logger, DateTimeHelper,
    DatabaseError, ValidationError, FileHelper
)

# Model imports
from .models import (
    # Base
    BaseModel, ModelRegistry,

    # User models
    User, UserSession, UserRole, UserStatus,

    # Project hierarchy
    Project, Module, Task,
    ProjectPhase, ProjectStatus, TaskStatus, TaskPriority, ModuleType,

    # Socratic conversation
    SocraticSession, Question, Conflict,
    TechnicalRole, ConversationStatus, ConflictType,

    # Technical specifications
    TechnicalSpec,

    # Code generation
    GeneratedCodebase, GeneratedFile, TestResult,
    FileType, TestType,

    # Analytics
    ProjectMetrics, UserActivity
)


# ============================================================================
# DATABASE SCHEMA MANAGEMENT
# ============================================================================

class DatabaseSchema:
    """Manages database schema creation and migrations"""

    def __init__(self):
        self.logger = get_logger('database.schema')
        self.current_version = 1

    def initialize_schema(self) -> bool:
        """Initialize complete database schema"""
        try:
            db_manager = DatabaseManager()

            with db_manager.transaction() as conn:
                cursor = conn.cursor()

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
                result = cursor.fetchone()
                current_version = result[0] if result and result[0] else 0

                if current_version < self.current_version:
                    self._create_all_tables(cursor)
                    self._create_indexes(cursor)

                    # Record schema version
                    cursor.execute('''
                        INSERT OR REPLACE INTO schema_version (version, applied_at, description)
                        VALUES (?, ?, ?)
                    ''', (
                        self.current_version,
                        DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                        "Initial schema with all models"
                    ))

                    self.logger.info(f"Database schema initialized to version {self.current_version}")

                return True

        except Exception as e:
            self.logger.error(f"Schema initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize database schema: {e}")

    def _create_all_tables(self, cursor: sqlite3.Cursor):
        """Create all database tables"""

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT DEFAULT '',
                last_name TEXT DEFAULT '',
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                avatar_url TEXT,
                bio TEXT DEFAULT '',
                skills TEXT DEFAULT '[]',
                preferences TEXT DEFAULT '{}',
                last_login TEXT,
                login_attempts INTEGER DEFAULT 0,
                locked_until TEXT,
                api_key TEXT,
                projects_created INTEGER DEFAULT 0,
                sessions_completed INTEGER DEFAULT 0,
                code_generated_lines INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                ip_address TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                expires_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                last_activity TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                owner_id TEXT NOT NULL,
                status TEXT NOT NULL,
                phase TEXT NOT NULL,
                technology_stack TEXT DEFAULT '{}',
                requirements TEXT DEFAULT '[]',
                constraints TEXT DEFAULT '[]',
                success_criteria TEXT DEFAULT '[]',
                start_date TEXT,
                end_date TEXT,
                estimated_hours INTEGER,
                budget REAL,
                team_members TEXT DEFAULT '[]',
                stakeholders TEXT DEFAULT '[]',
                progress_percentage REAL DEFAULT 0.0,
                completed_modules INTEGER DEFAULT 0,
                total_modules INTEGER DEFAULT 0,
                generated_codebase_id TEXT,
                repository_url TEXT,
                deployment_url TEXT,
                tags TEXT DEFAULT '[]',
                priority TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            )
        ''')

        # Modules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                module_type TEXT NOT NULL,
                parent_module_id TEXT,
                order_index INTEGER DEFAULT 0,
                dependencies TEXT DEFAULT '[]',
                technologies TEXT DEFAULT '[]',
                apis_provided TEXT DEFAULT '[]',
                apis_consumed TEXT DEFAULT '[]',
                status TEXT NOT NULL,
                progress_percentage REAL DEFAULT 0.0,
                estimated_hours INTEGER,
                actual_hours INTEGER,
                assigned_to TEXT,
                reviewer TEXT,
                generated_files TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_module_id) REFERENCES modules(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id),
                FOREIGN KEY (reviewer) REFERENCES users(id)
            )
        ''')

        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                module_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                task_type TEXT DEFAULT '',
                assigned_to TEXT,
                estimated_hours INTEGER,
                actual_hours INTEGER,
                due_date TEXT,
                completed_date TEXT,
                depends_on TEXT DEFAULT '[]',
                blocks TEXT DEFAULT '[]',
                progress_percentage REAL DEFAULT 0.0,
                notes TEXT DEFAULT '',
                related_files TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_to) REFERENCES users(id)
            )
        ''')

        # Socratic sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS socratic_sessions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                current_role TEXT NOT NULL,
                status TEXT NOT NULL,
                roles_to_cover TEXT DEFAULT '[]',
                completed_roles TEXT DEFAULT '[]',
                total_questions INTEGER DEFAULT 0,
                questions_answered INTEGER DEFAULT 0,
                insights_generated INTEGER DEFAULT 0,
                conflicts_detected INTEGER DEFAULT 0,
                session_notes TEXT DEFAULT '',
                quality_score REAL DEFAULT 0.0,
                completion_percentage REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                question_text TEXT NOT NULL,
                context TEXT DEFAULT '',
                is_follow_up BOOLEAN DEFAULT 0,
                parent_question_id TEXT,
                importance_score REAL DEFAULT 0.5,
                is_answered BOOLEAN DEFAULT 0,
                answer_text TEXT DEFAULT '',
                answer_quality_score REAL DEFAULT 0.0,
                generated_insights TEXT DEFAULT '[]',
                detected_conflicts TEXT DEFAULT '[]',
                recommended_follow_ups TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES socratic_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_question_id) REFERENCES questions(id)
            )
        ''')

        # Conflicts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conflicts (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                first_requirement TEXT NOT NULL,
                second_requirement TEXT NOT NULL,
                conflicting_roles TEXT DEFAULT '[]',
                is_resolved BOOLEAN DEFAULT 0,
                resolution_strategy TEXT DEFAULT '',
                resolution_notes TEXT DEFAULT '',
                resolved_by TEXT,
                resolved_at TEXT,
                affected_modules TEXT DEFAULT '[]',
                estimated_impact_hours INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES socratic_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (resolved_by) REFERENCES users(id)
            )
        ''')

        # Technical specifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS technical_specs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                version TEXT DEFAULT '1.0.0',
                architecture_type TEXT DEFAULT '',
                technology_stack TEXT DEFAULT '{}',
                functional_requirements TEXT DEFAULT '[]',
                non_functional_requirements TEXT DEFAULT '[]',
                system_components TEXT DEFAULT '[]',
                data_models TEXT DEFAULT '[]',
                api_specifications TEXT DEFAULT '[]',
                performance_requirements TEXT DEFAULT '{}',
                security_requirements TEXT DEFAULT '[]',
                scalability_requirements TEXT DEFAULT '{}',
                deployment_strategy TEXT DEFAULT '',
                infrastructure_requirements TEXT DEFAULT '{}',
                monitoring_requirements TEXT DEFAULT '[]',
                testing_strategy TEXT DEFAULT '{}',
                acceptance_criteria TEXT DEFAULT '[]',
                documentation_requirements TEXT DEFAULT '[]',
                is_approved BOOLEAN DEFAULT 0,
                approved_by TEXT,
                approved_at TEXT,
                approval_notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (approved_by) REFERENCES users(id)
            )
        ''')

        # Generated codebases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_codebases (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                spec_id TEXT,
                version TEXT DEFAULT '1.0.0',
                architecture_type TEXT DEFAULT '',
                technology_stack TEXT DEFAULT '{}',
                file_structure TEXT DEFAULT '{}',
                generated_files TEXT DEFAULT '[]',
                total_lines_of_code INTEGER DEFAULT 0,
                total_files INTEGER DEFAULT 0,
                code_quality_score REAL DEFAULT 0.0,
                test_coverage REAL DEFAULT 0.0,
                generation_time_seconds REAL DEFAULT 0.0,
                compilation_successful BOOLEAN DEFAULT 0,
                tests_passing BOOLEAN DEFAULT 0,
                security_scan_results TEXT DEFAULT '{}',
                security_issues_count INTEGER DEFAULT 0,
                critical_issues_count INTEGER DEFAULT 0,
                deployment_config TEXT DEFAULT '{}',
                deployment_status TEXT DEFAULT 'not_deployed',
                validation_results TEXT DEFAULT '[]',
                error_count INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (spec_id) REFERENCES technical_specs(id)
            )
        ''')

        # Generated files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_files (
                id TEXT PRIMARY KEY,
                codebase_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_purpose TEXT DEFAULT '',
                content TEXT DEFAULT '',
                dependencies TEXT DEFAULT '[]',
                documentation TEXT DEFAULT '',
                generated_by_agent TEXT DEFAULT '',
                version TEXT DEFAULT '1.0.0',
                size_bytes INTEGER DEFAULT 0,
                complexity_score REAL DEFAULT 0.0,
                test_coverage REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (codebase_id) REFERENCES generated_codebases(id) ON DELETE CASCADE,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        ''')

        # Test results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id TEXT PRIMARY KEY,
                codebase_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                test_type TEXT NOT NULL,
                test_suite TEXT DEFAULT '',
                files_tested TEXT DEFAULT '[]',
                passed BOOLEAN DEFAULT 0,
                total_tests INTEGER DEFAULT 0,
                passed_tests INTEGER DEFAULT 0,
                failed_tests INTEGER DEFAULT 0,
                skipped_tests INTEGER DEFAULT 0,
                coverage_percentage REAL DEFAULT 0.0,
                failure_details TEXT DEFAULT '[]',
                stack_traces TEXT DEFAULT '[]',
                memory_usage_mb REAL DEFAULT 0.0,
                cpu_usage_percentage REAL DEFAULT 0.0,
                test_environment TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (codebase_id) REFERENCES generated_codebases(id) ON DELETE CASCADE,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        ''')

        # Project metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_metrics (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                total_development_hours REAL DEFAULT 0.0,
                code_generation_time REAL DEFAULT 0.0,
                testing_time REAL DEFAULT 0.0,
                review_time REAL DEFAULT 0.0,
                average_code_quality REAL DEFAULT 0.0,
                test_coverage REAL DEFAULT 0.0,
                bug_count INTEGER DEFAULT 0,
                security_issues INTEGER DEFAULT 0,
                lines_of_code_generated INTEGER DEFAULT 0,
                files_generated INTEGER DEFAULT 0,
                tests_generated INTEGER DEFAULT 0,
                documentation_pages INTEGER DEFAULT 0,
                team_members_active INTEGER DEFAULT 0,
                sessions_completed INTEGER DEFAULT 0,
                conflicts_resolved INTEGER DEFAULT 0,
                insights_generated INTEGER DEFAULT 0,
                planned_duration_days INTEGER,
                actual_duration_days INTEGER,
                delays_count INTEGER DEFAULT 0,
                client_satisfaction REAL DEFAULT 0.0,
                deployment_success BOOLEAN DEFAULT 0,
                post_deployment_issues INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        ''')

        # User activity table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                sessions_started INTEGER DEFAULT 0,
                sessions_completed INTEGER DEFAULT 0,
                questions_answered INTEGER DEFAULT 0,
                projects_created INTEGER DEFAULT 0,
                total_active_time_hours REAL DEFAULT 0.0,
                last_activity TEXT NOT NULL,
                code_lines_generated INTEGER DEFAULT 0,
                tests_created INTEGER DEFAULT 0,
                bugs_found INTEGER DEFAULT 0,
                insights_provided INTEGER DEFAULT 0,
                conflicts_mediated INTEGER DEFAULT 0,
                reviews_completed INTEGER DEFAULT 0,
                mentoring_sessions INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Project collaborators table (simple version)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_collaborators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                joined_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (username) REFERENCES users(username),
                UNIQUE(project_id, username)
            )
        ''')

    def _create_indexes(self, cursor: sqlite3.Cursor):
        """Create database indexes for performance"""
        indexes = [
            # Users
            'CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)',
            'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)',
            'CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)',

            # Projects
            'CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id)',
            'CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)',
            'CREATE INDEX IF NOT EXISTS idx_projects_phase ON projects(phase)',

            # Modules
            'CREATE INDEX IF NOT EXISTS idx_modules_project ON modules(project_id)',
            'CREATE INDEX IF NOT EXISTS idx_modules_status ON modules(status)',
            'CREATE INDEX IF NOT EXISTS idx_modules_assigned ON modules(assigned_to)',

            # Tasks
            'CREATE INDEX IF NOT EXISTS idx_tasks_module ON tasks(module_id)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to)',

            # Socratic sessions
            'CREATE INDEX IF NOT EXISTS idx_sessions_project ON socratic_sessions(project_id)',
            'CREATE INDEX IF NOT EXISTS idx_sessions_user ON socratic_sessions(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_sessions_status ON socratic_sessions(status)',

            # Questions
            'CREATE INDEX IF NOT EXISTS idx_questions_session ON questions(session_id)',
            'CREATE INDEX IF NOT EXISTS idx_questions_role ON questions(role)',

            # Generated files
            'CREATE INDEX IF NOT EXISTS idx_files_codebase ON generated_files(codebase_id)',
            'CREATE INDEX IF NOT EXISTS idx_files_project ON generated_files(project_id)',
            'CREATE INDEX IF NOT EXISTS idx_files_type ON generated_files(file_type)',

            # Test results
            'CREATE INDEX IF NOT EXISTS idx_tests_codebase ON test_results(codebase_id)',
            'CREATE INDEX IF NOT EXISTS idx_tests_project ON test_results(project_id)',
            'CREATE INDEX IF NOT EXISTS idx_tests_type ON test_results(test_type)',

            # Project collaborators
            'CREATE INDEX IF NOT EXISTS idx_collaborators_project ON project_collaborators(project_id)',
            'CREATE INDEX IF NOT EXISTS idx_collaborators_user ON project_collaborators(username)',
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)


# ============================================================================
# BASE REPOSITORY CLASS
# ============================================================================

class BaseRepository:
    """Base repository with common database operations"""

    def __init__(self, table_name: str, model_class: Type[BaseModel]):
        self.table_name = table_name
        self.model_class = model_class
        self.logger = get_logger(f'db.{table_name}')
        self.db_manager = DatabaseManager()

    def _serialize_json_field(self, value: Any) -> str:
        """Serialize value to JSON string"""
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

    def _convert_model_to_dict(self, model: BaseModel) -> Dict[str, Any]:
        """Convert model to dictionary with proper serialization"""
        data = asdict(model)

        # Convert datetime fields to ISO strings
        datetime_fields = ['created_at', 'updated_at', 'last_login', 'expires_at',
                           'last_activity', 'start_date', 'end_date', 'due_date',
                           'completed_date', 'resolved_at', 'approved_at']

        for field in datetime_fields:
            if field in data and data[field] is not None:
                if hasattr(data[field], 'isoformat'):
                    data[field] = DateTimeHelper.to_iso_string(data[field])

        # Convert enum fields to strings
        for key, value in data.items():
            if hasattr(value, 'value'):  # Enum
                data[key] = value.value
            elif isinstance(value, list) and value and hasattr(value[0], 'value'):  # List of enums
                data[key] = [item.value for item in value]

        return data

    def _convert_row_to_model(self, row: sqlite3.Row) -> BaseModel:
        """Convert database row to model instance (to be overridden)"""
        raise NotImplementedError("Subclasses must implement _convert_row_to_model")

    def create(self, model: BaseModel) -> bool:
        """Create new record"""
        try:
            with self.db_manager.transaction() as conn:
                data = self._convert_model_to_dict(model)

                # Build INSERT query
                columns = list(data.keys())
                placeholders = ', '.join(['?' for _ in columns])
                values = [data[col] for col in columns]

                query = f'INSERT INTO {self.table_name} ({", ".join(columns)}) VALUES ({placeholders})'

                cursor = conn.execute(query, values)
                success = cursor.rowcount > 0

                if success:
                    self.logger.info(f"Created {self.model_class.__name__}: {model.id}")

                return success

        except sqlite3.IntegrityError as e:
            self.logger.error(f"Integrity error creating {self.model_class.__name__}: {e}")
            raise ValidationError(f"Record already exists or violates constraints")
        except Exception as e:
            self.logger.error(f"Failed to create {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Creation failed: {e}")

    def get_by_id(self, record_id: str) -> Optional[BaseModel]:
        """Get record by ID"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(f'SELECT * FROM {self.table_name} WHERE id = ?', (record_id,))
                row = cursor.fetchone()

                if row:
                    return self._convert_row_to_model(row)
                return None

        except Exception as e:
            self.logger.error(f"Failed to get {self.model_class.__name__} {record_id}: {e}")
            raise DatabaseError(f"Lookup failed: {e}")

    def update(self, model: BaseModel) -> bool:
        """Update existing record"""
        try:
            with self.db_manager.transaction() as conn:
                data = self._convert_model_to_dict(model)
                data['updated_at'] = DateTimeHelper.to_iso_string(DateTimeHelper.now())

                # Build UPDATE query
                set_clause = ', '.join([f'{col} = ?' for col in data.keys() if col != 'id'])
                values = [data[col] for col in data.keys() if col != 'id']
                values.append(model.id)

                query = f'UPDATE {self.table_name} SET {set_clause} WHERE id = ?'

                cursor = conn.execute(query, values)
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to update {self.model_class.__name__} {model.id}: {e}")
            raise DatabaseError(f"Update failed: {e}")

    def delete(self, record_id: str) -> bool:
        """Delete record by ID"""
        try:
            with self.db_manager.transaction() as conn:
                cursor = conn.execute(f'DELETE FROM {self.table_name} WHERE id = ?', (record_id,))
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to delete {self.model_class.__name__} {record_id}: {e}")
            raise DatabaseError(f"Deletion failed: {e}")

    def list_all(self, limit: Optional[int] = None, offset: int = 0) -> List[BaseModel]:
        """List all records with optional pagination"""
        try:
            with self.db_manager.get_connection() as conn:
                query = f'SELECT * FROM {self.table_name} ORDER BY created_at DESC'
                params = []

                if limit is not None:
                    query += ' LIMIT ? OFFSET ?'
                    params.extend([limit, offset])

                cursor = conn.execute(query, params)
                return [self._convert_row_to_model(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to list {self.model_class.__name__} records: {e}")
            return []


# ============================================================================
# MODEL-SPECIFIC REPOSITORIES
# ============================================================================

class UserRepository(BaseRepository):
    """Repository for User model"""

    def __init__(self):
        super().__init__('users', User)

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('SELECT * FROM users WHERE username = ?', (username,))
                row = cursor.fetchone()

                if row:
                    return self._convert_row_to_model(row)
                return None

        except Exception as e:
            self.logger.error(f"Failed to get user by username {username}: {e}")
            return None

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('SELECT * FROM users WHERE email = ?', (email,))
                row = cursor.fetchone()

                if row:
                    return self._convert_row_to_model(row)
                return None

        except Exception as e:
            self.logger.error(f"Failed to get user by email {email}: {e}")
            return None

    def _convert_row_to_model(self, row: sqlite3.Row) -> User:
        """Convert database row to User model"""
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            first_name=row['first_name'] or '',
            last_name=row['last_name'] or '',
            role=UserRole(row['role']),
            status=UserStatus(row['status']),
            avatar_url=row['avatar_url'],
            bio=row['bio'] or '',
            skills=self._deserialize_json_field(row['skills'], list),
            preferences=self._deserialize_json_field(row['preferences']),
            last_login=DateTimeHelper.from_iso_string(row['last_login']) if row['last_login'] else None,
            login_attempts=row['login_attempts'] or 0,
            locked_until=DateTimeHelper.from_iso_string(row['locked_until']) if row['locked_until'] else None,
            api_key=row['api_key'],
            projects_created=row['projects_created'] or 0,
            sessions_completed=row['sessions_completed'] or 0,
            code_generated_lines=row['code_generated_lines'] or 0,
            created_at=DateTimeHelper.from_iso_string(row['created_at']),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at'])
        )


class ProjectRepository(BaseRepository):
    """Repository for Project model"""

    def __init__(self):
        super().__init__('projects', Project)

    def get_user_projects(self, user_id: str) -> List[Project]:
        """Get all projects for a user (owner or team member)"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM projects 
                    WHERE owner_id = ? OR team_members LIKE ?
                    ORDER BY updated_at DESC
                ''', (user_id, f'%"{user_id}"%'))

                return [self._convert_row_to_model(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get projects for user {user_id}: {e}")
            return []

    def _convert_row_to_model(self, row: sqlite3.Row) -> Project:
        """Convert database row to Project model"""
        return Project(
            id=row['id'],
            name=row['name'],
            description=row['description'] or '',
            owner_id=row['owner_id'],
            status=ProjectStatus(row['status']),
            phase=ProjectPhase(row['phase']),
            technology_stack=self._deserialize_json_field(row['technology_stack']),
            requirements=self._deserialize_json_field(row['requirements'], list),
            constraints=self._deserialize_json_field(row['constraints'], list),
            success_criteria=self._deserialize_json_field(row['success_criteria'], list),
            start_date=DateTimeHelper.from_iso_string(row['start_date']) if row['start_date'] else None,
            end_date=DateTimeHelper.from_iso_string(row['end_date']) if row['end_date'] else None,
            estimated_hours=row['estimated_hours'],
            budget=row['budget'],
            team_members=self._deserialize_json_field(row['team_members'], list),
            stakeholders=self._deserialize_json_field(row['stakeholders'], list),
            progress_percentage=row['progress_percentage'] or 0.0,
            completed_modules=row['completed_modules'] or 0,
            total_modules=row['total_modules'] or 0,
            generated_codebase_id=row['generated_codebase_id'],
            repository_url=row['repository_url'],
            deployment_url=row['deployment_url'],
            tags=self._deserialize_json_field(row['tags'], list),
            priority=TaskPriority(row['priority']),
            created_at=DateTimeHelper.from_iso_string(row['created_at']),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at'])
        )


class ModuleRepository(BaseRepository):
    """Repository for Module model"""

    def __init__(self):
        super().__init__('modules', Module)

    def get_project_modules(self, project_id: str) -> List[Module]:
        """Get all modules for a project"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM modules 
                    WHERE project_id = ? 
                    ORDER BY order_index, created_at
                ''', (project_id,))

                return [self._convert_row_to_model(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get modules for project {project_id}: {e}")
            return []

    def _convert_row_to_model(self, row: sqlite3.Row) -> Module:
        """Convert database row to Module model"""
        return Module(
            id=row['id'],
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'] or '',
            module_type=ModuleType(row['module_type']),
            parent_module_id=row['parent_module_id'],
            order=row['order_index'] or 0,
            dependencies=self._deserialize_json_field(row['dependencies'], list),
            technologies=self._deserialize_json_field(row['technologies'], list),
            apis_provided=self._deserialize_json_field(row['apis_provided'], list),
            apis_consumed=self._deserialize_json_field(row['apis_consumed'], list),
            status=TaskStatus(row['status']),
            progress_percentage=row['progress_percentage'] or 0.0,
            estimated_hours=row['estimated_hours'],
            actual_hours=row['actual_hours'],
            assigned_to=row['assigned_to'],
            reviewer=row['reviewer'],
            generated_files=self._deserialize_json_field(row['generated_files'], list),
            created_at=DateTimeHelper.from_iso_string(row['created_at']),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at'])
        )


class TaskRepository(BaseRepository):
    """Repository for Task model"""

    def __init__(self):
        super().__init__('tasks', Task)

    def get_module_tasks(self, module_id: str) -> List[Task]:
        """Get all tasks for a module"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM tasks 
                    WHERE module_id = ? 
                    ORDER BY priority DESC, created_at
                ''', (module_id,))

                return [self._convert_row_to_model(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get tasks for module {module_id}: {e}")
            return []

    def get_user_tasks(self, user_id: str) -> List[Task]:
        """Get all tasks assigned to a user"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM tasks 
                    WHERE assigned_to = ? 
                    ORDER BY priority DESC, due_date
                ''', (user_id,))

                return [self._convert_row_to_model(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get tasks for user {user_id}: {e}")
            return []

    def _convert_row_to_model(self, row: sqlite3.Row) -> Task:
        """Convert database row to Task model"""
        return Task(
            id=row['id'],
            module_id=row['module_id'],
            project_id=row['project_id'],
            title=row['title'],
            description=row['description'] or '',
            status=TaskStatus(row['status']),
            priority=TaskPriority(row['priority']),
            task_type=row['task_type'] or '',
            assigned_to=row['assigned_to'],
            estimated_hours=row['estimated_hours'],
            actual_hours=row['actual_hours'],
            due_date=DateTimeHelper.from_iso_string(row['due_date']) if row['due_date'] else None,
            completed_date=DateTimeHelper.from_iso_string(row['completed_date']) if row['completed_date'] else None,
            depends_on=self._deserialize_json_field(row['depends_on'], list),
            blocks=self._deserialize_json_field(row['blocks'], list),
            progress_percentage=row['progress_percentage'] or 0.0,
            notes=row['notes'] or '',
            related_files=self._deserialize_json_field(row['related_files'], list),
            created_at=DateTimeHelper.from_iso_string(row['created_at']),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at'])
        )


class SocraticSessionRepository(BaseRepository):
    """Repository for SocraticSession model"""

    def __init__(self):
        super().__init__('socratic_sessions', SocraticSession)

    def get_project_sessions(self, project_id: str) -> List[SocraticSession]:
        """Get all sessions for a project"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM socratic_sessions 
                    WHERE project_id = ? 
                    ORDER BY created_at DESC
                ''', (project_id,))

                return [self._convert_row_to_model(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get sessions for project {project_id}: {e}")
            return []

    def _convert_row_to_model(self, row: sqlite3.Row) -> SocraticSession:
        """Convert database row to SocraticSession model"""
        return SocraticSession(
            id=row['id'],
            project_id=row['project_id'],
            user_id=row['user_id'],
            current_role=TechnicalRole(row['current_role']),
            status=ConversationStatus(row['status']),
            roles_to_cover=[TechnicalRole(role) for role in self._deserialize_json_field(row['roles_to_cover'], list)],
            completed_roles=[TechnicalRole(role) for role in
                             self._deserialize_json_field(row['completed_roles'], list)],
            total_questions=row['total_questions'] or 0,
            questions_answered=row['questions_answered'] or 0,
            insights_generated=row['insights_generated'] or 0,
            conflicts_detected=row['conflicts_detected'] or 0,
            session_notes=row['session_notes'] or '',
            quality_score=row['quality_score'] or 0.0,
            completion_percentage=row['completion_percentage'] or 0.0,
            created_at=DateTimeHelper.from_iso_string(row['created_at']),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at'])
        )


class GeneratedCodebaseRepository(BaseRepository):
    """Repository for GeneratedCodebase model"""

    def __init__(self):
        super().__init__('generated_codebases', GeneratedCodebase)

    def get_project_codebase(self, project_id: str) -> Optional[GeneratedCodebase]:
        """Get codebase for a project"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM generated_codebases 
                    WHERE project_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ''', (project_id,))

                row = cursor.fetchone()
                if row:
                    return self._convert_row_to_model(row)
                return None

        except Exception as e:
            self.logger.error(f"Failed to get codebase for project {project_id}: {e}")
            return None

    def _convert_row_to_model(self, row: sqlite3.Row) -> GeneratedCodebase:
        """Convert database row to GeneratedCodebase model"""
        return GeneratedCodebase(
            id=row['id'],
            project_id=row['project_id'],
            spec_id=row['spec_id'],
            version=row['version'] or '1.0.0',
            architecture_type=row['architecture_type'] or '',
            technology_stack=self._deserialize_json_field(row['technology_stack']),
            file_structure=self._deserialize_json_field(row['file_structure']),
            generated_files=self._deserialize_json_field(row['generated_files'], list),
            total_lines_of_code=row['total_lines_of_code'] or 0,
            total_files=row['total_files'] or 0,
            code_quality_score=row['code_quality_score'] or 0.0,
            test_coverage=row['test_coverage'] or 0.0,
            generation_time_seconds=row['generation_time_seconds'] or 0.0,
            compilation_successful=bool(row['compilation_successful']),
            tests_passing=bool(row['tests_passing']),
            security_scan_results=self._deserialize_json_field(row['security_scan_results']),
            security_issues_count=row['security_issues_count'] or 0,
            critical_issues_count=row['critical_issues_count'] or 0,
            deployment_config=self._deserialize_json_field(row['deployment_config']),
            deployment_status=row['deployment_status'] or 'not_deployed',
            validation_results=self._deserialize_json_field(row['validation_results'], list),
            error_count=row['error_count'] or 0,
            warning_count=row['warning_count'] or 0,
            created_at=DateTimeHelper.from_iso_string(row['created_at']),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at'])
        )


class GeneratedFileRepository(BaseRepository):
    """Repository for GeneratedFile model"""

    def __init__(self):
        super().__init__('generated_files', GeneratedFile)

    def get_codebase_files(self, codebase_id: str) -> List[GeneratedFile]:
        """Get all files for a codebase"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM generated_files 
                    WHERE codebase_id = ? 
                    ORDER BY file_path
                ''', (codebase_id,))

                return [self._convert_row_to_model(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get files for codebase {codebase_id}: {e}")
            return []

    def get_project_files(self, project_id: str) -> List[GeneratedFile]:
        """Get all files for a project"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM generated_files 
                    WHERE project_id = ? 
                    ORDER BY file_path
                ''', (project_id,))

                return [self._convert_row_to_model(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get files for project {project_id}: {e}")
            return []

    def get_by_path(self, project_id: str, file_path: str) -> Optional[GeneratedFile]:
        """Get file by path within a project"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM generated_files 
                    WHERE project_id = ? AND file_path = ?
                ''', (project_id, file_path))

                row = cursor.fetchone()
                if row:
                    return self._convert_row_to_model(row)
                return None

        except Exception as e:
            self.logger.error(f"Failed to get file {file_path} for project {project_id}: {e}")
            return None

    def _convert_row_to_model(self, row: sqlite3.Row) -> GeneratedFile:
        """Convert database row to GeneratedFile model"""
        return GeneratedFile(
            id=row['id'],
            codebase_id=row['codebase_id'],
            project_id=row['project_id'],
            file_path=row['file_path'],
            file_type=FileType(row['file_type']),
            file_purpose=row['file_purpose'] or '',
            content=row['content'] or '',
            dependencies=self._deserialize_json_field(row['dependencies'], list),
            documentation=row['documentation'] or '',
            generated_by_agent=row['generated_by_agent'] or '',
            version=row['version'] or '1.0.0',
            size_bytes=row['size_bytes'] or 0,
            complexity_score=row['complexity_score'] or 0.0,
            test_coverage=row['test_coverage'] or 0.0,
            created_at=DateTimeHelper.from_iso_string(row['created_at']),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at'])
        )


class TestResultRepository(BaseRepository):
    """Repository for TestResult model"""

    def __init__(self):
        super().__init__('test_results', TestResult)

    def get_codebase_tests(self, codebase_id: str) -> List[TestResult]:
        """Get all test results for a codebase"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM test_results 
                    WHERE codebase_id = ? 
                    ORDER BY created_at DESC
                ''', (codebase_id,))

                return [self._convert_row_to_model(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get tests for codebase {codebase_id}: {e}")
            return []

    def get_project_tests(self, project_id: str) -> List[TestResult]:
        """Get all test results for a project"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM test_results 
                    WHERE project_id = ? 
                    ORDER BY created_at DESC
                ''', (project_id,))

                return [self._convert_row_to_model(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get tests for project {project_id}: {e}")
            return []

    def _convert_row_to_model(self, row: sqlite3.Row) -> TestResult:
        """Convert database row to TestResult model"""
        return TestResult(
            id=row['id'],
            codebase_id=row['codebase_id'],
            project_id=row['project_id'],
            test_type=TestType(row['test_type']),
            test_suite=row['test_suite'] or '',
            files_tested=self._deserialize_json_field(row['files_tested'], list),
            passed=bool(row['passed']),
            total_tests=row['total_tests'] or 0,
            passed_tests=row['passed_tests'] or 0,
            failed_tests=row['failed_tests'] or 0,
            skipped_tests=row['skipped_tests'] or 0,
            coverage_percentage=row['coverage_percentage'] or 0.0,
            failure_details=self._deserialize_json_field(row['failure_details'], list),
            stack_traces=self._deserialize_json_field(row['stack_traces'], list),
            memory_usage_mb=row['memory_usage_mb'] or 0.0,
            cpu_usage_percentage=row['cpu_usage_percentage'] or 0.0,
            test_environment=self._deserialize_json_field(row['test_environment']),
            created_at=DateTimeHelper.from_iso_string(row['created_at']),
            updated_at=DateTimeHelper.from_iso_string(row['updated_at'])
        )


class ProjectCollaboratorRepository(BaseRepository):
    """Repository for project collaborators"""

    def __init__(self):
        super().__init__('project_collaborators', BaseModel)  # Using BaseModel since we don't have a specific model

    def add_collaborator(self, project_id: str, username: str, role: str) -> bool:
        """Add collaborator to project"""
        try:
            with self.db_manager.transaction() as conn:
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO project_collaborators 
                    (project_id, username, role, joined_at, is_active)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    project_id, username, role,
                    DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                    True
                ))

                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to add collaborator {username} to {project_id}: {e}")
            return False

    def get_project_collaborators(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all collaborators for a project"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM project_collaborators 
                    WHERE project_id = ? AND is_active = 1
                    ORDER BY joined_at
                ''', (project_id,))

                collaborators = []
                for row in cursor.fetchall():
                    collaborators.append({
                        'username': row['username'],
                        'role': row['role'],
                        'joined_at': row['joined_at'],
                        'is_active': bool(row['is_active'])
                    })

                return collaborators

        except Exception as e:
            self.logger.error(f"Failed to get collaborators for project {project_id}: {e}")
            return []

    def remove_collaborator(self, project_id: str, username: str) -> bool:
        """Remove collaborator from project"""
        try:
            with self.db_manager.transaction() as conn:
                cursor = conn.execute('''
                    UPDATE project_collaborators 
                    SET is_active = 0 
                    WHERE project_id = ? AND username = ?
                ''', (project_id, username))

                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to remove collaborator {username} from {project_id}: {e}")
            return False

    def _convert_row_to_model(self, row: sqlite3.Row):
        """Convert database row to dict (no specific model)"""
        return {
            'project_id': row['project_id'],
            'username': row['username'],
            'role': row['role'],
            'joined_at': row['joined_at'],
            'is_active': bool(row['is_active'])
        }


# ============================================================================
# DATABASE SERVICE (MAIN INTERFACE)
# ============================================================================

class DatabaseService:
    """Main database service providing unified access to all repositories"""

    def __init__(self):
        self.logger = get_logger('database.service')

        # Initialize repositories
        self.users = UserRepository()
        self.projects = ProjectRepository()
        self.modules = ModuleRepository()
        self.tasks = TaskRepository()
        self.socratic_sessions = SocraticSessionRepository()
        self.generated_codebases = GeneratedCodebaseRepository()
        self.generated_files = GeneratedFileRepository()
        self.test_results = TestResultRepository()
        self.project_collaborators = ProjectCollaboratorRepository()  # Add this line

        # Note: Add other repositories as needed
        # self.questions = QuestionRepository()
        # self.conflicts = ConflictRepository()
        # self.technical_specs = TechnicalSpecRepository()
        # self.project_metrics = ProjectMetricsRepository()
        # self.user_activity = UserActivityRepository()

    def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            db_manager = DatabaseManager()
            if db_manager.health_check():
                stats = db_manager.get_stats()
                return {
                    'status': 'healthy',
                    'database_stats': stats,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Database connection failed',
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            }


# ============================================================================
# REPOSITORY MANAGER (COMPATIBILITY LAYER)
# ============================================================================

class RepositoryManager:
    """Repository manager providing unified access to all repositories"""

    def __init__(self):
        self.logger = get_logger('database.repo_manager')
        self._db_service = None

    @property
    def db_service(self):
        """Get database service instance"""
        if self._db_service is None:
            self._db_service = get_database()
        return self._db_service

    def get_repository(self, repository_name: str):
        """Get repository by name"""
        repository_map = {
            'user': self.db_service.users,
            'project': self.db_service.projects,
            'module': self.db_service.modules,
            'task': self.db_service.tasks,
            'socratic_session': self.db_service.socratic_sessions,
            'generated_codebase': self.db_service.generated_codebases,
            'generated_file': self.db_service.generated_files,
            'test_result': self.db_service.test_results,
            'project_collaborator': self.db_service.project_collaborators,
        }

        repository = repository_map.get(repository_name)
        if not repository:
            raise ValueError(f"Unknown repository: {repository_name}")

        return repository

    def health_check(self) -> Dict[str, Any]:
        """Check repository manager health"""
        return self.db_service.health_check()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_database() -> bool:
    """Initialize database schema and verify connectivity"""
    try:
        logger = get_logger('database.init')
        logger.info("Initializing database...")

        # Create schema
        schema = DatabaseSchema()
        schema.initialize_schema()

        # Verify database service
        db_service = DatabaseService()
        health = db_service.health_check()

        if health['status'] == 'healthy':
            logger.info("Database initialization completed successfully")
            return True
        else:
            logger.error(f"Database health check failed: {health}")
            return False

    except Exception as e:
        logger = get_logger('database.init')
        logger.error(f"Database initialization failed: {e}")
        return False


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


# Global repository manager instance
_repository_manager: Optional[RepositoryManager] = None


def get_repository_manager() -> RepositoryManager:
    """Get the global repository manager instance"""
    global _repository_manager
    if _repository_manager is None:
        _repository_manager = RepositoryManager()
    return _repository_manager


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Schema management
    'DatabaseSchema',

    # Repository classes
    'BaseRepository', 'UserRepository', 'ProjectRepository',
    'ModuleRepository', 'TaskRepository', 'SocraticSessionRepository',
    'GeneratedCodebaseRepository', 'GeneratedFileRepository', 'TestResultRepository',
    'ProjectCollaboratorRepository',

    # Service classes
    'DatabaseService', 'RepositoryManager',

    # Functions
    'init_database', 'get_database', 'get_repository_manager'
]

if __name__ == "__main__":
    # Test database functionality
    print("Testing database functionality...")

    try:
        # Initialize database
        if init_database():
            print("✅ Database initialization successful")
        else:
            print("❌ Database initialization failed")
            exit(1)

        # Test database service
        db = get_database()
        health = db.health_check()
        print(f"📊 Database health: {health['status']}")

        if health['status'] == 'healthy':
            print("🎉 Database system is ready!")
        else:
            print("⚠️ Database system has issues")

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        raise
