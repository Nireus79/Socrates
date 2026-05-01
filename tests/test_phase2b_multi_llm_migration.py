"""Phase 2B: MultiLLMAgent Migration Tests"""
import asyncio
import pytest
from unittest.mock import MagicMock
from socratic_system.agents.multi_llm_agent import MultiLLMAgent


class TestMultiLLMMigrationSetup:
    """Test MultiLLMAgent migration setup and initialization."""

    def test_agent_initialization(self):
        """Test agent initializes correctly after Phase 2B migration."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()
        mock_orchestrator.agent_registry = MagicMock()
        mock_orchestrator.agent_bus.registry = mock_orchestrator.agent_registry

        agent = MultiLLMAgent(mock_orchestrator)

        assert agent.name == "Multi-LLM Manager"
        assert agent.orchestrator is mock_orchestrator

    def test_agent_auto_registration(self):
        """Test agent registers with bus during initialization (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_registry = MagicMock()
        mock_bus = MagicMock()
        mock_orchestrator.agent_bus = mock_bus
        mock_orchestrator.agent_registry = mock_registry
        mock_bus.registry = mock_registry

        agent = MultiLLMAgent(mock_orchestrator)

        assert mock_registry.register.called

    def test_agent_capabilities(self):
        """Test agent declares capabilities for bus discovery (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)
        capabilities = agent.get_capabilities()

        assert isinstance(capabilities, list)
        assert "provider_management" in capabilities
        assert "api_key_management" in capabilities
        assert "auth_configuration" in capabilities
        assert "usage_tracking" in capabilities
        assert "model_selection" in capabilities

    def test_agent_metadata(self):
        """Test agent provides metadata for registration (Phase 2B)."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)
        metadata = agent.get_metadata()

        assert isinstance(metadata, dict)
        assert metadata["version"] == "2.0"
        assert "description" in metadata


class TestMultiLLMSyncInterface:
    """Test backward compatibility with sync process() interface."""

    def test_process_list_providers_success(self):
        """Test sync list providers action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "providers": [],
            "count": 0,
        }
        agent._list_providers_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "list_providers",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._list_providers_sync.assert_called_once_with(request)

    def test_process_get_provider_config_success(self):
        """Test sync get provider config action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "config": {},
        }
        agent._get_provider_config_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "get_provider_config",
            "user_id": "user-1",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._get_provider_config_sync.assert_called_once_with(request)

    def test_process_set_default_provider_success(self):
        """Test sync set default provider action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "provider": "claude",
        }
        agent._set_default_provider_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "set_default_provider",
            "user_id": "user-1",
            "provider": "claude",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._set_default_provider_sync.assert_called_once_with(request)

    def test_process_set_provider_model_success(self):
        """Test sync set provider model action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "model": "claude-3-opus",
        }
        agent._set_provider_model_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "set_provider_model",
            "user_id": "user-1",
            "provider": "claude",
            "model": "claude-3-opus",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._set_provider_model_sync.assert_called_once_with(request)

    def test_process_add_api_key_success(self):
        """Test sync add API key action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "key_id": "key-1",
        }
        agent._add_api_key_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "add_api_key",
            "user_id": "user-1",
            "provider": "claude",
            "api_key": "sk-test",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._add_api_key_sync.assert_called_once_with(request)

    def test_process_remove_api_key_success(self):
        """Test sync remove API key action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
        }
        agent._remove_api_key_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "remove_api_key",
            "user_id": "user-1",
            "provider": "claude",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._remove_api_key_sync.assert_called_once_with(request)

    def test_process_set_auth_method_success(self):
        """Test sync set auth method action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "auth_method": "api_key",
        }
        agent._set_auth_method_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "set_auth_method",
            "user_id": "user-1",
            "provider": "claude",
            "auth_method": "api_key",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._set_auth_method_sync.assert_called_once_with(request)

    def test_process_track_usage_success(self):
        """Test sync track usage action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "tracked": True,
        }
        agent._track_usage_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "track_usage",
            "user_id": "user-1",
            "provider": "claude",
            "model": "claude-3-opus",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._track_usage_sync.assert_called_once_with(request)

    def test_process_get_usage_stats_success(self):
        """Test sync get usage stats action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "stats": {},
        }
        agent._get_usage_stats_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "get_usage_stats",
            "user_id": "user-1",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._get_usage_stats_sync.assert_called_once_with(request)

    def test_process_get_provider_models_success(self):
        """Test sync get provider models action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {
            "status": "success",
            "models": [],
        }
        agent._get_provider_models_sync = MagicMock(return_value=mock_result)

        request = {
            "action": "get_provider_models",
            "provider": "claude",
        }

        result = agent.process(request)

        assert result["status"] == "success"
        agent._get_provider_models_sync.assert_called_once_with(request)

    def test_process_unknown_action(self):
        """Test handling unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        result = agent.process({"action": "unknown_action"})

        assert result["status"] == "error"
        assert "Unknown action" in result["message"]


class TestMultiLLMAsyncInterface:
    """Test new async process_async() interface (Phase 2B)."""

    @pytest.mark.asyncio
    async def test_process_async_list_providers(self):
        """Test async list providers action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {"status": "success", "providers": []}
        agent._list_providers_sync = MagicMock(return_value=mock_result)

        result = await agent.process_async({"action": "list_providers"})

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_get_provider_config(self):
        """Test async get provider config action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {"status": "success", "config": {}}
        agent._get_provider_config_sync = MagicMock(return_value=mock_result)

        result = await agent.process_async(
            {"action": "get_provider_config", "user_id": "user-1"}
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_set_default_provider(self):
        """Test async set default provider action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {"status": "success", "provider": "claude"}
        agent._set_default_provider_sync = MagicMock(return_value=mock_result)

        result = await agent.process_async(
            {"action": "set_default_provider", "user_id": "user-1", "provider": "claude"}
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_set_provider_model(self):
        """Test async set provider model action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {"status": "success", "model": "claude-3-opus"}
        agent._set_provider_model_sync = MagicMock(return_value=mock_result)

        result = await agent.process_async(
            {
                "action": "set_provider_model",
                "user_id": "user-1",
                "provider": "claude",
                "model": "claude-3-opus",
            }
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_add_api_key(self):
        """Test async add API key action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {"status": "success", "key_id": "key-1"}
        agent._add_api_key_sync = MagicMock(return_value=mock_result)

        result = await agent.process_async(
            {
                "action": "add_api_key",
                "user_id": "user-1",
                "provider": "claude",
                "api_key": "sk-test",
            }
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_remove_api_key(self):
        """Test async remove API key action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {"status": "success"}
        agent._remove_api_key_sync = MagicMock(return_value=mock_result)

        result = await agent.process_async(
            {"action": "remove_api_key", "user_id": "user-1", "provider": "claude"}
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_set_auth_method(self):
        """Test async set auth method action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {"status": "success", "auth_method": "api_key"}
        agent._set_auth_method_sync = MagicMock(return_value=mock_result)

        result = await agent.process_async(
            {
                "action": "set_auth_method",
                "user_id": "user-1",
                "provider": "claude",
                "auth_method": "api_key",
            }
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_track_usage(self):
        """Test async track usage action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {"status": "success", "tracked": True}
        agent._track_usage_sync = MagicMock(return_value=mock_result)

        result = await agent.process_async(
            {
                "action": "track_usage",
                "user_id": "user-1",
                "provider": "claude",
                "model": "claude-3-opus",
            }
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_get_usage_stats(self):
        """Test async get usage stats action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {"status": "success", "stats": {}}
        agent._get_usage_stats_sync = MagicMock(return_value=mock_result)

        result = await agent.process_async({"action": "get_usage_stats", "user_id": "user-1"})

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_get_provider_models(self):
        """Test async get provider models action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {"status": "success", "models": []}
        agent._get_provider_models_sync = MagicMock(return_value=mock_result)

        result = await agent.process_async(
            {"action": "get_provider_models", "provider": "claude"}
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_async_unknown_action(self):
        """Test async handling of unknown action."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        result = await agent.process_async({"action": "unknown"})

        assert result["status"] == "error"


class TestMultiLLMPhase2BIntegration:
    """Test Phase 2B integration with agent bus."""

    def test_bus_message_handler(self):
        """Test agent can handle messages from bus."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.agent_bus = MagicMock()

        agent = MultiLLMAgent(mock_orchestrator)

        mock_result = {"status": "success", "providers": []}
        agent._list_providers_sync = MagicMock(return_value=mock_result)

        bus_request = {
            "action": "list_providers",
            "message_id": "msg-555",
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

        agent = MultiLLMAgent(mock_orchestrator)

        capabilities = agent.get_capabilities()
        metadata = agent.get_metadata()

        assert len(capabilities) > 0
        assert "version" in metadata
