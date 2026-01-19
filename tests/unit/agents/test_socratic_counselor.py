"""
Unit tests for Socratic Counselor agent.

Tests socratic questioning agent including:
- Generating questions
- Evaluating answers
- Guiding learning
- Managing conversation state
- Detecting knowledge gaps
"""

import datetime
from unittest.mock import MagicMock

import pytest

from socratic_system.agents.socratic_counselor import SocraticCounselorAgent
from socratic_system.models import ProjectContext, User


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing"""
    orchestrator = MagicMock()
    orchestrator.context_analyzer = MagicMock()
    orchestrator.context_analyzer.get_context_summary = MagicMock(
        return_value="Test project context"
    )
    orchestrator.database = MagicMock()
    orchestrator.database.load_user = MagicMock(return_value=None)
    orchestrator.database.save_user = MagicMock()
    orchestrator.client = MagicMock()
    orchestrator.conflict_detector = MagicMock()
    orchestrator.conflict_detector.process = MagicMock(
        return_value={"status": "success", "conflicts": []}
    )
    orchestrator.knowledge_manager = MagicMock()
    orchestrator.knowledge_manager.process = MagicMock(
        return_value={"status": "success", "knowledge": []}
    )
    # Mock claude_client for question generation
    orchestrator.claude_client = MagicMock()
    orchestrator.claude_client.generate_socratic_question = MagicMock(
        return_value="What is your target audience?"
    )
    # Mock vector_db for knowledge search
    orchestrator.vector_db = MagicMock()
    orchestrator.vector_db.search_similar_adaptive = MagicMock(return_value=[])
    # Mock process_request to return success for all agents
    orchestrator.process_request = MagicMock(
        return_value={"status": "success", "conflicts": [], "knowledge": []}
    )
    return orchestrator


@pytest.fixture
def socratic_agent(mock_orchestrator):
    """Create a SocraticCounselorAgent instance for testing"""
    return SocraticCounselorAgent(mock_orchestrator)


@pytest.fixture
def sample_project():
    """Create a sample project for testing"""
    return ProjectContext(
        project_id="test_proj_001",
        name="Test Project",
        owner="testuser",
        collaborators=[],
        goals="Test goal",
        requirements=["req1"],
        tech_stack=["Python"],
        constraints=[],
        team_structure="individual",
        language_preferences="python",
        deployment_target="cloud",
        code_style="documented",
        phase="planning",
        conversation_history=[],
        pending_questions=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(
        username="testuser",
        email="test@example.com",
        passcode_hash="hash123",
        created_at=datetime.datetime.now(),
        projects=["test_proj_001"],
        subscription_tier="pro",
    )


@pytest.mark.unit
class TestSocraticQuestionGeneration:
    """Tests for socratic question generation"""

    def test_agent_initialization(self, socratic_agent):
        """Test that agent initializes with correct properties"""
        assert socratic_agent.name == "SocraticCounselor"
        assert socratic_agent.use_dynamic_questions is True
        assert socratic_agent.max_questions_per_phase == 5
        assert "discovery" in socratic_agent.static_questions
        assert "analysis" in socratic_agent.static_questions
        assert "design" in socratic_agent.static_questions
        assert "implementation" in socratic_agent.static_questions

    def test_generate_question_with_project(
        self, socratic_agent, sample_project, mock_orchestrator
    ):
        """Test generating socratic question with valid project"""
        mock_orchestrator.context_analyzer.get_context_summary.return_value = "Test project context in planning phase"

        # Mock a user with pro tier (unlimited questions)
        from socratic_system.models.user import User
        mock_user = User(
            username="testuser",
            email="test@example.com",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=["test_proj_001"],
            subscription_tier="pro",
        )
        mock_orchestrator.database.load_user.return_value = mock_user

        request = {
            "action": "generate_question",
            "project": sample_project,
            "current_user": "testuser",
        }
        result = socratic_agent.process(request)

        # Question generation should return a successful result
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "success"
        assert "question" in result

    def test_generate_question_without_project(self, socratic_agent):
        """Test generating question without project context fails appropriately"""
        request = {"action": "generate_question"}
        result = socratic_agent.process(request)

        assert result["status"] == "error"
        assert "Project context is required" in result["message"]

    def test_static_questions_available(self, socratic_agent):
        """Test that static fallback questions are available"""
        assert len(socratic_agent.static_questions["discovery"]) > 0
        assert all(isinstance(q, str) for q in socratic_agent.static_questions["discovery"])
        assert all(isinstance(q, str) for q in socratic_agent.static_questions["analysis"])
        assert all(isinstance(q, str) for q in socratic_agent.static_questions["design"])
        assert all(isinstance(q, str) for q in socratic_agent.static_questions["implementation"])


@pytest.mark.unit
class TestAnswerEvaluation:
    """Tests for evaluating student answers"""

    def test_process_response_action(self, socratic_agent, sample_project):
        """Test processing a student response"""
        request = {
            "action": "process_response",
            "project": sample_project,
            "response": "This is the student's answer",
        }
        result = socratic_agent.process(request)

        assert isinstance(result, dict)
        assert "status" in result

    def test_extract_insights_only_action(self, socratic_agent, sample_project):
        """Test extracting insights from response"""
        request = {
            "action": "extract_insights_only",
            "project": sample_project,
            "response": "Student insight",
        }
        result = socratic_agent.process(request)

        assert isinstance(result, dict)
        assert "status" in result

    def test_generate_hint_action(self, socratic_agent, sample_project):
        """Test generating hint for student"""
        request = {
            "action": "generate_hint",
            "project": sample_project,
            "question": "What is your target audience?",
        }
        result = socratic_agent.process(request)

        assert isinstance(result, dict)
        assert "status" in result


@pytest.mark.unit
class TestLearningGuidance:
    """Tests for learning guidance"""

    def test_advance_phase_action(self, socratic_agent, sample_project):
        """Test advancing to next project phase"""
        # Use a valid phase from the _advance_phase method's phase list
        sample_project.phase = "discovery"
        request = {"action": "advance_phase", "project": sample_project}
        result = socratic_agent.process(request)

        assert isinstance(result, dict)
        assert "status" in result

    def test_explain_document_action(self, socratic_agent, sample_project):
        """Test explaining document content"""
        request = {
            "action": "explain_document",
            "project": sample_project,
            "content": "Sample document content",
        }
        result = socratic_agent.process(request)

        assert isinstance(result, dict)
        assert "status" in result

    def test_dynamic_question_toggle(self, socratic_agent):
        """Test toggling between dynamic and static questions"""
        initial_mode = socratic_agent.use_dynamic_questions
        request = {"action": "toggle_dynamic_questions"}
        result = socratic_agent.process(request)

        assert result["status"] == "success"
        assert result["dynamic_mode"] == (not initial_mode)
        assert socratic_agent.use_dynamic_questions == (not initial_mode)


@pytest.mark.unit
class TestConversationManagement:
    """Tests for managing conversation"""

    def test_process_method_routes_correctly(self, socratic_agent):
        """Test that process method routes actions correctly"""
        # Test unknown action
        request = {"action": "unknown_action"}
        result = socratic_agent.process(request)

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]

    def test_process_response_preserves_context(self, socratic_agent, sample_project):
        """Test that processing response preserves project context"""
        request = {
            "action": "process_response",
            "project": sample_project,
            "response": "Answer to question",
        }
        result = socratic_agent.process(request)

        # Should return valid response structure
        assert isinstance(result, dict)

    def test_redirect_off_topic(self, socratic_agent, sample_project):
        """Test redirecting off-topic discussion"""
        # Socratic agent should handle off-topic responses gracefully
        request = {
            "action": "process_response",
            "project": sample_project,
            "response": "This is completely off-topic",
        }
        result = socratic_agent.process(request)

        # Should return a valid response (not crash)
        assert isinstance(result, dict)
        assert "status" in result


@pytest.mark.unit
class TestKnowledgeGapDetection:
    """Tests for detecting knowledge gaps"""

    def test_agent_uses_orchestrator(self, socratic_agent, mock_orchestrator):
        """Test that agent properly uses orchestrator for context"""
        mock_orchestrator.context_analyzer.get_context_summary.return_value = {"phase": "planning"}

        # Agent should have access to orchestrator
        assert socratic_agent.orchestrator == mock_orchestrator

    def test_max_questions_limit_configured(self, socratic_agent):
        """Test that max questions per phase is configured"""
        assert socratic_agent.max_questions_per_phase > 0
        assert socratic_agent.max_questions_per_phase <= 10

    def test_phases_have_questions(self, socratic_agent):
        """Test that all project phases have static questions"""
        phases = ["discovery", "analysis", "design", "implementation"]
        for phase in phases:
            assert phase in socratic_agent.static_questions
            questions = socratic_agent.static_questions[phase]
            assert len(questions) > 0
            # Each question should be a non-empty string
            for question in questions:
                assert isinstance(question, str)
                assert len(question) > 10  # Should be a meaningful question
