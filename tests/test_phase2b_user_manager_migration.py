"""
Phase 2B: UserManagerAgent Migration Tests

Tests for UserManagerAgent after Phase 2B migration to async-first,
agent bus-aware implementation.

Validates:
- Backward compatibility with sync interface
- New async interface with thread pool execution
- Agent bus registration and discovery
- CRUD operations (archive, restore, delete, list)
- Permission checks (users can only manage their own accounts)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from socratic_system.agents.user_manager import UserManagerAgent


class TestUserManagerMigrationSetup:
    """Test UserManagerAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()

        agent = UserManagerAgent(mock_orchestrator)

        assert agent.name == "UserManager"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_auto_registration(self):
        """Test agent registers with bus during initialization (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_bus.registry = mock_registry

        agent = UserManagerAgent(mock_orchestrator)

        # Agent should attempt to register
        assert mock_registry.register.called

    def test_agent_capabilities(self):
        """Test agent declares capabilities for bus discovery (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserManagerAgent(mock_orchestrator)
        capabilities = agent.get_capabilities()

        assert isinstance(capabilities, list)
        assert "user_management" in capabilities
        assert "account_archival" in capabilities
        assert "account_deletion" in capabilities

    def test_agent_metadata(self):
        """Test agent provides metadata for registration (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserManagerAgent(mock_orchestrator)
        metadata = agent.get_metadata()

        assert isinstance(metadata, dict)
        assert metadata["version"] == "2.0"
        assert "description" in metadata


class TestUserManagerSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_archive_user_success(self):
        """Test sync archive user action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.archive_user = MagicMock(return_value=True)

        agent = UserManagerAgent(mock_orchestrator)

        request = {
            "action": "archive_user",
            "username": "alice",
            "requester": "alice",
            "archive_projects": True,
        }

        result = agent.process(request)

        assert result["status"] == "success"
        mock_orchestrator.database.archive_user.assert_called_once_with("alice", True)

    def test_process_archive_user_permission_denied(self):
        """Test archive user with permission check."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserManagerAgent(mock_orchestrator)

        request = {
            "action": "archive_user",
            "username": "alice",
            "requester": "bob",  # Different user - should fail
        }

        result = agent.process(request)

        assert result["status"] == "error"
        assert "own accounts" in result["message"]

    def test_process_restore_user_success(self):
        """Test sync restore user action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.restore_user = MagicMock(return_value=True)

        agent = UserManagerAgent(mock_orchestrator)

        request = {"action": "restore_user", "username": "alice"}

        result = agent.process(request)

        assert result["status"] == "success"
        mock_orchestrator.database.restore_user.assert_called_once_with("alice")

    def test_process_delete_user_success(self):
        """Test sync delete user action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.permanently_delete_user = MagicMock(return_value=True)

        agent = UserManagerAgent(mock_orchestrator)

        request = {
            "action": "delete_user_permanently",
            "username": "alice",
            "requester": "alice",
            "confirmation": "DELETE",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        mock_orchestrator.database.permanently_delete_user.assert_called_once_with("alice")

    def test_process_delete_user_missing_confirmation(self):
        """Test delete user requires confirmation."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserManagerAgent(mock_orchestrator)

        request = {
            "action": "delete_user_permanently",
            "username": "alice",
            "requester": "alice",
            "confirmation": "yes",  # Wrong confirmation
        }

        result = agent.process(request)

        assert result["status"] == "error"
        assert "DELETE" in result["message"]

    def test_process_get_archived_users(self):
        """Test sync get archived users action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.get_archived_items = MagicMock(
            return_value=["alice", "bob"]
        )

        agent = UserManagerAgent(mock_orchestrator)

        request = {"action": "get_archived_users"}

        result = agent.process(request)

        assert result["status"] == "success"
        assert result["archived_users"] == ["alice", "bob"]

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserManagerAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestUserManagerAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_archive_user_success(self):
        """Test async archive user action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.archive_user = MagicMock(return_value=True)

        agent = UserManagerAgent(mock_orchestrator)

        request = {
            "action": "archive_user",
            "username": "alice",
            "requester": "alice",
            "archive_projects": True,
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_restore_user(self):
        """Test async restore user action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.restore_user = MagicMock(return_value=True)

        agent = UserManagerAgent(mock_orchestrator)

        request = {"action": "restore_user", "username": "alice"}

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_delete_user(self):
        """Test async delete user action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.permanently_delete_user = MagicMock(return_value=True)

        agent = UserManagerAgent(mock_orchestrator)

        request = {
            "action": "delete_user_permanently",
            "username": "alice",
            "requester": "alice",
            "confirmation": "DELETE",
        }

        result = await agent.process_async(request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_get_archived_users(self):
        """Test async get archived users action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.get_archived_items = MagicMock(
            return_value=["alice", "bob", "charlie"]
        )

        agent = UserManagerAgent(mock_orchestrator)

        request = {"action": "get_archived_users"}

        result = await agent.process_async(request)

        assert result["status"] == "success"
        assert len(result["archived_users"]) == 3

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserManagerAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestUserManagerPermissions:
    """Test permission checks for user operations."""

    def test_archive_requires_self_permission(self):
        """Test that users can only archive their own accounts."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserManagerAgent(mock_orchestrator)

        # Try to archive another user
        request = {
            "action": "archive_user",
            "username": "alice",
            "requester": "bob",
        }

        result = agent.process(request)

        assert result["status"] == "error"

    def test_delete_requires_self_permission(self):
        """Test that users can only delete their own accounts."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = UserManagerAgent(mock_orchestrator)

        # Try to delete another user
        request = {
            "action": "delete_user_permanently",
            "username": "alice",
            "requester": "bob",
            "confirmation": "DELETE",
        }

        result = agent.process(request)

        assert result["status"] == "error"


class TestUserManagerDatabaseOperations:
    """Test database operation behavior."""

    def test_archive_user_database_failure(self):
        """Test handling of database archive failure."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.archive_user = MagicMock(return_value=False)

        agent = UserManagerAgent(mock_orchestrator)

        request = {
            "action": "archive_user",
            "username": "alice",
            "requester": "alice",
        }

        result = agent.process(request)

        assert result["status"] == "error"
        assert "Failed to archive" in result["message"]

    def test_restore_user_database_failure(self):
        """Test handling of database restore failure."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.restore_user = MagicMock(return_value=False)

        agent = UserManagerAgent(mock_orchestrator)

        request = {"action": "restore_user", "username": "alice"}

        result = agent.process(request)

        assert result["status"] == "error"


class TestUserManagerPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.database = MagicMock()
        mock_orchestrator.database.get_archived_items = MagicMock(return_value=[])

        agent = UserManagerAgent(mock_orchestrator)

        # Bus sends request as RequestMessage-like dict
        bus_request = {
            "action": "get_archived_users",
            "message_id": "msg-123",
        }

        # Test via process_async
        import asyncio
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

        agent = UserManagerAgent(mock_orchestrator)

        # Should have capabilities for discovery
        capabilities = agent.get_capabilities()
        metadata = agent.get_metadata()

        assert len(capabilities) > 0
        assert "version" in metadata
