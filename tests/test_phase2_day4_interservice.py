"""
Tests for Phase 2 Day 4: Inter-Service Communication.

Tests:
- Services calling each other via orchestrator
- Request/response patterns
- Cross-service workflows
- Error handling and fallback
- Service dependency testing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from core.orchestrator import ServiceOrchestrator
from modules.agents.service import AgentsService
from modules.learning.service import LearningService
from modules.knowledge.service import KnowledgeService
from modules.workflow.service import WorkflowService
from modules.analytics.service import AnalyticsService


def create_mock_service(name, class_name="MockService"):
    """Helper to create mock service with required methods."""
    service = MagicMock()
    service.service_name = name
    service.__class__.__name__ = class_name
    service.initialize = AsyncMock()
    service.shutdown = AsyncMock()
    service.health_check = AsyncMock(return_value={})
    service.set_orchestrator = MagicMock()
    service.set_event_bus = MagicMock()
    return service


def setup_orchestrator_with_all_services():
    """Create orchestrator with all mock services registered."""
    orch = ServiceOrchestrator()

    services_data = [
        ("foundation", "FoundationService"),
        ("knowledge", "KnowledgeService"),
        ("learning", "LearningService"),
        ("agents", "AgentsService"),
        ("analytics", "AnalyticsService"),
        ("workflow", "WorkflowService"),
    ]

    for name, class_name in services_data:
        service = create_mock_service(name, class_name)
        orch.register_service(service)

    return orch


@pytest.fixture
def orchestrator():
    """Create a fresh orchestrator with all services."""
    return setup_orchestrator_with_all_services()


@pytest.mark.asyncio
async def test_service_orchestrator_injection(orchestrator):
    """Test that orchestrator is injected into services."""
    for service in orchestrator._services.values():
        # Verify set_orchestrator was called
        service.set_orchestrator.assert_called_with(orchestrator)


@pytest.mark.asyncio
async def test_agents_service_stores_orchestrator():
    """Test that AgentsService can store orchestrator reference."""
    service = AgentsService()
    orch = ServiceOrchestrator()

    orch.register_service(service)

    # Service should have orchestrator
    assert service.orchestrator is not None
    assert service.orchestrator is orch


@pytest.mark.asyncio
async def test_agents_calls_learning_service():
    """Test agents service calling learning service."""
    # Setup orchestrator with all required services
    orch = setup_orchestrator_with_all_services()

    # Replace agents and learning with real services
    agents_svc = AgentsService()
    learning_svc = LearningService()

    orch._services["agents"] = agents_svc
    orch._services["learning"] = learning_svc

    # Inject orchestrator
    agents_svc.set_orchestrator(orch)
    learning_svc.set_orchestrator(orch)

    # Start services
    await orch.start_all_services()

    # Mock an agent
    mock_agent = MagicMock()
    mock_agent.name = "test_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "success"})

    agents_svc.agents["test_agent"] = mock_agent

    # Execute agent (should call learning service)
    result = await agents_svc.execute_agent("test_agent", "test_task")

    # Verify execution was successful
    assert result["status"] == "success"
    assert len(agents_svc.execution_history) > 0


@pytest.mark.asyncio
async def test_learning_calls_agents_service():
    """Test learning service calling agents service."""
    orch = setup_orchestrator_with_all_services()

    agents_svc = AgentsService()
    learning_svc = LearningService()

    orch._services["agents"] = agents_svc
    orch._services["learning"] = learning_svc

    agents_svc.set_orchestrator(orch)
    learning_svc.set_orchestrator(orch)

    await orch.start_all_services()

    # Setup some execution history
    agents_svc.execution_history = [
        {"agent": "agent1", "status": "success", "result": "test"}
    ]

    # Call agents service from learning
    history = await learning_svc.call_agents_service("agent1")

    assert history is not None
    assert len(history) > 0


@pytest.mark.asyncio
async def test_learning_calls_knowledge_service():
    """Test learning service storing insights in knowledge service."""
    orch = setup_orchestrator_with_all_services()

    learning_svc = LearningService()
    knowledge_svc = KnowledgeService()

    orch._services["learning"] = learning_svc
    orch._services["knowledge"] = knowledge_svc

    learning_svc.set_orchestrator(orch)
    knowledge_svc.set_orchestrator(orch)

    await orch.start_all_services()

    # Call knowledge service from learning
    doc_id = await learning_svc.call_knowledge_service("This is a learning insight")

    assert doc_id is not None
    assert doc_id.startswith("doc_")
    assert doc_id in knowledge_svc.knowledge_index


@pytest.mark.asyncio
async def test_workflow_calls_agents_service():
    """Test workflow service executing agents."""
    orch = setup_orchestrator_with_all_services()

    agents_svc = AgentsService()
    workflow_svc = WorkflowService()

    orch._services["agents"] = agents_svc
    orch._services["workflow"] = workflow_svc

    agents_svc.set_orchestrator(orch)
    workflow_svc.set_orchestrator(orch)

    await orch.start_all_services()

    # Setup agent
    mock_agent = MagicMock()
    mock_agent.name = "task_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "completed"})
    agents_svc.agents["task_agent"] = mock_agent

    # Call agent from workflow
    result = await workflow_svc.call_agents_service("task_agent", "workflow_task")

    assert result is not None
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_workflow_calls_analytics_service():
    """Test workflow service recording metrics."""
    orch = setup_orchestrator_with_all_services()

    workflow_svc = WorkflowService()
    analytics_svc = AnalyticsService()

    orch._services["workflow"] = workflow_svc
    orch._services["analytics"] = analytics_svc

    workflow_svc.set_orchestrator(orch)
    analytics_svc.set_orchestrator(orch)

    await orch.start_all_services()

    # Call analytics from workflow
    success = await workflow_svc.call_analytics_service("workflow_execution_time", 1234)

    assert success is True
    assert "workflow_execution_time" in analytics_svc.metrics


@pytest.mark.asyncio
async def test_analytics_collects_system_health():
    """Test analytics service collecting health from all services."""
    orch = setup_orchestrator_with_all_services()

    analytics_svc = AnalyticsService()
    orch._services["analytics"] = analytics_svc
    analytics_svc.set_orchestrator(orch)

    await orch.start_all_services()

    # Collect health
    health = await analytics_svc.collect_system_health()

    assert health is not None
    assert "overall_status" in health
    assert "services" in health


@pytest.mark.asyncio
async def test_service_call_without_orchestrator():
    """Test service gracefully handling missing orchestrator."""
    agents_svc = AgentsService()
    learning_svc = LearningService()

    # No orchestrator set
    assert agents_svc.orchestrator is None

    # Should handle gracefully
    success = await agents_svc.call_learning_service("agent1", {})
    assert success is False

    history = await learning_svc.call_agents_service("agent1")
    assert history is None


@pytest.mark.asyncio
async def test_service_call_service_not_found():
    """Test handling when called service doesn't exist."""
    orch = setup_orchestrator_with_all_services()

    agents_svc = AgentsService()
    orch._services["agents"] = agents_svc
    agents_svc.set_orchestrator(orch)

    await orch.start_all_services()

    # Try to call non-existent service
    with pytest.raises(RuntimeError):
        await orch.call_service("nonexistent", "some_method")


@pytest.mark.asyncio
async def test_service_call_method_not_found():
    """Test handling when method doesn't exist."""
    orch = setup_orchestrator_with_all_services()

    agents_svc = AgentsService()
    orch._services["agents"] = agents_svc
    agents_svc.set_orchestrator(orch)

    await orch.start_all_services()

    # Try to call non-existent method
    with pytest.raises(RuntimeError):
        await orch.call_service("agents", "nonexistent_method")


@pytest.mark.asyncio
async def test_multi_hop_service_calls():
    """Test service A calling B calling C."""
    orch = setup_orchestrator_with_all_services()

    # Setup services
    agents_svc = AgentsService()
    learning_svc = LearningService()
    knowledge_svc = KnowledgeService()

    orch._services["agents"] = agents_svc
    orch._services["learning"] = learning_svc
    orch._services["knowledge"] = knowledge_svc

    agents_svc.set_orchestrator(orch)
    learning_svc.set_orchestrator(orch)
    knowledge_svc.set_orchestrator(orch)

    await orch.start_all_services()

    # Setup agent
    mock_agent = MagicMock()
    mock_agent.name = "test_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "success"})
    agents_svc.agents["test_agent"] = mock_agent

    # Multi-hop: Agents -> Learning -> Knowledge
    # 1. Execute agent
    result = await agents_svc.execute_agent("test_agent", "test_task")
    assert result["status"] == "success"

    # 2. Learning service calls knowledge service
    doc_id = await learning_svc.call_knowledge_service("Learned insight")
    assert doc_id is not None

    # 3. Verify knowledge service has the data
    knowledge = await knowledge_svc.get_knowledge(doc_id)
    assert knowledge is not None


@pytest.mark.asyncio
async def test_concurrent_service_calls():
    """Test multiple services calling each other concurrently."""
    import asyncio

    orch = setup_orchestrator_with_all_services()

    agents_svc = AgentsService()
    analytics_svc = AnalyticsService()

    orch._services["agents"] = agents_svc
    orch._services["analytics"] = analytics_svc

    agents_svc.set_orchestrator(orch)
    analytics_svc.set_orchestrator(orch)

    await orch.start_all_services()

    # Concurrent metric recording
    tasks = [
        analytics_svc.record_metric(f"metric_{i}", i * 100)
        for i in range(5)
    ]

    await asyncio.gather(*tasks)

    # Verify all metrics recorded
    assert len(analytics_svc.metrics) >= 5


@pytest.mark.asyncio
async def test_service_call_error_handling():
    """Test service handling errors during inter-service calls."""
    orch = setup_orchestrator_with_all_services()

    agents_svc = AgentsService()
    learning_svc = LearningService()

    orch._services["agents"] = agents_svc
    orch._services["learning"] = learning_svc

    agents_svc.set_orchestrator(orch)
    learning_svc.set_orchestrator(orch)

    await orch.start_all_services()

    # Mock learning service to fail
    learning_svc.track_interaction = AsyncMock(side_effect=Exception("Service error"))

    # Should handle error gracefully
    success = await agents_svc.call_learning_service("agent1", {})
    # The implementation catches the exception
    assert success is False  # Because the call failed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
