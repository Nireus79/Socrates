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
from typing import Dict, List, Optional, Union

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
            now = datetime.utcnow().isoformat()
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
            now = datetime.utcnow().isoformat()
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
            now = datetime.utcnow().isoformat()

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
        Get all projects for a user (both owned and collaborated).

        Args:
            username: Username to get projects for

        Returns:
            List[ProjectContext]: List of project objects (empty list if no projects)

        Raises:
            DatabaseError: If database operation fails
        """
        try:

            # For now, return all projects owned by the user
            # Collaboration support can be added later with a separate table
            cursor = self.conn.execute(
                "SELECT * FROM projects WHERE owner = ? ORDER BY updated_at DESC", (username,)
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
            now = datetime.utcnow().isoformat()
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

    def get_api_key(self, username: str, provider: str) -> Optional[str]:
        """Get API key for a user and provider (stub - not persisted)"""
        # In production, this would be stored in database
        # For now, return None (API key not found)
        return None

    def delete_project(self, project_id: str) -> None:
        """
        Delete (archive) a project.

        Args:
            project_id: Project ID to archive

        Raises:
            DatabaseError: If delete operation fails
        """
        try:
            self.conn.execute("UPDATE projects SET is_archived = 1 WHERE id = ?", (project_id,))
            self.conn.commit()
            logger.info(f"Project {project_id} archived")
        except Exception as e:
            logger.error(f"Failed to archive project {project_id}: {e}")
            raise DatabaseError(
                f"Failed to delete project {project_id}: {e}", operation="delete_project"
            ) from e

    def permanently_delete_user(self, username: str) -> None:
        """
        Permanently delete a user and all associated data.

        Args:
            username: Username to delete

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
        except Exception as e:
            logger.error(f"Failed to permanently delete user {username}: {e}")
            raise DatabaseError(
                f"Failed to delete user {username}: {e}", operation="permanently_delete_user"
            ) from e

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
