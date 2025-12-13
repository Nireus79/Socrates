"""
Tests for remaining agents: Counselor, Analyzer, DocumentProcessor,
ConflictDetector, SystemMonitor, UserManager, NoteManager
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestSocraticCounselorAgent:
    """Tests for SocraticCounselorAgent - Socratic dialogue"""

    def test_agent_initialization(self, mock_orchestrator):
        """Test SocraticCounselorAgent initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.socratic_counselor import SocraticCounselorAgent

            agent = SocraticCounselorAgent(orchestrator)

            assert agent is not None
            assert agent.name == "SocraticCounselor"

    def test_start_dialogue_with_topic(self, mock_orchestrator, sample_project):
        """Test starting Socratic dialogue on a topic"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.socratic_counselor import SocraticCounselorAgent

            agent = SocraticCounselorAgent(orchestrator)

            mock_question = "What are the main components of your system?"
            orchestrator.claude_client.generate_response = MagicMock(return_value=mock_question)

            request = {
                "action": "start_dialogue",
                "project": sample_project,
                "topic": "system_architecture",
            }

            result = agent.process(request)

            assert "status" in result
            # Should generate a Socratic question
            if result.get("status") == "success":
                assert "question" in result or "message" in result


@pytest.mark.unit
class TestContextAnalyzerAgent:
    """Tests for ContextAnalyzerAgent - Context analysis and relevance scoring"""

    def test_agent_initialization(self, mock_orchestrator):
        """Test ContextAnalyzerAgent initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.context_analyzer import ContextAnalyzerAgent

            agent = ContextAnalyzerAgent(orchestrator)

            assert agent is not None
            assert agent.name == "ContextAnalyzer"

    def test_extract_context_from_conversation(self, mock_orchestrator):
        """Test extracting context from conversation history"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.context_analyzer import ContextAnalyzerAgent

            agent = ContextAnalyzerAgent(orchestrator)

            conversation = [
                {"type": "user", "content": "I want to build a REST API"},
                {"type": "assistant", "content": "REST APIs need endpoints"},
                {"type": "user", "content": "Should I use authentication?"},
            ]

            request = {"action": "analyze_context", "conversation": conversation}

            result = agent.process(request)

            assert "status" in result
            # Should analyze and extract relevant context
            if result.get("status") == "success":
                assert "context" in result or "analysis" in result


@pytest.mark.unit
class TestDocumentProcessorAgent:
    """Tests for DocumentProcessorAgent - Document processing"""

    def test_agent_initialization(self, mock_orchestrator):
        """Test DocumentProcessorAgent initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.document_processor import DocumentProcessorAgent

            agent = DocumentProcessorAgent(orchestrator)

            assert agent is not None
            assert agent.name == "DocumentProcessor"

    def test_extract_text_from_document(self, mock_orchestrator, temp_data_dir):
        """Test extracting text from documents"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.document_processor import DocumentProcessorAgent

            agent = DocumentProcessorAgent(orchestrator)

            # Create a mock document for testing
            request = {"action": "extract_text", "document_path": str(temp_data_dir / "test.txt")}

            result = agent.process(request)

            assert "status" in result
            # Should handle file operations gracefully


@pytest.mark.unit
class TestConflictDetectorAgent:
    """Tests for ConflictDetectorAgent - Conflict detection"""

    def test_agent_initialization(self, mock_orchestrator):
        """Test ConflictDetectorAgent initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.conflict_detector import ConflictDetectorAgent

            agent = ConflictDetectorAgent(orchestrator)

            assert agent is not None
            assert agent.name == "ConflictDetector"

    def test_detect_note_conflict(self, mock_orchestrator):
        """Test detecting conflicts in notes"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.conflict_detector import ConflictDetectorAgent

            agent = ConflictDetectorAgent(orchestrator)

            request = {
                "action": "detect_conflict",
                "resource_type": "note",
                "resource_id": "note_123",
                "version_a": "Original content",
                "version_b": "Modified content",
            }

            result = agent.process(request)

            assert "status" in result
            # Should detect or indicate conflict status


@pytest.mark.unit
class TestSystemMonitorAgent:
    """Tests for SystemMonitorAgent - System monitoring"""

    def test_agent_initialization(self, mock_orchestrator):
        """Test SystemMonitorAgent initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.system_monitor import SystemMonitorAgent

            agent = SystemMonitorAgent(orchestrator)

            assert agent is not None
            assert agent.name == "SystemMonitor"

    def test_perform_health_check(self, mock_orchestrator):
        """Test system health check"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.system_monitor import SystemMonitorAgent

            agent = SystemMonitorAgent(orchestrator)

            request = {"action": "health_check"}

            result = agent.process(request)

            assert "status" in result
            # Health check should always return some status
            assert result["status"] in ["success", "error", "warning"]


@pytest.mark.unit
class TestUserManagerAgent:
    """Tests for UserManagerAgent - User management"""

    def test_agent_initialization(self, mock_orchestrator):
        """Test UserManagerAgent initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.user_manager import UserManagerAgent

            agent = UserManagerAgent(orchestrator)

            assert agent is not None
            assert agent.name == "UserManager"

    def test_create_user(self, mock_orchestrator):
        """Test creating a new user"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.user_manager import UserManagerAgent

            agent = UserManagerAgent(orchestrator)

            request = {
                "action": "create_user",
                "username": "newuser",
                "password": "secure_password_123",
            }

            result = agent.process(request)

            assert "status" in result
            # Should create user or indicate if already exists

    def test_authenticate_user(self, mock_orchestrator):
        """Test user authentication"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.user_manager import UserManagerAgent

            agent = UserManagerAgent(orchestrator)

            request = {"action": "authenticate", "username": "testuser", "password": "password123"}

            result = agent.process(request)

            assert "status" in result
            # Should authenticate or return error


@pytest.mark.unit
class TestNoteManagerAgent:
    """Tests for NoteManagerAgent - Note management"""

    def test_agent_initialization(self, mock_orchestrator):
        """Test NoteManagerAgent initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.note_manager import NoteManagerAgent

            agent = NoteManagerAgent(orchestrator)

            assert agent is not None
            assert agent.name == "NoteManager"

    def test_create_note(self, mock_orchestrator, sample_project):
        """Test creating a note"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.note_manager import NoteManagerAgent

            agent = NoteManagerAgent(orchestrator)

            request = {
                "action": "create_note",
                "project_id": sample_project.project_id,
                "content": "This is a test note",
                "tags": ["test", "important"],
            }

            result = agent.process(request)

            assert "status" in result
            # Should create note with provided content

    def test_get_note(self, mock_orchestrator, sample_project):
        """Test retrieving a note"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.note_manager import NoteManagerAgent

            agent = NoteManagerAgent(orchestrator)

            request = {
                "action": "get_note",
                "note_id": "test_note_123",
                "project_id": sample_project.project_id,
            }

            result = agent.process(request)

            assert "status" in result
            # Should retrieve note or indicate not found

    def test_list_project_notes(self, mock_orchestrator, sample_project):
        """Test listing notes in a project"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.note_manager import NoteManagerAgent

            agent = NoteManagerAgent(orchestrator)

            request = {"action": "list_notes", "project_id": sample_project.project_id}

            result = agent.process(request)

            assert "status" in result
            # Should list notes for project
            if result.get("status") == "success":
                assert "notes" in result


@pytest.mark.integration
class TestAgentCrossCollaboration:
    """Integration tests for multiple agents working together"""

    def test_counselor_analyzer_collaboration(self, mock_orchestrator, sample_project):
        """Test SocraticCounselor and ContextAnalyzer working together"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.context_analyzer import ContextAnalyzerAgent
            from socratic_system.agents.socratic_counselor import SocraticCounselorAgent

            counselor = SocraticCounselorAgent(orchestrator)
            analyzer = ContextAnalyzerAgent(orchestrator)

            # Counselor generates a question
            question_request = {
                "action": "start_dialogue",
                "project": sample_project,
                "topic": "requirements",
            }

            # Analyzer processes the conversation
            conversation = [
                {"type": "assistant", "content": "What are your requirements?"},
                {"type": "user", "content": "I need authentication and caching"},
            ]

            analyze_request = {"action": "analyze_context", "conversation": conversation}

            # Both should work without errors
            counsel_result = counselor.process(question_request)
            analyze_result = analyzer.process(analyze_request)

            assert "status" in counsel_result
            assert "status" in analyze_result

    def test_project_manager_note_manager_collaboration(self, mock_orchestrator, sample_project):
        """Test ProjectManager and NoteManager collaboration"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.note_manager import NoteManagerAgent
            from socratic_system.agents.project_manager import ProjectManagerAgent

            proj_mgr = ProjectManagerAgent(orchestrator)
            note_mgr = NoteManagerAgent(orchestrator)

            # Save project first
            orchestrator.database.save_project(sample_project)

            # Create note for project
            note_request = {
                "action": "create_note",
                "project_id": sample_project.project_id,
                "content": "Design decision: Use async for I/O",
                "tags": ["design", "async"],
            }

            note_result = note_mgr.process(note_request)
            assert "status" in note_result

            # Load project and verify it's unchanged
            load_request = {"action": "load_project", "project_id": sample_project.project_id}
            load_result = proj_mgr.process(load_request)
            assert load_result["status"] == "success"

    def test_conflict_detector_with_project_manager(self, mock_orchestrator, sample_project):
        """Test ConflictDetector working with ProjectManager"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator
            from socratic_system.agents.conflict_detector import ConflictDetectorAgent
            from socratic_system.agents.project_manager import ProjectManagerAgent

            proj_mgr = ProjectManagerAgent(orchestrator)
            conflict_detector = ConflictDetectorAgent(orchestrator)

            orchestrator.database.save_project(sample_project)

            # Make changes that might cause conflicts
            sample_project.description = "Version A"
            proj_mgr.process({"action": "save_project", "project": sample_project})

            # Check for conflicts
            conflict_request = {
                "action": "detect_conflict",
                "resource_type": "project",
                "resource_id": sample_project.project_id,
                "version_a": "Version A",
                "version_b": "Version B (concurrent edit)",
            }

            result = conflict_detector.process(conflict_request)
            assert "status" in result


@pytest.mark.unit
class TestAgentErrorHandling:
    """Test error handling across all remaining agents"""

    def test_missing_action_field_all_agents(self, mock_orchestrator):
        """Test that all agents handle missing action field"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator

            from socratic_system.agents.conflict_detector import ConflictDetectorAgent
            from socratic_system.agents.context_analyzer import ContextAnalyzerAgent
            from socratic_system.agents.document_processor import DocumentProcessorAgent
            from socratic_system.agents.note_manager import NoteManagerAgent
            from socratic_system.agents.socratic_counselor import SocraticCounselorAgent
            from socratic_system.agents.system_monitor import SystemMonitorAgent
            from socratic_system.agents.user_manager import UserManagerAgent

            agents = [
                SocraticCounselorAgent(orchestrator),
                ContextAnalyzerAgent(orchestrator),
                DocumentProcessorAgent(orchestrator),
                ConflictDetectorAgent(orchestrator),
                SystemMonitorAgent(orchestrator),
                UserManagerAgent(orchestrator),
                NoteManagerAgent(orchestrator),
            ]

            for agent in agents:
                result = agent.process({})
                # Should have status field
                assert "status" in result

    @pytest.mark.parametrize(
        "agent_class,agent_name,module_name",
        [
            ("SocraticCounselorAgent", "SocraticCounselor", "socratic_counselor"),
            ("ContextAnalyzerAgent", "ContextAnalyzer", "context_analyzer"),
            ("DocumentProcessorAgent", "DocumentProcessor", "document_processor"),
            ("ConflictDetectorAgent", "ConflictDetector", "conflict_detector"),
            ("SystemMonitorAgent", "SystemMonitor", "system_monitor"),
            ("UserManagerAgent", "UserManager", "user_manager"),
            ("NoteManagerAgent", "NoteManager", "note_manager"),
        ],
    )
    def test_agent_initialization_all(
        self, mock_orchestrator, agent_class, agent_name, module_name
    ):
        """Test all agents initialize with correct names"""
        with patch("anthropic.Anthropic"):
            orchestrator = mock_orchestrator

            # Dynamic import using explicit module names
            module = __import__(f"socratic_system.agents.{module_name}", fromlist=[agent_class])
            AgentClass = getattr(module, agent_class)
            agent = AgentClass(orchestrator)

            assert agent.name == agent_name
