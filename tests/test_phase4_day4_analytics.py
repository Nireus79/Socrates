"""
Tests for Phase 4 Day 4: Analytics & Optimization.

Tests:
- Skill metric tracking
- Performance analysis
- High-performing skill identification
- Ecosystem health monitoring
- Performance reporting
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import pytest_asyncio

from modules.analytics.service import SkillAnalytics


@pytest.fixture
def skill_analytics():
    """Create a fresh analytics service."""
    return SkillAnalytics()


@pytest_asyncio.fixture
async def analytics_initialized():
    """Create initialized analytics service."""
    service = SkillAnalytics()
    await service.initialize()
    return service


@pytest.mark.asyncio
async def test_analytics_initialization(analytics_initialized):
    """Test analytics initialization."""
    analytics = analytics_initialized

    assert analytics.service_name == "analytics"
    assert len(analytics.metrics_cache) == 0


@pytest.mark.asyncio
async def test_track_skill_metric(analytics_initialized):
    """Test tracking skill metrics."""
    analytics = analytics_initialized

    success = await analytics.track_skill_metric(
        skill_id="skill_1",
        agent_name="agent1",
        metric_name="effectiveness",
        metric_value=0.85,
    )

    assert success is True
    assert "skill_1" in analytics.metrics_cache
    assert "agent1" in analytics.metrics_cache["skill_1"]["agents_using"]


@pytest.mark.asyncio
async def test_multiple_metrics_tracking(analytics_initialized):
    """Test tracking multiple metrics for a skill."""
    analytics = analytics_initialized

    # Track different metrics
    await analytics.track_skill_metric("skill_1", "agent1", "effectiveness", 0.85)
    await analytics.track_skill_metric("skill_1", "agent1", "adoption", 5.0)

    metrics = analytics.metrics_cache["skill_1"]["metrics"]
    assert len(metrics) == 2
    assert len(metrics["effectiveness"]) == 1
    assert len(metrics["adoption"]) == 1


@pytest.mark.asyncio
async def test_analyze_skill_performance(analytics_initialized):
    """Test analyzing skill performance."""
    analytics = analytics_initialized

    # Track metrics
    for score in [0.8, 0.85, 0.9]:
        await analytics.track_skill_metric("skill_1", "agent1", "effectiveness", score)

    # Analyze
    analysis = await analytics.analyze_skill_performance("skill_1")

    assert analysis is not None
    assert analysis["skill_id"] == "skill_1"
    assert "metric_summaries" in analysis
    assert analysis["metric_summaries"]["effectiveness"]["average"] == (0.8 + 0.85 + 0.9) / 3


@pytest.mark.asyncio
async def test_identify_high_performing_skills(analytics_initialized):
    """Test identifying high-performing skills."""
    analytics = analytics_initialized

    # Track metrics for multiple skills
    for skill_num in range(3):
        skill_id = f"skill_{skill_num}"
        # High performers
        for _ in range(3):
            await analytics.track_skill_metric(skill_id, f"agent_{skill_num}", "effectiveness", 0.85)
    
    # Low performer
    await analytics.track_skill_metric("skill_low", "agent_low", "effectiveness", 0.5)

    # Identify high performers
    high_performers = await analytics.identify_high_performing_skills(min_effectiveness=0.75)

    assert len(high_performers) == 3
    assert all(h["effectiveness"] >= 0.75 for h in high_performers)


@pytest.mark.asyncio
async def test_ecosystem_health_excellent(analytics_initialized):
    """Test ecosystem health with excellent scores."""
    analytics = analytics_initialized

    # Create excellent ecosystem
    for i in range(3):
        skill_id = f"skill_{i}"
        for _ in range(2):
            await analytics.track_skill_metric(skill_id, f"agent_{i}", "effectiveness", 0.9)

    # Check health
    health = await analytics.get_ecosystem_health()

    assert health["ecosystem_health"] == "excellent"
    assert health["average_effectiveness"] > 0.8


@pytest.mark.asyncio
async def test_ecosystem_health_good(analytics_initialized):
    """Test ecosystem health with good scores."""
    analytics = analytics_initialized

    # Create good ecosystem (0.7 effectiveness)
    for i in range(2):
        await analytics.track_skill_metric(f"skill_{i}", "agent1", "effectiveness", 0.7)

    health = await analytics.get_ecosystem_health()

    assert health["ecosystem_health"] == "good"
    assert 0.6 < health["average_effectiveness"] <= 0.8


@pytest.mark.asyncio
async def test_ecosystem_health_poor(analytics_initialized):
    """Test ecosystem health with poor scores."""
    analytics = analytics_initialized

    # Create poor ecosystem (0.3 effectiveness)
    await analytics.track_skill_metric("skill_1", "agent1", "effectiveness", 0.3)

    health = await analytics.get_ecosystem_health()

    assert health["ecosystem_health"] == "poor"


@pytest.mark.asyncio
async def test_performance_report(analytics_initialized):
    """Test generating performance report."""
    analytics = analytics_initialized

    # Track some metrics
    await analytics.track_skill_metric("skill_1", "agent1", "effectiveness", 0.85)
    await analytics.track_skill_metric("skill_2", "agent1", "effectiveness", 0.75)

    # Generate report
    report = await analytics.get_performance_report()

    assert "report_type" in report
    assert "ecosystem_health" in report
    assert "high_performers" in report


@pytest.mark.asyncio
async def test_health_check(analytics_initialized):
    """Test health check."""
    analytics = analytics_initialized

    await analytics.track_skill_metric("skill_1", "agent1", "effectiveness", 0.8)

    health = await analytics.health_check()

    assert health["skills_tracked"] == 1


@pytest.mark.asyncio
async def test_no_data_ecosystem_health(analytics_initialized):
    """Test ecosystem health with no data."""
    analytics = analytics_initialized

    health = await analytics.get_ecosystem_health()

    assert health["ecosystem_health"] == "no_data"
    assert health["total_skills"] == 0


@pytest.mark.asyncio
async def test_high_performers_limit(analytics_initialized):
    """Test high performers limit."""
    analytics = analytics_initialized

    # Create 15 high-performing skills
    for i in range(15):
        await analytics.track_skill_metric(f"skill_{i}", "agent1", "effectiveness", 0.85)

    # Get top 5
    high_performers = await analytics.identify_high_performing_skills(limit=5)

    assert len(high_performers) <= 5


@pytest.mark.asyncio
async def test_analyze_nonexistent_skill(analytics_initialized):
    """Test analyzing nonexistent skill."""
    analytics = analytics_initialized

    analysis = await analytics.analyze_skill_performance("nonexistent")

    assert analysis is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
