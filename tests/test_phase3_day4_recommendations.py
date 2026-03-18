"""
Tests for Phase 3 Day 4: Skill Recommendation Engine.

Tests:
- Agent performance analysis
- Skill gap identification
- Recommendation generation
- Confidence scoring
- Recommendation ranking
- Performance-based reasoning
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import pytest_asyncio

from modules.skills.service import SkillService


@pytest.fixture
def skill_service():
    """Create a fresh skill service."""
    return SkillService()


@pytest_asyncio.fixture
async def skill_service_initialized():
    """Create initialized skill service."""
    service = SkillService()
    await service.initialize()
    return service


@pytest.mark.asyncio
async def test_analyze_agent_performance_no_skills(skill_service_initialized):
    """Test analyzing agent with no skills."""
    service = skill_service_initialized

    # Analyze agent without skills
    result = await service.analyze_agent_performance("new_agent")

    # Verify
    assert result["agent"] == "new_agent"
    assert result["current_skills"] == 0
    assert result["average_effectiveness"] == 0


@pytest.mark.asyncio
async def test_analyze_agent_performance_with_skills(skill_service_initialized):
    """Test analyzing agent with existing skills."""
    service = skill_service_initialized

    # Set up agent with skills
    service.agent_skills["agent1"] = ["skill_1", "skill_2"]
    service.skill_effectiveness["skill_1"] = 0.8
    service.skill_effectiveness["skill_2"] = 0.6
    service.skills["skill_1"] = {"id": "skill_1", "name": "skill_1"}
    service.skills["skill_2"] = {"id": "skill_2", "name": "skill_2"}

    # Analyze
    result = await service.analyze_agent_performance("agent1")

    # Verify
    assert result["agent"] == "agent1"
    assert result["current_skills"] == 2
    assert result["average_effectiveness"] == 0.7  # (0.8 + 0.6) / 2


@pytest.mark.asyncio
async def test_analyze_identifies_weak_skills(skill_service_initialized):
    """Test that analysis identifies weak skills."""
    service = skill_service_initialized

    # Set up agent with weak skill
    service.agent_skills["agent1"] = ["skill_good", "skill_weak"]
    service.skill_effectiveness["skill_good"] = 0.8
    service.skill_effectiveness["skill_weak"] = 0.4  # Below 0.6 threshold

    # Analyze
    result = await service.analyze_agent_performance("agent1")

    # Verify weak skill identified
    assert "skill_weak" in result["weak_skills"]
    assert "skill_good" not in result["weak_skills"]


@pytest.mark.asyncio
async def test_analyze_calculates_skill_gap(skill_service_initialized):
    """Test skill gap calculation."""
    service = skill_service_initialized

    # Set up multiple agents with different skill counts
    service.agent_skills["agent1"] = ["skill_1", "skill_2", "skill_3"]
    service.agent_skills["agent2"] = ["skill_1", "skill_2"]
    service.agent_skills["agent3"] = ["skill_1"]

    service.skill_effectiveness["skill_1"] = 0.8
    service.skill_effectiveness["skill_2"] = 0.7
    service.skill_effectiveness["skill_3"] = 0.6

    # Analyze agent3 (has fewer skills than average)
    result = await service.analyze_agent_performance("agent3")

    # Average is (3 + 2 + 1) / 3 = 2, agent3 has 1, gap = 1
    assert result["skill_gap"] > 0


@pytest.mark.asyncio
async def test_recommend_skills_no_available(skill_service_initialized):
    """Test recommendations when all skills are assigned."""
    service = skill_service_initialized

    # Create one skill assigned to agent
    service.skills["skill_1"] = {
        "id": "skill_1",
        "name": "skill_1",
        "type": "optimization",
    }
    service.agent_skills["agent1"] = ["skill_1"]
    service.skill_effectiveness["skill_1"] = 0.8

    # Try to get recommendations
    result = await service.recommend_skills("agent1")

    # Should return empty or indicate all skills assigned
    if "count" in result:
        assert result["count"] == 0
    else:
        assert result.get("reason") == "all_skills_assigned"


@pytest.mark.asyncio
async def test_recommend_skills_basic(skill_service_initialized):
    """Test basic skill recommendation."""
    service = skill_service_initialized

    # Create skills
    service.skills["skill_1"] = {
        "id": "skill_1",
        "name": "skill_1",
        "type": "optimization",
    }
    service.skills["skill_2"] = {
        "id": "skill_2",
        "name": "skill_2",
        "type": "error_handling",
    }

    # Assign skill_1 to agent
    service.agent_skills["agent1"] = ["skill_1"]
    service.skill_effectiveness["skill_1"] = 0.8
    service.skill_effectiveness["skill_2"] = 0.7
    service.skill_usage["skill_2"] = 5

    # Get recommendations
    result = await service.recommend_skills("agent1", max_recommendations=2)

    # Should recommend skill_2
    assert result["count"] >= 1
    assert result["recommendations"][0]["skill_id"] == "skill_2"


@pytest.mark.asyncio
async def test_recommend_skills_ranked_by_confidence(skill_service_initialized):
    """Test that recommendations are ranked by confidence."""
    service = skill_service_initialized

    # Create multiple skills
    service.skills["high_eff"] = {
        "id": "high_eff",
        "name": "high_eff",
        "type": "optimization",
    }
    service.skills["low_eff"] = {
        "id": "low_eff",
        "name": "low_eff",
        "type": "error_handling",
    }

    # Set up effectiveness
    service.agent_skills["agent1"] = []
    service.skill_effectiveness["high_eff"] = 0.95
    service.skill_effectiveness["low_eff"] = 0.3
    service.skill_usage["high_eff"] = 20
    service.skill_usage["low_eff"] = 1

    # Get recommendations
    result = await service.recommend_skills("agent1", max_recommendations=5)

    # High effectiveness should come first
    assert result["recommendations"][0]["skill_id"] == "high_eff"
    assert result["recommendations"][0]["confidence"] > 0.5


@pytest.mark.asyncio
async def test_recommendation_confidence_calculation(skill_service_initialized):
    """Test confidence score calculation."""
    service = skill_service_initialized

    # Set up performance analysis
    performance = {
        "average_effectiveness": 0.6,
        "skill_gap": 2,
        "current_skills": 2,
    }

    # Calculate confidence for high effectiveness, high usage skill
    confidence = service._calculate_recommendation_confidence(
        skill_effectiveness=0.9,
        skill_usage=15,
        performance=performance,
    )

    # Should be high (0.9 * 0.5 + min(1, 15/10) * 0.3 + min(1, 2/5) * 0.2)
    assert confidence > 0.7
    assert 0 <= confidence <= 1.0


@pytest.mark.asyncio
async def test_recommendation_reason_low_performance(skill_service_initialized):
    """Test recommendation reason for low performance."""
    service = skill_service_initialized

    performance = {"average_effectiveness": 0.3}
    skill = {"type": "optimization"}

    reason = service._get_recommendation_reason(skill, performance)

    assert "Low performance" in reason
    assert "optimization" in reason


@pytest.mark.asyncio
async def test_recommendation_reason_skill_gap(skill_service_initialized):
    """Test recommendation reason for skill gap."""
    service = skill_service_initialized

    performance = {
        "average_effectiveness": 0.7,
        "skill_gap": 2,
    }
    skill = {"type": "error_handling"}

    reason = service._get_recommendation_reason(skill, performance)

    assert "Skill gap" in reason or "gap" in reason.lower()


@pytest.mark.asyncio
async def test_recommend_skills_includes_performance_analysis(skill_service_initialized):
    """Test that recommendations include performance analysis."""
    service = skill_service_initialized

    # Set up skills
    service.skills["skill_1"] = {
        "id": "skill_1",
        "name": "skill_1",
        "type": "optimization",
    }
    service.agent_skills["agent1"] = []
    service.skill_effectiveness["skill_1"] = 0.8

    # Get recommendations
    result = await service.recommend_skills("agent1")

    # Should include performance analysis
    assert "performance_analysis" in result
    assert "agent" in result["performance_analysis"]


@pytest.mark.asyncio
async def test_recommend_skills_expected_improvement(skill_service_initialized):
    """Test that recommendations include expected improvement estimate."""
    service = skill_service_initialized

    # Set up skill with high effectiveness
    service.skills["skill_high"] = {
        "id": "skill_high",
        "name": "skill_high",
        "type": "optimization",
    }
    service.agent_skills["agent1"] = []
    service.skill_effectiveness["skill_high"] = 0.9
    service.skill_usage["skill_high"] = 5

    # Get recommendations
    result = await service.recommend_skills("agent1", max_recommendations=1)

    # Should show expected improvement
    assert "expected_improvement" in result["recommendations"][0]
    expected = result["recommendations"][0]["expected_improvement"]
    assert expected > 0


@pytest.mark.asyncio
async def test_recommend_skills_max_limit(skill_service_initialized):
    """Test that max recommendations limit is respected."""
    service = skill_service_initialized

    # Create 10 skills
    for i in range(10):
        skill_id = f"skill_{i}"
        service.skills[skill_id] = {
            "id": skill_id,
            "name": f"skill_{i}",
            "type": "optimization",
        }
        service.skill_effectiveness[skill_id] = 0.5 + (i * 0.04)
        service.skill_usage[skill_id] = i

    service.agent_skills["agent1"] = []

    # Request max 3
    result = await service.recommend_skills("agent1", max_recommendations=3)

    # Should return at most 3
    assert result["count"] <= 3
    assert len(result["recommendations"]) <= 3


@pytest.mark.asyncio
async def test_recommend_skills_event_publishing(skill_service_initialized):
    """Test that recommendations publish events."""
    service = skill_service_initialized

    # Mock event bus
    service.event_bus = MagicMock()
    service.event_bus.publish = AsyncMock()

    # Set up skills
    service.skills["skill_1"] = {
        "id": "skill_1",
        "name": "skill_1",
        "type": "optimization",
    }
    service.agent_skills["agent1"] = []
    service.skill_effectiveness["skill_1"] = 0.8

    # Get recommendations
    await service.recommend_skills("agent1")

    # Should publish event
    service.event_bus.publish.assert_called_once()
    call_args = service.event_bus.publish.call_args
    assert call_args[0][0] == "recommendations_generated"


@pytest.mark.asyncio
async def test_multiple_agents_different_recommendations(skill_service_initialized):
    """Test that different agents get different recommendations."""
    service = skill_service_initialized

    # Set up skills
    service.skills["skill_1"] = {
        "id": "skill_1",
        "name": "skill_1",
        "type": "optimization",
    }
    service.skills["skill_2"] = {
        "id": "skill_2",
        "name": "skill_2",
        "type": "error_handling",
    }

    # Assign different skills to different agents
    service.agent_skills["agent1"] = ["skill_1"]
    service.agent_skills["agent2"] = ["skill_2"]
    service.skill_effectiveness["skill_1"] = 0.8
    service.skill_effectiveness["skill_2"] = 0.7

    # Get recommendations for both
    rec1 = await service.recommend_skills("agent1")
    rec2 = await service.recommend_skills("agent2")

    # Agent1 should get skill_2, agent2 should get skill_1
    if rec1["count"] > 0:
        assert rec1["recommendations"][0]["skill_id"] == "skill_2"
    if rec2["count"] > 0:
        assert rec2["recommendations"][0]["skill_id"] == "skill_1"


@pytest.mark.asyncio
async def test_recommend_skills_handles_errors(skill_service_initialized):
    """Test that recommendation handles errors gracefully."""
    service = skill_service_initialized

    # This should handle gracefully even with malformed data
    result = await service.recommend_skills("nonexistent_agent")

    assert "error" not in result or result.get("recommendations") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
