"""
Phase 2B: QuestionQueueAgent Migration Tests

Tests for QuestionQueueAgent after Phase 2B migration to async-first,
agent bus-aware implementation.

Validates:
- Backward compatibility with sync interface
- New async interface functionality
- Agent bus registration and discovery
- Question queue management (add, get, answer, skip, status)
- Role-based assignment
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from socratic_system.agents.question_queue_agent import QuestionQueueAgent


class TestQuestionQueueMigrationSetup:
    """Test QuestionQueueAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()

        agent = QuestionQueueAgent(mock_orchestrator)

        assert agent.name == "QuestionQueue"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_auto_registration(self):
        """Test agent registers with bus during initialization (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_bus.registry = mock_registry

        agent = QuestionQueueAgent(mock_orchestrator)

        # Agent should attempt to register
        assert mock_registry.register.called

    def test_agent_capabilities(self):
        """Test agent declares capabilities for bus discovery (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = QuestionQueueAgent(mock_orchestrator)
        capabilities = agent.get_capabilities()

        assert isinstance(capabilities, list)
        assert "question_management" in capabilities
        assert "question_assignment" in capabilities
        assert "queue_tracking" in capabilities
        assert "role_based_assignment" in capabilities

    def test_agent_metadata(self):
        """Test agent provides metadata for registration (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = QuestionQueueAgent(mock_orchestrator)
        metadata = agent.get_metadata()

        assert isinstance(metadata, dict)
        assert metadata["version"] == "2.0"
        assert "description" in metadata


class TestQuestionQueueSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_add_question_success(self):
        """Test sync add question action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        # Create mock project
        mock_project = MagicMock()
        mock_project.team_members = [
            MagicMock(username="alice", role="lead"),
            MagicMock(username="bob", role="creator"),
        ]
        mock_project.pending_questions = None
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {
            "action": "add_question",
            "project_id": "proj-123",
            "question": "What is the project strategy?",
            "phase": "planning",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        assert "question_id" in result
        mock_orchestrator.database.save_project.assert_called_once()

    def test_process_get_user_questions(self):
        """Test sync get user questions action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        # Create mock project with questions
        mock_project = MagicMock()
        mock_project.pending_questions = [
            {
                "id": "q_123",
                "question": "Test question",
                "status": "pending",
                "assigned_to_users": ["alice"],
            }
        ]
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {"action": "get_user_questions", "project_id": "proj-123", "username": "alice"}

        result = agent.process(request)

        assert result["status"] == "success"
        assert result["total"] == 1
        assert len(result["questions"]) == 1

    def test_process_answer_question_success(self):
        """Test sync answer question action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        # Create mock project with question
        mock_project = MagicMock()
        mock_project.pending_questions = [
            {
                "id": "q_123",
                "question": "Test question",
                "status": "pending",
                "assigned_to_users": ["alice"],
            }
        ]
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {
            "action": "answer_question",
            "project_id": "proj-123",
            "question_id": "q_123",
            "username": "alice",
            "answer": "The strategy is X",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        mock_orchestrator.database.save_project.assert_called_once()

    def test_process_skip_question_success(self):
        """Test sync skip question action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        # Create mock project with question
        mock_project = MagicMock()
        mock_project.pending_questions = [
            {
                "id": "q_123",
                "question": "Test question",
                "status": "pending",
                "assigned_to_users": ["alice"],
            }
        ]
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {
            "action": "skip_question",
            "project_id": "proj-123",
            "question_id": "q_123",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        mock_orchestrator.database.save_project.assert_called_once()

    def test_process_get_queue_status(self):
        """Test sync get queue status action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        # Create mock project with mixed questions
        mock_project = MagicMock()
        mock_project.pending_questions = [
            {"id": "q_1", "status": "pending"},
            {"id": "q_2", "status": "answered"},
            {"id": "q_3", "status": "skipped"},
        ]
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {"action": "get_queue_status", "project_id": "proj-123"}

        result = agent.process(request)

        assert result["status"] == "success"
        assert result["total_questions"] == 3
        assert result["pending"] == 1
        assert result["answered"] == 1
        assert result["skipped"] == 1

    def test_process_project_not_found(self):
        """Test handling when project not found."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.load_project = MagicMock(return_value=None)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {"action": "add_question", "project_id": "invalid-id", "question": "test"}

        result = agent.process(request)

        assert result["status"] == "error"
        assert "Project not found" in result["message"]

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = QuestionQueueAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestQuestionQueueAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_add_question_success(self):
        """Test async add question action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        # Create mock project
        mock_project = MagicMock()
        mock_project.team_members = [
            MagicMock(username="alice", role="lead"),
            MagicMock(username="bob", role="creator"),
        ]
        mock_project.pending_questions = None
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {
            "action": "add_question",
            "project_id": "proj-123",
            "question": "What is the project strategy?",
            "phase": "planning",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"
        assert "question_id" in result

    @pytest.mark.asyncio
    async def test_process_async_get_user_questions(self):
        """Test async get user questions action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        # Create mock project with questions
        mock_project = MagicMock()
        mock_project.pending_questions = [
            {
                "id": "q_123",
                "question": "Test question",
                "status": "pending",
                "assigned_to_users": ["alice"],
            },
            {
                "id": "q_456",
                "question": "Another question",
                "status": "pending",
                "assigned_to_users": ["alice"],
            },
        ]
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {"action": "get_user_questions", "project_id": "proj-123", "username": "alice"}

        result = await agent.process_async(request)

        assert result["status"] == "success"
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_process_async_answer_question(self):
        """Test async answer question action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        # Create mock project with question
        mock_project = MagicMock()
        mock_project.pending_questions = [
            {
                "id": "q_123",
                "question": "Test question",
                "status": "pending",
                "assigned_to_users": ["alice"],
            }
        ]
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {
            "action": "answer_question",
            "project_id": "proj-123",
            "question_id": "q_123",
            "username": "alice",
            "answer": "The strategy is X",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_skip_question(self):
        """Test async skip question action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        # Create mock project with question
        mock_project = MagicMock()
        mock_project.pending_questions = [
            {
                "id": "q_123",
                "question": "Test question",
                "status": "pending",
                "assigned_to_users": ["alice"],
            }
        ]
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {
            "action": "skip_question",
            "project_id": "proj-123",
            "question_id": "q_123",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_get_queue_status(self):
        """Test async get queue status action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        # Create mock project with mixed questions
        mock_project = MagicMock()
        mock_project.pending_questions = [
            {"id": "q_1", "status": "pending"},
            {"id": "q_2", "status": "answered"},
            {"id": "q_3", "status": "skipped"},
        ]
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {"action": "get_queue_status", "project_id": "proj-123"}

        result = await agent.process_async(request)

        assert result["status"] == "success"
        assert result["total_questions"] == 3

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = QuestionQueueAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestQuestionQueueRoleAssignment:
    """Test role-based question assignment."""

    def test_determine_roles_strategy_question(self):
        """Test role determination for strategy question."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        mock_project = MagicMock()
        mock_project.team_members = [
            MagicMock(username="alice", role="lead"),
            MagicMock(username="bob", role="creator"),
            MagicMock(username="charlie", role="specialist"),
        ]

        agent = QuestionQueueAgent(mock_orchestrator)

        roles = agent._determine_roles("What is our overall strategy?", mock_project)

        assert "lead" in roles

    def test_determine_roles_technical_question(self):
        """Test role determination for technical question."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        mock_project = MagicMock()
        mock_project.team_members = [
            MagicMock(username="alice", role="lead"),
            MagicMock(username="bob", role="creator"),
            MagicMock(username="charlie", role="specialist"),
        ]

        agent = QuestionQueueAgent(mock_orchestrator)

        roles = agent._determine_roles("What are the best practices for implementation?", mock_project)

        assert "specialist" in roles or "lead" in roles

    def test_determine_roles_fallback_to_available(self):
        """Test role determination falls back to available roles."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        mock_project = MagicMock()
        mock_project.team_members = [
            MagicMock(username="alice", role="lead"),
        ]

        agent = QuestionQueueAgent(mock_orchestrator)

        roles = agent._determine_roles("xyzabc random text with no keywords", mock_project)

        assert "lead" in roles


class TestQuestionQueueDatabaseOperations:
    """Test database operation behavior."""

    def test_add_question_database_failure(self):
        """Test handling of database save failure."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.team_members = []
        mock_project.pending_questions = None
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)
        mock_orchestrator.database.save_project = MagicMock(side_effect=Exception("DB error"))

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {
            "action": "add_question",
            "project_id": "proj-123",
            "question": "test",
            "phase": "planning",
        }

        result = agent.process(request)

        assert result["status"] == "error"
        assert "Failed" in result["message"]

    def test_answer_question_not_found(self):
        """Test handling when question not found."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.pending_questions = [
            {"id": "q_123", "status": "pending"}
        ]
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        request = {
            "action": "answer_question",
            "project_id": "proj-123",
            "question_id": "q_nonexistent",
            "username": "alice",
            "answer": "test",
        }

        result = agent.process(request)

        assert result["status"] == "error"
        assert "Question not found" in result["message"]


class TestQuestionQueuePhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()

        mock_project = MagicMock()
        mock_project.pending_questions = [
            {"id": "q_1", "status": "pending"},
            {"id": "q_2", "status": "answered"},
        ]
        mock_orchestrator.database.load_project = MagicMock(return_value=mock_project)

        agent = QuestionQueueAgent(mock_orchestrator)

        # Bus sends request as RequestMessage-like dict
        bus_request = {
            "action": "get_queue_status",
            "project_id": "proj-123",
            "message_id": "msg-456",
        }

        # Test via process_async
        result = asyncio.run(agent.process_async(bus_request))

        assert result["status"] == "success"
        assert "total_questions" in result

    def test_agent_is_discoverable(self):
        """Test agent provides discovery information (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_bus.registry = mock_registry

        agent = QuestionQueueAgent(mock_orchestrator)

        # Should have capabilities for discovery
        capabilities = agent.get_capabilities()
        metadata = agent.get_metadata()

        assert len(capabilities) > 0
        assert "version" in metadata
