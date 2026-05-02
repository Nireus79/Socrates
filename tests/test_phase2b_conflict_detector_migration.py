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

from socratic_system.agents.conflict_detector import ConflictDetectorAgent


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

    def test_agent_auto_registration(self):
        """Test agent registers with bus during initialization (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_bus.registry = mock_registry

        agent = ConflictDetectorAgent(mock_orchestrator)

        assert mock_registry.register.called

    def test_agent_capabilities(self):
        """Test agent declares capabilities for bus discovery (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)
        capabilities = agent.get_capabilities()

        assert isinstance(capabilities, list)
        assert "conflict_detection" in capabilities
        assert "conflict_resolution" in capabilities
        assert "suggestion_generation" in capabilities

    def test_agent_metadata(self):
        """Test agent provides metadata for registration (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = ConflictDetectorAgent(mock_orchestrator)
        metadata = agent.get_metadata()

        assert isinstance(metadata, dict)
        assert metadata["version"] == "2.0"
        assert "description" in metadata


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
        agent._detect_conflicts_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "detect_conflicts",
            "project": MagicMock(),
            "new_insights": {"goals": ["Goal 1"]},
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._detect_conflicts_sync.assert_called_once_with(request)

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
        agent._resolve_conflict_sync = MagicMock(return_value=mock_result)

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
        agent._get_conflict_suggestions_sync = MagicMock(return_value=mock_result)

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
        agent._detect_conflicts_sync = MagicMock(return_value=mock_result)

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
        agent._resolve_conflict_sync = MagicMock(return_value=mock_result)

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
        agent._get_conflict_suggestions_sync = MagicMock(return_value=mock_result)

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

    def test_agent_is_discoverable(self):
        """Test agent provides discovery information (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_bus.registry = mock_registry

        agent = ConflictDetectorAgent(mock_orchestrator)

        capabilities = agent.get_capabilities()
        metadata = agent.get_metadata()

        assert len(capabilities) > 0
        assert "version" in metadata
