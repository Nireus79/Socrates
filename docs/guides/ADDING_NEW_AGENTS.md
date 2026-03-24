# Developer Guide: Adding New Agents

**Version:** 1.0
**Status:** Complete
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [Overview](#overview)
2. [Agent Architecture](#agent-architecture)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Implementation Examples](#implementation-examples)
5. [Testing](#testing)
6. [Integration](#integration)
7. [Best Practices](#best-practices)

---

## Overview

This guide explains how to add new agents to the Socrates system. Agents are the core units of work that perform specific tasks within the orchestration system.

### What is an Agent?

An agent is a specialized module that:
- Receives a **request** with specific parameters
- Processes the request using business logic
- Returns a **result** with status and data
- Emits **events** during execution
- Respects **maturity gates** for workflow progression

### When to Create an Agent

Create a new agent when you need to:
- Perform a new type of analysis or transformation
- Support a new domain or specialty
- Add a tool that fits the agent-based architecture
- Enable new workflows in Socrates

---

## Agent Architecture

### Agent Structure

```
MyCustomAgent
├── __init__.py (initialization)
├── core.py (business logic)
├── models.py (request/response schemas)
├── validators.py (input validation)
└── events.py (event definitions)
```

### Agent Interface

All agents must implement this interface:

```python
from socratic_core import EventEmitter, AgentError

class MyAgent(EventEmitter):
    """Custom agent template"""

    def __init__(self):
        super().__init__()
        self.name = "MyAgent"
        self.version = "1.0.0"
        self.supported_actions = ["action_name"]

    def can_handle(self, request: dict) -> bool:
        """Check if agent can handle request"""
        return request.get("agent") == self.name

    def process(self, request: dict) -> dict:
        """Process request and return result"""
        try:
            # Validate request
            self._validate_request(request)

            # Emit started event
            self.emit_event("agent_started", {
                "agent": self.name,
                "action": request["action"]
            })

            # Execute business logic
            result = self._execute(request)

            # Emit completed event
            self.emit_event("agent_completed", {
                "agent": self.name,
                "status": "success",
                "result": result
            })

            return {
                "status": "success",
                "agent": self.name,
                "result": result
            }

        except AgentError as e:
            self.emit_event("agent_failed", {
                "agent": self.name,
                "error": str(e)
            })

            return {
                "status": "error",
                "agent": self.name,
                "error": str(e)
            }

    def _validate_request(self, request: dict):
        """Validate request format and parameters"""
        if "action" not in request:
            raise AgentError("Missing 'action' field")

        if request["action"] not in self.supported_actions:
            raise AgentError(
                f"Unsupported action: {request['action']}"
            )

    def _execute(self, request: dict) -> dict:
        """Execute business logic"""
        action = request["action"]
        parameters = request.get("parameters", {})

        if action == "action_name":
            return self._action_name(parameters)
        else:
            raise AgentError(f"Unknown action: {action}")

    def _action_name(self, parameters: dict) -> dict:
        """Implement specific action"""
        return {"result": "implementation"}
```

---

## Step-by-Step Guide

### Step 1: Define Agent Class

Create the core agent class:

```python
# agents/my_agent/core.py

from socratic_core import EventEmitter, AgentError
from typing import Dict, Any

class MyAnalysisAgent(EventEmitter):
    """Agent that performs custom analysis"""

    def __init__(self):
        super().__init__()
        self.name = "MyAnalysisAgent"
        self.version = "1.0.0"
        self.supported_actions = ["analyze", "report"]

    def can_handle(self, request: dict) -> bool:
        """Check if this agent can handle the request"""
        return request.get("agent") == self.name

    def process(self, request: dict) -> dict:
        """Main entry point for request processing"""
        try:
            self._validate_request(request)
            return self._handle_request(request)
        except AgentError as e:
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "error_code": "AGENT_ERROR"
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.name,
                "error": f"Unexpected error: {str(e)}",
                "error_code": "UNKNOWN_ERROR"
            }

    def _validate_request(self, request: dict):
        """Validate incoming request"""
        required_fields = ["agent", "action"]
        for field in required_fields:
            if field not in request:
                raise AgentError(f"Missing required field: {field}")

        if request["agent"] != self.name:
            raise AgentError(f"Wrong agent: {request['agent']}")

        if request["action"] not in self.supported_actions:
            raise AgentError(f"Unsupported action: {request['action']}")

    def _handle_request(self, request: dict) -> dict:
        """Dispatch to appropriate handler"""
        action = request["action"]
        parameters = request.get("parameters", {})
        project_id = request.get("project_id")

        self.emit_event("agent_started", {
            "agent": self.name,
            "action": action,
            "project_id": project_id
        })

        try:
            if action == "analyze":
                result = self._analyze(project_id, parameters)
            elif action == "report":
                result = self._report(project_id, parameters)
            else:
                raise AgentError(f"Unknown action: {action}")

            self.emit_event("agent_completed", {
                "agent": self.name,
                "action": action,
                "status": "success"
            })

            return {
                "status": "success",
                "agent": self.name,
                "result": result
            }
        except Exception as e:
            self.emit_event("agent_failed", {
                "agent": self.name,
                "action": action,
                "error": str(e)
            })
            raise

    def _analyze(self, project_id: str, parameters: dict) -> dict:
        """Implement analyze action"""
        # Business logic here
        return {
            "project_id": project_id,
            "analysis": "results"
        }

    def _report(self, project_id: str, parameters: dict) -> dict:
        """Implement report action"""
        # Business logic here
        return {
            "project_id": project_id,
            "report": "data"
        }
```

### Step 2: Define Request/Response Models

Create models for type safety:

```python
# agents/my_agent/models.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class AnalyzeRequest:
    """Request for analyze action"""
    project_id: str
    depth: str = "standard"
    include_details: bool = True
    focus_areas: Optional[List[str]] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AnalyzeRequest":
        return AnalyzeRequest(
            project_id=data["project_id"],
            depth=data.get("depth", "standard"),
            include_details=data.get("include_details", True),
            focus_areas=data.get("focus_areas")
        )

@dataclass
class AnalyzeResult:
    """Result of analyze action"""
    project_id: str
    analysis_score: float
    issues: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "analysis_score": self.analysis_score,
            "issues": self.issues,
            "recommendations": self.recommendations
        }
```

### Step 3: Create __init__.py

Export the agent:

```python
# agents/my_agent/__init__.py

from .core import MyAnalysisAgent

__all__ = ["MyAnalysisAgent"]
```

### Step 4: Register the Agent

Register with the orchestrator:

```python
# In your application startup code

from socratic_system.orchestration import AgentOrchestrator
from agents.my_agent import MyAnalysisAgent

def initialize_agents(orchestrator: AgentOrchestrator):
    """Register all agents with orchestrator"""

    # Register custom agent
    my_agent = MyAnalysisAgent()
    orchestrator.register_agent(my_agent)

    # Agent is now available for processing
```

### Step 5: Add Tests

Create comprehensive tests:

```python
# tests/agents/test_my_agent.py

import pytest
from agents.my_agent import MyAnalysisAgent

class TestMyAnalysisAgent:
    @pytest.fixture
    def agent(self):
        return MyAnalysisAgent()

    def test_can_handle(self, agent):
        """Test agent can handle its own requests"""
        request = {"agent": "MyAnalysisAgent", "action": "analyze"}
        assert agent.can_handle(request) is True

    def test_analyze_action(self, agent):
        """Test analyze action"""
        result = agent.process({
            "agent": "MyAnalysisAgent",
            "action": "analyze",
            "project_id": "proj_123"
        })

        assert result["status"] == "success"
        assert result["agent"] == "MyAnalysisAgent"
        assert "analysis" in result["result"]

    def test_missing_required_field(self, agent):
        """Test validation of missing fields"""
        result = agent.process({
            "agent": "MyAnalysisAgent"
            # Missing "action" field
        })

        assert result["status"] == "error"
        assert "Missing required field" in result["error"]

    def test_unsupported_action(self, agent):
        """Test handling of unsupported actions"""
        result = agent.process({
            "agent": "MyAnalysisAgent",
            "action": "unsupported_action"
        })

        assert result["status"] == "error"
        assert "Unsupported action" in result["error"]

    def test_event_emission(self, agent):
        """Test events are emitted"""
        events = []

        agent.on_event("agent_started", lambda e: events.append(("started", e)))
        agent.on_event("agent_completed", lambda e: events.append(("completed", e)))

        agent.process({
            "agent": "MyAnalysisAgent",
            "action": "analyze",
            "project_id": "proj_123"
        })

        assert len(events) == 2
        assert events[0][0] == "started"
        assert events[1][0] == "completed"
```

---

## Implementation Examples

### Example 1: Simple Transformation Agent

```python
"""Agent that transforms data"""

from socratic_core import EventEmitter, AgentError

class DataTransformerAgent(EventEmitter):
    def __init__(self):
        super().__init__()
        self.name = "DataTransformer"
        self.version = "1.0.0"
        self.supported_actions = ["transform", "validate"]

    def can_handle(self, request: dict) -> bool:
        return request.get("agent") == self.name

    def process(self, request: dict) -> dict:
        try:
            if "data" not in request:
                raise AgentError("Missing 'data' field")

            action = request["action"]

            if action == "transform":
                result = self._transform(request["data"])
            elif action == "validate":
                result = self._validate(request["data"])
            else:
                raise AgentError(f"Unknown action: {action}")

            return {"status": "success", "result": result}

        except AgentError as e:
            return {"status": "error", "error": str(e)}

    def _transform(self, data: dict) -> dict:
        """Transform data"""
        return {
            "original": data,
            "transformed": {k.upper(): v for k, v in data.items()}
        }

    def _validate(self, data: dict) -> dict:
        """Validate data"""
        return {
            "valid": all(v is not None for v in data.values()),
            "fields": len(data),
            "errors": [] if all(v is not None for v in data.values()) else ["Some fields are None"]
        }
```

### Example 2: Analysis Agent with Maturity Gate

```python
"""Agent that respects maturity gates"""

from socratic_core import EventEmitter, AgentError
from socrates_maturity import MaturityCalculator

class MaturityAwareAnalyzer(EventEmitter):
    def __init__(self):
        super().__init__()
        self.name = "MaturityAwareAnalyzer"
        self.version = "1.0.0"
        self.supported_actions = ["analyze"]
        self.required_phase = "analysis"  # Requires analysis phase

    def can_handle(self, request: dict) -> bool:
        return request.get("agent") == self.name

    def process(self, request: dict) -> dict:
        try:
            # Check maturity gate
            project = request.get("project")
            if project:
                current_phase = MaturityCalculator.estimate_current_phase(
                    project.overall_maturity
                )

                if current_phase != self.required_phase:
                    return {
                        "status": "skipped",
                        "reason": f"Agent requires {self.required_phase} phase, current is {current_phase}"
                    }

            # Proceed with analysis
            result = self._analyze(request)
            return {"status": "success", "result": result}

        except AgentError as e:
            return {"status": "error", "error": str(e)}

    def _analyze(self, request: dict) -> dict:
        """Perform analysis"""
        return {
            "analysis_complete": True,
            "score": 0.85
        }
```

---

## Testing

### Unit Test Template

```python
import pytest
from agents.my_agent import MyAnalysisAgent

class TestMyAnalysisAgent:
    @pytest.fixture
    def agent(self):
        return MyAnalysisAgent()

    @pytest.fixture
    def valid_request(self):
        return {
            "agent": "MyAnalysisAgent",
            "action": "analyze",
            "project_id": "proj_123",
            "parameters": {
                "depth": "thorough"
            }
        }

    def test_agent_name(self, agent):
        assert agent.name == "MyAnalysisAgent"

    def test_supported_actions(self, agent):
        assert "analyze" in agent.supported_actions
        assert "report" in agent.supported_actions

    def test_can_handle_own_requests(self, agent):
        request = {"agent": "MyAnalysisAgent", "action": "analyze"}
        assert agent.can_handle(request) is True

    def test_cannot_handle_other_agents(self, agent):
        request = {"agent": "OtherAgent", "action": "analyze"}
        assert agent.can_handle(request) is False

    def test_successful_analysis(self, agent, valid_request):
        result = agent.process(valid_request)
        assert result["status"] == "success"
        assert result["agent"] == "MyAnalysisAgent"
        assert "result" in result

    def test_error_on_invalid_request(self, agent):
        invalid_request = {
            "agent": "MyAnalysisAgent"
            # Missing action
        }
        result = agent.process(invalid_request)
        assert result["status"] == "error"

    def test_events_fired(self, agent, valid_request):
        events = []
        agent.on_event("agent_started", lambda e: events.append(e))
        agent.on_event("agent_completed", lambda e: events.append(e))

        agent.process(valid_request)

        assert len(events) >= 2
```

---

## Integration

### Register Agent with Orchestrator

```python
from socratic_system.orchestration import AgentOrchestrator
from agents.my_agent import MyAnalysisAgent

# Create orchestrator
orchestrator = AgentOrchestrator(config)

# Create and register agent
my_agent = MyAnalysisAgent()
orchestrator.register_agent(my_agent)

# Now can use agent
result = orchestrator.process_request({
    "agent": "MyAnalysisAgent",
    "action": "analyze",
    "project_id": "proj_123"
})
```

### Listen to Agent Events

```python
from socratic_core import EventType

def on_agent_started(event):
    print(f"Agent {event['agent']} started")

def on_agent_completed(event):
    print(f"Agent {event['agent']} completed in {event.get('duration_ms')}ms")

orchestrator.on_event(EventType.AGENT_STARTED, on_agent_started)
orchestrator.on_event(EventType.AGENT_COMPLETED, on_agent_completed)

# Process request (events will be emitted)
result = orchestrator.process_request({...})
```

---

## Best Practices

### 1. Comprehensive Validation

```python
# Good: Validate all inputs
def _validate_request(self, request: dict):
    if "action" not in request:
        raise AgentError("Missing 'action'")

    if request["action"] not in self.supported_actions:
        raise AgentError(f"Unsupported action: {request['action']}")

    if "parameters" in request:
        params = request["parameters"]
        if "required_param" not in params:
            raise AgentError("Missing required parameter")

# Avoid: Assuming inputs are valid
def _handle_request(self, request: dict):
    action = request["action"]  # May fail
    params = request["parameters"]["required_param"]  # May fail
```

### 2. Clear Error Messages

```python
# Good: Specific, actionable error messages
raise AgentError(
    "Invalid code_quality score: 1.5. "
    "Must be between 0.0 and 1.0"
)

# Avoid: Generic error messages
raise AgentError("Invalid parameter")
```

### 3. Emit Meaningful Events

```python
# Good: Include context in events
self.emit_event("agent_started", {
    "agent": self.name,
    "action": action,
    "project_id": project_id,
    "parameters": parameters
})

# Avoid: Minimal event data
self.emit_event("started", {})
```

### 4. Return Consistent Response Format

```python
# Good: Consistent structure
return {
    "status": "success" | "error" | "partial",
    "agent": self.name,
    "result": {...},
    "error": "error message if status != success",
    "metadata": {
        "duration_ms": 1234,
        "timestamp": "2026-03-24T...",
        "version": "1.0"
    }
}

# Avoid: Inconsistent formats
return {"success": True, "data": {...}}
return {"error": "failed"}
```

### 5. Make Agents Testable

```python
# Good: Separate business logic from request handling
def process(self, request: dict) -> dict:
    result = self._analyze(request["parameters"])
    return {"status": "success", "result": result}

def _analyze(self, params: dict) -> dict:
    # Pure function, easy to test
    return params

# Avoid: Mixing concerns
def process(self, request: dict) -> dict:
    # Hard to test without full request context
    return self._do_everything(request)
```

---

## Checklist for New Agents

- [ ] Agent class implements `can_handle()` and `process()`
- [ ] Request validation in `_validate_request()`
- [ ] Error handling with `AgentError`
- [ ] Events emitted for lifecycle (started, completed, failed)
- [ ] Response format consistent
- [ ] Unit tests cover happy path
- [ ] Unit tests cover error cases
- [ ] Unit tests cover validation
- [ ] Documentation with examples
- [ ] Registered with orchestrator
- [ ] Tested end-to-end with orchestrator

---

## Related Documentation

- [Orchestration API](./ORCHESTRATION_API.md)
- [Common Integration Patterns](./COMMON_INTEGRATION_PATTERNS.md)
- [Common Recipes](./COMMON_RECIPES.md)

