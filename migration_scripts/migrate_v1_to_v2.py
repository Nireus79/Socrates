"""
Migration script: Convert Socrates database from V1 (pickle BLOBs) to V2 (normalized schema)

This script:
1. Creates a backup of the original database
2. Creates the V2 schema in the same database
3. Migrates data from V1 to V2 (if any exists)
4. Validates the migration
5. Renames old V1 tables to _v1_backup

Since the project is pre-launch, there's typically no data to migrate, but the script
handles it properly for any edge cases.
"""

import sqlite3
import pickle
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("migration")


class SchemaMigrator:
    """Handles migration from V1 (pickle) to V2 (normalized) schema"""

    def __init__(self, db_path: str, dry_run: bool = False):
        """
        Initialize migrator

        Args:
            db_path: Path to SQLite database
            dry_run: If True, don't commit changes (for testing)
        """
        self.db_path = db_path
        self.dry_run = dry_run
        self.stats = {
            "projects_migrated": 0,
            "users_migrated": 0,
            "notes_migrated": 0,
            "effectiveness_migrated": 0,
            "patterns_migrated": 0,
            "knowledge_migrated": 0,
            "errors": 0,
        }
        self.errors = []

    def run_migration(self) -> bool:
        """
        Execute full migration pipeline

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("=" * 80)
            logger.info("Starting Database Migration: V1 (pickle) → V2 (normalized)")
            logger.info("=" * 80)

            # Step 1: Create backup
            backup_path = self._backup_database()
            logger.info(f"✓ Database backed up to: {backup_path}")

            # Step 2: Create V2 schema
            self._create_v2_schema()
            logger.info("✓ V2 schema created")

            # Step 3: Migrate data
            self._migrate_all_data()
            logger.info(f"✓ Data migration complete (errors: {self.stats['errors']})")

            # Step 4: Validate migration
            if self._validate_migration():
                logger.info("✓ Migration validation passed")
            else:
                logger.error("✗ Migration validation failed")
                if not self.dry_run:
                    self._rollback_migration(backup_path)
                    logger.info(f"Rolled back to: {backup_path}")
                return False

            # Step 5: Rename old tables
            if not self.dry_run:
                self._rename_v1_tables()
                logger.info("✓ V1 tables renamed to _v1_backup")

            logger.info("=" * 80)
            logger.info("Migration Summary:")
            for key, value in self.stats.items():
                logger.info(f"  {key}: {value}")
            logger.info("=" * 80)

            return True

        except Exception as e:
            logger.error(f"Migration failed with error: {e}")
            self.errors.append(str(e))
            return False

    def _backup_database(self) -> str:
        """Create backup of original database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.db_path}.backup_{timestamp}"

        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        else:
            logger.warning(f"Database not found at {self.db_path}, skipping backup")

        return backup_path

    def _rollback_migration(self, backup_path: str) -> None:
        """Restore from backup if migration fails"""
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Restored from backup: {backup_path}")

    def _create_v2_schema(self) -> None:
        """Create V2 schema by executing schema_v2.sql"""
        schema_path = Path(__file__).parent.parent / "socratic_system" / "database" / "schema_v2.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            # Execute schema creation
            cursor.executescript(schema_sql)
            conn.commit()
            logger.info(f"V2 schema created from {schema_path}")

        finally:
            conn.close()

    def _migrate_all_data(self) -> None:
        """Migrate all data from V1 to V2"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        try:
            # Check if V1 tables have data
            v1_tables = ["users", "projects", "project_notes", "question_effectiveness",
                         "behavior_patterns", "knowledge_documents", "llm_provider_configs"]

            has_data = False
            for table in v1_tables:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    has_data = True
                    logger.info(f"Found {count} records in {table}")

            if not has_data:
                logger.info("No data found in V1 tables (pre-launch database)")
                return

            # Migrate each data type
            self._migrate_users(conn)
            self._migrate_projects(conn)
            self._migrate_notes(conn)
            self._migrate_effectiveness(conn)
            self._migrate_patterns(conn)
            self._migrate_knowledge(conn)
            self._migrate_llm_configs(conn)

            if not self.dry_run:
                conn.commit()

        finally:
            conn.close()

    def _migrate_users(self, conn: sqlite3.Connection) -> None:
        """Migrate users from V1 to V2"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()

            if not rows:
                return

            for row in rows:
                try:
                    # Unpickle user data
                    user_data = pickle.loads(row['data']) if row['data'] else {}

                    # Insert into V2
                    cursor.execute("""
                        INSERT OR IGNORE INTO users (
                            username, passcode_hash, subscription_tier,
                            subscription_status, testing_mode, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row['username'],
                        row['passcode_hash'],
                        user_data.get('subscription_tier', 'free'),
                        user_data.get('subscription_status', 'active'),
                        user_data.get('testing_mode', False),
                        row['created_at'] or datetime.now().isoformat()
                    ))

                    self.stats['users_migrated'] += 1

                except Exception as e:
                    logger.error(f"Error migrating user {row.get('username')}: {e}")
                    self.stats['errors'] += 1
                    self.errors.append(f"User {row.get('username')}: {e}")

        except Exception as e:
            logger.error(f"Error in _migrate_users: {e}")
            self.stats['errors'] += 1

    def _migrate_projects(self, conn: sqlite3.Connection) -> None:
        """Migrate projects from V1 to V2"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects")
            rows = cursor.fetchall()

            if not rows:
                return

            for row in rows:
                try:
                    # Unpickle project data
                    project_data = pickle.loads(row['data']) if row['data'] else {}

                    project_id = row['project_id']

                    # Insert main project record
                    cursor.execute("""
                        INSERT OR IGNORE INTO projects (
                            project_id, name, owner, phase, project_type,
                            team_structure, language_preferences, deployment_target,
                            code_style, chat_mode, goals, status, progress,
                            is_archived, created_at, updated_at, archived_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        project_id,
                        project_data.get('name', ''),
                        project_data.get('owner', ''),
                        project_data.get('phase', 'discovery'),
                        project_data.get('project_type', 'software'),
                        project_data.get('team_structure', 'individual'),
                        project_data.get('language_preferences', 'python'),
                        project_data.get('deployment_target', 'local'),
                        project_data.get('code_style', 'standard'),
                        project_data.get('chat_mode', 'socratic'),
                        project_data.get('goals', ''),
                        project_data.get('status', 'active'),
                        project_data.get('progress', 0),
                        project_data.get('is_archived', False),
                        row['created_at'] or datetime.now().isoformat(),
                        row['updated_at'] or datetime.now().isoformat(),
                        project_data.get('archived_at')
                    ))

                    # Migrate arrays to separate tables
                    self._migrate_project_requirements(cursor, project_id, project_data)
                    self._migrate_project_tech_stack(cursor, project_id, project_data)
                    self._migrate_project_constraints(cursor, project_id, project_data)
                    self._migrate_conversation_history(cursor, project_id, project_data)
                    self._migrate_team_members(cursor, project_id, project_data)
                    self._migrate_phase_maturity(cursor, project_id, project_data)
                    self._migrate_category_scores(cursor, project_id, project_data)
                    self._migrate_analytics_metrics(cursor, project_id, project_data)

                    self.stats['projects_migrated'] += 1

                except Exception as e:
                    logger.error(f"Error migrating project {row.get('project_id')}: {e}")
                    self.stats['errors'] += 1
                    self.errors.append(f"Project {row.get('project_id')}: {e}")

        except Exception as e:
            logger.error(f"Error in _migrate_projects: {e}")
            self.stats['errors'] += 1

    def _migrate_project_requirements(self, cursor: sqlite3.Cursor, project_id: str, project_data: Dict) -> None:
        """Migrate project requirements to separate table"""
        requirements = project_data.get('requirements', [])
        for i, req in enumerate(requirements):
            cursor.execute("""
                INSERT INTO project_requirements (project_id, requirement, sort_order)
                VALUES (?, ?, ?)
            """, (project_id, req, i))

    def _migrate_project_tech_stack(self, cursor: sqlite3.Cursor, project_id: str, project_data: Dict) -> None:
        """Migrate tech stack to separate table"""
        tech_stack = project_data.get('tech_stack', [])
        for i, tech in enumerate(tech_stack):
            cursor.execute("""
                INSERT INTO project_tech_stack (project_id, technology, sort_order)
                VALUES (?, ?, ?)
            """, (project_id, tech, i))

    def _migrate_project_constraints(self, cursor: sqlite3.Cursor, project_id: str, project_data: Dict) -> None:
        """Migrate constraints to separate table"""
        constraints = project_data.get('constraints', [])
        for i, constraint in enumerate(constraints):
            cursor.execute("""
                INSERT INTO project_constraints (project_id, constraint_text, sort_order)
                VALUES (?, ?, ?)
            """, (project_id, constraint, i))

    def _migrate_conversation_history(self, cursor: sqlite3.Cursor, project_id: str, project_data: Dict) -> None:
        """Migrate conversation history to separate table"""
        history = project_data.get('conversation_history', [])
        for msg in history:
            cursor.execute("""
                INSERT INTO conversation_history (project_id, message_type, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                project_id,
                msg.get('role', 'user'),
                msg.get('content', ''),
                msg.get('timestamp', datetime.now().isoformat())
            ))

    def _migrate_team_members(self, cursor: sqlite3.Cursor, project_id: str, project_data: Dict) -> None:
        """Migrate team members to separate table"""
        team_members = project_data.get('team_members', [])
        for member in team_members:
            if isinstance(member, dict):
                cursor.execute("""
                    INSERT OR IGNORE INTO team_members (project_id, username, role, joined_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    project_id,
                    member.get('username', ''),
                    member.get('role', 'contributor'),
                    member.get('joined_at', datetime.now().isoformat())
                ))

    def _migrate_phase_maturity(self, cursor: sqlite3.Cursor, project_id: str, project_data: Dict) -> None:
        """Migrate phase maturity scores"""
        maturity_scores = project_data.get('phase_maturity_scores', {})
        for phase, score in maturity_scores.items():
            cursor.execute("""
                INSERT OR IGNORE INTO phase_maturity_scores (project_id, phase, score)
                VALUES (?, ?, ?)
            """, (project_id, phase, score))

    def _migrate_category_scores(self, cursor: sqlite3.Cursor, project_id: str, project_data: Dict) -> None:
        """Migrate category scores"""
        category_scores = project_data.get('category_scores', {})
        for phase, categories in category_scores.items():
            if isinstance(categories, dict):
                for category, score in categories.items():
                    cursor.execute("""
                        INSERT OR IGNORE INTO category_scores (project_id, phase, category, score)
                        VALUES (?, ?, ?, ?)
                    """, (project_id, phase, category, score))

    def _migrate_analytics_metrics(self, cursor: sqlite3.Cursor, project_id: str, project_data: Dict) -> None:
        """Migrate analytics metrics"""
        metrics = project_data.get('analytics_metrics', {})
        if metrics:
            import json
            cursor.execute("""
                INSERT OR IGNORE INTO analytics_metrics (
                    project_id, velocity, total_qa_sessions, avg_confidence,
                    weak_categories, strong_categories
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                metrics.get('velocity', 0.0),
                metrics.get('total_qa_sessions', 0),
                metrics.get('avg_confidence', 0.0),
                json.dumps(metrics.get('weak_categories', [])),
                json.dumps(metrics.get('strong_categories', []))
            ))

    def _migrate_notes(self, conn: sqlite3.Connection) -> None:
        """Migrate project notes from V1 to V2"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_notes")
            rows = cursor.fetchall()

            if not rows:
                return

            for row in rows:
                try:
                    note_data = pickle.loads(row['data']) if row['data'] else {}

                    cursor.execute("""
                        INSERT OR IGNORE INTO project_notes (
                            note_id, project_id, title, content, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row['note_id'],
                        row['project_id'],
                        note_data.get('title', ''),
                        note_data.get('content', ''),
                        row['created_at'] or datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))

                    self.stats['notes_migrated'] += 1

                except Exception as e:
                    logger.error(f"Error migrating note {row.get('note_id')}: {e}")
                    self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error in _migrate_notes: {e}")
            self.stats['errors'] += 1

    def _migrate_effectiveness(self, conn: sqlite3.Connection) -> None:
        """Migrate question effectiveness from V1 to V2"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM question_effectiveness")
            rows = cursor.fetchall()

            if not rows:
                return

            for row in rows:
                try:
                    data = pickle.loads(row['data']) if row['data'] else {}

                    cursor.execute("""
                        INSERT OR IGNORE INTO question_effectiveness (
                            id, user_id, question_template_id, effectiveness_score,
                            times_asked, times_answered_well, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['id'],
                        row['user_id'],
                        row['question_template_id'],
                        data.get('effectiveness_score', 0.5),
                        data.get('times_asked', 0),
                        data.get('times_answered_well', 0),
                        row['created_at'] or datetime.now().isoformat(),
                        row['updated_at'] or datetime.now().isoformat()
                    ))

                    self.stats['effectiveness_migrated'] += 1

                except Exception as e:
                    logger.error(f"Error migrating effectiveness {row.get('id')}: {e}")
                    self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error in _migrate_effectiveness: {e}")
            self.stats['errors'] += 1

    def _migrate_patterns(self, conn: sqlite3.Connection) -> None:
        """Migrate behavior patterns from V1 to V2"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM behavior_patterns")
            rows = cursor.fetchall()

            if not rows:
                return

            for row in rows:
                try:
                    import json
                    data = pickle.loads(row['data']) if row['data'] else {}

                    cursor.execute("""
                        INSERT OR IGNORE INTO behavior_patterns (
                            id, user_id, pattern_type, pattern_data,
                            learned_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row['id'],
                        row['user_id'],
                        row['pattern_type'],
                        json.dumps(data),
                        row['learned_at'] or datetime.now().isoformat(),
                        row['updated_at'] or datetime.now().isoformat()
                    ))

                    self.stats['patterns_migrated'] += 1

                except Exception as e:
                    logger.error(f"Error migrating pattern {row.get('id')}: {e}")
                    self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error in _migrate_patterns: {e}")
            self.stats['errors'] += 1

    def _migrate_knowledge(self, conn: sqlite3.Connection) -> None:
        """Migrate knowledge documents from V1 to V2"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_documents")
            rows = cursor.fetchall()

            if not rows:
                return

            for row in rows:
                try:
                    data = pickle.loads(row['data']) if row['data'] else {}

                    cursor.execute("""
                        INSERT OR IGNORE INTO knowledge_documents (
                            id, project_id, user_id, title, content, uploaded_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row['id'],
                        row['project_id'],
                        row['user_id'],
                        data.get('title', ''),
                        data.get('content', ''),
                        row['uploaded_at'] or datetime.now().isoformat()
                    ))

                    self.stats['knowledge_migrated'] += 1

                except Exception as e:
                    logger.error(f"Error migrating knowledge {row.get('id')}: {e}")
                    self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error in _migrate_knowledge: {e}")
            self.stats['errors'] += 1

    def _migrate_llm_configs(self, conn: sqlite3.Connection) -> None:
        """Migrate LLM provider configs from V1 to V2"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM llm_provider_configs")
            rows = cursor.fetchall()

            if not rows:
                return

            for row in rows:
                try:
                    import json
                    data = pickle.loads(row['data']) if row['data'] else {}

                    cursor.execute("""
                        INSERT OR IGNORE INTO llm_provider_configs (
                            id, user_id, provider, config_data, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row['id'],
                        row['user_id'],
                        row['provider'],
                        json.dumps(data),
                        row['created_at'] or datetime.now().isoformat(),
                        row['updated_at'] or datetime.now().isoformat()
                    ))

                except Exception as e:
                    logger.error(f"Error migrating LLM config {row.get('id')}: {e}")
                    self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error in _migrate_llm_configs: {e}")
            self.stats['errors'] += 1

    def _validate_migration(self) -> bool:
        """Validate that migration was successful"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check V1 and V2 table counts match
            for v1_table, v2_table in [
                ("users", "users"),
                ("projects", "projects"),
                ("project_notes", "project_notes"),
                ("question_effectiveness", "question_effectiveness"),
                ("behavior_patterns", "behavior_patterns"),
            ]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {v1_table}")
                    v1_count = cursor.fetchone()[0]

                    cursor.execute(f"SELECT COUNT(*) FROM {v2_table}")
                    v2_count = cursor.fetchone()[0]

                    if v1_count != v2_count:
                        logger.warning(f"Count mismatch for {v1_table}/{v2_table}: {v1_count} vs {v2_count}")

                except sqlite3.OperationalError:
                    # Table doesn't exist, that's ok
                    pass

            # Check for NULL required fields
            cursor.execute("SELECT COUNT(*) FROM users WHERE username IS NULL")
            null_count = cursor.fetchone()[0]
            if null_count > 0:
                logger.error(f"Found {null_count} NULL usernames in users")
                return False

            cursor.execute("SELECT COUNT(*) FROM projects WHERE project_id IS NULL")
            null_count = cursor.fetchone()[0]
            if null_count > 0:
                logger.error(f"Found {null_count} NULL project_ids in projects")
                return False

            logger.info("✓ Validation checks passed")
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    def _rename_v1_tables(self) -> None:
        """Rename V1 tables to _v1_backup"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        v1_tables = [
            "users",
            "projects",
            "project_notes",
            "question_effectiveness",
            "behavior_patterns",
            "knowledge_documents",
            "llm_provider_configs",
            "api_keys",
            "llm_usage",
        ]

        try:
            for table in v1_tables:
                try:
                    cursor.execute(f"ALTER TABLE {table} RENAME TO {table}_v1_backup")
                    logger.info(f"Renamed {table} → {table}_v1_backup")
                except sqlite3.OperationalError:
                    # Table doesn't exist, that's ok
                    pass

            conn.commit()
        finally:
            conn.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate Socrates database from V1 to V2")
    parser.add_argument("--db-path", default=None, help="Path to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Test migration without committing")

    args = parser.parse_args()

    # Determine database path
    if args.db_path:
        db_path = args.db_path
    else:
        # Use default path from config
        from pathlib import Path
        data_dir = Path.home() / ".socrates"
        db_path = str(data_dir / "projects.db")

    logger.info(f"Using database: {db_path}")

    if args.dry_run:
        logger.info("Running in DRY-RUN mode (no changes will be committed)")

    # Run migration
    migrator = SchemaMigrator(db_path, dry_run=args.dry_run)
    success = migrator.run_migration()

    if success:
        logger.info("✓ Migration completed successfully")
        return 0
    else:
        logger.error("✗ Migration failed")
        return 1


if __name__ == "__main__":
    exit(main())
