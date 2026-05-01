"""
Phase 2: Agent Bus Integration Tests

Tests for agent-to-agent messaging via the Agent Bus.
Validates registry integration and message routing.
"""

import asyncio
import pytest

from socratic_system.events import EventEmitter
from socratic_system.messaging.agent_registry import AgentRegistry
from socratic_system.messaging.agent_bus import AgentBus
from socratic_system.messaging.messages import RequestMessage


class TestAgentBusBasics:
    """Test basic AgentBus functionality with registry."""

    def test_bus_init_with_registry(self):
        """Test initializing bus with registry."""
        emitter = EventEmitter()
        registry = AgentRegistry()

        bus = AgentBus(
            event_emitter=emitter,
            registry=registry,
            max_concurrent_requests=100,
            default_timeout=30.0,
        )

        assert bus.registry is registry
        assert bus.event_emitter is emitter
        assert bus.default_timeout == 30.0

    def test_bus_init_without_registry(self):
        """Test initializing bus without registry (backward compat)."""
        emitter = EventEmitter()
        bus = AgentBus(event_emitter=emitter)
        assert bus.registry is None


class TestAgentBusDirectInvocation:
    """Test direct handler invocation through registry."""

    @pytest.mark.asyncio
    async def test_simple_request_response(self):
        """Test simple request-response via direct invocation."""
        emitter = EventEmitter()
        registry = AgentRegistry()
        bus = AgentBus(event_emitter=emitter, registry=registry)

        async def handler(request):
            return {
                "status": "success",
                "action": request.action,
                "agent": "test_agent",
            }

        registry.register(
            agent_name="test_agent",
            handler=handler,
            capabilities=["test"],
        )

        result = await bus.send_request(
            target_agent="test_agent",
            action="test_action",
            payload={"data": "test"},
        )

        assert result["status"] == "success"
        assert result["action"] == "test_action"
        assert bus.metrics["direct_handler_invocations"] >= 1

    @pytest.mark.asyncio
    async def test_handler_receives_request_message(self):
        """Test handler receives proper RequestMessage object."""
        emitter = EventEmitter()
        registry = AgentRegistry()
        bus = AgentBus(event_emitter=emitter, registry=registry)

        received_request = None

        async def test_handler(request):
            nonlocal received_request
            received_request = request
            return {"status": "success"}

        registry.register("agent", handler=test_handler)

        await bus.send_request(
            target_agent="agent",
            action="action1",
            payload={"key": "value"},
        )

        assert received_request is not None
        assert isinstance(received_request, RequestMessage)
        assert received_request.action == "action1"
        assert received_request.payload == {"key": "value"}

    @pytest.mark.asyncio
    async def test_handler_error_propagation(self):
        """Test error from handler is propagated."""
        emitter = EventEmitter()
        registry = AgentRegistry()
        bus = AgentBus(event_emitter=emitter, registry=registry, default_timeout=1.0)

        async def error_handler(request):
            raise ValueError("Test error from handler")

        registry.register("error_agent", handler=error_handler)

        # Error should be propagated from the handler
        with pytest.raises((ValueError, Exception)):
            await bus.send_request(
                target_agent="error_agent",
                action="test",
            )


class TestAgentBusBroadcast:
    """Test broadcast messaging."""

    @pytest.mark.asyncio
    async def test_broadcast_all_agents(self):
        """Test broadcasting to all registered agents."""
        emitter = EventEmitter()
        registry = AgentRegistry()
        bus = AgentBus(event_emitter=emitter, registry=registry)

        async def handler1(request):
            return {"agent": "agent1"}

        async def handler2(request):
            return {"agent": "agent2"}

        async def handler3(request):
            return {"agent": "agent3"}

        registry.register("agent1", handler=handler1)
        registry.register("agent2", handler=handler2)
        registry.register("agent3", handler=handler3)

        result = await bus.broadcast(
            action="refresh",
            payload={"type": "cache"},
        )

        assert result["status"] == "success"
        assert result["count"] == 3
        assert len(result["agents_notified"]) == 3

    @pytest.mark.asyncio
    async def test_broadcast_with_capability_filter(self):
        """Test broadcast with capability filtering."""
        emitter = EventEmitter()
        registry = AgentRegistry()
        bus = AgentBus(event_emitter=emitter, registry=registry)

        async def handler1(request):
            return {"status": "success"}

        async def handler2(request):
            return {"status": "success"}

        registry.register("agent1", handler=handler1, capabilities=["cache_aware"])
        registry.register("agent2", handler=handler2, capabilities=["other"])

        result = await bus.broadcast(
            action="refresh_cache",
            capability_filter="cache_aware",
        )

        assert result["count"] == 1
        assert "agent1" in result["agents_notified"]
        assert "agent2" not in result["agents_notified"]

    @pytest.mark.asyncio
    async def test_broadcast_no_matching(self):
        """Test broadcast when no agents match filter."""
        emitter = EventEmitter()
        registry = AgentRegistry()
        bus = AgentBus(event_emitter=emitter, registry=registry)

        async def handler(request):
            return {"status": "success"}

        registry.register("agent1", handler=handler, capabilities=["other"])

        result = await bus.broadcast(
            action="refresh",
            capability_filter="nonexistent",
        )

        assert result["status"] == "success"
        # Check for agents_notified instead of count
        assert len(result.get("agents_notified", [])) == 0


class TestAgentBusMetrics:
    """Test metrics tracking."""

    @pytest.mark.asyncio
    async def test_metrics_direct_invocation(self):
        """Test metrics for direct invocation."""
        emitter = EventEmitter()
        registry = AgentRegistry()
        bus = AgentBus(event_emitter=emitter, registry=registry)

        async def handler(request):
            return {"status": "success"}

        registry.register("agent", handler=handler)

        initial = bus.metrics["direct_handler_invocations"]

        await bus.send_request(target_agent="agent", action="test")

        assert bus.metrics["direct_handler_invocations"] > initial

    @pytest.mark.asyncio
    async def test_metrics_successful_request(self):
        """Test metrics for successful requests."""
        emitter = EventEmitter()
        registry = AgentRegistry()
        bus = AgentBus(event_emitter=emitter, registry=registry)

        async def handler(request):
            return {"status": "success"}

        registry.register("agent", handler=handler)

        initial = bus.metrics["successful_requests"]

        await bus.send_request(target_agent="agent", action="test")

        assert bus.metrics["successful_requests"] > initial

    def test_get_metrics_complete(self):
        """Test getting complete metrics."""
        emitter = EventEmitter()
        registry = AgentRegistry()
        bus = AgentBus(event_emitter=emitter, registry=registry)

        metrics = bus.get_metrics()

        assert "total_requests" in metrics
        assert "successful_requests" in metrics
        assert "failed_requests" in metrics
        assert "direct_handler_invocations" in metrics
        assert "active_requests" in metrics


class TestAgentBusAgentNotFound:
    """Test handling of missing agents."""

    @pytest.mark.asyncio
    async def test_agent_not_found_timeout(self):
        """Test timeout when agent not registered."""
        emitter = EventEmitter()
        registry = AgentRegistry()
        bus = AgentBus(event_emitter=emitter, registry=registry, default_timeout=0.5)

        from socratic_system.messaging.exceptions import AgentTimeoutError

        # Unregistered agent will timeout (event-based routing has no listeners)
        with pytest.raises(AgentTimeoutError):
            await bus.send_request(
                target_agent="nonexistent",
                action="test",
                timeout=0.5,
            )


class TestAgentBusTimeout:
    """Test timeout handling."""

    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """Test timeout in direct invocation."""
        emitter = EventEmitter()
        registry = AgentRegistry()
        bus = AgentBus(event_emitter=emitter, registry=registry, default_timeout=0.1)

        async def slow_handler(request):
            await asyncio.sleep(1)
            return {"status": "success"}

        registry.register("slow_agent", handler=slow_handler)

        from socratic_system.messaging.exceptions import AgentTimeoutError

        with pytest.raises(AgentTimeoutError):
            await bus.send_request(
                target_agent="slow_agent",
                action="test",
                timeout=0.1,
            )

        assert bus.metrics["timeout_requests"] >= 1
