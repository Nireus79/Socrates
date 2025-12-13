"""
End-to-End Test Suite for Socratic RAG System

Tests all commands and workflows in realistic scenarios
"""

import os
import shutil
import sys
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Fix Windows console encoding issues (only when NOT in PyCharm IDE)
# Detecting PyCharm to avoid interfering with its console
_is_pycharm_ide = sys.stdout.__class__.__name__ == "PyCharmOutput" or hasattr(sys.stdout, "_stream")
if sys.platform == "win32" and not _is_pycharm_ide:
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from socratic_system.models import ProjectContext, ProjectNote, User
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.ui.command_handler import CommandHandler
from socratic_system.ui.commands import (
    ClearCommand,
    CollabAddCommand,
    CollabListCommand,
    CollabRemoveCommand,
    ConvSearchCommand,
    ConvSummaryCommand,
    ExitCommand,
    HelpCommand,
    NoteAddCommand,
    NoteDeleteCommand,
    NoteListCommand,
    NoteSearchCommand,
    ProjectArchiveCommand,
    ProjectCreateCommand,
    ProjectListCommand,
    ProjectLoadCommand,
    ProjectProgressCommand,
    ProjectRestoreCommand,
    ProjectStatsCommand,
    ProjectStatusCommand,
    StatusCommand,
    UserCreateCommand,
    UserLoginCommand,
    UserLogoutCommand,
)
from socratic_system.ui.context_display import ContextDisplay
from socratic_system.ui.main_app import SocraticRAGSystem
from socratic_system.ui.navigation import NavigationStack


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for testing"""
    temp_dir = tempfile.mkdtemp()
    os.environ["SOCRATES_DATA_DIR"] = temp_dir
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def orchestrator(temp_data_dir):
    """Initialize orchestrator with test database (fresh for each test)"""
    # Mock API key for testing
    with patch.dict(os.environ, {"API_KEY_CLAUDE": "test-key", "SOCRATES_DATA_DIR": temp_data_dir}):
        with patch("socratic_system.orchestration.orchestrator.ClaudeClient"):
            with patch("socratic_system.orchestration.orchestrator.VectorDatabase"):
                from socratic_system.config import SocratesConfig
                config = SocratesConfig.from_env()
                orch = AgentOrchestrator(config)
                orch.claude_client = MagicMock()
                orch.claude_client.generate_response = MagicMock(return_value="Test response")
                orch.claude_client.generate_suggestions = MagicMock(return_value="Test suggestions")

                # Clear all data before test
                orch.database.users = {}
                orch.database.projects = {}
                orch.database.notes = {}

                yield orch


@pytest.fixture
def app(orchestrator):
    """Initialize app with test orchestrator"""
    app = SocraticRAGSystem()
    app.orchestrator = orchestrator
    app.command_handler = CommandHandler()
    app.nav_stack = NavigationStack()
    app.context_display = ContextDisplay()
    app._register_commands()
    return app


class TestUserAuthenticationWorkflow:
    """Test user login, registration, and account management"""

    def test_user_create_command(self, app):
        """Test creating a new user account"""
        cmd = UserCreateCommand()

        username = f"testuser_{id(app)}"  # Unique username per test run
        with patch("builtins.input", side_effect=[username, "password123", "password123"]):
            result = cmd.execute([], {"orchestrator": app.orchestrator, "app": app})

        assert result["status"] == "success", f"Error: {result.get('message', 'Unknown error')}"
        assert app.current_user is not None
        assert app.current_user.username == username
        print("✓ User account creation works")

    def test_user_login_command(self, app):
        """Test user login"""
        # First create a user with unique username
        import hashlib

        username = f"logintest_{id(app)}"
        passcode_hash = hashlib.sha256(b"password123").hexdigest()
        user = User(
            username=username, passcode_hash=passcode_hash, created_at=datetime.now(), projects=[]
        )
        app.orchestrator.database.save_user(user)

        cmd = UserLoginCommand()

        with patch("builtins.input", side_effect=[username, "password123"]):
            result = cmd.execute([], {"orchestrator": app.orchestrator, "app": app})

        assert result["status"] == "success", f"Error: {result.get('message', 'Unknown error')}"
        assert app.current_user is not None
        assert app.current_user.username == username
        print("✓ User login works")

    def test_user_logout_command(self, app):
        """Test user logout"""
        app.current_user = User(
            username="testuser", passcode_hash="test", created_at=datetime.now(), projects=[]
        )
        app.current_project = None

        cmd = UserLogoutCommand()
        result = cmd.execute([], {"app": app})

        assert result["status"] == "success"
        assert app.current_user is None
        print("✓ User logout works")


class TestProjectManagementWorkflow:
    """Test project creation, loading, and management"""

    def setup_authenticated_user(self, app):
        """Helper to set up authenticated user"""
        user = User(
            username="projecttest",
            passcode_hash="hash",
            created_at=datetime.now(),
            projects=[],
            subscription_tier="pro",  # Pro tier allows multiple projects
        )
        app.orchestrator.database.save_user(user)
        app.current_user = user
        app.context_display.set_context(user=user)
        return user

    def test_project_create_command(self, app):
        """Test creating a new project"""
        self.setup_authenticated_user(app)

        cmd = ProjectCreateCommand()

        with patch("builtins.input", side_effect=["1"]):  # Select project type 1
            result = cmd.execute(
                ["Test Project"],
                {"orchestrator": app.orchestrator, "user": app.current_user, "app": app},
            )

        assert result["status"] == "success"
        assert app.current_project is not None
        assert app.current_project.name == "Test Project"
        print("✓ Project creation works")

    def test_project_list_command(self, app):
        """Test listing projects"""
        user = self.setup_authenticated_user(app)

        # Create a test project
        cmd_create = ProjectCreateCommand()
        with patch("builtins.input", side_effect=["1"]):  # Select project type 1
            cmd_create.execute(
                ["Project 1"], {"orchestrator": app.orchestrator, "user": user, "app": app}
            )

        cmd_list = ProjectListCommand()
        result = cmd_list.execute([], {"orchestrator": app.orchestrator, "user": user})

        assert result["status"] == "success"
        print("✓ Project listing works")

    def test_project_load_command(self, app):
        """Test loading a project"""
        user = self.setup_authenticated_user(app)

        # Create and save a project with unique name
        project_name = f"Load Test {id(app)}"
        cmd_create = ProjectCreateCommand()
        with patch("builtins.input", side_effect=["1"]):  # Select project type 1
            cmd_create.execute(
                [project_name], {"orchestrator": app.orchestrator, "user": user, "app": app}
            )

        project_id = app.current_project.project_id
        app.current_project = None

        # Get the list of projects to find the right option number
        projects = app.orchestrator.database.get_user_projects(
            user.username, include_archived=False
        )
        project_option = None
        for i, proj_data in enumerate(projects, 1):
            # proj_data might be a dict or ProjectContext object
            proj_id = (
                proj_data.get("project_id") if isinstance(proj_data, dict) else proj_data.project_id
            )
            if proj_id == project_id:
                project_option = str(i)
                break

        assert project_option is not None, f"Project {project_name} not found in user's projects"

        # Now load it
        cmd_load = ProjectLoadCommand()
        with patch("builtins.input", return_value=project_option):
            result = cmd_load.execute(
                [], {"orchestrator": app.orchestrator, "user": user, "app": app, "project": None}
            )

        assert result["status"] == "success", f"Error: {result.get('message', 'Unknown error')}"
        assert app.current_project is not None
        assert app.current_project.project_id == project_id
        print("✓ Project loading works")


class TestNotesSystemWorkflow:
    """Test notes creation, listing, searching, and deletion"""

    def setup_project_with_user(self, app):
        """Helper to set up user and project"""
        # Use unique IDs to avoid test isolation issues
        test_id = id(app)
        username = f"notestest_{test_id}"
        user = User(
            username=username,
            passcode_hash="hash",
            created_at=datetime.now(),
            projects=[],
            subscription_tier="pro",  # Pro tier allows multiple projects
        )
        app.orchestrator.database.save_user(user)
        app.current_user = user

        # Create project with unique ID
        project_id = f"proj-notes-test-{test_id}"
        project = ProjectContext(
            project_id=project_id,
            name="Notes Test Project",
            owner=username,
            collaborators=[],
            goals="Test notes",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="Solo",
            language_preferences="English",
            deployment_target="Cloud",
            code_style="PEP8",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        app.orchestrator.database.save_project(project)
        app.current_project = project
        app.context_display.set_context(user=user, project=project)

        return user, project

    def test_note_add_command(self, app):
        """Test adding a note"""
        user, project = self.setup_project_with_user(app)

        cmd = NoteAddCommand()

        # Note: needs empty lines to terminate multi-line input
        with patch(
            "builtins.input",
            side_effect=[
                "design",
                "Database Schema",
                "",
                "Need to design the database schema for user management",
                "",
                "",
            ],
        ):
            result = cmd.execute(
                [], {"orchestrator": app.orchestrator, "project": project, "user": user}
            )

        assert result["status"] == "success", f"Error: {result.get('message', 'Unknown error')}"
        assert result["data"]["note"]["title"] == "Database Schema"
        print("✓ Note addition works")

    def test_note_list_command(self, app):
        """Test listing notes"""
        user, project = self.setup_project_with_user(app)

        # Add a note first
        note = ProjectNote.create(
            project_id=project.project_id,
            note_type="design",
            title="Test Note",
            content="This is a test note",
            created_by=user.username,
        )
        app.orchestrator.database.save_note(note)

        cmd = NoteListCommand()
        result = cmd.execute([], {"orchestrator": app.orchestrator, "project": project})

        assert result["status"] == "success"
        assert len(result["data"]["notes"]) == 1
        print("✓ Note listing works")

    def test_note_search_command(self, app):
        """Test searching notes"""
        user, project = self.setup_project_with_user(app)

        # Add test notes
        note1 = ProjectNote.create(
            project_id=project.project_id,
            note_type="design",
            title="Database Schema",
            content="Design the user database",
            created_by=user.username,
        )
        note2 = ProjectNote.create(
            project_id=project.project_id,
            note_type="bug",
            title="Login Bug",
            content="Fix authentication issue",
            created_by=user.username,
        )
        app.orchestrator.database.save_note(note1)
        app.orchestrator.database.save_note(note2)

        cmd = NoteSearchCommand()
        result = cmd.execute(["database"], {"orchestrator": app.orchestrator, "project": project})

        assert result["status"] == "success"
        assert len(result["data"]["results"]) >= 1
        print("✓ Note searching works")

    def test_note_delete_command(self, app):
        """Test deleting notes"""
        user, project = self.setup_project_with_user(app)

        # Add a note
        note = ProjectNote.create(
            project_id=project.project_id,
            note_type="idea",
            title="Delete Me",
            content="This note will be deleted",
            created_by=user.username,
        )
        app.orchestrator.database.save_note(note)

        cmd = NoteDeleteCommand()

        with patch("builtins.input", return_value="yes"):
            result = cmd.execute(
                [note.note_id], {"orchestrator": app.orchestrator, "project": project}
            )

        assert result["status"] == "success"
        print("✓ Note deletion works")


class TestConversationFeaturesWorkflow:
    """Test conversation search and summaries"""

    def setup_project_with_conversation(self, app):
        """Helper to set up project with conversation history"""
        user = User(
            username="convtest", passcode_hash="hash", created_at=datetime.now(), projects=[]
        )
        app.orchestrator.database.save_user(user)
        app.current_user = user

        conversation = [
            {
                "role": "assistant",
                "content": "What are your main project goals?",
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
            },
            {
                "role": "user",
                "content": "We want to build a REST API for user management",
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
            },
            {
                "role": "assistant",
                "content": "What technologies do you plan to use?",
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
            },
            {
                "role": "user",
                "content": "Python with FastAPI and PostgreSQL",
                "timestamp": datetime.now().isoformat(),
                "phase": "discovery",
            },
        ]

        project = ProjectContext(
            project_id="proj-conv-test",
            name="Conv Test Project",
            owner="convtest",
            collaborators=[],
            goals="Build a REST API",
            requirements=["User authentication", "CRUD operations"],
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            constraints=[],
            team_structure="Solo",
            language_preferences="English",
            deployment_target="Cloud",
            code_style="PEP8",
            phase="discovery",
            conversation_history=conversation,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        app.orchestrator.database.save_project(project)
        app.current_project = project
        app.context_display.set_context(user=user, project=project)

        return user, project

    def test_conversation_search_command(self, app):
        """Test searching conversation history"""
        user, project = self.setup_project_with_conversation(app)

        cmd = ConvSearchCommand()
        result = cmd.execute(["API"], {"orchestrator": app.orchestrator, "project": project})

        assert result["status"] == "success"
        assert result["data"]["count"] > 0
        print("✓ Conversation search works")

    def test_conversation_summary_command(self, app):
        """Test generating conversation summary"""
        user, project = self.setup_project_with_conversation(app)

        app.orchestrator.claude_client.generate_response = MagicMock(
            return_value="Summary: User wants to build a REST API using Python, FastAPI, and PostgreSQL"
        )

        cmd = ConvSummaryCommand()
        result = cmd.execute(["4"], {"orchestrator": app.orchestrator, "project": project})

        assert result["status"] == "success"
        assert "summary" in result["data"]
        print("✓ Conversation summary generation works")


class TestProjectStatisticsWorkflow:
    """Test statistics and progress tracking"""

    def setup_project_with_stats(self, app):
        """Helper to set up project with content for statistics"""
        user = User(
            username="statstest", passcode_hash="hash", created_at=datetime.now(), projects=[]
        )
        app.orchestrator.database.save_user(user)
        app.current_user = user

        project = ProjectContext(
            project_id="proj-stats-test",
            name="Stats Test Project",
            owner="statstest",
            collaborators=["collaborator1", "collaborator2"],
            goals="Test statistics",
            requirements=["Req 1", "Req 2", "Req 3"],
            tech_stack=["Python", "FastAPI"],
            constraints=["Budget limited"],
            team_structure="Team of 3",
            language_preferences="English",
            deployment_target="AWS",
            code_style="PEP8",
            phase="implementation",
            conversation_history=[
                {"role": "assistant", "content": "Question 1"},
                {"role": "user", "content": "Answer 1"},
                {"role": "assistant", "content": "Question 2"},
                {"role": "user", "content": "Answer 2"},
            ],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            progress=75,
            status="active",
        )
        app.orchestrator.database.save_project(project)
        app.current_project = project
        app.context_display.set_context(user=user, project=project)

        return user, project

    def test_project_stats_command(self, app):
        """Test viewing project statistics"""
        user, project = self.setup_project_with_stats(app)

        cmd = ProjectStatsCommand()
        result = cmd.execute([], {"orchestrator": app.orchestrator, "project": project})

        assert result["status"] == "success"
        stats = result["data"]["statistics"]
        assert stats["project_name"] == "Stats Test Project"
        assert stats["progress"] == 75
        assert stats["status"] == "active"
        assert stats["collaborators"] == 2
        print("✓ Project statistics display works")

    def test_project_progress_command(self, app):
        """Test updating project progress"""
        user, project = self.setup_project_with_stats(app)

        cmd = ProjectProgressCommand()
        result = cmd.execute(
            ["85"], {"orchestrator": app.orchestrator, "project": project, "app": app}
        )

        assert result["status"] == "success"
        assert result["data"]["progress"] == 85
        assert app.current_project.progress == 85
        print("✓ Project progress update works")

    def test_project_status_command(self, app):
        """Test updating project status"""
        user, project = self.setup_project_with_stats(app)

        cmd = ProjectStatusCommand()
        result = cmd.execute(
            ["completed"], {"orchestrator": app.orchestrator, "project": project, "app": app}
        )

        assert result["status"] == "success"
        assert result["data"]["status"] == "completed"
        assert app.current_project.status == "completed"
        print("✓ Project status update works")


class TestCollaborationWorkflow:
    """Test collaboration features"""

    def setup_project_with_users(self, app):
        """Helper to set up project and multiple users"""
        owner = User(
            username="owner",
            passcode_hash="hash",
            created_at=datetime.now(),
            projects=[],
            subscription_tier="pro",  # Pro tier allows team collaboration
        )
        collab = User(
            username="collaborator", passcode_hash="hash", created_at=datetime.now(), projects=[]
        )
        app.orchestrator.database.save_user(owner)
        app.orchestrator.database.save_user(collab)
        app.current_user = owner

        project = ProjectContext(
            project_id="proj-collab-test",
            name="Collab Test Project",
            owner="owner",
            collaborators=[],
            goals="Test collaboration",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="Solo",
            language_preferences="English",
            deployment_target="Cloud",
            code_style="PEP8",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        app.orchestrator.database.save_project(project)
        app.current_project = project
        app.context_display.set_context(user=owner, project=project)

        return owner, collab, project

    def test_collaborator_add_command(self, app):
        """Test adding a collaborator"""
        owner, collab, project = self.setup_project_with_users(app)

        cmd = CollabAddCommand()
        result = cmd.execute(
            ["collaborator"], {"orchestrator": app.orchestrator, "user": owner, "project": project}
        )

        assert result["status"] == "success"
        assert "collaborator" in app.current_project.collaborators
        print("✓ Collaborator addition works")

    def test_collaborator_list_command(self, app):
        """Test listing collaborators"""
        owner, collab, project = self.setup_project_with_users(app)

        # Add a collaborator first
        project.collaborators.append("collaborator")
        app.orchestrator.database.save_project(project)

        cmd = CollabListCommand()
        result = cmd.execute([], {"orchestrator": app.orchestrator, "project": project})

        assert result["status"] == "success"
        assert len(result["data"]["collaborators"]) >= 1
        print("✓ Collaborator listing works")

    def test_collaborator_remove_command(self, app):
        """Test removing a collaborator"""
        owner, collab, project = self.setup_project_with_users(app)

        # Add collaborator first
        project.collaborators.append("collaborator")
        app.orchestrator.database.save_project(project)

        cmd = CollabRemoveCommand()

        with patch("builtins.input", return_value="y"):
            result = cmd.execute(
                ["collaborator"],
                {"orchestrator": app.orchestrator, "user": owner, "project": project},
            )

        assert result["status"] == "success", f"Error: {result.get('message', 'Unknown error')}"
        # Reload project to verify removal
        reloaded_project = app.orchestrator.database.load_project(project.project_id)
        assert "collaborator" not in reloaded_project.collaborators
        print("✓ Collaborator removal works")


class TestProjectArchiveWorkflow:
    """Test project archival and restoration"""

    def setup_project_for_archive(self, app):
        """Helper to set up project for archival"""
        user = User(
            username="archivetest", passcode_hash="hash", created_at=datetime.now(), projects=[]
        )
        app.orchestrator.database.save_user(user)
        app.current_user = user

        project = ProjectContext(
            project_id="proj-archive-test",
            name="Archive Test",
            owner="archivetest",
            collaborators=[],
            goals="Test archive",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="Solo",
            language_preferences="English",
            deployment_target="Cloud",
            code_style="PEP8",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        app.orchestrator.database.save_project(project)
        app.current_project = project
        app.context_display.set_context(user=user, project=project)

        return user, project

    def test_project_archive_command(self, app):
        """Test archiving a project"""
        user, project = self.setup_project_for_archive(app)

        cmd = ProjectArchiveCommand()

        with patch("builtins.input", return_value="y"):
            result = cmd.execute(
                [], {"orchestrator": app.orchestrator, "user": user, "project": project, "app": app}
            )

        assert result["status"] == "success"
        print("✓ Project archival works")

    def test_project_restore_command(self, app):
        """Test restoring an archived project"""
        user, project = self.setup_project_for_archive(app)

        # Archive it first
        project.is_archived = True
        project.archived_at = datetime.now()
        app.orchestrator.database.save_project(project)

        cmd = ProjectRestoreCommand()

        with patch("builtins.input", side_effect=["1", "y"]):
            result = cmd.execute([], {"orchestrator": app.orchestrator, "user": user})

        assert result["status"] == "success"
        print("✓ Project restoration works")


class TestSystemCommands:
    """Test system-level commands"""

    def test_help_command(self, app):
        """Test help command"""
        cmd = HelpCommand()
        result = cmd.execute([], {"app": app})

        assert result["status"] == "success"
        print("✓ Help command works")

    def test_status_command(self, app):
        """Test status command"""
        cmd = StatusCommand()
        result = cmd.execute([], {"orchestrator": app.orchestrator})

        assert result["status"] == "success"
        print("✓ Status command works")

    def test_clear_command(self, app):
        """Test clear command"""
        cmd = ClearCommand()
        result = cmd.execute([], {})

        assert result["status"] == "success"
        print("✓ Clear command works")

    def test_exit_command(self, app):
        """Test exit command"""
        cmd = ExitCommand()
        result = cmd.execute([], {})

        assert result["status"] == "exit"
        print("✓ Exit command works")


class TestCompleteE2EWorkflow:
    """Complete end-to-end workflow test"""

    def test_full_user_project_workflow(self, app):
        """Test complete workflow: create user → project → notes → stats"""
        print("\n" + "=" * 60)
        print("COMPLETE END-TO-END WORKFLOW TEST")
        print("=" * 60)

        # 1. Create user
        print("\n1. Creating user account...")
        cmd_user = UserCreateCommand()
        e2e_username = f"e2euser_{id(app)}"
        with patch("builtins.input", side_effect=[e2e_username, "secure123", "secure123"]):
            result = cmd_user.execute([], {"orchestrator": app.orchestrator, "app": app})
        assert result["status"] == "success", f"Error: {result.get('message', 'Unknown error')}"
        print(f"   ✓ User created: {e2e_username}")

        # Upgrade user to pro tier for testing multiple features
        app.current_user.subscription_tier = "pro"
        app.orchestrator.database.save_user(app.current_user)

        # 2. Create project
        print("\n2. Creating project...")
        cmd_project = ProjectCreateCommand()
        with patch("builtins.input", side_effect=["1"]):  # Select project type 1
            result = cmd_project.execute(
                ["E2E Test Project"],
                {"orchestrator": app.orchestrator, "user": app.current_user, "app": app},
            )
        assert result["status"] == "success"
        print("   ✓ Project created: E2E Test Project")

        # 3. Add notes
        print("\n3. Adding project notes...")
        cmd_note = NoteAddCommand()
        # Need to provide: type, title, tags, content, empty, empty
        with patch(
            "builtins.input",
            side_effect=["design", "API Architecture", "", "Need to design REST API", "", ""],
        ):
            result = cmd_note.execute(
                [],
                {
                    "orchestrator": app.orchestrator,
                    "project": app.current_project,
                    "user": app.current_user,
                },
            )
        assert result["status"] == "success", f"Error: {result.get('message', 'Unknown error')}"
        print("   ✓ Note added: API Architecture")

        # 4. Add another note
        with patch(
            "builtins.input", side_effect=["bug", "Auth Issue", "", "Fix login validation", "", ""]
        ):
            result = cmd_note.execute(
                [],
                {
                    "orchestrator": app.orchestrator,
                    "project": app.current_project,
                    "user": app.current_user,
                },
            )
        assert result["status"] == "success", f"Error: {result.get('message', 'Unknown error')}"
        print("   ✓ Note added: Auth Issue")

        # 5. List notes
        print("\n4. Listing notes...")
        cmd_list_notes = NoteListCommand()
        result = cmd_list_notes.execute(
            [], {"orchestrator": app.orchestrator, "project": app.current_project}
        )
        assert result["status"] == "success"
        print(f"   ✓ Notes listed: {len(result['data']['notes'])} notes")

        # 6. Search notes
        print("\n5. Searching notes...")
        cmd_search = NoteSearchCommand()
        result = cmd_search.execute(
            ["API"], {"orchestrator": app.orchestrator, "project": app.current_project}
        )
        assert result["status"] == "success"
        print(f"   ✓ Search completed: {result['data']['count']} matches")

        # 7. Update progress
        print("\n6. Updating project progress...")
        cmd_progress = ProjectProgressCommand()
        result = cmd_progress.execute(
            ["50"], {"orchestrator": app.orchestrator, "project": app.current_project, "app": app}
        )
        assert result["status"] == "success"
        print("   ✓ Progress updated to 50%")

        # 8. Update status
        print("\n7. Updating project status...")
        cmd_status = ProjectStatusCommand()
        result = cmd_status.execute(
            ["active"],
            {"orchestrator": app.orchestrator, "project": app.current_project, "app": app},
        )
        assert result["status"] == "success"
        print("   ✓ Status set to active")

        # 9. View statistics
        print("\n8. Viewing project statistics...")
        cmd_stats = ProjectStatsCommand()
        result = cmd_stats.execute(
            [], {"orchestrator": app.orchestrator, "project": app.current_project}
        )
        assert result["status"] == "success"
        stats = result["data"]["statistics"]
        print("   ✓ Statistics displayed:")
        print(f"     - Project: {stats['project_name']}")
        print(f"     - Phase: {stats['current_phase']}")
        print(f"     - Progress: {stats['progress']}%")
        print(f"     - Status: {stats['status']}")
        print(f"     - Notes: {stats['notes']}")

        # 10. Add collaborator
        print("\n9. Adding collaborator...")
        # Create another user first
        collab_user = User(
            username="collaborator", passcode_hash="hash", created_at=datetime.now(), projects=[]
        )
        app.orchestrator.database.save_user(collab_user)

        cmd_collab = CollabAddCommand()
        result = cmd_collab.execute(
            ["collaborator"],
            {
                "orchestrator": app.orchestrator,
                "user": app.current_user,
                "project": app.current_project,
            },
        )
        assert result["status"] == "success"
        print("   ✓ Collaborator added: collaborator")

        # 11. List collaborators
        print("\n10. Listing collaborators...")
        cmd_list_collab = CollabListCommand()
        result = cmd_list_collab.execute(
            [], {"orchestrator": app.orchestrator, "project": app.current_project}
        )
        assert result["status"] == "success"
        print(f"   ✓ Collaborators: {len(result['data']['collaborators'])}")

        # 12. Save project
        print("\n11. Saving project...")
        app.orchestrator.database.save_project(app.current_project)
        print("   ✓ Project saved to database")

        # 13. Load project
        print("\n12. Loading project...")
        loaded_project = app.orchestrator.database.load_project(app.current_project.project_id)
        assert loaded_project is not None
        assert loaded_project.name == "E2E Test Project"
        print("   ✓ Project loaded successfully")

        print("\n" + "=" * 60)
        print("ALL E2E WORKFLOW TESTS PASSED!")
        print("=" * 60 + "\n")


class TestCommandValidation:
    """Test command syntax and validation rules"""

    def test_command_requires_slash_prefix(self, app):
        """Test that commands without / prefix are rejected"""
        # Commands without / should fail
        result = app.command_handler.execute("help", {})
        assert result["status"] == "error"
        assert "must start with" in result["message"].lower()

        result = app.command_handler.execute("project list", {})
        assert result["status"] == "error"
        assert "must start with" in result["message"].lower()

    def test_command_with_slash_prefix_works(self, app):
        """Test that commands with / prefix are accepted"""
        # Commands with / should be recognized as valid syntax
        # (though they might fail if app context is incomplete)
        result = app.command_handler.execute("/help", {"app": app})
        assert result["status"] != "error" or "must start with" not in result["message"].lower()

    def test_natural_language_not_treated_as_command(self, app):
        """Test that natural language input is not treated as commands"""
        # Regular text without / should be rejected as command
        result = app.command_handler.execute("Tell me about Python", {})
        assert result["status"] == "error"
        assert "must start with" in result["message"].lower()

        result = app.command_handler.execute("What is a design pattern?", {})
        assert result["status"] == "error"
        assert "must start with" in result["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
