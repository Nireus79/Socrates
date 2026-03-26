"""
Local database module for Socrates API

Provides minimal local persistence for API-specific data (projects, users, sessions).
Uses SQLite for simplicity - NOT replicated from PyPI libraries.
All components should use get_database() to access the database.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LocalDatabase:
    """Minimal SQLite wrapper for API project and user data (local only)"""

    def __init__(self, db_path: str = None):
        """Initialize database connection"""
        if db_path is None:
            data_dir = Path.home() / ".socrates"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "api_projects.db")

        self.db_path = Path(db_path)
        self.conn = None
        self._initialize()

    def _initialize(self):
        """Create tables if they don't exist"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row

            # Projects table - stores project metadata
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT,
                    updated_at TEXT,
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

            # Create indexes separately (SQLite doesn't support inline indexes)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_user_tokens ON refresh_tokens(user_id)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON refresh_tokens(expires_at)")

            self.conn.commit()

            # Perform schema migration for existing databases
            self._migrate_schema()

            logger.info(f"Local database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _migrate_schema(self):
        """Add missing columns to existing tables from previous schema versions"""
        try:
            # Get existing columns in users table
            cursor = self.conn.execute("PRAGMA table_info(users)")
            existing_columns = {row[1] for row in cursor.fetchall()}

            # Define required columns with their SQL definitions
            required_columns = {
                'passcode_hash': 'ALTER TABLE users ADD COLUMN passcode_hash TEXT',
                'subscription_tier': "ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free'",
                'subscription_status': "ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'active'",
                'testing_mode': 'ALTER TABLE users ADD COLUMN testing_mode INTEGER DEFAULT 0',
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
                        if 'duplicate column' not in str(e).lower():
                            raise

            logger.info("Schema migration completed successfully")
        except Exception as e:
            logger.error(f"Failed to migrate schema: {e}")
            # Don't raise - migration failure shouldn't crash initialization
            # The app can still work if migration partially succeeded

    def create_project(self, project_id: str, name: str, description: str = "", metadata: Dict = None) -> Dict:
        """Create a new project"""
        try:
            now = datetime.utcnow().isoformat()
            meta_json = json.dumps(metadata or {})

            self.conn.execute(
                "INSERT INTO projects (id, name, description, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (project_id, name, description, now, now, meta_json)
            )
            self.conn.commit()

            return {"id": project_id, "name": name, "description": description, "created_at": now, "status": "created"}
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        try:
            cursor = self.conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "metadata": json.loads(row[5] or "{}"),
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get project: {e}")
            return None

    def list_projects(self, limit: int = 100) -> List[Dict]:
        """List all projects"""
        try:
            cursor = self.conn.execute("SELECT * FROM projects LIMIT ?", (limit,))
            projects = []
            for row in cursor.fetchall():
                projects.append({"id": row[0], "name": row[1], "description": row[2], "created_at": row[3]})
            return projects
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    def create_user(self, user_id: str, username: str, email: str = "", passcode_hash: str = "", metadata: Dict = None) -> Dict:
        """Create a new user"""
        try:
            now = datetime.utcnow().isoformat()
            meta_json = json.dumps(metadata or {})

            self.conn.execute(
                "INSERT INTO users (id, username, email, passcode_hash, subscription_tier, subscription_status, testing_mode, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, username, email, passcode_hash or "", "free", "active", 0, now, now, meta_json),
            )
            self.conn.commit()

            return {"id": user_id, "username": username, "email": email, "created_at": now}
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        try:
            cursor = self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "passcode_hash": row[3],
                    "subscription_tier": row[4],
                    "subscription_status": row[5],
                    "testing_mode": bool(row[6]),
                    "created_at": row[7],
                    "updated_at": row[8],
                    "metadata": json.loads(row[9] or "{}"),
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None

    def load_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        try:
            cursor = self.conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "passcode_hash": row[3],
                    "subscription_tier": row[4],
                    "subscription_status": row[5],
                    "testing_mode": bool(row[6]),
                    "created_at": row[7],
                    "updated_at": row[8],
                    "metadata": json.loads(row[9] or "{}"),
                }
            return None
        except Exception as e:
            logger.error(f"Failed to load user by username: {e}")
            return None

    def load_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            cursor = self.conn.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "passcode_hash": row[3],
                    "subscription_tier": row[4],
                    "subscription_status": row[5],
                    "testing_mode": bool(row[6]),
                    "created_at": row[7],
                    "updated_at": row[8],
                    "metadata": json.loads(row[9] or "{}"),
                }
            return None
        except Exception as e:
            logger.error(f"Failed to load user by email: {e}")
            return None

    def save_user(self, user_data: Dict) -> Optional[Dict]:
        """Insert or update a user record"""
        try:
            now = datetime.utcnow().isoformat()
            user_id = user_data.get("id")
            username = user_data.get("username")
            email = user_data.get("email", "")
            passcode_hash = user_data.get("passcode_hash", "")
            subscription_tier = user_data.get("subscription_tier", "free")
            subscription_status = user_data.get("subscription_status", "active")
            testing_mode = int(user_data.get("testing_mode", False))
            meta_json = json.dumps(user_data.get("metadata", {}))

            # Check if user exists
            existing = self.get_user(user_id) if user_id else None

            if existing:
                # Update existing user
                self.conn.execute(
                    "UPDATE users SET username = ?, email = ?, passcode_hash = ?, subscription_tier = ?, subscription_status = ?, testing_mode = ?, updated_at = ?, metadata = ? WHERE id = ?",
                    (username, email, passcode_hash, subscription_tier, subscription_status, testing_mode, now, meta_json, user_id)
                )
            else:
                # Create new user
                if not user_id:
                    import uuid
                    user_id = str(uuid.uuid4())
                created_at = user_data.get("created_at", now)
                self.conn.execute(
                    "INSERT INTO users (id, username, email, passcode_hash, subscription_tier, subscription_status, testing_mode, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, username, email, passcode_hash, subscription_tier, subscription_status, testing_mode, created_at, now, meta_json)
                )
            self.conn.commit()
            return self.get_user(user_id)
        except Exception as e:
            logger.error(f"Failed to save user: {e}")
            return None

    def load_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID (alias for get_project for compatibility)"""
        return self.get_project(project_id)

    def close(self):
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
