"""
Phase 2B: KnowledgeManagerAgent Migration Tests

Tests for KnowledgeManagerAgent after Phase 2B migration to async-first,
agent bus-aware implementation.

Validates:
- Backward compatibility with sync interface
- New async interface functionality
- Agent bus registration and discovery
- Knowledge suggestion management
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from socratic_agents.knowledge_manager import KnowledgeManagerAgent


class TestKnowledgeManagerMigrationSetup:
    """Test KnowledgeManagerAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        assert agent.name == "KnowledgeManager"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_has_process_method(self):
        """Test agent has synchronous process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        # Agent must have process method
        assert hasattr(agent, 'process')
        assert callable(agent.process)

    def test_agent_has_process_async_method(self):
        """Test agent has asynchronous process_async method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        # Agent must have process_async method
        assert hasattr(agent, 'process_async')
        assert callable(agent.process_async)

    def test_agent_has_name_attribute(self):
        """Test agent has name attribute identifying itself."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        # Agent must identify itself
        assert hasattr(agent, 'name')
        assert isinstance(agent.name, str)


class TestKnowledgeManagerSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_get_suggestions_success(self):
        """Test sync get suggestions action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "suggestions": [{"id": "sug-123", "content": "Add caching"}],
            "count": 1,
        }
        agent._get_suggestions_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "get_suggestions",
            "project_id": "proj-123",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._get_suggestions_sync.assert_called_once_with(request)

    def test_process_approve_suggestion_success(self):
        """Test sync approve suggestion action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "message": "Knowledge added: Caching Strategy",
        }
        agent._approve_suggestion_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "approve_suggestion",
            "project_id": "proj-123",
            "suggestion_id": "sug-123",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._approve_suggestion_sync.assert_called_once_with(request)

    def test_process_reject_suggestion_success(self):
        """Test sync reject suggestion action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "message": "Suggestion rejected",
        }
        agent._reject_suggestion_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "reject_suggestion",
            "project_id": "proj-123",
            "suggestion_id": "sug-123",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_get_queue_status_success(self):
        """Test sync get queue status action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "pending": 2,
            "approved": 1,
            "rejected": 0,
            "total": 3,
        }
        agent._get_queue_status_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "get_queue_status",
            "project_id": "proj-123",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_clear_suggestions_success(self):
        """Test sync clear suggestions action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "cleared": 2,
        }
        agent._clear_suggestions_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "clear_suggestions",
            "project_id": "proj-123",
            "keep_pending": True,
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestKnowledgeManagerAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_get_suggestions(self):
        """Test async get suggestions action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "suggestions": [],
            "count": 0,
        }
        agent._get_suggestions_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "get_suggestions",
            "project_id": "proj-123",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_approve_suggestion(self):
        """Test async approve suggestion action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        mock_result = {"status": "success", "message": "Knowledge added"}
        agent._approve_suggestion_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "approve_suggestion",
            "project_id": "proj-123",
            "suggestion_id": "sug-123",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_reject_suggestion(self):
        """Test async reject suggestion action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        mock_result = {"status": "success", "message": "Suggestion rejected"}
        agent._reject_suggestion_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "reject_suggestion",
            "project_id": "proj-123",
            "suggestion_id": "sug-123",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_get_queue_status(self):
        """Test async get queue status action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "total": 0,
        }
        agent._get_queue_status_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "get_queue_status",
            "project_id": "proj-123",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_clear_suggestions(self):
        """Test async clear suggestions action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        mock_result = {"status": "success", "cleared": 0}
        agent._clear_suggestions_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "clear_suggestions",
            "project_id": "proj-123",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestKnowledgeManagerPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        bus_request = {
            "action": "get_queue_status",
            "project_id": "proj-123",
            "message_id": "msg-456",
        }

        result = asyncio.run(agent.process_async(bus_request))

        assert result["status"] == "success"

    def test_agent_has_required_interface(self):
        """Test agent has all required interface methods."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = KnowledgeManagerAgent(mock_orchestrator)

        # Agent must have core interface
        assert hasattr(agent, 'name')
        assert hasattr(agent, 'orchestrator')
        assert hasattr(agent, 'process')
        assert hasattr(agent, 'process_async')

        # Verify they're callable/accessible
        assert isinstance(agent.name, str)
        assert agent.orchestrator is mock_orchestrator
        assert callable(agent.process)
        assert callable(agent.process_async)
