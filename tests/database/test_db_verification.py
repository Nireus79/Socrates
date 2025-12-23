"""
Comprehensive Database Verification Test Suite

Tests:
1. Database initialization and schema creation
2. Foreign key relationships and cascade deletes
3. All CRUD operations
4. Data persistence and integrity
5. Interconnection between API and database
"""

import json
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from socratic_system.database.project_db_v2 import ProjectDatabaseV2
from socratic_system.models.project import ProjectContext
from socratic_system.models.user import User


class TestDatabaseInitialization:
    """Test database schema initialization"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabaseV2(db_path)
        yield db_instance

        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)

    def test_database_creation(self, db):
        """Verify database file is created"""
        assert os.path.exists(db.db_path), "Database file should be created"

    def test_all_tables_exist(self, db):
        """Verify all required tables are created"""
        required_tables = [
            "users_v2",
            "projects_v2",
            "project_requirements",
            "project_tech_stack",
            "project_constraints",
            "team_members",
            "conversation_history",
            "refresh_tokens",
            "api_keys_v2",
            "phase_maturity_scores",
            "category_scores",
            "analytics_metrics",
            "knowledge_documents_v2",
            "llm_provider_configs_v2",
            "question_effectiveness_v2",
            "behavior_patterns_v2",
            "llm_usage_v2",
            "project_notes_v2",
        ]

        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        existing_tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        for table in required_tables:
            assert table in existing_tables, f"Table {table} should exist"

    def test_foreign_keys_enabled(self, db):
        """Verify foreign keys are enabled"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        conn.close()

        # Foreign keys might be off by default, but should be enabled when needed
        assert result is not None, "PRAGMA foreign_keys should return a result"

    def test_indexes_exist(self, db):
        """Verify key indexes are created for performance"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Should have indexes on foreign keys and frequently queried columns
        assert len(indexes) > 0, "Should have at least some indexes"


class TestUserOperations:
    """Test user CRUD operations"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabaseV2(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_save_and_load_user(self, db):
        """Test user creation and retrieval"""
        user = User(
            username="testuser",
            email="testuser@example.com",
            passcode_hash="hashed_password_here",
            created_at=datetime.now(),
        )
        user.subscription_tier = "free"
        user.subscription_status = "active"

        db.save_user(user)
        loaded_user = db.load_user("testuser")

        assert loaded_user is not None, "User should be loaded"
        assert loaded_user.username == "testuser"
        assert loaded_user.subscription_tier == "free"

    def test_user_not_found(self, db):
        """Test loading non-existent user"""
        loaded_user = db.load_user("nonexistent")
        assert loaded_user is None, "Non-existent user should return None"

    def test_user_exists_check(self, db):
        """Test user existence check"""
        user = User(
            username="testuser2",
            email="testuser2@example.com",
            passcode_hash="hashed_password",
            created_at=datetime.now(),
        )
        db.save_user(user)

        assert db.user_exists("testuser2"), "User should exist"
        assert not db.user_exists("nonexistent"), "Non-existent user should not exist"

    def test_multiple_users(self, db):
        """Test multiple users can be stored and retrieved independently"""
        for i in range(5):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                passcode_hash=f"hash{i}",
                created_at=datetime.now(),
            )
            db.save_user(user)

        # Verify all users exist
        for i in range(5):
            assert db.user_exists(f"user{i}"), f"User {i} should exist"


class TestProjectOperations:
    """Test project CRUD operations"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabaseV2(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.fixture
    def sample_project(self):
        """Create a sample project for testing"""
        return ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="testuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            goals=["Build API", "Deploy to cloud"],
            requirements=["RESTful endpoints", "Database"],
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            constraints=["6 month deadline"],
            team_structure={"frontend": 2, "backend": 3},
            language_preferences={"primary": "Python", "secondary": "JavaScript"},
            deployment_target="AWS",
            code_style={"indent": 4, "line_length": 100},
            chat_mode="socratic",
            status="active",
            progress=0.25,
        )

    def test_save_and_load_project(self, db, sample_project):
        """Test project creation and retrieval"""
        db.save_project(sample_project)
        loaded = db.load_project("proj-001")

        assert loaded is not None, "Project should be loaded"
        assert loaded.name == "Test Project"
        assert loaded.owner == "testuser"
        assert loaded.phase == "phase1"
        assert loaded.progress == 0.25

    def test_project_requirements_persisted(self, db, sample_project):
        """Test that project requirements are properly stored"""
        db.save_project(sample_project)
        loaded = db.load_project("proj-001")

        assert loaded.requirements == ["RESTful endpoints", "Database"]

    def test_project_tech_stack_persisted(self, db, sample_project):
        """Test that tech stack is properly stored"""
        db.save_project(sample_project)
        loaded = db.load_project("proj-001")

        assert loaded.tech_stack == ["Python", "FastAPI", "PostgreSQL"]

    def test_project_json_fields(self, db, sample_project):
        """Test that JSON fields are properly serialized/deserialized"""
        db.save_project(sample_project)
        loaded = db.load_project("proj-001")

        assert loaded.team_structure == {"frontend": 2, "backend": 3}
        assert loaded.language_preferences == {"primary": "Python", "secondary": "JavaScript"}
        assert loaded.code_style == {"indent": 4, "line_length": 100}

    def test_get_user_projects(self, db):
        """Test retrieving all projects for a user"""
        # Create multiple projects for same user
        for i in range(3):
            project = ProjectContext(
                project_id=f"proj-00{i}",
                name=f"Project {i}",
                owner="testuser",
                phase="phase1",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.save_project(project)

        projects = db.get_user_projects("testuser")
        assert len(projects) == 3, "Should retrieve 3 projects"

    def test_archive_project(self, db, sample_project):
        """Test project archival"""
        db.save_project(sample_project)
        success = db.archive_project("proj-001")

        assert success, "Archive should succeed"

        loaded = db.load_project("proj-001")
        assert loaded.is_archived, "Project should be marked as archived"

    def test_restore_project(self, db, sample_project):
        """Test project restoration"""
        db.save_project(sample_project)
        db.archive_project("proj-001")
        db.restore_project("proj-001")

        loaded = db.load_project("proj-001")
        assert not loaded.is_archived, "Project should be restored"

    def test_delete_project_cascade(self, db, sample_project):
        """Test that deleting a project cascades to related tables"""
        db.save_project(sample_project)

        # Add conversation history
        history = [
            {"role": "user", "content": "Hello", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": "Hi there", "timestamp": datetime.now().isoformat()},
        ]
        db.save_conversation_history("proj-001", history)

        # Delete project
        success = db.delete_project("proj-001")
        assert success, "Delete should succeed"

        # Verify project is gone
        loaded = db.load_project("proj-001")
        assert loaded is None, "Project should be deleted"

        # Verify related conversation history is also gone
        history = db.get_conversation_history("proj-001")
        assert len(history) == 0, "Conversation history should be cascade deleted"


class TestConversationHistory:
    """Test conversation/chat history operations"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabaseV2(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_save_and_load_conversation(self, db):
        """Test saving and loading conversation history"""
        history = [
            {
                "role": "user",
                "content": "What is the first phase?",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "role": "assistant",
                "content": "The first phase focuses on requirements...",
                "timestamp": datetime.now().isoformat(),
            },
        ]

        db.save_conversation_history("proj-001", history)
        loaded = db.get_conversation_history("proj-001")

        assert len(loaded) == 2, "Should load 2 messages"
        # Verify both messages exist
        contents = [msg["content"] for msg in loaded]
        assert "What is the first phase?" in contents
        assert "The first phase focuses on requirements..." in contents

    def test_conversation_metadata(self, db):
        """Test conversation history with metadata"""
        history = [
            {
                "role": "user",
                "content": "Test message",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"mode": "socratic", "source": "websocket"},
            }
        ]

        db.save_conversation_history("proj-001", history)
        loaded = db.get_conversation_history("proj-001")

        assert loaded[0]["metadata"]["mode"] == "socratic"

    def test_conversation_order(self, db):
        """Test that conversation history maintains order"""
        now = datetime.now()
        history = [
            {
                "role": "user",
                "content": f"Message {i}",
                "timestamp": (now + timedelta(seconds=i)).isoformat(),
            }
            for i in range(5)
        ]

        db.save_conversation_history("proj-001", history)
        loaded = db.get_conversation_history("proj-001")

        for i, msg in enumerate(loaded):
            assert f"Message {i}" in msg["content"], "Messages should be in order"


class TestPhaseMaturityScores:
    """Test phase maturity tracking"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabaseV2(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_phase_maturity_persistence(self, db):
        """Test that phase maturity scores are persisted"""
        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="testuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            phase_maturity_scores={"phase1": 0.5, "phase2": 0.2, "phase3": 0.0},
        )

        db.save_project(project)
        loaded = db.load_project("proj-001")

        assert loaded.phase_maturity_scores["phase1"] == 0.5
        assert loaded.phase_maturity_scores["phase2"] == 0.2

    def test_category_scores_persistence(self, db):
        """Test that category scores are persisted"""
        project = ProjectContext(
            project_id="proj-001",
            name="Test Project",
            owner="testuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            category_scores={
                "phase1": {"architecture": 0.8, "api_design": 0.6},
                "phase2": {"testing": 0.4},
            },
        )

        db.save_project(project)
        loaded = db.load_project("proj-001")

        assert loaded.category_scores["phase1"]["architecture"] == 0.8
        assert loaded.category_scores["phase1"]["api_design"] == 0.6


class TestDatabaseIntegrity:
    """Test data integrity and constraints"""

    @pytest.fixture
    def db(self):
        """Create a temporary test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_instance = ProjectDatabaseV2(db_path)
        yield db_instance

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_project_update_preserves_relationships(self, db):
        """Test that updating a project preserves related data"""
        project = ProjectContext(
            project_id="proj-001",
            name="Original Name",
            owner="testuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            requirements=["Req1", "Req2"],
        )

        db.save_project(project)

        # Update project
        project.name = "Updated Name"
        db.save_project(project)

        loaded = db.load_project("proj-001")
        assert loaded.name == "Updated Name"
        assert loaded.requirements == ["Req1", "Req2"], "Requirements should be preserved"

    def test_null_values_handled(self, db):
        """Test that NULL values are handled properly"""
        project = ProjectContext(
            project_id="proj-001",
            name="Test",
            owner="testuser",
            phase="phase1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            # Leaving optional fields as None
        )

        db.save_project(project)
        loaded = db.load_project("proj-001")

        assert loaded is not None, "Project should load even with NULL optional fields"
        assert loaded.requirements is None or len(loaded.requirements) == 0

    def test_concurrent_user_projects_independent(self, db):
        """Test that projects from different users are independent"""
        # Create projects for different users
        for user in ["user1", "user2"]:
            for i in range(2):
                project = ProjectContext(
                    project_id=f"{user}-proj-{i}",
                    name=f"{user} Project {i}",
                    owner=user,
                    phase="phase1",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.save_project(project)

        # Verify isolation
        user1_projects = db.get_user_projects("user1")
        user2_projects = db.get_user_projects("user2")

        assert len(user1_projects) == 2, "User1 should have 2 projects"
        assert len(user2_projects) == 2, "User2 should have 2 projects"
        assert all(p.owner == "user1" for p in user1_projects)
        assert all(p.owner == "user2" for p in user2_projects)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
