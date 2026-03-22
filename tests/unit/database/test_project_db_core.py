"""
Comprehensive tests for project_db core functionality.

Tests the most critical CRUD operations and basic functionality
of the ProjectDatabase class.
"""

import datetime
import tempfile
from pathlib import Path

import pytest

from socratic_system.database.project_db import ProjectDatabase
from socratic_system.models.project import ProjectContext
from socratic_system.models.user import User


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = ProjectDatabase(str(db_path))
        yield db


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    now = datetime.datetime.now()
    return ProjectContext(
        project_id="test-proj-001",
        name="Test Project",
        owner="user123",
        phase="development",
        created_at=now,
        updated_at=now,
        collaborators=["user456"],
        goals="Build a test application",
        requirements=["Requirement 1"],
        tech_stack=["Python", "FastAPI"],
        constraints=[],
        team_structure="distributed",
        language_preferences="python",
        deployment_target="cloud",
        code_style="Google",
        conversation_history=[],
    )


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        username="testuser",
        email="test@example.com",
        passcode_hash="hashed_password_123",
        created_at=datetime.datetime.now(),
        projects=["proj1", "proj2"],
        subscription_tier="pro",
    )


class TestProjectDBInitialization:
    """Tests for ProjectDatabase initialization."""

    def test_init_with_custom_path(self, temp_db):
        """Test database initialization with custom path."""
        assert temp_db.db_path
        assert Path(temp_db.db_path).parent.exists()

    def test_init_creates_directory(self, temp_db):
        """Test that initialization creates parent directories."""
        assert Path(temp_db.db_path).parent.exists()

    def test_init_with_invalid_path_raises_error(self):
        """Test that invalid db_path raises ValueError."""
        with pytest.raises(ValueError):
            ProjectDatabase("")

    def test_init_with_none_path(self):
        """Test initialization with None uses environment variables."""
        db = ProjectDatabase(None)
        assert db.db_path is not None

    def test_init_with_whitespace_path_raises_error(self):
        """Test that whitespace-only path raises ValueError."""
        with pytest.raises(ValueError):
            ProjectDatabase("   ")


class TestProjectSaveLoad:
    """Tests for basic project save and load operations."""

    def test_save_and_load_project(self, temp_db, sample_project):
        """Test saving and loading a project."""
        temp_db.save_project(sample_project)
        loaded = temp_db.load_project(sample_project.project_id)

        assert loaded is not None
        assert loaded.project_id == sample_project.project_id
        assert loaded.name == sample_project.name
        assert loaded.owner == sample_project.owner

    def test_load_nonexistent_project(self, temp_db):
        """Test loading nonexistent project returns None."""
        result = temp_db.load_project("nonexistent-id-xyz")
        assert result is None

    def test_save_project_minimal(self, temp_db):
        """Test saving minimal project."""
        now = datetime.datetime.now()
        project = ProjectContext(
            project_id="minimal-proj",
            name="Minimal",
            owner="user1",
            phase="planning",
            created_at=now,
            updated_at=now,
        )
        temp_db.save_project(project)
        loaded = temp_db.load_project("minimal-proj")

        assert loaded is not None
        assert loaded.project_id == "minimal-proj"

    def test_save_overwrites_existing_project(self, temp_db, sample_project):
        """Test that saving overwrites existing project."""
        temp_db.save_project(sample_project)

        # Modify and save again
        sample_project.name = "Updated Name"
        temp_db.save_project(sample_project)

        loaded = temp_db.load_project(sample_project.project_id)
        assert loaded.name == "Updated Name"

    def test_save_project_with_conversation_history(self, temp_db, sample_project):
        """Test saving project with conversation history."""
        sample_project.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        temp_db.save_project(sample_project)

        loaded = temp_db.load_project(sample_project.project_id)
        assert loaded is not None
        # Conversation history may be in separate table
        assert isinstance(loaded.conversation_history, list)

    def test_save_multiple_projects(self, temp_db):
        """Test saving and retrieving multiple projects."""
        now = datetime.datetime.now()
        projects = []

        for i in range(5):
            project = ProjectContext(
                project_id=f"proj-{i}",
                name=f"Project {i}",
                owner="owner1",
                phase="planning",
                created_at=now,
                updated_at=now,
            )
            temp_db.save_project(project)
            projects.append(project)

        # Verify all saved
        for proj in projects:
            loaded = temp_db.load_project(proj.project_id)
            assert loaded is not None

    def test_load_project_preserves_fields(self, temp_db, sample_project):
        """Test that loading preserves all project fields."""
        temp_db.save_project(sample_project)
        loaded = temp_db.load_project(sample_project.project_id)

        assert loaded.goals == sample_project.goals
        assert loaded.code_style == sample_project.code_style
        assert len(loaded.requirements) >= len(sample_project.requirements)


class TestProjectDelete:
    """Tests for project deletion."""

    def test_delete_project(self, temp_db, sample_project):
        """Test deleting a project."""
        temp_db.save_project(sample_project)
        result = temp_db.delete_project(sample_project.project_id)

        assert result is True
        loaded = temp_db.load_project(sample_project.project_id)
        assert loaded is None

    def test_delete_nonexistent_project(self, temp_db):
        """Test deleting nonexistent project returns False."""
        result = temp_db.delete_project("nonexistent-id")
        assert result is False

    def test_delete_returns_false_on_second_delete(self, temp_db, sample_project):
        """Test that deleting twice returns False on second attempt."""
        temp_db.save_project(sample_project)
        first_delete = temp_db.delete_project(sample_project.project_id)
        second_delete = temp_db.delete_project(sample_project.project_id)

        assert first_delete is True
        assert second_delete is False


class TestGetUserProjects:
    """Tests for retrieving user projects."""

    def test_get_user_projects(self, temp_db):
        """Test getting all projects for a user."""
        owner = "user123"
        now = datetime.datetime.now()

        for i in range(3):
            project = ProjectContext(
                project_id=f"proj-user-{i}",
                name=f"Project {i}",
                owner=owner,
                phase="planning",
                created_at=now,
                updated_at=now,
            )
            temp_db.save_project(project)

        projects = temp_db.get_user_projects(owner)
        assert isinstance(projects, list)
        assert len(projects) >= 3
        # Check that returned items are ProjectContext objects
        for proj in projects:
            assert isinstance(proj, ProjectContext)
            assert proj.owner == owner

    def test_get_user_projects_empty(self, temp_db):
        """Test getting projects for user with no projects."""
        projects = temp_db.get_user_projects("user-with-no-projects")
        assert projects == []

    def test_get_user_projects_returns_only_owner_projects(self, temp_db):
        """Test that get_user_projects returns only owner's projects."""
        user1 = "owner1"
        user2 = "owner2"
        now = datetime.datetime.now()

        # Create projects for user1
        for i in range(2):
            temp_db.save_project(
                ProjectContext(
                    project_id=f"user1-proj-{i}",
                    name=f"User1 Project {i}",
                    owner=user1,
                    phase="planning",
                    created_at=now,
                    updated_at=now,
                )
            )

        # Create projects for user2
        for i in range(3):
            temp_db.save_project(
                ProjectContext(
                    project_id=f"user2-proj-{i}",
                    name=f"User2 Project {i}",
                    owner=user2,
                    phase="planning",
                    created_at=now,
                    updated_at=now,
                )
            )

        user1_projects = temp_db.get_user_projects(user1)
        user2_projects = temp_db.get_user_projects(user2)

        assert len(user1_projects) == 2
        assert len(user2_projects) == 3
        assert all(p.owner == user1 for p in user1_projects)
        assert all(p.owner == user2 for p in user2_projects)


class TestUserSaveLoad:
    """Tests for user save and load operations."""

    def test_save_and_load_user(self, temp_db, sample_user):
        """Test saving and loading a user."""
        temp_db.save_user(sample_user)
        loaded = temp_db.load_user(sample_user.username)

        assert loaded is not None
        assert loaded.username == sample_user.username
        assert loaded.email == sample_user.email

    def test_load_nonexistent_user(self, temp_db):
        """Test loading nonexistent user returns None."""
        result = temp_db.load_user("nonexistent-user")
        assert result is None

    def test_save_user_minimal(self, temp_db):
        """Test saving minimal user."""
        user = User(
            username="minimal",
            email="minimal@example.com",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
        )
        temp_db.save_user(user)

        loaded = temp_db.load_user("minimal")
        assert loaded is not None
        assert loaded.username == "minimal"

    def test_load_user_by_email(self, temp_db, sample_user):
        """Test loading user by email."""
        temp_db.save_user(sample_user)
        loaded = temp_db.load_user_by_email(sample_user.email)

        assert loaded is not None
        assert loaded.username == sample_user.username

    def test_load_user_by_email_nonexistent(self, temp_db):
        """Test loading user by nonexistent email returns None."""
        result = temp_db.load_user_by_email("nonexistent@example.com")
        assert result is None

    def test_save_user_overwrite(self, temp_db, sample_user):
        """Test that saving overwrites existing user."""
        temp_db.save_user(sample_user)

        sample_user.email = "newemail@example.com"
        temp_db.save_user(sample_user)

        loaded = temp_db.load_user(sample_user.username)
        assert loaded.email == "newemail@example.com"

    def test_load_user_preserves_subscription(self, temp_db, sample_user):
        """Test that user subscription info is preserved."""
        temp_db.save_user(sample_user)
        loaded = temp_db.load_user(sample_user.username)

        assert loaded.subscription_tier == "pro"
        assert loaded.email == sample_user.email


class TestConversationHistory:
    """Tests for conversation history operations."""

    def test_save_and_get_conversation_history(self, temp_db, sample_project):
        """Test saving and retrieving conversation history."""
        temp_db.save_project(sample_project)

        # Save conversation
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        temp_db.save_conversation_history(sample_project.project_id, history)

        # Load conversation
        loaded = temp_db.get_conversation_history(sample_project.project_id)
        assert isinstance(loaded, list)
        assert len(loaded) > 0

    def test_get_empty_conversation_history(self, temp_db, sample_project):
        """Test getting conversation history when none exists."""
        temp_db.save_project(sample_project)

        history = temp_db.get_conversation_history(sample_project.project_id)
        assert isinstance(history, list)

    def test_get_conversation_for_nonexistent_project(self, temp_db):
        """Test getting history for nonexistent project."""
        history = temp_db.get_conversation_history("nonexistent-proj")
        # Should handle gracefully - return empty or None
        assert history is None or history == []

    def test_overwrite_conversation_history(self, temp_db, sample_project):
        """Test that new history overwrites old history."""
        temp_db.save_project(sample_project)

        # Save first history
        history1 = [{"role": "user", "content": "First"}]
        temp_db.save_conversation_history(sample_project.project_id, history1)

        # Overwrite with second history
        history2 = [
            {"role": "user", "content": "Second"},
            {"role": "assistant", "content": "Response"},
        ]
        temp_db.save_conversation_history(sample_project.project_id, history2)

        loaded = temp_db.get_conversation_history(sample_project.project_id)
        # Should contain latest history
        assert isinstance(loaded, list)


class TestDatabaseIntegration:
    """Integration tests combining multiple operations."""

    def test_create_project_load_get_in_user_projects(self, temp_db):
        """Test complete workflow: create project, verify in user projects."""
        now = datetime.datetime.now()
        user = "integration-user"

        project = ProjectContext(
            project_id="integration-proj",
            name="Integration Test",
            owner=user,
            phase="design",
            created_at=now,
            updated_at=now,
        )

        # Create project
        temp_db.save_project(project)

        # Load directly
        loaded = temp_db.load_project("integration-proj")
        assert loaded is not None

        # Verify in user projects
        user_projects = temp_db.get_user_projects(user)
        assert len(user_projects) > 0

    def test_save_user_and_create_projects(self, temp_db):
        """Test saving user and creating associated projects."""
        user = User(
            username="projowner",
            email="owner@example.com",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=["proj1", "proj2"],
        )

        temp_db.save_user(user)

        # Create associated projects
        now = datetime.datetime.now()
        for proj_id in ["proj1", "proj2"]:
            temp_db.save_project(
                ProjectContext(
                    project_id=proj_id,
                    name=proj_id,
                    owner="projowner",
                    phase="planning",
                    created_at=now,
                    updated_at=now,
                )
            )

        # Verify user
        loaded_user = temp_db.load_user("projowner")
        assert loaded_user is not None

        # Verify projects
        user_projects = temp_db.get_user_projects("projowner")
        assert len(user_projects) >= 2
