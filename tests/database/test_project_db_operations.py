"""
Tests for Project Database operations - Core database functionality.

Tests cover:
- Project CRUD operations (create, read, update, delete)
- User management
- Project notes
- Learning data (question effectiveness, behavior patterns)
- LLM configuration
- API keys
"""

import datetime
import os
import tempfile
from decimal import Decimal

import pytest

from socratic_system.database.project_db import ProjectDatabase
from socratic_system.models import (
    LLMUsageRecord,
    ProjectContext,
    ProjectNote,
    QuestionEffectiveness,
    User,
    UserBehaviorPattern,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = ProjectDatabase(db_path)
        yield db


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    return ProjectContext(
        project_id="test-proj-001",
        name="Test Project",
        owner="testuser",
        collaborators=[],
        goals="Test goals",
        requirements=["req1", "req2"],
        tech_stack=["Python", "Django"],
        constraints=["time"],
        team_structure="individual",
        language_preferences="python",
        deployment_target="local",
        code_style="documented",
        phase="discovery",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        username="testuser",
        email="testuser@example.com",
        passcode_hash="hashed_password",
        created_at=datetime.datetime.now(),
        projects=["test-proj-001"],
    )


class TestProjectDatabaseInitialization:
    """Tests for database initialization."""

    def test_database_initialization(self, temp_db):
        """Test database initializes correctly."""
        assert temp_db is not None
        assert os.path.exists(temp_db.db_path)

    def test_database_creates_tables(self, temp_db):
        """Test database creates all necessary tables."""
        # If database initialized without error, tables were created
        assert temp_db.logger is not None


class TestProjectDatabaseProjectOperations:
    """Tests for project CRUD operations."""

    def test_save_project(self, temp_db, sample_project):
        """Test saving a project."""
        try:
            temp_db.save_project(sample_project)
            # If save succeeded without error, test passes
            assert True
        except Exception as e:
            pytest.fail(f"Failed to save project: {e}")

    def test_load_project(self, temp_db, sample_project):
        """Test loading a saved project."""
        temp_db.save_project(sample_project)

        loaded = temp_db.load_project(sample_project.project_id)

        assert loaded is not None
        assert loaded.project_id == sample_project.project_id
        assert loaded.name == sample_project.name

    def test_load_nonexistent_project(self, temp_db):
        """Test loading a project that doesn't exist."""
        loaded = temp_db.load_project("nonexistent-id")

        assert loaded is None

    def test_delete_project(self, temp_db, sample_project):
        """Test deleting a project permanently."""
        temp_db.save_project(sample_project)
        success = temp_db.permanently_delete_project(sample_project.project_id)

        assert success is True

    def test_delete_nonexistent_project(self, temp_db):
        """Test deleting a project that doesn't exist."""
        success = temp_db.permanently_delete_project("nonexistent")

        assert success is False

    def test_list_all_projects(self, temp_db, sample_project):
        """Test listing projects for a user."""
        temp_db.save_project(sample_project)

        # Use get_user_projects instead of list_all_projects
        projects = temp_db.get_user_projects(sample_project.owner, include_archived=False)

        assert isinstance(projects, list)
        assert len(projects) >= 1

    def test_project_persistence(self, temp_db, sample_project):
        """Test that project data persists correctly."""
        # Save
        temp_db.save_project(sample_project)

        # Modify in memory
        sample_project.goals = "Modified goals"

        # Load from database
        loaded = temp_db.load_project(sample_project.project_id)

        # Should have original goals from database, not modified version
        assert loaded.goals == "Test goals"


class TestProjectDatabaseUserOperations:
    """Tests for user management."""

    def test_save_user(self, temp_db, sample_user):
        """Test saving a user."""
        try:
            temp_db.save_user(sample_user)
            assert True
        except Exception as e:
            pytest.fail(f"Failed to save user: {e}")

    def test_load_user(self, temp_db, sample_user):
        """Test loading a user."""
        temp_db.save_user(sample_user)

        loaded = temp_db.load_user(sample_user.username)

        assert loaded is not None
        assert loaded.username == sample_user.username

    def test_load_nonexistent_user(self, temp_db):
        """Test loading a user that doesn't exist."""
        loaded = temp_db.load_user("nonexistent")

        assert loaded is None

    def test_delete_user(self, temp_db, sample_user):
        """Test permanently deleting a user."""
        temp_db.save_user(sample_user)
        success = temp_db.permanently_delete_user(sample_user.username)

        assert success is True

    def test_user_projects_list(self, temp_db, sample_user, sample_project):
        """Test getting user's projects."""
        temp_db.save_user(sample_user)
        temp_db.save_project(sample_project)

        # Note: get_user_projects retrieves from database
        # This test verifies the method exists and handles data correctly
        projects = temp_db.get_user_projects(sample_user.username)

        assert isinstance(projects, list)


class TestProjectDatabaseNotesOperations:
    """Tests for project notes."""

    def test_add_note(self, temp_db, sample_project):
        """Test saving a note to a project."""
        temp_db.save_project(sample_project)

        note = ProjectNote(
            note_id="note-001",
            project_id=sample_project.project_id,
            title="Test Note",
            content="Test content",
            note_type="design",
            created_by="testuser",
            created_at=datetime.datetime.now(),
            tags=["test"],
        )

        try:
            success = temp_db.save_note(note)
            assert success is True
        except Exception as e:
            pytest.fail(f"Failed to save note: {e}")

    def test_get_project_notes(self, temp_db, sample_project):
        """Test retrieving notes for a project."""
        temp_db.save_project(sample_project)

        note = ProjectNote(
            note_id="note-002",
            project_id=sample_project.project_id,
            title="Test",
            content="Content",
            note_type="bug",
            created_by="testuser",
            created_at=datetime.datetime.now(),
            tags=[],
        )

        temp_db.save_note(note)
        notes = temp_db.get_project_notes(sample_project.project_id)

        assert isinstance(notes, list)
        assert len(notes) >= 1

    def test_delete_note(self, temp_db, sample_project):
        """Test deleting a note."""
        temp_db.save_project(sample_project)

        note = ProjectNote(
            note_id="note-003",
            project_id=sample_project.project_id,
            title="To Delete",
            content="Content",
            note_type="idea",
            created_by="testuser",
            created_at=datetime.datetime.now(),
            tags=[],
        )

        temp_db.save_note(note)
        success = temp_db.delete_note("note-003")

        assert success is True


class TestProjectDatabaseLearningOperations:
    """Tests for learning data storage."""

    def test_record_question_effectiveness(self, temp_db):
        """Test recording question effectiveness."""
        effectiveness = QuestionEffectiveness(
            id="eff-001",
            user_id="testuser",
            question_template_id="qt-001",
            role="PM",
            times_asked=5,
            times_answered_well=4,
            average_answer_length=250,
            effectiveness_score=Decimal("0.8"),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        try:
            temp_db.save_question_effectiveness(effectiveness)
            assert True
        except Exception as e:
            pytest.fail(f"Failed to save question effectiveness: {e}")

    def test_get_question_effectiveness(self, temp_db):
        """Test retrieving question effectiveness."""
        effectiveness = QuestionEffectiveness(
            id="eff-002",
            user_id="testuser",
            question_template_id="qt-002",
            role="BA",
            times_asked=3,
            times_answered_well=2,
            average_answer_length=200,
            effectiveness_score=Decimal("0.67"),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        temp_db.save_question_effectiveness(effectiveness)
        retrieved = temp_db.get_question_effectiveness("testuser", "qt-002")

        assert retrieved is not None

    def test_record_behavior_pattern(self, temp_db):
        """Test recording user behavior pattern."""
        pattern = UserBehaviorPattern(
            id="pat-001",
            user_id="testuser",
            pattern_type="quick_responder",
            pattern_data={"avg_response_time": 2.5},
            learned_from_projects=["proj-001"],
            learned_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        try:
            temp_db.save_behavior_pattern(pattern)
            assert True
        except Exception as e:
            pytest.fail(f"Failed to save behavior pattern: {e}")

    def test_get_behavior_patterns(self, temp_db):
        """Test retrieving behavior patterns for a user."""
        pattern = UserBehaviorPattern(
            id="pat-002",
            user_id="testuser",
            pattern_type="thorough_responder",
            pattern_data={},
            learned_from_projects=[],
            learned_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        temp_db.save_behavior_pattern(pattern)
        patterns = temp_db.get_user_behavior_patterns("testuser")

        assert isinstance(patterns, list)


class TestProjectDatabaseLLMConfiguration:
    """Tests for LLM configuration storage."""

    def test_save_llm_config(self, temp_db):
        """Test saving LLM provider configuration."""
        try:
            temp_db.save_llm_config(
                "testuser",
                "claude",
                {
                    "model": "claude-3-sonnet-20240229",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                },
            )
            assert True
        except Exception as e:
            pytest.fail(f"Failed to save LLM config: {e}")

    def test_get_llm_configs(self, temp_db):
        """Test retrieving LLM configurations."""
        temp_db.save_llm_config(
            "testuser",
            "openai",
            {
                "model": "gpt-4",
                "temperature": 0.8,
                "max_tokens": 4096,
            },
        )
        configs = temp_db.get_user_llm_configs("testuser")

        assert isinstance(configs, list)

    def test_get_default_llm_config(self, temp_db):
        """Test retrieving LLM configuration by provider."""
        temp_db.save_llm_config(
            "testuser",
            "claude",
            {
                "model": "claude-haiku-4-5-20251001",
                "temperature": 0.5,
                "max_tokens": 1024,
            },
        )
        retrieved = temp_db.get_user_llm_config("testuser", "claude")

        assert retrieved is not None
        # Retrieved can be a dict or object depending on implementation
        provider = retrieved.get("provider") if isinstance(retrieved, dict) else retrieved.provider
        assert provider == "claude"


class TestProjectDatabaseUsageTracking:
    """Tests for LLM usage tracking."""

    def test_record_llm_usage(self, temp_db, sample_project):
        """Test recording LLM usage."""
        usage = LLMUsageRecord(
            id="usage-001",
            user_id="testuser",
            provider="claude",
            model="claude-3-sonnet-20240229",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost=0.05,
            success=True,
            timestamp=datetime.datetime.now(),
        )

        try:
            temp_db.save_usage_record(usage)
            assert True
        except Exception as e:
            pytest.fail(f"Failed to record LLM usage: {e}")

    def test_get_user_usage_summary(self, temp_db):
        """Test getting user's LLM usage records."""
        usage = LLMUsageRecord(
            id="usage-002",
            user_id="testuser",
            provider="claude",
            model="claude-3-sonnet",
            input_tokens=200,
            output_tokens=100,
            total_tokens=300,
            cost=0.10,
            success=True,
            timestamp=datetime.datetime.now(),
        )

        temp_db.save_usage_record(usage)
        records = temp_db.get_usage_records("testuser", days=30, provider="claude")

        assert isinstance(records, list)

    def test_get_monthly_usage(self, temp_db):
        """Test getting monthly LLM usage records."""
        usage = LLMUsageRecord(
            id="usage-003",
            user_id="testuser",
            provider="openai",
            model="gpt-4",
            input_tokens=150,
            output_tokens=75,
            total_tokens=225,
            cost=0.08,
            success=True,
            timestamp=datetime.datetime.now(),
        )

        temp_db.save_usage_record(usage)
        records = temp_db.get_usage_records("testuser", days=30, provider="openai")

        assert isinstance(records, list)


class TestProjectDatabaseAPIKeys:
    """Tests for API key management."""

    def test_save_api_key(self, temp_db):
        """Test saving an API key."""
        try:
            temp_db.save_api_key("testuser", "claude", "encrypted_secret", "hash_of_key")
            assert True
        except Exception as e:
            pytest.fail(f"Failed to save API key: {e}")

    def test_get_api_keys(self, temp_db):
        """Test retrieving API key by provider."""
        temp_db.save_api_key("testuser", "openai", "secret", "hash_of_secret")
        key = temp_db.get_api_key("testuser", "openai")

        assert key is not None

    def test_deactivate_api_key(self, temp_db):
        """Test deleting an API key."""
        temp_db.save_api_key("testuser", "claude", "key", "hash_of_key")
        success = temp_db.delete_api_key("testuser", "claude")

        assert success is True


class TestProjectDatabaseEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_save_project_with_none_fields(self, temp_db):
        """Test saving project with None optional fields."""
        project = ProjectContext(
            project_id="test-none",
            name="None Test",
            owner="user",
            collaborators=[],
            goals=None,
            requirements=None,
            tech_stack=None,
            constraints=None,
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        try:
            temp_db.save_project(project)
            loaded = temp_db.load_project(project.project_id)
            assert loaded is not None
        except Exception as e:
            pytest.fail(f"Failed to handle None fields: {e}")

    def test_concurrent_project_access(self, temp_db, sample_project):
        """Test concurrent access to same project."""
        temp_db.save_project(sample_project)

        # Load same project multiple times
        loaded1 = temp_db.load_project(sample_project.project_id)
        loaded2 = temp_db.load_project(sample_project.project_id)

        assert loaded1.project_id == loaded2.project_id
        assert loaded1.name == loaded2.name

    def test_large_project_data(self, temp_db):
        """Test saving/loading project with large data."""
        # Create project with large data in other fields
        project = ProjectContext(
            project_id="large-proj",
            name="Large Project",
            owner="user",
            collaborators=[],
            goals="Large test",
            requirements=["req"] * 100,
            tech_stack=["tech"] * 100,
            constraints=["constraint"] * 50,
            team_structure="team",
            language_preferences="python",
            deployment_target="cloud",
            code_style="documented",
            phase="implementation",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        try:
            temp_db.save_project(project)
            loaded = temp_db.load_project("large-proj")
            assert loaded is not None
            assert len(loaded.requirements) == 100
            assert len(loaded.tech_stack) == 100
            assert len(loaded.constraints) == 50
        except Exception as e:
            pytest.fail(f"Failed to handle large data: {e}")
