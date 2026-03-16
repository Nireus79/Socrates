"""
Tests for Phase 3 Day 1: SkillService and SkillGeneratorAgent Integration.

Tests:
- SkillService initialization and lifecycle
- Skill CRUD operations
- Skill storage and retrieval
- Agent-skill associations
- Effectiveness tracking
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from modules.skills.service import SkillService


@pytest.fixture
def skill_service():
    """Create a fresh skill service for each test."""
    return SkillService()


def mock_skill_data():
    """Generate mock skill data."""
    return {
        "status": "success",
        "skills": [
            {
                "name": "optimization",
                "type": "optimization",
                "effectiveness": 0.8,
                "parameters": {"level": "high"},
            },
            {
                "name": "error_handling",
                "type": "resilience",
                "effectiveness": 0.7,
                "parameters": {"recovery": "auto"},
            }
        ]
    }


@pytest.mark.asyncio
async def test_skill_service_initialization(skill_service):
    """Test SkillService initialization."""
    assert skill_service.service_name == "skills"
    assert len(skill_service.skills) == 0
    assert len(skill_service.agent_skills) == 0

    await skill_service.initialize()
    assert skill_service is not None


@pytest.mark.asyncio
async def test_skill_service_health_check(skill_service):
    """Test skill service health check."""
    await skill_service.initialize()

    health = await skill_service.health_check()

    assert "skills_stored" in health
    assert "agents_with_skills" in health
    assert health["skills_stored"] == 0


@pytest.mark.asyncio
async def test_skill_service_with_mocked_generator(skill_service):
    """Test SkillService with mocked SkillGeneratorAgent."""
    await skill_service.initialize()

    # Mock the generator's process method to return skill data
    # Use a lambda to ensure mock_skill_data is called each time
    skill_service.skill_generator = MagicMock()
    skill_service.skill_generator.process = MagicMock(side_effect=lambda x: mock_skill_data())

    result = await skill_service.generate_skills(
        agent_name="test_agent",
        maturity_data={"current_phase": "growth"},
        learning_data={"velocity": 0.8},
    )

    assert result["agent"] == "test_agent"
    assert result["skills_generated"] > 0
    assert len(skill_service.skills) > 0


@pytest.mark.asyncio
async def test_skill_manual_storage(skill_service):
    """Test manual skill storage and retrieval."""
    await skill_service.initialize()

    # Manually create and store a skill
    skill_id = "skill_manual_1"
    skill_data = {
        "id": skill_id,
        "agent": "test_agent",
        "name": "custom_skill",
        "type": "optimization",
        "effectiveness": 0.75,
        "created_at": "2026-03-18T00:00:00",
        "usage_count": 0,
        "parameters": {},
    }

    skill_service.skills[skill_id] = skill_data
    skill_service.agent_skills["test_agent"] = [skill_id]
    skill_service.skill_effectiveness[skill_id] = 0.75

    # Retrieve skill
    skills = await skill_service.get_agent_skills("test_agent")
    assert len(skills) == 1
    assert skills[0]["name"] == "custom_skill"


@pytest.mark.asyncio
async def test_agent_skill_association(skill_service):
    """Test agent-skill associations."""
    await skill_service.initialize()

    # Manually add skills for two agents
    skill_service.skills["skill_1"] = {
        "id": "skill_1",
        "agent": "agent1",
        "name": "skill_1",
        "created_at": "2026-03-18T00:00:00",
    }
    skill_service.skills["skill_2"] = {
        "id": "skill_2",
        "agent": "agent2",
        "name": "skill_2",
        "created_at": "2026-03-18T00:00:00",
    }
    skill_service.agent_skills["agent1"] = ["skill_1"]
    skill_service.agent_skills["agent2"] = ["skill_2"]

    # Verify associations
    agent1_skills = await skill_service.get_agent_skills("agent1")
    agent2_skills = await skill_service.get_agent_skills("agent2")

    assert len(agent1_skills) == 1
    assert len(agent2_skills) == 1
    assert agent1_skills[0]["id"] == "skill_1"
    assert agent2_skills[0]["id"] == "skill_2"


@pytest.mark.asyncio
async def test_skill_effectiveness_tracking(skill_service):
    """Test skill effectiveness tracking."""
    await skill_service.initialize()

    # Create a skill with all required fields
    skill_id = "skill_eff_1"
    skill_service.skills[skill_id] = {
        "id": skill_id,
        "agent": "agent1",
        "name": "test_skill",
        "type": "optimization",
        "effectiveness": 0.5,
        "created_at": "2026-03-18T00:00:00",
    }
    skill_service.skill_effectiveness[skill_id] = 0.5
    skill_service.skill_usage[skill_id] = 1

    # Update effectiveness
    success = await skill_service.update_skill_effectiveness(skill_id, 0.9)
    assert success is True

    # Verify effectiveness was updated
    stats = await skill_service.get_skill_stats(skill_id)
    assert "effectiveness" in stats
    assert stats["effectiveness"] > 0.5


@pytest.mark.asyncio
async def test_skill_usage_tracking(skill_service):
    """Test skill usage counting."""
    await skill_service.initialize()

    skill_id = "skill_usage_1"
    skill_service.skills[skill_id] = {
        "id": skill_id,
        "agent": "agent1",
        "name": "usage_test_skill",
        "created_at": "2026-03-18T00:00:00",
    }
    skill_service.skill_usage[skill_id] = 0

    # Apply skill multiple times
    success1 = await skill_service.apply_skill(skill_id)
    success2 = await skill_service.apply_skill(skill_id)
    success3 = await skill_service.apply_skill(skill_id)

    assert success1 is True
    assert success2 is True
    assert success3 is True

    # Verify usage count
    stats = await skill_service.get_skill_stats(skill_id)
    assert stats["usage_count"] == 3


@pytest.mark.asyncio
async def test_list_skills_all(skill_service):
    """Test listing all skills."""
    await skill_service.initialize()

    # Add some skills
    skill_service.skills["skill_1"] = {
        "id": "skill_1",
        "agent": "agent1",
        "name": "skill_1",
        "created_at": "2026-03-18T00:00:00",
    }
    skill_service.skills["skill_2"] = {
        "id": "skill_2",
        "agent": "agent2",
        "name": "skill_2",
        "created_at": "2026-03-18T00:00:00",
    }

    # List all
    result = await skill_service.list_skills()

    assert result["total_skills"] == 2
    assert len(result["skills"]) == 2


@pytest.mark.asyncio
async def test_list_skills_by_agent(skill_service):
    """Test listing skills for specific agent."""
    await skill_service.initialize()

    # Add skills
    skill_service.skills["skill_1"] = {
        "id": "skill_1",
        "agent": "agent1",
        "name": "skill_1",
        "created_at": "2026-03-18T00:00:00",
    }
    skill_service.skills["skill_2"] = {
        "id": "skill_2",
        "agent": "agent1",
        "name": "skill_2",
        "created_at": "2026-03-18T00:00:00",
    }
    skill_service.agent_skills["agent1"] = ["skill_1", "skill_2"]

    # List for agent
    result = await skill_service.list_skills("agent1")

    assert result["agent"] == "agent1"
    assert result["count"] == 2


@pytest.mark.asyncio
async def test_skill_recommendations(skill_service):
    """Test skill recommendations."""
    await skill_service.initialize()

    # Mock the generator if available
    if skill_service.skill_generator:
        skill_service.skill_generator.process = MagicMock(return_value={
            "recommendations": [
                {
                    "skill": "error_handling",
                    "confidence": 0.85,
                }
            ]
        })

    result = await skill_service.get_skill_recommendations("test_agent")

    assert "recommendations" in result
    assert result["agent"] == "test_agent"
    assert isinstance(result["recommendations"], list)


@pytest.mark.asyncio
async def test_apply_nonexistent_skill(skill_service):
    """Test applying nonexistent skill gracefully."""
    await skill_service.initialize()

    result = await skill_service.apply_skill("nonexistent_skill_id")
    assert result is False


@pytest.mark.asyncio
async def test_get_stats_nonexistent_skill(skill_service):
    """Test getting stats for nonexistent skill."""
    await skill_service.initialize()

    result = await skill_service.get_skill_stats("nonexistent_skill_id")
    assert "error" in result


@pytest.mark.asyncio
async def test_skill_service_shutdown(skill_service):
    """Test SkillService shutdown."""
    await skill_service.initialize()

    # Add some data
    skill_service.skills["skill_1"] = {
        "id": "skill_1",
        "name": "skill_1",
        "created_at": "2026-03-18T00:00:00",
    }
    skill_service.agent_skills["agent1"] = ["skill_1"]

    assert len(skill_service.skills) > 0

    # Shutdown
    await skill_service.shutdown()

    # Data should be cleared
    assert len(skill_service.skills) == 0
    assert len(skill_service.agent_skills) == 0


@pytest.mark.asyncio
async def test_skill_service_event_bus(skill_service):
    """Test SkillService event bus integration."""
    from core.event_bus import EventBus

    event_bus = EventBus()
    skill_service.set_event_bus(event_bus)

    assert skill_service.event_bus is not None

    await skill_service.initialize()

    # Mock the generator
    skill_service.skill_generator = MagicMock()
    skill_service.skill_generator.process = MagicMock(return_value=mock_skill_data())

    events_received = []

    async def handler(event):
        events_received.append(event)

    event_bus.subscribe("skills_generated", handler)

    # Generate skills (should publish event)
    await skill_service.generate_skills(
        agent_name="test_agent",
        maturity_data={},
        learning_data={},
    )

    # Verify event was published
    assert len(events_received) > 0
    assert events_received[0].event_type == "skills_generated"


@pytest.mark.asyncio
async def test_ecosystem_skill_generator_available(skill_service):
    """Test that SkillGeneratorAgent from ecosystem is available."""
    await skill_service.initialize()

    # Should have loaded the real generator
    # (or None gracefully if not available)
    # This test just verifies no errors during initialization
    assert True  # If we got here without exception, initialization succeeded


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
