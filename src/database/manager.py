#!/usr/bin/env python3
"""
Database Manager - Connection and Schema Management
===================================================
Handles database connections, schema initialization, and core operations.
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Any

# Core imports with fallbacks
try:
    from src import get_config, get_logger
    from src.core import DateTimeHelper

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    import logging
    from datetime import datetime


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


# ==============================================================================
# EXCEPTIONS
# ==============================================================================

class DatabaseError(Exception):
    """Database operation error"""
    pass


# ==============================================================================
# DATABASE MANAGER
# ==============================================================================

class DatabaseManager:
    """Core database management with connection pooling and schema initialization"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            config = get_config()
            db_path = config.get('database', {}).get('path', 'data/socratic.db')

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

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                yield conn
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Connection failed: {e}")
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as list of dicts"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                columns = [col[0] for col in cursor.description] if cursor.description else []
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
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

    def _init_schema(self):
        """Initialize complete database schema"""
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
                        initiated_by TEXT NOT NULL,
                        session_type TEXT NOT NULL DEFAULT 'discovery',
                        status TEXT NOT NULL DEFAULT 'active',
                        current_phase TEXT NOT NULL DEFAULT 'discovery',
                        total_questions INTEGER DEFAULT 0,
                        answered_questions INTEGER DEFAULT 0,
                        session_data TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        completed_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES projects(id),
                        FOREIGN KEY (initiated_by) REFERENCES users(id)
                    )
                """)

                # Questions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS questions (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        question_number INTEGER NOT NULL,
                        phase TEXT NOT NULL,
                        question_text TEXT NOT NULL,
                        answer_text TEXT,
                        is_answered INTEGER DEFAULT 0,
                        context TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        answered_at TEXT,
                        FOREIGN KEY (session_id) REFERENCES socratic_sessions(id),
                        UNIQUE(session_id, question_number)
                    )
                """)

                # Conversation messages table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_messages (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        project_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        message_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        phase TEXT,
                        role TEXT,
                        author TEXT,
                        question_number INTEGER,
                        insights_extracted TEXT,
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
                        constraints TEXT,
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
                        project_id TEXT NOT NULL,
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
                        FOREIGN KEY (project_id) REFERENCES projects(id),
                        UNIQUE(project_id)
                    )
                """)

                # Module contexts table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS module_contexts (
                        id TEXT PRIMARY KEY,
                        module_id TEXT NOT NULL,
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
                        FOREIGN KEY (project_id) REFERENCES projects(id),
                        UNIQUE(module_id)
                    )
                """)

                # Task contexts table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS task_contexts (
                        id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
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
                        FOREIGN KEY (project_id) REFERENCES projects(id),
                        UNIQUE(task_id)
                    )
                """)

                # Create indexes for performance
                self._create_indexes(conn)

                conn.commit()
                self.logger.info("Database schema initialized successfully")

        except Exception as e:
            self.logger.error(f"Schema initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize schema: {e}")

    def _create_indexes(self, conn):
        """Create database indexes for query optimization"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_project ON socratic_sessions(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user ON socratic_sessions(initiated_by)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_status ON socratic_sessions(status)",
            "CREATE INDEX IF NOT EXISTS idx_questions_session ON questions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_session ON conversation_messages(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_project ON conversation_messages(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_specs_project ON technical_specifications(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_specs_session ON technical_specifications(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_collaborators_project ON project_collaborators(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_collaborators_user ON project_collaborators(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_project_contexts_project ON project_contexts(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_module_contexts_project ON module_contexts(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_contexts_project ON task_contexts(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_codebases_project ON generated_codebases(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_files_codebase ON generated_files(codebase_id)",
        ]

        for index_sql in indexes:
            try:
                conn.execute(index_sql)
            except Exception as e:
                self.logger.warning(f"Failed to create index: {e}")
