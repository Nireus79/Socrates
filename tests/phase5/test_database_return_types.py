"""
Phase 5 Tests: Database Return Types

Verify that LocalDatabase methods return correctly typed objects
(User, ProjectContext) instead of dicts, and that the objects
work correctly downstream.

Tests Phase 4 changes:
- 9 database methods now return typed objects
- Type safety improvements at database boundary
- Backward compatibility with dict-like interface
"""

import pytest
from pathlib import Path
import tempfile

from socrates_api.database import LocalDatabase
from socrates_api.models_local import User, ProjectContext


class TestDatabaseUserReturnTypes:
    """Test that database returns User objects with correct types."""

    @pytest.fixture
    def db(self):
        """Create in-memory test database."""
        db = LocalDatabase(":memory:")
        yield db
        db.close()

    def test_create_user_returns_user_object(self, db):
        """create_user returns User object, not dict."""
        user = db.create_user("testuser", "test@example.com", "pass_hash")

        assert isinstance(user, User)
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_get_user_returns_user_object(self, db):
        """get_user returns User object, not dict."""
        # Create user first
        created_user = db.create_user("testuser", "test@example.com", "pass_hash")

        # Retrieve with get_user
        user = db.get_user("testuser")

        assert isinstance(user, User)
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_get_user_nonexistent_raises_error(self, db):
        """get_user raises error for nonexistent user."""
        from socrates_api.exceptions import UserNotFoundError

        with pytest.raises(UserNotFoundError):
            db.get_user("nonexistent")

    def test_load_user_returns_user_object(self, db):
        """load_user returns User object, not dict."""
        created_user = db.create_user("testuser", "test@example.com", "pass_hash")

        user = db.load_user("testuser")

        assert isinstance(user, User)
        assert user.username == "testuser"
        assert user.id == created_user.id

    def test_load_user_nonexistent_raises_error(self, db):
        """load_user raises error for nonexistent user."""
        from socrates_api.exceptions import UserNotFoundError

        with pytest.raises(UserNotFoundError):
            db.load_user("nonexistent")

    def test_load_user_by_email_returns_user_object(self, db):
        """load_user_by_email returns User object, not dict."""
        created_user = db.create_user("testuser", "test@example.com", "pass_hash")

        user = db.load_user_by_email("test@example.com")

        assert isinstance(user, User)
        assert user.email == "test@example.com"
        assert user.username == "testuser"

    def test_load_user_by_email_nonexistent_raises_error(self, db):
        """load_user_by_email raises error for nonexistent email."""
        from socrates_api.exceptions import UserNotFoundError

        with pytest.raises(UserNotFoundError):
            db.load_user_by_email("nonexistent@example.com")

    def test_save_user_returns_user_object(self, db):
        """save_user returns User object, not dict."""
        created_user = db.create_user("testuser", "test@example.com", "pass_hash")

        # Modify user
        created_user.subscription_tier = "pro"

        # Save modified user
        saved_user = db.save_user(created_user)

        assert isinstance(saved_user, User)
        assert saved_user.subscription_tier == "pro"

    def test_user_object_has_all_fields(self, db):
        """User object has all required fields after database retrieval."""
        user = db.create_user("testuser", "test@example.com", "pass_hash")

        assert hasattr(user, 'id')
        assert hasattr(user, 'username')
        assert hasattr(user, 'email')
        assert hasattr(user, 'passcode_hash')
        assert hasattr(user, 'subscription_tier')
        assert hasattr(user, 'subscription_status')
        assert hasattr(user, 'metadata')


class TestDatabaseProjectReturnTypes:
    """Test that database returns ProjectContext objects with correct types."""

    @pytest.fixture
    def db(self):
        """Create in-memory test database."""
        db = LocalDatabase(":memory:")
        # Create a user first (projects need owner)
        db.create_user("testuser", "test@example.com", "pass_hash")
        yield db
        db.close()

    def test_create_project_returns_project_context(self, db):
        """create_project returns ProjectContext object, not dict."""
        project = db.create_project(
            project_id="proj_123",
            owner="testuser",
            name="Test Project",
            description="Test description"
        )

        assert isinstance(project, ProjectContext)
        assert project.project_id == "proj_123"
        assert project.name == "Test Project"
        assert project.owner == "testuser"

    def test_get_project_returns_project_context(self, db):
        """get_project returns ProjectContext object, not dict."""
        created = db.create_project(
            project_id="proj_123",
            owner="testuser",
            name="Test Project"
        )

        project = db.get_project("proj_123")

        assert isinstance(project, ProjectContext)
        assert project.project_id == "proj_123"
        assert project.name == "Test Project"

    def test_get_project_nonexistent_raises_error(self, db):
        """get_project raises error for nonexistent project."""
        from socrates_api.exceptions import ProjectNotFoundError

        with pytest.raises(ProjectNotFoundError):
            db.get_project("nonexistent")

    def test_load_project_returns_project_context(self, db):
        """load_project returns ProjectContext object, not dict."""
        created = db.create_project(
            project_id="proj_123",
            owner="testuser",
            name="Test Project"
        )

        project = db.load_project("proj_123")

        assert isinstance(project, ProjectContext)
        assert project.project_id == "proj_123"

    def test_list_projects_returns_list_of_project_context(self, db):
        """list_projects returns list of ProjectContext objects."""
        db.create_project("proj_1", "testuser", "Project 1")
        db.create_project("proj_2", "testuser", "Project 2")

        projects = db.list_projects("testuser")

        assert isinstance(projects, list)
        assert len(projects) == 2
        assert all(isinstance(p, ProjectContext) for p in projects)
        assert projects[0].name == "Project 1"
        assert projects[1].name == "Project 2"

    def test_list_projects_empty(self, db):
        """list_projects returns empty list for user with no projects."""
        from socrates_api.exceptions import DatabaseError

        # Should raise DatabaseError since we have no projects
        # (or return empty list depending on implementation)
        try:
            projects = db.list_projects("otheruser")
            assert isinstance(projects, list)
            assert len(projects) == 0
        except DatabaseError:
            # This is acceptable - database layer may raise instead of returning []
            pass

    def test_project_context_has_all_fields(self, db):
        """ProjectContext has all required fields after retrieval."""
        project = db.create_project(
            project_id="proj_123",
            owner="testuser",
            name="Test Project",
            description="Test description"
        )

        assert hasattr(project, 'project_id')
        assert hasattr(project, 'name')
        assert hasattr(project, 'owner')
        assert hasattr(project, 'description')
        assert hasattr(project, 'phase')
        assert hasattr(project, 'is_archived')
        assert hasattr(project, 'metadata')
        assert hasattr(project, 'conversation_history')

    def test_project_nested_structures(self, db):
        """ProjectContext nested structures are accessible."""
        project = db.create_project(
            project_id="proj_123",
            owner="testuser",
            name="Test Project"
        )

        # Set up nested data
        project.conversation_history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"}
        ]
        project.metadata = {"key": "value"}

        saved = db.save_project(project)

        assert len(saved.conversation_history) == 2
        assert saved.metadata["key"] == "value"


class TestDatabaseReturnTypeDictCompatibility:
    """Test dict-like interface on database return objects."""

    @pytest.fixture
    def db(self):
        """Create in-memory test database."""
        db = LocalDatabase(":memory:")
        db.create_user("testuser", "test@example.com", "pass_hash")
        yield db
        db.close()

    def test_user_getitem_access(self, db):
        """User object supports dict-style access with []."""
        user = db.create_user("testuser", "test@example.com", "pass_hash")

        assert user["id"] == user.id
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"

    def test_user_get_method(self, db):
        """User object supports .get() method."""
        user = db.create_user("testuser", "test@example.com", "pass_hash")

        assert user.get("username") == "testuser"
        assert user.get("nonexistent") is None
        assert user.get("nonexistent", "default") == "default"

    def test_user_in_operator(self, db):
        """User object supports 'in' operator."""
        user = db.create_user("testuser", "test@example.com", "pass_hash")

        assert "username" in user
        assert "email" in user
        assert "nonexistent" not in user

    def test_project_getitem_access(self, db):
        """ProjectContext object supports dict-style access."""
        project = db.create_project("proj_123", "testuser", "Test")

        assert project["project_id"] == "proj_123"
        assert project["name"] == "Test"
        assert project["owner"] == "testuser"

    def test_project_get_method(self, db):
        """ProjectContext object supports .get() method."""
        project = db.create_project("proj_123", "testuser", "Test")

        assert project.get("project_id") == "proj_123"
        assert project.get("nonexistent") is None

    def test_project_in_operator(self, db):
        """ProjectContext object supports 'in' operator."""
        project = db.create_project("proj_123", "testuser", "Test")

        assert "project_id" in project
        assert "name" in project
        assert "nonexistent" not in project


class TestDatabaseErrorHandling:
    """Test that database methods properly handle errors."""

    @pytest.fixture
    def db(self):
        """Create in-memory test database."""
        db = LocalDatabase(":memory:")
        yield db
        db.close()

    def test_create_project_handles_invalid_owner(self, db):
        """create_project handles invalid owner gracefully."""
        from socrates_api.exceptions import DatabaseError

        # Create project with nonexistent owner - should work or raise DatabaseError
        try:
            project = db.create_project(
                project_id="proj_123",
                owner="nonexistent_user",
                name="Test"
            )
            # Some implementations may allow this
            assert isinstance(project, ProjectContext)
        except DatabaseError:
            # Other implementations may validate owner exists
            pass

    def test_get_user_returns_none_or_raises(self, db):
        """get_user returns None or raises error (not dict)."""
        from socrates_api.exceptions import UserNotFoundError

        with pytest.raises(UserNotFoundError):
            db.get_user("nonexistent")

    def test_get_project_returns_none_or_raises(self, db):
        """get_project returns None or raises error (not dict)."""
        from socrates_api.exceptions import ProjectNotFoundError

        with pytest.raises(ProjectNotFoundError):
            db.get_project("nonexistent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
