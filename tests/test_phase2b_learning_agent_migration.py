"""Phase 2B: UserLearningAgent Migration Tests"""

import asyncio
from unittest.mock import MagicMock

import pytest
from socratic_agents.learning_agent import UserLearningAgent


class TestLearningAgentMigrationSetup:
    """Test UserLearningAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()
        mock_orchestrator.agent_bus.registry = mock_orchestrator.agent_registry

        agent = UserLearningAgent(mock_orchestrator)

        assert agent.name == "User Learning"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_has_process_method(self):
        """Test agent has synchronous process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        # Agent must have process method
        assert hasattr(agent, "process")
        assert callable(agent.process)

    def test_agent_has_process_async_method(self):
        """Test agent has asynchronous process_async method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        # Agent must have process_async method
        assert hasattr(agent, "process_async")
        assert callable(agent.process_async)

    def test_agent_has_name_attribute(self):
        """Test agent has name attribute identifying itself."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        # Agent must identify itself
        assert hasattr(agent, "name")
        assert isinstance(agent.name, str)


class TestLearningAgentSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_track_question_effectiveness_success(self):
        """Test sync track question effectiveness action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "effectiveness": 0.85,
        }
        agent._track_question_effectiveness = MagicMock(return_value=mock_result)

        request = {
            "action": "track_question_effectiveness",
            "user_id": "user-1",
            "question_template_id": "q-1",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._track_question_effectiveness.assert_called_once_with(request)

    def test_process_learn_behavior_pattern_success(self):
        """Test sync learn behavior pattern action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "pattern_learned": True,
        }
        agent._learn_behavior_pattern = MagicMock(return_value=mock_result)

        request = {
            "action": "learn_behavior_pattern",
            "user_id": "user-1",
            "pattern_type": "communication_style",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._learn_behavior_pattern.assert_called_once_with(request)

    def test_process_recommend_next_question_success(self):
        """Test sync recommend next question action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "recommended": True,
        }
        agent._recommend_next_question = MagicMock(return_value=mock_result)

        request = {
            "action": "recommend_next_question",
            "user_id": "user-1",
            "project_id": "proj-1",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._recommend_next_question.assert_called_once_with(request)

    def test_process_upload_knowledge_document_success(self):
        """Test sync upload knowledge document action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "document_uploaded": True,
        }
        agent._upload_knowledge_document = MagicMock(return_value=mock_result)

        request = {
            "action": "upload_knowledge_document",
            "project_id": "proj-1",
            "filename": "doc.txt",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._upload_knowledge_document.assert_called_once_with(request)

    def test_process_get_user_profile_success(self):
        """Test sync get user profile action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "profile": {"user_id": "user-1"},
        }
        agent._get_user_profile = MagicMock(return_value=mock_result)

        request = {
            "action": "get_user_profile",
            "user_id": "user-1",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._get_user_profile.assert_called_once_with(request)

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestLearningAgentAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_track_question_effectiveness(self):
        """Test async track question effectiveness action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "effectiveness": 0.85,
        }
        agent._track_question_effectiveness = MagicMock(return_value=mock_result)

        request = {
            "action": "track_question_effectiveness",
            "user_id": "user-1",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_learn_behavior_pattern(self):
        """Test async learn behavior pattern action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "pattern_learned": True,
        }
        agent._learn_behavior_pattern = MagicMock(return_value=mock_result)

        request = {
            "action": "learn_behavior_pattern",
            "user_id": "user-1",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_recommend_next_question(self):
        """Test async recommend next question action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "recommended": True,
        }
        agent._recommend_next_question = MagicMock(return_value=mock_result)

        request = {
            "action": "recommend_next_question",
            "user_id": "user-1",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_upload_knowledge_document(self):
        """Test async upload knowledge document action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "document_uploaded": True,
        }
        agent._upload_knowledge_document = MagicMock(return_value=mock_result)

        request = {
            "action": "upload_knowledge_document",
            "project_id": "proj-1",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_get_user_profile(self):
        """Test async get user profile action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "profile": {"user_id": "user-1"},
        }
        agent._get_user_profile = MagicMock(return_value=mock_result)

        request = {
            "action": "get_user_profile",
            "user_id": "user-1",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestLearningAgentPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "profile": {"user_id": "user-1"},
        }
        agent._get_user_profile = MagicMock(return_value=mock_result)

        bus_request = {
            "action": "get_user_profile",
            "user_id": "user-1",
            "message_id": "msg-444",
        }

        result = asyncio.run(agent.process_async(bus_request))

        assert result["status"] == "success"

    def test_agent_has_required_interface(self):
        """Test agent has all required interface methods."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserLearningAgent(mock_orchestrator)

        # Agent must have core interface
        assert hasattr(agent, "name")
        assert hasattr(agent, "orchestrator")
        assert hasattr(agent, "process")
        assert hasattr(agent, "process_async")

        # Verify they're callable/accessible
        assert isinstance(agent.name, str)
        assert agent.orchestrator is mock_orchestrator
        assert callable(agent.process)
        assert callable(agent.process_async)
