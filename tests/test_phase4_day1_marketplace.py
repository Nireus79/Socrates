"""
Tests for Phase 4 Day 1: Skill Marketplace Foundation.

Tests:
- Skill registration and cataloging
- Skill discovery by type, effectiveness, usage
- Search functionality
- Indexing and filtering
- Marketplace metrics
- Event publishing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import pytest_asyncio

from modules.marketplace.service import SkillMarketplace


@pytest.fixture
def skill_marketplace():
    """Create a fresh skill marketplace."""
    return SkillMarketplace()


@pytest_asyncio.fixture
async def marketplace_initialized():
    """Create initialized marketplace."""
    service = SkillMarketplace()
    await service.initialize()
    return service


def create_test_skill(
    skill_id: str = "test_skill",
    name: str = "Test Skill",
    skill_type: str = "optimization",
    agent: str = "agent1",
    effectiveness: float = 0.8,
    usage_count: int = 5,
    tags: list = None,
) -> dict:
    """Create test skill data."""
    return {
        "skill_id": skill_id,
        "name": name,
        "type": skill_type,
        "agent": agent,
        "effectiveness": effectiveness,
        "usage_count": usage_count,
        "created_at": "2026-03-25T00:00:00",
        "tags": tags or [],
    }


@pytest.mark.asyncio
async def test_marketplace_initialization(marketplace_initialized):
    """Test marketplace initialization."""
    marketplace = marketplace_initialized

    assert marketplace.service_name == "marketplace"
    assert len(marketplace.catalog) == 0
    assert len(marketplace.index_by_type) == 0


@pytest.mark.asyncio
async def test_register_skill(marketplace_initialized):
    """Test registering a skill."""
    marketplace = marketplace_initialized

    skill_data = create_test_skill("skill_1", "Skill One")
    success = await marketplace.register_skill("skill_1", skill_data)

    assert success is True
    assert "skill_1" in marketplace.catalog
    assert "skill_1" in marketplace.skill_metadata


@pytest.mark.asyncio
async def test_register_duplicate_skill(marketplace_initialized):
    """Test registering duplicate skill."""
    marketplace = marketplace_initialized

    skill_data = create_test_skill("skill_1")
    await marketplace.register_skill("skill_1", skill_data)

    # Try to register again
    success = await marketplace.register_skill("skill_1", skill_data)

    assert success is False


@pytest.mark.asyncio
async def test_register_skill_creates_metadata(marketplace_initialized):
    """Test that registration creates proper metadata."""
    marketplace = marketplace_initialized

    skill_data = create_test_skill(
        "skill_1",
        effectiveness=0.85,
        usage_count=10,
    )
    await marketplace.register_skill("skill_1", skill_data)

    metadata = marketplace.skill_metadata["skill_1"]

    assert metadata["name"] == "Test Skill"
    assert metadata["effectiveness"] == 0.85
    assert metadata["usage_count"] == 10
    assert "registered_at" in metadata


@pytest.mark.asyncio
async def test_index_by_type(marketplace_initialized):
    """Test skill indexing by type."""
    marketplace = marketplace_initialized

    # Register skills of different types
    skill1 = create_test_skill("skill_1", skill_type="optimization")
    skill2 = create_test_skill("skill_2", skill_type="error_handling")
    skill3 = create_test_skill("skill_3", skill_type="optimization")

    await marketplace.register_skill("skill_1", skill1)
    await marketplace.register_skill("skill_2", skill2)
    await marketplace.register_skill("skill_3", skill3)

    # Verify indexing
    assert len(marketplace.index_by_type["optimization"]) == 2
    assert len(marketplace.index_by_type["error_handling"]) == 1
    assert "skill_1" in marketplace.index_by_type["optimization"]


@pytest.mark.asyncio
async def test_index_by_agent(marketplace_initialized):
    """Test skill indexing by agent."""
    marketplace = marketplace_initialized

    # Register skills from different agents
    skill1 = create_test_skill("skill_1", agent="agent1")
    skill2 = create_test_skill("skill_2", agent="agent2")
    skill3 = create_test_skill("skill_3", agent="agent1")

    await marketplace.register_skill("skill_1", skill1)
    await marketplace.register_skill("skill_2", skill2)
    await marketplace.register_skill("skill_3", skill3)

    # Verify indexing
    assert len(marketplace.index_by_agent["agent1"]) == 2
    assert len(marketplace.index_by_agent["agent2"]) == 1


@pytest.mark.asyncio
async def test_discover_skills_all(marketplace_initialized):
    """Test discovering all skills."""
    marketplace = marketplace_initialized

    # Register multiple skills
    for i in range(5):
        skill = create_test_skill(f"skill_{i}", effectiveness=0.5 + (i * 0.1))
        await marketplace.register_skill(f"skill_{i}", skill)

    # Discover without filter
    results = await marketplace.discover_skills()

    assert len(results) == 5


@pytest.mark.asyncio
async def test_discover_skills_by_type(marketplace_initialized):
    """Test discovering skills by type."""
    marketplace = marketplace_initialized

    # Register skills of different types
    opt_skill = create_test_skill("skill_opt", skill_type="optimization")
    err_skill = create_test_skill("skill_err", skill_type="error_handling")

    await marketplace.register_skill("skill_opt", opt_skill)
    await marketplace.register_skill("skill_err", err_skill)

    # Discover by type
    results = await marketplace.discover_skills(skill_type="optimization")

    assert len(results) == 1
    assert results[0]["skill_id"] == "skill_opt"


@pytest.mark.asyncio
async def test_discover_skills_by_effectiveness(marketplace_initialized):
    """Test discovering skills by effectiveness threshold."""
    marketplace = marketplace_initialized

    # Register skills with different effectiveness
    skill_good = create_test_skill("skill_good", effectiveness=0.9)
    skill_bad = create_test_skill("skill_bad", effectiveness=0.3)

    await marketplace.register_skill("skill_good", skill_good)
    await marketplace.register_skill("skill_bad", skill_bad)

    # Discover only good ones
    results = await marketplace.discover_skills(min_effectiveness=0.8)

    assert len(results) == 1
    assert results[0]["skill_id"] == "skill_good"


@pytest.mark.asyncio
async def test_discover_skills_by_usage(marketplace_initialized):
    """Test discovering skills by minimum usage."""
    marketplace = marketplace_initialized

    # Register skills with different usage counts
    skill_used = create_test_skill("skill_used", usage_count=10)
    skill_new = create_test_skill("skill_new", usage_count=1)

    await marketplace.register_skill("skill_used", skill_used)
    await marketplace.register_skill("skill_new", skill_new)

    # Discover only well-used
    results = await marketplace.discover_skills(min_usage=5)

    assert len(results) == 1
    assert results[0]["skill_id"] == "skill_used"


@pytest.mark.asyncio
async def test_discover_skills_sorted_by_effectiveness(marketplace_initialized):
    """Test that results are sorted by effectiveness."""
    marketplace = marketplace_initialized

    # Register skills in random effectiveness order
    for i in range(5):
        skill = create_test_skill(f"skill_{i}", effectiveness=0.2 + (i * 0.1))
        await marketplace.register_skill(f"skill_{i}", skill)

    # Discover all
    results = await marketplace.discover_skills()

    # Verify sorted descending by effectiveness
    for i in range(len(results) - 1):
        assert results[i]["effectiveness"] >= results[i + 1]["effectiveness"]


@pytest.mark.asyncio
async def test_discover_skills_max_results(marketplace_initialized):
    """Test max results limit."""
    marketplace = marketplace_initialized

    # Register 10 skills
    for i in range(10):
        skill = create_test_skill(f"skill_{i}")
        await marketplace.register_skill(f"skill_{i}", skill)

    # Request max 5
    results = await marketplace.discover_skills(max_results=5)

    assert len(results) == 5


@pytest.mark.asyncio
async def test_search_skills(marketplace_initialized):
    """Test skill search by name."""
    marketplace = marketplace_initialized

    # Register skills with different names and types
    skill1 = create_test_skill("skill_1", name="optimization_advanced", skill_type="optimization")
    skill2 = create_test_skill("skill_2", name="error_recovery", skill_type="error_handling")
    skill3 = create_test_skill("skill_3", name="optimization_basic", skill_type="optimization")

    await marketplace.register_skill("skill_1", skill1)
    await marketplace.register_skill("skill_2", skill2)
    await marketplace.register_skill("skill_3", skill3)

    # Search for optimization (matches name)
    results = await marketplace.search_skills("optimization")

    assert len(results) == 2
    skill_ids = [r["skill_id"] for r in results]
    assert "skill_1" in skill_ids
    assert "skill_3" in skill_ids


@pytest.mark.asyncio
async def test_search_skills_by_type(marketplace_initialized):
    """Test search by skill type."""
    marketplace = marketplace_initialized

    # Register skills
    skill = create_test_skill("skill_1", skill_type="error_handling")
    await marketplace.register_skill("skill_1", skill)

    # Search by type
    results = await marketplace.search_skills("error_handling")

    assert len(results) == 1
    assert results[0]["skill_id"] == "skill_1"


@pytest.mark.asyncio
async def test_get_skills_by_agent(marketplace_initialized):
    """Test getting all skills by agent."""
    marketplace = marketplace_initialized

    # Register skills for different agents
    skill1 = create_test_skill("skill_1", agent="agent1")
    skill2 = create_test_skill("skill_2", agent="agent1")
    skill3 = create_test_skill("skill_3", agent="agent2")

    await marketplace.register_skill("skill_1", skill1)
    await marketplace.register_skill("skill_2", skill2)
    await marketplace.register_skill("skill_3", skill3)

    # Get skills for agent1
    results = await marketplace.get_skills_by_agent("agent1")

    assert len(results) == 2
    skill_ids = [r["skill_id"] for r in results]
    assert "skill_1" in skill_ids
    assert "skill_2" in skill_ids


@pytest.mark.asyncio
async def test_get_skills_by_type(marketplace_initialized):
    """Test getting all skills of a type."""
    marketplace = marketplace_initialized

    # Register skills
    skill1 = create_test_skill("skill_1", skill_type="optimization", effectiveness=0.8)
    skill2 = create_test_skill("skill_2", skill_type="optimization", effectiveness=0.9)
    skill3 = create_test_skill("skill_3", skill_type="error_handling")

    await marketplace.register_skill("skill_1", skill1)
    await marketplace.register_skill("skill_2", skill2)
    await marketplace.register_skill("skill_3", skill3)

    # Get optimization skills
    results = await marketplace.get_skills_by_type("optimization")

    assert len(results) == 2
    # Verify sorted by effectiveness
    assert results[0]["effectiveness"] > results[1]["effectiveness"]


@pytest.mark.asyncio
async def test_get_top_skills(marketplace_initialized):
    """Test getting top performing skills."""
    marketplace = marketplace_initialized

    # Register skills with varying effectiveness
    for i in range(10):
        skill = create_test_skill(f"skill_{i}", effectiveness=0.1 + (i * 0.09))
        await marketplace.register_skill(f"skill_{i}", skill)

    # Get top 3
    results = await marketplace.get_top_skills(limit=3)

    assert len(results) == 3
    # Verify they're the highest effectiveness
    for i in range(len(results) - 1):
        assert results[i]["effectiveness"] >= results[i + 1]["effectiveness"]


@pytest.mark.asyncio
async def test_marketplace_stats(marketplace_initialized):
    """Test marketplace statistics."""
    marketplace = marketplace_initialized

    # Register skills
    for i in range(3):
        skill = create_test_skill(f"skill_{i}", skill_type="optimization", effectiveness=0.7)
        await marketplace.register_skill(f"skill_{i}", skill)

    skill = create_test_skill("skill_type2", skill_type="error_handling", effectiveness=0.5)
    await marketplace.register_skill("skill_type2", skill)

    # Get stats
    stats = await marketplace.get_marketplace_stats()

    assert stats["total_skills"] == 4
    assert stats["total_skill_types"] == 2
    assert "average_effectiveness" in stats


@pytest.mark.asyncio
async def test_get_skill_metadata(marketplace_initialized):
    """Test getting detailed skill metadata."""
    marketplace = marketplace_initialized

    skill = create_test_skill("skill_1", effectiveness=0.85)
    await marketplace.register_skill("skill_1", skill)

    # Get metadata
    metadata = await marketplace.get_skill_metadata("skill_1")

    assert metadata is not None
    assert metadata["skill_id"] == "skill_1"
    assert metadata["effectiveness"] == 0.85
    assert "adoption_stats" in metadata


@pytest.mark.asyncio
async def test_update_skill_in_marketplace(marketplace_initialized):
    """Test updating skill metadata."""
    marketplace = marketplace_initialized

    skill = create_test_skill("skill_1")
    await marketplace.register_skill("skill_1", skill)

    # Update effectiveness
    success = await marketplace.update_skill_in_marketplace(
        "skill_1",
        {"effectiveness": 0.95},
    )

    assert success is True
    assert marketplace.skill_metadata["skill_1"]["effectiveness"] == 0.95


@pytest.mark.asyncio
async def test_register_skill_event_publishing(marketplace_initialized):
    """Test that skill registration publishes events."""
    marketplace = marketplace_initialized

    # Mock event bus
    marketplace.event_bus = MagicMock()
    marketplace.event_bus.publish = AsyncMock()

    # Register skill
    skill = create_test_skill("skill_1")
    await marketplace.register_skill("skill_1", skill)

    # Verify event published
    marketplace.event_bus.publish.assert_called_once()
    call_args = marketplace.event_bus.publish.call_args
    assert call_args[0][0] == "skill_registered"


@pytest.mark.asyncio
async def test_health_check(marketplace_initialized):
    """Test health check."""
    marketplace = marketplace_initialized

    # Register a few skills
    for i in range(2):
        skill = create_test_skill(f"skill_{i}", skill_type="optimization")
        await marketplace.register_skill(f"skill_{i}", skill)

    # Get health
    health = await marketplace.health_check()

    assert health["skills_in_catalog"] == 2
    assert health["skill_types"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
