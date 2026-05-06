"""
Phase 2B: KnowledgeAnalysisAgent Migration Tests

Tests for KnowledgeAnalysisAgent after Phase 2B migration to async-first,
agent bus-aware implementation.

Validates:
- Backward compatibility with sync interface
- New async interface functionality
- Agent bus registration and discovery
- Knowledge analysis and gap identification
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from socratic_agents.knowledge_analysis import KnowledgeAnalysisAgent


class TestKnowledgeAnalysisMigrationSetup:
    """Test KnowledgeAnalysisAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        assert agent.name == "KnowledgeAnalysis"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_has_process_method(self):
        """Test agent has synchronous process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        # Agent must have process method
        assert hasattr(agent, 'process')
        assert callable(agent.process)

    def test_agent_has_process_async_method(self):
        """Test agent has asynchronous process_async method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        # Agent must have process_async method
        assert hasattr(agent, 'process_async')
        assert callable(agent.process_async)

    def test_agent_has_name_attribute(self):
        """Test agent has name attribute identifying itself."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        # Agent must identify itself
        assert hasattr(agent, 'name')
        assert isinstance(agent.name, str)


class TestKnowledgeAnalysisSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_analyze_knowledge_success(self):
        """Test sync analyze knowledge action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.vector_db = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "analysis": {
                "document": "test.pdf",
                "key_concepts": ["concept1", "concept2"],
                "gaps_filled": [],
            },
            "message": "Analyzed test.pdf in context of project goals",
        }
        agent._analyze_knowledge = MagicMock(return_value=mock_result)

        request = {
            "action": "analyze_knowledge",
            "project_id": "proj-123",
            "document_name": "test.pdf",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._analyze_knowledge.assert_called_once_with(request)

    def test_process_regenerate_questions_success(self):
        """Test sync regenerate questions action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "message": "Questions regenerated for 2 new focus areas",
            "new_focus_areas": ["area1", "area2"],
        }
        agent._regenerate_questions = MagicMock(return_value=mock_result)

        request = {
            "action": "regenerate_questions",
            "project_id": "proj-123",
            "knowledge_analysis": {},
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._regenerate_questions.assert_called_once_with(request)

    def test_process_get_knowledge_gaps_success(self):
        """Test sync get knowledge gaps action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "project_id": "proj-123",
            "knowledge_gaps": [{"area": "testing", "description": "Testing strategies"}],
            "count": 1,
        }
        agent._get_knowledge_gaps = MagicMock(return_value=mock_result)

        request = {
            "action": "get_knowledge_gaps",
            "project_id": "proj-123",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestKnowledgeAnalysisAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_analyze_knowledge(self):
        """Test async analyze knowledge action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.vector_db = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "analysis": {},
            "message": "Analyzed successfully",
        }
        agent._analyze_knowledge = MagicMock(return_value=mock_result)

        request = {
            "action": "analyze_knowledge",
            "project_id": "proj-123",
            "document_name": "test.pdf",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_regenerate_questions(self):
        """Test async regenerate questions action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "message": "Questions regenerated",
            "new_focus_areas": [],
        }
        agent._regenerate_questions = MagicMock(return_value=mock_result)

        request = {
            "action": "regenerate_questions",
            "project_id": "proj-123",
            "knowledge_analysis": {},
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_get_knowledge_gaps(self):
        """Test async get knowledge gaps action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "project_id": "proj-123",
            "knowledge_gaps": [],
            "count": 0,
        }
        agent._get_knowledge_gaps = MagicMock(return_value=mock_result)

        request = {
            "action": "get_knowledge_gaps",
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

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestKnowledgeAnalysisPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.event_emitter = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

        bus_request = {
            "action": "get_knowledge_gaps",
            "project_id": "proj-123",
            "message_id": "msg-789",
        }

        result = asyncio.run(agent.process_async(bus_request))

        assert result["status"] == "success"

    def test_agent_has_required_interface(self):
        """Test agent has all required interface methods."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = KnowledgeAnalysisAgent(mock_orchestrator)

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
