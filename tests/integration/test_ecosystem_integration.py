"""
Ecosystem Integration Tests - Phase 7

Tests the modularized ecosystem components working together:
- socratic-core (configuration, events, services)
- socratic-agents (agent implementations)
- socrates-maturity (maturity tracking)
- socratic-learning (interaction tracking)

These tests verify the foundation for the complete Socrates system.
"""

import pytest

from socratic_core import (
    BaseService,
    ConfigBuilder,
    EventBus,
    EventEmitter,
    EventType,
    SocratesConfig,
    SocratesError,
    ServiceOrchestrator,
)
from socrates_maturity import MaturityCalculator, PhaseProgressionWorkflow
from socratic_agents import BaseAgent, CodeGenerator, SocraticCounselor


class TestSocratiCoreFoundation:
    """Test socratic-core foundation components."""

    def test_socrates_config_creation(self):
        """Test creating SocratesConfig."""
        config = SocratesConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.data_dir is not None
        assert config.projects_db_path is not None

    def test_config_builder(self):
        """Test ConfigBuilder pattern."""
        config = (
            ConfigBuilder("test-key")
            .with_log_level("DEBUG")
            .with_debug(True)
            .build()
        )
        assert config.api_key == "test-key"
        assert config.log_level == "DEBUG"
        assert config.debug is True

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "api_key": "test-key",
            "log_level": "INFO",
            "debug": False,
        }
        config = SocratesConfig.from_dict(config_dict)
        assert config.api_key == "test-key"
        assert config.log_level == "INFO"
        assert config.debug is False

    def test_event_emitter(self):
        """Test EventEmitter functionality."""
        emitter = EventEmitter()
        events_received = []

        def listener(data):
            events_received.append(data)

        emitter.on("test_event", listener)
        emitter.emit("test_event", {"key": "value"})

        assert len(events_received) == 1
        assert events_received[0] == {"key": "value"}

    def test_event_emitter_once(self):
        """Test EventEmitter one-time listener."""
        emitter = EventEmitter()
        events_received = []

        def listener(data):
            events_received.append(data)

        emitter.once("test_event", listener)
        emitter.emit("test_event", {"first": True})
        emitter.emit("test_event", {"second": True})

        assert len(events_received) == 1

    def test_event_type_enum(self):
        """Test EventType enumeration."""
        assert hasattr(EventType, "SYSTEM_STARTED")
        assert hasattr(EventType, "AGENT_STARTED")
        assert hasattr(EventType, "SKILL_GENERATED")
        assert hasattr(EventType, "MATURITY_UPDATED")


class TestEventBusIntegration:
    """Test EventBus async event system."""

    @pytest.mark.asyncio
    async def test_event_bus_publish_subscribe(self):
        """Test EventBus publish/subscribe pattern."""
        bus = EventBus()
        events_received = []

        async def handler(event):
            events_received.append(event)

        bus.subscribe("test_event", handler)
        await bus.publish("test_event", "test_service", {"data": "test"})

        assert len(events_received) == 1
        assert events_received[0].event_type == "test_event"
        assert events_received[0].data == {"data": "test"}

    @pytest.mark.asyncio
    async def test_event_bus_multiple_subscribers(self):
        """Test EventBus with multiple subscribers."""
        bus = EventBus()
        events1 = []
        events2 = []

        async def handler1(event):
            events1.append(event)

        async def handler2(event):
            events2.append(event)

        bus.subscribe("event1", handler1)
        bus.subscribe("event1", handler2)
        await bus.publish("event1", "service1", {"test": "data"})

        assert len(events1) == 1
        assert len(events2) == 1


class TestMaturityCalculation:
    """Test maturity tracking with ecosystem components."""

    def test_maturity_calculator_basic(self):
        """Test basic maturity calculation."""
        phase_scores = {"discovery": 1.0, "analysis": 0.5}
        overall = MaturityCalculator.calculate_overall_maturity(phase_scores)

        assert overall == 0.75  # Average of 1.0 and 0.5
        assert 0 <= overall <= 1

    def test_phase_estimation(self):
        """Test phase estimation from maturity score."""
        # Low maturity -> discovery
        phase = MaturityCalculator.estimate_current_phase(0.1)
        assert phase == "discovery"

        # Medium-low -> analysis
        phase = MaturityCalculator.estimate_current_phase(0.4)
        assert phase == "analysis"

        # Medium-high -> design
        phase = MaturityCalculator.estimate_current_phase(0.6)
        assert phase == "design"

        # High -> implementation
        phase = MaturityCalculator.estimate_current_phase(0.9)
        assert phase == "implementation"

    def test_weak_category_detection(self):
        """Test identifying weak categories."""
        categories = {
            "code_quality": 0.3,
            "testing": 0.8,
            "documentation": 0.2,
            "architecture": 0.6,
            "performance": 0.9,
        }
        weak = MaturityCalculator.identify_weak_categories(categories, threshold=0.5)

        assert "code_quality" in weak
        assert "documentation" in weak
        assert "testing" not in weak
        assert "performance" not in weak

    def test_phase_progression_workflow(self):
        """Test phase progression workflow."""
        workflow = PhaseProgressionWorkflow()
        assert workflow is not None
        # Verify workflow is initialized properly
        assert hasattr(workflow, "current_phase")


class TestAgentIntegration:
    """Test agent ecosystem integration."""

    def test_base_agent_creation(self):
        """Test creating agent instances."""
        agent = SocraticCounselor()
        assert agent is not None
        assert hasattr(agent, "name") or hasattr(agent, "agent_name")

    def test_code_generator_agent(self):
        """Test CodeGenerator agent availability."""
        agent = CodeGenerator()
        assert agent is not None

    def test_agent_process_method(self):
        """Test agent process method exists."""
        agent = SocraticCounselor()
        assert hasattr(agent, "process") or hasattr(agent, "execute")


class TestCrossComponentIntegration:
    """Test integration across multiple components."""

    def test_config_to_service(self):
        """Test passing config to service."""
        config = SocratesConfig(api_key="test-key")

        # Simulate service initialization
        assert config is not None
        assert config.api_key == "test-key"

    def test_event_emission_on_maturity_change(self):
        """Test event emission on maturity changes."""
        emitter = EventEmitter()
        maturity_events = []

        def on_maturity_update(data):
            maturity_events.append(data)

        emitter.on(EventType.MATURITY_UPDATED, on_maturity_update)
        emitter.emit(EventType.MATURITY_UPDATED, {"phase": "design", "score": 0.65})

        assert len(maturity_events) == 1
        assert maturity_events[0]["phase"] == "design"

    def test_error_handling_integration(self):
        """Test exception handling across components."""
        from socratic_core import AgentError, ConfigurationError

        with pytest.raises(SocratesError):
            raise AgentError("Test agent error")

        with pytest.raises(SocratesError):
            raise ConfigurationError("Test config error")


@pytest.mark.integration
class TestCompleteIntegration:
    """Test complete integration of ecosystem components."""

    def test_ecosystem_imports(self):
        """Verify all ecosystem packages are importable."""
        from socratic_core import SocratesConfig
        from socrates_maturity import MaturityCalculator
        from socratic_agents import BaseAgent

        assert SocratesConfig is not None
        assert MaturityCalculator is not None
        assert BaseAgent is not None

    def test_workflow_with_maturity(self):
        """Test workflow using maturity tracking."""
        config = SocratesConfig(api_key="test-key")
        calculator = MaturityCalculator()

        # Simulate workflow
        phase_scores = {"discovery": 1.0}
        maturity = calculator.calculate_overall_maturity(phase_scores)
        phase = calculator.estimate_current_phase(maturity)

        assert phase == "discovery"
        assert maturity == 1.0

    def test_event_driven_workflow(self):
        """Test event-driven workflow across components."""
        emitter = EventEmitter()
        config = SocratesConfig(api_key="test-key")
        events_log = []

        def log_event(event_data):
            events_log.append(event_data)

        # Subscribe to multiple event types
        emitter.on(EventType.AGENT_STARTED, log_event)
        emitter.on(EventType.SKILL_GENERATED, log_event)
        emitter.on(EventType.MATURITY_UPDATED, log_event)

        # Emit events
        emitter.emit(EventType.AGENT_STARTED, {"agent": "CodeGenerator"})
        emitter.emit(EventType.SKILL_GENERATED, {"skill": "pattern_matching"})
        emitter.emit(EventType.MATURITY_UPDATED, {"phase": "design"})

        assert len(events_log) == 3
