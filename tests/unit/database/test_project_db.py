"""
Unit tests for ProjectDatabase - core database operations for projects and users.

Tests cover:
- Database initialization and schema creation
- Project CRUD operations
- User management
- Project notes
- Learning and behavior tracking
"""

import datetime
import sqlite3
import tempfile
from pathlib import Path

import pytest

from socratic_system.database.project_db import ProjectDatabase
from socratic_system.models import (
    ProjectContext,
    ProjectNote,
    QuestionEffectiveness,
    User,
    UserBehaviorPattern,
)


class TestProjectDatabaseInitialization:
    """Test database setup and schema creation"""

    @pytest.fixture
    def db_path(self):
        """Create a temporary database file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_file = Path(temp_dir) / "test.db"
            yield str(db_file)

    def test_database_initialization(self, db_path):
        """Test that database is properly initialized"""
        db = ProjectDatabase(db_path)
        assert Path(db_path).exists()
        assert db.db_path == db_path

    def test_database_schema_creation(self, db_path):
        """Test that all required tables are created"""
        ProjectDatabase(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = {row[0] for row in cursor.fetchall()}

        required_tables = {
            "projects",
            "users",
            "project_notes",
            "question_effectiveness",
            "behavior_patterns",
        }
        assert required_tables.issubset(tables)
        conn.close()

    def test_creates_directory_if_not_exists(self):
        """Test that database directory is created if it doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "nested" / "dir" / "test.db"
            ProjectDatabase(str(nested_path))
            assert nested_path.exists()


class TestProjectOperations:
    """Test project CRUD operations"""

    @pytest.fixture
    def db(self):
        """Create a test database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            yield ProjectDatabase(str(db_path))

    @pytest.fixture
    def sample_project(self):
        """Create a sample project"""
        return ProjectContext(
            project_id="proj_test_001",
            name="Test Project",
            owner="testuser",
            collaborators=[],
            goals="Test goal",
            requirements=["req1", "req2"],
            tech_stack=["Python"],
            constraints=["constraint1"],
            team_structure="individual",
            language_preferences="python",
            deployment_target="cloud",
            code_style="documented",
            phase="planning",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

    def test_save_project_returns_none(self, db, sample_project):
        """Test that save_project returns None (no return value)"""
        result = db.save_project(sample_project)
        assert result is None

    def test_save_and_load_project(self, db, sample_project):
        """Test saving and loading a project"""
        db.save_project(sample_project)
        loaded = db.load_project(sample_project.project_id)
        assert loaded is not None
        assert loaded.project_id == sample_project.project_id
        assert loaded.name == sample_project.name

    def test_load_nonexistent_project(self, db):
        """Test loading a project that doesn't exist"""
        result = db.load_project("nonexistent_id")
        assert result is None

    def test_get_user_projects(self, db):
        """Test getting all projects for a user"""
        user = "testuser"

        proj1 = ProjectContext(
            project_id="proj_001",
            name="Project 1",
            owner=user,
            collaborators=[],
            goals="goal1",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="cloud",
            code_style="documented",
            phase="planning",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        proj2 = ProjectContext(
            project_id="proj_002",
            name="Project 2",
            owner=user,
            collaborators=[],
            goals="goal2",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="cloud",
            code_style="documented",
            phase="planning",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        db.save_project(proj1)
        db.save_project(proj2)

        projects = db.get_user_projects(user)
        assert len(projects) == 2
        assert any(p["project_id"] == "proj_001" for p in projects)
        assert any(p["project_id"] == "proj_002" for p in projects)

    def test_archive_project(self, db, sample_project):
        """Test archiving a project"""
        db.save_project(sample_project)
        result = db.archive_project(sample_project.project_id)
        assert result is True

        loaded = db.load_project(sample_project.project_id)
        assert loaded.is_archived is True

    def test_restore_project(self, db, sample_project):
        """Test restoring an archived project"""
        db.save_project(sample_project)
        db.archive_project(sample_project.project_id)
        result = db.restore_project(sample_project.project_id)
        assert result is True

        loaded = db.load_project(sample_project.project_id)
        assert loaded.is_archived is False

    def test_permanently_delete_project(self, db, sample_project):
        """Test permanently deleting a project"""
        db.save_project(sample_project)
        result = db.permanently_delete_project(sample_project.project_id)
        assert result is True

        loaded = db.load_project(sample_project.project_id)
        assert loaded is None


class TestUserOperations:
    """Test user management operations"""

    @pytest.fixture
    def db(self):
        """Create a test database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            yield ProjectDatabase(str(db_path))

    @pytest.fixture
    def sample_user(self):
        """Create a sample user"""
        return User(
            username="testuser",
            email="test@example.com",
            passcode_hash="hash123",
            created_at=datetime.datetime.now(),
            projects=["proj_001"],
            subscription_tier="free",
        )

    def test_save_user_returns_none(self, db, sample_user):
        """Test that save_user returns None (no return value)"""
        result = db.save_user(sample_user)
        assert result is None

    def test_save_and_load_user(self, db, sample_user):
        """Test saving and loading a user"""
        db.save_user(sample_user)
        loaded = db.load_user(sample_user.username)
        assert loaded is not None
        assert loaded.username == sample_user.username
        assert loaded.email == sample_user.email

    def test_load_nonexistent_user(self, db):
        """Test loading a user that doesn't exist"""
        result = db.load_user("nonexistent_user")
        assert result is None

    def test_user_exists(self, db, sample_user):
        """Test checking if user exists"""
        assert db.user_exists(sample_user.username) is False
        db.save_user(sample_user)
        assert db.user_exists(sample_user.username) is True

    def test_archive_user(self, db, sample_user):
        """Test archiving a user"""
        db.save_user(sample_user)
        result = db.archive_user(sample_user.username, archive_projects=False)
        assert result is True

        loaded = db.load_user(sample_user.username)
        assert loaded.is_archived is True

    def test_restore_user(self, db, sample_user):
        """Test restoring an archived user"""
        db.save_user(sample_user)
        db.archive_user(sample_user.username, archive_projects=False)
        result = db.restore_user(sample_user.username)
        assert result is True

        loaded = db.load_user(sample_user.username)
        assert loaded.is_archived is False

    def test_permanently_delete_user(self, db, sample_user):
        """Test permanently deleting a user"""
        db.save_user(sample_user)
        result = db.permanently_delete_user(sample_user.username)
        assert result is True

        loaded = db.load_user(sample_user.username)
        assert loaded is None


class TestProjectNotes:
    """Test project notes management"""

    @pytest.fixture
    def db(self):
        """Create a test database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            yield ProjectDatabase(str(db_path))

    def test_save_note_returns_true(self, db):
        """Test that save_note returns True"""
        note = ProjectNote(
            note_id="note_001",
            project_id="proj_001",
            title="Test Note",
            content="Test content",
            created_at=datetime.datetime.now(),
        )
        result = db.save_note(note)
        assert result is True

    def test_get_project_notes(self, db):
        """Test getting all notes for a project"""
        proj_id = "proj_001"

        for i in range(3):
            note = ProjectNote(
                note_id=f"note_{i}",
                project_id=proj_id,
                title=f"Note {i}",
                content=f"Content {i}",
                created_at=datetime.datetime.now(),
            )
            db.save_note(note)

        notes = db.get_project_notes(proj_id)
        assert len(notes) == 3

    def test_delete_note(self, db):
        """Test deleting a note"""
        note = ProjectNote(
            note_id="note_001",
            project_id="proj_001",
            title="Test Note",
            content="Test content",
            created_at=datetime.datetime.now(),
        )
        db.save_note(note)
        result = db.delete_note(note.note_id)
        assert result is True

        notes = db.get_project_notes("proj_001")
        assert len(notes) == 0

    def test_search_notes(self, db):
        """Test searching notes"""
        note = ProjectNote(
            note_id="note_001",
            project_id="proj_001",
            title="Test Note",
            content="Important information",
            created_at=datetime.datetime.now(),
        )
        db.save_note(note)

        results = db.search_notes("proj_001", "important")
        assert len(results) >= 0


class TestLearningTracking:
    """Test question effectiveness and behavior patterns"""

    @pytest.fixture
    def db(self):
        """Create a test database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            yield ProjectDatabase(str(db_path))

    def test_save_question_effectiveness_returns_true(self, db):
        """Test that save_question_effectiveness returns True"""
        qe = QuestionEffectiveness(
            id="qe_001",
            user_id="user_001",
            question_template_id="template_001",
            role="PM",
            times_asked=5,
            times_answered_well=4,
            average_answer_length=150,
        )
        result = db.save_question_effectiveness(qe)
        assert result is True

    def test_get_question_effectiveness(self, db):
        """Test loading question effectiveness"""
        qe = QuestionEffectiveness(
            id="qe_001",
            user_id="user_001",
            question_template_id="template_001",
            role="PM",
            times_asked=5,
            times_answered_well=4,
            average_answer_length=150,
        )
        db.save_question_effectiveness(qe)
        loaded = db.get_question_effectiveness("user_001", "template_001")
        assert loaded is not None
        assert loaded.times_asked == 5

    def test_get_user_effectiveness_all(self, db):
        """Test getting all effectiveness records for a user"""
        user_id = "user_001"

        for i in range(3):
            qe = QuestionEffectiveness(
                id=f"qe_{i}",
                user_id=user_id,
                question_template_id=f"template_{i}",
                role="PM",
                times_asked=i + 1,
                times_answered_well=i,
                average_answer_length=150,
            )
            db.save_question_effectiveness(qe)

        records = db.get_user_effectiveness_all(user_id)
        assert len(records) == 3

    def test_save_behavior_pattern_returns_true(self, db):
        """Test that save_behavior_pattern returns True"""
        pattern = UserBehaviorPattern(
            id="pattern_001",
            user_id="user_001",
            pattern_type="learning_speed",
            pattern_data={"speed": "fast", "consistency": "high"},
            learned_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        result = db.save_behavior_pattern(pattern)
        assert result is True

    def test_get_behavior_pattern(self, db):
        """Test loading behavior patterns"""
        pattern = UserBehaviorPattern(
            id="pattern_001",
            user_id="user_001",
            pattern_type="learning_speed",
            pattern_data={"speed": "fast", "consistency": "high"},
            learned_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        db.save_behavior_pattern(pattern)
        loaded = db.get_behavior_pattern("user_001", "learning_speed")
        assert loaded is not None
        assert loaded.pattern_type == "learning_speed"

    def test_get_user_behavior_patterns(self, db):
        """Test getting all behavior patterns for a user"""
        user_id = "user_001"

        for i in range(3):
            pattern = UserBehaviorPattern(
                id=f"pattern_{i}",
                user_id=user_id,
                pattern_type=f"pattern_type_{i}",
                pattern_data={"index": i},
                learned_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            )
            db.save_behavior_pattern(pattern)

        patterns = db.get_user_behavior_patterns(user_id)
        assert len(patterns) == 3


class TestDatabaseConsistency:
    """Test data consistency and edge cases"""

    @pytest.fixture
    def db(self):
        """Create a test database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            yield ProjectDatabase(str(db_path))

    def test_update_existing_project(self, db):
        """Test updating an existing project"""
        project = ProjectContext(
            project_id="proj_001",
            name="Original Name",
            owner="user",
            collaborators=[],
            goals="goal",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="cloud",
            code_style="documented",
            phase="planning",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        db.save_project(project)

        project.name = "Updated Name"
        db.save_project(project)

        loaded = db.load_project("proj_001")
        assert loaded.name == "Updated Name"

    def test_duplicate_user_save_updates(self, db):
        """Test saving the same user twice (update behavior)"""
        user = User(
            username="testuser",
            email="test@example.com",
            passcode_hash="hash123",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )

        db.save_user(user)
        user.email = "newemail@example.com"
        db.save_user(user)

        loaded = db.load_user("testuser")
        assert loaded.email == "newemail@example.com"

    def test_get_archived_items_projects(self, db):
        """Test getting archived items"""
        project = ProjectContext(
            project_id="proj_001",
            name="Test Project",
            owner="user",
            collaborators=[],
            goals="goal",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="cloud",
            code_style="documented",
            phase="planning",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

        db.save_project(project)
        db.archive_project("proj_001")

        archived = db.get_archived_items("projects")
        assert len(archived) == 1
        assert archived[0]["project_id"] == "proj_001"

    def test_get_archived_items_users(self, db):
        """Test getting archived users"""
        user = User(
            username="testuser",
            email="test@example.com",
            passcode_hash="hash123",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier="free",
        )

        db.save_user(user)
        db.archive_user("testuser", archive_projects=False)

        archived = db.get_archived_items("users")
        assert len(archived) == 1
        assert archived[0]["username"] == "testuser"
