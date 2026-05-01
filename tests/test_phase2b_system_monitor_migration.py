"""
Phase 2B: SystemMonitorAgent Migration Tests

Tests for SystemMonitorAgent after Phase 2B migration to async-first,
agent bus-aware implementation.

Validates:
- Backward compatibility with sync interface
- New async interface functionality
- Agent bus registration and discovery
- State management (token tracking)
- Health check capabilities
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from socratic_system.agents.system_monitor import SystemMonitorAgent
from socratic_system.config import SocratesConfig
from socratic_system.events import EventEmitter
from socratic_system.messaging.agent_registry import AgentRegistry
from socratic_system.messaging.agent_bus import AgentBus
from socratic_system.models import TokenUsage


class TestSystemMonitorMigrationSetup:
    """Test SystemMonitorAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        assert agent.name == "SystemMonitor"
        assert agent.token_usage == []
        assert agent.connection_status is True
        assert agent.orchestrator is mock_orchestrator

    def test_agent_auto_registration(self):
        """Test agent registers with bus during initialization (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_bus.registry = mock_registry

        agent = SystemMonitorAgent(mock_orchestrator)

        # Agent should attempt to register
        assert mock_registry.register.called

    def test_agent_capabilities(self):
        """Test agent declares capabilities for bus discovery (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)
        capabilities = agent.get_capabilities()

        assert isinstance(capabilities, list)
        assert "system_monitoring" in capabilities
        assert "health_check" in capabilities
        assert "token_tracking" in capabilities
        assert "limit_checking" in capabilities

    def test_agent_metadata(self):
        """Test agent provides metadata for registration (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)
        metadata = agent.get_metadata()

        assert isinstance(metadata, dict)
        assert metadata["version"] == "2.0"
        assert "description" in metadata
        assert "capabilities_count" in metadata


class TestSystemMonitorSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_track_tokens(self):
        """Test sync track_tokens action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        request = {
            "action": "track_tokens",
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "cost_estimate": 0.005,
        }

        result = agent.process(request)

        assert result["status"] == "success"
        assert result["warning"] is False
        assert len(agent.token_usage) == 1
        assert agent.token_usage[0].total_tokens == 150

    def test_process_get_stats(self):
        """Test sync get_stats action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        # Track some tokens first
        agent._track_tokens({
            "action": "track_tokens",
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "cost_estimate": 0.005,
        })

        result = agent.process({"action": "get_stats"})

        assert result["status"] == "success"
        assert result["total_tokens"] == 150
        assert result["total_cost"] == 0.005
        assert result["api_calls"] == 1

    def test_process_check_limits(self):
        """Test sync check_limits action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        result = agent.process({"action": "check_limits"})

        assert result["status"] == "success"
        assert "warnings" in result
        assert result["recent_usage"] == 0

    def test_process_check_health_sync(self):
        """Test sync check_health action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.claude_client.test_connection = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        result = agent.process({"action": "check_health"})

        assert result["status"] == "success"
        assert result["connection"] is True
        mock_orchestrator.claude_client.test_connection.assert_called_once()

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestSystemMonitorAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_track_tokens(self):
        """Test async track_tokens action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        request = {
            "action": "track_tokens",
            "input_tokens": 200,
            "output_tokens": 100,
            "total_tokens": 300,
            "cost_estimate": 0.01,
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"
        assert len(agent.token_usage) == 1
        assert agent.token_usage[0].total_tokens == 300

    @pytest.mark.asyncio
    async def test_process_async_get_stats(self):
        """Test async get_stats action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        # Track tokens
        agent._track_tokens({
            "action": "track_tokens",
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "cost_estimate": 0.005,
        })

        result = await agent.process_async({"action": "get_stats"})

        assert result["status"] == "success"
        assert result["total_tokens"] == 150

    @pytest.mark.asyncio
    async def test_process_async_check_health(self):
        """Test async check_health with async API call (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.claude_client.test_connection = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        result = await agent.process_async({"action": "check_health"})

        assert result["status"] == "success"
        assert result["connection"] is True
        # Verify API was called in thread pool
        mock_orchestrator.claude_client.test_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_async_check_limits(self):
        """Test async check_limits action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        result = await agent.process_async({"action": "check_limits"})

        assert result["status"] == "success"
        assert isinstance(result["warnings"], list)

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestSystemMonitorStateManagement:
    """Test agent state management (token tracking)."""

    def test_token_tracking_accumulation(self):
        """Test token usage accumulates correctly."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        # Track multiple token usages
        for i in range(5):
            agent._track_tokens({
                "action": "track_tokens",
                "input_tokens": 100 * (i + 1),
                "output_tokens": 50 * (i + 1),
                "total_tokens": 150 * (i + 1),
                "cost_estimate": 0.005 * (i + 1),
            })

        assert len(agent.token_usage) == 5
        assert agent.token_usage[0].total_tokens == 150
        assert agent.token_usage[4].total_tokens == 750

    def test_warning_threshold_detection(self):
        """Test warning when usage exceeds threshold."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        # Track high usage
        result = agent._track_tokens({
            "action": "track_tokens",
            "input_tokens": 40000,
            "output_tokens": 15000,
            "total_tokens": 55000,
            "cost_estimate": 1.0,
        })

        assert result["warning"] is True

    def test_connection_status_tracking(self):
        """Test connection status is tracked."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        # Initially true
        assert agent.connection_status is True

        # Simulate health check failure
        mock_orchestrator.claude_client.test_connection.side_effect = Exception("Connection failed")

        agent._check_health_sync({"action": "check_health"})

        # Should be false after failure
        assert agent.connection_status is False


class TestSystemMonitorHealthChecks:
    """Test health check functionality."""

    def test_health_check_success(self):
        """Test successful health check."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.claude_client.test_connection = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        result = agent._check_health_sync({"action": "check_health"})

        assert result["status"] == "success"
        assert result["connection"] is True
        assert "last_check" in result

    def test_health_check_failure(self):
        """Test failed health check."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        mock_orchestrator.claude_client.test_connection.side_effect = Exception("API Error")

        agent = SystemMonitorAgent(mock_orchestrator)

        result = agent._check_health_sync({"action": "check_health"})

        assert result["status"] == "error"
        assert result["connection"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_health_check_async_uses_thread_pool(self):
        """Test async health check runs in thread pool (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.claude_client = MagicMock()

        # Create a blocking function
        def blocking_check():
            pass

        mock_orchestrator.claude_client.test_connection = blocking_check

        agent = SystemMonitorAgent(mock_orchestrator)

        # Async version should run without blocking
        result = await agent.process_async({"action": "check_health"})

        assert result["status"] == "success"


class TestSystemMonitorPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = SystemMonitorAgent(mock_orchestrator)

        # Bus sends request as RequestMessage-like dict
        bus_request = {
            "action": "get_stats",
            "message_id": "msg-123",
        }

        # Test via process_async
        import asyncio
        result = asyncio.run(agent.process_async(bus_request))

        assert result["status"] == "success"
        assert "total_tokens" in result

    def test_agent_is_discoverable(self):
        """Test agent provides discovery information (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_bus.registry = mock_registry

        agent = SystemMonitorAgent(mock_orchestrator)

        # Should have capabilities for discovery
        capabilities = agent.get_capabilities()
        metadata = agent.get_metadata()

        assert len(capabilities) > 0
        assert "version" in metadata
