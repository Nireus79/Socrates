"""
Phase 2: Agent Registry Tests

Tests for agent discovery, registration, and lifecycle management.
Validates the foundation of the Agent Bus system.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from socratic_system.messaging.agent_registry import (
    AgentMetadata,
    AgentHandler,
    AgentRegistry,
)


class TestAgentMetadata:
    """Test AgentMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating agent metadata."""
        meta = AgentMetadata(
            name="test_agent",
            capabilities=["test", "debug"],
            status="active",
            version="1.0",
        )

        assert meta.name == "test_agent"
        assert meta.capabilities == ["test", "debug"]
        assert meta.status == "active"
        assert meta.version == "1.0"

    def test_metadata_is_healthy_true(self):
        """Test health check when recently updated."""
        meta = AgentMetadata(name="agent")
        assert meta.is_healthy(timeout_seconds=60)

    def test_metadata_is_healthy_false(self):
        """Test health check when stale."""
        import time

        meta = AgentMetadata(name="agent")
        time.sleep(0.1)
        assert not meta.is_healthy(timeout_seconds=0)

    def test_metadata_update_heartbeat(self):
        """Test heartbeat update."""
        import time

        meta = AgentMetadata(name="agent")
        old_heartbeat = meta.last_heartbeat
        time.sleep(0.01)
        meta.update_heartbeat()
        assert meta.last_heartbeat > old_heartbeat


class TestAgentHandler:
    """Test AgentHandler wrapper."""

    @pytest.mark.asyncio
    async def test_handler_invoke_async(self):
        """Test invoking async handler."""
        async def async_handler(request):
            return {"status": "success", "data": request}

        handler = AgentHandler(
            agent_name="test",
            handler=async_handler,
            supports_async=True,
        )

        result = await handler.invoke({"action": "test"})
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_handler_invoke_sync_wrapped(self):
        """Test invoking sync handler wrapped in async."""
        def sync_handler(request):
            return {"status": "success", "data": request}

        handler = AgentHandler(
            agent_name="test",
            handler=sync_handler,
            supports_sync=True,
            supports_async=False,
        )

        result = await handler.invoke({"action": "test"})
        assert result["status"] == "success"


class TestAgentRegistryInitialization:
    """Test AgentRegistry initialization."""

    def test_registry_initialization(self):
        """Test creating registry."""
        registry = AgentRegistry(health_check_timeout=60)
        assert registry.count() == 0
        assert registry.logger is not None

    def test_registry_thread_safe(self):
        """Test registry is thread-safe."""
        registry = AgentRegistry()
        assert hasattr(registry, "_lock")
        assert registry._lock is not None


class TestAgentRegistryRegistration:
    """Test agent registration and retrieval."""

    def test_register_agent(self):
        """Test registering an agent."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register(
            agent_name="test_agent",
            handler=handler,
            capabilities=["test"],
        )

        assert registry.count() == 1
        assert registry.is_available("test_agent")

    def test_register_with_metadata(self):
        """Test registering with metadata."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        metadata = {"version": "2.0", "author": "test"}

        registry.register(
            agent_name="agent1",
            handler=handler,
            metadata=metadata,
        )

        meta = registry.get_agent("agent1")
        assert meta.metadata == metadata

    def test_register_duplicate_agent(self):
        """Test re-registering an agent (should update)."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register("agent1", handler, capabilities=["v1"])
        registry.register("agent1", handler, capabilities=["v2"])

        # Should have 1 agent (updated, not duplicated)
        assert registry.count() == 1
        agent = registry.get_agent("agent1")
        assert agent.capabilities == ["v2"]

    def test_get_agent_not_found(self):
        """Test getting non-existent agent."""
        registry = AgentRegistry()
        assert registry.get_agent("nonexistent") is None

    def test_get_handler(self):
        """Test retrieving agent handler."""
        async def handler(req):
            return {"result": "ok"}

        registry = AgentRegistry()
        registry.register("agent1", handler)

        retrieved_handler = registry.get_handler("agent1")
        assert retrieved_handler is not None
        assert retrieved_handler.agent_name == "agent1"

    def test_unregister_agent(self):
        """Test unregistering an agent."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register("agent1", handler)
        assert registry.count() == 1

        success = registry.unregister("agent1")
        assert success
        assert registry.count() == 0

    def test_unregister_nonexistent(self):
        """Test unregistering non-existent agent."""
        registry = AgentRegistry()
        success = registry.unregister("nonexistent")
        assert not success


class TestAgentRegistryListing:
    """Test agent listing and discovery."""

    def test_list_all_agents(self):
        """Test listing all agents."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register("agent1", handler)
        registry.register("agent2", handler)
        registry.register("agent3", handler)

        agents = registry.list_agents()
        assert len(agents) == 3
        assert "agent1" in agents
        assert "agent2" in agents
        assert "agent3" in agents

    def test_list_by_capability(self):
        """Test listing agents by capability."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register("agent1", handler, capabilities=["code_gen", "test"])
        registry.register("agent2", handler, capabilities=["test"])
        registry.register("agent3", handler, capabilities=["code_gen"])

        # Find agents with "code_gen" capability
        code_agents = registry.list_agents(capability="code_gen")
        assert len(code_agents) == 2
        assert "agent1" in code_agents
        assert "agent3" in code_agents

        # Find agents with "test" capability
        test_agents = registry.list_agents(capability="test")
        assert len(test_agents) == 2
        assert "agent1" in test_agents
        assert "agent2" in test_agents

    def test_find_by_capability(self):
        """Test finding agents by capability."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register("agent1", handler, capabilities=["project_mgmt"])
        registry.register("agent2", handler, capabilities=["project_mgmt", "code"])
        registry.register("agent3", handler, capabilities=["code"])

        found = registry.find_by_capability("project_mgmt")
        assert len(found) == 2
        assert "agent1" in found
        assert "agent2" in found

    def test_list_empty_registry(self):
        """Test listing from empty registry."""
        registry = AgentRegistry()
        agents = registry.list_agents()
        assert agents == []


class TestAgentRegistryStatus:
    """Test agent status management."""

    def test_is_available_true(self):
        """Test agent availability check when available."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register("agent1", handler)
        assert registry.is_available("agent1")

    def test_is_available_false_nonexistent(self):
        """Test availability check for non-existent agent."""
        registry = AgentRegistry()
        assert not registry.is_available("nonexistent")

    def test_set_status(self):
        """Test setting agent status."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register("agent1", handler)

        registry.set_status("agent1", "busy")
        assert registry.get_status("agent1") == "busy"

        registry.set_status("agent1", "offline")
        assert registry.get_status("agent1") == "offline"

    def test_set_status_nonexistent(self):
        """Test setting status on non-existent agent."""
        registry = AgentRegistry()
        success = registry.set_status("nonexistent", "busy")
        assert not success

    def test_get_status(self):
        """Test getting agent status."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register("agent1", handler)

        status = registry.get_status("agent1")
        assert status == "active"  # Default status

    def test_get_capabilities(self):
        """Test getting agent capabilities."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register(
            "agent1", handler, capabilities=["code_gen", "testing", "docs"]
        )

        capabilities = registry.get_capabilities("agent1")
        assert len(capabilities) == 3
        assert "code_gen" in capabilities


class TestAgentRegistryHeartbeat:
    """Test agent heartbeat tracking."""

    def test_update_heartbeat(self):
        """Test updating agent heartbeat."""
        import time

        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register("agent1", handler)

        old_time = registry.get_agent("agent1").last_heartbeat
        time.sleep(0.01)

        success = registry.update_heartbeat("agent1")
        assert success

        new_time = registry.get_agent("agent1").last_heartbeat
        assert new_time > old_time

    def test_update_heartbeat_nonexistent(self):
        """Test updating heartbeat for non-existent agent."""
        registry = AgentRegistry()
        success = registry.update_heartbeat("nonexistent")
        assert not success


class TestAgentRegistryMetadata:
    """Test metadata retrieval."""

    def test_get_all_metadata(self):
        """Test retrieving all agent metadata."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register("agent1", handler, capabilities=["test"])
        registry.register("agent2", handler, capabilities=["code"])

        all_meta = registry.get_all_metadata()
        assert len(all_meta) == 2
        assert "agent1" in all_meta
        assert "agent2" in all_meta
        assert all_meta["agent1"].capabilities == ["test"]
        assert all_meta["agent2"].capabilities == ["code"]


class TestAgentRegistryClearing:
    """Test registry clearing (for testing)."""

    def test_clear_registry(self):
        """Test clearing all agents from registry."""
        async def handler(req):
            return {}

        registry = AgentRegistry()
        registry.register("agent1", handler)
        registry.register("agent2", handler)
        assert registry.count() == 2

        registry.clear()
        assert registry.count() == 0
