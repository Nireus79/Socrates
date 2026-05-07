"""Phase 2B: ContextAnalyzerAgent Migration Tests"""

import asyncio
from unittest.mock import MagicMock

import pytest
from socratic_agents.context_analyzer import ContextAnalyzerAgent


class TestContextAnalyzerMigration:
    """Test ContextAnalyzerAgent Phase 2B migration"""

    def test_initialization(self):
        """Test agent initializes correctly."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)
        assert agent.name == "ContextAnalyzer"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_has_process_method(self):
        """Test agent has synchronous process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)
        assert hasattr(agent, "process")
        assert callable(agent.process)

    def test_agent_has_process_async_method(self):
        """Test agent has asynchronous process_async method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)
        assert hasattr(agent, "process_async")
        assert callable(agent.process_async)

    def test_process_sync(self):
        """Test sync process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)

        agent._analyze_context = MagicMock(return_value={"status": "success"})
        result = agent.process({"action": "analyze_context", "project": MagicMock()})
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async(self):
        """Test async process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)

        agent._analyze_context = MagicMock(return_value={"status": "success"})
        result = await agent.process_async({"action": "analyze_context", "project": MagicMock()})
        assert result["status"] == "success"

    def test_bus_integration(self):
        """Test agent can handle bus messages."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)

        agent._get_statistics = MagicMock(return_value={"status": "success"})
        result = asyncio.run(
            agent.process_async({"action": "get_statistics", "project": MagicMock()})
        )
        assert result["status"] == "success"

    def test_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        agent = ContextAnalyzerAgent(mock_orchestrator)
        result = agent.process({"action": "unknown"})
        assert result["status"] == "error"
