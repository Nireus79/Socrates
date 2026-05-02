"""Phase 2B: NoteManagerAgent Migration Tests"""
import asyncio
import pytest
from unittest.mock import MagicMock
from socratic_system.agents.note_manager import NoteManagerAgent


class TestNoteManagerMigrationSetup:
    """Test NoteManagerAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()
        mock_orchestrator.agent_bus.registry = mock_orchestrator.agent_registry

        agent = NoteManagerAgent(mock_orchestrator)

        assert agent.name == "NoteManager"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_auto_registration(self):
        """Test agent registers with bus during initialization (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_bus.registry = mock_registry

        agent = NoteManagerAgent(mock_orchestrator)

        assert mock_registry.register.called

    def test_agent_capabilities(self):
        """Test agent declares capabilities for bus discovery (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)
        capabilities = agent.get_capabilities()

        assert isinstance(capabilities, list)
        assert "note_management" in capabilities
        assert "note_search" in capabilities
        assert "note_persistence" in capabilities

    def test_agent_metadata(self):
        """Test agent provides metadata for registration (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)
        metadata = agent.get_metadata()

        assert isinstance(metadata, dict)
        assert metadata["version"] == "2.0"
        assert "description" in metadata


class TestNoteManagerSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_add_note_success(self):
        """Test sync add note action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "message": "Note added successfully",
            "note": {"note_id": "note-1", "title": "Test Note"},
            "vectorization_result": {"status": "success"},
        }
        agent._add_note_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "add_note",
            "project_id": "proj-1",
            "note_type": "design",
            "title": "Test Note",
            "content": "Test content",
            "created_by": "user-1",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._add_note_sync.assert_called_once_with(request)

    def test_process_list_notes_success(self):
        """Test sync list notes action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "notes": [],
            "count": 0,
        }
        agent._list_notes_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "list_notes",
            "project_id": "proj-1",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._list_notes_sync.assert_called_once_with(request)

    def test_process_search_notes_success(self):
        """Test sync search notes action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "results": [],
            "count": 0,
            "query": "test",
        }
        agent._search_notes_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "search_notes",
            "project_id": "proj-1",
            "query": "test",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._search_notes_sync.assert_called_once_with(request)

    def test_process_delete_note_success(self):
        """Test sync delete note action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "message": "Note deleted successfully",
        }
        agent._delete_note_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "delete_note",
            "note_id": "note-1",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._delete_note_sync.assert_called_once_with(request)

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestNoteManagerAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_add_note(self):
        """Test async add note action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "message": "Note added successfully",
            "note": {"note_id": "note-1", "title": "Test Note"},
        }
        agent._add_note_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "add_note",
            "project_id": "proj-1",
            "note_type": "design",
            "title": "Test Note",
            "content": "Test content",
            "created_by": "user-1",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_list_notes(self):
        """Test async list notes action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "notes": [],
            "count": 0,
        }
        agent._list_notes_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "list_notes",
            "project_id": "proj-1",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_search_notes(self):
        """Test async search notes action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "results": [],
            "count": 0,
        }
        agent._search_notes_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "search_notes",
            "project_id": "proj-1",
            "query": "test",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_delete_note(self):
        """Test async delete note action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "message": "Note deleted successfully",
        }
        agent._delete_note_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "delete_note",
            "note_id": "note-1",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestNoteManagerPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = NoteManagerAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "notes": [],
            "count": 0,
        }
        agent._list_notes_sync = MagicMock(return_value=mock_result)

        bus_request = {
            "action": "list_notes",
            "project_id": "proj-1",
            "message_id": "msg-222",
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

        agent = NoteManagerAgent(mock_orchestrator)

        capabilities = agent.get_capabilities()
        metadata = agent.get_metadata()

        assert len(capabilities) > 0
        assert "version" in metadata
