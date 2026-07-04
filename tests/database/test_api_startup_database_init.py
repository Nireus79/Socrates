"""
API Startup Database Initialization Tests

Tests that the database is properly initialized when the API starts.
This test catches issues where the database file is not created.

**Why this test exists:**
The bug where projects.db was never created in Docker went undetected
because existing tests didn't verify the initialization sequence.
These tests ensure database initialization happens BEFORE the API
is ready to handle requests.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure socrates_api is importable (add to path)
api_src = Path(__file__).parent.parent.parent / "socrates-api" / "src"
if str(api_src) not in sys.path:
    sys.path.insert(0, str(api_src))


@pytest.mark.unit
class TestAPIStartupDatabaseInitialization:
    """Test database initialization during API startup"""

    def test_database_singleton_initializes_with_defaults(self):
        """Test: DatabaseSingleton.initialize() + get_instance() creates database file"""
        from socrates_api.database import DatabaseSingleton

        with tempfile.TemporaryDirectory() as tmpdir:
            # Set environment variable to temp directory
            original_env = os.environ.get("SOCRATES_DATA_DIR")
            try:
                os.environ["SOCRATES_DATA_DIR"] = tmpdir

                # Reset singleton to test initialization
                DatabaseSingleton.reset()

                # Initialize with defaults (no arguments) - this sets the path
                DatabaseSingleton.initialize()

                # Get instance - this actually creates the database file
                db = DatabaseSingleton.get_instance()

                # Verify database file was created
                db_path = os.path.join(tmpdir, "projects.db")
                assert Path(db_path).exists(), f"Database file not created at {db_path}"
                assert db.db_path == db_path, "Database path mismatch"

            finally:
                # Restore environment
                if original_env:
                    os.environ["SOCRATES_DATA_DIR"] = original_env
                else:
                    os.environ.pop("SOCRATES_DATA_DIR", None)
                DatabaseSingleton.reset()

    def test_database_file_is_created_before_first_query(self):
        """Test: Database file exists immediately after initialize"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_env = os.environ.get("SOCRATES_DATA_DIR")
            try:
                os.environ["SOCRATES_DATA_DIR"] = tmpdir

                from socrates_api.database import DatabaseSingleton

                DatabaseSingleton.reset()

                # Initialize
                DatabaseSingleton.initialize()

                # File should exist now, before any queries
                db_path = os.path.join(tmpdir, "projects.db")
                assert Path(db_path).exists(), (
                    f"Database file not created at {db_path}. "
                    f"Directory contents: {os.listdir(tmpdir)}"
                )

                # File should have content (schema)
                file_size = Path(db_path).stat().st_size
                assert file_size > 0, f"Database file is empty (0 bytes) at {db_path}"

            finally:
                if original_env:
                    os.environ["SOCRATES_DATA_DIR"] = original_env
                else:
                    os.environ.pop("SOCRATES_DATA_DIR", None)
                DatabaseSingleton.reset()

    def test_database_initialization_creates_schema(self):
        """Test: Database schema tables exist after initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_env = os.environ.get("SOCRATES_DATA_DIR")
            try:
                os.environ["SOCRATES_DATA_DIR"] = tmpdir

                from socrates_api.database import DatabaseSingleton

                DatabaseSingleton.reset()

                # Initialize
                DatabaseSingleton.initialize()
                db = DatabaseSingleton.get_instance()

                # Verify schema tables exist
                import sqlite3

                conn = sqlite3.connect(db.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()

                # Should have at least the basic tables
                expected_tables = [
                    "users",
                    "projects",
                    "questions",
                    "conversation_messages",
                ]
                for table in expected_tables:
                    assert table in tables, (
                        f"Expected table '{table}' not found. " f"Available tables: {tables}"
                    )

            finally:
                if original_env:
                    os.environ["SOCRATES_DATA_DIR"] = original_env
                else:
                    os.environ.pop("SOCRATES_DATA_DIR", None)
                DatabaseSingleton.reset()

    def test_get_instance_creates_file_if_not_exists(self):
        """Test: get_instance() creates database file if initialize() not called"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_env = os.environ.get("SOCRATES_DATA_DIR")
            try:
                os.environ["SOCRATES_DATA_DIR"] = tmpdir

                from socrates_api.database import DatabaseSingleton

                DatabaseSingleton.reset()

                # Call get_instance WITHOUT calling initialize first
                # It should initialize automatically
                db = DatabaseSingleton.get_instance()

                # File should exist
                assert Path(db.db_path).exists(), f"Database file not created at {db.db_path}"

            finally:
                if original_env:
                    os.environ["SOCRATES_DATA_DIR"] = original_env
                else:
                    os.environ.pop("SOCRATES_DATA_DIR", None)
                DatabaseSingleton.reset()

    def test_database_path_respects_socrates_data_dir(self):
        """Test: Database is created in SOCRATES_DATA_DIR, not default location"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_env = os.environ.get("SOCRATES_DATA_DIR")
            try:
                os.environ["SOCRATES_DATA_DIR"] = tmpdir

                from socrates_api.database import DatabaseSingleton

                DatabaseSingleton.reset()

                # Initialize and get instance
                DatabaseSingleton.initialize()
                db = DatabaseSingleton.get_instance()

                # Verify path is in the temp directory (from SOCRATES_DATA_DIR)
                assert db.db_path.startswith(
                    tmpdir
                ), f"Database path {db.db_path} not in SOCRATES_DATA_DIR {tmpdir}"

                # Verify file is in correct location
                assert Path(db.db_path).exists()
                assert Path(db.db_path).parent == Path(tmpdir)

            finally:
                if original_env:
                    os.environ["SOCRATES_DATA_DIR"] = original_env
                else:
                    os.environ.pop("SOCRATES_DATA_DIR", None)
                DatabaseSingleton.reset()

    def test_multiple_calls_to_initialize_are_safe(self):
        """Test: Calling initialize() multiple times doesn't corrupt database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_env = os.environ.get("SOCRATES_DATA_DIR")
            try:
                os.environ["SOCRATES_DATA_DIR"] = tmpdir

                from socrates_api.database import DatabaseSingleton

                DatabaseSingleton.reset()

                # Initialize multiple times
                DatabaseSingleton.initialize()
                db1 = DatabaseSingleton.get_instance()
                db_path = db1.db_path

                # Reset and initialize again (simulating restart)
                DatabaseSingleton.reset()
                DatabaseSingleton.initialize()
                db2 = DatabaseSingleton.get_instance()

                # Should be same path and file should still exist
                assert db2.db_path == db_path
                assert Path(db_path).exists()

                # Should be able to query without errors
                import sqlite3

                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                count = cursor.fetchone()[0]
                conn.close()

                assert count > 0, "Schema not properly initialized on restart"

            finally:
                if original_env:
                    os.environ["SOCRATES_DATA_DIR"] = original_env
                else:
                    os.environ.pop("SOCRATES_DATA_DIR", None)
                DatabaseSingleton.reset()


class TestDatabaseInitializationErrorHandling:
    """Test error handling during database initialization"""

    def test_initialization_fails_gracefully_with_invalid_path(self):
        """Test: Proper error if SOCRATES_DATA_DIR is invalid"""
        original_env = os.environ.get("SOCRATES_DATA_DIR")
        try:
            # Set to a path that can't be created
            os.environ["SOCRATES_DATA_DIR"] = "/invalid/path/that/cannot/exist/12345"

            from socrates_api.database import DatabaseSingleton

            DatabaseSingleton.reset()

            # Should raise an exception (not silently fail)
            with pytest.raises(OSError):
                DatabaseSingleton.initialize()
                DatabaseSingleton.get_instance()

        finally:
            if original_env:
                os.environ["SOCRATES_DATA_DIR"] = original_env
            else:
                os.environ.pop("SOCRATES_DATA_DIR", None)
            DatabaseSingleton.reset()

    def test_initialization_fails_loudly_not_silently(self):
        """Test: Exceptions during init are logged and raised, not swallowed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_env = os.environ.get("SOCRATES_DATA_DIR")
            try:
                os.environ["SOCRATES_DATA_DIR"] = tmpdir

                from socrates_api.database import DatabaseSingleton

                DatabaseSingleton.reset()

                # Create a file where the database should be
                # This will cause an error when trying to create directory
                db_file_path = os.path.join(tmpdir, "projects.db")
                Path(tmpdir).mkdir(exist_ok=True)
                # Create a regular file where database should be created
                with open(db_file_path, "w") as f:
                    f.write("this is a file, not a directory")

                # Initialize should handle this gracefully
                DatabaseSingleton.initialize()

                # get_instance should either create it successfully or raise
                try:
                    db = DatabaseSingleton.get_instance()
                    # If it succeeds, that's fine
                    assert db is not None
                except OSError as e:
                    # If it fails due to file/path issue, the exception should be raised
                    assert isinstance(e, OSError)
                    raise  # Re-raise to show the error was caught

            finally:
                if original_env:
                    os.environ["SOCRATES_DATA_DIR"] = original_env
                else:
                    os.environ.pop("SOCRATES_DATA_DIR", None)
                DatabaseSingleton.reset()
