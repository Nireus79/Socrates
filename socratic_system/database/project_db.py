"""
Project database for persistent storage in Socratic RAG System
"""

import datetime
import logging
import os
import pickle
import sqlite3
from dataclasses import asdict
from datetime import timedelta
from typing import Dict, List, Optional

from socratic_system.models import (
    APIKeyRecord,
    KnowledgeBaseDocument,
    LLMProviderConfig,
    LLMUsageRecord,
    ProjectContext,
    ProjectNote,
    QuestionEffectiveness,
    User,
    UserBehaviorPattern,
)
from socratic_system.utils.datetime_helpers import deserialize_datetime, serialize_datetime


class ProjectDatabase:
    """SQLite database for storing projects and users"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger("socrates.database.projects")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for project metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                data BLOB,
                created_at TEXT,
                updated_at TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                passcode_hash TEXT,
                data BLOB,
                created_at TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS project_notes (
                note_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                data BLOB,
                created_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        """
        )

        # Learning tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS question_effectiveness (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                question_template_id TEXT NOT NULL,
                data BLOB,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(user_id, question_template_id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS behavior_patterns (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                data BLOB,
                learned_at TEXT,
                updated_at TEXT,
                UNIQUE(user_id, pattern_type)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                data BLOB,
                uploaded_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        """
        )

        # LLM Provider tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_provider_configs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                data BLOB,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(user_id, provider)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                encrypted_key TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                last_used_at TEXT,
                UNIQUE(user_id, provider)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_usage (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                data BLOB,
                timestamp TEXT,
                cost REAL
            )
        """
        )

        conn.commit()
        conn.close()

    def save_project(self, project: ProjectContext):
        """Save project to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = pickle.dumps(asdict(project))
        created_at_str = serialize_datetime(project.created_at)
        updated_at_str = serialize_datetime(project.updated_at)

        cursor.execute(
            """
            INSERT OR REPLACE INTO projects (project_id, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (project.project_id, data, created_at_str, updated_at_str),
        )

        conn.commit()
        conn.close()

    def load_project(self, project_id: str) -> Optional[ProjectContext]:
        """Load project from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT data FROM projects WHERE project_id = ?", (project_id,))
        result = cursor.fetchone()

        conn.close()

        if result:
            data = pickle.loads(result[0])
            # Convert datetime strings back to datetime objects if needed
            if isinstance(data.get("created_at"), str):
                data["created_at"] = deserialize_datetime(data["created_at"])
            if isinstance(data.get("updated_at"), str):
                data["updated_at"] = deserialize_datetime(data["updated_at"])
            return ProjectContext(**data)
        return None

    def get_user_projects(self, username: str, include_archived: bool = False) -> List[Dict]:
        """Get all projects for a user (as owner or collaborator)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT project_id, data FROM projects")
        results = cursor.fetchall()
        conn.close()

        projects = []
        for project_id, data in results:
            try:
                project_data = pickle.loads(data)

                # Handle datetime deserialization if needed
                if isinstance(project_data.get("updated_at"), str):
                    project_data["updated_at"] = deserialize_datetime(project_data["updated_at"])

                # Skip archived projects unless requested
                if project_data.get("is_archived", False) and not include_archived:
                    continue

                # Check if user is owner or collaborator
                if project_data["owner"] == username or username in project_data.get(
                    "collaborators", []
                ):
                    status = "archived" if project_data.get("is_archived", False) else "active"

                    projects.append(
                        {
                            "project_id": project_id,
                            "name": project_data["name"],
                            "phase": project_data["phase"],
                            "status": status,
                            "updated_at": (
                                project_data["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
                                if isinstance(project_data["updated_at"], datetime.datetime)
                                else str(project_data["updated_at"])
                            ),
                        }
                    )
            except Exception as e:
                self.logger.warning(f"Could not load project {project_id}: {e}")

        return projects

    def save_user(self, user: User):
        """Save user to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = pickle.dumps(asdict(user))
        created_at_str = serialize_datetime(user.created_at)

        cursor.execute(
            """
            INSERT OR REPLACE INTO users (username, passcode_hash, data, created_at)
            VALUES (?, ?, ?, ?)
        """,
            (user.username, user.passcode_hash, data, created_at_str),
        )

        conn.commit()
        conn.close()

    def load_user(self, username: str) -> Optional[User]:
        """Load user from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT data FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        conn.close()

        if result:
            data = pickle.loads(result[0])
            # Convert datetime string back to datetime object if needed
            if isinstance(data.get("created_at"), str):
                data["created_at"] = deserialize_datetime(data["created_at"])
            return User(**data)
        return None

    def user_exists(self, username: str) -> bool:
        """Check if a user exists in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        conn.close()
        return result is not None

    def archive_user(self, username: str, archive_projects: bool = True) -> bool:
        """Archive a user (soft delete)"""
        try:
            user = self.load_user(username)
            if not user:
                return False

            # Archive user
            user.is_archived = True
            user.archived_at = datetime.datetime.now()
            self.save_user(user)

            if archive_projects:
                # Archive all projects owned by this user
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT project_id, data FROM projects")
                results = cursor.fetchall()

                for project_id, data in results:
                    try:
                        project_data = pickle.loads(data)
                        if project_data["owner"] == username and not project_data.get(
                            "is_archived", False
                        ):
                            # Archive this project
                            project_data["is_archived"] = True
                            project_data["archived_at"] = datetime.datetime.now()
                            updated_data = pickle.dumps(project_data)

                            cursor.execute(
                                """
                                UPDATE projects SET data = ?, updated_at = ?
                                WHERE project_id = ?
                            """,
                                (updated_data, datetime.datetime.now().isoformat(), project_id),
                            )

                    except Exception as e:
                        self.logger.warning(f"Could not archive project {project_id}: {e}")

                conn.commit()
                conn.close()

            return True

        except Exception as e:
            self.logger.error(f"Error archiving user: {e}")
            return False

    def restore_user(self, username: str) -> bool:
        """Restore an archived user"""
        try:
            user = self.load_user(username)
            if not user or not user.is_archived:
                return False

            user.is_archived = False
            user.archived_at = None
            self.save_user(user)
            return True

        except Exception as e:
            self.logger.error(f"Error restoring user: {e}")
            return False

    def permanently_delete_user(self, username: str) -> bool:
        """Permanently delete a user and transfer their projects"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # First, handle projects owned by this user
            cursor.execute("SELECT project_id, data FROM projects")
            results = cursor.fetchall()

            projects_to_delete = []
            projects_to_transfer = []

            for project_id, data in results:
                try:
                    project_data = pickle.loads(data)
                    if project_data["owner"] == username:
                        if project_data.get("collaborators"):
                            # Transfer to first collaborator
                            new_owner = project_data["collaborators"][0]
                            project_data["owner"] = new_owner
                            project_data["collaborators"].remove(new_owner)
                            project_data["updated_at"] = datetime.datetime.now()

                            updated_data = pickle.dumps(project_data)
                            cursor.execute(
                                """
                                UPDATE projects SET data = ?, updated_at = ?
                                WHERE project_id = ?
                            """,
                                (updated_data, project_data["updated_at"].isoformat(), project_id),
                            )

                            projects_to_transfer.append((project_id, new_owner))
                        else:
                            # No collaborators, mark for deletion
                            projects_to_delete.append(project_id)

                except Exception as e:
                    self.logger.warning(f"Could not process project {project_id}: {e}")

            # Delete projects with no collaborators
            for project_id in projects_to_delete:
                cursor.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))

            # Delete the user
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            user_deleted = cursor.rowcount > 0

            conn.commit()
            conn.close()

            if user_deleted:
                self.logger.info(
                    f"User {username} deleted. {len(projects_to_transfer)} projects transferred, {len(projects_to_delete)} projects deleted."
                )
            return user_deleted

        except Exception as e:
            self.logger.error(f"Error permanently deleting user: {e}")
            return False

    def archive_project(self, project_id: str) -> bool:
        """Archive a project (soft delete)"""
        try:
            project = self.load_project(project_id)
            if not project:
                return False

            project.is_archived = True
            project.archived_at = datetime.datetime.now()
            project.updated_at = datetime.datetime.now()
            self.save_project(project)
            return True

        except Exception as e:
            self.logger.error(f"Error archiving project: {e}")
            return False

    def restore_project(self, project_id: str) -> bool:
        """Restore an archived project"""
        try:
            project = self.load_project(project_id)
            if not project or not project.is_archived:
                return False

            project.is_archived = False
            project.archived_at = None
            project.updated_at = datetime.datetime.now()
            self.save_project(project)
            return True

        except Exception as e:
            self.logger.error(f"Error restoring project: {e}")
            return False

    def permanently_delete_project(self, project_id: str) -> bool:
        """Permanently delete a project"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            return deleted

        except Exception as e:
            self.logger.error(f"Error permanently deleting project: {e}")
            return False

    def get_archived_items(self, item_type: str) -> List[Dict]:
        """Get all archived users or projects"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if item_type == "users":
            cursor.execute("SELECT username, data FROM users")
            results = cursor.fetchall()

            archived_users = []
            for username, data in results:
                try:
                    user_data = pickle.loads(data)
                    if user_data.get("is_archived", False):
                        archived_users.append(
                            {
                                "username": username,
                                "archived_at": user_data.get("archived_at"),
                                "project_count": len(user_data.get("projects", [])),
                            }
                        )
                except Exception as e:
                    self.logger.warning(f"Could not load user {username}: {e}")

            conn.close()
            return archived_users

        elif item_type == "projects":
            cursor.execute("SELECT project_id, data FROM projects")
            results = cursor.fetchall()

            archived_projects = []
            for project_id, data in results:
                try:
                    project_data = pickle.loads(data)
                    if project_data.get("is_archived", False):
                        archived_projects.append(
                            {
                                "project_id": project_id,
                                "name": project_data["name"],
                                "owner": project_data["owner"],
                                "archived_at": project_data.get("archived_at"),
                            }
                        )
                except Exception as e:
                    self.logger.warning(f"Could not load project {project_id}: {e}")

            conn.close()
            return archived_projects

        conn.close()
        return []

    def save_note(self, note: ProjectNote) -> bool:
        """Save a project note to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            data = pickle.dumps(asdict(note))
            created_at_str = serialize_datetime(note.created_at)

            cursor.execute(
                """
                INSERT OR REPLACE INTO project_notes (note_id, project_id, data, created_at)
                VALUES (?, ?, ?, ?)
            """,
                (note.note_id, note.project_id, data, created_at_str),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Error saving note: {e}")
            return False

    def get_project_notes(
        self, project_id: str, note_type: Optional[str] = None
    ) -> List[ProjectNote]:
        """Get all notes for a project, optionally filtered by type"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT data FROM project_notes WHERE project_id = ?", (project_id,))
            results = cursor.fetchall()

            conn.close()

            notes = []
            for (data,) in results:
                try:
                    note_data = pickle.loads(data)
                    # Convert datetime strings back to datetime objects if needed
                    if isinstance(note_data.get("created_at"), str):
                        note_data["created_at"] = deserialize_datetime(note_data["created_at"])

                    note = ProjectNote(**note_data)

                    # Filter by type if specified
                    if note_type is None or note.note_type == note_type:
                        notes.append(note)

                except Exception as e:
                    self.logger.warning(f"Could not load note: {e}")

            return notes

        except Exception as e:
            self.logger.error(f"Error getting notes: {e}")
            return []

    def search_notes(self, project_id: str, query: str) -> List[ProjectNote]:
        """Search notes for a project by content"""
        notes = self.get_project_notes(project_id)
        return [note for note in notes if note.matches_query(query)]

    def delete_note(self, note_id: str) -> bool:
        """Delete a note by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM project_notes WHERE note_id = ?", (note_id,))
            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Error deleting note: {e}")
            return False

    # ============================================================================
    # Learning-related methods
    # ============================================================================

    def save_question_effectiveness(self, effectiveness: QuestionEffectiveness) -> bool:
        """Save question effectiveness record"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            data = pickle.dumps(asdict(effectiveness))
            created_at_str = serialize_datetime(effectiveness.created_at)
            updated_at_str = serialize_datetime(effectiveness.updated_at)

            cursor.execute(
                """
                INSERT OR REPLACE INTO question_effectiveness
                (id, user_id, question_template_id, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    effectiveness.id,
                    effectiveness.user_id,
                    effectiveness.question_template_id,
                    data,
                    created_at_str,
                    updated_at_str,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Error saving question effectiveness: {e}")
            return False

    def get_question_effectiveness(
        self, user_id: str, question_template_id: str
    ) -> Optional[QuestionEffectiveness]:
        """Get question effectiveness record for a user-question pair"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT data FROM question_effectiveness WHERE user_id = ? AND question_template_id = ?",
                (user_id, question_template_id),
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                data = pickle.loads(result[0])
                # Deserialize datetimes if needed
                if isinstance(data.get("created_at"), str):
                    data["created_at"] = deserialize_datetime(data["created_at"])
                if isinstance(data.get("updated_at"), str):
                    data["updated_at"] = deserialize_datetime(data["updated_at"])
                if data.get("last_asked_at") and isinstance(data["last_asked_at"], str):
                    data["last_asked_at"] = deserialize_datetime(data["last_asked_at"])

                return QuestionEffectiveness(**data)
            return None

        except Exception as e:
            self.logger.error(f"Error getting question effectiveness: {e}")
            return None

    def get_user_effectiveness_all(self, user_id: str) -> List[QuestionEffectiveness]:
        """Get all question effectiveness records for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT data FROM question_effectiveness WHERE user_id = ?",
                (user_id,),
            )
            results = cursor.fetchall()
            conn.close()

            effectiveness_records = []
            for (data,) in results:
                try:
                    eff_data = pickle.loads(data)
                    # Deserialize datetimes
                    if isinstance(eff_data.get("created_at"), str):
                        eff_data["created_at"] = deserialize_datetime(eff_data["created_at"])
                    if isinstance(eff_data.get("updated_at"), str):
                        eff_data["updated_at"] = deserialize_datetime(eff_data["updated_at"])
                    if eff_data.get("last_asked_at") and isinstance(eff_data["last_asked_at"], str):
                        eff_data["last_asked_at"] = deserialize_datetime(eff_data["last_asked_at"])

                    effectiveness_records.append(QuestionEffectiveness(**eff_data))
                except Exception as e:
                    self.logger.warning(f"Could not load effectiveness record: {e}")

            return effectiveness_records

        except Exception as e:
            self.logger.error(f"Error getting user effectiveness records: {e}")
            return []

    def save_behavior_pattern(self, pattern: UserBehaviorPattern) -> bool:
        """Save behavior pattern record"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            data = pickle.dumps(asdict(pattern))
            learned_at_str = serialize_datetime(pattern.learned_at)
            updated_at_str = serialize_datetime(pattern.updated_at)

            cursor.execute(
                """
                INSERT OR REPLACE INTO behavior_patterns
                (id, user_id, pattern_type, data, learned_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    pattern.id,
                    pattern.user_id,
                    pattern.pattern_type,
                    data,
                    learned_at_str,
                    updated_at_str,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Error saving behavior pattern: {e}")
            return False

    def get_behavior_pattern(
        self, user_id: str, pattern_type: str
    ) -> Optional[UserBehaviorPattern]:
        """Get behavior pattern for a user-pattern_type pair"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT data FROM behavior_patterns WHERE user_id = ? AND pattern_type = ?",
                (user_id, pattern_type),
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                data = pickle.loads(result[0])
                # Deserialize datetimes
                if isinstance(data.get("learned_at"), str):
                    data["learned_at"] = deserialize_datetime(data["learned_at"])
                if isinstance(data.get("updated_at"), str):
                    data["updated_at"] = deserialize_datetime(data["updated_at"])

                return UserBehaviorPattern(**data)
            return None

        except Exception as e:
            self.logger.error(f"Error getting behavior pattern: {e}")
            return None

    def get_user_behavior_patterns(self, user_id: str) -> List[UserBehaviorPattern]:
        """Get all behavior patterns for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT data FROM behavior_patterns WHERE user_id = ?",
                (user_id,),
            )
            results = cursor.fetchall()
            conn.close()

            patterns = []
            for (data,) in results:
                try:
                    pattern_data = pickle.loads(data)
                    # Deserialize datetimes
                    if isinstance(pattern_data.get("learned_at"), str):
                        pattern_data["learned_at"] = deserialize_datetime(
                            pattern_data["learned_at"]
                        )
                    if isinstance(pattern_data.get("updated_at"), str):
                        pattern_data["updated_at"] = deserialize_datetime(
                            pattern_data["updated_at"]
                        )

                    patterns.append(UserBehaviorPattern(**pattern_data))
                except Exception as e:
                    self.logger.warning(f"Could not load behavior pattern: {e}")

            return patterns

        except Exception as e:
            self.logger.error(f"Error getting user behavior patterns: {e}")
            return []

    def save_knowledge_document(self, document: KnowledgeBaseDocument) -> bool:
        """Save knowledge base document"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            data = pickle.dumps(asdict(document))
            uploaded_at_str = serialize_datetime(document.uploaded_at)

            cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge_documents
                (id, project_id, user_id, data, uploaded_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    document.id,
                    document.project_id,
                    document.user_id,
                    data,
                    uploaded_at_str,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Error saving knowledge document: {e}")
            return False

    def get_knowledge_document(self, document_id: str) -> Optional[KnowledgeBaseDocument]:
        """Get a knowledge document by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT data FROM knowledge_documents WHERE id = ?", (document_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                data = pickle.loads(result[0])
                # Deserialize datetime
                if isinstance(data.get("uploaded_at"), str):
                    data["uploaded_at"] = deserialize_datetime(data["uploaded_at"])

                return KnowledgeBaseDocument(**data)
            return None

        except Exception as e:
            self.logger.error(f"Error getting knowledge document: {e}")
            return None

    def get_project_knowledge_documents(self, project_id: str) -> List[KnowledgeBaseDocument]:
        """Get all knowledge documents for a project"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT data FROM knowledge_documents WHERE project_id = ?",
                (project_id,),
            )
            results = cursor.fetchall()
            conn.close()

            documents = []
            for (data,) in results:
                try:
                    doc_data = pickle.loads(data)
                    # Deserialize datetime
                    if isinstance(doc_data.get("uploaded_at"), str):
                        doc_data["uploaded_at"] = deserialize_datetime(doc_data["uploaded_at"])

                    documents.append(KnowledgeBaseDocument(**doc_data))
                except Exception as e:
                    self.logger.warning(f"Could not load knowledge document: {e}")

            return documents

        except Exception as e:
            self.logger.error(f"Error getting project knowledge documents: {e}")
            return []

    # ============================================================================
    # LLM Provider Management
    # ============================================================================

    def save_llm_config(self, config: LLMProviderConfig) -> bool:
        """Save LLM provider configuration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            data = pickle.dumps(asdict(config))
            created_at_str = serialize_datetime(config.created_at)
            updated_at_str = serialize_datetime(config.updated_at)

            cursor.execute(
                """
                INSERT OR REPLACE INTO llm_provider_configs
                (id, user_id, provider, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    config.id,
                    config.user_id,
                    config.provider,
                    data,
                    created_at_str,
                    updated_at_str,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Error saving LLM config: {e}")
            return False

    def get_user_llm_config(self, user_id: str, provider: str) -> Optional[LLMProviderConfig]:
        """Get LLM config for user and provider"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT data FROM llm_provider_configs WHERE user_id = ? AND provider = ?",
                (user_id, provider),
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                data = pickle.loads(result[0])
                if isinstance(data.get("created_at"), str):
                    data["created_at"] = deserialize_datetime(data["created_at"])
                if isinstance(data.get("updated_at"), str):
                    data["updated_at"] = deserialize_datetime(data["updated_at"])

                return LLMProviderConfig(**data)
            return None

        except Exception as e:
            self.logger.error(f"Error getting LLM config: {e}")
            return None

    def get_user_llm_configs(self, user_id: str) -> List[LLMProviderConfig]:
        """Get all LLM configs for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT data FROM llm_provider_configs WHERE user_id = ?",
                (user_id,),
            )
            results = cursor.fetchall()
            conn.close()

            configs = []
            for (data,) in results:
                try:
                    config_data = pickle.loads(data)
                    if isinstance(config_data.get("created_at"), str):
                        config_data["created_at"] = deserialize_datetime(config_data["created_at"])
                    if isinstance(config_data.get("updated_at"), str):
                        config_data["updated_at"] = deserialize_datetime(config_data["updated_at"])

                    configs.append(LLMProviderConfig(**config_data))
                except Exception as e:
                    self.logger.warning(f"Could not load LLM config: {e}")

            return configs

        except Exception as e:
            self.logger.error(f"Error getting user LLM configs: {e}")
            return []

    def unset_other_default_providers(self, user_id: str, current_provider: str) -> None:
        """Unset default flag for other providers"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT data FROM llm_provider_configs WHERE user_id = ? AND provider != ?",
                (user_id, current_provider),
            )
            results = cursor.fetchall()

            for (data,) in results:
                try:
                    config_data = pickle.loads(data)
                    if config_data.get("is_default"):
                        config_data["is_default"] = False
                        updated_data = pickle.dumps(config_data)

                        cursor.execute(
                            "UPDATE llm_provider_configs SET data = ? WHERE user_id = ? AND provider = ?",
                            (updated_data, user_id, config_data["provider"]),
                        )

                except Exception as e:
                    self.logger.warning(f"Could not update provider default flag: {e}")

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error unsetting other defaults: {e}")

    def save_api_key(self, record: APIKeyRecord) -> bool:
        """Save encrypted API key"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            created_at_str = serialize_datetime(record.created_at)
            updated_at_str = serialize_datetime(record.updated_at)
            last_used_str = serialize_datetime(record.last_used_at) if record.last_used_at else None

            cursor.execute(
                """
                INSERT OR REPLACE INTO api_keys
                (id, user_id, provider, encrypted_key, key_hash, created_at, updated_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.id,
                    record.user_id,
                    record.provider,
                    record.encrypted_key,
                    record.key_hash,
                    created_at_str,
                    updated_at_str,
                    last_used_str,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Error saving API key: {e}")
            return False

    def get_api_key(self, user_id: str, provider: str) -> Optional[APIKeyRecord]:
        """Get API key for user and provider (without decryption)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, encrypted_key, created_at, updated_at, last_used_at FROM api_keys WHERE user_id = ? AND provider = ?",
                (user_id, provider),
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                record_id, encrypted_key, created_at_str, updated_at_str, last_used_str = result
                record = APIKeyRecord(
                    id=record_id,
                    user_id=user_id,
                    provider=provider,
                    encrypted_key=encrypted_key,
                    key_hash="",  # Not stored separately
                    created_at=deserialize_datetime(created_at_str) if created_at_str else None,
                    updated_at=deserialize_datetime(updated_at_str) if updated_at_str else None,
                    last_used_at=deserialize_datetime(last_used_str) if last_used_str else None,
                )
                return record
            return None

        except Exception as e:
            self.logger.error(f"Error getting API key: {e}")
            return None

    def delete_api_key(self, user_id: str, provider: str) -> bool:
        """Delete API key"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM api_keys WHERE user_id = ? AND provider = ?",
                (user_id, provider),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Error deleting API key: {e}")
            return False

    def save_usage_record(self, usage: LLMUsageRecord) -> bool:
        """Save LLM usage record"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            data = pickle.dumps(asdict(usage))
            timestamp_str = serialize_datetime(usage.timestamp)

            cursor.execute(
                """
                INSERT INTO llm_usage
                (id, user_id, provider, model, data, timestamp, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    usage.id,
                    usage.user_id,
                    usage.provider,
                    usage.model,
                    data,
                    timestamp_str,
                    usage.cost,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Error saving usage record: {e}")
            return False

    def get_usage_records(
        self, user_id: str, days: int = 30, provider: Optional[str] = None
    ) -> List[LLMUsageRecord]:
        """Get usage records for a user in last N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = datetime.datetime.now() - timedelta(days=days)
            cutoff_str = serialize_datetime(cutoff_date)

            if provider:
                cursor.execute(
                    "SELECT data FROM llm_usage WHERE user_id = ? AND provider = ? AND timestamp > ?",
                    (user_id, provider, cutoff_str),
                )
            else:
                cursor.execute(
                    "SELECT data FROM llm_usage WHERE user_id = ? AND timestamp > ?",
                    (user_id, cutoff_str),
                )

            results = cursor.fetchall()
            conn.close()

            records = []
            for (data,) in results:
                try:
                    usage_data = pickle.loads(data)
                    if isinstance(usage_data.get("timestamp"), str):
                        usage_data["timestamp"] = deserialize_datetime(usage_data["timestamp"])

                    records.append(LLMUsageRecord(**usage_data))
                except Exception as e:
                    self.logger.warning(f"Could not load usage record: {e}")

            return records

        except Exception as e:
            self.logger.error(f"Error getting usage records: {e}")
            return []
