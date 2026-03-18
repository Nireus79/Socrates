"""
Tests for Phase 2 Day 3: EventBus publish/subscribe and service event publishing.

Tests:
- Event publishing from services
- Event subscription and handling
- Event routing to subscribers
- Event history tracking
- Service event broadcasting
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from core.event_bus import Event, EventBus
from core.orchestrator import ServiceOrchestrator
from modules.analytics.service import SkillAnalytics


@pytest.fixture
def event_bus():
    """Create a fresh event bus for each test."""
    return EventBus()


@pytest.fixture
def orchestrator():
    """Create a fresh orchestrator for each test."""
    return ServiceOrchestrator()


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe(event_bus):
    """Test basic publish/subscribe functionality."""
    events_received = []

    async def handler(event: Event):
        events_received.append(event)

    # Subscribe to event type
    event_bus.subscribe("test_event", handler)

    # Publish event
    await event_bus.publish("test_event", "test_service", {"data": "test"})

    # Verify event was received
    assert len(events_received) == 1
    assert events_received[0].event_type == "test_event"
    assert events_received[0].source_service == "test_service"


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers(event_bus):
    """Test multiple subscribers receiving same event."""
    events1 = []
    events2 = []

    async def handler1(event: Event):
        events1.append(event)

    async def handler2(event: Event):
        events2.append(event)

    # Subscribe multiple handlers
    event_bus.subscribe("test_event", handler1)
    event_bus.subscribe("test_event", handler2)

    # Publish event
    await event_bus.publish("test_event", "test_service", {"data": "test"})

    # Both subscribers should receive event
    assert len(events1) == 1
    assert len(events2) == 1


@pytest.mark.asyncio
async def test_event_bus_event_history(event_bus):
    """Test event history tracking."""
    # Publish several events
    await event_bus.publish("event1", "service1", {"data": "data1"})
    await event_bus.publish("event2", "service2", {"data": "data2"})
    await event_bus.publish("event1", "service1", {"data": "data3"})

    # Get all events
    all_events = event_bus.get_event_history()
    assert len(all_events) == 3

    # Filter by event type
    event1_events = event_bus.get_event_history(event_type="event1")
    assert len(event1_events) == 2

    # Limit results
    limited_events = event_bus.get_event_history(limit=2)
    assert len(limited_events) == 2


@pytest.mark.asyncio
async def test_event_bus_clear_history(event_bus):
    """Test clearing event history."""
    # Publish events
    await event_bus.publish("event1", "service1", {"data": "data1"})
    await event_bus.publish("event2", "service2", {"data": "data2"})

    assert len(event_bus.get_event_history()) == 2

    # Clear history
    event_bus.clear_history()

    assert len(event_bus.get_event_history()) == 0


@pytest.mark.asyncio
async def test_agent_service_publishes_agent_executed(event_bus):
    """Test that AgentsService publishes agent_executed event."""
    service = AgentsService()
    service.set_event_bus(event_bus)

    events_received = []

    async def handler(event: Event):
        events_received.append(event)

    event_bus.subscribe("agent_executed", handler)

    # Mock an agent
    mock_agent = MagicMock()
    mock_agent.name = "test_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "success"})

    service.agents["test_agent"] = mock_agent

    # Execute agent
    await service.execute_agent("test_agent", "test_task")

    # Verify event was published
    assert len(events_received) == 1
    assert events_received[0].event_type == "agent_executed"
    assert events_received[0].source_service == "agents"
    assert events_received[0].data["agent"] == "test_agent"


@pytest.mark.asyncio
async def test_learning_service_publishes_skill_generated(event_bus):
    """Test that LearningService publishes skill_generated event."""
    service = LearningService()
    service.set_event_bus(event_bus)

    events_received = []

    async def handler(event: Event):
        events_received.append(event)

    event_bus.subscribe("skill_generated", handler)

    # Add some interaction history
    service.interaction_history["agent1"] = [{"status": "success"} for _ in range(10)]
    service.agent_metrics["agent1"] = {
        "total_interactions": 10,
        "successful_tasks": 9,
        "failed_tasks": 1,
    }

    # Generate skills
    result = await service.generate_skills("agent1")

    # Should have generated skills and published event
    assert result["skills_generated"] > 0
    assert len(events_received) == 1
    assert events_received[0].event_type == "skill_generated"


@pytest.mark.asyncio
async def test_knowledge_service_publishes_knowledge_added(event_bus):
    """Test that KnowledgeService publishes knowledge_added event."""
    service = KnowledgeService()
    service.set_event_bus(event_bus)

    events_received = []

    async def handler(event: Event):
        events_received.append(event)

    event_bus.subscribe("knowledge_added", handler)

    # Add knowledge
    doc_id = await service.add_knowledge("This is test knowledge", {"category": "test"})

    # Verify event was published
    assert len(events_received) == 1
    assert events_received[0].event_type == "knowledge_added"
    assert events_received[0].source_service == "knowledge"
    assert events_received[0].data["doc_id"] == doc_id


@pytest.mark.asyncio
async def test_workflow_service_publishes_workflow_events(event_bus):
    """Test that WorkflowService publishes workflow events."""
    service = WorkflowService()
    service.set_event_bus(event_bus)

    started_events = []
    completed_events = []

    async def started_handler(event: Event):
        started_events.append(event)

    async def completed_handler(event: Event):
        completed_events.append(event)

    event_bus.subscribe("workflow_started", started_handler)
    event_bus.subscribe("workflow_completed", completed_handler)

    # Create and execute workflow
    workflow_id = await service.create_workflow({"steps": []})
    await service.execute_workflow(workflow_id)

    # Verify events were published
    assert len(started_events) == 1
    assert started_events[0].event_type == "workflow_started"
    assert len(completed_events) == 1
    assert completed_events[0].event_type == "workflow_completed"


@pytest.mark.asyncio
async def test_analytics_service_publishes_metrics_recorded(event_bus):
    """Test that AnalyticsService publishes metrics_recorded event."""
    service = AnalyticsService()
    service.set_event_bus(event_bus)

    events_received = []

    async def handler(event: Event):
        events_received.append(event)

    event_bus.subscribe("metrics_recorded", handler)

    # Record metric
    await service.record_metric("cpu_usage", 45.2)

    # Verify event was published
    assert len(events_received) == 1
    assert events_received[0].event_type == "metrics_recorded"
    assert events_received[0].data["metric_name"] == "cpu_usage"
    assert events_received[0].data["value"] == 45.2


@pytest.mark.asyncio
async def test_orchestrator_injects_event_bus(orchestrator):
    """Test that orchestrator injects event bus into services."""
    service = AgentsService()
    orchestrator.register_service(service)

    # Service should have event_bus set
    assert service.event_bus is not None
    assert service.event_bus is orchestrator.event_bus


@pytest.mark.asyncio
async def test_orchestrator_publishes_system_events(orchestrator):
    """Test that orchestrator publishes system events."""
    service = MagicMock()
    service.service_name = "test"
    service.__class__.__name__ = "TestService"
    service.initialize = AsyncMock()
    service.shutdown = AsyncMock()
    service.health_check = AsyncMock(return_value={})
    service.set_event_bus = MagicMock()

    orchestrator.register_service(service)

    events_received = []

    async def handler(event: Event):
        events_received.append(event)

    orchestrator.event_bus.subscribe("system_started", handler)

    # Start services
    await orchestrator.start_all_services()

    # Verify system_started event was published
    assert len(events_received) == 1
    assert events_received[0].event_type == "system_started"


@pytest.mark.asyncio
async def test_service_event_payload_structure(event_bus):
    """Test that service events have correct payload structure."""
    service = KnowledgeService()
    service.set_event_bus(event_bus)

    captured_events = []

    async def handler(event: Event):
        captured_events.append(event)

    event_bus.subscribe("knowledge_added", handler)

    await service.add_knowledge("test content", {"source": "test"})

    event = captured_events[0]

    # Verify event structure
    assert event.event_type == "knowledge_added"
    assert event.source_service == "knowledge"
    assert isinstance(event.data, dict)
    assert "doc_id" in event.data
    assert "content_length" in event.data
    assert "metadata" in event.data
    assert event.timestamp is not None


@pytest.mark.asyncio
async def test_event_bus_handler_exception_handling(event_bus):
    """Test that event bus handles handler exceptions gracefully."""
    async def failing_handler(event: Event):
        raise Exception("Handler failed")

    async def working_handler(event: Event):
        pass

    event_bus.subscribe("test_event", failing_handler)
    event_bus.subscribe("test_event", working_handler)

    # This should not raise, just log the error
    await event_bus.publish("test_event", "service", {"data": "test"})


@pytest.mark.asyncio
async def test_unsubscribe_from_event(event_bus):
    """Test unsubscribing from events."""
    events_received = []

    async def handler(event: Event):
        events_received.append(event)

    event_bus.subscribe("test_event", handler)
    event_bus.unsubscribe("test_event", handler)

    # Publish event
    await event_bus.publish("test_event", "service", {"data": "test"})

    # Handler should not be called
    assert len(events_received) == 0


@pytest.mark.asyncio
async def test_event_catalog(event_bus):
    """Test that all expected event types can be published."""
    event_types = [
        "agent_executed",
        "skill_generated",
        "knowledge_added",
        "workflow_started",
        "workflow_completed",
        "system_started",
        "system_stopped",
        "metrics_recorded",
    ]

    for event_type in event_types:
        # All events should be publishable
        await event_bus.publish(event_type, "test_service", {"test": "data"})

    history = event_bus.get_event_history()
    assert len(history) == len(event_types)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
