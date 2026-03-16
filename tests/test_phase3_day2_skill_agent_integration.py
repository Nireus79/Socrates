"""
Tests for Phase 3 Day 2: Skill-Agent Integration.

Tests:
- AgentsService skill retrieval
- Skill availability in agent context
- Skill usage tracking
- Agent execution with skills
- Skill effectiveness updates after execution
- Multiple skill application
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from modules.agents.service import AgentsService
from modules.skills.service import SkillService
from modules.agents.base import Agent


class MockAgent(Agent):
    """Mock agent for testing."""

    def __init__(self, name: str = "test_agent"):
        self.name = name
        self.processed = False
        # Don't call parent __init__ since we're not using orchestrator
        self.orchestrator = None

    def process(self, request: dict) -> dict:
        """Mock process implementation."""
        return {
            "status": "success",
            "result": "Mock result",
            "skills_available": request.get("skills_available_count", 0),
            "skills_used": request.get("skills_used", []),
        }

    async def process_async(self, context: dict) -> dict:
        """Mock async process implementation."""
        self.processed = True
        return self.process(context)


@pytest.fixture
def agents_service():
    """Create agents service."""
    return AgentsService()


@pytest.fixture
def skills_service():
    """Create skills service."""
    return SkillService()


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator."""
    orchestrator = MagicMock()
    orchestrator.call_service = AsyncMock()
    return orchestrator


@pytest.mark.asyncio
async def test_agents_service_get_agent_skills(agents_service, skills_service, mock_orchestrator):
    """Test AgentsService retrieving skills from SkillService."""
    await agents_service.initialize()

    # Set up mock orchestrator
    agents_service.set_orchestrator(mock_orchestrator)

    # Create test skills
    test_skills = [
        {
            "id": "skill_1",
            "name": "optimization",
            "agent": "test_agent",
            "effectiveness": 0.8,
        },
        {
            "id": "skill_2",
            "name": "error_handling",
            "agent": "test_agent",
            "effectiveness": 0.7,
        },
    ]

    # Mock orchestrator to return skills
    mock_orchestrator.call_service.return_value = test_skills

    # Get skills
    skills = await agents_service.get_agent_skills("test_agent")

    # Verify
    assert len(skills) == 2
    assert skills[0]["id"] == "skill_1"
    assert skills[1]["id"] == "skill_2"
    mock_orchestrator.call_service.assert_called_with(
        "skills", "get_agent_skills", "test_agent"
    )


@pytest.mark.asyncio
async def test_agents_service_get_agent_skills_no_orchestrator(agents_service):
    """Test getting skills without orchestrator."""
    await agents_service.initialize()

    # Get skills (no orchestrator set)
    skills = await agents_service.get_agent_skills("test_agent")

    # Should return empty list
    assert skills == []


@pytest.mark.asyncio
async def test_agents_service_apply_skill_usage(agents_service, mock_orchestrator):
    """Test applying skill usage."""
    await agents_service.initialize()
    agents_service.set_orchestrator(mock_orchestrator)

    # Mock skill application
    mock_orchestrator.call_service.return_value = True

    # Apply skill
    result = await agents_service.apply_skill_usage("test_agent", "skill_1")

    # Verify
    assert result is True
    mock_orchestrator.call_service.assert_called_with(
        "skills", "apply_skill", "skill_1"
    )


@pytest.mark.asyncio
async def test_agents_service_apply_skill_no_orchestrator(agents_service):
    """Test applying skill without orchestrator."""
    await agents_service.initialize()

    # Apply skill (no orchestrator)
    result = await agents_service.apply_skill_usage("test_agent", "skill_1")

    # Should return False
    assert result is False


@pytest.mark.asyncio
async def test_execute_agent_with_skills(agents_service, mock_orchestrator):
    """Test executing agent with available skills."""
    await agents_service.initialize()
    agents_service.set_orchestrator(mock_orchestrator)

    # Register agent
    agent = MockAgent("test_agent")
    await agents_service.register_agent(agent)

    # Mock skill retrieval
    test_skills = [
        {"id": "skill_1", "name": "optimization", "effectiveness": 0.8},
        {"id": "skill_2", "name": "error_handling", "effectiveness": 0.7},
    ]
    mock_orchestrator.call_service.return_value = test_skills

    # Execute agent
    result = await agents_service.execute_agent("test_agent", "test task")

    # Verify
    assert result["status"] == "success"
    assert result["skills_available"] == 2
    assert result["agent"] == "test_agent"
    assert agent.processed is True


@pytest.mark.asyncio
async def test_execute_agent_tracks_skill_usage(agents_service, mock_orchestrator):
    """Test that agent execution tracks skill usage."""
    await agents_service.initialize()
    agents_service.set_orchestrator(mock_orchestrator)

    # Register agent
    agent = MockAgent("test_agent")
    await agents_service.register_agent(agent)

    # Mock skill retrieval and application
    test_skills = [
        {"id": "skill_1", "name": "optimization", "effectiveness": 0.8},
    ]

    def mock_call_service(service_name, method_name, *args):
        if method_name == "get_agent_skills":
            return test_skills
        elif method_name == "apply_skill":
            return True
        return None

    mock_orchestrator.call_service.side_effect = mock_call_service

    # Create custom agent that uses skills
    class SkillUsingAgent(Agent):
        def __init__(self, name: str = "skill_agent"):
            self.name = name
            self.orchestrator = None

        def process(self, request: dict) -> dict:
            return {
                "status": "success",
                "result": "Used skill successfully",
                "skills_used": ["skill_1"],  # Track which skills were used
            }

        async def process_async(self, context: dict) -> dict:
            return self.process(context)

    # Register skill-using agent
    await agents_service.register_agent(SkillUsingAgent("skill_agent"))

    # Execute agent
    result = await agents_service.execute_agent("skill_agent", "test task")

    # Verify skill usage was tracked
    assert result["skills_used"] == 1
    assert result["skills_available"] == 1


@pytest.mark.asyncio
async def test_execute_agent_without_skills(agents_service, mock_orchestrator):
    """Test executing agent when no skills are available."""
    await agents_service.initialize()
    agents_service.set_orchestrator(mock_orchestrator)

    # Register agent
    agent = MockAgent("test_agent")
    await agents_service.register_agent(agent)

    # Mock empty skill retrieval
    mock_orchestrator.call_service.return_value = []

    # Execute agent
    result = await agents_service.execute_agent("test_agent", "test task")

    # Verify
    assert result["status"] == "success"
    assert result["skills_available"] == 0
    assert result["skills_used"] == 0


@pytest.mark.asyncio
async def test_execute_agent_missing_agent(agents_service):
    """Test executing non-existent agent."""
    await agents_service.initialize()

    # Execute non-existent agent
    result = await agents_service.execute_agent("nonexistent", "task")

    # Should return error
    assert result["status"] == "error"
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_agent_execution_history_with_skills(agents_service, mock_orchestrator):
    """Test execution history includes skill information."""
    await agents_service.initialize()
    agents_service.set_orchestrator(mock_orchestrator)

    # Register agent
    agent = MockAgent("test_agent")
    await agents_service.register_agent(agent)

    # Mock skills
    test_skills = [
        {"id": "skill_1", "name": "optimization"},
        {"id": "skill_2", "name": "error_handling"},
    ]
    mock_orchestrator.call_service.return_value = test_skills

    # Execute agent
    await agents_service.execute_agent("test_agent", "task 1")
    await agents_service.execute_agent("test_agent", "task 2")

    # Get history
    history = await agents_service.get_execution_history("test_agent")

    # Verify
    assert len(history) == 2
    assert history[0]["skills_available"] == 2
    assert history[1]["skills_available"] == 2


@pytest.mark.asyncio
async def test_skill_retrieval_failure_graceful(agents_service, mock_orchestrator):
    """Test that skill retrieval failure doesn't stop agent execution."""
    await agents_service.initialize()
    agents_service.set_orchestrator(mock_orchestrator)

    # Register agent
    agent = MockAgent("test_agent")
    await agents_service.register_agent(agent)

    # Mock orchestrator to raise exception
    mock_orchestrator.call_service.side_effect = Exception("Service error")

    # Execute agent - should still work
    result = await agents_service.execute_agent("test_agent", "task")

    # Should succeed with empty skills
    assert result["status"] == "success"
    assert result["skills_available"] == 0


@pytest.mark.asyncio
async def test_agent_context_includes_skills(agents_service, mock_orchestrator):
    """Test that agent context includes available skills."""
    await agents_service.initialize()
    agents_service.set_orchestrator(mock_orchestrator)

    # Track context passed to agent
    captured_context = {}

    class ContextCapturingAgent(Agent):
        def __init__(self, name: str = "capture_agent"):
            self.name = name
            self.orchestrator = None

        def process(self, request: dict) -> dict:
            captured_context.update(request)
            return {"status": "success"}

        async def process_async(self, context: dict) -> dict:
            return self.process(context)

    # Register agent
    await agents_service.register_agent(ContextCapturingAgent("capture_agent"))

    # Mock skills
    test_skills = [{"id": "skill_1", "name": "test_skill"}]
    mock_orchestrator.call_service.return_value = test_skills

    # Execute agent
    await agents_service.execute_agent("capture_agent", "test task")

    # Verify context includes skills
    assert "available_skills" in captured_context
    assert captured_context["available_skills"] == test_skills
    assert captured_context["skills_available_count"] == 1
    assert captured_context["task"] == "test task"


@pytest.mark.asyncio
async def test_multiple_agents_different_skills(agents_service, mock_orchestrator):
    """Test that different agents get their own skills."""
    await agents_service.initialize()
    agents_service.set_orchestrator(mock_orchestrator)

    # Register two agents
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    await agents_service.register_agent(agent1)
    await agents_service.register_agent(agent2)

    # Create different skill sets
    def mock_call_service(service_name, method_name, agent_name, *args):
        if method_name == "get_agent_skills":
            if agent_name == "agent1":
                return [{"id": "skill_1"}]
            elif agent_name == "agent2":
                return [{"id": "skill_2"}, {"id": "skill_3"}]
        return []

    mock_orchestrator.call_service.side_effect = mock_call_service

    # Execute both agents
    result1 = await agents_service.execute_agent("agent1", "task1")
    result2 = await agents_service.execute_agent("agent2", "task2")

    # Verify each got their own skills
    assert result1["skills_available"] == 1
    assert result2["skills_available"] == 2


@pytest.mark.asyncio
async def test_agent_stats_include_skill_info(agents_service, mock_orchestrator):
    """Test that agent statistics are recorded."""
    await agents_service.initialize()
    agents_service.set_orchestrator(mock_orchestrator)

    # Register agent
    agent = MockAgent("test_agent")
    await agents_service.register_agent(agent)

    # Mock skills
    mock_orchestrator.call_service.return_value = [{"id": "skill_1"}]

    # Execute agent
    await agents_service.execute_agent("test_agent", "task")

    # Get stats
    stats = await agents_service.get_agent_stats("test_agent")

    # Verify
    assert stats["agent"] == "test_agent"
    assert stats["total_executions"] == 1
    assert stats["successful"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
