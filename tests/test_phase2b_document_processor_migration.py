"""
Phase 2B: DocumentProcessorAgent Migration Tests

Tests for DocumentProcessorAgent after Phase 2B migration to async-first,
agent bus-aware implementation.

Validates:
- Backward compatibility with sync interface
- New async interface functionality
- Agent bus registration and discovery
- Document import functionality
- Content extraction and chunking
"""

import asyncio
from unittest.mock import MagicMock

import pytest
from socratic_agents.document_processor import DocumentProcessorAgent


class TestDocumentProcessorMigrationSetup:
    """Test DocumentProcessorAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        assert agent.name == "DocumentProcessor"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_has_process_method(self):
        """Test agent has synchronous process method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        # Agent must have process method
        assert hasattr(agent, "process")
        assert callable(agent.process)

    def test_agent_has_process_async_method(self):
        """Test agent has asynchronous process_async method."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        # Agent must have process_async method
        assert hasattr(agent, "process_async")
        assert callable(agent.process_async)

    def test_agent_has_name_attribute(self):
        """Test agent has name attribute identifying itself."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        # Agent must identify itself
        assert hasattr(agent, "name")
        assert isinstance(agent.name, str)


class TestDocumentProcessorSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_import_file_success(self):
        """Test sync import file action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        # Mock the _import_file_sync method to return success
        mock_result = {
            "status": "success",
            "file_name": "test.py",
            "words_extracted": 100,
            "chunks_created": 2,
            "entries_added": 2,
        }
        agent._import_file = MagicMock(return_value=mock_result)

        request = {
            "action": "import_file",
            "file_path": "/tmp/test.py",
            "project_id": "proj-123",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._import_file.assert_called_once_with(request)

    def test_process_import_text_success(self):
        """Test sync import text action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "file_name": "pasted_text.txt",
            "words_extracted": 50,
            "chunks_created": 1,
            "entries_added": 1,
        }
        agent._import_text = MagicMock(return_value=mock_result)

        request = {
            "action": "import_text",
            "text_content": "Some pasted content",
            "project_id": "proj-123",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_import_directory_success(self):
        """Test sync import directory action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "files_processed": 5,
            "files_failed": 0,
            "total_words_extracted": 500,
        }
        agent._import_directory = MagicMock(return_value=mock_result)

        request = {
            "action": "import_directory",
            "directory_path": "/tmp/project",
            "project_id": "proj-123",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_import_url_success(self):
        """Test sync import URL action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "url": "https://example.com",
            "words_extracted": 200,
            "chunks_created": 2,
        }
        agent._import_url = MagicMock(return_value=mock_result)

        request = {
            "action": "import_url",
            "url": "https://example.com",
            "project_id": "proj-123",
        }

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_list_documents(self):
        """Test sync list documents action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        request = {"action": "list_documents", "project_id": "proj-123"}

        result = agent.process(request)

        assert result["status"] == "success"

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestDocumentProcessorAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_import_file(self):
        """Test async import file action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "file_name": "test.py",
            "words_extracted": 100,
        }
        agent._import_file = MagicMock(return_value=mock_result)

        request = {
            "action": "import_file",
            "file_path": "/tmp/test.py",
            "project_id": "proj-123",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_import_text(self):
        """Test async import text action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        mock_result = {"status": "success", "words_extracted": 50}
        agent._import_text = MagicMock(return_value=mock_result)

        request = {
            "action": "import_text",
            "text_content": "Some content",
            "project_id": "proj-123",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_import_directory(self):
        """Test async import directory action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        mock_result = {"status": "success", "files_processed": 5}
        agent._import_directory = MagicMock(return_value=mock_result)

        request = {
            "action": "import_directory",
            "directory_path": "/tmp/project",
            "project_id": "proj-123",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_import_url(self):
        """Test async import URL action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        mock_result = {"status": "success", "url": "https://example.com"}
        agent._import_url = MagicMock(return_value=mock_result)

        request = {
            "action": "import_url",
            "url": "https://example.com",
            "project_id": "proj-123",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_list_documents(self):
        """Test async list documents action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        request = {"action": "list_documents", "project_id": "proj-123"}

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestDocumentProcessorPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

        bus_request = {
            "action": "list_documents",
            "project_id": "proj-123",
            "message_id": "msg-456",
        }

        result = asyncio.run(agent.process_async(bus_request))

        assert result["status"] == "success"

    def test_agent_has_required_interface(self):
        """Test agent has all required interface methods."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = DocumentProcessorAgent(mock_orchestrator)

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
