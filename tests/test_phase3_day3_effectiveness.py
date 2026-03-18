"""
Tests for Phase 3 Day 3: Effectiveness Tracking and Optimization.

Tests:
- Skill execution tracking
- Performance score calculation
- Effectiveness updates
- Trend analysis
- Skill optimization
- Effectiveness reporting
- Performance history
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import pytest_asyncio

from modules.skills.service import SkillService


@pytest.fixture
def skill_service():
    """Create a fresh skill service for each test."""
    return SkillService()


@pytest_asyncio.fixture
async def skill_service_initialized():
    """Create initialized skill service."""
    service = SkillService()
    await service.initialize()
    return service


@pytest.mark.asyncio
async def test_track_skill_execution_success(skill_service_initialized):
    """Test tracking skill execution with successful result."""
    service = skill_service_initialized

    # Create a skill
    skill_id = "skill_track_1"
    service.skills[skill_id] = {
        "id": skill_id,
        "name": "test_skill",
        "agent": "agent1",
        "effectiveness": 0.5,
        "created_at": "2026-03-18T00:00:00",
    }
    service.skill_effectiveness[skill_id] = 0.5
    service.skill_usage[skill_id] = 1

    # Track successful execution
    result = {"status": "success", "result": "Task completed"}
    success = await service.track_skill_execution(skill_id, result)

    # Verify
    assert success is True
    assert skill_id in service.skill_performance
    assert len(service.skill_performance[skill_id]) == 1
    assert service.skill_performance[skill_id][0] == 0.9  # Success score


@pytest.mark.asyncio
async def test_track_skill_execution_updates_effectiveness(skill_service_initialized):
    """Test that tracking execution updates effectiveness score."""
    service = skill_service_initialized

    # Create a skill
    skill_id = "skill_eff_1"
    service.skills[skill_id] = {
        "id": skill_id,
        "name": "test_skill",
        "agent": "agent1",
        "effectiveness": 0.5,
        "created_at": "2026-03-18T00:00:00",
    }
    service.skill_effectiveness[skill_id] = 0.5
    service.skill_usage[skill_id] = 1

    # Track execution with high performance
    result = {"status": "success"}
    await service.track_skill_execution(skill_id, result, performance_score=0.95)

    # Verify effectiveness was updated
    new_eff = service.skill_effectiveness[skill_id]
    assert new_eff > 0.5
    assert new_eff == (0.5 * 1 + 0.95) / 2  # Weighted average


@pytest.mark.asyncio
async def test_track_nonexistent_skill(skill_service_initialized):
    """Test tracking nonexistent skill gracefully."""
    service = skill_service_initialized

    # Track execution for nonexistent skill
    result = {"status": "success"}
    success = await service.track_skill_execution("nonexistent", result)

    # Should return False
    assert success is False


@pytest.mark.asyncio
async def test_calculate_performance_score_success(skill_service_initialized):
    """Test performance score calculation for success."""
    service = skill_service_initialized

    # Test different status values
    score_success = service._calculate_performance_score({"status": "success"})
    score_partial = service._calculate_performance_score({"status": "partial_success"})
    score_error = service._calculate_performance_score({"status": "error"})

    assert score_success == 0.9
    assert score_partial == 0.6
    assert score_error == 0.1


@pytest.mark.asyncio
async def test_calculate_performance_score_explicit(skill_service_initialized):
    """Test explicit performance score in result."""
    service = skill_service_initialized

    # Test explicit score
    result = {
        "status": "success",
        "performance_score": 0.75,
    }
    score = service._calculate_performance_score(result)

    assert score == 0.75


@pytest.mark.asyncio
async def test_performance_trend_improving(skill_service_initialized):
    """Test trend calculation for improving performance."""
    service = skill_service_initialized

    # Simulate improving trend
    history = [0.3, 0.4, 0.5, 0.7, 0.8, 0.85, 0.9]

    trend = service._calculate_trend(history)

    assert trend == "improving"


@pytest.mark.asyncio
async def test_performance_trend_declining(skill_service_initialized):
    """Test trend calculation for declining performance."""
    service = skill_service_initialized

    # Simulate declining trend
    history = [0.9, 0.85, 0.8, 0.6, 0.5, 0.4, 0.3]

    trend = service._calculate_trend(history)

    assert trend == "declining"


@pytest.mark.asyncio
async def test_performance_trend_stable(skill_service_initialized):
    """Test trend calculation for stable performance."""
    service = skill_service_initialized

    # Simulate stable trend
    history = [0.6, 0.62, 0.61, 0.59, 0.60]

    trend = service._calculate_trend(history)

    assert trend == "stable"


@pytest.mark.asyncio
async def test_multiple_executions_track_history(skill_service_initialized):
    """Test that multiple executions build performance history."""
    service = skill_service_initialized

    # Create a skill
    skill_id = "skill_multi_1"
    service.skills[skill_id] = {
        "id": skill_id,
        "name": "test_skill",
        "agent": "agent1",
        "effectiveness": 0.5,
        "created_at": "2026-03-18T00:00:00",
    }
    service.skill_effectiveness[skill_id] = 0.5
    service.skill_usage[skill_id] = 0

    # Execute multiple times
    for _ in range(5):
        result = {"status": "success"}
        await service.track_skill_execution(skill_id, result)

    # Verify history
    assert len(service.skill_performance[skill_id]) == 5
    assert all(s == 0.9 for s in service.skill_performance[skill_id])


@pytest.mark.asyncio
async def test_optimize_skills_removes_ineffective(skill_service_initialized):
    """Test skill optimization removes ineffective skills."""
    service = skill_service_initialized

    # Create skills with varying effectiveness
    service.skills["skill_good"] = {
        "id": "skill_good",
        "name": "good_skill",
        "agent": "agent1",
        "effectiveness": 0.8,
        "created_at": "2026-03-18T00:00:00",
    }
    service.skills["skill_bad"] = {
        "id": "skill_bad",
        "name": "bad_skill",
        "agent": "agent1",
        "effectiveness": 0.2,
        "created_at": "2026-03-18T00:00:00",
    }

    service.skill_effectiveness["skill_good"] = 0.8
    service.skill_effectiveness["skill_bad"] = 0.2
    service.skill_usage["skill_good"] = 2
    service.skill_usage["skill_bad"] = 10  # Used many times but ineffective

    service.agent_skills["agent1"] = ["skill_good", "skill_bad"]

    # Optimize skills
    result = await service.optimize_skills("agent1")

    # Verify bad skill was removed
    assert "skill_bad" in result["removed_skills"]
    assert "skill_good" not in result["removed_skills"]
    assert "skill_good" in service.agent_skills["agent1"]
    assert "skill_bad" not in service.agent_skills["agent1"]


@pytest.mark.asyncio
async def test_optimize_skills_identifies_improvements(skill_service_initialized):
    """Test skill optimization identifies skills needing improvement."""
    service = skill_service_initialized

    # Create skill needing improvement
    service.skills["skill_improve"] = {
        "id": "skill_improve",
        "name": "improve_skill",
        "agent": "agent1",
        "effectiveness": 0.4,
        "created_at": "2026-03-18T00:00:00",
    }

    service.skill_effectiveness["skill_improve"] = 0.4
    service.skill_usage["skill_improve"] = 2
    service.agent_skills["agent1"] = ["skill_improve"]

    # Optimize
    result = await service.optimize_skills("agent1")

    # Verify skill flagged for improvement
    assert len(result["optimized_skills"]) == 1
    assert result["optimized_skills"][0]["skill_id"] == "skill_improve"
    assert result["optimized_skills"][0]["action"] == "improve"


@pytest.mark.asyncio
async def test_optimize_skills_no_agents(skill_service_initialized):
    """Test optimization when agent has no skills."""
    service = skill_service_initialized

    # Optimize agent with no skills
    result = await service.optimize_skills("agent_no_skills")

    # Should return empty results
    assert result["optimized_skills"] == []
    assert result["removed_skills"] == []


@pytest.mark.asyncio
async def test_get_effectiveness_report_single_agent(skill_service_initialized):
    """Test effectiveness report for single agent."""
    service = skill_service_initialized

    # Create skills for agent
    service.skills["skill_1"] = {
        "id": "skill_1",
        "name": "skill_1",
        "agent": "agent1",
        "effectiveness": 0.8,
        "created_at": "2026-03-18T00:00:00",
    }
    service.skills["skill_2"] = {
        "id": "skill_2",
        "name": "skill_2",
        "agent": "agent1",
        "effectiveness": 0.6,
        "created_at": "2026-03-18T00:00:00",
    }

    service.skill_effectiveness["skill_1"] = 0.8
    service.skill_effectiveness["skill_2"] = 0.6
    service.skill_usage["skill_1"] = 5
    service.skill_usage["skill_2"] = 3
    service.agent_skills["agent1"] = ["skill_1", "skill_2"]

    # Get report
    report = await service.get_effectiveness_report("agent1")

    # Verify
    assert report["agent"] == "agent1"
    assert len(report["skills"]) == 2
    assert report["average_effectiveness"] == 0.7  # (0.8 + 0.6) / 2


@pytest.mark.asyncio
async def test_get_effectiveness_report_all_skills(skill_service_initialized):
    """Test effectiveness report for all skills."""
    service = skill_service_initialized

    # Create multiple skills
    service.skills["skill_1"] = {
        "id": "skill_1",
        "name": "skill_1",
        "agent": "agent1",
        "effectiveness": 0.8,
        "created_at": "2026-03-18T00:00:00",
    }
    service.skills["skill_2"] = {
        "id": "skill_2",
        "name": "skill_2",
        "agent": "agent2",
        "effectiveness": 0.5,
        "created_at": "2026-03-18T00:00:00",
    }

    service.skill_effectiveness["skill_1"] = 0.8
    service.skill_effectiveness["skill_2"] = 0.5

    # Get all skills report
    report = await service.get_effectiveness_report()

    # Verify
    assert report["total_skills"] == 2
    assert len(report["skills"]) == 2


@pytest.mark.asyncio
async def test_skill_stats_includes_performance_info(skill_service_initialized):
    """Test that skill stats include performance information."""
    service = skill_service_initialized

    # Create skill with performance history
    skill_id = "skill_stats_1"
    service.skills[skill_id] = {
        "id": skill_id,
        "name": "test_skill",
        "agent": "agent1",
        "effectiveness": 0.75,
        "created_at": "2026-03-18T00:00:00",
    }
    service.skill_effectiveness[skill_id] = 0.75
    service.skill_usage[skill_id] = 5
    service.skill_performance[skill_id] = [0.7, 0.8, 0.85, 0.9, 0.75]

    # Get stats
    stats = await service.get_skill_stats(skill_id)

    # Verify
    assert "performance_history_length" in stats
    assert stats["performance_history_length"] == 5
    assert "performance_trend" in stats


@pytest.mark.asyncio
async def test_skill_last_applied_timestamp(skill_service_initialized):
    """Test that last applied timestamp is recorded."""
    service = skill_service_initialized

    # Create skill
    skill_id = "skill_timestamp_1"
    service.skills[skill_id] = {
        "id": skill_id,
        "name": "test_skill",
        "agent": "agent1",
        "effectiveness": 0.5,
        "created_at": "2026-03-18T00:00:00",
    }
    service.skill_effectiveness[skill_id] = 0.5
    service.skill_usage[skill_id] = 0

    # Track execution
    result = {"status": "success"}
    await service.track_skill_execution(skill_id, result)

    # Verify last applied is set
    stats = await service.get_skill_stats(skill_id)
    assert stats["last_applied"] is not None


@pytest.mark.asyncio
async def test_track_skill_event_publishing(skill_service_initialized):
    """Test that skill execution publishes events."""
    service = skill_service_initialized

    # Mock event bus
    service.event_bus = MagicMock()
    service.event_bus.publish = AsyncMock()

    # Create skill
    skill_id = "skill_event_1"
    service.skills[skill_id] = {
        "id": skill_id,
        "name": "test_skill",
        "agent": "agent1",
        "effectiveness": 0.5,
        "created_at": "2026-03-18T00:00:00",
    }
    service.skill_effectiveness[skill_id] = 0.5
    service.skill_usage[skill_id] = 0

    # Track execution
    result = {"status": "success"}
    await service.track_skill_execution(skill_id, result)

    # Verify event was published
    service.event_bus.publish.assert_called_once()
    call_args = service.event_bus.publish.call_args
    assert call_args[0][0] == "skill_executed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
