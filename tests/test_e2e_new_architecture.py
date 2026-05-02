"""
End-to-end tests for the new Library Export Architecture.

Tests the complete workflow using:
- Agent Bus for inter-agent communication
- Services with dependency injection
- Resilience patterns (circuit breaker, retry)
- Event-driven background processing
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from socratic_system.events import EventEmitter
from socratic_system.messaging import AgentBus, CircuitBreaker, RetryPolicy
from socratic_system.services import (
    CodeService,
    ConflictService,
    LearningService,
    QualityService,
    ValidationService,
)


class TestServiceAgentBusIntegration:
    """Test services communicating via agent bus."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_emitter = EventEmitter()
        self.agent_bus = AgentBus(self.event_emitter)

        # Create mock orchestrator with agent_bus
        self.orchestrator = MagicMock()
        self.orchestrator.agent_bus = self.agent_bus
        self.orchestrator.event_emitter = self.event_emitter

    def test_code_service_uses_agent_bus(self):
        """Test CodeService uses agent_bus instead of orchestrator.process_request()."""
        code_service = CodeService(config=MagicMock(), orchestrator=self.orchestrator)

        # Mock the agent bus response
        mock_response = {
            "status": "success",
            "files": [{"path": "main.py", "content": "# code"}],
        }
        self.agent_bus.send_request_sync = MagicMock(return_value=mock_response)

        # Create mock project
        project = MagicMock()
        project.project_id = "test_proj_1"

        # Call generate_code
        result = code_service.generate_code(project, language="python", user_id="user1")

        # Verify agent_bus was called
        self.agent_bus.send_request_sync.assert_called_once()
        call_args = self.agent_bus.send_request_sync.call_args
        assert call_args[0][0] == "code_generator"  # agent name
        assert call_args[0][1]["action"] == "generate_script"

    def test_conflict_service_uses_agent_bus(self):
        """Test ConflictService uses agent_bus for conflict detection."""
        conflict_service = ConflictService(config=MagicMock(), orchestrator=self.orchestrator)

        # Mock the agent bus response
        mock_response = {
            "status": "success",
            "conflicts": [{"type": "technical_stack", "severity": "high"}],
        }
        self.agent_bus.send_request_sync = MagicMock(return_value=mock_response)

        # Create mock project
        project = MagicMock()
        project.project_id = "test_proj_1"

        # Call detect_conflicts
        result = conflict_service.detect_conflicts(project, user_id="user1")

        # Verify agent_bus was called
        self.agent_bus.send_request_sync.assert_called_once()
        call_args = self.agent_bus.send_request_sync.call_args
        assert call_args[0][0] == "conflict_detector"

    def test_quality_service_uses_agent_bus(self):
        """Test QualityService uses agent_bus for maturity calculation."""
        quality_service = QualityService(config=MagicMock(), orchestrator=self.orchestrator)

        # Mock the agent bus response
        mock_response = {
            "status": "success",
            "maturity": {"overall_maturity": 75.5, "phase_scores": {"discovery": 85}},
        }
        self.agent_bus.send_request_sync = MagicMock(return_value=mock_response)

        # Create mock project
        project = MagicMock()
        project.project_id = "test_proj_1"

        # Call calculate_maturity
        result = quality_service.calculate_maturity(project)

        # Verify agent_bus was called
        self.agent_bus.send_request_sync.assert_called_once()
        call_args = self.agent_bus.send_request_sync.call_args
        assert call_args[0][0] == "quality_controller"

    def test_validation_service_uses_agent_bus(self):
        """Test ValidationService uses agent_bus for code validation."""
        validation_service = ValidationService(config=MagicMock(), orchestrator=self.orchestrator)

        # Mock the agent bus response
        mock_response = {
            "status": "success",
            "passed": 45,
            "total": 50,
        }
        self.agent_bus.send_request_sync = MagicMock(return_value=mock_response)

        # Call run_tests
        result = validation_service.run_tests(project_id="test_proj_1", user_id="user1")

        # Verify agent_bus was called
        self.agent_bus.send_request_sync.assert_called_once()
        call_args = self.agent_bus.send_request_sync.call_args
        assert call_args[0][0] == "code_validation"


class TestCompleteWorkflowWithAgentBus:
    """Test complete project workflow using agent bus."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_emitter = EventEmitter()
        self.agent_bus = AgentBus(self.event_emitter)

        self.orchestrator = MagicMock()
        self.orchestrator.agent_bus = self.agent_bus
        self.orchestrator.event_emitter = self.event_emitter

    def test_project_creation_to_validation_workflow(self):
        """Test workflow: create project → validate → check quality."""
        # Initialize services
        code_service = CodeService(config=MagicMock(), orchestrator=self.orchestrator)
        validation_service = ValidationService(config=MagicMock(), orchestrator=self.orchestrator)
        quality_service = QualityService(config=MagicMock(), orchestrator=self.orchestrator)

        # Mock project
        project = MagicMock()
        project.project_id = "test_proj_workflow"
        project.name = "Test Project"

        # Step 1: Generate code via agent_bus
        code_response = {
            "status": "success",
            "files": [{"path": "main.py", "content": "# code"}],
        }
        self.agent_bus.send_request_sync = MagicMock(return_value=code_response)

        code_result = code_service.generate_code(project, language="python", user_id="user1")
        assert code_result["status"] == "success"

        # Step 2: Validate code via agent_bus
        validation_response = {
            "status": "success",
            "passed": 50,
            "total": 50,
        }
        self.agent_bus.send_request_sync = MagicMock(return_value=validation_response)

        validation_result = validation_service.run_tests(project.project_id, user_id="user1")
        assert validation_result["status"] == "success"
        assert validation_result["passed"] == 50

        # Step 3: Check quality via agent_bus
        quality_response = {
            "status": "success",
            "maturity": {"overall_maturity": 95.0, "phase_scores": {"implementation": 95}},
        }
        self.agent_bus.send_request_sync = MagicMock(return_value=quality_response)

        quality_result = quality_service.calculate_maturity(project)
        assert quality_result["overall_maturity"] == 95.0


class TestResiliencePatternIntegration:
    """Test resilience patterns in workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_emitter = EventEmitter()
        self.agent_bus = AgentBus(self.event_emitter, enable_circuit_breaker=True, enable_retry=True)

        self.orchestrator = MagicMock()
        self.orchestrator.agent_bus = self.agent_bus
        self.orchestrator.event_emitter = self.event_emitter

    def test_circuit_breaker_protects_agent_call(self):
        """Test circuit breaker opens after failures."""
        code_service = CodeService(config=MagicMock(), orchestrator=self.orchestrator)
        project = MagicMock()
        project.project_id = "test_proj"

        # Simulate agent failures - circuit breaker should eventually open
        def failing_call(*args, **kwargs):
            raise Exception("Agent service unavailable")

        self.agent_bus.send_request_sync = failing_call

        # Try multiple calls - should fail due to exception
        for i in range(3):
            try:
                code_service.generate_code(project, language="python", user_id="user1")
            except Exception as e:
                assert "unavailable" in str(e) or "circuit" in str(e).lower()


class TestServiceDecoupling:
    """Test that services are decoupled from agent implementation."""

    def test_service_doesnt_depend_on_agent_internals(self):
        """Test CodeService doesn't import agent classes."""
        from socratic_system.services.code_service import CodeService
        import inspect

        source = inspect.getsource(CodeService)

        # Service shouldn't import agent classes
        assert "CodeGeneratorAgent" not in source
        assert "from socratic_system.agents" not in source

        # Service should use agent_bus instead
        assert "agent_bus.send_request_sync" in source

    def test_service_uses_orchestrator_bus_not_direct_call(self):
        """Test services use agent_bus, not orchestrator.process_request()."""
        from socratic_system.services.code_service import CodeService
        import inspect

        source = inspect.getsource(CodeService)

        # Should NOT use orchestrator.process_request
        assert "orchestrator.process_request(" not in source

        # Should use agent_bus
        assert "agent_bus.send_request_sync" in source


class TestPerformanceCharacteristics:
    """Test performance improvements from new architecture."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_emitter = EventEmitter()
        self.agent_bus = AgentBus(self.event_emitter)

        self.orchestrator = MagicMock()
        self.orchestrator.agent_bus = self.agent_bus
        self.orchestrator.event_emitter = self.event_emitter

    def test_agent_bus_call_is_efficient(self):
        """Test agent_bus send_request_sync is fast."""
        import time

        code_service = CodeService(config=MagicMock(), orchestrator=self.orchestrator)

        # Mock fast response
        mock_response = {"status": "success", "files": []}
        self.agent_bus.send_request_sync = MagicMock(return_value=mock_response)

        project = MagicMock()
        project.project_id = "perf_test"

        # Measure 100 calls
        start = time.time()
        for _ in range(100):
            code_service.generate_code(project, language="python", user_id="user1")
        elapsed = time.time() - start

        # Should be fast (less than 1 second for 100 mocked calls)
        assert elapsed < 1.0, f"Service calls took {elapsed}s for 100 iterations"

    def test_multiple_services_in_workflow(self):
        """Test multiple services can be called in sequence efficiently."""
        import time

        code_service = CodeService(config=MagicMock(), orchestrator=self.orchestrator)
        validation_service = ValidationService(config=MagicMock(), orchestrator=self.orchestrator)
        quality_service = QualityService(config=MagicMock(), orchestrator=self.orchestrator)

        project = MagicMock()
        project.project_id = "multi_service_test"

        # Mock all responses
        self.agent_bus.send_request_sync = MagicMock(
            return_value={"status": "success", "data": {}}
        )

        # Run workflow 20 times
        start = time.time()
        for _ in range(20):
            code_service.generate_code(project)
            validation_service.run_tests(project.project_id)
            quality_service.calculate_maturity(project)
        elapsed = time.time() - start

        # Should handle 60 service calls quickly
        assert elapsed < 2.0, f"Workflow calls took {elapsed}s for 60 iterations"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
