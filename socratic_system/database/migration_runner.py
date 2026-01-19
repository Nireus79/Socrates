"""
Database Migration Runner - Applies SQL migrations to initialize/upgrade database schema

Handles:
- Running SQL migration scripts
- Checking if tables exist
- Safe migration execution with error handling
"""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger("socrates.database.migrations")


class MigrationRunner:
    """Runs SQL migration scripts to set up and upgrade database schema"""

    def __init__(self, db_path: str):
        """
        Initialize migration runner

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        # Try archive directory first (preferred location), fall back to root migration_scripts
        archive_dir = Path(__file__).parent.parent.parent / "archive" / "migration_scripts"
        root_dir = Path(__file__).parent.parent.parent / "migration_scripts"
        self.migration_dir = archive_dir if archive_dir.exists() else root_dir
        self.logger = logging.getLogger("socrates.database.migrations")

    def apply_migration(self, migration_file: str) -> Tuple[bool, str]:
        """
        Apply a SQL migration script to the database

        Args:
            migration_file: Name of migration file (e.g., "add_github_import_tables.sql")

        Returns:
            Tuple of (success: bool, message: str)
        """
        migration_path = self.migration_dir / migration_file

        if not migration_path.exists():
            msg = f"Migration file not found: {migration_path}"
            self.logger.error(msg)
            return False, msg

        try:
            with open(migration_path) as f:
                sql_script = f.read()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Execute all statements in the migration file
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in sql_script.split(";") if s.strip()]

            for statement in statements:
                self.logger.debug(f"Executing: {statement[:50]}...")
                cursor.execute(statement)

            conn.commit()
            conn.close()

            msg = f"Successfully applied migration: {migration_file}"
            self.logger.info(msg)
            return True, msg

        except sqlite3.DatabaseError as e:
            msg = f"Database error applying migration {migration_file}: {str(e)}"
            self.logger.error(msg)
            return False, msg

        except Exception as e:
            msg = f"Error applying migration {migration_file}: {str(e)}"
            self.logger.error(msg)
            return False, msg

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
                """,
                (table_name,),
            )

            result = cursor.fetchone() is not None
            conn.close()

            return result

        except Exception as e:
            self.logger.error(f"Error checking if table exists: {str(e)}")
            return False

    def get_existing_tables(self) -> List[str]:
        """
        Get list of all existing tables in database

        Returns:
            List of table names
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
                """
            )

            tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            return tables

        except Exception as e:
            self.logger.error(f"Error getting existing tables: {str(e)}")
            return []

    def check_migration_status(self) -> Dict[str, bool]:
        """
        Check status of all required migrations

        Returns:
            Dictionary with migration name as key and completion status as value
        """
        # Check for GitHub import tables
        github_tables_exist = (
            self.table_exists("project_files")
            and self.table_exists("repository_metadata")
            and self.table_exists("code_validation_results")
        )

        # Check for claude_auth_method column in users table
        users_column_exists = self._column_exists("users", "claude_auth_method")

        status = {
            "github_import_tables": github_tables_exist,
            "users_claude_auth_method": users_column_exists,
        }

        return status

    def _column_exists(self, table_name: str, column_name: str) -> bool:
        """
        Check if a column exists in a table

        Args:
            table_name: Name of the table
            column_name: Name of the column

        Returns:
            True if column exists, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Use PRAGMA table_info to get column information
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            conn.close()

            # columns is a list of tuples: (cid, name, type, notnull, dflt_value, pk)
            column_names = [col[1] for col in columns]
            return column_name in column_names

        except Exception as e:
            self.logger.error(
                f"Error checking if column {column_name} exists in {table_name}: {str(e)}"
            )
            return False

    def ensure_migrations_applied(self) -> Tuple[bool, str]:
        """
        Ensure all required migrations are applied

        Applies migrations in order:
        1. GitHub import tables (project_files, repository_metadata, code_validation_results)
        2. Claude auth method column (users.claude_auth_method)

        Returns:
            Tuple of (success: bool, message: str)
        """
        status = self.check_migration_status()

        # If all migrations are applied, we're done
        if all(status.values()):
            msg = "All required migrations already applied"
            self.logger.info(msg)
            return True, msg

        # Apply migrations in order
        migrations_to_apply = [
            ("add_github_import_tables.sql", "GitHub import tables"),
            ("add_claude_auth_method_column.sql", "Claude auth method column"),
        ]

        all_migrations_successful = True
        messages = []

        for migration_file, migration_name in migrations_to_apply:
            # Check if this migration is already applied
            if migration_file == "add_github_import_tables.sql" and status.get(
                "github_import_tables"
            ):
                self.logger.info(f"{migration_name} already applied, skipping")
                messages.append(f"{migration_name}: already applied")
                continue
            elif migration_file == "add_claude_auth_method_column.sql" and status.get(
                "users_claude_auth_method"
            ):
                self.logger.info(f"{migration_name} already applied, skipping")
                messages.append(f"{migration_name}: already applied")
                continue

            # Apply the migration
            self.logger.info(f"Applying {migration_name} migration ({migration_file})...")
            success, msg = self.apply_migration(migration_file)

            if success:
                messages.append(f"{migration_name}: applied successfully")
            else:
                messages.append(f"{migration_name}: FAILED - {msg}")
                all_migrations_successful = False

        # Verify all migrations were successful
        final_status = self.check_migration_status()
        if all(final_status.values()):
            final_msg = f"All migrations applied successfully. Status: {final_status}"
            self.logger.info(final_msg)
            return True, final_msg
        else:
            final_msg = f"Some migrations failed or incomplete. Status: {final_status}. Details: {'; '.join(messages)}"
            self.logger.error(final_msg)
            return all_migrations_successful, final_msg

    def list_migrations(self) -> List[str]:
        """
        List all available migration files

        Returns:
            List of migration file names
        """
        if not self.migration_dir.exists():
            return []

        migrations = [
            f.name
            for f in self.migration_dir.glob("*.sql")
            if f.is_file() and f.name.startswith("add_")
        ]

        return sorted(migrations)
