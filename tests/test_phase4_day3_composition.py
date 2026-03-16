"""
Tests for Phase 4 Day 3: Skill Composition & Chaining.

Tests:
- Composition creation
- Sequential execution
- Parallel execution
- Conditional execution
- Parameter mapping
- Error handling
- Execution history
- Performance metrics
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import pytest_asyncio

from modules.composition.service import SkillComposer, SkillComposition


@pytest.fixture
def skill_composer():
    """Create a fresh skill composer."""
    return SkillComposer()


@pytest_asyncio.fixture
async def composer_initialized():
    """Create initialized composer."""
    service = SkillComposer()
    await service.initialize()
    return service


async def mock_skill_executor(skill_id: str, context: dict) -> dict:
    """Mock skill executor for testing."""
    # Simulate skill execution
    return {
        "status": "success",
        "skill_id": skill_id,
        "output": f"result_{skill_id}",
        "context_received": len(context) > 0,
    }


@pytest.mark.asyncio
async def test_composer_initialization(composer_initialized):
    """Test composer initialization."""
    composer = composer_initialized

    assert composer.service_name == "composition"
    assert len(composer.compositions) == 0
    assert len(composer.execution_history) == 0


@pytest.mark.asyncio
async def test_create_composition(composer_initialized):
    """Test creating a composition."""
    composer = composer_initialized

    success = await composer.create_composition(
        composition_id="comp_1",
        name="Test Composition",
        skills=["skill_1", "skill_2", "skill_3"],
        execution_type="sequential",
    )

    assert success is True
    assert "comp_1" in composer.compositions


@pytest.mark.asyncio
async def test_create_duplicate_composition(composer_initialized):
    """Test creating duplicate composition fails."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Test Composition",
        skills=["skill_1"],
    )

    # Try to create duplicate
    success = await composer.create_composition(
        composition_id="comp_1",
        name="Test Composition",
        skills=["skill_1"],
    )

    assert success is False


@pytest.mark.asyncio
async def test_composition_data_model(composer_initialized):
    """Test composition data model."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Test",
        skills=["skill_1", "skill_2"],
    )

    composition = composer.compositions["comp_1"]
    assert composition.composition_id == "comp_1"
    assert composition.name == "Test"
    assert composition.skills == ["skill_1", "skill_2"]
    assert composition.execution_type == "sequential"


@pytest.mark.asyncio
async def test_add_parameter_mapping(composer_initialized):
    """Test adding parameter mappings."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Test",
        skills=["skill_1", "skill_2"],
    )

    success = await composer.add_parameter_mapping(
        composition_id="comp_1",
        from_skill_index=0,
        from_param="output",
        to_skill_index=1,
        to_param="input",
    )

    assert success is True
    composition = composer.compositions["comp_1"]
    assert len(composition.parameter_mappings) == 1


@pytest.mark.asyncio
async def test_add_condition(composer_initialized):
    """Test adding execution conditions."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Test",
        skills=["skill_1", "skill_2"],
    )

    success = await composer.add_condition(
        composition_id="comp_1",
        skill_index=1,
        condition_type="if_success",
        condition_value="success",
    )

    assert success is True
    composition = composer.compositions["comp_1"]
    assert 1 in composition.conditions


@pytest.mark.asyncio
async def test_add_error_handler(composer_initialized):
    """Test adding error handlers."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Test",
        skills=["skill_1"],
    )

    success = await composer.add_error_handler(
        composition_id="comp_1",
        skill_id="skill_1",
        handler="retry",
    )

    assert success is True
    composition = composer.compositions["comp_1"]
    assert composition.error_handling["skill_1"] == "retry"


@pytest.mark.asyncio
async def test_execute_sequential_composition(composer_initialized):
    """Test executing sequential composition."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_seq",
        name="Sequential",
        skills=["skill_1", "skill_2", "skill_3"],
        execution_type="sequential",
    )

    result = await composer.execute_composition(
        composition_id="comp_seq",
        initial_context={"input": "test"},
        skill_executor=mock_skill_executor,
    )

    assert result["status"] == "success"
    assert len(result["results"]) == 3
    assert "skill_1" in result["results"]


@pytest.mark.asyncio
async def test_execute_parallel_composition(composer_initialized):
    """Test executing parallel composition."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_par",
        name="Parallel",
        skills=["skill_1", "skill_2"],
        execution_type="parallel",
    )

    result = await composer.execute_composition(
        composition_id="comp_par",
        initial_context={"input": "test"},
        skill_executor=mock_skill_executor,
    )

    assert result["status"] == "success"
    assert result["execution_type"] == "parallel"
    assert len(result["results"]) == 2


@pytest.mark.asyncio
async def test_execute_conditional_composition(composer_initialized):
    """Test executing conditional composition."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_cond",
        name="Conditional",
        skills=["skill_1", "skill_2"],
        execution_type="conditional",
    )

    result = await composer.execute_composition(
        composition_id="comp_cond",
        initial_context={"input": "test"},
        skill_executor=mock_skill_executor,
    )

    assert result["status"] == "success"
    assert result["execution_type"] == "conditional"


@pytest.mark.asyncio
async def test_sequential_with_parameter_mapping(composer_initialized):
    """Test sequential execution with parameter passing."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_params",
        name="With Parameters",
        skills=["skill_1", "skill_2"],
    )

    # Add parameter mapping
    await composer.add_parameter_mapping(
        composition_id="comp_params",
        from_skill_index=0,
        from_param="output",
        to_skill_index=1,
        to_param="input",
    )

    result = await composer.execute_composition(
        composition_id="comp_params",
        initial_context={},
        skill_executor=mock_skill_executor,
    )

    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_execution_history_tracking(composer_initialized):
    """Test execution history is recorded."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Test",
        skills=["skill_1"],
    )

    # Execute twice
    for _ in range(2):
        await composer.execute_composition(
            composition_id="comp_1",
            initial_context={},
            skill_executor=mock_skill_executor,
        )

    history = await composer.get_execution_history()
    assert len(history) == 2


@pytest.mark.asyncio
async def test_execution_history_filtering(composer_initialized):
    """Test filtering execution history."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Comp 1",
        skills=["skill_1"],
    )
    await composer.create_composition(
        composition_id="comp_2",
        name="Comp 2",
        skills=["skill_1"],
    )

    # Execute both
    for comp_id in ["comp_1", "comp_2"]:
        await composer.execute_composition(
            composition_id=comp_id,
            initial_context={},
            skill_executor=mock_skill_executor,
        )

    # Get history for comp_1 only
    history = await composer.get_execution_history(composition_id="comp_1")
    assert len(history) == 1
    assert history[0]["composition_id"] == "comp_1"


@pytest.mark.asyncio
async def test_composition_metrics(composer_initialized):
    """Test composition metrics tracking."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Test",
        skills=["skill_1"],
    )

    # Execute composition
    await composer.execute_composition(
        composition_id="comp_1",
        initial_context={},
        skill_executor=mock_skill_executor,
    )

    metrics = await composer.get_composition_metrics("comp_1")
    assert metrics["executions"] == 1
    assert metrics["successes"] == 1
    assert metrics["failures"] == 0


@pytest.mark.asyncio
async def test_performance_stats(composer_initialized):
    """Test overall performance statistics."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Comp 1",
        skills=["skill_1"],
    )
    await composer.create_composition(
        composition_id="comp_2",
        name="Comp 2",
        skills=["skill_2"],
    )

    # Execute both
    for comp_id in ["comp_1", "comp_2"]:
        await composer.execute_composition(
            composition_id=comp_id,
            initial_context={},
            skill_executor=mock_skill_executor,
        )

    stats = await composer.get_composition_performance_stats()
    assert stats["total_compositions"] == 2
    assert stats["total_executions"] == 2
    assert stats["total_successes"] == 2
    assert stats["success_rate"] == 1.0


@pytest.mark.asyncio
async def test_get_composition(composer_initialized):
    """Test retrieving composition details."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Test Composition",
        skills=["skill_1", "skill_2"],
    )

    comp_data = await composer.get_composition("comp_1")
    assert comp_data is not None
    assert comp_data["name"] == "Test Composition"
    assert comp_data["skills"] == ["skill_1", "skill_2"]


@pytest.mark.asyncio
async def test_list_compositions(composer_initialized):
    """Test listing all compositions."""
    composer = composer_initialized

    # Create multiple compositions
    for i in range(3):
        await composer.create_composition(
            composition_id=f"comp_{i}",
            name=f"Composition {i}",
            skills=[f"skill_{i}"],
        )

    comps = await composer.list_compositions()
    assert len(comps) == 3


@pytest.mark.asyncio
async def test_execution_duration_tracking(composer_initialized):
    """Test that execution duration is tracked."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Test",
        skills=["skill_1"],
    )

    await composer.execute_composition(
        composition_id="comp_1",
        initial_context={},
        skill_executor=mock_skill_executor,
    )

    history = await composer.get_execution_history()
    execution = history[0]
    assert "duration" in execution
    assert execution["duration"] >= 0


@pytest.mark.asyncio
async def test_composition_event_publishing(composer_initialized):
    """Test that composition execution publishes events."""
    composer = composer_initialized

    # Mock event bus
    composer.event_bus = MagicMock()
    composer.event_bus.publish = AsyncMock()

    await composer.create_composition(
        composition_id="comp_1",
        name="Test",
        skills=["skill_1"],
    )

    await composer.execute_composition(
        composition_id="comp_1",
        initial_context={},
        skill_executor=mock_skill_executor,
    )

    # Verify event published
    composer.event_bus.publish.assert_called_once()
    call_args = composer.event_bus.publish.call_args
    assert call_args[0][0] == "composition_executed"


@pytest.mark.asyncio
async def test_health_check(composer_initialized):
    """Test health check."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Test",
        skills=["skill_1"],
    )

    await composer.execute_composition(
        composition_id="comp_1",
        initial_context={},
        skill_executor=mock_skill_executor,
    )

    health = await composer.health_check()
    assert health["compositions_defined"] == 1
    assert health["executions_recorded"] == 1


@pytest.mark.asyncio
async def test_nonexistent_composition(composer_initialized):
    """Test querying nonexistent composition."""
    composer = composer_initialized

    comp = await composer.get_composition("nonexistent")
    assert comp is None


@pytest.mark.asyncio
async def test_execute_nonexistent_composition(composer_initialized):
    """Test executing nonexistent composition."""
    composer = composer_initialized

    result = await composer.execute_composition(
        composition_id="nonexistent",
        initial_context={},
        skill_executor=mock_skill_executor,
    )

    assert result["status"] == "error"
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_composition_without_executor(composer_initialized):
    """Test execution without skill executor."""
    composer = composer_initialized

    await composer.create_composition(
        composition_id="comp_1",
        name="Test",
        skills=["skill_1"],
    )

    result = await composer.execute_composition(
        composition_id="comp_1",
        initial_context={},
        skill_executor=None,
    )

    assert result["status"] == "success"
    # Skills should be marked as skipped


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
