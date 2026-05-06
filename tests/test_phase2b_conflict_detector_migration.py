"""
Phase 2B: ConflictDetectorAgent Migration Tests

Tests for ConflictDetectorAgent after Phase 2B migration to async-first,
agent bus-aware implementation.

Validates:
- Backward compatibility with sync interface
- New async interface functionality
- Agent bus registration and discovery
- Conflict detection and resolution
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from socratic_agents.conflict_detector import ConflictDetectorAgent


class TestConflictDetectorMigrationSetup:
    """Test ConflictDetectorAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        assert agent.name == "ConflictDetector"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_has_process_method(self):
        """Test agent has synchronous process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        # Agent must have process method
        assert hasattr(agent, 'process')
        assert callable(agent.process)

    def test_agent_has_process_async_method(self):
        """Test agent has asynchronous process_async method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        # Agent must have process_async method
        assert hasattr(agent, 'process_async')
        assert callable(agent.process_async)

    def test_agent_has_name_attribute(self):
        """Test agent has name attribute identifying itself."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        # Agent must identify itself
        assert hasattr(agent, 'name')
        assert isinstance(agent.name, str)


class TestConflictDetectorSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_detect_conflicts_success(self):
        """Test sync detect conflicts action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "conflicts": [{"type": "tech_stack", "message": "Conflict detected"}],
        }
        agent._detect_conflicts = MagicMock(return_value=mock_result)

        request = {
            "action": "detect_conflicts",
            "project": MagicMock(),
            "new_insights": {"goals": ["Goal 1"]},
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._detect_conflicts.assert_called_once_with(request)

    def test_process_resolve_conflict_success(self):
        """Test sync resolve conflict action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        mock_conflict = MagicMock()
        mock_conflict.conflict_id = "conflict-123"

        mock_result = {
            "status": "success",
            "conflict_id": "conflict-123",
            "resolved": True,
        }
        agent._resolve_conflict = MagicMock(return_value=mock_result)

        request = {
            "action": "resolve_conflict",
            "conflict": mock_conflict,
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_get_suggestions_success(self):
        """Test sync get suggestions action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        mock_conflict = MagicMock()
        mock_conflict.suggestions = ["Suggestion 1", "Suggestion 2"]

        mock_result = {
            "status": "success",
            "suggestions": ["Suggestion 1", "Suggestion 2"],
        }
        agent._get_conflict_suggestions = MagicMock(return_value=mock_result)

        request = {
            "action": "get_suggestions",
            "conflict": mock_conflict,
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestConflictDetectorAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_detect_conflicts(self):
        """Test async detect conflicts action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "conflicts": [],
        }
        agent._detect_conflicts = MagicMock(return_value=mock_result)

        request = {
            "action": "detect_conflicts",
            "project": MagicMock(),
            "new_insights": {},
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_resolve_conflict(self):
        """Test async resolve conflict action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        mock_conflict = MagicMock()
        mock_conflict.conflict_id = "conflict-123"

        mock_result = {"status": "success", "conflict_id": "conflict-123", "resolved": True}
        agent._resolve_conflict = MagicMock(return_value=mock_result)

        request = {
            "action": "resolve_conflict",
            "conflict": mock_conflict,
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_get_suggestions(self):
        """Test async get suggestions action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        mock_conflict = MagicMock()
        mock_conflict.suggestions = []

        mock_result = {"status": "success", "suggestions": []}
        agent._get_conflict_suggestions = MagicMock(return_value=mock_result)

        request = {
            "action": "get_suggestions",
            "conflict": mock_conflict,
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestConflictDetectorPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

        bus_request = {
            "action": "detect_conflicts",
            "project": MagicMock(),
            "new_insights": {},
            "message_id": "msg-999",
        }

        result = asyncio.run(agent.process_async(bus_request))

        assert result["status"] == "success"

    def test_agent_has_required_interface(self):
        """Test agent has all required interface methods."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)

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
