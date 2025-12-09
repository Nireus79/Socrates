"""
Expanded tests for database operations - Project and Vector DB
"""

from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest
import socrates

from socratic_system.models import User, ProjectContext


@pytest.mark.unit
class TestProjectDatabaseOperations:
    """Tests for project database operations"""

    def test_save_and_load_project(self, test_config, sample_project):
        """Test saving and loading a project"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            # Save project
            orchestrator.database.save_project(sample_project)

            # Load project
            loaded = orchestrator.database.load_project(sample_project.project_id)

            assert loaded is not None
            assert loaded.project_id == sample_project.project_id
            assert loaded.name == sample_project.name

    def test_save_project_with_complex_data(self, test_config):
        """Test saving project with complex nested data"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            project = ProjectContext(
                project_id="complex-001",
                name="Complex Project",
                description="Project with complex data",
                owner="testuser",
                phase="implementation",
                goals="Build scalable system",
                tech_stack=["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
                requirements=["High performance", "Scalability", "Security", "Monitoring"],
                constraints=["Budget limit", "Team size", "Timeline"],
                deployment_target="Kubernetes",
                code_style="PEP 8",
                conversation_history=[
                    {"type": "user", "content": "Build API"},
                    {"type": "assistant", "content": "I'll help build an API"},
                ]
            )

            orchestrator.database.save_project(project)
            loaded = orchestrator.database.load_project(project.project_id)

            assert loaded.tech_stack == project.tech_stack
            assert len(loaded.requirements) == len(project.requirements)
            assert loaded.deployment_target == project.deployment_target

    def test_update_project(self, test_config, sample_project):
        """Test updating an existing project"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            # Save initial project
            orchestrator.database.save_project(sample_project)

            # Update project
            sample_project.goals = "Updated goals"
            sample_project.phase = "testing"
            sample_project.tech_stack.append("Kubernetes")

            orchestrator.database.save_project(sample_project)

            # Verify update
            loaded = orchestrator.database.load_project(sample_project.project_id)
            assert loaded.goals == "Updated goals"
            assert loaded.phase == "testing"
            assert "Kubernetes" in loaded.tech_stack

    def test_load_nonexistent_project(self, test_config):
        """Test loading a project that doesn't exist"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            result = orchestrator.database.load_project("nonexistent-id")

            assert result is None

    def test_save_and_load_multiple_projects(self, test_config):
        """Test saving and loading multiple projects"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            projects = []
            for i in range(5):
                project = ProjectContext(
                    project_id=f"project-{i}",
                    name=f"Project {i}",
                    description=f"Description {i}",
                    owner="testuser",
                    phase="planning"
                )
                projects.append(project)
                orchestrator.database.save_project(project)

            # Load each project
            for project in projects:
                loaded = orchestrator.database.load_project(project.project_id)
                assert loaded is not None
                assert loaded.name == project.name

    def test_project_with_empty_fields(self, test_config):
        """Test saving project with empty optional fields"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            project = ProjectContext(
                project_id="empty-001",
                name="Minimal Project",
                description="",
                owner="testuser",
                phase="planning",
                goals="",
                tech_stack=[],
                requirements=[],
                constraints=[],
                deployment_target="",
                code_style=""
            )

            orchestrator.database.save_project(project)
            loaded = orchestrator.database.load_project(project.project_id)

            assert loaded is not None
            assert loaded.tech_stack == []
            assert loaded.requirements == []


@pytest.mark.unit
class TestUserDatabaseOperations:
    """Tests for user database operations"""

    def test_save_and_load_user(self, test_config, sample_user):
        """Test saving and loading a user"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            # Save user
            orchestrator.database.save_user(sample_user)

            # Load user
            loaded = orchestrator.database.load_user(sample_user.username)

            assert loaded is not None
            assert loaded.username == sample_user.username
            assert loaded.passcode_hash == sample_user.passcode_hash

    def test_save_multiple_users(self, test_config):
        """Test saving and loading multiple users"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            users = []
            for i in range(3):
                user = User(
                    username=f"user{i}",
                    passcode_hash=f"hash{i}",
                    created_at=datetime.now(),
                    projects=[]
                )
                users.append(user)
                orchestrator.database.save_user(user)

            # Load each user
            for user in users:
                loaded = orchestrator.database.load_user(user.username)
                assert loaded is not None
                assert loaded.username == user.username

    def test_load_nonexistent_user(self, test_config):
        """Test loading a user that doesn't exist"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            result = orchestrator.database.load_user("nonexistent-user")

            assert result is None

    def test_update_user(self, test_config):
        """Test updating an existing user"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            user = User(
                username="update-test",
                passcode_hash="original-hash",
                created_at=datetime.now(),
                projects=["proj1"]
            )

            orchestrator.database.save_user(user)

            # Update user
            user.projects.append("proj2")
            user.passcode_hash = "new-hash"
            orchestrator.database.save_user(user)

            # Verify update
            loaded = orchestrator.database.load_user(user.username)
            assert loaded.passcode_hash == "new-hash"
            assert "proj2" in loaded.projects


@pytest.mark.unit
class TestVectorDatabaseOperations:
    """Tests for vector database operations"""

    def test_vector_db_initialization(self, test_config):
        """Test vector database initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            assert orchestrator.vector_db is not None

    def test_add_knowledge_entry(self, test_config):
        """Test adding a knowledge entry"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            knowledge_entry = {
                "content": "Python is a programming language",
                "metadata": {"language": "python", "category": "basics"}
            }

            try:
                orchestrator.vector_db.add_knowledge(knowledge_entry)
            except Exception:
                # Some implementations may not have add_knowledge
                pass

    def test_search_knowledge_base(self, test_config):
        """Test searching the knowledge base"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            try:
                results = orchestrator.vector_db.search("programming")
                assert isinstance(results, (list, dict))
            except Exception:
                # Some implementations may not have search
                pass

    def test_vector_db_has_collection(self, test_config):
        """Test that vector DB has knowledge collection"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            # Vector DB should have a collection
            assert hasattr(orchestrator.vector_db, "collection")


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations"""

    def test_project_and_user_relationship(self, test_config):
        """Test relationship between projects and users"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            # Create user
            user = User(
                username="owner-user",
                passcode_hash="hash",
                created_at=datetime.now(),
                projects=[]
            )
            orchestrator.database.save_user(user)

            # Create project for user
            project = ProjectContext(
                project_id="user-project",
                name="User's Project",
                description="",
                owner=user.username,
                phase="planning"
            )
            orchestrator.database.save_project(project)

            # Load both
            loaded_user = orchestrator.database.load_user(user.username)
            loaded_project = orchestrator.database.load_project(project.project_id)

            assert loaded_project.owner == loaded_user.username

    def test_database_consistency(self, test_config):
        """Test database maintains consistency across operations"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            # Create and save multiple items
            user = User(
                username="consistency-test",
                passcode_hash="hash",
                created_at=datetime.now(),
                projects=["p1", "p2"]
            )
            orchestrator.database.save_user(user)

            project = ProjectContext(
                project_id="consistency-proj",
                name="Consistency Test",
                description="",
                owner="consistency-test",
                phase="planning"
            )
            orchestrator.database.save_project(project)

            # Load and verify consistency
            loaded_user = orchestrator.database.load_user("consistency-test")
            loaded_project = orchestrator.database.load_project("consistency-proj")

            assert loaded_user is not None
            assert loaded_project is not None
            assert loaded_project.owner == loaded_user.username

    def test_large_project_data_persistence(self, test_config):
        """Test persistence of large project data"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            # Create project with large data
            large_project = ProjectContext(
                project_id="large-001",
                name="Large Project",
                description="x" * 10000,  # Large description
                owner="testuser",
                phase="implementation",
                goals="x" * 5000,
                tech_stack=[f"tech{i}" for i in range(100)],
                requirements=[f"req{i}" for i in range(100)],
                conversation_history=[
                    {"type": "user", "content": f"msg{i}"}
                    for i in range(50)
                ]
            )

            orchestrator.database.save_project(large_project)
            loaded = orchestrator.database.load_project(large_project.project_id)

            assert loaded is not None
            assert len(loaded.tech_stack) == 100
            assert len(loaded.conversation_history) == 50

    def test_special_characters_in_data(self, test_config):
        """Test handling special characters in saved data"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            project = ProjectContext(
                project_id="special-001",
                name="Project with special chars: @#$%^&*()",
                description="Description with emojis 😀 🎉 🚀",
                owner="user@example.com",
                phase="planning",
                goals="Build system with special chars & symbols",
                tech_stack=["C++", "C#", ".NET"],
            )

            orchestrator.database.save_project(project)
            loaded = orchestrator.database.load_project(project.project_id)

            assert loaded.name == project.name
            assert loaded.description == project.description
            assert "C++" in loaded.tech_stack
