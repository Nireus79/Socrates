"""
Unit tests for Socrates data models
"""

from datetime import datetime

import pytest

from socratic_system.models import KnowledgeEntry, ProjectContext, ProjectNote, TokenUsage, User


@pytest.mark.unit
class TestUser:
    """Tests for User model"""

    def test_user_creation(self, sample_user):
        """Test creating a user"""
        assert sample_user.username == "testuser"
        assert sample_user.is_archived is False

    def test_user_fields(self, sample_user):
        """Test user fields"""
        assert hasattr(sample_user, "username")
        assert hasattr(sample_user, "passcode_hash")
        assert hasattr(sample_user, "created_at")
        assert hasattr(sample_user, "is_archived")
        assert hasattr(sample_user, "archived_at")

    def test_user_timestamps(self):
        """Test user timestamp handling"""
        now = datetime.now()
        user = User(
            username="testuser", email="test@example.com", passcode_hash="hashed", created_at=now
        )

        assert user.created_at == now
        assert isinstance(user.created_at, datetime)

    def test_user_archive_status(self):
        """Test user archive status"""
        user = User(
            username="testuser",
            email="test@example.com",
            passcode_hash="hashed",
            created_at=datetime.now(),
            is_archived=True,
            archived_at=datetime.now(),
        )

        assert user.is_archived is True
        assert user.archived_at is not None


@pytest.mark.unit
class TestProjectContext:
    """Tests for ProjectContext model"""

    def test_project_creation(self, sample_project):
        """Test creating a project"""
        assert sample_project.project_id == "test_proj_001"
        assert sample_project.name == "Test Project"
        assert sample_project.owner == "testuser"

    def test_project_fields(self, sample_project):
        """Test project fields"""
        required_fields = ["project_id", "name", "owner", "phase", "created_at", "updated_at"]

        for field in required_fields:
            assert hasattr(sample_project, field)

    def test_project_phase(self):
        """Test project phase"""
        project = ProjectContext(
            project_id="test",
            name="Test",
            owner="user",
            phase="completed",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert project.phase == "completed"

    def test_project_collaborators(self):
        """Test project collaborators"""
        project = ProjectContext(
            project_id="test",
            name="Test",
            owner="user1",
            phase="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            collaborators=["user2", "user3"],
        )

        assert len(project.collaborators) == 2
        assert "user2" in project.collaborators

    def test_project_archive(self):
        """Test project archive status"""
        project = ProjectContext(
            project_id="test",
            name="Test",
            owner="user",
            phase="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_archived=True,
            archived_at=datetime.now(),
        )

        assert project.is_archived is True

    def test_project_notes_list(self):
        """Test project notes list"""
        project = ProjectContext(
            project_id="test",
            name="Test",
            owner="user",
            phase="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            notes=[],
        )

        assert isinstance(project.notes, list)


@pytest.mark.unit
class TestKnowledgeEntry:
    """Tests for KnowledgeEntry model"""

    def test_knowledge_entry_creation(self, sample_knowledge_entry):
        """Test creating a knowledge entry"""
        assert sample_knowledge_entry.id == "test_knowledge_001"
        assert "REST" in sample_knowledge_entry.content

    def test_knowledge_entry_fields(self, sample_knowledge_entry):
        """Test knowledge entry fields"""
        assert hasattr(sample_knowledge_entry, "id")
        assert hasattr(sample_knowledge_entry, "content")
        assert hasattr(sample_knowledge_entry, "category")
        assert hasattr(sample_knowledge_entry, "metadata")

    def test_knowledge_entry_embedding(self):
        """Test knowledge entry embedding"""
        entry = KnowledgeEntry(
            id="test", content="Test content", category="test", embedding=[0.1, 0.2, 0.3]
        )

        assert entry.embedding == [0.1, 0.2, 0.3]

    def test_knowledge_entry_metadata(self):
        """Test knowledge entry metadata"""
        metadata = {
            "source": "documentation",
            "difficulty": "intermediate",
            "tags": ["api", "rest"],
        }

        entry = KnowledgeEntry(id="test", content="Test", category="api", metadata=metadata)

        assert entry.metadata == metadata
        assert entry.metadata["source"] == "documentation"

    def test_knowledge_entry_optional_embedding(self):
        """Test knowledge entry with no embedding"""
        entry = KnowledgeEntry(id="test", content="Test", category="test")

        assert entry.embedding is None


@pytest.mark.unit
class TestTokenUsage:
    """Tests for TokenUsage model"""

    def test_token_usage_creation(self, sample_token_usage):
        """Test creating token usage record"""
        assert sample_token_usage.input_tokens == 100
        assert sample_token_usage.output_tokens == 50
        assert sample_token_usage.total_tokens == 150

    def test_token_usage_calculation(self):
        """Test token usage total calculation"""
        usage = TokenUsage(
            input_tokens=200,
            output_tokens=100,
            total_tokens=300,
            model="claude-opus-4-5-20251101",
            timestamp=datetime.now(),
        )

        assert usage.total_tokens == 300

    def test_token_usage_fields(self, sample_token_usage):
        """Test token usage fields"""
        assert hasattr(sample_token_usage, "input_tokens")
        assert hasattr(sample_token_usage, "output_tokens")
        assert hasattr(sample_token_usage, "total_tokens")
        assert hasattr(sample_token_usage, "model")
        assert hasattr(sample_token_usage, "timestamp")

    def test_token_usage_model(self):
        """Test token usage model field"""
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            model="claude-sonnet-4-5-20250929",
            timestamp=datetime.now(),
        )

        assert usage.model == "claude-sonnet-4-5-20250929"

    def test_token_usage_timestamp(self):
        """Test token usage timestamp"""
        now = datetime.now()
        usage = TokenUsage(
            input_tokens=100, output_tokens=50, total_tokens=150, model="test", timestamp=now
        )

        assert usage.timestamp == now


@pytest.mark.unit
class TestProjectNote:
    """Tests for ProjectNote model"""

    def test_project_note_creation(self):
        """Test creating a project note"""
        note = ProjectNote(
            note_id="note_001",
            project_id="proj_001",
            title="Test Note",
            content="This is a test note",
            note_type="observation",
            created_at=datetime.now(),
        )

        assert note.note_id == "note_001"
        assert note.project_id == "proj_001"

    def test_project_note_types(self):
        """Test different note types"""
        types = ["observation", "insight", "question", "answer", "feedback"]

        for note_type in types:
            note = ProjectNote(
                note_id=f"note_{note_type}",
                project_id="proj",
                title="Title",
                content="Content",
                note_type=note_type,
                created_at=datetime.now(),
            )

            assert note.note_type == note_type

    def test_project_note_fields(self):
        """Test project note fields"""
        note = ProjectNote(
            note_id="test",
            project_id="proj",
            title="Title",
            content="Content",
            note_type="observation",
            created_at=datetime.now(),
        )

        assert hasattr(note, "note_id")
        assert hasattr(note, "project_id")
        assert hasattr(note, "title")
        assert hasattr(note, "content")
        assert hasattr(note, "note_type")
        assert hasattr(note, "created_at")

    def test_project_note_search_capability(self):
        """Test if note has search capability"""
        note = ProjectNote(
            note_id="test",
            project_id="proj",
            title="FastAPI Tutorial",
            content="Learn how to build REST APIs with FastAPI",
            note_type="observation",
            created_at=datetime.now(),
        )

        # Check if note can be searched (if method exists)
        if hasattr(note, "matches_query"):
            assert note.matches_query("FastAPI")
            assert note.matches_query("REST")
            assert not note.matches_query("Django")


@pytest.mark.unit
class TestModelDataTypes:
    """Tests for model data type validation"""

    def test_user_string_fields(self):
        """Test that user string fields are strings"""
        user = User(
            username="testuser",
            email="test@example.com",
            passcode_hash="hashed_value",
            created_at=datetime.now(),
        )

        assert isinstance(user.username, str)
        assert isinstance(user.passcode_hash, str)

    def test_project_string_fields(self):
        """Test that project string fields are strings"""
        project = ProjectContext(
            project_id="proj_001",
            name="Test Project",
            owner="owner_name",
            phase="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert isinstance(project.project_id, str)
        assert isinstance(project.name, str)
        assert isinstance(project.owner, str)

    def test_knowledge_entry_string_fields(self):
        """Test knowledge entry string fields"""
        entry = KnowledgeEntry(id="entry_001", content="Some content", category="general")

        assert isinstance(entry.id, str)
        assert isinstance(entry.content, str)
        assert isinstance(entry.category, str)

    def test_token_usage_numeric_fields(self):
        """Test token usage numeric fields"""
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            model="test",
            timestamp=datetime.now(),
        )

        assert isinstance(usage.input_tokens, int)
        assert isinstance(usage.output_tokens, int)
        assert isinstance(usage.total_tokens, int)


@pytest.mark.unit
class TestModelDefaults:
    """Tests for model default values"""

    def test_user_defaults(self):
        """Test User default values"""
        user = User(
            username="test",
            email="test@example.com",
            passcode_hash="hashed",
            created_at=datetime.now(),
        )

        assert user.is_archived is False

    def test_project_defaults(self):
        """Test ProjectContext default values"""
        project = ProjectContext(
            project_id="proj",
            name="Project",
            owner="user",
            phase="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert project.is_archived is False
        assert isinstance(project.collaborators, list)
        assert len(project.collaborators) == 0

    def test_knowledge_entry_defaults(self):
        """Test KnowledgeEntry default values"""
        entry = KnowledgeEntry(id="entry", content="content", category="category")

        assert entry.embedding is None
        assert isinstance(entry.metadata, dict) or entry.metadata is None
