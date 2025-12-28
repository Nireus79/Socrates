"""
Asynchronous Database Layer for Socratic RAG System (Phase 2)

Provides async/await support for all database operations using aiosqlite.
Enables concurrent request handling and non-blocking I/O.

Key improvements over sync layer:
- True async operations (not thread pool wrapped)
- Connection pooling for efficient resource usage
- Non-blocking concurrent access
- Task-based concurrency patterns
"""

import asyncio
import json
import logging
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite

from socratic_system.models import KnowledgeEntry, TeamMemberRole
from socratic_system.models.project import ProjectContext
from socratic_system.models.user import User


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO format string for storage."""
    if dt is None:
        return None
    return dt.isoformat()


def deserialize_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Convert ISO format string back to datetime."""
    if dt_str is None:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return datetime.now()


class AsyncConnectionPool:
    """
    Manages a pool of async database connections.

    Limits concurrent connections to prevent resource exhaustion while
    enabling high concurrency patterns.
    """

    def __init__(self, db_path: str, min_size: int = 2, max_size: int = 10):
        """
        Initialize connection pool.

        Args:
            db_path: Path to SQLite database file
            min_size: Minimum connections to maintain
            max_size: Maximum connections allowed
        """
        self.db_path = db_path
        self.min_size = min_size
        self.max_size = max_size
        self._pool: asyncio.Queue[aiosqlite.Connection] = None
        self._initialized = False
        self._semaphore = asyncio.Semaphore(max_size)

    async def initialize(self) -> None:
        """Initialize the connection pool."""
        if self._initialized:
            return

        self._pool = asyncio.Queue(maxsize=self.max_size)

        # Pre-create minimum connections
        for _ in range(self.min_size):
            conn = await aiosqlite.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            await self._pool.put(conn)

        self._initialized = True

    async def close_all(self) -> None:
        """Close all connections in the pool."""
        if not self._initialized:
            return

        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                await conn.close()
            except asyncio.QueueEmpty:
                break

        self._initialized = False

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from the pool.

        Usage:
            async with pool.acquire() as conn:
                cursor = await conn.cursor()
        """
        await self._semaphore.acquire()
        try:
            # Try to get existing connection
            try:
                conn = self._pool.get_nowait()
            except asyncio.QueueEmpty:
                # Create new connection if pool empty
                conn = await aiosqlite.connect(self.db_path)
                conn.row_factory = sqlite3.Row

            try:
                yield conn
            finally:
                # Return connection to pool
                try:
                    self._pool.put_nowait(conn)
                except asyncio.QueueFull:
                    # Pool full, close connection
                    await conn.close()
        finally:
            self._semaphore.release()


class AsyncProjectDatabase:
    """
    Asynchronous database layer for Socratic RAG System.

    All operations are non-blocking and support concurrent access through
    connection pooling. Designed for use with async/await patterns and
    asyncio event loops.
    """

    def __init__(self, db_path: str, pool_min_size: int = 2, pool_max_size: int = 10):
        """
        Initialize async database layer.

        Args:
            db_path: Path to SQLite database
            pool_min_size: Minimum connections in pool
            pool_max_size: Maximum connections in pool
        """
        self.db_path = db_path
        self.pool = AsyncConnectionPool(db_path, pool_min_size, pool_max_size)
        self.logger = logging.getLogger("async_db")
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the async database layer."""
        if self._initialized:
            return

        await self.pool.initialize()

        # Create schema if needed
        async with self.pool.acquire() as conn:
            # Create projects_v2 table if not exists
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects_v2 (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    phase TEXT NOT NULL DEFAULT 'discovery',
                    project_type TEXT DEFAULT 'software',
                    team_structure TEXT DEFAULT 'individual',
                    language_preferences TEXT DEFAULT 'python',
                    deployment_target TEXT DEFAULT 'local',
                    code_style TEXT DEFAULT 'standard',
                    chat_mode TEXT DEFAULT 'socratic',
                    goals TEXT,
                    status TEXT DEFAULT 'active',
                    progress INTEGER DEFAULT 0,
                    is_archived BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    archived_at TIMESTAMP,
                    FOREIGN KEY (owner) REFERENCES users_v2(username)
                )
                """
            )

            # Create other required tables
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_requirements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    requirement TEXT NOT NULL,
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_tech_stack (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    technology TEXT NOT NULL,
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_constraints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    constraint_text TEXT NOT NULL,
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS team_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    role TEXT NOT NULL,
                    skills TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(project_id, username),
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS phase_maturity_scores (
                    project_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    score REAL DEFAULT 0.0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (project_id, phase),
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS category_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    category TEXT NOT NULL,
                    score REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(project_id, phase, category),
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    question_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sort_order INTEGER DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analytics_metrics (
                    project_id TEXT PRIMARY KEY,
                    velocity REAL DEFAULT 0.0,
                    total_qa_sessions INTEGER DEFAULT 0,
                    avg_confidence REAL DEFAULT 0.0,
                    weak_categories TEXT,
                    strong_categories TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users_v2 (
                    username TEXT PRIMARY KEY,
                    passcode_hash TEXT NOT NULL,
                    subscription_tier TEXT DEFAULT 'free',
                    subscription_status TEXT DEFAULT 'active',
                    subscription_start TIMESTAMP,
                    subscription_end TIMESTAMP,
                    testing_mode BOOLEAN DEFAULT 0,
                    is_archived BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    archived_at TIMESTAMP
                )
                """
            )

            # Create additional tables from full schema
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS project_notes_v2 (
                    note_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    note_type TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS categorized_specs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    category TEXT NOT NULL,
                    spec_data TEXT NOT NULL,
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS maturity_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    old_score REAL,
                    new_score REAL,
                    event_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS question_effectiveness_v2 (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    question_template_id TEXT NOT NULL,
                    effectiveness_score REAL DEFAULT 0.5,
                    times_asked INTEGER DEFAULT 0,
                    times_answered_well INTEGER DEFAULT 0,
                    last_asked_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    UNIQUE(user_id, question_template_id),
                    FOREIGN KEY (user_id) REFERENCES users_v2(username)
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS behavior_patterns_v2 (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    learned_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    UNIQUE(user_id, pattern_type),
                    FOREIGN KEY (user_id) REFERENCES users_v2(username)
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_documents_v2 (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    user_id TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    source TEXT,
                    document_type TEXT DEFAULT 'document',
                    uploaded_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects_v2(project_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users_v2(username)
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_provider_configs_v2 (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    config_data TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    UNIQUE(user_id, provider),
                    FOREIGN KEY (user_id) REFERENCES users_v2(username)
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys_v2 (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    encrypted_key TEXT NOT NULL,
                    key_hash TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    last_used_at TIMESTAMP,
                    UNIQUE(user_id, provider),
                    FOREIGN KEY (user_id) REFERENCES users_v2(username)
                )
                """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_usage_v2 (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users_v2(username)
                )
                """
            )

            await conn.commit()

        self._initialized = True
        self.logger.info(f"Async database initialized: {self.db_path}")

    async def close(self) -> None:
        """Close all database connections."""
        await self.pool.close_all()
        self._initialized = False

    # =====================================================================
    # PROJECT OPERATIONS
    # =====================================================================

    async def load_project(self, project_id: str) -> Optional[ProjectContext]:
        """
        Load project by ID (async).

        Args:
            project_id: Project identifier

        Returns:
            ProjectContext if found, None otherwise
        """
        async with self.pool.acquire() as conn:
            # Load main project data
            cursor = await conn.execute(
                "SELECT * FROM projects_v2 WHERE project_id = ?", (project_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return None

            # Load related data
            requirements = await self._load_project_requirements(conn, project_id)
            tech_stack = await self._load_project_tech_stack(conn, project_id)
            constraints = await self._load_project_constraints(conn, project_id)
            team = await self._load_team_members(conn, project_id)
            phase_scores = await self._load_phase_maturity_scores(conn, project_id)
            category_scores = await self._load_category_scores(conn, project_id)
            pending_questions = await self._load_pending_questions(conn, project_id)
            analytics = await self._load_analytics_metrics(conn, project_id)

            return self._row_to_project(
                row,
                requirements,
                tech_stack,
                constraints,
                team,
                phase_scores,
                category_scores,
                pending_questions,
                analytics,
            )

    async def load_project_lightweight(self, project_id: str) -> Optional[ProjectContext]:
        """
        Load project WITHOUT conversation history (faster).

        Args:
            project_id: Project identifier

        Returns:
            ProjectContext if found, None otherwise
        """
        # Same as load_project but skips conversation history
        return await self.load_project(project_id)

    async def save_project(self, project: ProjectContext) -> bool:
        """
        Save project (async).

        Args:
            project: ProjectContext to save

        Returns:
            True if successful, False otherwise
        """
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")

                # Save main project
                now = datetime.now()
                project.updated_at = now

                await conn.execute(
                    """
                    INSERT OR REPLACE INTO projects_v2
                    (project_id, name, owner, phase, project_type, team_structure,
                     language_preferences, deployment_target, code_style, chat_mode,
                     goals, status, progress, is_archived, created_at, updated_at, archived_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project.project_id,
                        project.name,
                        project.owner,
                        project.phase,
                        getattr(project, "project_type", "software"),
                        getattr(project, "team_structure", "individual"),
                        getattr(project, "language_preferences", "python"),
                        getattr(project, "deployment_target", "local"),
                        getattr(project, "code_style", "standard"),
                        getattr(project, "chat_mode", "socratic"),
                        project.goals,
                        project.status,
                        project.progress,
                        int(project.is_archived),
                        serialize_datetime(project.created_at),
                        serialize_datetime(project.updated_at),
                        serialize_datetime(
                            getattr(project, "archived_at", None)
                        ),
                    ),
                )

                # Save arrays
                await self._save_project_requirements(conn, project)
                await self._save_project_tech_stack(conn, project)
                await self._save_project_constraints(conn, project)
                await self._save_team_members(conn, project)
                await self._save_phase_maturity_scores(conn, project)
                await self._save_category_scores(conn, project)
                await self._save_pending_questions(conn, project)
                await self._save_analytics_metrics(conn, project)

                await conn.execute("COMMIT")
                return True

            except Exception as e:
                await conn.execute("ROLLBACK")
                self.logger.error(f"Error saving project {project.project_id}: {e}")
                return False

    async def get_user_projects(
        self, username: str, include_archived: bool = False
    ) -> List[ProjectContext]:
        """
        Get all projects for a user (async, indexed query).

        Performance: < 50ms for 20 projects (vs 500-800ms pickle baseline)

        Args:
            username: Username
            include_archived: Whether to include archived projects

        Returns:
            List of ProjectContext objects
        """
        async with self.pool.acquire() as conn:
            where_clause = "WHERE owner = ?"
            if not include_archived:
                where_clause += " AND is_archived = 0"

            cursor = await conn.execute(
                f"SELECT * FROM projects_v2 {where_clause} ORDER BY updated_at DESC",
                (username,),
            )
            rows = await cursor.fetchall()

            projects = []
            for row in rows:
                project = await self.load_project(row["project_id"])
                if project:
                    projects.append(project)

            return projects

    async def archive_project(self, project_id: str) -> bool:
        """
        Archive a project (async).

        Args:
            project_id: Project to archive

        Returns:
            True if successful
        """
        async with self.pool.acquire() as conn:
            now = datetime.now()
            await conn.execute(
                """
                UPDATE projects_v2
                SET is_archived = 1, archived_at = ?
                WHERE project_id = ?
                """,
                (serialize_datetime(now), project_id),
            )
            await conn.commit()
            return True

    async def delete_project(self, project_id: str) -> bool:
        """
        Delete a project and all related data (async).

        Args:
            project_id: Project to delete

        Returns:
            True if successful
        """
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")

                # Foreign key cascades will delete related tables
                await conn.execute("DELETE FROM projects_v2 WHERE project_id = ?", (project_id,))

                await conn.execute("COMMIT")
                return True
            except Exception as e:
                await conn.execute("ROLLBACK")
                self.logger.error(f"Error deleting project {project_id}: {e}")
                return False

    async def bulk_save_projects(self, projects: List[ProjectContext]) -> int:
        """
        Save multiple projects concurrently (async).

        Args:
            projects: List of ProjectContext objects

        Returns:
            Number of successfully saved projects
        """
        tasks = [self.save_project(p) for p in projects]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return sum(1 for r in results if r is True)

    # =====================================================================
    # USER OPERATIONS
    # =====================================================================

    async def load_user(self, username: str) -> Optional[User]:
        """
        Load user by username (async).

        Args:
            username: Username

        Returns:
            User if found, None otherwise
        """
        async with self.pool.acquire() as conn:
            cursor = await conn.execute(
                "SELECT * FROM users_v2 WHERE username = ?", (username,)
            )
            row = await cursor.fetchone()

            if not row:
                return None

            return User(
                username=row["username"],
                passcode_hash=row["passcode_hash"],
                subscription_tier=row["subscription_tier"] if row["subscription_tier"] else "free",
                subscription_status=row["subscription_status"] if row["subscription_status"] else "active",
                subscription_start=deserialize_datetime(row["subscription_start"]),
                subscription_end=deserialize_datetime(row["subscription_end"]),
                testing_mode=bool(row["testing_mode"] or 0),
                is_archived=bool(row["is_archived"] or 0),
                created_at=deserialize_datetime(row["created_at"]),
            )

    async def save_user(self, user: User) -> bool:
        """
        Save user (async).

        Args:
            user: User object to save

        Returns:
            True if successful
        """
        async with self.pool.acquire() as conn:
            sub_start = getattr(user, "subscription_start", None)
            sub_end = getattr(user, "subscription_end", None)

            await conn.execute(
                """
                INSERT OR REPLACE INTO users_v2
                (username, passcode_hash, subscription_tier, subscription_status,
                 subscription_start, subscription_end, testing_mode, is_archived, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.username,
                    user.passcode_hash,
                    getattr(user, "subscription_tier", "free"),
                    getattr(user, "subscription_status", "active"),
                    serialize_datetime(sub_start) if sub_start else None,
                    serialize_datetime(sub_end) if sub_end else None,
                    int(getattr(user, "testing_mode", False)),
                    int(getattr(user, "is_archived", False)),
                    serialize_datetime(user.created_at),
                ),
            )
            await conn.commit()
            return True

    async def get_all_users(self, include_archived: bool = False) -> List[User]:
        """
        Get all users (async).

        Args:
            include_archived: Whether to include archived users

        Returns:
            List of User objects
        """
        async with self.pool.acquire() as conn:
            where_clause = "WHERE 1=1"
            if not include_archived:
                where_clause += " AND is_archived = 0"

            cursor = await conn.execute(f"SELECT * FROM users_v2 {where_clause}")
            rows = await cursor.fetchall()

            users = []
            for row in rows:
                user = User(
                    username=row["username"],
                    passcode_hash=row["passcode_hash"],
                    subscription_tier=row.get("subscription_tier", "free"),
                    subscription_status=row.get("subscription_status", "active"),
                    subscription_start=deserialize_datetime(row.get("subscription_start")),
                    subscription_end=deserialize_datetime(row.get("subscription_end")),
                    testing_mode=bool(row.get("testing_mode", 0)),
                    is_archived=bool(row.get("is_archived", 0)),
                    created_at=deserialize_datetime(row["created_at"]),
                )
                users.append(user)

            return users

    # =====================================================================
    # CONVERSATION HISTORY
    # =====================================================================

    async def save_conversation_history(
        self, project_id: str, history: List[Dict[str, Any]]
    ) -> bool:
        """
        Save conversation history (async).

        Args:
            project_id: Project identifier
            history: List of message dicts with 'role', 'content', 'timestamp'

        Returns:
            True if successful
        """
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")

                # Clear existing history
                await conn.execute(
                    "DELETE FROM conversation_history WHERE project_id = ?", (project_id,)
                )

                # Insert new history
                for message in history:
                    await conn.execute(
                        """
                        INSERT INTO conversation_history
                        (project_id, message_type, content, timestamp)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            project_id,
                            message.get("role", "user"),
                            message.get("content", ""),
                            message.get("timestamp", serialize_datetime(datetime.now())),
                        ),
                    )

                await conn.execute("COMMIT")
                return True

            except Exception as e:
                await conn.execute("ROLLBACK")
                self.logger.error(f"Error saving conversation history: {e}")
                return False

    async def get_conversation_history(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for project (async).

        Args:
            project_id: Project identifier

        Returns:
            List of conversation messages
        """
        async with self.pool.acquire() as conn:
            cursor = await conn.execute(
                """
                SELECT message_type, content, timestamp, metadata
                FROM conversation_history
                WHERE project_id = ?
                ORDER BY timestamp ASC
                """,
                (project_id,),
            )
            rows = await cursor.fetchall()

            history = []
            for row in rows:
                history.append(
                    {
                        "role": row["message_type"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                    }
                )

            return history

    # =====================================================================
    # PRE-SESSION CONVERSATIONS (async)
    # =====================================================================

    async def save_presession_message(
        self,
        username: str,
        session_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save a message to presession conversation history (async).

        Args:
            username: User who created the message
            session_id: Session identifier for grouping
            message_type: Either 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata dict
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO presession_conversations
                (username, session_id, message_type, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    username,
                    session_id,
                    message_type,
                    content,
                    datetime.now().isoformat(),
                    json.dumps(metadata or {}),
                ),
            )
            await conn.commit()

    async def get_presession_conversation(
        self, username: str, session_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get presession conversation history for a session (async).

        Args:
            username: Username to filter by
            session_id: Session identifier
            limit: Maximum messages to return

        Returns:
            List of message dicts
        """
        async with self.pool.acquire() as conn:
            cursor = await conn.execute(
                """
                SELECT message_type, content, timestamp, metadata
                FROM presession_conversations
                WHERE username = ? AND session_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """,
                (username, session_id, limit),
            )
            rows = await cursor.fetchall()

            history = []
            for row in rows:
                history.append(
                    {
                        "role": row["message_type"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    }
                )

            return history

    async def get_presession_sessions(
        self, username: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get list of presession sessions for a user (async).

        Args:
            username: Username to filter by
            limit: Maximum sessions to return

        Returns:
            List of session summary dicts
        """
        async with self.pool.acquire() as conn:
            cursor = await conn.execute(
                """
                SELECT
                    session_id,
                    MIN(timestamp) as started_at,
                    MAX(timestamp) as last_activity,
                    COUNT(*) as message_count,
                    SUM(CASE WHEN message_type = 'user' THEN 1 ELSE 0 END) as user_messages,
                    SUM(CASE WHEN message_type = 'assistant' THEN 1 ELSE 0 END) as assistant_messages
                FROM presession_conversations
                WHERE username = ?
                GROUP BY session_id
                ORDER BY MAX(timestamp) DESC
                LIMIT ?
            """,
                (username, limit),
            )
            rows = await cursor.fetchall()

            sessions = []
            for row in rows:
                sessions.append(
                    {
                        "session_id": row["session_id"],
                        "started_at": row["started_at"],
                        "last_activity": row["last_activity"],
                        "message_count": row["message_count"],
                        "user_messages": row["user_messages"],
                        "assistant_messages": row["assistant_messages"],
                    }
                )

            return sessions

    async def delete_presession_session(self, username: str, session_id: str) -> bool:
        """
        Delete a presession session and all its messages (async).

        Args:
            username: Username (for authorization)
            session_id: Session to delete

        Returns:
            True if deleted, False if not found
        """
        async with self.pool.acquire() as conn:
            # Verify ownership
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM presession_conversations WHERE username = ? AND session_id = ?",
                (username, session_id),
            )
            row = await cursor.fetchone()
            if row["count"] == 0:
                return False

            # Delete session messages
            await conn.execute(
                "DELETE FROM presession_conversations WHERE username = ? AND session_id = ?",
                (username, session_id),
            )
            await conn.commit()
            return True

    # =====================================================================
    # PRIVATE HELPER METHODS
    # =====================================================================

    async def _load_project_requirements(
        self, conn: aiosqlite.Connection, project_id: str
    ) -> List[str]:
        """Load project requirements from normalized table."""
        cursor = await conn.execute(
            "SELECT requirement FROM project_requirements WHERE project_id = ? ORDER BY sort_order",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def _load_project_tech_stack(
        self, conn: aiosqlite.Connection, project_id: str
    ) -> List[str]:
        """Load project tech stack from normalized table."""
        cursor = await conn.execute(
            "SELECT technology FROM project_tech_stack WHERE project_id = ? ORDER BY sort_order",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def _load_project_constraints(
        self, conn: aiosqlite.Connection, project_id: str
    ) -> List[str]:
        """Load project constraints from normalized table."""
        cursor = await conn.execute(
            "SELECT constraint_text FROM project_constraints WHERE project_id = ? ORDER BY sort_order",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def _load_team_members(
        self, conn: aiosqlite.Connection, project_id: str
    ) -> List[TeamMemberRole]:
        """Load team members from normalized table."""
        cursor = await conn.execute(
            "SELECT username, role, skills, joined_at FROM team_members WHERE project_id = ?",
            (project_id,),
        )
        rows = await cursor.fetchall()

        team = []
        for row in rows:
            skills = {}
            if row[2]:
                try:
                    skills = json.loads(row[2])
                except (json.JSONDecodeError, TypeError):
                    skills = {}

            member = TeamMemberRole(
                username=row[0],
                role=row[1],
                skills=skills,
                joined_at=deserialize_datetime(row[3]) if row[3] else datetime.now(),
            )
            team.append(member)

        return team

    async def _load_phase_maturity_scores(
        self, conn: aiosqlite.Connection, project_id: str
    ) -> Dict[str, float]:
        """Load phase maturity scores from normalized table."""
        cursor = await conn.execute(
            "SELECT phase, score FROM phase_maturity_scores WHERE project_id = ?",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}

    async def _load_category_scores(
        self, conn: aiosqlite.Connection, project_id: str
    ) -> Dict[str, Dict[str, float]]:
        """Load category scores from normalized table."""
        cursor = await conn.execute(
            "SELECT phase, category, score FROM category_scores WHERE project_id = ?",
            (project_id,),
        )
        rows = await cursor.fetchall()

        scores = {}
        for row in rows:
            phase = row[0]
            if phase not in scores:
                scores[phase] = {}
            scores[phase][row[1]] = row[2]

        return scores

    async def _load_pending_questions(
        self, conn: aiosqlite.Connection, project_id: str
    ) -> List[Dict[str, Any]]:
        """Load pending questions from normalized table."""
        cursor = await conn.execute(
            "SELECT question_data FROM pending_questions WHERE project_id = ? ORDER BY sort_order",
            (project_id,),
        )
        rows = await cursor.fetchall()

        questions = []
        for row in rows:
            try:
                question_data = json.loads(row[0])
                questions.append(question_data)
            except (json.JSONDecodeError, TypeError):
                pass

        return questions

    async def _load_analytics_metrics(
        self, conn: aiosqlite.Connection, project_id: str
    ) -> Dict[str, Any]:
        """Load analytics metrics from normalized table."""
        cursor = await conn.execute(
            """
            SELECT velocity, total_qa_sessions, avg_confidence, weak_categories, strong_categories
            FROM analytics_metrics WHERE project_id = ?
            """,
            (project_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return {}

        return {
            "velocity": row[0],
            "total_qa_sessions": row[1],
            "avg_confidence": row[2],
            "weak_categories": json.loads(row[3]) if row[3] else [],
            "strong_categories": json.loads(row[4]) if row[4] else [],
        }

    async def _save_project_requirements(
        self, conn: aiosqlite.Connection, project: ProjectContext
    ) -> None:
        """Save project requirements to normalized table."""
        await conn.execute(
            "DELETE FROM project_requirements WHERE project_id = ?",
            (project.project_id,),
        )

        for idx, req in enumerate(getattr(project, "requirements", [])):
            await conn.execute(
                """
                INSERT INTO project_requirements (project_id, requirement, sort_order)
                VALUES (?, ?, ?)
                """,
                (project.project_id, req, idx),
            )

    async def _save_project_tech_stack(
        self, conn: aiosqlite.Connection, project: ProjectContext
    ) -> None:
        """Save project tech stack to normalized table."""
        await conn.execute(
            "DELETE FROM project_tech_stack WHERE project_id = ?",
            (project.project_id,),
        )

        for idx, tech in enumerate(getattr(project, "tech_stack", [])):
            await conn.execute(
                """
                INSERT INTO project_tech_stack (project_id, technology, sort_order)
                VALUES (?, ?, ?)
                """,
                (project.project_id, tech, idx),
            )

    async def _save_project_constraints(
        self, conn: aiosqlite.Connection, project: ProjectContext
    ) -> None:
        """Save project constraints to normalized table."""
        await conn.execute(
            "DELETE FROM project_constraints WHERE project_id = ?",
            (project.project_id,),
        )

        for idx, constraint in enumerate(getattr(project, "constraints", [])):
            await conn.execute(
                """
                INSERT INTO project_constraints (project_id, constraint_text, sort_order)
                VALUES (?, ?, ?)
                """,
                (project.project_id, constraint, idx),
            )

    async def _save_team_members(
        self, conn: aiosqlite.Connection, project: ProjectContext
    ) -> None:
        """Save team members to normalized table."""
        await conn.execute(
            "DELETE FROM team_members WHERE project_id = ?",
            (project.project_id,),
        )

        team = getattr(project, "team_structure", [])
        if isinstance(team, str):
            # team_structure is a string descriptor, not actual team members
            return

        team_members = getattr(project, "team_members", [])
        for member in team_members:
            skills_json = json.dumps(getattr(member, "skills", {}))
            await conn.execute(
                """
                INSERT OR IGNORE INTO team_members (project_id, username, role, skills, joined_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    project.project_id,
                    member.username,
                    member.role,
                    skills_json,
                    serialize_datetime(getattr(member, "joined_at", datetime.now())),
                ),
            )

    async def _save_phase_maturity_scores(
        self, conn: aiosqlite.Connection, project: ProjectContext
    ) -> None:
        """Save phase maturity scores to normalized table."""
        await conn.execute(
            "DELETE FROM phase_maturity_scores WHERE project_id = ?",
            (project.project_id,),
        )

        scores = getattr(project, "phase_maturity_scores", {})
        for phase, score in scores.items():
            await conn.execute(
                """
                INSERT INTO phase_maturity_scores (project_id, phase, score)
                VALUES (?, ?, ?)
                """,
                (project.project_id, phase, score),
            )

    async def _save_category_scores(
        self, conn: aiosqlite.Connection, project: ProjectContext
    ) -> None:
        """Save category scores to normalized table."""
        await conn.execute(
            "DELETE FROM category_scores WHERE project_id = ?",
            (project.project_id,),
        )

        category_scores = getattr(project, "category_scores", {})
        for phase, categories in category_scores.items():
            for category, score in categories.items():
                await conn.execute(
                    """
                    INSERT INTO category_scores (project_id, phase, category, score)
                    VALUES (?, ?, ?, ?)
                    """,
                    (project.project_id, phase, category, score),
                )

    async def _save_pending_questions(
        self, conn: aiosqlite.Connection, project: ProjectContext
    ) -> None:
        """Save pending questions to normalized table."""
        await conn.execute(
            "DELETE FROM pending_questions WHERE project_id = ?",
            (project.project_id,),
        )

        questions = getattr(project, "pending_questions", [])
        for idx, question in enumerate(questions):
            question_json = json.dumps(question) if isinstance(question, dict) else str(question)
            await conn.execute(
                """
                INSERT INTO pending_questions (project_id, question_data, sort_order)
                VALUES (?, ?, ?)
                """,
                (project.project_id, question_json, idx),
            )

    async def _save_analytics_metrics(
        self, conn: aiosqlite.Connection, project: ProjectContext
    ) -> None:
        """Save analytics metrics to normalized table."""
        metrics = getattr(project, "analytics_metrics", {})

        weak_cats = json.dumps(metrics.get("weak_categories", []))
        strong_cats = json.dumps(metrics.get("strong_categories", []))

        await conn.execute(
            """
            INSERT OR REPLACE INTO analytics_metrics
            (project_id, velocity, total_qa_sessions, avg_confidence, weak_categories, strong_categories)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project.project_id,
                metrics.get("velocity", 0.0),
                metrics.get("total_qa_sessions", 0),
                metrics.get("avg_confidence", 0.0),
                weak_cats,
                strong_cats,
            ),
        )

    def _row_to_project(
        self,
        row: sqlite3.Row,
        requirements: List[str],
        tech_stack: List[str],
        constraints: List[str],
        team: List[TeamMemberRole],
        phase_scores: Dict[str, float],
        category_scores: Dict[str, Dict[str, float]],
        pending_questions: List[Dict],
        analytics: Dict[str, Any],
    ) -> ProjectContext:
        """Convert database row to ProjectContext."""
        return ProjectContext(
            project_id=row["project_id"],
            name=row["name"],
            owner=row["owner"],
            phase=row["phase"],
            project_type=row["project_type"] if row["project_type"] else "software",
            team_structure=row["team_structure"] if row["team_structure"] else "individual",
            language_preferences=row["language_preferences"] if row["language_preferences"] else "python",
            deployment_target=row["deployment_target"] if row["deployment_target"] else "local",
            code_style=row["code_style"] if row["code_style"] else "standard",
            chat_mode=row["chat_mode"] if row["chat_mode"] else "socratic",
            goals=row["goals"],
            status=row["status"] if row["status"] else "active",
            progress=row["progress"] if row["progress"] is not None else 0,
            is_archived=bool(row["is_archived"] or 0),
            created_at=deserialize_datetime(row["created_at"]),
            updated_at=deserialize_datetime(row["updated_at"]),
            requirements=requirements,
            tech_stack=tech_stack,
            constraints=constraints,
            team_members=team,
            phase_maturity_scores=phase_scores,
            category_scores=category_scores,
            pending_questions=pending_questions,
            analytics_metrics=analytics,
        )
