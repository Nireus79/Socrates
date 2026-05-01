"""Phase 2B: ContextAnalyzerAgent Migration Tests"""
import asyncio
import pytest
from unittest.mock import MagicMock
from socratic_system.agents.context_analyzer import ContextAnalyzerAgent


class TestContextAnalyzerMigration:
    """Test ContextAnalyzerAgent Phase 2B migration"""

    def test_initialization(self):
        """Test agent initializes with auto_register."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()
        mock_orchestrator.agent_bus.registry = mock_orchestrator.agent_registry
        agent = ContextAnalyzerAgent(mock_orchestrator)
        assert agent.name == "ContextAnalyzer"
        assert mock_orchestrator.agent_registry.register.called

    def test_capabilities(self):
        """Test agent declares capabilities."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)
        assert "context_analysis" in agent.get_capabilities()

    def test_metadata(self):
        """Test agent provides metadata."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)
        metadata = agent.get_metadata()
        assert metadata["version"] == "2.0"

    def test_process_sync(self):
        """Test sync process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)

        agent._analyze_context_sync = MagicMock(return_value={"status": "success"})
        result = agent.process({"action": "analyze_context", "project": MagicMock()})
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async(self):
        """Test async process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)

        agent._analyze_context_sync = MagicMock(return_value={"status": "success"})
        result = await agent.process_async({"action": "analyze_context", "project": MagicMock()})
        assert result["status"] == "success"

    def test_bus_integration(self):
        """Test agent can handle bus messages."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)

        agent._get_statistics_sync = MagicMock(return_value={"status": "success"})
        result = asyncio.run(agent.process_async({"action": "get_statistics", "project": MagicMock()}))
        assert result["status"] == "success"

    def test_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)
        result = agent.process({"action": "unknown"})
        assert result["status"] == "error"
