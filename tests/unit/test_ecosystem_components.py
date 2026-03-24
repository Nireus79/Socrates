"""
Unit Tests for Ecosystem Components - Phase 7

Tests the modularized ecosystem components working together:
- socratic-core (configuration, events, services)
- socratic-agents (agent implementations)
- socrates-maturity (maturity tracking)

These tests can run without requiring an API server.
"""

import pytest

from socratic_core import (
    ConfigBuilder,
    EventBus,
    EventEmitter,
    EventType,
    SocratesConfig,
    SocratesError,
    AgentError,
    ConfigurationError,
)
from socrates_maturity import MaturityCalculator, PhaseProgressionWorkflow
from socratic_agents import SocraticCounselor, CodeGenerator


class TestSocratiCoreFoundation:
    """Test socratic-core foundation components."""

    def test_socrates_config_creation(self):
        """Test creating SocratesConfig."""
        config = SocratesConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.data_dir is not None
        assert config.projects_db_path is not None
        assert config.to_dict() is not None

    def test_config_builder(self):
        """Test ConfigBuilder pattern."""
        config = (
            ConfigBuilder("test-key")
            .with_log_level("DEBUG")
            .with_debug(True)
            .with_embedding_model("custom-model")
            .build()
        )
        assert config.api_key == "test-key"
        assert config.log_level == "DEBUG"
        assert config.debug is True
        assert config.embedding_model == "custom-model"

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "api_key": "test-key",
            "log_level": "INFO",
            "debug": False,
            "embedding_model": "test-model",
        }
        config = SocratesConfig.from_dict(config_dict)
        assert config.api_key == "test-key"
        assert config.log_level == "INFO"
        assert config.debug is False
        assert config.embedding_model == "test-model"

    def test_event_emitter_basic(self):
        """Test EventEmitter functionality."""
        emitter = EventEmitter()
        events_received = []

        def listener(data):
            events_received.append(data)

        emitter.on("test_event", listener)
        emitter.emit("test_event", {"key": "value"})

        assert len(events_received) == 1
        assert events_received[0] == {"key": "value"}

    def test_event_emitter_multiple_listeners(self):
        """Test EventEmitter with multiple listeners."""
        emitter = EventEmitter()
        events1 = []
        events2 = []

        def listener1(data):
            events1.append(data)

        def listener2(data):
            events2.append(data)

        emitter.on("test_event", listener1)
        emitter.on("test_event", listener2)
        emitter.emit("test_event", {"shared": "data"})

        assert len(events1) == 1
        assert len(events2) == 1

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

    def test_event_emitter_unsubscribe(self):
        """Test EventEmitter unsubscribe."""
        emitter = EventEmitter()
        events_received = []

        def listener(data):
            events_received.append(data)

        emitter.on("test_event", listener)
        emitter.emit("test_event", {"first": True})
        emitter.off("test_event", listener)
        emitter.emit("test_event", {"second": True})

        assert len(events_received) == 1

    def test_event_type_enum(self):
        """Test EventType enumeration."""
        # Verify system events
        assert EventType.SYSTEM_STARTED.value == "system_started"
        assert EventType.SYSTEM_STOPPED.value == "system_stopped"

        # Verify agent events
        assert EventType.AGENT_STARTED.value == "agent_started"
        assert EventType.AGENT_COMPLETED.value == "agent_completed"

        # Verify learning events
        assert EventType.SKILL_GENERATED.value == "skill_generated"
        assert EventType.MATURITY_UPDATED.value == "maturity_updated"


class TestEventBusAsync:
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
        assert events_received[0].source_service == "test_service"

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

    @pytest.mark.asyncio
    async def test_event_bus_different_event_types(self):
        """Test EventBus with different event types."""
        bus = EventBus()
        type1_events = []
        type2_events = []

        async def handler1(event):
            type1_events.append(event)

        async def handler2(event):
            type2_events.append(event)

        bus.subscribe("type1", handler1)
        bus.subscribe("type2", handler2)
        await bus.publish("type1", "service1", {"data": 1})
        await bus.publish("type2", "service1", {"data": 2})

        assert len(type1_events) == 1
        assert len(type2_events) == 1

    @pytest.mark.asyncio
    async def test_event_bus_history(self):
        """Test EventBus event history."""
        bus = EventBus()

        async def dummy_handler(event):
            pass

        bus.subscribe("test_event", dummy_handler)
        await bus.publish("test_event", "service1", {"data": 1})
        await bus.publish("test_event", "service1", {"data": 2})

        history = bus.get_event_history("test_event")
        assert len(history) == 2


class TestMaturityCalculation:
    """Test maturity tracking with ecosystem components."""

    def test_maturity_calculator_basic(self):
        """Test basic maturity calculation."""
        phase_scores = {"discovery": 1.0, "analysis": 0.5}
        overall = MaturityCalculator.calculate_overall_maturity(phase_scores)

        assert overall == 0.75  # Average of 1.0 and 0.5
        assert 0 <= overall <= 1

    def test_maturity_calculator_single_phase(self):
        """Test maturity with single phase."""
        phase_scores = {"discovery": 0.8}
        overall = MaturityCalculator.calculate_overall_maturity(phase_scores)

        assert overall == 0.8

    def test_phase_estimation(self):
        """Test phase estimation from maturity score."""
        # Test boundaries for each phase
        # Boundaries: discovery < 0.25, analysis 0.25-0.5, design 0.5-0.75, implementation >= 0.75
        test_cases = [
            (0.0, "discovery"),
            (0.1, "discovery"),
            (0.24, "discovery"),
            (0.25, "analysis"),
            (0.4, "analysis"),
            (0.49, "analysis"),
            (0.5, "design"),
            (0.65, "design"),
            (0.74, "design"),
            (0.75, "implementation"),
            (0.9, "implementation"),
            (1.0, "implementation"),
        ]

        for score, expected_phase in test_cases:
            phase = MaturityCalculator.estimate_current_phase(score)
            assert phase == expected_phase, f"Score {score} should map to {expected_phase}, got {phase}"

    def test_weak_category_detection(self):
        """Test identifying weak categories."""
        categories = {
            "code_quality": 0.3,
            "testing": 0.8,
            "documentation": 0.2,
            "architecture": 0.6,
            "performance": 0.9,
        }
        weak = MaturityCalculator.identify_weak_categories(categories, weak_threshold=0.5)

        assert "code_quality" in weak
        assert "documentation" in weak
        assert "testing" not in weak
        assert "performance" not in weak
        assert len(weak) == 2

    def test_weak_categories_custom_threshold(self):
        """Test weak categories with custom threshold."""
        categories = {
            "code_quality": 0.3,
            "testing": 0.8,
            "documentation": 0.2,
        }
        # Use threshold of 0.25 - only documentation (0.2) is below threshold
        weak = MaturityCalculator.identify_weak_categories(categories, weak_threshold=0.25)

        assert "documentation" in weak
        assert "code_quality" not in weak
        assert "testing" not in weak

    def test_phase_progression_workflow(self):
        """Test phase progression workflow."""
        workflow = PhaseProgressionWorkflow()
        assert workflow is not None


class TestAgentIntegration:
    """Test agent ecosystem integration."""

    def test_socratic_counselor_creation(self):
        """Test creating SocraticCounselor agent."""
        agent = SocraticCounselor()
        assert agent is not None
        # Check for common agent attributes
        assert hasattr(agent, "name") or hasattr(agent, "agent_name")

    def test_code_generator_creation(self):
        """Test creating CodeGenerator agent."""
        agent = CodeGenerator()
        assert agent is not None

    def test_agents_have_process_method(self):
        """Test that agents have processing capability."""
        agents = [SocraticCounselor(), CodeGenerator()]

        for agent in agents:
            # Check for process or execute method
            has_process = hasattr(agent, "process")
            has_execute = hasattr(agent, "execute")
            assert has_process or has_execute, f"{agent.__class__.__name__} has no process/execute method"


class TestExceptionHandling:
    """Test exception handling across components."""

    def test_socrates_error_base(self):
        """Test SocratesError base exception."""
        with pytest.raises(SocratesError):
            raise SocratesError("Test error")

    def test_agent_error(self):
        """Test AgentError."""
        with pytest.raises(SocratesError):
            raise AgentError("Agent failed")

    def test_configuration_error(self):
        """Test ConfigurationError."""
        with pytest.raises(SocratesError):
            raise ConfigurationError("Invalid config")

    def test_error_inheritance(self):
        """Test exception inheritance chain."""
        assert issubclass(AgentError, SocratesError)
        assert issubclass(ConfigurationError, SocratesError)


class TestCrossComponentIntegration:
    """Test integration across multiple components."""

    def test_config_to_event_integration(self):
        """Test config and event integration."""
        config = SocratesConfig(api_key="test-key")
        emitter = EventEmitter()

        # Simulate config-based event emission
        def on_config_loaded(cfg):
            emitter.emit(EventType.SYSTEM_STARTED, {"api_configured": True})

        events = []

        def capture_event(data):
            events.append(data)

        emitter.on(EventType.SYSTEM_STARTED, capture_event)
        on_config_loaded(config)

        assert len(events) == 1
        assert events[0]["api_configured"] is True

    def test_maturity_event_integration(self):
        """Test maturity calculation with events."""
        emitter = EventEmitter()
        maturity_events = []

        def on_maturity_update(data):
            maturity_events.append(data)

        emitter.on(EventType.MATURITY_UPDATED, on_maturity_update)

        # Simulate maturity calculation (design phase requires 0.5-0.75)
        phase_scores = {"discovery": 1.0, "analysis": 0.3}
        overall = MaturityCalculator.calculate_overall_maturity(phase_scores)
        phase = MaturityCalculator.estimate_current_phase(overall)

        # Emit maturity updated event
        emitter.emit(
            EventType.MATURITY_UPDATED,
            {"phase": phase, "score": overall, "scores": phase_scores},
        )

        assert len(maturity_events) == 1
        assert maturity_events[0]["phase"] == "design"
        assert maturity_events[0]["score"] == 0.65

    def test_skill_generation_workflow(self):
        """Test skill generation integrated with components."""
        config = ConfigBuilder("test-key").with_log_level("DEBUG").build()
        emitter = EventEmitter()
        skill_events = []

        def on_skill_generated(data):
            skill_events.append(data)

        emitter.on(EventType.SKILL_GENERATED, on_skill_generated)

        # Simulate skill generation workflow (using default weak_threshold of 0.6)
        categories = {
            "code_quality": 0.3,
            "testing": 0.8,
            "documentation": 0.2,
        }
        weak = MaturityCalculator.identify_weak_categories(categories, weak_threshold=0.6)

        # Emit skill generated event for weak categories
        for category in weak:
            emitter.emit(
                EventType.SKILL_GENERATED, {"category": category, "agent": "SkillGenerator"}
            )

        assert len(skill_events) == len(weak)
        for i, event in enumerate(skill_events):
            assert event["category"] in weak


@pytest.mark.unit
class TestEcosystemIntegration:
    """Complete ecosystem integration tests."""

    def test_full_config_builder_workflow(self):
        """Test complete config builder workflow."""
        config = (
            ConfigBuilder("test-key")
            .with_log_level("DEBUG")
            .with_debug(True)
            .with_embedding_model("test-model")
            .with_option("custom_option", "value")
            .build()
        )

        assert config.api_key == "test-key"
        assert config.log_level == "DEBUG"
        assert config.debug is True
        assert config.extra["custom_option"] == "value"

    def test_event_driven_ecosystem(self):
        """Test event-driven ecosystem."""
        emitter = EventEmitter()
        log = []

        def log_event(data):
            log.append(data)

        # Subscribe to multiple events
        emitter.on(EventType.SYSTEM_STARTED, log_event)
        emitter.on(EventType.AGENT_STARTED, log_event)
        emitter.on(EventType.SKILL_GENERATED, log_event)

        # Emit system events
        emitter.emit(EventType.SYSTEM_STARTED, {"system": "ready"})
        emitter.emit(EventType.AGENT_STARTED, {"agent": "CodeGenerator"})
        emitter.emit(EventType.SKILL_GENERATED, {"skill": "optimization"})

        assert len(log) == 3
        assert all(isinstance(entry, dict) for entry in log)

    def test_maturity_phase_workflow(self):
        """Test complete maturity and phase workflow."""
        # Start at discovery (maturity < 0.25)
        phase_scores = {"discovery": 0.2}
        maturity = MaturityCalculator.calculate_overall_maturity(phase_scores)
        phase = MaturityCalculator.estimate_current_phase(maturity)

        assert phase == "discovery"

        # Progress to analysis (maturity 0.25-0.5)
        # Average of 0.8 + 0.1 = 0.45
        phase_scores = {"discovery": 0.8, "analysis": 0.1}
        maturity = MaturityCalculator.calculate_overall_maturity(phase_scores)
        phase = MaturityCalculator.estimate_current_phase(maturity)

        assert phase == "analysis"

        # Progress to design (maturity 0.5-0.75)
        # Average of 1.0 + 1.0 + 0.2 = 0.733
        phase_scores = {"discovery": 1.0, "analysis": 1.0, "design": 0.2}
        maturity = MaturityCalculator.calculate_overall_maturity(phase_scores)
        phase = MaturityCalculator.estimate_current_phase(maturity)

        assert phase == "design"
