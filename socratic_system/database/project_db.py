"""
Socrates Database Layer - Normalized Schema Implementation

This module provides the database interface for the Socrates AI system using a
normalized schema (no pickle BLOBs).

Key features:
- 10-20x faster database operations (indexed queries vs full table scans)
- All data queryable (no unpickling required)
- Separation of concerns (arrays in separate tables)
- Lazy loading support (conversation history separate)
- Type safety (no pickle deserialization issues)
- Full support for chat sessions, invitations, activities, and analytics
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from socratic_system.database.migration_runner import MigrationRunner
from socratic_system.models.learning import QuestionEffectiveness, UserBehaviorPattern
from socratic_system.models.llm_provider import LLMUsageRecord
from socratic_system.models.note import ProjectNote
from socratic_system.models.project import ProjectContext
from socratic_system.models.user import User
from socratic_system.utils.datetime_helpers import deserialize_datetime, serialize_datetime

logger = logging.getLogger("socrates.database")


class ProjectDatabase:
    """
    SQLite database implementation using normalized schema.
    Uses queryable columns and separate tables for optimal performance.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file. If not provided, uses SOCRATES_DATA_DIR environment variable

        Raises:
            ValueError: If db_path is invalid or empty
        """
        # Support SOCRATES_DATA_DIR environment variable
        if db_path is None:
            data_dir = os.getenv("SOCRATES_DATA_DIR", str(Path.home() / ".socrates"))
            db_path = os.path.join(data_dir, "projects.db")

        if not db_path or not isinstance(db_path, str) or db_path.strip() == "":
            raise ValueError(f"Invalid db_path: {db_path!r}. Must be a non-empty string.")

        self.db_path = db_path
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Create directory if it doesn't exist
        data_dir = os.path.dirname(db_path)
        if data_dir:  # Only create if directory path is non-empty
            os.makedirs(data_dir, exist_ok=True)

        # Initialize V2 schema if not already exists
        self._init_database_v2()

    def _init_database_v2(self):
        """Initialize V2 database schema and apply migrations"""
        # Check if V2 schema exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Enable foreign keys globally for proper cascading deletes
            self._enable_foreign_keys(cursor)

            # Test if V2 tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
            if cursor.fetchone():
                self.logger.info("V2 schema already exists (foreign keys enabled)")
                # Still need to ensure migrations are applied
                conn.close()
                self._ensure_migrations()
                return

            # V2 schema doesn't exist, create it
            schema_path = Path(__file__).parent / "schema_v2.sql"
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")

            with open(schema_path) as f:
                schema_sql = f.read()

            cursor.executescript(schema_sql)
            conn.commit()
            self.logger.info("V2 schema initialized with foreign keys enabled")

        finally:
            conn.close()

        # Apply any pending migrations after schema initialization
        self._ensure_migrations()

    def _ensure_migrations(self) -> None:
        """Ensure all required migrations are applied"""
        try:
            migration_runner = MigrationRunner(self.db_path)
            success, message = migration_runner.ensure_migrations_applied()
            if success:
                self.logger.info(f"Migrations check passed: {message}")
            else:
                self.logger.error(f"Migration issue: {message}")
        except Exception as e:
            self.logger.error(f"Error ensuring migrations applied: {e}")

    def _enable_foreign_keys(self, cursor: sqlite3.Cursor) -> None:
        """
        Enable foreign key constraints globally for this database connection

        SQLite has foreign key support disabled by default for backward compatibility.
        This enables it to ensure cascade deletes work properly when projects are deleted.

        Must be called on every connection, as the setting is per-connection.
        """
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA foreign_keys")
            result = cursor.fetchone()
            if result and result[0]:
                self.logger.debug("Foreign keys enabled for this connection")
            else:
                self.logger.warning("Failed to enable foreign keys - cascade deletes may not work")
        except Exception as e:
            self.logger.error(f"Error enabling foreign keys: {e}")

    def _get_cascade_delete_counts(self, cursor: sqlite3.Cursor, project_id: str) -> dict[str, int]:
        """
        Get counts of records that will be cascade deleted when project is deleted

        Args:
            cursor: Database cursor
            project_id: Project ID to check

        Returns:
            Dictionary with counts for each related table
        """
        counts = {
            "conversation": 0,
            "requirements": 0,
            "tech_stack": 0,
            "constraints": 0,
            "team_members": 0,
            "notes": 0,
            "maturity": 0,
            "category": 0,
            "analytics": 0,
        }

        try:
            # Count records in each child table
            cursor.execute(
                "SELECT COUNT(*) FROM conversation_history WHERE project_id = ?",
                (project_id,),
            )
            counts["conversation"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM project_requirements WHERE project_id = ?", (project_id,)
            )
            counts["requirements"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM project_tech_stack WHERE project_id = ?", (project_id,)
            )
            counts["tech_stack"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM project_constraints WHERE project_id = ?", (project_id,)
            )
            counts["constraints"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM team_members WHERE project_id = ?", (project_id,))
            counts["team_members"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM project_notes WHERE project_id = ?", (project_id,))
            counts["notes"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM phase_maturity_scores WHERE project_id = ?", (project_id,)
            )
            counts["maturity"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM category_scores WHERE project_id = ?", (project_id,)
            )
            counts["category"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM analytics_metrics WHERE project_id = ?", (project_id,)
            )
            counts["analytics"] = cursor.fetchone()[0]

        except Exception as e:
            self.logger.warning(f"Error counting cascade deletes for {project_id}: {e}")

        return counts

    # ========================================================================
    # PROJECT OPERATIONS (Core optimization: 10-20x faster)
    # ========================================================================

    def save_project(self, project: ProjectContext) -> None:
        """
        Save or update a project

        Args:
            project: ProjectContext object to save
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now()
            self._save_main_project_record(cursor, project, now)
            self._delete_project_related_records(cursor, project.project_id)
            self._save_project_lists(cursor, project)
            self._save_project_team_members(cursor, project, now)
            self._save_project_scores(cursor, project)
            self._save_project_analytics(cursor, project)
            self._save_categorized_specs(cursor, project)
            conn.commit()
            self.logger.debug(f"Saved project {project.project_id}")

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving project {project.project_id}: {e}")
            raise
        finally:
            conn.close()

        # Save pending questions separately
        if project.pending_questions:
            self._save_pending_questions(project.project_id, project.pending_questions)
            self.logger.debug(
                f"Saved {len(project.pending_questions)} pending questions for project {project.project_id}"
            )

        # Save conversation history separately (after main transaction completes)
        if project.conversation_history:
            self.save_conversation_history(project.project_id, project.conversation_history)
            self.logger.debug(
                f"Saved conversation history for project {project.project_id} "
                f"({len(project.conversation_history)} messages)"
            )

        # Save notes separately
        if project.notes:
            self._save_project_notes(project.project_id, project.notes)
            self.logger.debug(
                f"Saved {len(project.notes)} notes for project {project.project_id}"
            )

    def _save_main_project_record(self, cursor, project: ProjectContext, now: datetime) -> None:
        """Save main project record"""
        cursor.execute(
            """
            INSERT OR REPLACE INTO projects (
                project_id, name, owner, phase, project_type,
                team_structure, language_preferences, deployment_target,
                code_style, chat_mode, goals, status, progress,
                is_archived, created_at, updated_at, archived_at, code_history
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                project.project_id,
                project.name,
                project.owner,
                project.phase,
                project.project_type,
                (
                    (
                        json.dumps(project.team_structure)
                        if isinstance(project.team_structure, dict)
                        else project.team_structure
                    )
                    if project.team_structure
                    else None
                ),
                (
                    (
                        json.dumps(project.language_preferences)
                        if isinstance(project.language_preferences, dict)
                        else project.language_preferences
                    )
                    if project.language_preferences
                    else None
                ),
                project.deployment_target,
                (
                    (
                        json.dumps(project.code_style)
                        if isinstance(project.code_style, dict)
                        else project.code_style
                    )
                    if project.code_style
                    else None
                ),
                project.chat_mode,
                (
                    json.dumps(project.goals)
                    if isinstance(project.goals, (list, dict))
                    else project.goals
                ),
                project.status,
                project.progress,
                project.is_archived,
                serialize_datetime(project.created_at),
                serialize_datetime(now),
                serialize_datetime(project.archived_at) if project.archived_at else None,  # type: ignore
                json.dumps(project.code_history) if project.code_history else None,
            ),
        )

    def _delete_project_related_records(self, cursor, project_id: str) -> None:
        """Delete all related project records"""
        cursor.execute("DELETE FROM project_requirements WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM project_tech_stack WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM project_constraints WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM team_members WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM phase_maturity_scores WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM category_scores WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM categorized_specs WHERE project_id = ?", (project_id,))

    def _save_project_lists(self, cursor, project: ProjectContext) -> None:
        """Save project requirements, tech stack, and constraints"""
        for i, req in enumerate(project.requirements or []):
            cursor.execute(
                "INSERT INTO project_requirements (project_id, requirement, sort_order) VALUES (?, ?, ?)",
                (project.project_id, req, i),
            )

        for i, tech in enumerate(project.tech_stack or []):
            cursor.execute(
                "INSERT INTO project_tech_stack (project_id, technology, sort_order) VALUES (?, ?, ?)",
                (project.project_id, tech, i),
            )

        for i, constraint in enumerate(project.constraints or []):
            cursor.execute(
                "INSERT INTO project_constraints (project_id, constraint_text, sort_order) VALUES (?, ?, ?)",
                (project.project_id, constraint, i),
            )

    def _save_project_team_members(self, cursor, project: ProjectContext, now: datetime) -> None:
        """Save project team members"""
        if not project.team_members:
            return
        for member in project.team_members:
            skills_json = json.dumps(getattr(member, "skills", {}))
            cursor.execute(
                "INSERT OR IGNORE INTO team_members (project_id, username, role, skills, joined_at) VALUES (?, ?, ?, ?, ?)",
                (
                    project.project_id,
                    member.username,
                    member.role,
                    skills_json,
                    serialize_datetime(getattr(member, "joined_at", now)),
                ),
            )

    def _save_project_scores(self, cursor, project: ProjectContext) -> None:
        """Save phase maturity scores and category scores"""
        if project.phase_maturity_scores:
            for phase, score in project.phase_maturity_scores.items():
                score_val = score if isinstance(score, (int, float)) else 0.0
                cursor.execute(
                    "INSERT OR REPLACE INTO phase_maturity_scores (project_id, phase, score) VALUES (?, ?, ?)",
                    (project.project_id, phase, score_val),
                )

        if project.category_scores:
            for phase, categories in project.category_scores.items():
                if isinstance(categories, dict):
                    for category, score in categories.items():
                        score_val = score if isinstance(score, (int, float)) else 0.0
                        cursor.execute(
                            "INSERT OR REPLACE INTO category_scores (project_id, phase, category, score) VALUES (?, ?, ?, ?)",
                            (project.project_id, phase, category, score_val),
                        )

    def _save_project_analytics(self, cursor, project: ProjectContext) -> None:
        """Save project analytics metrics"""
        if not project.analytics_metrics:
            return
        cursor.execute(
            "INSERT OR REPLACE INTO analytics_metrics (project_id, velocity, total_qa_sessions, avg_confidence, weak_categories, strong_categories) VALUES (?, ?, ?, ?, ?, ?)",
            (
                project.project_id,
                (
                    float(project.analytics_metrics.get("velocity", 0.0))
                    if not isinstance(project.analytics_metrics.get("velocity"), dict)
                    else 0.0
                ),
                (
                    int(project.analytics_metrics.get("total_qa_sessions", 0))
                    if not isinstance(project.analytics_metrics.get("total_qa_sessions"), dict)
                    else 0
                ),
                (
                    float(project.analytics_metrics.get("avg_confidence", 0.0))
                    if not isinstance(project.analytics_metrics.get("avg_confidence"), dict)
                    else 0.0
                ),
                json.dumps(project.analytics_metrics.get("weak_categories", [])),
                json.dumps(project.analytics_metrics.get("strong_categories", [])),
            ),
        )

    def _save_categorized_specs(self, cursor: sqlite3.Cursor, project: ProjectContext) -> None:
        """Save categorized specifications for a project"""
        if not project.categorized_specs:
            return

        try:
            # Track overall sort order
            global_order = 0

            # Save specs phase by phase
            for phase, specs_list in project.categorized_specs.items():
                if not isinstance(specs_list, list):
                    self.logger.warning(f"Invalid specs format for phase {phase}")
                    continue

                for spec in specs_list:
                    if not isinstance(spec, dict):
                        continue

                    try:
                        spec_json = json.dumps(spec)
                        category = spec.get("category", "uncategorized")

                        cursor.execute(
                            """
                            INSERT INTO categorized_specs
                            (project_id, phase, category, spec_data, sort_order)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (project.project_id, phase, category, spec_json, global_order),
                        )
                        global_order += 1

                    except (json.JSONEncodeError, TypeError) as e:
                        self.logger.error(f"Failed to serialize spec: {e}")
                        continue

            self.logger.debug(f"Saved {global_order} specs for {project.project_id}")

        except Exception as e:
            self.logger.error(f"Error saving specs: {e}")
            raise

    def load_project(self, project_id: str) -> ProjectContext | None:
        """
        Load a project by ID

        Performance: < 10ms (vs 30ms+ with pickle)

        Args:
            project_id: ID of project to load

        Returns:
            ProjectContext or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Load main project record
            cursor.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
            row = cursor.fetchone()

            if not row:
                return None

            # Load related data
            requirements = self._load_project_requirements(cursor, project_id)
            tech_stack = self._load_project_tech_stack(cursor, project_id)
            constraints = self._load_project_constraints(cursor, project_id)
            team_members = self._load_team_members(cursor, project_id)
            phase_maturity = self._load_phase_maturity(cursor, project_id)
            category_scores = self._load_category_scores(cursor, project_id)
            categorized_specs = self._load_categorized_specs(cursor, project_id)
            analytics = self._load_analytics_metrics(cursor, project_id)
            conversation_history = self.get_conversation_history(project_id)
            pending_questions = self._load_pending_questions(project_id)
            notes = self._load_project_notes(project_id)

            # Deserialize JSON fields (only if they're actually JSON)
            def try_json_load(value):
                """Try to parse as JSON, return original value if not JSON"""
                if not value or not isinstance(value, str):
                    return value
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value

            goals = try_json_load(row["goals"])
            team_structure = try_json_load(row["team_structure"])
            language_preferences = try_json_load(row["language_preferences"])
            code_style = try_json_load(row["code_style"])

            # Load code_history if column exists (handles backward compatibility)
            code_history = None
            try:
                code_history = try_json_load(row["code_history"])
            except (IndexError, KeyError):
                # Column doesn't exist yet (migration not applied)
                code_history = None

            # Construct ProjectContext
            project = ProjectContext(
                project_id=row["project_id"],
                name=row["name"],
                owner=row["owner"],
                phase=row["phase"],
                created_at=deserialize_datetime(row["created_at"]),
                updated_at=deserialize_datetime(row["updated_at"]),
                goals=goals,
                requirements=requirements,
                tech_stack=tech_stack,
                constraints=constraints,
                team_structure=team_structure,
                language_preferences=language_preferences,
                deployment_target=row["deployment_target"],
                code_style=code_style,
                chat_mode=row["chat_mode"],
                status=row["status"],
                progress=row["progress"],
                is_archived=bool(row["is_archived"]),
                archived_at=(
                    deserialize_datetime(row["archived_at"]) if row["archived_at"] else None
                ),
                project_type=row["project_type"],
                team_members=team_members,
                phase_maturity_scores=phase_maturity,
                category_scores=category_scores,
                categorized_specs=categorized_specs,
                analytics_metrics=analytics,
                conversation_history=conversation_history,
                pending_questions=pending_questions,
                notes=notes,
                code_history=code_history,
            )

            self.logger.debug(f"Loaded project {project_id}")
            return project

        except Exception as e:
            self.logger.error(f"Error loading project {project_id}: {e}")
            return None
        finally:
            conn.close()

    def get_user_projects(
        self, username: str, include_archived: bool = False
    ) -> list[ProjectContext]:
        """
        Get all projects for a user (owned or collaborated)

        Performance: 50ms for 107 projects (vs 500-800ms with pickle unpickling)

        Args:
            username: Username to get projects for
            include_archived: Whether to include archived projects

        Returns:
            List of ProjectContext objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Query owned projects
            where_clause = "WHERE owner = ?"
            if not include_archived:
                where_clause += " AND is_archived = 0"

            cursor.execute(
                f"""
                SELECT * FROM projects {where_clause}
                ORDER BY updated_at DESC
            """,  # nosec B608
                (username,),
            )

            owned_rows = cursor.fetchall()

            # Query collaborated projects
            cursor.execute(
                """
                SELECT DISTINCT p.* FROM projects p
                INNER JOIN team_members t ON p.project_id = t.project_id
                WHERE t.username = ?
            """,
                (username,),
            )

            collab_rows = cursor.fetchall()

            # Deduplicate (in case user is owner and collaborator)
            project_ids = set()
            all_rows = []
            for row in owned_rows + collab_rows:
                if row["project_id"] not in project_ids:
                    project_ids.add(row["project_id"])
                    all_rows.append(row)

            # Convert rows to ProjectContext objects
            projects = []
            for row in all_rows:
                project = self._row_to_project(cursor, row)
                if project:
                    projects.append(project)

            self.logger.debug(f"Got {len(projects)} projects for user {username}")
            return projects

        except Exception as e:
            self.logger.error(f"Error getting projects for user {username}: {e}")
            return []
        finally:
            conn.close()

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project with cascading deletes to all related tables

        When foreign_keys are enabled, SQLite automatically deletes all related records
        from child tables (conversation history, requirements, tech stack, constraints,
        team members, notes, maturity scores, category scores, analytics, etc.)

        Args:
            project_id: ID of project to delete

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Explicitly enable foreign keys to ensure cascade deletes work
            self._enable_foreign_keys(cursor)

            # Get cascading delete counts before deletion for logging
            cascade_counts = self._get_cascade_delete_counts(cursor, project_id)

            # Delete the project (cascade deletes will occur automatically)
            cursor.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
            conn.commit()

            deleted = cursor.rowcount > 0
            if deleted:
                self.logger.info(
                    f"Deleted project {project_id} "
                    f"(cascade: {cascade_counts['conversation']} conversation msgs, "
                    f"{cascade_counts['requirements']} requirements, "
                    f"{cascade_counts['tech_stack']} tech stack items, "
                    f"{cascade_counts['constraints']} constraints, "
                    f"{cascade_counts['team_members']} team members, "
                    f"{cascade_counts['notes']} notes, "
                    f"{cascade_counts['maturity']} maturity scores, "
                    f"{cascade_counts['category']} category scores, "
                    f"{cascade_counts['analytics']} analytics records)"
                )
            return deleted

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error deleting project {project_id}: {e}")
            return False
        finally:
            conn.close()

    def archive_project(self, project_id: str) -> bool:
        """
        Archive a project (soft delete)

        Args:
            project_id: ID of project to archive

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE projects
                SET is_archived = 1, archived_at = ?, status = 'archived'
                WHERE project_id = ?
            """,
                (datetime.now().isoformat(), project_id),
            )

            conn.commit()
            success = cursor.rowcount > 0

            if success:
                self.logger.info(f"Archived project {project_id}")
            return success

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error archiving project {project_id}: {e}")
            return False
        finally:
            conn.close()

    def restore_project(self, project_id: str) -> bool:
        """
        Restore an archived project

        Args:
            project_id: ID of project to restore

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE projects
                SET is_archived = 0, archived_at = NULL, status = 'active'
                WHERE project_id = ?
            """,
                (project_id,),
            )

            conn.commit()
            success = cursor.rowcount > 0

            if success:
                self.logger.info(f"Restored project {project_id}")
            return success

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error restoring project {project_id}: {e}")
            return False
        finally:
            conn.close()

    # ========================================================================
    # CONVERSATION HISTORY (Lazy loading support)
    # ========================================================================

    def get_conversation_history(self, project_id: str) -> list[dict]:
        """
        Load conversation history for a project

        This is separated for lazy loading - can be loaded on demand without
        loading entire project.

        Args:
            project_id: ID of project

        Returns:
            List of message dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM conversation_history
                WHERE project_id = ?
                ORDER BY timestamp ASC, rowid ASC
            """,
                (project_id,),
            )

            rows = cursor.fetchall()
            messages = []

            for row in rows:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                # Return with "type" field to match socratic_counselor expectations
                msg = {
                    "type": row["message_type"],  # Use "type" not "role" to match code expectations
                    "content": row["content"],
                    "timestamp": row["timestamp"],
                }
                # Add metadata fields at top level for easier access
                msg.update(metadata)
                messages.append(msg)

            return messages

        except Exception as e:
            self.logger.error(f"Error loading conversation for project {project_id}: {e}")
            return []
        finally:
            conn.close()

    def save_conversation_history(self, project_id: str, history: list[dict]) -> None:
        """
        Save conversation history for a project

        Args:
            project_id: ID of project
            history: List of message dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Clear existing
            cursor.execute("DELETE FROM conversation_history WHERE project_id = ?", (project_id,))

            # Insert new
            for msg in history:
                # Support both "type" and "role" field names
                message_type = msg.get("type") or msg.get("role", "user")
                # Preserve all metadata fields except the main ones
                metadata = {
                    k: v
                    for k, v in msg.items()
                    if k not in ["type", "role", "content", "timestamp"]
                }
                cursor.execute(
                    """
                    INSERT INTO conversation_history (project_id, message_type, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        project_id,
                        message_type,
                        msg.get("content", ""),
                        msg.get("timestamp", datetime.now().isoformat()),
                        json.dumps(metadata) if metadata else json.dumps({}),
                    ),
                )

            conn.commit()

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving conversation for project {project_id}: {e}")
            raise
        finally:
            conn.close()

    def _save_project_notes(self, project_id: str, notes: list[dict]) -> None:
        """
        Save project notes to database

        Args:
            project_id: ID of project
            notes: List of note dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Delete existing notes for this project
            cursor.execute("DELETE FROM project_notes WHERE project_id = ?", (project_id,))

            # Insert new notes
            import json
            for note in notes:
                cursor.execute(
                    """
                    INSERT INTO project_notes (
                        note_id, project_id, title, content, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        note.get("id"),
                        project_id,
                        note.get("title", "Untitled"),
                        note.get("content", ""),
                        note.get("created_at"),
                        note.get("created_at"),  # Use created_at for updated_at on first save
                    ),
                )

            conn.commit()
            self.logger.debug(f"Saved {len(notes)} notes for project {project_id}")

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving notes for project {project_id}: {e}")
            raise
        finally:
            conn.close()

    def _save_pending_questions(self, project_id: str, questions: list[dict]) -> None:
        """
        Save pending questions for a project

        Args:
            project_id: ID of project
            questions: List of question dicts with fields like id, question, phase, status, etc.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Clear existing pending questions
            cursor.execute("DELETE FROM pending_questions WHERE project_id = ?", (project_id,))

            # Insert new pending questions in order
            for i, question in enumerate(questions):
                # Ensure question data is properly serialized
                question_data = (
                    json.dumps(question) if isinstance(question, dict) else str(question)
                )
                cursor.execute(
                    """
                    INSERT INTO pending_questions (project_id, question_data, sort_order)
                    VALUES (?, ?, ?)
                """,
                    (project_id, question_data, i),
                )

            conn.commit()
            self.logger.debug(f"Saved {len(questions)} pending questions for project {project_id}")

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving pending questions for project {project_id}: {e}")
            raise
        finally:
            conn.close()

    def _load_project_notes(self, project_id: str) -> list[dict]:
        """
        Load project notes from database

        Args:
            project_id: ID of project

        Returns:
            List of note dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT note_id as id, title, content, created_at, created_by
                FROM project_notes
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project_id,),
            )

            notes = []
            for row in cursor.fetchall():
                note = {
                    "id": row[0],
                    "title": row[1] or "Untitled",
                    "content": row[2] or "",
                    "created_at": row[3],
                    "created_by": row[4],
                }
                notes.append(note)

            return notes

        except Exception as e:
            self.logger.error(f"Error loading notes for project {project_id}: {e}")
            return []
        finally:
            conn.close()

    def _load_pending_questions(self, project_id: str) -> list[dict]:
        """
        Load pending questions for a project

        Args:
            project_id: ID of project

        Returns:
            List of question dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT question_data FROM pending_questions
                WHERE project_id = ?
                ORDER BY sort_order
                """,
                (project_id,),
            )

            questions = []
            for row in cursor.fetchall():
                try:
                    question = json.loads(row[0])
                    questions.append(question)
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to decode question data for project {project_id}")
                    continue

            return questions

        except Exception as e:
            self.logger.error(f"Error loading pending questions for project {project_id}: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # PRE-SESSION CONVERSATIONS (before project selection)
    # ========================================================================

    def save_free_session_message(
        self,
        username: str,
        session_id: str,
        message_type: str,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        """
        Save a single message to free_session conversation history.

        Args:
            username: User who created the message
            session_id: Session identifier for grouping conversations
            message_type: Either 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (topics, intents, etc.)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO free_session_conversations
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
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(
                f"Error saving free_session message for {username} in session {session_id}: {e}"
            )
            raise
        finally:
            conn.close()

    def get_free_session_conversation(
        self, username: str, session_id: str, limit: int = 50
    ) -> list[dict]:
        """
        Load free_session conversation history for a specific session.

        Args:
            username: Username to filter by
            session_id: Session identifier
            limit: Maximum number of messages to return

        Returns:
            List of message dicts with timestamp and metadata
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM free_session_conversations
                WHERE username = ? AND session_id = ?
                ORDER BY timestamp ASC, rowid ASC
                LIMIT ?
            """,
                (username, session_id, limit),
            )

            rows = cursor.fetchall()
            messages = []

            for row in rows:
                messages.append(
                    {
                        "role": row["message_type"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    }
                )

            return messages

        except Exception as e:
            self.logger.error(
                f"Error loading free_session conversation for {username} session {session_id}: {e}"
            )
            return []
        finally:
            conn.close()

    def get_free_session_sessions(self, username: str, limit: int = 20) -> list[dict]:
        """
        Get list of free_session sessions for a user.

        Args:
            username: Username to filter by
            limit: Maximum number of sessions to return

        Returns:
            List of session dicts with metadata
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    session_id,
                    MIN(timestamp) as started_at,
                    MAX(timestamp) as last_activity,
                    COUNT(*) as message_count,
                    SUM(CASE WHEN message_type = 'user' THEN 1 ELSE 0 END) as user_messages,
                    SUM(CASE WHEN message_type = 'assistant' THEN 1 ELSE 0 END) as assistant_messages
                FROM free_session_conversations
                WHERE username = ?
                GROUP BY session_id
                ORDER BY MAX(timestamp) DESC
                LIMIT ?
            """,
                (username, limit),
            )

            rows = cursor.fetchall()
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

        except Exception as e:
            self.logger.error(f"Error loading free_session sessions for {username}: {e}")
            return []
        finally:
            conn.close()

    def delete_free_session_session(self, username: str, session_id: str) -> bool:
        """
        Delete a free_session session and all its messages.

        Args:
            username: Username (for authorization check)
            session_id: Session identifier to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Verify ownership by checking if session exists for this user
            cursor.execute(
                "SELECT COUNT(*) as count FROM free_session_conversations WHERE username = ? AND session_id = ?",
                (username, session_id),
            )
            if cursor.fetchone()["count"] == 0:
                self.logger.warning(
                    f"free-session session {session_id} not found for user {username}"
                )
                return False

            # Delete all messages in session
            cursor.execute(
                "DELETE FROM free_session_conversations WHERE username = ? AND session_id = ?",
                (username, session_id),
            )
            conn.commit()
            self.logger.info(f"Deleted free_session session {session_id} for user {username}")
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(
                f"Error deleting free_session session {session_id} for {username}: {e}"
            )
            return False
        finally:
            conn.close()

    # ========================================================================
    # USER OPERATIONS
    # ========================================================================

    def save_user(self, user: User) -> None:
        """Save or update a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            sub_start = getattr(user, "subscription_start", None)
            sub_end = getattr(user, "subscription_end", None)
            is_archived = getattr(user, "is_archived", False)
            archived_at = getattr(user, "archived_at", None)

            cursor.execute(
                """
                INSERT OR REPLACE INTO users (
                    username, email, passcode_hash, subscription_tier, subscription_status,
                    subscription_start, subscription_end, testing_mode, created_at,
                    claude_auth_method, is_archived, archived_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user.username,
                    user.email,
                    user.passcode_hash,
                    getattr(user, "subscription_tier", "free"),
                    getattr(user, "subscription_status", "active"),
                    serialize_datetime(sub_start) if sub_start else None,
                    serialize_datetime(sub_end) if sub_end else None,
                    getattr(user, "testing_mode", False),
                    serialize_datetime(user.created_at),
                    getattr(user, "claude_auth_method", "api_key"),
                    is_archived,
                    serialize_datetime(archived_at) if archived_at else None,
                ),
            )

            conn.commit()

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving user {user.username}: {e}")
            raise
        finally:
            conn.close()

    def load_user(self, username: str) -> User | None:
        """Load a user by username"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()

            if not row:
                return None

            user = User(
                username=row["username"],
                email=row["email"],
                passcode_hash=row["passcode_hash"],
                created_at=deserialize_datetime(row["created_at"]),
            )

            # Set optional fields
            user.subscription_tier = row["subscription_tier"]
            user.subscription_status = row["subscription_status"]
            user.testing_mode = bool(row["testing_mode"])
            try:
                user.claude_auth_method = row["claude_auth_method"] or "api_key"
            except (IndexError, KeyError):
                user.claude_auth_method = "api_key"

            # Set archive fields
            try:
                user.is_archived = bool(row["is_archived"])
                user.archived_at = (
                    deserialize_datetime(row["archived_at"]) if row["archived_at"] else None
                )
            except (IndexError, KeyError):
                user.is_archived = False
                user.archived_at = None

            return user

        except Exception as e:
            self.logger.error(f"Error loading user {username}: {e}")
            return None
        finally:
            conn.close()

    def load_user_by_email(self, email: str) -> User | None:
        """Load a user by email address"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()

            if not row:
                return None

            user = User(
                username=row["username"],
                email=row["email"],
                passcode_hash=row["passcode_hash"],
                created_at=deserialize_datetime(row["created_at"]),
            )

            # Set optional fields
            user.subscription_tier = row["subscription_tier"]
            user.subscription_status = row["subscription_status"]
            user.testing_mode = bool(row["testing_mode"])
            try:
                user.claude_auth_method = row["claude_auth_method"] or "api_key"
            except (IndexError, KeyError):
                user.claude_auth_method = "api_key"

            # Set archive fields
            try:
                user.is_archived = bool(row["is_archived"])
                user.archived_at = (
                    deserialize_datetime(row["archived_at"]) if row["archived_at"] else None
                )
            except (IndexError, KeyError):
                user.is_archived = False
                user.archived_at = None

            return user

        except Exception as e:
            self.logger.error(f"Error loading user by email {email}: {e}")
            return None
        finally:
            conn.close()

    def get_user_llm_configs(self, user_id: str) -> list[dict[str, Any]]:
        """
        Get all LLM provider configurations for a user.

        Args:
            user_id: Username to get configs for

        Returns:
            List of LLM configuration dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, user_id, provider, config_data, created_at, updated_at
                FROM llm_provider_configs
                WHERE user_id = ?
                ORDER BY created_at DESC
            """,
                (user_id,),
            )

            configs = []
            for row in cursor.fetchall():
                config_dict = {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "provider": row["provider"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }

                # Parse JSON config data
                if row["config_data"]:
                    try:
                        config_dict["config"] = json.loads(row["config_data"])
                    except json.JSONDecodeError:
                        self.logger.warning(
                            f"Invalid JSON in config for {user_id}/{row['provider']}"
                        )
                        config_dict["config"] = {}

                configs.append(config_dict)

            return configs

        except Exception as e:
            self.logger.error(f"Error loading LLM configs for {user_id}: {e}")
            return []
        finally:
            conn.close()

    def get_user_llm_config(self, user_id: str, provider: str) -> dict[str, Any] | None:
        """
        Get single LLM provider configuration for a user.

        Args:
            user_id: Username
            provider: Provider name (e.g., 'claude', 'openai')

        Returns:
            Configuration dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, user_id, provider, config_data, created_at, updated_at
                FROM llm_provider_configs
                WHERE user_id = ? AND provider = ?
            """,
                (user_id, provider),
            )

            row = cursor.fetchone()
            if not row:
                return None

            config_dict = {
                "id": row["id"],
                "user_id": row["user_id"],
                "provider": row["provider"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

            # Parse JSON config data
            if row["config_data"]:
                try:
                    config_dict["config"] = json.loads(row["config_data"])
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON in config for {user_id}/{provider}")
                    config_dict["config"] = {}

            return config_dict

        except Exception as e:
            self.logger.error(f"Error loading LLM config for {user_id}/{provider}: {e}")
            return None
        finally:
            conn.close()

    def save_llm_config(self, user_id: str, provider: str, config_data: dict[str, Any]) -> bool:
        """
        Save or update an LLM provider configuration.

        Args:
            user_id: Username
            provider: Provider name (e.g., 'claude', 'openai')
            config_data: Configuration dictionary

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            config_id = f"{user_id}:{provider}:{int(datetime.now().timestamp())}"
            now = datetime.now()

            cursor.execute(
                """
                INSERT OR REPLACE INTO llm_provider_configs
                (id, user_id, provider, config_data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    config_id,
                    user_id,
                    provider,
                    json.dumps(config_data),
                    serialize_datetime(now),
                    serialize_datetime(now),
                ),
            )

            conn.commit()
            self.logger.debug(f"Saved LLM config for {user_id}/{provider}")
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving LLM config for {user_id}/{provider}: {e}")
            return False
        finally:
            conn.close()

    def save_api_key(self, user_id: str, provider: str, encrypted_key: str, key_hash: str) -> bool:
        """
        Save or update an API key for a provider.

        Args:
            user_id: Username
            provider: Provider name (e.g., 'claude', 'openai')
            encrypted_key: Encrypted API key
            key_hash: Hash of the API key for verification

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            api_key_id = f"{user_id}:{provider}:{int(datetime.now().timestamp())}"
            now = datetime.now()

            cursor.execute(
                """
                INSERT OR REPLACE INTO api_keys
                (id, user_id, provider, encrypted_key, key_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    api_key_id,
                    user_id,
                    provider,
                    encrypted_key,
                    key_hash,
                    serialize_datetime(now),
                    serialize_datetime(now),
                ),
            )

            conn.commit()
            self.logger.debug(f"Saved API key for {user_id}/{provider}")
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving API key for {user_id}/{provider}: {e}")
            return False
        finally:
            conn.close()

    def get_api_key(self, user_id: str, provider: str) -> str | None:
        """
        Get encrypted API key for a provider.

        Args:
            user_id: Username
            provider: Provider name (e.g., 'claude', 'openai')

        Returns:
            Encrypted API key or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT encrypted_key FROM api_keys
                WHERE user_id = ? AND provider = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """,
                (user_id, provider),
            )

            row = cursor.fetchone()
            if row:
                return row["encrypted_key"]
            return None

        except Exception as e:
            self.logger.error(f"Error loading API key for {user_id}/{provider}: {e}")
            return None
        finally:
            conn.close()

    def delete_api_key(self, user_id: str, provider: str) -> bool:
        """
        Delete an API key for a provider.

        Args:
            user_id: Username
            provider: Provider name (e.g., 'claude', 'openai')

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                DELETE FROM api_keys
                WHERE user_id = ? AND provider = ?
            """,
                (user_id, provider),
            )

            conn.commit()
            self.logger.debug(f"Deleted API key for {user_id}/{provider}")
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error deleting API key for {user_id}/{provider}: {e}")
            return False
        finally:
            conn.close()

    def save_knowledge_document(
        self,
        user_id: str,
        project_id: str,
        doc_id: str,
        title: str = "",
        content: str = "",
        source: str | None = None,
        document_type: str = "document",
        file_path: str | None = None,
        file_size: int | None = None,
    ) -> bool:
        """
        Save a knowledge document (entry).

        Args:
            user_id: Username
            project_id: Project ID
            doc_id: Document ID
            title: Document title
            content: Document content
            source: Optional source reference
            document_type: Type of document
            file_path: Optional path to stored file
            file_size: Optional file size in bytes

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now()

            # Try inserting with all columns including file_path and file_size
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO knowledge_documents
                    (id, project_id, user_id, title, content, source, document_type, file_path, file_size, uploaded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        doc_id,
                        project_id,
                        user_id,
                        title,
                        content,
                        source,
                        document_type,
                        file_path,
                        file_size,
                        serialize_datetime(now),
                    ),
                )
            except sqlite3.OperationalError as col_err:
                # If file_path/file_size columns don't exist, insert without them
                if "no column named file_path" in str(
                    col_err
                ) or "no column named file_size" in str(col_err):
                    self.logger.debug(
                        f"file_path/file_size columns not found, inserting without them: {col_err}"
                    )
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO knowledge_documents
                        (id, project_id, user_id, title, content, source, document_type, uploaded_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            doc_id,
                            project_id,
                            user_id,
                            title,
                            content,
                            source,
                            document_type,
                            serialize_datetime(now),
                        ),
                    )
                else:
                    raise

            conn.commit()
            self.logger.debug(f"Saved knowledge document {doc_id} for project {project_id}")
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving knowledge document {doc_id}: {e}")
            return False
        finally:
            conn.close()

    # ========================================================================
    # USER MANAGEMENT METHODS
    # ========================================================================

    def user_exists(self, username: str) -> bool:
        """Check if a user exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            return result is not None
        finally:
            conn.close()

    def archive_user(self, username: str, archive_projects: bool = True) -> bool:
        """Archive a user (soft delete)"""
        try:
            user = self.load_user(username)
            if not user:
                return False

            user.is_archived = True
            user.archived_at = datetime.now()
            self.save_user(user)

            if archive_projects:
                # Archive all projects owned by this user
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    "UPDATE projects SET is_archived = 1, updated_at = ? WHERE owner = ? AND is_archived = 0",
                    (serialize_datetime(datetime.now()), username),
                )
                conn.commit()
                conn.close()

            self.logger.debug(f"Archived user {username}")
            return True

        except Exception as e:
            self.logger.error(f"Error archiving user {username}: {e}")
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
            self.logger.debug(f"Restored user {username}")
            return True

        except Exception as e:
            self.logger.error(f"Error restoring user {username}: {e}")
            return False

    def permanently_delete_user(self, username: str) -> bool:
        """Permanently delete a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Delete user and all associated data
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            cursor.execute("DELETE FROM question_effectiveness WHERE user_id = ?", (username,))
            cursor.execute("DELETE FROM behavior_patterns WHERE user_id = ?", (username,))
            cursor.execute("DELETE FROM llm_usage WHERE user_id = ?", (username,))
            cursor.execute("DELETE FROM knowledge_documents WHERE user_id = ?", (username,))

            conn.commit()
            self.logger.debug(f"Permanently deleted user {username}")
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error deleting user {username}: {e}")
            return False
        finally:
            conn.close()

    # ========================================================================
    # LEARNING METHODS - QUESTION EFFECTIVENESS
    # ========================================================================

    def save_question_effectiveness(self, effectiveness: QuestionEffectiveness) -> bool:
        """Save question effectiveness record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Convert Decimal to float for SQLite compatibility
            effectiveness_score = getattr(effectiveness, "effectiveness_score", 0.5)
            if hasattr(effectiveness_score, "__float__"):
                effectiveness_score = float(effectiveness_score)

            times_asked = getattr(effectiveness, "times_asked", 0)
            if hasattr(times_asked, "__int__"):
                times_asked = int(times_asked)

            times_answered_well = getattr(effectiveness, "times_answered_well", 0)
            if hasattr(times_answered_well, "__int__"):
                times_answered_well = int(times_answered_well)

            last_asked_at = getattr(effectiveness, "last_asked_at", None)
            if last_asked_at:
                last_asked_at = serialize_datetime(last_asked_at)

            created_at_str = serialize_datetime(effectiveness.created_at)
            updated_at_str = serialize_datetime(effectiveness.updated_at)

            cursor.execute(
                """
                INSERT OR REPLACE INTO question_effectiveness
                (id, user_id, question_template_id, effectiveness_score, times_asked,
                 times_answered_well, last_asked_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    effectiveness.id,
                    effectiveness.user_id,
                    effectiveness.question_template_id,
                    effectiveness_score,
                    times_asked,
                    times_answered_well,
                    last_asked_at,
                    created_at_str,
                    updated_at_str,
                ),
            )

            conn.commit()
            self.logger.debug(
                f"Saved question effectiveness for {effectiveness.user_id}/{effectiveness.question_template_id}"
            )
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving question effectiveness: {e}")
            return False
        finally:
            conn.close()

    def get_question_effectiveness(
        self, user_id: str, question_template_id: str
    ) -> dict[str, any] | None:
        """Get question effectiveness record for a user-question pair"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, user_id, question_template_id, effectiveness_score, times_asked,
                       times_answered_well, last_asked_at, created_at, updated_at
                FROM question_effectiveness
                WHERE user_id = ? AND question_template_id = ?
            """,
                (user_id, question_template_id),
            )
            result = cursor.fetchone()

            if result:
                effectiveness_dict = {
                    "id": result[0],
                    "user_id": result[1],
                    "question_template_id": result[2],
                    "effectiveness_score": result[3],
                    "times_asked": result[4],
                    "times_answered_well": result[5],
                    "last_asked_at": deserialize_datetime(result[6]) if result[6] else None,
                    "created_at": deserialize_datetime(result[7]) if result[7] else None,
                    "updated_at": deserialize_datetime(result[8]) if result[8] else None,
                }
                return effectiveness_dict

            return None

        except Exception as e:
            self.logger.error(
                f"Error getting question effectiveness for {user_id}/{question_template_id}: {e}"
            )
            return None
        finally:
            conn.close()

    def get_user_effectiveness_all(self, user_id: str) -> list[dict[str, any]]:
        """Get all question effectiveness records for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, user_id, question_template_id, effectiveness_score, times_asked,
                       times_answered_well, last_asked_at, created_at, updated_at
                FROM question_effectiveness
                WHERE user_id = ?
            """,
                (user_id,),
            )
            results = cursor.fetchall()

            effectiveness_records = []
            for result in results:
                try:
                    eff_data = {
                        "id": result[0],
                        "user_id": result[1],
                        "question_template_id": result[2],
                        "effectiveness_score": result[3],
                        "times_asked": result[4],
                        "times_answered_well": result[5],
                        "last_asked_at": deserialize_datetime(result[6]) if result[6] else None,
                        "created_at": deserialize_datetime(result[7]) if result[7] else None,
                        "updated_at": deserialize_datetime(result[8]) if result[8] else None,
                    }
                    effectiveness_records.append(eff_data)
                except Exception as e:
                    self.logger.warning(f"Could not load effectiveness record: {e}")

            return effectiveness_records

        except Exception as e:
            self.logger.error(f"Error getting user effectiveness records: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # LEARNING METHODS - BEHAVIOR PATTERNS
    # ========================================================================

    def save_behavior_pattern(self, pattern: UserBehaviorPattern) -> bool:
        """Save behavior pattern record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            pattern_dict = pattern.to_dict() if hasattr(pattern, "to_dict") else asdict(pattern)
            pattern_data = json.dumps(pattern_dict)
            learned_at_str = serialize_datetime(pattern.learned_at)
            updated_at_str = serialize_datetime(pattern.updated_at)
            frequency = getattr(pattern, "frequency", 1)

            cursor.execute(
                """
                INSERT OR REPLACE INTO behavior_patterns
                (id, user_id, pattern_type, pattern_data, frequency, learned_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pattern.id,
                    pattern.user_id,
                    pattern.pattern_type,
                    pattern_data,
                    frequency,
                    learned_at_str,
                    updated_at_str,
                ),
            )

            conn.commit()
            self.logger.debug(
                f"Saved behavior pattern for {pattern.user_id}/{pattern.pattern_type}"
            )
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving behavior pattern: {e}")
            return False
        finally:
            conn.close()

    def get_behavior_pattern(self, user_id: str, pattern_type: str) -> dict[str, any] | None:
        """Get behavior pattern for a user-pattern_type pair"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, user_id, pattern_type, pattern_data, frequency, learned_at, updated_at
                FROM behavior_patterns
                WHERE user_id = ? AND pattern_type = ?
            """,
                (user_id, pattern_type),
            )
            result = cursor.fetchone()

            if result:
                pattern_data_json = result[3]
                pattern_dict = json.loads(pattern_data_json) if pattern_data_json else {}
                # Add metadata fields
                pattern_dict["id"] = result[0]
                pattern_dict["user_id"] = result[1]
                pattern_dict["pattern_type"] = result[2]
                pattern_dict["frequency"] = result[4]
                pattern_dict["learned_at"] = deserialize_datetime(result[5]) if result[5] else None
                pattern_dict["updated_at"] = deserialize_datetime(result[6]) if result[6] else None

                return pattern_dict

            return None

        except Exception as e:
            self.logger.error(f"Error getting behavior pattern for {user_id}/{pattern_type}: {e}")
            return None
        finally:
            conn.close()

    def get_user_behavior_patterns(self, user_id: str) -> list[dict[str, any]]:
        """Get all behavior patterns for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, user_id, pattern_type, pattern_data, frequency, learned_at, updated_at
                FROM behavior_patterns
                WHERE user_id = ?
            """,
                (user_id,),
            )
            results = cursor.fetchall()

            patterns = []
            for result in results:
                try:
                    pattern_data_json = result[3]
                    pattern_dict = json.loads(pattern_data_json) if pattern_data_json else {}
                    # Add metadata fields
                    pattern_dict["id"] = result[0]
                    pattern_dict["user_id"] = result[1]
                    pattern_dict["pattern_type"] = result[2]
                    pattern_dict["frequency"] = result[4]
                    pattern_dict["learned_at"] = (
                        deserialize_datetime(result[5]) if result[5] else None
                    )
                    pattern_dict["updated_at"] = (
                        deserialize_datetime(result[6]) if result[6] else None
                    )

                    patterns.append(pattern_dict)
                except Exception as e:
                    self.logger.warning(f"Could not load behavior pattern: {e}")

            return patterns

        except Exception as e:
            self.logger.error(f"Error getting user behavior patterns: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # NOTE MANAGEMENT METHODS
    # ========================================================================

    def delete_note(self, note_id: str) -> bool:
        """Delete a note by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM project_notes WHERE note_id = ?", (note_id,))
            conn.commit()
            self.logger.debug(f"Deleted note {note_id}")
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error deleting note {note_id}: {e}")
            return False
        finally:
            conn.close()

    def search_notes(self, project_id: str, query: str) -> list[ProjectNote]:
        """Search notes for a project by content"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Search in title and content
            search_pattern = f"%{query}%"
            cursor.execute(
                """
                SELECT note_id, project_id, title, content, created_at
                FROM project_notes
                WHERE project_id = ? AND (title LIKE ? OR content LIKE ?)
                ORDER BY created_at DESC
            """,
                (project_id, search_pattern, search_pattern),
            )

            notes = []
            for row in cursor.fetchall():
                note = ProjectNote(
                    note_id=row["note_id"],
                    project_id=row["project_id"],
                    title=row["title"],
                    content=row["content"],
                    note_type="general",  # Not stored in DB
                    created_at=deserialize_datetime(row["created_at"]),
                    created_by="unknown",  # Not stored in DB
                    tags=[],  # Not stored in DB
                )
                notes.append(note)

            return notes

        except Exception as e:
            self.logger.error(f"Error searching notes for project {project_id}: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # KNOWLEDGE DOCUMENT METHODS
    # ========================================================================

    def get_knowledge_document(self, doc_id: str) -> dict[str, any] | None:
        """Get a single knowledge document"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Try to get document with content column
            try:
                cursor.execute(
                    """
                    SELECT id, project_id, user_id, title, content, source, document_type, uploaded_at
                    FROM knowledge_documents
                    WHERE id = ?
                """,
                    (doc_id,),
                )
                row = cursor.fetchone()

                if row:
                    return {
                        "id": row[0],
                        "project_id": row[1],
                        "user_id": row[2],
                        "title": row[3],
                        "content": row[4],
                        "source": row[5],
                        "document_type": row[6],
                        "uploaded_at": row[7],
                    }
            except sqlite3.OperationalError as col_err:
                # Column doesn't exist, try without content
                if "no column named content" in str(col_err):
                    cursor.execute(
                        """
                        SELECT id, project_id, user_id, title, source, document_type, uploaded_at
                        FROM knowledge_documents
                        WHERE id = ?
                    """,
                        (doc_id,),
                    )
                    row = cursor.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "project_id": row[1],
                            "user_id": row[2],
                            "title": row[3],
                            "content": "",  # Empty content if column doesn't exist
                            "source": row[4],
                            "document_type": row[5],
                            "uploaded_at": row[6],
                        }
                else:
                    raise

            return None

        except Exception as e:
            self.logger.error(f"Error getting knowledge document {doc_id}: {e}")
            return None
        finally:
            conn.close()

    def get_project_knowledge_documents(self, project_id: str) -> list[dict[str, any]]:
        """Get all knowledge documents for a project (includes file_size for storage tracking)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Try to get documents with all columns including file_size
            try:
                cursor.execute(
                    """
                    SELECT id, project_id, user_id, title, content, source, document_type, file_size, uploaded_at
                    FROM knowledge_documents
                    WHERE project_id = ?
                    ORDER BY uploaded_at DESC
                """,
                    (project_id,),
                )
            except sqlite3.OperationalError as col_err:
                # Fallback for older schema without file_size
                try:
                    if "no column named file_size" in str(col_err):
                        cursor.execute(
                            """
                            SELECT id, project_id, user_id, title, content, source, document_type, uploaded_at
                            FROM knowledge_documents
                            WHERE project_id = ?
                            ORDER BY uploaded_at DESC
                        """,
                            (project_id,),
                        )
                    else:
                        raise
                except sqlite3.OperationalError as col_err2:
                    # Try without content column
                    if "no column named content" in str(col_err2):
                        cursor.execute(
                            """
                            SELECT id, project_id, user_id, title, source, document_type, uploaded_at
                            FROM knowledge_documents
                            WHERE project_id = ?
                            ORDER BY uploaded_at DESC
                        """,
                            (project_id,),
                        )
                    else:
                        raise

            documents = []
            for row in cursor.fetchall():
                # Handle different column configurations
                if len(row) == 9:
                    # With file_size and content
                    documents.append(
                        {
                            "id": row[0],
                            "project_id": row[1],
                            "user_id": row[2],
                            "title": row[3],
                            "content": row[4],
                            "source": row[5],
                            "document_type": row[6],
                            "file_size": row[7] or 0,
                            "uploaded_at": row[8],
                        }
                    )
                elif len(row) == 8:
                    # With content but no file_size
                    documents.append(
                        {
                            "id": row[0],
                            "project_id": row[1],
                            "user_id": row[2],
                            "title": row[3],
                            "content": row[4],
                            "source": row[5],
                            "document_type": row[6],
                            "file_size": 0,
                            "uploaded_at": row[7],
                        }
                    )
                else:
                    # Without content column (legacy)
                    documents.append(
                        {
                            "id": row[0],
                            "project_id": row[1],
                            "user_id": row[2],
                            "title": row[3],
                            "content": "",
                            "source": row[4],
                            "document_type": row[5],
                            "file_size": 0,
                            "uploaded_at": row[6],
                        }
                    )

            return documents

        except Exception as e:
            self.logger.error(f"Error getting knowledge documents for project {project_id}: {e}")
            return []
        finally:
            conn.close()

    def delete_knowledge_document(self, doc_id: str) -> bool:
        """Delete a knowledge document by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM knowledge_documents WHERE id = ?", (doc_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error deleting knowledge document {doc_id}: {e}")
            return False
        finally:
            conn.close()

    def get_user_knowledge_documents(self, user_id: str) -> list:
        """Get all knowledge documents for a user across all projects"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, project_id, user_id, title, content, source,
                       document_type, uploaded_at
                FROM knowledge_documents
                WHERE user_id = ?
                ORDER BY uploaded_at DESC
                """,
                (user_id,),
            )

            documents = []
            for row in cursor.fetchall():
                documents.append(
                    {
                        "id": row[0],
                        "project_id": row[1],
                        "user_id": row[2],
                        "title": row[3],
                        "content": row[4],
                        "source": row[5],
                        "document_type": row[6],
                        "uploaded_at": row[7],
                    }
                )

            return documents
        except Exception as e:
            self.logger.error(f"Error getting user knowledge documents: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # USAGE TRACKING METHODS
    # ========================================================================

    def save_usage_record(self, usage: LLMUsageRecord) -> bool:
        """Save LLM usage record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            usage_dict = usage.to_dict() if hasattr(usage, "to_dict") else asdict(usage)
            usage_json = json.dumps(usage_dict)
            timestamp_str = serialize_datetime(usage.timestamp)
            cost = getattr(usage, "cost", 0.0)

            cursor.execute(
                """
                INSERT INTO llm_usage
                (id, user_id, provider, model, usage_json, timestamp, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    usage.id,
                    usage.user_id,
                    usage.provider,
                    usage.model,
                    usage_json,
                    timestamp_str,
                    cost,
                ),
            )

            conn.commit()
            self.logger.debug(f"Saved usage record for {usage.user_id}/{usage.provider}")
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving usage record: {e}")
            return False
        finally:
            conn.close()

    def get_usage_records(self, user_id: str, days: int, provider: str) -> list[dict[str, any]]:
        """Get usage records for a user within specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = serialize_datetime(cutoff_date)

            cursor.execute(
                """
                SELECT id, user_id, provider, model, usage_json, timestamp, cost
                FROM llm_usage
                WHERE user_id = ? AND provider = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (user_id, provider, cutoff_str),
            )

            records = []
            for row in cursor.fetchall():
                usage_dict = json.loads(row[4])
                records.append(
                    {
                        "id": row[0],
                        "user_id": row[1],
                        "provider": row[2],
                        "model": row[3],
                        "usage": usage_dict,
                        "timestamp": row[5],
                        "cost": row[6],
                    }
                )

            return records

        except Exception as e:
            self.logger.error(f"Error getting usage records for {user_id}/{provider}: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # ARCHIVED ITEMS & UTILITY METHODS
    # ========================================================================

    def get_archived_items(self, item_type: str) -> list[dict[str, any]]:
        """Get archived items (projects or users)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            items = []

            if item_type == "projects":
                cursor.execute(
                    """
                    SELECT project_id, name, owner, phase, updated_at
                    FROM projects
                    WHERE is_archived = 1
                    ORDER BY updated_at DESC
                """
                )

                for row in cursor.fetchall():
                    items.append(
                        {
                            "project_id": row[0],
                            "name": row[1],
                            "owner": row[2],
                            "phase": row[3],
                            "updated_at": row[4],
                            "type": "project",
                        }
                    )

            elif item_type == "users":
                cursor.execute(
                    """
                    SELECT username, created_at
                    FROM users
                    WHERE is_archived = 1
                    ORDER BY created_at DESC
                """
                )

                for row in cursor.fetchall():
                    items.append(
                        {
                            "username": row[0],
                            "created_at": row[1],
                            "type": "user",
                        }
                    )

            return items

        except Exception as e:
            self.logger.error(f"Error getting archived {item_type}: {e}")
            return []
        finally:
            conn.close()

    def permanently_delete_project(self, project_id: str) -> bool:
        """Permanently delete a project (alias for delete_project)"""
        return self.delete_project(project_id)

    def unset_other_default_providers(self, user_id: str, current_provider: str) -> None:
        """Unset all other default LLM providers when setting a new default"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE llm_provider_configs
                SET is_default = 0
                WHERE user_id = ? AND provider != ?
            """,
                (user_id, current_provider),
            )
            conn.commit()
            self.logger.debug(f"Unset other default providers for {user_id}")

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error unsetting other default providers: {e}")
        finally:
            conn.close()

    # ========================================================================
    # UPDATED SIGNATURE METHODS - HANDLE BOTH OBJECT AND PARAMETER SIGNATURES
    # ========================================================================

    def _save_llm_config_impl(
        self, user_id: str, provider: str, config_data: dict[str, any]
    ) -> bool:
        """Internal implementation for saving LLM config"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            config_json = json.dumps(config_data)
            now = datetime.now()

            cursor.execute(
                """
                INSERT OR REPLACE INTO llm_provider_configs
                (id, user_id, provider, config_data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    f"{user_id}_{provider}",
                    user_id,
                    provider,
                    config_json,
                    serialize_datetime(now),
                    serialize_datetime(now),
                ),
            )

            conn.commit()
            self.logger.debug(f"Saved LLM config for {user_id}/{provider}")
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving LLM config: {e}")
            return False
        finally:
            conn.close()

    def _save_api_key_impl(
        self, user_id: str, provider: str, encrypted_key: str, key_hash: str
    ) -> bool:
        """Internal implementation for saving API key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now()

            cursor.execute(
                """
                INSERT OR REPLACE INTO api_keys
                (id, user_id, provider, encrypted_key, key_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    f"{user_id}_{provider}",
                    user_id,
                    provider,
                    encrypted_key,
                    key_hash,
                    serialize_datetime(now),
                    serialize_datetime(now),
                ),
            )

            conn.commit()
            self.logger.debug(f"Saved API key for {user_id}/{provider}")
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving API key: {e}")
            return False
        finally:
            conn.close()

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _row_to_project(self, cursor: sqlite3.Cursor, row: sqlite3.Row) -> ProjectContext | None:
        """Convert a database row to ProjectContext"""
        try:
            requirements = self._load_project_requirements(cursor, row["project_id"])
            tech_stack = self._load_project_tech_stack(cursor, row["project_id"])
            constraints = self._load_project_constraints(cursor, row["project_id"])
            team_members = self._load_team_members(cursor, row["project_id"])
            phase_maturity = self._load_phase_maturity(cursor, row["project_id"])
            category_scores = self._load_category_scores(cursor, row["project_id"])
            analytics = self._load_analytics_metrics(cursor, row["project_id"])

            # Deserialize JSON fields (only if they're actually JSON)
            def try_json_load(value):
                """Try to parse as JSON, return original value if not JSON"""
                if not value or not isinstance(value, str):
                    return value
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value

            goals = try_json_load(row["goals"])
            team_structure = try_json_load(row["team_structure"])
            language_preferences = try_json_load(row["language_preferences"])
            code_style = try_json_load(row["code_style"])

            return ProjectContext(
                project_id=row["project_id"],
                name=row["name"],
                owner=row["owner"],
                phase=row["phase"],
                created_at=deserialize_datetime(row["created_at"]),
                updated_at=deserialize_datetime(row["updated_at"]),
                goals=goals,
                requirements=requirements,
                tech_stack=tech_stack,
                constraints=constraints,
                team_structure=team_structure,
                language_preferences=language_preferences,
                deployment_target=row["deployment_target"],
                code_style=code_style,
                chat_mode=row["chat_mode"],
                status=row["status"],
                progress=row["progress"],
                is_archived=bool(row["is_archived"]),
                archived_at=(
                    deserialize_datetime(row["archived_at"]) if row["archived_at"] else None
                ),
                project_type=row["project_type"],
                team_members=team_members,
                phase_maturity_scores=phase_maturity,
                category_scores=category_scores,
                analytics_metrics=analytics,
            )

        except Exception as e:
            self.logger.error(f"Error converting row to project: {e}")
            return None

    def _load_project_requirements(self, cursor: sqlite3.Cursor, project_id: str) -> list[str]:
        """Load project requirements"""
        cursor.execute(
            """
            SELECT requirement FROM project_requirements
            WHERE project_id = ? ORDER BY sort_order
        """,
            (project_id,),
        )
        return [row[0] for row in cursor.fetchall()]

    def _load_project_tech_stack(self, cursor: sqlite3.Cursor, project_id: str) -> list[str]:
        """Load project tech stack"""
        cursor.execute(
            """
            SELECT technology FROM project_tech_stack
            WHERE project_id = ? ORDER BY sort_order
        """,
            (project_id,),
        )
        return [row[0] for row in cursor.fetchall()]

    def _load_project_constraints(self, cursor: sqlite3.Cursor, project_id: str) -> list[str]:
        """Load project constraints"""
        cursor.execute(
            """
            SELECT constraint_text FROM project_constraints
            WHERE project_id = ? ORDER BY sort_order
        """,
            (project_id,),
        )
        return [row[0] for row in cursor.fetchall()]

    def _load_team_members(self, cursor: sqlite3.Cursor, project_id: str):
        """Load team members"""
        from socratic_system.models.role import TeamMemberRole

        cursor.execute(
            """
            SELECT username, role, skills, joined_at FROM team_members
            WHERE project_id = ?
        """,
            (project_id,),
        )

        members = []
        for row in cursor.fetchall():
            skills = json.loads(row[2]) if row[2] else {}
            joined_at = deserialize_datetime(row[3]) if row[3] else datetime.now()

            member = TeamMemberRole(
                username=row[0], role=row[1], skills=skills, joined_at=joined_at
            )
            members.append(member)

        return members if members else None

    def _load_phase_maturity(
        self, cursor: sqlite3.Cursor, project_id: str
    ) -> dict[str, float] | None:
        """Load phase maturity scores"""
        cursor.execute(
            """
            SELECT phase, score FROM phase_maturity_scores
            WHERE project_id = ?
        """,
            (project_id,),
        )

        scores = {}
        for phase, score in cursor.fetchall():
            scores[phase] = score

        return scores if scores else None

    def _load_category_scores(
        self, cursor: sqlite3.Cursor, project_id: str
    ) -> dict[str, dict[str, float]] | None:
        """Load category scores"""
        cursor.execute(
            """
            SELECT phase, category, score FROM category_scores
            WHERE project_id = ?
        """,
            (project_id,),
        )

        scores = {}
        for phase, category, score in cursor.fetchall():
            if phase not in scores:
                scores[phase] = {}
            scores[phase][category] = score

        return scores if scores else None

    def _load_analytics_metrics(self, cursor: sqlite3.Cursor, project_id: str) -> dict | None:
        """Load analytics metrics"""
        cursor.execute(
            """
            SELECT velocity, total_qa_sessions, avg_confidence, weak_categories, strong_categories
            FROM analytics_metrics WHERE project_id = ?
        """,
            (project_id,),
        )

        row = cursor.fetchone()
        if not row:
            return None

        return {
            "velocity": row[0],
            "total_qa_sessions": row[1],
            "avg_confidence": row[2],
            "weak_categories": json.loads(row[3]) if row[3] else [],
            "strong_categories": json.loads(row[4]) if row[4] else [],
        }

    def _load_categorized_specs(
        self, cursor: sqlite3.Cursor, project_id: str
    ) -> dict[str, list[dict]] | None:
        """Load categorized specifications for a project"""
        try:
            cursor.execute(
                """
                SELECT phase, spec_data
                FROM categorized_specs
                WHERE project_id = ?
                ORDER BY sort_order
                """,
                (project_id,),
            )

            rows = cursor.fetchall()
            if not rows:
                return None

            specs_by_phase = {}

            for phase, spec_json in rows:
                if phase not in specs_by_phase:
                    specs_by_phase[phase] = []

                try:
                    spec = json.loads(spec_json)
                    specs_by_phase[phase].append(spec)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to decode spec: {e}")
                    continue

            if specs_by_phase:
                self.logger.debug(f"Loaded {sum(len(v) for v in specs_by_phase.values())} specs")
                return specs_by_phase

            return None

        except Exception as e:
            self.logger.error(f"Error loading specs: {e}")
            return None

    # ========================================================================
    # BACKWARD COMPATIBILITY - Stub methods pointing to V2 implementations
    # ========================================================================

    def save_note(self, note: ProjectNote) -> bool:
        """Save a project note"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO project_notes (
                    note_id, project_id, title, content, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    note.note_id,
                    note.project_id,
                    getattr(note, "title", ""),
                    note.content,
                    serialize_datetime(note.created_at),
                    serialize_datetime(datetime.now()),
                ),
            )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving note {note.note_id}: {e}")
            return False
        finally:
            conn.close()

    def get_project_notes(self, project_id: str, note_type: str | None = None) -> list[ProjectNote]:
        """Get notes for a project"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM project_notes
                WHERE project_id = ?
                ORDER BY created_at DESC
            """,
                (project_id,),
            )

            notes = []
            for row in cursor.fetchall():
                note = ProjectNote(
                    note_id=row["note_id"],
                    project_id=row["project_id"],
                    title=row["title"],
                    content=row["content"],
                    note_type="general",  # Not stored in DB
                    created_at=deserialize_datetime(row["created_at"]),
                    created_by="unknown",  # Not stored in DB
                    tags=[],  # Not stored in DB
                )
                notes.append(note)

            return notes

        except Exception as e:
            self.logger.error(f"Error getting notes for project {project_id}: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # CHAT OPERATIONS (Phase 2 - Session-based chat)
    # ========================================================================

    def save_chat_session(self, session: dict) -> None:
        """
        Save or update a chat session

        Args:
            session: Dictionary with session_id, project_id, user_id, title, created_at, updated_at, archived
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO chat_sessions (
                    session_id, project_id, user_id, title, created_at, updated_at, archived
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.get("session_id"),
                    session.get("project_id"),
                    session.get("user_id"),
                    session.get("title"),
                    session.get("created_at"),  # Already in ISO format string
                    session.get("updated_at"),  # Already in ISO format string
                    1 if session.get("archived") else 0,
                ),
            )
            conn.commit()
            self.logger.debug(f"Saved chat session {session.get('session_id')}")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving chat session: {e}")
            raise
        finally:
            conn.close()

    def load_chat_sessions(self, project_id: str, archived: bool | None = None) -> list[dict]:
        """
        Load all chat sessions for a project

        Args:
            project_id: Project ID
            archived: Optional filter (True/False/None for all)

        Returns:
            List of session dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if archived is None:
                cursor.execute(
                    "SELECT * FROM chat_sessions WHERE project_id = ? ORDER BY created_at DESC",
                    (project_id,),
                )
            else:
                cursor.execute(
                    "SELECT * FROM chat_sessions WHERE project_id = ? AND archived = ? ORDER BY created_at DESC",
                    (project_id, 1 if archived else 0),
                )

            sessions = []
            for row in cursor.fetchall():
                session = {
                    "session_id": row["session_id"],
                    "project_id": row["project_id"],
                    "user_id": row["user_id"],
                    "title": row["title"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "archived": bool(row["archived"]),
                    "message_count": self._count_session_messages(row["session_id"]),
                }
                sessions.append(session)

            return sessions
        except Exception as e:
            self.logger.error(f"Error loading chat sessions for project {project_id}: {e}")
            return []
        finally:
            conn.close()

    def get_chat_session(self, session_id: str) -> dict | None:
        """Get a single chat session by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM chat_sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "session_id": row["session_id"],
                "project_id": row["project_id"],
                "user_id": row["user_id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "archived": bool(row["archived"]),
                "message_count": self._count_session_messages(session_id),
            }
        except Exception as e:
            self.logger.error(f"Error getting chat session {session_id}: {e}")
            return None
        finally:
            conn.close()

    def archive_chat_session(self, session_id: str, archived: bool) -> None:
        """Archive or restore a chat session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now()
            cursor.execute(
                "UPDATE chat_sessions SET archived = ?, updated_at = ? WHERE session_id = ?",
                (1 if archived else 0, now.isoformat(), session_id),
            )
            conn.commit()
            self.logger.debug(f"{'Archived' if archived else 'Restored'} chat session {session_id}")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error archiving chat session: {e}")
            raise
        finally:
            conn.close()

    def delete_chat_session(self, session_id: str) -> None:
        """Delete a chat session (cascade deletes messages)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            self.logger.debug(f"Deleted chat session {session_id}")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error deleting chat session: {e}")
            raise
        finally:
            conn.close()

    def _count_session_messages(self, session_id: str) -> int:
        """Count messages in a session (helper method)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM chat_messages WHERE session_id = ?", (session_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            self.logger.warning(f"Error counting messages for session {session_id}: {e}")
            return 0
        finally:
            conn.close()

    def save_chat_message(self, message: dict) -> None:
        """
        Save a chat message

        Args:
            message: Dictionary with message_id, session_id, user_id, content, role, metadata, created_at, updated_at
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            metadata_json = json.dumps(message.get("metadata")) if message.get("metadata") else None
            cursor.execute(
                """
                INSERT OR REPLACE INTO chat_messages (
                    message_id, session_id, user_id, content, role, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.get("message_id"),
                    message.get("session_id"),
                    message.get("user_id"),
                    message.get("content"),
                    message.get("role"),
                    metadata_json,
                    message.get("created_at"),
                    message.get("updated_at"),
                ),
            )
            conn.commit()
            self.logger.debug(f"Saved chat message {message.get('message_id')}")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving chat message: {e}")
            raise
        finally:
            conn.close()

    def load_chat_messages(
        self, session_id: str, limit: int = 50, offset: int = 0, order: str = "asc"
    ) -> list[dict]:
        """
        Load messages for a session with pagination

        Args:
            session_id: Session ID
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            order: 'asc' or 'desc' for message ordering

        Returns:
            List of message dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            order_by = "ASC" if order == "asc" else "DESC"
            cursor.execute(
                f"""
                SELECT * FROM chat_messages
                WHERE session_id = ?
                ORDER BY created_at {order_by}
                LIMIT ? OFFSET ?
                """,  # nosec B608
                (session_id, limit, offset),
            )

            messages = []
            for row in cursor.fetchall():
                message = {
                    "message_id": row["message_id"],
                    "session_id": row["session_id"],
                    "user_id": row["user_id"],
                    "content": row["content"],
                    "role": row["role"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                messages.append(message)

            return messages
        except Exception as e:
            self.logger.error(f"Error loading chat messages for session {session_id}: {e}")
            return []
        finally:
            conn.close()

    def get_chat_message(self, message_id: str) -> dict | None:
        """Get a single chat message by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM chat_messages WHERE message_id = ?", (message_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "message_id": row["message_id"],
                "session_id": row["session_id"],
                "user_id": row["user_id"],
                "content": row["content"],
                "role": row["role"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        except Exception as e:
            self.logger.error(f"Error getting chat message {message_id}: {e}")
            return None
        finally:
            conn.close()

    def update_chat_message(
        self, message_id: str, content: str, metadata: dict | None = None
    ) -> None:
        """Update a chat message's content and metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now()
            metadata_json = json.dumps(metadata) if metadata else None
            cursor.execute(
                """
                UPDATE chat_messages
                SET content = ?, metadata = ?, updated_at = ?
                WHERE message_id = ?
                """,
                (content, metadata_json, now.isoformat(), message_id),
            )
            conn.commit()
            self.logger.debug(f"Updated chat message {message_id}")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error updating chat message: {e}")
            raise
        finally:
            conn.close()

    def delete_chat_message(self, message_id: str) -> None:
        """Delete a chat message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM chat_messages WHERE message_id = ?", (message_id,))
            conn.commit()
            self.logger.debug(f"Deleted chat message {message_id}")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error deleting chat message: {e}")
            raise
        finally:
            conn.close()

    def get_session_message_count(self, session_id: str) -> int:
        """Get total message count for a session"""
        return self._count_session_messages(session_id)

    # ========================================================================
    # Collaboration Invitation Methods
    # ========================================================================

    def save_invitation(self, invitation: dict) -> None:
        """Save or update a collaboration invitation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO collaboration_invitations
                (id, project_id, inviter_id, invitee_email, role, token, status, created_at, expires_at, accepted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invitation.get("id"),
                    invitation.get("project_id"),
                    invitation.get("inviter_id"),
                    invitation.get("invitee_email"),
                    invitation.get("role"),
                    invitation.get("token"),
                    invitation.get("status", "pending"),
                    invitation.get("created_at"),
                    invitation.get("expires_at"),
                    invitation.get("accepted_at"),
                ),
            )
            conn.commit()
            self.logger.debug(f"Saved invitation {invitation.get('id')}")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving invitation: {e}")
            raise
        finally:
            conn.close()

    def get_invitation_by_token(self, token: str) -> dict | None:
        """Get invitation by token"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM collaboration_invitations WHERE token = ?", (token,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "id": row["id"],
                "project_id": row["project_id"],
                "inviter_id": row["inviter_id"],
                "invitee_email": row["invitee_email"],
                "role": row["role"],
                "token": row["token"],
                "status": row["status"],
                "created_at": row["created_at"],
                "expires_at": row["expires_at"],
                "accepted_at": row["accepted_at"],
            }
        except Exception as e:
            self.logger.error(f"Error getting invitation by token: {e}")
            return None
        finally:
            conn.close()

    def get_project_invitations(self, project_id: str, status: str | None = None) -> list[dict]:
        """Get invitations for a project, optionally filtered by status"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if status:
                cursor.execute(
                    "SELECT * FROM collaboration_invitations WHERE project_id = ? AND status = ? ORDER BY created_at DESC",
                    (project_id, status),
                )
            else:
                cursor.execute(
                    "SELECT * FROM collaboration_invitations WHERE project_id = ? ORDER BY created_at DESC",
                    (project_id,),
                )

            invitations = []
            for row in cursor.fetchall():
                invitations.append(
                    {
                        "id": row["id"],
                        "project_id": row["project_id"],
                        "inviter_id": row["inviter_id"],
                        "invitee_email": row["invitee_email"],
                        "role": row["role"],
                        "token": row["token"],
                        "status": row["status"],
                        "created_at": row["created_at"],
                        "expires_at": row["expires_at"],
                        "accepted_at": row["accepted_at"],
                    }
                )

            return invitations
        except Exception as e:
            self.logger.error(f"Error getting project invitations for {project_id}: {e}")
            return []
        finally:
            conn.close()

    def get_user_invitations(self, email: str, status: str | None = None) -> list[dict]:
        """Get invitations for a user by email, optionally filtered by status"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if status:
                cursor.execute(
                    "SELECT * FROM collaboration_invitations WHERE invitee_email = ? AND status = ? ORDER BY created_at DESC",
                    (email, status),
                )
            else:
                cursor.execute(
                    "SELECT * FROM collaboration_invitations WHERE invitee_email = ? ORDER BY created_at DESC",
                    (email,),
                )

            invitations = []
            for row in cursor.fetchall():
                invitations.append(
                    {
                        "id": row["id"],
                        "project_id": row["project_id"],
                        "inviter_id": row["inviter_id"],
                        "invitee_email": row["invitee_email"],
                        "role": row["role"],
                        "token": row["token"],
                        "status": row["status"],
                        "created_at": row["created_at"],
                        "expires_at": row["expires_at"],
                        "accepted_at": row["accepted_at"],
                    }
                )

            return invitations
        except Exception as e:
            self.logger.error(f"Error getting invitations for {email}: {e}")
            return []
        finally:
            conn.close()

    def accept_invitation(self, invitation_id: str) -> None:
        """Accept an invitation and mark it as accepted"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now()
            cursor.execute(
                """
                UPDATE collaboration_invitations
                SET status = ?, accepted_at = ?
                WHERE id = ?
                """,
                ("accepted", now.isoformat(), invitation_id),
            )
            conn.commit()
            self.logger.debug(f"Accepted invitation {invitation_id}")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error accepting invitation: {e}")
            raise
        finally:
            conn.close()

    def delete_invitation(self, invitation_id: str) -> None:
        """Delete/cancel an invitation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM collaboration_invitations WHERE id = ?", (invitation_id,))
            conn.commit()
            self.logger.debug(f"Deleted invitation {invitation_id}")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error deleting invitation: {e}")
            raise
        finally:
            conn.close()

    # ========================================================================
    # Collaboration Activity Methods
    # ========================================================================

    def save_activity(self, activity: dict) -> None:
        """Save a collaboration activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            activity_data_json = (
                json.dumps(activity.get("activity_data")) if activity.get("activity_data") else None
            )
            cursor.execute(
                """
                INSERT INTO collaboration_activities
                (id, project_id, user_id, activity_type, activity_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    activity.get("id"),
                    activity.get("project_id"),
                    activity.get("user_id"),
                    activity.get("activity_type"),
                    activity_data_json,
                    activity.get("created_at"),
                ),
            )
            conn.commit()
            self.logger.debug(f"Saved activity {activity.get('id')}")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error saving activity: {e}")
            raise
        finally:
            conn.close()

    def get_project_activities(
        self, project_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        """Get activities for a project with pagination"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM collaboration_activities
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (project_id, limit, offset),
            )

            activities = []
            for row in cursor.fetchall():
                activities.append(
                    {
                        "id": row["id"],
                        "project_id": row["project_id"],
                        "user_id": row["user_id"],
                        "activity_type": row["activity_type"],
                        "activity_data": (
                            json.loads(row["activity_data"]) if row["activity_data"] else None
                        ),
                        "created_at": row["created_at"],
                    }
                )

            return activities
        except Exception as e:
            self.logger.error(f"Error getting project activities for {project_id}: {e}")
            return []
        finally:
            conn.close()

    def count_project_activities(self, project_id: str) -> int:
        """Count total activities for a project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT COUNT(*) as count FROM collaboration_activities WHERE project_id = ?",
                (project_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else 0
        except Exception as e:
            self.logger.error(f"Error counting activities for {project_id}: {e}")
            return 0
        finally:
            conn.close()

    # ========================================================================
    # GitHub Sponsors / Sponsorship Methods
    # ========================================================================

    def create_sponsorship(self, sponsorship_data: dict) -> int:
        """Create or update a sponsorship record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO sponsorships (
                    username, github_username, github_sponsor_id, sponsorship_amount,
                    socrates_tier_granted, sponsorship_status, sponsored_at, tier_expires_at,
                    last_payment_at, payment_id, webhook_event_id, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    sponsorship_data.get("username"),
                    sponsorship_data.get("github_username"),
                    sponsorship_data.get("github_sponsor_id"),
                    sponsorship_data.get("sponsorship_amount", 0),
                    sponsorship_data.get("socrates_tier_granted", ""),
                    sponsorship_data.get("sponsorship_status", "active"),
                    sponsorship_data.get("sponsored_at"),
                    sponsorship_data.get("tier_expires_at"),
                    sponsorship_data.get("last_payment_at"),
                    sponsorship_data.get("payment_id", ""),
                    sponsorship_data.get("webhook_event_id", ""),
                    sponsorship_data.get("notes", ""),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error creating sponsorship: {e}")
            raise
        finally:
            conn.close()

    def get_active_sponsorship(self, username: str) -> dict | None:
        """Get active sponsorship for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM sponsorships
                WHERE username = ? AND sponsorship_status = 'active'
                AND (tier_expires_at IS NULL OR tier_expires_at > datetime('now'))
                ORDER BY sponsored_at DESC
                LIMIT 1
            """,
                (username,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Error getting active sponsorship for {username}: {e}")
            return None
        finally:
            conn.close()

    def get_sponsorship_history(self, username: str) -> list:
        """Get all sponsorships for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM sponsorships
                WHERE username = ?
                ORDER BY sponsored_at DESC
            """,
                (username,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting sponsorship history for {username}: {e}")
            return []
        finally:
            conn.close()

    def get_sponsorship_by_github_username(self, github_username: str) -> dict | None:
        """Get sponsorship by GitHub username"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM sponsorships
                WHERE github_username = ?
                AND sponsorship_status = 'active'
                AND (tier_expires_at IS NULL OR tier_expires_at > datetime('now'))
                ORDER BY sponsored_at DESC
                LIMIT 1
            """,
                (github_username,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Error getting sponsorship for {github_username}: {e}")
            return None
        finally:
            conn.close()

    def cancel_sponsorship(self, username: str) -> bool:
        """Cancel active sponsorship for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE sponsorships
                SET sponsorship_status = 'cancelled'
                WHERE username = ? AND sponsorship_status = 'active'
            """,
                (username,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error cancelling sponsorship for {username}: {e}")
            return False
        finally:
            conn.close()

    def get_all_sponsorships(self) -> list:
        """Get all sponsorships (admin/dashboard use)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM sponsorships
                ORDER BY sponsored_at DESC
            """
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting all sponsorships: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # Payment History & Tracking Methods
    # ========================================================================

    def record_payment(self, payment_data: dict) -> int:
        """Record a sponsorship payment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO sponsorship_payments (
                    sponsorship_id, username, amount, currency, payment_status,
                    payment_date, payment_id, payment_method_id, reference_id, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    payment_data.get("sponsorship_id"),
                    payment_data.get("username"),
                    payment_data.get("amount", 0),
                    payment_data.get("currency", "USD"),
                    payment_data.get("payment_status", "pending"),
                    payment_data.get("payment_date"),
                    payment_data.get("payment_id", ""),
                    payment_data.get("payment_method_id"),
                    payment_data.get("reference_id", ""),
                    payment_data.get("notes", ""),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error recording payment: {e}")
            raise
        finally:
            conn.close()

    def get_payment_history(self, username: str, limit: int = 50) -> list:
        """Get payment history for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM sponsorship_payments
                WHERE username = ?
                ORDER BY payment_date DESC
                LIMIT ?
            """,
                (username, limit),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting payment history for {username}: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # Refund Tracking Methods
    # ========================================================================

    def record_refund(self, refund_data: dict) -> int:
        """Record a sponsorship refund"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO sponsorship_refunds (
                    payment_id, sponsorship_id, username, refund_amount,
                    refund_status, refund_reason, refund_date, processed_date,
                    refund_id, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    refund_data.get("payment_id"),
                    refund_data.get("sponsorship_id"),
                    refund_data.get("username"),
                    refund_data.get("refund_amount", 0),
                    refund_data.get("refund_status", "pending"),
                    refund_data.get("refund_reason", "user_request"),
                    refund_data.get("refund_date"),
                    refund_data.get("processed_date"),
                    refund_data.get("refund_id", ""),
                    refund_data.get("notes", ""),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error recording refund: {e}")
            raise
        finally:
            conn.close()

    def get_refund_history(self, username: str, limit: int = 50) -> list:
        """Get refund history for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM sponsorship_refunds
                WHERE username = ?
                ORDER BY refund_date DESC
                LIMIT ?
            """,
                (username, limit),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting refund history for {username}: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # Payment Method Tracking Methods
    # ========================================================================

    def add_payment_method(self, method_data: dict) -> int:
        """Add a payment method for a sponsorship"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO sponsorship_payment_methods (
                    sponsorship_id, username, payment_method_type, last_four,
                    card_brand, expiry_date, is_default, is_expired, added_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    method_data.get("sponsorship_id"),
                    method_data.get("username"),
                    method_data.get("payment_method_type"),
                    method_data.get("last_four", ""),
                    method_data.get("card_brand", ""),
                    method_data.get("expiry_date", ""),
                    method_data.get("is_default", 0),
                    method_data.get("is_expired", 0),
                    method_data.get("added_at"),
                    method_data.get("notes", ""),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error adding payment method: {e}")
            raise
        finally:
            conn.close()

    def get_payment_methods(self, sponsorship_id: int) -> list:
        """Get all payment methods for a sponsorship"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM sponsorship_payment_methods
                WHERE sponsorship_id = ?
                ORDER BY is_default DESC, added_at DESC
            """,
                (sponsorship_id,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting payment methods: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # Tier Change Tracking Methods
    # ========================================================================

    def record_tier_change(self, change_data: dict) -> int:
        """Record a sponsorship tier change (upgrade, downgrade, renewal, etc.)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO sponsorship_tier_changes (
                    sponsorship_id, username, change_type, old_tier, new_tier,
                    old_amount, new_amount, change_reason, change_date,
                    effective_date, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    change_data.get("sponsorship_id"),
                    change_data.get("username"),
                    change_data.get("change_type"),
                    change_data.get("old_tier"),
                    change_data.get("new_tier"),
                    change_data.get("old_amount"),
                    change_data.get("new_amount"),
                    change_data.get("change_reason", ""),
                    change_data.get("change_date"),
                    change_data.get("effective_date"),
                    change_data.get("notes", ""),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error recording tier change: {e}")
            raise
        finally:
            conn.close()

    def get_tier_change_history(self, username: str, limit: int = 50) -> list:
        """Get tier change history for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM sponsorship_tier_changes
                WHERE username = ?
                ORDER BY change_date DESC
                LIMIT ?
            """,
                (username, limit),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting tier change history for {username}: {e}")
            return []
        finally:
            conn.close()

    # ========================================================================
    # Sponsorship Analytics Methods
    # ========================================================================

    def get_sponsorship_analytics(self, username: str) -> dict:
        """Get comprehensive sponsorship analytics for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Get current sponsorship
            cursor.execute(
                "SELECT * FROM sponsorships WHERE username = ? AND sponsorship_status = 'active'",
                (username,),
            )
            sponsorship = dict(cursor.fetchone() or {})

            # Get payment stats
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_payments,
                    SUM(amount) as total_paid,
                    SUM(CASE WHEN payment_status = 'succeeded' THEN amount ELSE 0 END) as total_successful,
                    SUM(CASE WHEN payment_status = 'failed' THEN 1 ELSE 0 END) as failed_payments
                FROM sponsorship_payments WHERE username = ?
            """,
                (username,),
            )
            payment_stats = dict(cursor.fetchone() or {})

            # Get refund stats
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_refunds,
                    SUM(refund_amount) as total_refunded
                FROM sponsorship_refunds WHERE username = ? AND refund_status = 'completed'
            """,
                (username,),
            )
            refund_stats = dict(cursor.fetchone() or {})

            # Get tier changes
            cursor.execute(
                """
                SELECT change_type, COUNT(*) as count
                FROM sponsorship_tier_changes WHERE username = ?
                GROUP BY change_type
            """,
                (username,),
            )
            tier_changes = {row["change_type"]: row["count"] for row in cursor.fetchall()}

            return {
                "sponsorship": sponsorship,
                "payments": payment_stats,
                "refunds": refund_stats,
                "tier_changes": tier_changes,
                "net_revenue": (payment_stats.get("total_successful", 0) or 0)
                - (refund_stats.get("total_refunded", 0) or 0),
            }

        except Exception as e:
            self.logger.error(f"Error getting sponsorship analytics for {username}: {e}")
            return {}
        finally:
            conn.close()
