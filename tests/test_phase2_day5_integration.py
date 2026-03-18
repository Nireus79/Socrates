"""
Tests for Phase 2 Day 5: End-to-End Integration Testing.

Tests:
- Complete service lifecycle (init → execute → shutdown)
- Full system workflows with all services
- Event propagation across services
- Inter-service communication chains
- System health and monitoring
- Error recovery
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from core.event_bus import EventBus
from core.orchestrator import ServiceOrchestrator
from modules.analytics.service import SkillAnalytics


def create_full_orchestrator():
    """Create orchestrator with all real services."""
    orch = ServiceOrchestrator()

    # Create mock foundation service (root dependency)
    foundation = MagicMock()
    foundation.service_name = "foundation"
    foundation.__class__.__name__ = "FoundationService"
    foundation.initialize = AsyncMock()
    foundation.shutdown = AsyncMock()
    foundation.health_check = AsyncMock(return_value={"status": "healthy"})
    foundation.set_orchestrator = MagicMock()
    foundation.set_event_bus = MagicMock()

    # Register foundation first
    orch.register_service(foundation)

    # Create real service instances
    agents = AgentsService()
    learning = LearningService()
    knowledge = KnowledgeService()
    workflow = WorkflowService()
    analytics = AnalyticsService()

    # Register all services
    orch.register_service(agents)
    orch.register_service(learning)
    orch.register_service(knowledge)
    orch.register_service(workflow)
    orch.register_service(analytics)

    return orch, {
        "foundation": foundation,
        "agents": agents,
        "learning": learning,
        "knowledge": knowledge,
        "workflow": workflow,
        "analytics": analytics,
    }


@pytest.mark.asyncio
async def test_complete_system_startup_shutdown():
    """Test complete system startup and shutdown sequence."""
    orch, services = create_full_orchestrator()

    # Start all services
    await orch.start_all_services()

    # Verify all services running
    status = orch.get_service_status()
    for service_name in ["foundation", "agents", "learning", "knowledge", "workflow", "analytics"]:
        assert status[service_name]["running"]

    # Stop all services
    await orch.stop_all_services()

    # Verify all services stopped
    status = orch.get_service_status()
    for service_name in ["foundation", "agents", "learning", "knowledge", "workflow", "analytics"]:
        assert not status[service_name]["running"]


@pytest.mark.asyncio
async def test_agent_execution_with_learning_tracking():
    """Test complete workflow: agent execution → learning tracking."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    agents = services["agents"]
    learning = services["learning"]

    # Mock an agent
    mock_agent = MagicMock()
    mock_agent.name = "integration_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "success"})

    agents.agents["integration_agent"] = mock_agent

    # Execute agent
    result = await agents.execute_agent("integration_agent", "test_task")

    # Verify execution
    assert result["status"] == "success"
    assert len(agents.execution_history) > 0

    # Verify learning service was called
    assert "integration_agent" in learning.interaction_history or len(learning.agent_metrics) > 0


@pytest.mark.asyncio
async def test_skill_generation_pipeline():
    """Test complete skill generation pipeline."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    learning = services["learning"]
    agents = services["agents"]

    # Setup agent with execution history
    mock_agent = MagicMock()
    mock_agent.name = "skilled_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "success"})
    agents.agents["skilled_agent"] = mock_agent

    # Execute agent multiple times
    for _ in range(10):
        await agents.execute_agent("skilled_agent", "test_task")

    # Generate skills
    skills_result = await learning.generate_skills("skilled_agent")

    # Should have generated skills (10+ interactions = high success rate)
    if len(agents.execution_history) >= 10:
        # Might have skills if success rate high enough
        assert "skills_generated" in skills_result


@pytest.mark.asyncio
async def test_knowledge_base_population():
    """Test populating and searching knowledge base."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    knowledge = services["knowledge"]

    # Add multiple knowledge items
    doc_ids = []
    for i in range(5):
        doc_id = await knowledge.add_knowledge(f"Knowledge item {i}", {"category": "test"})
        doc_ids.append(doc_id)
        assert doc_id in knowledge.knowledge_index

    # Search knowledge
    results = await knowledge.search_knowledge("item", limit=10)
    assert len(results) > 0

    # Get specific knowledge
    for doc_id in doc_ids:
        content = await knowledge.get_knowledge(doc_id)
        assert content is not None


@pytest.mark.asyncio
async def test_workflow_execution_with_agents():
    """Test workflow execution using multiple services."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    workflow = services["workflow"]
    agents = services["agents"]
    analytics = services["analytics"]

    # Create workflow
    workflow_id = await workflow.create_workflow({"steps": ["step1", "step2"]})
    assert workflow_id in workflow.workflows

    # Mock agent
    mock_agent = MagicMock()
    mock_agent.name = "workflow_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "completed"})
    agents.agents["workflow_agent"] = mock_agent

    # Execute workflow
    execution = await workflow.execute_workflow(workflow_id)
    assert execution["status"] == "executed"

    # Record metrics
    await workflow.call_analytics_service("workflow_time", 1234)
    assert "workflow_time" in analytics.metrics


@pytest.mark.asyncio
async def test_event_propagation_through_services():
    """Test event propagation when services interact."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    agents = services["agents"]
    knowledge = services["knowledge"]

    # Subscribe to events
    agent_executed_events = []
    knowledge_added_events = []

    async def on_agent_executed(event):
        agent_executed_events.append(event)

    async def on_knowledge_added(event):
        knowledge_added_events.append(event)

    orch.event_bus.subscribe("agent_executed", on_agent_executed)
    orch.event_bus.subscribe("knowledge_added", on_knowledge_added)

    # Execute agent (should publish event)
    mock_agent = MagicMock()
    mock_agent.name = "event_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "success"})
    agents.agents["event_agent"] = mock_agent

    await agents.execute_agent("event_agent", "test")
    assert len(agent_executed_events) > 0

    # Add knowledge (should publish event)
    await knowledge.add_knowledge("test knowledge")
    assert len(knowledge_added_events) > 0


@pytest.mark.asyncio
async def test_system_health_check():
    """Test system-wide health check across all services."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    # Get system health
    health = await orch.health_check_all()

    # Verify health structure
    assert "overall_status" in health
    assert "services" in health
    assert "started_services" in health

    # All services should report health
    for service_name in ["foundation", "agents", "learning", "knowledge", "workflow", "analytics"]:
        assert service_name in health["services"]
        assert "status" in health["services"][service_name]
        assert "running" in health["services"][service_name]


@pytest.mark.asyncio
async def test_analytics_system_monitoring():
    """Test analytics collecting and aggregating system data."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    analytics = services["analytics"]
    agents = services["agents"]

    # Execute some operations
    mock_agent = MagicMock()
    mock_agent.name = "monitor_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "success"})
    agents.agents["monitor_agent"] = mock_agent

    for i in range(3):
        await agents.execute_agent("monitor_agent", f"task_{i}")
        await analytics.record_metric(f"operation_{i}", i * 100)

    # Collect system health
    health = await analytics.collect_system_health()
    assert health is not None

    # Record metrics
    assert len(analytics.metrics) >= 3


@pytest.mark.asyncio
async def test_multi_service_request_response_chain():
    """Test request/response chain across multiple services."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    workflow = services["workflow"]
    agents = services["agents"]
    learning = services["learning"]
    knowledge = services["knowledge"]

    # Setup agent
    mock_agent = MagicMock()
    mock_agent.name = "chain_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "success"})
    agents.agents["chain_agent"] = mock_agent

    # Step 1: Workflow requests agent execution
    agent_result = await workflow.call_agents_service("chain_agent", "chain_task")
    assert agent_result is not None

    # Step 2: Agent calls learning service
    agents.execution_history = [{"agent": "chain_agent", "status": "success"}]
    history = await learning.call_agents_service("chain_agent")
    assert history is not None

    # Step 3: Learning service stores in knowledge
    doc_id = await learning.call_knowledge_service("Chain learning insight")
    assert doc_id is not None

    # Verify knowledge has the data
    content = await knowledge.get_knowledge(doc_id)
    assert content is not None


@pytest.mark.asyncio
async def test_concurrent_service_operations():
    """Test concurrent operations across services."""
    import asyncio

    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    knowledge = services["knowledge"]
    analytics = services["analytics"]

    # Concurrent knowledge additions
    async def add_docs():
        tasks = [
            knowledge.add_knowledge(f"Document {i}")
            for i in range(5)
        ]
        return await asyncio.gather(*tasks)

    # Concurrent metric recordings
    async def record_metrics():
        tasks = [
            analytics.record_metric(f"metric_{i}", i * 10)
            for i in range(5)
        ]
        return await asyncio.gather(*tasks)

    # Run concurrently
    doc_ids, _ = await asyncio.gather(add_docs(), record_metrics())

    assert len(doc_ids) == 5
    assert len(analytics.metrics) >= 5


@pytest.mark.asyncio
async def test_service_dependency_chain():
    """Test that service dependencies work correctly."""
    orch, services = create_full_orchestrator()

    # Verify dependency graph
    assert orch.get_dependencies("foundation") == []
    assert "foundation" in orch.get_dependencies("agents")
    assert "agents" in orch.get_dependencies("workflow")

    # Start services
    await orch.start_all_services()

    # All services should be running
    started = orch._started_services
    assert "foundation" in started
    assert "agents" in started
    assert "workflow" in started


@pytest.mark.asyncio
async def test_service_isolation():
    """Test that services are properly isolated."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    agents = services["agents"]
    learning = services["learning"]

    # Services should have independent data
    agents.execution_history.append({"test": "data"})

    # Learning service shouldn't be affected
    assert "test" not in str(learning.interaction_history)

    # But inter-service calls should work
    interaction = await agents.call_learning_service("test_agent", {"data": "test"})
    # Should execute without error (graceful if service not found)


@pytest.mark.asyncio
async def test_error_recovery():
    """Test system recovery from errors."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    agents = services["agents"]

    # Try to execute non-existent agent
    result = await agents.execute_agent("nonexistent_agent", "task")
    assert result["status"] == "error"

    # System should still be healthy
    health = await orch.health_check_all()
    assert health["overall_status"] == "healthy"

    # Other operations should work
    mock_agent = MagicMock()
    mock_agent.name = "recovery_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "success"})
    agents.agents["recovery_agent"] = mock_agent

    result = await agents.execute_agent("recovery_agent", "task")
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_service_list_and_status():
    """Test service discovery and status reporting."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    # List services
    service_list = orch.list_services()
    assert len(service_list) == 6

    # Get status
    status = orch.get_service_status()
    assert len(status) == 6

    for name, info in status.items():
        assert "class" in info
        assert "running" in info
        assert info["running"] is True


@pytest.mark.asyncio
async def test_event_history_tracking():
    """Test event history tracking across operations."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    agents = services["agents"]
    knowledge = services["knowledge"]

    # Execute operations that generate events
    mock_agent = MagicMock()
    mock_agent.name = "history_agent"
    mock_agent.process_async = AsyncMock(return_value={"result": "success"})
    agents.agents["history_agent"] = mock_agent

    await agents.execute_agent("history_agent", "task")
    await knowledge.add_knowledge("test")

    # Get event history
    history = orch.event_bus.get_event_history()
    assert len(history) >= 2

    # Filter by type
    agent_events = orch.event_bus.get_event_history(event_type="agent_executed")
    assert len(agent_events) >= 1

    knowledge_events = orch.event_bus.get_event_history(event_type="knowledge_added")
    assert len(knowledge_events) >= 1


@pytest.mark.asyncio
async def test_complete_workflow_scenario():
    """Test complete real-world workflow scenario."""
    orch, services = create_full_orchestrator()
    await orch.start_all_services()

    agents = services["agents"]
    learning = services["learning"]
    knowledge = services["knowledge"]
    workflow = services["workflow"]
    analytics = services["analytics"]

    # Scenario: Multi-agent workflow with learning and knowledge

    # 1. Create workflow
    wf_id = await workflow.create_workflow({"name": "data_processing", "steps": ["extract", "analyze", "store"]})

    # 2. Setup agents
    for agent_name in ["extractor", "analyzer"]:
        mock_agent = MagicMock()
        mock_agent.name = agent_name
        mock_agent.process_async = AsyncMock(return_value={"status": "complete"})
        agents.agents[agent_name] = mock_agent

    # 3. Execute agents through workflow
    result1 = await workflow.call_agents_service("extractor", "extract_data")
    assert result1 is not None

    result2 = await workflow.call_agents_service("analyzer", "analyze_data")
    assert result2 is not None

    # 4. Track interactions in learning
    await agents.execute_agent("extractor", "extract")
    await agents.execute_agent("analyzer", "analyze")

    # 5. Generate skills if enough interactions
    skills = await learning.generate_skills("extractor")
    assert "skills" in skills

    # 6. Store knowledge
    doc_id = await knowledge.add_knowledge("Data processing complete")
    assert doc_id is not None

    # 7. Record metrics
    await analytics.record_metric("workflow_success", True)
    await analytics.record_metric("processed_items", 100)

    # 8. Verify final state
    health = await analytics.collect_system_health()
    assert health is not None

    # All services should be healthy
    assert health["overall_status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
