"""
Local database module for Socrates API

Provides minimal local persistence for API-specific data (projects, users, sessions).
Uses SQLite for simplicity - NOT replicated from PyPI libraries.
All components should use get_database() to access the database.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from socrates_api.exceptions import (
    DatabaseError,
    ProjectNotFoundError,
    UserNotFoundError,
)
from socrates_api.models_local import ProjectContext, User
from socrates_api.utils import IDGenerator

logger = logging.getLogger(__name__)


class LocalDatabase:
    """Minimal SQLite wrapper for API project and user data (local only)"""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize database connection"""
        if db_path is None:
            data_dir = Path.home() / ".socrates"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "api_projects.db")

        self.db_path = Path(db_path)
        self.conn = None
        self._initialize()

    def _initialize(self) -> None:
        """Create tables if they don't exist"""
        try:
            # SECURITY FIX: Enable timeout and disable threading bypass
            # Note: SQLite is not designed for concurrent writes - consider PostgreSQL for production
            self.conn = sqlite3.connect(
                str(self.db_path),
                timeout=10.0,  # 10 second timeout for database locks
                check_same_thread=False  # Allow threads (but ensure single write access via locks)
            )
            self.conn.row_factory = sqlite3.Row

            # Projects table - stores project metadata
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    owner TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    phase TEXT DEFAULT 'discovery',
                    is_archived INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)

            # Users table - stores user information
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    passcode_hash TEXT,
                    subscription_tier TEXT DEFAULT 'free',
                    subscription_status TEXT DEFAULT 'active',
                    testing_mode INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    metadata TEXT
                )
            """)

            # Refresh tokens table - stores refresh token hashes for authentication
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    revoked_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(username)
                )
            """)

            # Knowledge documents table - stores all knowledge base documents
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_documents (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    document_type TEXT DEFAULT 'text',
                    uploaded_at TEXT NOT NULL,
                    chunk_count INTEGER DEFAULT 0,
                    is_deleted INTEGER DEFAULT 0,
                    metadata TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(project_id, id)
                )
            """)

            # Team members table - stores project collaborators
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS team_members (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'viewer',
                    joined_at TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    skills TEXT,
                    metadata TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (username) REFERENCES users(username),
                    UNIQUE(project_id, username)
                )
            """)

            # User API keys table - stores user's API keys for different providers
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS user_api_keys (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(username),
                    UNIQUE(user_id, provider)
                )
            """)

            # Create indexes separately (SQLite doesn't support inline indexes)
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_tokens ON refresh_tokens(user_id)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expires ON refresh_tokens(expires_at)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_kb_project ON knowledge_documents(project_id)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_kb_user ON knowledge_documents(user_id)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_kb_deleted ON knowledge_documents(is_deleted)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tm_project ON team_members(project_id)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tm_username ON team_members(username)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_keys_user ON user_api_keys(user_id)"
            )

            # Question cache table - stores cached Socratic questions for performance
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS question_cache (
                    cache_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    phase TEXT,
                    category TEXT,
                    question_text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    used_count INTEGER DEFAULT 0,
                    last_used_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)

            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_question_cache_lookup ON question_cache(project_id, phase, category)"
            )

            # Conflict History Tables
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS conflict_history (
                    conflict_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    conflict_type TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    severity TEXT DEFAULT 'medium',
                    related_agents TEXT,
                    detected_at TEXT NOT NULL,
                    context TEXT,
                    metadata TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)

            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conflict_by_project ON conflict_history(project_id)"
            )

            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conflict_by_type ON conflict_history(project_id, conflict_type)"
            )

            # Conflict Resolutions Table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS conflict_resolutions (
                    resolution_id TEXT PRIMARY KEY,
                    conflict_id TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    rationale TEXT,
                    created_at TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (conflict_id) REFERENCES conflict_history(conflict_id) ON DELETE CASCADE
                )
            """)

            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_resolution_by_conflict ON conflict_resolutions(conflict_id)"
            )

            # Conflict Decisions Table (for versioning)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS conflict_decisions (
                    decision_id TEXT PRIMARY KEY,
                    conflict_id TEXT NOT NULL,
                    resolution_id TEXT,
                    chosen_proposal_id TEXT,
                    decided_by TEXT,
                    rationale TEXT,
                    version INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (conflict_id) REFERENCES conflict_history(conflict_id) ON DELETE CASCADE,
                    FOREIGN KEY (resolution_id) REFERENCES conflict_resolutions(resolution_id) ON DELETE SET NULL
                )
            """)

            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_decision_by_conflict ON conflict_decisions(conflict_id)"
            )

            self.conn.commit()

            # Perform schema migration for existing databases
            self._migrate_schema()

            logger.info(f"Local database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _migrate_schema(self) -> None:
        """Add missing columns to existing tables from previous schema versions"""
        try:
            # Get existing columns in projects table
            cursor = self.conn.execute("PRAGMA table_info(projects)")
            projects_columns = {row[1] for row in cursor.fetchall()}

            # Define required columns for projects table
            projects_required = {
                "owner": "ALTER TABLE projects ADD COLUMN owner TEXT",
                "phase": "ALTER TABLE projects ADD COLUMN phase TEXT DEFAULT 'discovery'",
                "is_archived": "ALTER TABLE projects ADD COLUMN is_archived INTEGER DEFAULT 0",
            }

            # Add any missing columns to projects
            for col_name, alter_sql in projects_required.items():
                if col_name not in projects_columns:
                    logger.info(f"Adding missing column to projects: {col_name}")
                    try:
                        self.conn.execute(alter_sql)
                        self.conn.commit()
                    except sqlite3.OperationalError as e:
                        # Column already exists (race condition in concurrent access)
                        if "duplicate column" not in str(e).lower():
                            raise

            # Get existing columns in users table
            cursor = self.conn.execute("PRAGMA table_info(users)")
            existing_columns = {row[1] for row in cursor.fetchall()}

            # Define required columns with their SQL definitions
            required_columns = {
                "passcode_hash": "ALTER TABLE users ADD COLUMN passcode_hash TEXT",
                "subscription_tier": "ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free'",
                "subscription_status": "ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'active'",
                "testing_mode": "ALTER TABLE users ADD COLUMN testing_mode INTEGER DEFAULT 0",
            }

            # Add any missing columns
            for col_name, alter_sql in required_columns.items():
                if col_name not in existing_columns:
                    logger.info(f"Adding missing column: {col_name}")
                    try:
                        self.conn.execute(alter_sql)
                        self.conn.commit()
                    except sqlite3.OperationalError as e:
                        # Column already exists (race condition in concurrent access)
                        if "duplicate column" not in str(e).lower():
                            raise

            logger.info("Schema migration completed successfully")
        except Exception as e:
            logger.error(f"Failed to migrate schema: {e}")
            # Don't raise - migration failure shouldn't crash initialization
            # The app can still work if migration partially succeeded

    # ========================================================================
    # Row Unpacking Helper Methods
    # ========================================================================
    # These helpers eliminate code duplication when converting database rows
    # to domain objects. Row format: [0]=id, [1]=owner, [2]=name, [3]=desc,
    # [4]=created_at, [5]=updated_at, [6]=phase, [7]=is_archived, [8]=metadata

    def _row_to_project(self, row) -> ProjectContext:
        """
        Convert a database row to a ProjectContext object.

        Row format: [id, owner, name, description, created_at, updated_at,
                    phase, is_archived, metadata_json]

        Args:
            row: sqlite3.Row object from projects table

        Returns:
            ProjectContext object with all fields populated
        """
        project = ProjectContext(
            project_id=row[0],
            owner=row[1],
            name=row[2],
            description=row[3],
            created_at=row[4],
            updated_at=row[5],
            phase=row[6],
            is_archived=row[7] == 1,
        )
        project.metadata = json.loads(row[8] or "{}")
        return project

    # ========================================================================
    # User row format: [0]=id, [1]=username, [2]=email, [3]=passcode_hash,
    # [4]=subscription_tier, [5]=subscription_status, [6]=testing_mode,
    # [7]=created_at, [8]=updated_at (skipped), [9]=metadata_json

    def _row_to_user(self, row) -> User:
        """
        Convert a database row to a User object.

        Row format: [id, username, email, passcode_hash, subscription_tier,
                    subscription_status, testing_mode, created_at, updated_at,
                    metadata_json]

        Note: updated_at is not stored in User model but is in database row[8]

        Args:
            row: sqlite3.Row object from users table

        Returns:
            User object with all fields populated
        """
        user = User(
            user_id=row[0],
            username=row[1],
            email=row[2],
            passcode_hash=row[3],
            subscription_tier=row[4],
            subscription_status=row[5],
            testing_mode=bool(row[6]),
            created_at=row[7],
        )
        user.metadata = json.loads(row[9] or "{}")
        return user

    def create_project(
        self,
        project_id: str,
        name: str,
        description: str = "",
        owner: str = None,
        metadata: Dict = None,
    ) -> ProjectContext:
        """
        Create a new project.

        Args:
            project_id: Unique project identifier
            name: Project name
            description: Project description (optional)
            owner: Owner username (optional)
            metadata: Additional metadata dictionary (optional)

        Returns:
            ProjectContext: The created project object

        Raises:
            DatabaseError: If project creation fails
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            meta_json = json.dumps(metadata or {})

            self.conn.execute(
                "INSERT INTO projects (id, owner, name, description, created_at, updated_at, phase, is_archived, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (project_id, owner, name, description, now, now, "discovery", 0, meta_json),
            )
            self.conn.commit()

            project = ProjectContext(
                project_id=project_id,
                name=name,
                description=description,
                owner=owner,
                created_at=now,
                updated_at=now,
                phase="discovery",
                is_archived=False,
            )
            project.metadata = metadata or {}
            return project
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise DatabaseError(
                f"Failed to create project {project_id}: {e}", operation="create_project"
            ) from e

    def get_project(self, project_id: str) -> ProjectContext:
        """
        Get project by ID.

        Args:
            project_id: The project ID to retrieve

        Returns:
            ProjectContext: The project object

        Raises:
            ProjectNotFoundError: If project does not exist
            DatabaseError: If database operation fails
        """
        try:
            cursor = self.conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if not row:
                raise ProjectNotFoundError(project_id)
            return self._row_to_project(row)
        except ProjectNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get project: {e}")
            raise DatabaseError(
                f"Failed to get project {project_id}: {e}", operation="get_project"
            ) from e

    def list_projects(self, limit: int = 100) -> List[ProjectContext]:
        """
        List all projects.

        Args:
            limit: Maximum number of projects to return (default: 100)

        Returns:
            List[ProjectContext]: List of project objects (empty list if no projects)

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            cursor = self.conn.execute("SELECT * FROM projects LIMIT ?", (limit,))
            projects = []
            for row in cursor.fetchall():
                projects.append(self._row_to_project(row))
            return projects
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            raise DatabaseError(f"Failed to list projects: {e}", operation="list_projects") from e

    def create_user(
        self,
        user_id: str,
        username: str,
        email: str = "",
        passcode_hash: str = "",
        metadata: Dict = None,
    ) -> Optional[User]:
        """Create a new user"""
        try:
            now = datetime.now(timezone.utc).isoformat()
            meta_json = json.dumps(metadata or {})

            self.conn.execute(
                "INSERT INTO users (id, username, email, passcode_hash, subscription_tier, subscription_status, testing_mode, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    username,
                    email,
                    passcode_hash or "",
                    "free",
                    "active",
                    0,
                    now,
                    now,
                    meta_json,
                ),
            )
            self.conn.commit()

            user = User(
                user_id=user_id,
                username=username,
                email=email,
                passcode_hash=passcode_hash or "",
                subscription_tier="free",
                subscription_status="active",
                testing_mode=False,
                created_at=now,
            )
            user.metadata = metadata or {}
            return user
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None

    def get_user(self, user_id: str) -> User:
        """
        Get user by ID.

        Args:
            user_id: The user ID to retrieve

        Returns:
            User: The user object

        Raises:
            UserNotFoundError: If user does not exist
            DatabaseError: If database operation fails
        """
        try:
            cursor = self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                raise UserNotFoundError(user_id)
            return self._row_to_user(row)
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            raise DatabaseError(f"Failed to get user {user_id}: {e}", operation="get_user") from e

    def load_user(self, username: str) -> User:
        """
        Get user by username.

        Args:
            username: The username to retrieve

        Returns:
            User: The user object

        Raises:
            UserNotFoundError: If user does not exist
            DatabaseError: If database operation fails
        """
        try:
            cursor = self.conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if not row:
                raise UserNotFoundError(username)
            return self._row_to_user(row)
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to load user by username: {e}")
            raise DatabaseError(
                f"Failed to load user {username}: {e}", operation="load_user"
            ) from e

    def load_user_by_email(self, email: str) -> User:
        """
        Get user by email.

        Args:
            email: The email address to retrieve

        Returns:
            User: The user object

        Raises:
            UserNotFoundError: If user does not exist
            DatabaseError: If database operation fails
        """
        try:
            cursor = self.conn.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if not row:
                raise UserNotFoundError(email)
            return self._row_to_user(row)
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to load user by email: {e}")
            raise DatabaseError(
                f"Failed to load user by email {email}: {e}", operation="load_user_by_email"
            ) from e

    def save_user(self, user_data: Union[Dict, User]) -> User:
        """
        Insert or update a user record. Accepts both dict and User objects.

        Args:
            user_data: User object or dictionary with user fields

        Returns:
            User: The saved/updated user object

        Raises:
            DatabaseError: If save operation fails
        """
        try:
            now = datetime.now(timezone.utc).isoformat()

            # Handle both dict and User object input
            if isinstance(user_data, User):
                user_id = user_data.id
                username = user_data.username
                email = user_data.email
                passcode_hash = user_data.passcode_hash
                subscription_tier = user_data.subscription_tier
                subscription_status = user_data.subscription_status
                testing_mode = int(user_data.testing_mode)
                metadata = user_data.metadata or {}
            else:
                user_id = user_data.get("id")
                username = user_data.get("username")
                email = user_data.get("email", "")
                passcode_hash = user_data.get("passcode_hash", "")
                subscription_tier = user_data.get("subscription_tier", "free")
                subscription_status = user_data.get("subscription_status", "active")
                testing_mode = int(user_data.get("testing_mode", False))
                metadata = user_data.get("metadata", {})

            meta_json = json.dumps(metadata)

            # Check if user exists
            existing = None
            if user_id:
                try:
                    existing = self.get_user(user_id)
                except (UserNotFoundError, DatabaseError):
                    existing = None

            if existing:
                # Update existing user
                self.conn.execute(
                    "UPDATE users SET username = ?, email = ?, passcode_hash = ?, subscription_tier = ?, subscription_status = ?, testing_mode = ?, updated_at = ?, metadata = ? WHERE id = ?",
                    (
                        username,
                        email,
                        passcode_hash,
                        subscription_tier,
                        subscription_status,
                        testing_mode,
                        now,
                        meta_json,
                        user_id,
                    ),
                )
            else:
                # Create new user
                if not user_id:
                    user_id = IDGenerator.user()
                created_at = (
                    user_data.get("created_at", now)
                    if isinstance(user_data, dict)
                    else (user_data.created_at or now)
                )
                self.conn.execute(
                    "INSERT INTO users (id, username, email, passcode_hash, subscription_tier, subscription_status, testing_mode, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        user_id,
                        username,
                        email,
                        passcode_hash,
                        subscription_tier,
                        subscription_status,
                        testing_mode,
                        created_at,
                        now,
                        meta_json,
                    ),
                )
            self.conn.commit()
            return self.get_user(user_id)
        except (UserNotFoundError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Failed to save user: {e}")
            raise DatabaseError(f"Failed to save user: {e}", operation="save_user") from e

    def user_exists(self, username: str) -> bool:
        """
        Check if a user exists by username.

        Args:
            username: Username to check

        Returns:
            True if user exists, False otherwise
        """
        try:
            cursor = self.conn.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.debug(f"Failed to check if user exists: {e}")
            return False

    def load_project(self, project_id: str) -> Optional[ProjectContext]:
        """Get project by ID (alias for get_project for compatibility)"""
        return self.get_project(project_id)

    def get_user_projects(self, username: str) -> List[ProjectContext]:
        """
        Get all non-archived projects for a user (both owned and collaborated).

        Args:
            username: Username to get projects for

        Returns:
            List[ProjectContext]: List of project objects (empty list if no projects)

        Raises:
            DatabaseError: If database operation fails
        """
        try:

            # Return only active (non-archived) projects owned by the user
            # Archived projects should not count toward subscription limits
            cursor = self.conn.execute(
                "SELECT * FROM projects WHERE owner = ? AND is_archived = 0 ORDER BY updated_at DESC", (username,)
            )
            projects = []
            for row in cursor.fetchall():
                projects.append(self._row_to_project(row))
            return projects
        except Exception as e:
            logger.error(f"Failed to get user projects: {e}")
            raise DatabaseError(
                f"Failed to get projects for user {username}: {e}", operation="get_user_projects"
            ) from e

    def save_project(self, project) -> ProjectContext:
        """
        Save or update a project.

        Args:
            project: ProjectContext object to save

        Returns:
            ProjectContext: The saved/updated project object

        Raises:
            DatabaseError: If save operation fails
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            project_id = project.project_id
            owner = getattr(project, "owner", None)
            name = project.name
            description = getattr(project, "description", "")
            phase = getattr(project, "phase", "discovery")
            is_archived = int(getattr(project, "is_archived", False))
            metadata = json.dumps(getattr(project, "metadata", {}))

            # Check if project exists
            cursor = self.conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
            exists = cursor.fetchone() is not None

            if exists:
                # Update
                self.conn.execute(
                    "UPDATE projects SET owner = ?, name = ?, description = ?, phase = ?, is_archived = ?, updated_at = ?, metadata = ? WHERE id = ?",
                    (owner, name, description, phase, is_archived, now, metadata, project_id),
                )
            else:
                # Insert
                created_at = getattr(project, "created_at", now)
                self.conn.execute(
                    "INSERT INTO projects (id, owner, name, description, phase, is_archived, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        project_id,
                        owner,
                        name,
                        description,
                        phase,
                        is_archived,
                        created_at,
                        now,
                        metadata,
                    ),
                )
            self.conn.commit()
            return self.get_project(project_id)
        except (ProjectNotFoundError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            raise DatabaseError(
                f"Failed to save project {project.project_id}: {e}", operation="save_project"
            ) from e

    def save_knowledge_document(
        self,
        user_id: str,
        project_id: str,
        doc_id: str,
        title: str,
        content: str,
        source: str,
        document_type: str,
    ) -> bool:
        """Save a knowledge document to database"""
        try:
            now = datetime.now(timezone.utc).isoformat()
            meta_json = json.dumps({})

            self.conn.execute(
                "INSERT OR REPLACE INTO knowledge_documents "
                "(id, project_id, user_id, title, content, source, document_type, uploaded_at, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (doc_id, project_id, user_id, title, content, source, document_type, now, meta_json)
            )
            self.conn.commit()
            logger.info(f"Knowledge document {doc_id} saved for project {project_id}: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to save knowledge document: {e}")
            return False

    def get_knowledge_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a single knowledge document by ID from database"""
        try:
            cursor = self.conn.execute(
                "SELECT id, project_id, user_id, title, content, source, document_type, uploaded_at, metadata "
                "FROM knowledge_documents WHERE id = ? AND is_deleted = 0",
                (document_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "project_id": row[1],
                "user_id": row[2],
                "title": row[3],
                "content": row[4],
                "source": row[5],
                "document_type": row[6],
                "uploaded_at": row[7],
                "metadata": json.loads(row[8] or "{}"),
            }
        except Exception as e:
            logger.debug(f"Failed to get knowledge document {document_id}: {e}")
            return None

    def get_project_knowledge_documents(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all knowledge documents for a project from database"""
        try:
            cursor = self.conn.execute(
                "SELECT id, project_id, user_id, title, content, source, document_type, uploaded_at, metadata "
                "FROM knowledge_documents WHERE project_id = ? AND is_deleted = 0 "
                "ORDER BY uploaded_at DESC",
                (project_id,)
            )

            documents = []
            for row in cursor.fetchall():
                documents.append({
                    "id": row[0],
                    "project_id": row[1],
                    "user_id": row[2],
                    "title": row[3],
                    "content": row[4],
                    "source": row[5],
                    "document_type": row[6],
                    "uploaded_at": row[7],
                    "metadata": json.loads(row[8] or "{}"),
                })
            return documents
        except Exception as e:
            logger.debug(f"Failed to get project knowledge documents for {project_id}: {e}")
            return []

    def get_user_knowledge_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all knowledge documents for a user from database"""
        try:
            cursor = self.conn.execute(
                "SELECT id, project_id, user_id, title, content, source, document_type, uploaded_at, metadata "
                "FROM knowledge_documents WHERE user_id = ? AND is_deleted = 0 "
                "ORDER BY uploaded_at DESC",
                (user_id,)
            )

            documents = []
            for row in cursor.fetchall():
                documents.append({
                    "id": row[0],
                    "project_id": row[1],
                    "user_id": row[2],
                    "title": row[3],
                    "content": row[4],
                    "source": row[5],
                    "document_type": row[6],
                    "uploaded_at": row[7],
                    "metadata": json.loads(row[8] or "{}"),
                })
            return documents
        except Exception as e:
            logger.debug(f"Failed to get user knowledge documents for {user_id}: {e}")
            return []

    def add_team_member(self, project_id: str, username: str, role: str) -> bool:
        """
        Add a team member to a project.

        Args:
            project_id: Project ID
            username: Username to add
            role: Role (owner, editor, viewer)

        Returns:
            True if successful, False otherwise
        """
        try:
            member_id = f"tm_{project_id}_{username}"
            now = datetime.now(timezone.utc).isoformat()

            self.conn.execute(
                "INSERT OR REPLACE INTO team_members "
                "(id, project_id, username, role, joined_at, status, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (member_id, project_id, username, role, now, "active", "{}")
            )
            self.conn.commit()
            logger.info(f"Added team member {username} to project {project_id} with role {role}")
            return True
        except Exception as e:
            logger.debug(f"Failed to add team member: {e}")
            return False

    def remove_team_member(self, project_id: str, username: str) -> bool:
        """
        Remove a team member from a project.

        Args:
            project_id: Project ID
            username: Username to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn.execute(
                "DELETE FROM team_members WHERE project_id = ? AND username = ?",
                (project_id, username)
            )
            self.conn.commit()
            logger.info(f"Removed team member {username} from project {project_id}")
            return True
        except Exception as e:
            logger.debug(f"Failed to remove team member: {e}")
            return False

    def get_project_team_members(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all team members for a project.

        Args:
            project_id: Project ID

        Returns:
            List of team member dictionaries
        """
        try:
            cursor = self.conn.execute(
                "SELECT id, project_id, username, role, joined_at, status, metadata "
                "FROM team_members WHERE project_id = ? AND status = 'active' "
                "ORDER BY joined_at DESC",
                (project_id,)
            )

            members = []
            for row in cursor.fetchall():
                members.append({
                    "id": row[0],
                    "project_id": row[1],
                    "username": row[2],
                    "role": row[3],
                    "joined_at": row[4],
                    "status": row[5],
                    "metadata": json.loads(row[6] or "{}"),
                })
            return members
        except Exception as e:
            logger.debug(f"Failed to get project team members: {e}")
            return []

    def get_user_projects_as_collaborator(self, username: str) -> List[str]:
        """
        Get project IDs where user is a collaborator (not owner).

        Args:
            username: Username to check

        Returns:
            List of project IDs
        """
        try:
            cursor = self.conn.execute(
                "SELECT project_id FROM team_members WHERE username = ? AND status = 'active'",
                (username,)
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.debug(f"Failed to get user collaborator projects: {e}")
            return []

    def save_api_key(self, user_id: str, provider: str, api_key: str) -> bool:
        """
        Save or update a user's API key for a provider.

        Args:
            user_id: User ID (username)
            provider: LLM provider name (e.g., 'anthropic', 'openai')
            api_key: The API key to store

        Returns:
            True if saved successfully

        Raises:
            DatabaseError: If save operation fails
        """
        try:
            from socrates_api.utils import IDGenerator
            now = datetime.now(timezone.utc).isoformat()
            key_id = IDGenerator.generate_id("apikey")

            self.conn.execute(
                """
                INSERT OR REPLACE INTO user_api_keys (id, user_id, provider, api_key, created_at, updated_at)
                VALUES (
                    COALESCE((SELECT id FROM user_api_keys WHERE user_id = ? AND provider = ?), ?),
                    ?,
                    ?,
                    ?,
                    COALESCE((SELECT created_at FROM user_api_keys WHERE user_id = ? AND provider = ?), ?),
                    ?
                )
                """,
                (user_id, provider, key_id, user_id, provider, api_key, user_id, provider, now, now)
            )
            self.conn.commit()
            logger.info(f"API key saved for user {user_id} provider {provider}")
            return True
        except Exception as e:
            logger.error(f"Failed to save API key: {e}")
            raise DatabaseError(
                f"Failed to save API key for {provider}: {e}", operation="save_api_key"
            ) from e

    def get_api_key(self, user_id: str, provider: str) -> Optional[str]:
        """
        Get a user's API key for a provider.

        Args:
            user_id: User ID (username)
            provider: LLM provider name (e.g., 'anthropic', 'openai')

        Returns:
            The API key if found, None otherwise
        """
        try:
            cursor = self.conn.execute(
                "SELECT api_key FROM user_api_keys WHERE user_id = ? AND provider = ?",
                (user_id, provider)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get API key: {e}")
            return None

    def delete_api_key(self, user_id: str, provider: str) -> bool:
        """
        Delete a user's API key for a provider.

        Args:
            user_id: User ID (username)
            provider: LLM provider name (e.g., 'anthropic', 'openai')

        Returns:
            True if deleted successfully or key didn't exist

        Raises:
            DatabaseError: If delete operation fails
        """
        try:
            self.conn.execute(
                "DELETE FROM user_api_keys WHERE user_id = ? AND provider = ?",
                (user_id, provider)
            )
            self.conn.commit()
            logger.info(f"API key deleted for user {user_id} provider {provider}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            raise DatabaseError(
                f"Failed to delete API key for {provider}: {e}", operation="delete_api_key"
            ) from e

    def set_user_default_provider(self, user_id: str, provider: str) -> bool:
        """
        Set user's default LLM provider.

        Args:
            user_id: User ID (username)
            provider: Provider name (anthropic, openai, google, etc.)

        Returns:
            True if set successfully
        """
        try:
            user = self.load_user(user_id)
            if user:
                if not user.metadata:
                    user.metadata = {}
                user.metadata["default_provider"] = provider
                self.save_user(user)
                logger.info(f"Default provider set to {provider} for user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to set default provider: {e}")
            return False

    def get_user_default_provider(self, user_id: str) -> str:
        """
        Get user's default LLM provider.

        Args:
            user_id: User ID (username)

        Returns:
            Provider name, defaults to "anthropic" if not set
        """
        try:
            user = self.load_user(user_id)
            if user and user.metadata:
                provider = user.metadata.get("default_provider")
                if provider:
                    return provider
            return "anthropic"  # Default fallback
        except Exception as e:
            logger.error(f"Failed to get default provider: {e}")
            return "anthropic"

    def set_provider_model(self, user_id: str, provider: str, model: str) -> bool:
        """
        Set user's preferred model for a specific provider.

        Args:
            user_id: User ID (username)
            provider: Provider name (anthropic, openai, google, etc.)
            model: Model name (e.g., claude-3-sonnet, gpt-4, gemini-pro)

        Returns:
            True if set successfully
        """
        try:
            user = self.load_user(user_id)
            if user:
                if not user.metadata:
                    user.metadata = {}
                if "provider_models" not in user.metadata:
                    user.metadata["provider_models"] = {}
                user.metadata["provider_models"][provider] = model
                self.save_user(user)
                logger.info(f"Model set to {model} for {provider} for user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to set provider model: {e}")
            return False

    def get_provider_model(self, user_id: str, provider: str) -> str:
        """
        Get user's preferred model for a specific provider.

        Args:
            user_id: User ID (username)
            provider: Provider name (anthropic, openai, google, etc.)

        Returns:
            Model name, defaults based on provider if not set
        """
        try:
            user = self.load_user(user_id)
            if user and user.metadata:
                provider_models = user.metadata.get("provider_models", {})
                if provider_models:
                    model = provider_models.get(provider)
                    if model:
                        return model

            # Fallback to sensible defaults
            defaults = {
                "anthropic": "claude-3-sonnet",
                "openai": "gpt-4",
                "google": "gemini-pro"
            }
            return defaults.get(provider, "claude-3-sonnet")
        except Exception as e:
            logger.error(f"Failed to get provider model: {e}")
            return "claude-3-sonnet"

    def delete_project(self, project_id: str) -> bool:
        """
        Delete (archive) a project.

        Args:
            project_id: Project ID to archive

        Returns:
            True if project was archived successfully

        Raises:
            DatabaseError: If delete operation fails
        """
        try:
            self.conn.execute("UPDATE projects SET is_archived = 1 WHERE id = ?", (project_id,))
            self.conn.commit()
            logger.info(f"Project {project_id} archived")
            return True
        except Exception as e:
            logger.error(f"Failed to archive project {project_id}: {e}")
            raise DatabaseError(
                f"Failed to delete project {project_id}: {e}", operation="delete_project"
            ) from e

    def permanently_delete_user(self, username: str) -> bool:
        """
        Permanently delete a user and all associated data.

        Args:
            username: Username to delete

        Returns:
            True if user was deleted successfully

        Raises:
            DatabaseError: If delete operation fails
        """
        try:
            # Delete refresh tokens
            self.conn.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (username,))
            # Delete projects
            self.conn.execute("DELETE FROM projects WHERE owner = ?", (username,))
            # Delete user
            self.conn.execute("DELETE FROM users WHERE username = ?", (username,))
            self.conn.commit()
            logger.info(f"User {username} permanently deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to permanently delete user {username}: {e}")
            raise DatabaseError(
                f"Failed to delete user {username}: {e}", operation="permanently_delete_user"
            ) from e

    # ============ Question Cache Methods ============

    def save_cached_question(
        self, project_id: str, phase: str, category: Optional[str], question_text: str
    ) -> str:
        """
        Save a question to the cache.

        Args:
            project_id: Project ID
            phase: Project phase (e.g., 'discovery', 'design')
            category: Question category (optional)
            question_text: The question text to cache

        Returns:
            cache_id of the saved question

        Raises:
            DatabaseError: If save fails
        """
        try:
            cache_id = IDGenerator.generate("cache")
            now = datetime.now(timezone.utc).isoformat()

            self.conn.execute(
                """
                INSERT INTO question_cache
                (cache_id, project_id, phase, category, question_text, created_at, used_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (cache_id, project_id, phase, category, question_text, now, 0),
            )
            self.conn.commit()

            logger.debug(f"Cached question {cache_id} for project {project_id}")
            return cache_id

        except Exception as e:
            logger.error(f"Failed to cache question: {e}")
            raise DatabaseError(f"Failed to cache question: {e}", operation="save_cached_question") from e

    def get_cached_questions(
        self,
        project_id: str,
        phase: Optional[str] = None,
        category: Optional[str] = None,
        exclude_recent: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve cached questions for a project.

        Args:
            project_id: Project ID
            phase: Filter by phase (optional)
            category: Filter by category (optional)
            exclude_recent: Exclude N most recently used questions

        Returns:
            List of cached question dicts with cache_id, question_text, used_count

        Raises:
            DatabaseError: If query fails
        """
        try:
            query = """
                SELECT cache_id, question_text, used_count, created_at
                FROM question_cache
                WHERE project_id = ?
            """
            params = [project_id]

            if phase:
                query += " AND phase = ?"
                params.append(phase)

            if category:
                query += " AND category = ?"
                params.append(category)

            # Order by used_count (prefer less-used questions)
            query += " ORDER BY used_count ASC, created_at DESC LIMIT 100"

            cursor = self.conn.execute(query, params)
            rows = cursor.fetchall()

            # Convert to dicts and exclude recent ones
            questions = []
            for i, row in enumerate(rows):
                if i < exclude_recent:
                    continue  # Skip recent questions
                questions.append(
                    {
                        "cache_id": row["cache_id"],
                        "question_text": row["question_text"],
                        "used_count": row["used_count"],
                        "created_at": row["created_at"],
                    }
                )

            logger.debug(
                f"Retrieved {len(questions)} cached questions for project {project_id}"
            )
            return questions

        except Exception as e:
            logger.error(f"Failed to retrieve cached questions: {e}")
            raise DatabaseError(
                f"Failed to retrieve cached questions: {e}", operation="get_cached_questions"
            ) from e

    def increment_question_usage(self, cache_id: str) -> bool:
        """
        Increment usage count and update last_used_at for a cached question.

        Args:
            cache_id: Cache ID of the question

        Returns:
            True if successful

        Raises:
            DatabaseError: If update fails
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            self.conn.execute(
                """
                UPDATE question_cache
                SET used_count = used_count + 1, last_used_at = ?
                WHERE cache_id = ?
                """,
                (now, cache_id),
            )
            self.conn.commit()

            logger.debug(f"Incremented usage for cached question {cache_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to increment question usage: {e}")
            raise DatabaseError(
                f"Failed to increment question usage: {e}", operation="increment_question_usage"
            ) from e

    def clear_question_cache(self, project_id: str, phase: Optional[str] = None) -> int:
        """
        Clear cached questions for a project.

        Args:
            project_id: Project ID
            phase: Optional phase to filter (clear only that phase)

        Returns:
            Number of questions deleted

        Raises:
            DatabaseError: If delete fails
        """
        try:
            query = "DELETE FROM question_cache WHERE project_id = ?"
            params = [project_id]

            if phase:
                query += " AND phase = ?"
                params.append(phase)

            cursor = self.conn.execute(query, params)
            count = cursor.rowcount
            self.conn.commit()

            logger.info(f"Cleared {count} cached questions for project {project_id}, phase={phase}")
            return count

        except Exception as e:
            logger.error(f"Failed to clear question cache: {e}")
            raise DatabaseError(
                f"Failed to clear question cache: {e}", operation="clear_question_cache"
            ) from e

    def prune_question_cache(self, project_id: str, max_questions: int = 50) -> int:
        """
        Prune question cache to keep only most recent questions.

        Args:
            project_id: Project ID
            max_questions: Maximum questions to keep per project

        Returns:
            Number of questions deleted

        Raises:
            DatabaseError: If delete fails
        """
        try:
            # Find questions to delete (keep newest ones)
            cursor = self.conn.execute(
                """
                SELECT cache_id FROM question_cache
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT -1 OFFSET ?
                """,
                (project_id, max_questions),
            )
            to_delete = [row["cache_id"] for row in cursor.fetchall()]

            if to_delete:
                placeholders = ",".join("?" * len(to_delete))
                self.conn.execute(
                    f"DELETE FROM question_cache WHERE cache_id IN ({placeholders})",
                    to_delete,
                )
                self.conn.commit()

            logger.debug(f"Pruned {len(to_delete)} questions from cache for project {project_id}")
            return len(to_delete)

        except Exception as e:
            logger.error(f"Failed to prune question cache: {e}")
            raise DatabaseError(
                f"Failed to prune question cache: {e}", operation="prune_question_cache"
            ) from e

    # ========================================================================
    # CONFLICT HISTORY MANAGEMENT
    # ========================================================================

    def save_conflict(
        self,
        project_id: str,
        conflict_id: str,
        conflict_type: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        severity: str = "medium",
        related_agents: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Save a conflict to history"""
        try:
            agents_str = json.dumps(related_agents or [])
            context_str = json.dumps(context or {})
            metadata_str = json.dumps(metadata or {})
            now = datetime.now(timezone.utc).isoformat()

            self.conn.execute(
                """INSERT OR REPLACE INTO conflict_history
                   (conflict_id, project_id, conflict_type, title, description, severity,
                    related_agents, detected_at, context, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (conflict_id, project_id, conflict_type, title, description, severity,
                 agents_str, now, context_str, metadata_str),
            )
            self.conn.commit()
            logger.debug(f"Saved conflict {conflict_id} for project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save conflict: {e}")
            return False

    def get_conflict_history(
        self, project_id: str, conflict_type: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conflict history for a project"""
        try:
            if conflict_type:
                query = """SELECT * FROM conflict_history
                          WHERE project_id = ? AND conflict_type = ?
                          ORDER BY detected_at DESC LIMIT ?"""
                cursor = self.conn.execute(query, (project_id, conflict_type, limit))
            else:
                query = """SELECT * FROM conflict_history
                          WHERE project_id = ?
                          ORDER BY detected_at DESC LIMIT ?"""
                cursor = self.conn.execute(query, (project_id, limit))

            conflicts = []
            for row in cursor.fetchall():
                conflict = {
                    "conflict_id": row[0],
                    "project_id": row[1],
                    "conflict_type": row[2],
                    "title": row[3],
                    "description": row[4],
                    "severity": row[5],
                    "related_agents": json.loads(row[6]),
                    "detected_at": row[7],
                    "context": json.loads(row[8]),
                    "metadata": json.loads(row[9]),
                }
                conflicts.append(conflict)
            return conflicts
        except Exception as e:
            logger.error(f"Failed to get conflict history: {e}")
            return []

    def save_resolution(
        self,
        resolution_id: str,
        conflict_id: str,
        strategy: str,
        confidence: float = 0.0,
        rationale: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Save a conflict resolution"""
        try:
            metadata_str = json.dumps(metadata or {})
            now = datetime.now(timezone.utc).isoformat()

            self.conn.execute(
                """INSERT OR REPLACE INTO conflict_resolutions
                   (resolution_id, conflict_id, strategy, confidence, rationale, created_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (resolution_id, conflict_id, strategy, confidence, rationale, now, metadata_str),
            )
            self.conn.commit()
            logger.debug(f"Saved resolution {resolution_id} for conflict {conflict_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save resolution: {e}")
            return False

    def get_conflict_resolutions(self, conflict_id: str) -> List[Dict[str, Any]]:
        """Get all resolutions for a conflict"""
        try:
            query = """SELECT * FROM conflict_resolutions WHERE conflict_id = ? ORDER BY created_at ASC"""
            cursor = self.conn.execute(query, (conflict_id,))

            resolutions = []
            for row in cursor.fetchall():
                resolution = {
                    "resolution_id": row[0],
                    "conflict_id": row[1],
                    "strategy": row[2],
                    "confidence": row[3],
                    "rationale": row[4],
                    "created_at": row[5],
                    "metadata": json.loads(row[6]),
                }
                resolutions.append(resolution)
            return resolutions
        except Exception as e:
            logger.error(f"Failed to get conflict resolutions: {e}")
            return []

    def save_decision(
        self,
        decision_id: str,
        conflict_id: str,
        resolution_id: Optional[str] = None,
        chosen_proposal_id: Optional[str] = None,
        decided_by: Optional[str] = None,
        rationale: Optional[str] = None,
        version: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Save a conflict decision (with versioning)"""
        try:
            metadata_str = json.dumps(metadata or {})
            now = datetime.now(timezone.utc).isoformat()

            self.conn.execute(
                """INSERT INTO conflict_decisions
                   (decision_id, conflict_id, resolution_id, chosen_proposal_id,
                    decided_by, rationale, version, created_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (decision_id, conflict_id, resolution_id, chosen_proposal_id,
                 decided_by, rationale, version, now, metadata_str),
            )
            self.conn.commit()
            logger.debug(f"Saved decision {decision_id} for conflict {conflict_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save decision: {e}")
            return False

    def get_conflict_decisions(self, conflict_id: str) -> List[Dict[str, Any]]:
        """Get all decisions for a conflict (with versions)"""
        try:
            query = """SELECT * FROM conflict_decisions WHERE conflict_id = ? ORDER BY version ASC"""
            cursor = self.conn.execute(query, (conflict_id,))

            decisions = []
            for row in cursor.fetchall():
                decision = {
                    "decision_id": row[0],
                    "conflict_id": row[1],
                    "resolution_id": row[2],
                    "chosen_proposal_id": row[3],
                    "decided_by": row[4],
                    "rationale": row[5],
                    "version": row[6],
                    "created_at": row[7],
                    "metadata": json.loads(row[8]),
                }
                decisions.append(decision)
            return decisions
        except Exception as e:
            logger.error(f"Failed to get conflict decisions: {e}")
            return []

    def get_conflict_statistics(self, project_id: str) -> Dict[str, Any]:
        """Get conflict statistics for a project"""
        try:
            # Total conflicts
            cursor = self.conn.execute(
                "SELECT COUNT(*) FROM conflict_history WHERE project_id = ?",
                (project_id,),
            )
            total_conflicts = cursor.fetchone()[0]

            # By type
            cursor = self.conn.execute(
                """SELECT conflict_type, COUNT(*) FROM conflict_history
                   WHERE project_id = ? GROUP BY conflict_type""",
                (project_id,),
            )
            conflict_types = {row[0]: row[1] for row in cursor.fetchall()}

            # By severity
            cursor = self.conn.execute(
                """SELECT severity, COUNT(*) FROM conflict_history
                   WHERE project_id = ? GROUP BY severity""",
                (project_id,),
            )
            severities = {row[0]: row[1] for row in cursor.fetchall()}

            # Resolution strategies used
            cursor = self.conn.execute(
                """SELECT r.strategy, COUNT(*) FROM conflict_resolutions r
                   JOIN conflict_history c ON r.conflict_id = c.conflict_id
                   WHERE c.project_id = ? GROUP BY r.strategy""",
                (project_id,),
            )
            strategies = {row[0]: row[1] for row in cursor.fetchall()}

            # Resolved count (has at least one decision)
            cursor = self.conn.execute(
                """SELECT COUNT(DISTINCT c.conflict_id) FROM conflict_history c
                   WHERE c.project_id = ? AND EXISTS
                   (SELECT 1 FROM conflict_decisions d WHERE d.conflict_id = c.conflict_id)""",
                (project_id,),
            )
            resolved_count = cursor.fetchone()[0]

            return {
                "total_conflicts": total_conflicts,
                "resolved_conflicts": resolved_count,
                "unresolved_conflicts": total_conflicts - resolved_count,
                "resolution_rate": resolved_count / total_conflicts if total_conflicts > 0 else 0.0,
                "conflict_types": conflict_types,
                "severities": severities,
                "strategies_used": strategies,
            }
        except Exception as e:
            logger.error(f"Failed to get conflict statistics: {e}")
            return {}

    def close(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()


class DatabaseSingleton:
    """Singleton for local database - API only"""

    _instance: LocalDatabase = None
    _db_path: str = None

    @classmethod
    def initialize(cls, db_path: str = None) -> None:
        """Initialize the database singleton"""
        cls._db_path = db_path
        cls._instance = None

    @classmethod
    def get_instance(cls) -> LocalDatabase:
        """Get or create the global database instance"""
        if cls._instance is None:
            cls._instance = LocalDatabase(cls._db_path)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing)"""
        if cls._instance:
            cls._instance.close()
        cls._instance = None
        cls._db_path = None


# FastAPI dependency
def get_database() -> LocalDatabase:
    """FastAPI dependency that gets the database instance"""
    return DatabaseSingleton.get_instance()


def close_database() -> None:
    """Close the global database connection"""
    try:
        DatabaseSingleton.reset()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


def reset_database() -> None:
    """Reset the database instance (for testing)"""
    close_database()
