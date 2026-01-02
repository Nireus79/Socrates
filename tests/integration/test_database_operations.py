"""
Integration tests for database operations.

Tests real database interactions including:
- Database initialization
- Project storage and retrieval
- Learning records
"""

import pytest
import tempfile
from pathlib import Path

from socratic_system.database.project_db import ProjectDatabase
from socratic_system.models.project import ProjectContext
from datetime import datetime


@pytest.fixture
def temp_db():
    """Create temporary database."""
    temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_path = temp_file.name
    temp_file.close()

    db = ProjectDatabase(db_path)
    yield db

    # Cleanup
    try:
        Path(db_path).unlink()
    except:
        pass


@pytest.mark.integration
class TestDatabaseInitialization:
    """Test database initialization."""

    def test_database_creates_successfully(self, temp_db):
        """Test database initializes without errors."""
        assert temp_db is not None
        assert temp_db.db_path is not None

    def test_database_with_env_path(self):
        """Test database can be created with explicit path."""
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        db_path = temp_file.name
        temp_file.close()

        try:
            db = ProjectDatabase(db_path)
            assert db is not None
            assert Path(db_path).exists()
        finally:
            Path(db_path).unlink()


@pytest.mark.integration
class TestProjectOperations:
    """Test project storage and retrieval."""

    def test_save_and_load_project(self, temp_db):
        """Test saving and loading a project."""
        # Create a project context
        project = ProjectContext(
            project_id="test_proj_1",
            name="Test Project",
            owner="test_user",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="A test project"
        )

        # Save project
        temp_db.save_project(project)

        # Load project
        loaded = temp_db.load_project(project.project_id)

        # Verify
        assert loaded is not None
        assert loaded.name == "Test Project"
        assert loaded.owner == "test_user"

    def test_load_nonexistent_project(self, temp_db):
        """Test loading non-existent project returns None."""
        loaded = temp_db.load_project("nonexistent_project_xyz")
        assert loaded is None


@pytest.mark.integration
class TestDatabaseMethods:
    """Test database has expected methods."""

    def test_database_has_project_methods(self, temp_db):
        """Test database has project-related methods."""
        assert hasattr(temp_db, 'save_project')
        assert hasattr(temp_db, 'load_project')
        assert hasattr(temp_db, 'delete_project')

    def test_database_has_activity_methods(self, temp_db):
        """Test database has activity tracking methods."""
        assert hasattr(temp_db, 'get_project_activities') or hasattr(temp_db, 'count_project_activities')

    def test_database_has_knowledge_methods(self, temp_db):
        """Test database has knowledge document methods."""
        assert hasattr(temp_db, 'get_project_knowledge_documents')
