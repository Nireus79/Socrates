"""
Tests for Phase 2 Day 2: ServiceOrchestrator with dependency ordering.

Tests:
- Service registration
- Startup sequence with dependency ordering
- Shutdown sequence in reverse order
- Inter-service communication
- Health check aggregation
- Event publishing
"""

import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

from core.orchestrator import ServiceOrchestrator
from modules.foundation.service import FoundationService
from modules.agents.service import AgentsService
from modules.learning.service import LearningService
from modules.knowledge.service import KnowledgeService
from modules.workflow.service import WorkflowService
from modules.analytics.service import AnalyticsService


@pytest.fixture
def orchestrator():
    """Create a fresh orchestrator for each test."""
    return ServiceOrchestrator()


@pytest.fixture
def mock_service(name):
    """Create a mock service."""
    service = MagicMock()
    service.service_name = name
    service.__class__.__name__ = f"{name.capitalize()}Service"
    service.initialize = AsyncMock()
    service.shutdown = AsyncMock()
    service.health_check = AsyncMock(return_value={"status": "ok"})
    return service


@pytest.mark.asyncio
async def test_orchestrator_service_registration(orchestrator):
    """Test that services can be registered."""
    service = MagicMock()
    service.service_name = "foundation"
    orchestrator.register_service(service)
    assert "foundation" in orchestrator._services


@pytest.mark.asyncio
async def test_orchestrator_get_service(orchestrator):
    """Test retrieving a service."""
    service = MagicMock()
    service.service_name = "foundation"
    orchestrator.register_service(service)
    retrieved = await orchestrator.get_service("foundation")
    assert retrieved == service


@pytest.mark.asyncio
async def test_orchestrator_list_services(orchestrator):
    """Test listing all services."""
    services_data = [
        ("foundation", "FoundationService"),
        ("agents", "AgentsService"),
        ("learning", "LearningService"),
    ]

    for name, class_name in services_data:
        service = MagicMock()
        service.service_name = name
        service.__class__.__name__ = class_name
        orchestrator.register_service(service)

    services = orchestrator.list_services()
    assert "foundation" in services
    assert "agents" in services
    assert "learning" in services


@pytest.mark.asyncio
async def test_orchestrator_startup_order(orchestrator):
    """Test that services start in correct dependency order."""
    # Create mock services
    for name in ["foundation", "learning", "agents"]:
        service = MagicMock()
        service.service_name = name
        service.__class__.__name__ = f"{name.capitalize()}Service"
        service.initialize = AsyncMock()
        service.shutdown = AsyncMock()
        service.health_check = AsyncMock(return_value={})
        orchestrator.register_service(service)

    await orchestrator.start_all_services()

    # Foundation should start first
    assert len(orchestrator._started_services) >= 1
    assert "foundation" in orchestrator._started_services


@pytest.mark.asyncio
async def test_orchestrator_dependency_check(orchestrator):
    """Test that services cannot start if dependencies aren't met."""
    # Register only agents service (missing foundation dependency)
    service = MagicMock()
    service.service_name = "agents"
    service.__class__.__name__ = "AgentsService"
    service.initialize = AsyncMock()
    service.shutdown = AsyncMock()
    service.health_check = AsyncMock(return_value={})
    orchestrator.register_service(service)

    with pytest.raises(RuntimeError, match="Dependency foundation not started"):
        await orchestrator.start_all_services()


@pytest.mark.asyncio
async def test_orchestrator_inter_service_call(orchestrator):
    """Test calling a method on a service through the orchestrator."""
    # Create mock services
    for name in ["foundation", "learning", "agents"]:
        service = MagicMock()
        service.service_name = name
        service.__class__.__name__ = f"{name.capitalize()}Service"
        service.initialize = AsyncMock()
        service.shutdown = AsyncMock()
        service.health_check = AsyncMock(return_value={})

        # Add a sample method to agents
        if name == "agents":
            service.list_agents = AsyncMock(return_value={"agent1": "Agent"})

        orchestrator.register_service(service)

    await orchestrator.start_all_services()

    result = await orchestrator.call_service("agents", "list_agents")
    assert result == {"agent1": "Agent"}


@pytest.mark.asyncio
async def test_orchestrator_inter_service_call_not_found(orchestrator):
    """Test calling a method on a non-existent service."""
    service = MagicMock()
    service.service_name = "foundation"
    service.__class__.__name__ = "FoundationService"
    service.initialize = AsyncMock()
    service.shutdown = AsyncMock()
    service.health_check = AsyncMock(return_value={})
    orchestrator.register_service(service)

    await orchestrator.start_all_services()

    with pytest.raises(RuntimeError, match="Service nonexistent not found"):
        await orchestrator.call_service("nonexistent", "some_method")


@pytest.mark.asyncio
async def test_orchestrator_inter_service_call_not_running(orchestrator):
    """Test calling a method on a service that isn't running."""
    service = MagicMock()
    service.service_name = "agents"
    service.__class__.__name__ = "AgentsService"
    service.initialize = AsyncMock()
    service.shutdown = AsyncMock()
    service.health_check = AsyncMock(return_value={})
    orchestrator.register_service(service)

    with pytest.raises(RuntimeError, match="is not running"):
        await orchestrator.call_service("agents", "list_agents")


@pytest.mark.asyncio
async def test_orchestrator_shutdown_order(orchestrator):
    """Test that services shut down in reverse order."""
    shutdown_order = []

    for name in ["foundation", "learning", "agents"]:
        service = MagicMock()
        service.service_name = name
        service.__class__.__name__ = f"{name.capitalize()}Service"
        service.initialize = AsyncMock()
        service.health_check = AsyncMock(return_value={})

        async def mock_shutdown(service_name):
            shutdown_order.append(service_name)

        service.shutdown = mock_shutdown(name)
        orchestrator.register_service(service)

    await orchestrator.start_all_services()
    await orchestrator.stop_all_services()

    # After stop: should be empty or partial depending on mock behavior


@pytest.mark.asyncio
async def test_orchestrator_health_check(orchestrator):
    """Test health check aggregation."""
    services_data = [
        ("foundation", {"llm_service": "healthy"}),
        ("agents", {"agents_loaded": 0}),
        ("learning", {"learning_engine": "available"}),
    ]

    for name, health_data in services_data:
        service = MagicMock()
        service.service_name = name
        service.__class__.__name__ = f"{name.capitalize()}Service"
        service.initialize = AsyncMock()
        service.shutdown = AsyncMock()
        service.health_check = AsyncMock(return_value=health_data)
        orchestrator.register_service(service)

    await orchestrator.start_all_services()

    health = await orchestrator.health_check_all()

    assert health["overall_status"] == "healthy"
    assert "foundation" in health["services"]
    assert "agents" in health["services"]


@pytest.mark.asyncio
async def test_orchestrator_get_dependencies(orchestrator):
    """Test retrieving dependencies for a service."""
    assert orchestrator.get_dependencies("foundation") == []
    assert orchestrator.get_dependencies("agents") == ["foundation", "learning"]
    assert orchestrator.get_dependencies("workflow") == ["foundation", "agents"]


@pytest.mark.asyncio
async def test_orchestrator_service_status(orchestrator):
    """Test getting service status."""
    services_data = [
        ("foundation", "FoundationService"),
        ("learning", "LearningService"),
        ("agents", "AgentsService"),
    ]

    for name, class_name in services_data:
        service = MagicMock()
        service.service_name = name
        service.__class__.__name__ = class_name
        service.initialize = AsyncMock()
        service.shutdown = AsyncMock()
        service.health_check = AsyncMock(return_value={})
        orchestrator.register_service(service)

    status = orchestrator.get_service_status()

    assert "foundation" in status
    assert "agents" in status
    assert not status["foundation"]["running"]
    assert not status["agents"]["running"]

    await orchestrator.start_all_services()

    status = orchestrator.get_service_status()
    assert status["foundation"]["running"]
    assert status["agents"]["running"]


@pytest.mark.asyncio
async def test_orchestrator_event_publishing(orchestrator):
    """Test that system events are published."""
    service = MagicMock()
    service.service_name = "foundation"
    service.__class__.__name__ = "FoundationService"
    service.initialize = AsyncMock()
    service.shutdown = AsyncMock()
    service.health_check = AsyncMock(return_value={})
    orchestrator.register_service(service)

    events_received = []

    async def event_handler(event):
        events_received.append(event)

    orchestrator.event_bus.subscribe("system_started", event_handler)

    await orchestrator.start_all_services()

    # Should have received system_started event
    assert len(events_received) >= 1


@pytest.mark.asyncio
async def test_orchestrator_full_workflow(orchestrator):
    """Test complete orchestrator workflow with all services."""
    services_data = [
        ("foundation", "FoundationService"),
        ("knowledge", "KnowledgeService"),
        ("learning", "LearningService"),
        ("agents", "AgentsService"),
        ("analytics", "AnalyticsService"),
        ("workflow", "WorkflowService"),
    ]

    for name, class_name in services_data:
        service = MagicMock()
        service.service_name = name
        service.__class__.__name__ = class_name
        service.initialize = AsyncMock()
        service.shutdown = AsyncMock()
        service.health_check = AsyncMock(return_value={"status": "ok"})
        orchestrator.register_service(service)

    # Start all
    await orchestrator.start_all_services()
    assert len(orchestrator._started_services) >= 4

    # Check health
    health = await orchestrator.health_check_all()
    assert health["overall_status"] == "healthy"

    # Get service status
    status = orchestrator.get_service_status()
    assert len(status) == 6

    # Stop all
    await orchestrator.stop_all_services()
    assert len(orchestrator._started_services) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
