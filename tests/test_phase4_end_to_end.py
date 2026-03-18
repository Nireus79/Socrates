"""
End-to-End Integration Tests for Phase 4: Complete Skill Ecosystem.

Tests complete workflows:
- Skill generation to marketplace registration
- Discovery and adoption
- Composition and execution
- Analytics and metrics
- Full ecosystem integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import pytest_asyncio

from modules.marketplace.service import SkillMarketplace
from modules.distribution.service import SkillDistributionService
from modules.composition.service import SkillComposer
from modules.analytics.service import SkillAnalytics


@pytest_asyncio.fixture
async def ecosystem():
    """Create a complete ecosystem with all services."""
    marketplace = SkillMarketplace()
    distribution = SkillDistributionService()
    composer = SkillComposer()
    analytics = SkillAnalytics()

    await marketplace.initialize()
    await distribution.initialize()
    await composer.initialize()
    await analytics.initialize()

    return {
        "marketplace": marketplace,
        "distribution": distribution,
        "composer": composer,
        "analytics": analytics,
    }


async def mock_skill_executor(skill_id: str, context: dict) -> dict:
    """Mock skill executor for composition testing."""
    return {
        "status": "success",
        "skill_id": skill_id,
        "output": f"result_{skill_id}",
        "context_received": len(context) > 0,
    }


@pytest.mark.asyncio
async def test_complete_skill_workflow(ecosystem):
    """Test complete workflow: register -> discover -> distribute -> compose -> analyze."""
    marketplace = ecosystem["marketplace"]
    distribution = ecosystem["distribution"]
    composer = ecosystem["composer"]
    analytics = ecosystem["analytics"]

    # Step 1: Register skills in marketplace
    skill_1 = {
        "name": "Search Skill",
        "type": "search",
        "effectiveness": 0.9,
        "agent": "agent_1",
        "description": "High-performing search skill",
    }

    skill_2 = {
        "name": "Filter Skill",
        "type": "filter",
        "effectiveness": 0.85,
        "agent": "agent_2",
        "description": "Reliable filtering skill",
    }

    assert await marketplace.register_skill("skill_search", skill_1)
    assert await marketplace.register_skill("skill_filter", skill_2)

    # Step 2: Discover skills
    discovered = await marketplace.discover_skills(min_effectiveness=0.8)
    assert len(discovered) >= 2
    assert any(s["skill_id"] == "skill_search" for s in discovered)

    # Step 3: Distribute skill_1 to agent_2
    dist_result = await distribution.distribute_skill_to_agent(
        source_skill_id="skill_search",
        source_agent="agent_1",
        target_agent="agent_2",
        skill_data=skill_1,
    )
    assert dist_result is not None

    # Step 4: Track adoption
    success = await distribution.record_adoption_result(
        source_skill_id="skill_search",
        target_agent="agent_2",
        effectiveness=0.89,
        success=True,
    )
    assert success

    # Step 5: Create composition with distributed skills
    success = await composer.create_composition(
        composition_id="workflow_1",
        name="Search and Filter Workflow",
        skills=["skill_search", "skill_filter"],
        execution_type="sequential",
    )
    assert success

    # Step 6: Add parameter mapping
    success = await composer.add_parameter_mapping(
        composition_id="workflow_1",
        from_skill_index=0,
        from_param="output",
        to_skill_index=1,
        to_param="input",
    )
    assert success

    # Step 7: Execute composition
    result = await composer.execute_composition(
        composition_id="workflow_1",
        initial_context={"query": "test"},
        skill_executor=mock_skill_executor,
    )
    assert result["status"] == "success"
    assert len(result["results"]) == 2

    # Step 8: Track metrics in analytics
    await analytics.track_skill_metric(
        "skill_search", "agent_2", "effectiveness", 0.92
    )
    await analytics.track_skill_metric(
        "skill_filter", "agent_2", "effectiveness", 0.87
    )

    # Step 9: Analyze performance
    perf = await analytics.analyze_skill_performance("skill_search")
    assert perf is not None
    assert perf["skill_id"] == "skill_search"

    # Step 10: Get ecosystem health
    health = await analytics.get_ecosystem_health()
    assert health["total_skills"] >= 2
    assert health["ecosystem_health"] in ["excellent", "good", "fair", "poor"]


@pytest.mark.asyncio
async def test_multi_agent_skill_sharing(ecosystem):
    """Test skill sharing across multiple agents."""
    marketplace = ecosystem["marketplace"]
    distribution = ecosystem["distribution"]
    analytics = ecosystem["analytics"]

    # Create high-performing skill
    skill = {
        "name": "Data Analysis",
        "type": "analysis",
        "effectiveness": 0.95,
        "agent": "agent_leader",
        "description": "Advanced analytics",
    }

    assert await marketplace.register_skill("analyze_data", skill)

    # Distribute to multiple agents
    target_agents = ["agent_a", "agent_b", "agent_c"]
    distributions = []

    for agent in target_agents:
        dist_id = await distribution.distribute_skill_to_agent(
            source_skill_id="analyze_data",
            source_agent="agent_leader",
            target_agent=agent,
            skill_data=skill,
        )
        assert dist_id is not None
        distributions.append(dist_id)

    # Record adoption results
    for i, _ in enumerate(distributions):
        success = await distribution.record_adoption_result(
            source_skill_id="analyze_data",
            target_agent=target_agents[i],
            effectiveness=0.93,
            success=True,
        )
        assert success

    # Track performance in analytics
    for agent in target_agents:
        await analytics.track_skill_metric(
            "analyze_data", agent, "effectiveness", 0.93
        )

    # Verify ecosystem metrics
    health = await analytics.get_ecosystem_health()
    assert health["total_skills"] >= 1  # At least the distributed skill


@pytest.mark.asyncio
async def test_skill_composition_with_metrics(ecosystem):
    """Test skill composition with performance tracking."""
    composer = ecosystem["composer"]
    analytics = ecosystem["analytics"]

    # Create composition
    success = await composer.create_composition(
        composition_id="metrics_workflow",
        name="Metrics Tracking Workflow",
        skills=["skill_a", "skill_b", "skill_c"],
        execution_type="sequential",
    )
    assert success

    # Execute multiple times
    executions = 5
    for i in range(executions):
        result = await composer.execute_composition(
            composition_id="metrics_workflow",
            initial_context={"run": i},
            skill_executor=mock_skill_executor,
        )
        assert result["status"] == "success"

    # Get composition metrics
    metrics = await composer.get_composition_metrics("metrics_workflow")
    assert metrics["executions"] == executions
    assert metrics["successes"] == executions

    # Track in analytics
    for _ in range(executions):
        await analytics.track_skill_metric(
            "skill_a", "agent_1", "composition_usage", 1.0
        )

    perf = await analytics.analyze_skill_performance("skill_a")
    assert perf is not None


@pytest.mark.asyncio
async def test_high_performers_marketplace(ecosystem):
    """Test identifying and using high-performing skills from marketplace."""
    marketplace = ecosystem["marketplace"]
    analytics = ecosystem["analytics"]

    # Register multiple skills with varying performance
    skills = [
        ("s1", {"name": "Skill 1", "type": "type_a", "effectiveness": 0.95, "agent": "agent_1"}),
        ("s2", {"name": "Skill 2", "type": "type_b", "effectiveness": 0.85, "agent": "agent_2"}),
        ("s3", {"name": "Skill 3", "type": "type_a", "effectiveness": 0.75, "agent": "agent_3"}),
        ("s4", {"name": "Skill 4", "type": "type_c", "effectiveness": 0.92, "agent": "agent_4"}),
    ]

    for skill_id, skill_data in skills:
        assert await marketplace.register_skill(skill_id, skill_data)

    # Get top skills by type
    top_a = await marketplace.get_skills_by_type("type_a")
    assert len(top_a) >= 1
    assert top_a[0]["effectiveness"] >= 0.75

    # Track performance metrics
    for skill_id, skill_data in skills:
        await analytics.track_skill_metric(
            skill_id, "agent_1", "effectiveness", skill_data["effectiveness"]
        )

    # Identify high performers
    high_performers = await analytics.identify_high_performing_skills(
        min_effectiveness=0.85, limit=10
    )
    assert len(high_performers) >= 2
    assert all(hp["effectiveness"] >= 0.85 for hp in high_performers)


@pytest.mark.asyncio
async def test_ecosystem_health_monitoring(ecosystem):
    """Test comprehensive ecosystem health monitoring."""
    marketplace = ecosystem["marketplace"]
    distribution = ecosystem["distribution"]
    analytics = ecosystem["analytics"]

    # Phase 1: Initial state - no data
    health = await analytics.get_ecosystem_health()
    assert health["ecosystem_health"] == "no_data"

    # Phase 2: Add high-performing skills
    for i in range(3):
        skill = {
            "name": f"High Performance Skill {i}",
            "type": "premium",
            "effectiveness": 0.9 + (i * 0.01),
            "agent": f"agent_{i}",
        }
        await marketplace.register_skill(f"hp_skill_{i}", skill)

    # Track metrics
    for i in range(3):
        await analytics.track_skill_metric(
            f"hp_skill_{i}", f"agent_{i}", "effectiveness", 0.91
        )

    # Check health
    health = await analytics.get_ecosystem_health()
    assert health["total_skills"] == 3
    assert health["ecosystem_health"] in ["excellent", "good"]
    assert health["average_effectiveness"] > 0.8

    # Phase 3: Get performance report
    report = await analytics.get_performance_report()
    assert report["report_type"] == "ecosystem_performance"
    assert "ecosystem_health" in report
    assert "high_performers" in report


@pytest.mark.asyncio
async def test_parallel_composition_integration(ecosystem):
    """Test parallel skill composition integrated with marketplace."""
    marketplace = ecosystem["marketplace"]
    composer = ecosystem["composer"]

    # Register parallel skills
    skills = [
        ("parallel_a", {"name": "Parallel A", "type": "parallel", "effectiveness": 0.88, "agent": "agent_1"}),
        ("parallel_b", {"name": "Parallel B", "type": "parallel", "effectiveness": 0.87, "agent": "agent_2"}),
    ]

    for skill_id, skill_data in skills:
        await marketplace.register_skill(skill_id, skill_data)

    # Create parallel composition
    success = await composer.create_composition(
        composition_id="parallel_workflow",
        name="Parallel Processing",
        skills=["parallel_a", "parallel_b"],
        execution_type="parallel",
    )
    assert success

    # Execute parallel composition
    result = await composer.execute_composition(
        composition_id="parallel_workflow",
        initial_context={"task": "process"},
        skill_executor=mock_skill_executor,
    )
    assert result["status"] == "success"
    assert result["execution_type"] == "parallel"
    assert len(result["results"]) == 2


@pytest.mark.asyncio
async def test_error_handling_integration(ecosystem):
    """Test error handling across ecosystem services."""
    composer = ecosystem["composer"]

    # Test non-existent composition
    result = await composer.execute_composition(
        composition_id="nonexistent",
        initial_context={},
        skill_executor=mock_skill_executor,
    )
    assert result["status"] == "error"

    # Test analytics with no data
    analytics = ecosystem["analytics"]
    analysis = await analytics.analyze_skill_performance("nonexistent_skill")
    assert analysis is None


@pytest.mark.asyncio
async def test_service_health_checks(ecosystem):
    """Test health checks across all services."""
    marketplace = ecosystem["marketplace"]
    distribution = ecosystem["distribution"]
    composer = ecosystem["composer"]
    analytics = ecosystem["analytics"]

    # Verify all services respond to health checks
    mp_health = await marketplace.health_check()
    assert "skills_in_catalog" in mp_health

    dist_health = await distribution.health_check()
    assert "total_distributions" in dist_health

    comp_health = await composer.health_check()
    assert "compositions_defined" in comp_health

    ana_health = await analytics.health_check()
    assert "skills_tracked" in ana_health


@pytest.mark.asyncio
async def test_event_publishing_integration(ecosystem):
    """Test event publishing across services."""
    marketplace = ecosystem["marketplace"]
    composer = ecosystem["composer"]

    # Mock event bus for marketplace
    marketplace.event_bus = MagicMock()
    marketplace.event_bus.publish = AsyncMock()

    skill = {
        "name": "Event Test",
        "type": "test",
        "effectiveness": 0.8,
        "agent": "agent_test",
    }

    await marketplace.register_skill("test_event", skill)

    # Verify event was published
    marketplace.event_bus.publish.assert_called()

    # Mock event bus for composer
    composer.event_bus = MagicMock()
    composer.event_bus.publish = AsyncMock()

    await composer.create_composition(
        composition_id="event_comp",
        name="Event Composition",
        skills=["test_event"],
    )

    await composer.execute_composition(
        composition_id="event_comp",
        initial_context={},
        skill_executor=mock_skill_executor,
    )

    # Verify composition events were published
    composer.event_bus.publish.assert_called()


@pytest.mark.asyncio
async def test_marketplace_statistics(ecosystem):
    """Test marketplace statistics generation."""
    marketplace = ecosystem["marketplace"]

    # Register diverse skills
    for i in range(5):
        skill = {
            "name": f"Stat Skill {i}",
            "type": f"type_{i % 2}",
            "effectiveness": 0.70 + (i * 0.05),
            "agent": f"agent_{i}",
            "tags": ["statistics", f"level_{i}"],
        }
        await marketplace.register_skill(f"stat_skill_{i}", skill)

    # Get metadata for verification
    metadata = await marketplace.get_skill_metadata("stat_skill_0")
    assert metadata is not None

    # Verify we can discover all skills
    all_skills = await marketplace.discover_skills()
    assert len(all_skills) == 5


@pytest.mark.asyncio
async def test_distribution_lineage_tracking(ecosystem):
    """Test distribution lineage and version tracking."""
    distribution = ecosystem["distribution"]

    # Distribute skill with version tracking
    dist_id = await distribution.distribute_skill_to_agent(
        source_skill_id="original_skill",
        source_agent="original_agent",
        target_agent="new_agent",
        skill_data={
            "skill_id": "original_skill",
            "name": "Original",
            "type": "test",
            "effectiveness": 0.85,
            "agent": "original_agent",
        },
    )
    assert dist_id is not None

    # Record adoption result
    success = await distribution.record_adoption_result(
        source_skill_id="original_skill",
        target_agent="new_agent",
        effectiveness=0.84,
        success=True,
    )
    assert success

    # Get adoption status
    status = await distribution.get_adoption_status("original_skill")
    assert status is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
