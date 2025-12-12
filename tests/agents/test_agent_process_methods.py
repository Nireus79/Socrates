"""
Tests for Agent process methods - Core agent functionality.

Tests cover:
- Agent initialization
- Process method for different actions
- Request validation
- Response handling
- Error conditions
"""

import datetime
from unittest.mock import MagicMock

import pytest

from socratic_system.agents.code_generator import CodeGeneratorAgent
from socratic_system.agents.context_analyzer import ContextAnalyzerAgent
from socratic_system.agents.project_manager import ProjectManagerAgent
from socratic_system.agents.socratic_counselor import SocraticCounselorAgent
from socratic_system.models import ProjectContext, User


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator."""
    orchestrator = MagicMock()
    orchestrator.database = MagicMock()
    orchestrator.claude_client = MagicMock()
    orchestrator.vector_db = MagicMock()
    return orchestrator


@pytest.fixture
def sample_project():
    """Create a sample project."""
    return ProjectContext(
        project_id="proj-123",
        name="Test Project",
        owner="testuser",
        collaborators=[],
        goals="Build a web application",
        requirements=["requirement1", "requirement2"],
        tech_stack=["python", "django"],
        constraints=["time constraint"],
        team_structure="individual",
        language_preferences="python",
        deployment_target="cloud",
        code_style="documented",
        phase="design",
        conversation_history=[
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "assistant",
                "content": "What are the goals?",
                "phase": "design",
            },
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "user",
                "content": "Build an app",
                "phase": "design",
            },
        ],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )


@pytest.fixture
def sample_user():
    """Create a sample user."""
    return User(
        username="testuser",
        passcode_hash="hash123",
        created_at=datetime.datetime.now(),
        projects=["proj-123"],
    )


class TestSocraticCounselorAgent:
    """Tests for SocraticCounselorAgent."""

    @pytest.fixture
    def agent(self, mock_orchestrator):
        """Create a SocraticCounselorAgent."""
        return SocraticCounselorAgent(mock_orchestrator)

    def test_agent_initialization(self, agent, mock_orchestrator):
        """Test agent initializes correctly."""
        assert agent is not None
        assert agent.orchestrator == mock_orchestrator
        assert agent.name == "SocraticCounselor"

    def test_process_generate_question(self, agent, sample_project, sample_user):
        """Test processing generate_question request."""
        mock_response = "What are your primary goals for this project?"
        agent.orchestrator.claude_client.generate_socratic_question.return_value = mock_response

        # Mock the user load to return a proper user object
        sample_user.questions_used_this_month = 0
        agent.orchestrator.database.load_user.return_value = sample_user

        request = {
            "action": "generate_question",
            "project": sample_project,
            "context": "Design phase",
            "current_user": "testuser",
        }

        result = agent.process(request)

        assert result is not None
        assert isinstance(result, dict)

    def test_process_analyze_response(self, agent, sample_project):
        """Test processing analyze_response request."""
        mock_insights = {"goals": "Build an app", "requirements": ["req1"]}
        agent.orchestrator.claude_client.extract_insights.return_value = mock_insights

        request = {
            "action": "analyze_response",
            "user_response": "I want to build a web app",
            "project": sample_project,
        }

        result = agent.process(request)

        assert result is not None
        assert isinstance(result, dict)

    def test_process_unknown_action(self, agent, sample_project):
        """Test processing unknown action."""
        request = {"action": "unknown_action", "project": sample_project}

        result = agent.process(request)

        assert result["status"] == "error"

    def test_process_missing_project(self, agent, sample_user):
        """Test processing request without project."""
        # Setup mock user with required attributes
        sample_user.questions_used_this_month = 0
        agent.orchestrator.database.load_user.return_value = sample_user

        request = {"action": "generate_question", "current_user": "testuser"}

        result = agent.process(request)

        # Should return error because project is missing
        assert result["status"] == "error"


class TestCodeGeneratorAgent:
    """Tests for CodeGeneratorAgent."""

    @pytest.fixture
    def agent(self, mock_orchestrator):
        """Create a CodeGeneratorAgent."""
        return CodeGeneratorAgent(mock_orchestrator)

    def test_agent_initialization(self, agent, mock_orchestrator):
        """Test agent initializes correctly."""
        assert agent is not None
        assert agent.orchestrator == mock_orchestrator
        assert agent.name == "CodeGenerator"

    def test_process_generate_code(self, agent, sample_project):
        """Test processing generate_code request."""
        mock_code = "print('Hello, world!')"
        agent.orchestrator.claude_client.generate_code.return_value = mock_code

        request = {
            "action": "generate_code",
            "project": sample_project,
            "context": "Generate a simple script",
        }

        result = agent.process(request)

        assert result is not None
        assert isinstance(result, dict)

    def test_process_generate_documentation(self, agent, sample_project):
        """Test processing generate_documentation request."""
        mock_docs = "# Project Documentation\n..."
        agent.orchestrator.claude_client.generate_documentation.return_value = mock_docs

        request = {
            "action": "generate_documentation",
            "project": sample_project,
            "code": "def hello(): pass",
        }

        result = agent.process(request)

        assert result is not None

    def test_process_missing_project(self, agent):
        """Test processing request without project."""
        request = {"action": "generate_code"}

        result = agent.process(request)

        assert result["status"] == "error"


class TestProjectManagerAgent:
    """Tests for ProjectManagerAgent."""

    @pytest.fixture
    def agent(self, mock_orchestrator):
        """Create a ProjectManagerAgent."""
        return ProjectManagerAgent(mock_orchestrator)

    def test_agent_initialization(self, agent, mock_orchestrator):
        """Test agent initializes correctly."""
        assert agent is not None
        assert agent.orchestrator == mock_orchestrator
        assert agent.name == "ProjectManager"

    def test_process_create_project(self, agent, sample_user):
        """Test processing create_project request."""
        mock_orchestrator = agent.orchestrator
        mock_orchestrator.database.load_user.return_value = sample_user
        mock_orchestrator.database.get_user_projects.return_value = []

        request = {
            "action": "create_project",
            "project_name": "New Project",
            "owner": "testuser",
            "project_type": "software",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        assert result["project"] is not None

    def test_process_load_project(self, agent, sample_project):
        """Test processing load_project request."""
        agent.orchestrator.database.load_project.return_value = sample_project

        request = {"action": "load_project", "project_id": "proj-123"}

        result = agent.process(request)

        assert result["status"] == "success"
        assert result["project"] == sample_project

    def test_process_save_project(self, agent, sample_project):
        """Test processing save_project request."""
        agent.orchestrator.database.save_project.return_value = None

        request = {"action": "save_project", "project": sample_project}

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_list_projects(self, agent, sample_project):
        """Test processing list_projects request."""
        agent.orchestrator.database.get_user_projects.return_value = [sample_project]

        request = {"action": "list_projects", "username": "testuser"}

        result = agent.process(request)

        assert result["status"] == "success"
        assert len(result["projects"]) >= 1

    def test_process_unknown_action(self, agent):
        """Test processing unknown action."""
        request = {"action": "unknown_action"}

        result = agent.process(request)

        assert result["status"] == "error"


class TestContextAnalyzerAgent:
    """Tests for ContextAnalyzerAgent."""

    @pytest.fixture
    def agent(self, mock_orchestrator):
        """Create a ContextAnalyzerAgent."""
        return ContextAnalyzerAgent(mock_orchestrator)

    def test_agent_initialization(self, agent, mock_orchestrator):
        """Test agent initializes correctly."""
        assert agent is not None
        assert agent.orchestrator == mock_orchestrator
        assert agent.name == "ContextAnalyzer"

    def test_process_analyze_context(self, agent, sample_project):
        """Test processing analyze_context request."""
        request = {"action": "analyze_context", "project": sample_project}

        result = agent.process(request)

        assert result is not None
        assert isinstance(result, dict)

    def test_process_get_statistics(self, agent, sample_project):
        """Test processing get_statistics request."""
        request = {"action": "get_statistics", "project": sample_project}

        result = agent.process(request)

        assert result is not None

    def test_process_unknown_action(self, agent, sample_project):
        """Test processing unknown action."""
        request = {"action": "unknown_action", "project": sample_project}

        result = agent.process(request)

        assert result["status"] == "error"


class TestAgentLogging:
    """Tests for agent logging functionality."""

    def test_agent_has_logger(self, mock_orchestrator):
        """Test agents have logging configured."""
        agent = SocraticCounselorAgent(mock_orchestrator)

        # All agents should have log method from base class
        assert hasattr(agent, "log")
        assert callable(agent.log)

    def test_agent_logging_works(self, mock_orchestrator):
        """Test agent can log messages."""
        agent = SocraticCounselorAgent(mock_orchestrator)

        # Should not raise error
        agent.log("Test message")


class TestAgentErrorHandling:
    """Tests for agent error handling."""

    def test_process_with_exception(self, mock_orchestrator, sample_user):
        """Test agent handles exceptions in process."""
        agent = SocraticCounselorAgent(mock_orchestrator)
        mock_orchestrator.database.load_user.return_value = sample_user
        agent.orchestrator.claude_client.generate_socratic_question.side_effect = Exception(
            "API Error"
        )

        request = {
            "action": "generate_question",
            "project": ProjectContext(
                project_id="p1",
                name="Test",
                owner="user",
                collaborators=[],
                goals="",
                requirements=[],
                tech_stack=[],
                constraints=[],
                team_structure="individual",
                language_preferences="python",
                deployment_target="local",
                code_style="documented",
                phase="discovery",
                conversation_history=[],
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now(),
            ),
            "current_user": "testuser",
        }

        result = agent.process(request)

        # Should handle error gracefully
        assert result is not None

    def test_invalid_request_data(self, mock_orchestrator):
        """Test agent handles invalid request data."""
        agent = ProjectManagerAgent(mock_orchestrator)

        # Missing required fields
        request = {"action": "create_project"}

        result = agent.process(request)

        assert result["status"] == "error"


class TestAgentIntegration:
    """Integration tests for agents working together."""

    def test_project_creation_workflow(self, mock_orchestrator, sample_user):
        """Test project creation workflow using ProjectManagerAgent."""
        manager = ProjectManagerAgent(mock_orchestrator)
        mock_orchestrator.database.load_user.return_value = sample_user
        mock_orchestrator.database.get_user_projects.return_value = []

        # Create project
        request = {
            "action": "create_project",
            "project_name": "New Workflow Project",
            "owner": "testuser",
            "project_type": "software",
        }

        result = manager.process(request)

        assert result["status"] == "success"
        created_project = result["project"]
        assert created_project.name == "New Workflow Project"

    def test_project_analysis_workflow(self, mock_orchestrator, sample_project):
        """Test project analysis workflow using ContextAnalyzerAgent."""
        analyzer = ContextAnalyzerAgent(mock_orchestrator)

        # Analyze project
        request = {"action": "analyze_context", "project": sample_project}

        result = analyzer.process(request)

        assert result is not None
        assert isinstance(result, dict)

    def test_code_generation_workflow(self, mock_orchestrator, sample_project):
        """Test code generation workflow using CodeGeneratorAgent."""
        code_gen = CodeGeneratorAgent(mock_orchestrator)
        mock_orchestrator.claude_client.generate_code.return_value = (
            "# Generated code\nprint('hello')"
        )

        # Generate code
        request = {
            "action": "generate_code",
            "project": sample_project,
            "context": "Generate starter code",
        }

        result = code_gen.process(request)

        assert result is not None


class TestAgentRequestValidation:
    """Tests for request validation in agents."""

    def test_socratic_counselor_requires_project(self, mock_orchestrator):
        """Test SocraticCounselorAgent requires project."""
        agent = SocraticCounselorAgent(mock_orchestrator)

        request = {"action": "generate_question"}

        result = agent.process(request)

        assert result["status"] == "error"

    def test_code_generator_requires_project(self, mock_orchestrator):
        """Test CodeGeneratorAgent requires project."""
        agent = CodeGeneratorAgent(mock_orchestrator)

        request = {"action": "generate_code"}

        result = agent.process(request)

        assert result["status"] == "error"

    def test_project_manager_handles_missing_user(self, mock_orchestrator):
        """Test ProjectManagerAgent auto-creates missing user on project creation."""
        agent = ProjectManagerAgent(mock_orchestrator)
        mock_orchestrator.database.load_user.return_value = None

        request = {
            "action": "create_project",
            "project_name": "Test",
            "owner": "nonexistent",
            "project_type": "software",
        }

        result = agent.process(request)

        # System should auto-create user and succeed
        assert result["status"] == "success"
        # Verify save_user was called to create the user
        assert mock_orchestrator.database.save_user.called


class TestAgentDataTransformation:
    """Tests for data transformation in agents."""

    def test_project_manager_transforms_response(self, mock_orchestrator, sample_project):
        """Test ProjectManagerAgent transforms responses correctly."""
        agent = ProjectManagerAgent(mock_orchestrator)
        mock_orchestrator.database.load_project.return_value = sample_project

        request = {"action": "load_project", "project_id": "proj-123"}

        result = agent.process(request)

        assert "project" in result
        assert result["project"].project_id == "proj-123"

    def test_context_analyzer_provides_context(self, mock_orchestrator, sample_project):
        """Test ContextAnalyzerAgent provides project context."""
        agent = ContextAnalyzerAgent(mock_orchestrator)

        request = {"action": "analyze_context", "project": sample_project}

        result = agent.process(request)

        assert result is not None
        assert isinstance(result, dict)
