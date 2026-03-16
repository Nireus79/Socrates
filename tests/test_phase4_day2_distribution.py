"""
Tests for Phase 4 Day 2: Skill Distribution & Sharing.

Tests:
- Skill distribution to single agent
- Skill broadcasting to multiple agents
- Adoption tracking
- Version management
- Cross-agent skill queries
- Distribution metrics
- Performance comparison
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import pytest_asyncio

from modules.distribution.service import SkillDistributionService


@pytest.fixture
def distribution_service():
    """Create a fresh distribution service."""
    return SkillDistributionService()


@pytest_asyncio.fixture
async def distribution_initialized():
    """Create initialized distribution service."""
    service = SkillDistributionService()
    await service.initialize()
    return service


def create_test_skill(
    skill_id: str = "source_skill",
    name: str = "Test Skill",
    skill_type: str = "optimization",
    effectiveness: float = 0.8,
) -> dict:
    """Create test skill data."""
    return {
        "skill_id": skill_id,
        "name": name,
        "type": skill_type,
        "effectiveness": effectiveness,
        "created_at": "2026-03-26T00:00:00",
    }


@pytest.mark.asyncio
async def test_distribution_initialization(distribution_initialized):
    """Test distribution service initialization."""
    service = distribution_initialized

    assert service.service_name == "distribution"
    assert len(service.distributions) == 0
    assert len(service.adoption_tracking) == 0


@pytest.mark.asyncio
async def test_distribute_skill_to_agent(distribution_initialized):
    """Test distributing skill to single agent."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")
    new_skill_id = await service.distribute_skill_to_agent(
        source_skill_id="skill_1",
        source_agent="agent1",
        target_agent="agent2",
        skill_data=skill,
    )

    assert new_skill_id is not None
    assert new_skill_id in [
        d.get("new_skill_id") for d in service.distributions.values()
    ]


@pytest.mark.asyncio
async def test_distribution_creates_version(distribution_initialized):
    """Test that distribution creates version record."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")
    await service.distribute_skill_to_agent(
        source_skill_id="skill_1",
        source_agent="agent1",
        target_agent="agent2",
        skill_data=skill,
    )

    # Check version tracking
    assert "skill_1" in service.skill_versions
    assert len(service.skill_versions["skill_1"]) == 1
    version = service.skill_versions["skill_1"][0]
    assert version["from_agent"] == "agent1"
    assert version["to_agent"] == "agent2"


@pytest.mark.asyncio
async def test_broadcast_skill_to_multiple_agents(distribution_initialized):
    """Test broadcasting skill to multiple agents."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")
    target_agents = ["agent2", "agent3", "agent4"]

    results = await service.broadcast_skill_to_agents(
        source_skill_id="skill_1",
        source_agent="agent1",
        target_agents=target_agents,
        skill_data=skill,
    )

    # Verify all agents received the skill
    assert len(results) == 3
    assert all(v is not None for v in results.values())
    assert "agent2" in results
    assert "agent3" in results
    assert "agent4" in results


@pytest.mark.asyncio
async def test_adoption_tracking_single_distribution(distribution_initialized):
    """Test adoption tracking after single distribution."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")
    await service.distribute_skill_to_agent(
        source_skill_id="skill_1",
        source_agent="agent1",
        target_agent="agent2",
        skill_data=skill,
    )

    # Check adoption tracking
    adoption = await service.get_adoption_status("skill_1")
    assert adoption is not None
    assert adoption["source_agent"] == "agent1"
    assert adoption["adoption_count"] == 1
    assert adoption["distributions"] == 1


@pytest.mark.asyncio
async def test_adoption_tracking_multiple_distributions(distribution_initialized):
    """Test adoption tracking with multiple distributions."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")

    # Distribute to multiple agents
    for i in range(3):
        await service.distribute_skill_to_agent(
            source_skill_id="skill_1",
            source_agent="agent1",
            target_agent=f"agent{i+2}",
            skill_data=skill,
        )

    # Check adoption tracking
    adoption = await service.get_adoption_status("skill_1")
    assert adoption["adoption_count"] == 3
    assert adoption["distributions"] == 3


@pytest.mark.asyncio
async def test_get_agent_adoptions(distribution_initialized):
    """Test retrieving adoptions for an agent."""
    service = distribution_initialized

    skill1 = create_test_skill("skill_1")
    skill2 = create_test_skill("skill_2")

    # Distribute different skills to agent2
    await service.distribute_skill_to_agent(
        "skill_1", "agent1", "agent2", skill1
    )
    await service.distribute_skill_to_agent(
        "skill_2", "agent1", "agent2", skill2
    )

    # Get adoptions for agent2
    adoptions = await service.get_agent_adoptions("agent2")

    assert len(adoptions) == 2
    assert all(a["source_agent"] == "agent1" for a in adoptions)


@pytest.mark.asyncio
async def test_get_skill_lineage(distribution_initialized):
    """Test retrieving skill version lineage."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")

    # Distribute multiple times
    await service.distribute_skill_to_agent("skill_1", "agent1", "agent2", skill)
    await service.distribute_skill_to_agent("skill_1", "agent1", "agent3", skill)

    # Get lineage
    lineage = await service.get_skill_lineage("skill_1")

    assert len(lineage) == 2
    assert all(v["lineage"] == "skill_1" for v in lineage)


@pytest.mark.asyncio
async def test_distribution_metrics(distribution_initialized):
    """Test distribution metrics calculation."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")

    # Create distributions
    for i in range(3):
        await service.distribute_skill_to_agent(
            "skill_1", "agent1", f"agent{i+2}", skill
        )

    # Get metrics
    metrics = await service.get_distribution_metrics()

    assert metrics["total_distributions"] == 3
    assert metrics["total_adoptions"] == 3
    assert metrics["skills_with_adoptions"] == 1


@pytest.mark.asyncio
async def test_distribution_history(distribution_initialized):
    """Test distribution history tracking."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")

    # Create distributions
    await service.distribute_skill_to_agent("skill_1", "agent1", "agent2", skill)
    await service.distribute_skill_to_agent("skill_1", "agent1", "agent3", skill)

    # Get history
    history = await service.get_distribution_history()

    assert len(history) == 2
    assert all(h["source"] == "skill_1" for h in history)


@pytest.mark.asyncio
async def test_distribution_history_filter_by_skill(distribution_initialized):
    """Test filtering distribution history by skill."""
    service = distribution_initialized

    skill1 = create_test_skill("skill_1")
    skill2 = create_test_skill("skill_2")

    # Create distributions for two skills
    await service.distribute_skill_to_agent("skill_1", "agent1", "agent2", skill1)
    await service.distribute_skill_to_agent("skill_2", "agent1", "agent3", skill2)

    # Get history for skill_1
    history = await service.get_distribution_history(skill_id="skill_1")

    assert len(history) == 1
    assert history[0]["source"] == "skill_1"


@pytest.mark.asyncio
async def test_distribution_history_filter_by_agent(distribution_initialized):
    """Test filtering distribution history by agent."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")

    # Create distributions to different agents
    await service.distribute_skill_to_agent("skill_1", "agent1", "agent2", skill)
    await service.distribute_skill_to_agent("skill_1", "agent1", "agent3", skill)

    # Get history for agent2
    history = await service.get_distribution_history(agent_name="agent2")

    assert len(history) == 1
    assert history[0]["target_agent"] == "agent2"


@pytest.mark.asyncio
async def test_record_adoption_result(distribution_initialized):
    """Test recording adoption result."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")

    # Distribute skill
    await service.distribute_skill_to_agent(
        "skill_1", "agent1", "agent2", skill
    )

    # Record result
    success = await service.record_adoption_result(
        source_skill_id="skill_1",
        target_agent="agent2",
        effectiveness=0.85,
        success=True,
    )

    assert success is True

    # Verify result was recorded
    adoption = await service.get_adoption_status("skill_1")
    agent_adoption = adoption["adoptions"][0]
    assert agent_adoption["effectiveness"] == 0.85
    assert agent_adoption["success"] is True


@pytest.mark.asyncio
async def test_adoption_performance_comparison(distribution_initialized):
    """Test comparing adoption performance across agents."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")

    # Distribute to multiple agents
    expected_values = [0.7, 0.8, 0.9]
    for i, agent in enumerate(["agent2", "agent3", "agent4"]):
        await service.distribute_skill_to_agent(
            "skill_1", "agent1", agent, skill
        )
        # Record different effectiveness for each
        await service.record_adoption_result(
            "skill_1", agent, effectiveness=expected_values[i]
        )

    # Get comparison
    comparison = await service.get_adoption_performance_comparison("skill_1")

    assert comparison["adoptions"] == 3
    assert len(comparison["agent_performance"]) == 3
    # Verify effectiveness values are close to expected
    effectiveness_values = [
        p["effectiveness"] for p in comparison["agent_performance"]
    ]
    for expected_val in expected_values:
        assert any(abs(v - expected_val) < 0.01 for v in effectiveness_values)


@pytest.mark.asyncio
async def test_adoption_rate_calculation(distribution_initialized):
    """Test adoption rate calculation."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")

    # Distribute to 5 agents
    for i in range(5):
        await service.distribute_skill_to_agent(
            "skill_1", "agent1", f"agent{i+2}", skill
        )

    # Get adoption status
    adoption = await service.get_adoption_status("skill_1")

    # All distributions were adopted
    assert adoption["adoption_rate"] == 1.0


@pytest.mark.asyncio
async def test_distribution_event_publishing(distribution_initialized):
    """Test that distribution publishes events."""
    service = distribution_initialized

    # Mock event bus
    service.event_bus = MagicMock()
    service.event_bus.publish = AsyncMock()

    skill = create_test_skill("skill_1")

    # Distribute skill
    await service.distribute_skill_to_agent(
        "skill_1", "agent1", "agent2", skill
    )

    # Verify event published
    service.event_bus.publish.assert_called_once()
    call_args = service.event_bus.publish.call_args
    assert call_args[0][0] == "skill_distributed"


@pytest.mark.asyncio
async def test_health_check(distribution_initialized):
    """Test health check."""
    service = distribution_initialized

    skill = create_test_skill("skill_1")

    # Create some distributions
    for i in range(2):
        await service.distribute_skill_to_agent(
            "skill_1", "agent1", f"agent{i+2}", skill
        )

    # Get health
    health = await service.health_check()

    assert health["total_distributions"] == 2
    assert health["skills_being_adopted"] == 1


@pytest.mark.asyncio
async def test_multiple_skills_distribution(distribution_initialized):
    """Test distributing multiple different skills."""
    service = distribution_initialized

    skill1 = create_test_skill("skill_1", name="Skill One")
    skill2 = create_test_skill("skill_2", name="Skill Two")

    # Distribute different skills to different agents
    await service.distribute_skill_to_agent("skill_1", "agent1", "agent2", skill1)
    await service.distribute_skill_to_agent("skill_2", "agent1", "agent3", skill2)

    # Check separate tracking
    adoption1 = await service.get_adoption_status("skill_1")
    adoption2 = await service.get_adoption_status("skill_2")

    assert adoption1["adoptions"][0]["agent"] == "agent2"
    assert adoption2["adoptions"][0]["agent"] == "agent3"


@pytest.mark.asyncio
async def test_adoption_with_nonexistent_skill(distribution_initialized):
    """Test getting adoption status for nonexistent skill."""
    service = distribution_initialized

    adoption = await service.get_adoption_status("nonexistent_skill")

    assert adoption is None


@pytest.mark.asyncio
async def test_agent_adoptions_empty(distribution_initialized):
    """Test getting adoptions for agent with none."""
    service = distribution_initialized

    adoptions = await service.get_agent_adoptions("agent_no_adoptions")

    assert len(adoptions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
