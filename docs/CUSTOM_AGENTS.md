# Creating Custom Agents for Socrates

Complete guide to creating, testing, and integrating custom agents in the Socrates system.

---

## Table of Contents

1. [Agent Basics](#agent-basics)
2. [Creating Custom Agents](#creating-custom-agents)
3. [Agent Lifecycle](#agent-lifecycle)
4. [Input/Output Formats](#inputoutput-formats)
5. [Error Handling](#error-handling)
6. [Testing Agents](#testing-agents)
7. [Integration](#integration)
8. [Advanced Patterns](#advanced-patterns)
9. [Performance Optimization](#performance-optimization)
10. [Common Pitfalls](#common-pitfalls)

---

## Agent Basics

### What is an Agent?

An agent in Socrates is a pure, stateless component that:

- ✅ Receives a request dictionary
- ✅ Processes it (often using LLM)
- ✅ Returns a result dictionary
- ✅ Never accesses database directly
- ✅ Reports completion via callbacks
- ✅ Works with or without LLM

### Agent Architecture

```
┌─────────────┐
│   Request   │  {"action": "...", "data": {...}}
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│     Your Custom Agent            │
│  ├─ Initialize (with LLM)       │
│  ├─ Validate input              │
│  ├─ Process request             │
│  └─ Return result               │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────┐
│   Result    │  {"status": "success", "data": {...}}
└─────────────┘
```

### Agent States

```
Initializing
    ↓
Ready (waiting for requests)
    ↓
Processing
    ↓
Complete (success or error)
```

---

## Creating Custom Agents

### Basic Agent Template

```python
# socrates_api/agents/my_custom_agent.py

from typing import Dict, Any, Optional
from socratic_agents import Agent
from socrates_nexus import LLMClient

class MyCustomAgent(Agent):
    """Brief description of what this agent does."""

    def __init__(self, llm_client: Optional[LLMClient]):
        """Initialize agent with LLM client.

        Args:
            llm_client: Optional LLM client (None for stub mode)
        """
        super().__init__(llm_client)
        self.agent_name = "MyCustomAgent"
        self.version = "1.0.0"

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request and return result.

        Args:
            request: Request dictionary with 'action' and parameters

        Returns:
            Result dictionary with 'status' and 'data'

        Raises:
            ValueError: If required fields missing
        """
        try:
            # Validate input
            self._validate_request(request)

            # Get action
            action = request.get("action")

            # Route to handler
            if action == "my_action":
                result = self._handle_my_action(request)
            elif action == "another_action":
                result = self._handle_another_action(request)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}"
                }

            # Return success
            return {
                "status": "success",
                "data": result
            }

        except ValueError as e:
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }

    def _validate_request(self, request: Dict[str, Any]) -> None:
        """Validate request has required fields.

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(request, dict):
            raise ValueError("Request must be a dictionary")

        if "action" not in request:
            raise ValueError("Request must include 'action' field")

    def _handle_my_action(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle 'my_action' request."""
        param = request.get("param", "default")

        # Use LLM if available
        if self.llm_client:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": f"Process {param}"}],
                temperature=0.7,
                max_tokens=500
            )
            result = response
        else:
            # Stub mode
            result = f"Processed {param} (stub mode)"

        return {
            "processed": True,
            "result": result
        }

    def _handle_another_action(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle 'another_action' request."""
        # Implementation
        return {
            "action": "another_action",
            "completed": True
        }
```

### Minimal Agent

```python
# Simplest possible agent

from typing import Dict, Any, Optional
from socratic_agents import Agent
from socrates_nexus import LLMClient

class SimpleAgent(Agent):
    """Minimal agent example."""

    def __init__(self, llm_client: Optional[LLMClient]):
        super().__init__(llm_client)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request."""
        try:
            # Your logic here
            result = f"Processed: {request.get('input')}"
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
```

---

## Agent Lifecycle

### 1. Initialization

```python
# Create agent with LLM
llm = LLMClient(provider="anthropic", api_key="sk-ant-...")
agent = MyCustomAgent(llm_client=llm)

# OR create agent without LLM (stub mode)
agent = MyCustomAgent(llm_client=None)

# Agent is now ready to process requests
```

### 2. Request Processing

```python
# Prepare request
request = {
    "action": "my_action",
    "param": "value",
    "options": {"key": "value"}
}

# Process request
result = agent.process(request)

# Check result
if result["status"] == "success":
    print(f"Success: {result['data']}")
else:
    print(f"Error: {result['message']}")
```

### 3. Event Emission

```python
# Agents can emit events (for integration with learning system)

class EventEmittingAgent(Agent):
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Emit event when starting
        self.emit_event("agent_started", {"agent": self.__class__.__name__})

        try:
            result = self._process_request(request)

            # Emit success event
            self.emit_event("agent_complete", {
                "agent": self.__class__.__name__,
                "success": True
            })

            return {"status": "success", "data": result}

        except Exception as e:
            # Emit error event
            self.emit_event("agent_complete", {
                "agent": self.__class__.__name__,
                "success": False,
                "error": str(e)
            })
            return {"status": "error", "message": str(e)}
```

### 4. Cleanup

```python
# Optional: Implement cleanup if needed

class ResourceAgent(Agent):
    def __init__(self, llm_client):
        super().__init__(llm_client)
        self.resources = []

    def __del__(self):
        """Cleanup resources on deletion."""
        for resource in self.resources:
            resource.close()
```

---

## Input/Output Formats

### Standard Request Format

```python
{
    "action": "action_name",           # Required: action to perform
    "user_id": "user_123",             # Optional: user context
    "project_id": "proj_456",          # Optional: project context
    "language": "python",              # Optional: code language
    "code": "...",                     # Optional: code content
    "prompt": "...",                   # Optional: LLM prompt
    "parameters": {...},               # Optional: action-specific params
    "metadata": {...}                  # Optional: additional data
}
```

### Standard Response Format

```python
# Success Response
{
    "status": "success",
    "data": {
        "result": "...",
        "details": {...}
    },
    "metadata": {
        "execution_time": 1.23,
        "tokens_used": 150,
        "model": "claude-3-sonnet"
    }
}

# Error Response
{
    "status": "error",
    "message": "Description of error",
    "error_code": "ERROR_CODE",
    "metadata": {
        "execution_time": 0.05
    }
}

# Partial Success Response
{
    "status": "partial",
    "data": {...},
    "warnings": ["Warning 1", "Warning 2"],
    "metadata": {...}
}
```

### Type Definitions

```python
from typing import Dict, Any, List, Optional, TypedDict

class AgentRequest(TypedDict, total=False):
    """Type definition for agent request."""
    action: str                    # Required
    user_id: str
    project_id: str
    language: str
    code: str
    prompt: str
    parameters: Dict[str, Any]
    metadata: Dict[str, Any]

class AgentResponse(TypedDict):
    """Type definition for agent response."""
    status: str                    # "success", "error", "partial"
    data: Optional[Dict[str, Any]]
    message: Optional[str]
    metadata: Dict[str, Any]

class AgentResult:
    """Structured result object."""
    def __init__(self, status: str, data: Any = None, message: str = ""):
        self.status = status
        self.data = data
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "data": self.data,
            "message": self.message
        }
```

---

## Error Handling

### Error Categories

```python
from enum import Enum

class ErrorCategory(Enum):
    """Error categories for agents."""
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    LLM_ERROR = "llm_error"
    RESOURCE_ERROR = "resource_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"
```

### Robust Error Handling

```python
class RobustAgent(Agent):
    """Agent with comprehensive error handling."""

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Validate input
            if not self._is_valid_request(request):
                return self._error_response(
                    "Invalid request format",
                    error_code="INVALID_REQUEST"
                )

            # Process
            action = request.get("action")
            result = self._execute_action(action, request)

            # Return success
            return self._success_response(result)

        except ValueError as e:
            # Validation errors
            return self._error_response(
                f"Validation error: {str(e)}",
                error_code="VALIDATION_ERROR"
            )

        except TimeoutError as e:
            # Timeout errors
            return self._error_response(
                "Request timed out",
                error_code="TIMEOUT_ERROR"
            )

        except Exception as e:
            # Unexpected errors
            self._log_error(e)
            return self._error_response(
                "Unexpected error occurred",
                error_code="UNKNOWN_ERROR"
            )

    def _is_valid_request(self, request: Dict[str, Any]) -> bool:
        """Validate request."""
        return isinstance(request, dict) and "action" in request

    def _execute_action(self, action: str, request: Dict[str, Any]) -> Any:
        """Execute action, may raise exceptions."""
        if action == "test":
            return {"test": "result"}
        raise ValueError(f"Unknown action: {action}")

    def _success_response(self, data: Any) -> Dict[str, Any]:
        """Build success response."""
        return {"status": "success", "data": data}

    def _error_response(self, message: str, error_code: str = "") -> Dict[str, Any]:
        """Build error response."""
        return {
            "status": "error",
            "message": message,
            "error_code": error_code
        }

    def _log_error(self, error: Exception) -> None:
        """Log error for debugging."""
        import traceback
        print(f"Agent error: {error}")
        traceback.print_exc()
```

---

## Testing Agents

### Unit Testing

```python
# tests/unit/test_my_custom_agent.py

import pytest
from socrates_api.agents.my_custom_agent import MyCustomAgent

class MockLLMClient:
    """Mock LLM client for testing."""
    def chat(self, messages, **kwargs):
        return "Mock LLM response"

@pytest.fixture
def agent_with_llm():
    """Agent with mock LLM."""
    return MyCustomAgent(llm_client=MockLLMClient())

@pytest.fixture
def agent_without_llm():
    """Agent in stub mode."""
    return MyCustomAgent(llm_client=None)

def test_agent_initializes(agent_with_llm):
    """Test agent initializes correctly."""
    assert agent_with_llm is not None
    assert agent_with_llm.llm_client is not None

def test_success_response(agent_with_llm):
    """Test successful request processing."""
    result = agent_with_llm.process({
        "action": "my_action",
        "param": "test"
    })

    assert result["status"] == "success"
    assert "data" in result

def test_error_response(agent_with_llm):
    """Test error handling."""
    result = agent_with_llm.process({
        "action": "invalid_action"
    })

    assert result["status"] == "error"
    assert "message" in result

def test_missing_action(agent_with_llm):
    """Test missing required action field."""
    result = agent_with_llm.process({})
    assert result["status"] == "error"

def test_stub_mode(agent_without_llm):
    """Test agent works without LLM."""
    result = agent_without_llm.process({
        "action": "my_action",
        "param": "test"
    })

    assert result["status"] == "success"
    assert "data" in result
```

### Integration Testing

```python
# tests/integration/test_agent_integration.py

import pytest
from socrates_api.orchestrator import APIOrchestrator

@pytest.fixture
def orchestrator():
    """Create orchestrator for integration tests."""
    return APIOrchestrator(api_key_or_config="")

def test_agent_registered(orchestrator):
    """Test custom agent is registered."""
    assert "my_custom" in orchestrator.agents

def test_agent_through_orchestrator(orchestrator):
    """Test calling agent through orchestrator."""
    result = orchestrator.execute_agent("my_custom", {
        "action": "my_action",
        "param": "test"
    })

    assert result["status"] == "success"

def test_agent_events(orchestrator):
    """Test agent emits events correctly."""
    events = []

    def capture_events(event_type, event_data):
        events.append((event_type, event_data))

    # Simulate event callback
    result = orchestrator.execute_agent("my_custom", {
        "action": "my_action"
    })

    assert result["status"] == "success"
```

---

## Integration

### 1. Create Agent File

```python
# socrates_api/agents/my_custom_agent.py

from socratic_agents import Agent
from socrates_nexus import LLMClient
from typing import Dict, Any, Optional

class MyCustomAgent(Agent):
    # ... agent implementation ...
```

### 2. Register in Orchestrator

```python
# socrates_api/orchestrator.py

from socrates_api.agents.my_custom_agent import MyCustomAgent

class APIOrchestrator:
    def _initialize_agents(self):
        self.agents = {
            "code_generator": CodeGenerator(llm_client=self.llm_client),
            "code_validator": CodeValidator(llm_client=self.llm_client),
            # ... other agents ...
            "my_custom": MyCustomAgent(llm_client=self.llm_client),  # Add here
        }
```

### 3. Create API Endpoint

```python
# socrates_api/routers/my_custom_router.py

from fastapi import APIRouter, Depends
from socrates_api.orchestrator import get_orchestrator

router = APIRouter(prefix="/api/my-custom", tags=["my-custom"])

@router.post("/action")
async def execute_action(
    request: dict,
    orchestrator = Depends(get_orchestrator)
):
    """Execute custom agent action."""
    result = orchestrator.execute_agent("my_custom", request)
    return result
```

### 4. Include Router in Main App

```python
# socrates_api/main.py

from socrates_api.routers.my_custom_router import router as my_custom_router

app.include_router(my_custom_router)
```

### 5. Use in Frontend

```javascript
// Frontend call to custom agent
const response = await fetch('/api/my-custom/action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        action: 'my_action',
        param: 'value'
    })
});

const result = await response.json();
console.log(result);
```

---

## Advanced Patterns

### Pattern 1: Async Agent

```python
import asyncio
from typing import Dict, Any, Optional

class AsyncAgent(Agent):
    """Agent with async processing."""

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Sync wrapper for async processing."""
        try:
            result = asyncio.run(self.process_async(request))
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def process_async(self, request: Dict[str, Any]) -> Any:
        """Async implementation."""
        # Can use await for async operations
        result = await self._async_operation(request)
        return result

    async def _async_operation(self, request: Dict[str, Any]) -> Any:
        """Perform async operation."""
        await asyncio.sleep(1)  # Simulate async work
        return {"completed": True}
```

### Pattern 2: Streaming Agent

```python
class StreamingAgent(Agent):
    """Agent that returns streamed responses."""

    def process_stream(self, request: Dict[str, Any]):
        """Stream responses instead of returning all at once."""
        if self.llm_client:
            # Use streaming LLM
            stream = self.llm_client.chat_stream(
                messages=[{"role": "user", "content": request.get("prompt")}]
            )

            for chunk in stream:
                yield {
                    "status": "streaming",
                    "chunk": chunk
                }

            yield {
                "status": "complete",
                "message": "Stream finished"
            }
        else:
            # Stub streaming
            yield {
                "status": "streaming",
                "chunk": "Stub response (streaming)"
            }
            yield {"status": "complete"}
```

### Pattern 3: Stateful Agent

```python
class StatefulAgent(Agent):
    """Agent that maintains state across requests."""

    def __init__(self, llm_client):
        super().__init__(llm_client)
        self.state = {}  # Maintain state

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request with state."""
        action = request.get("action")

        if action == "set_state":
            # Store state
            key = request.get("key")
            value = request.get("value")
            self.state[key] = value
            return {"status": "success", "message": "State updated"}

        elif action == "get_state":
            # Retrieve state
            key = request.get("key")
            value = self.state.get(key)
            return {"status": "success", "data": {"value": value}}

        elif action == "clear_state":
            # Clear state
            self.state = {}
            return {"status": "success", "message": "State cleared"}
```

### Pattern 4: Chaining Agent

```python
class ChainingAgent(Agent):
    """Agent that chains other agents."""

    def __init__(self, llm_client, agent_registry: Dict[str, Agent]):
        super().__init__(llm_client)
        self.agent_registry = agent_registry

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Chain multiple agents."""
        agents_to_run = request.get("chain", [])

        results = []
        current_data = request.get("initial_data", {})

        for agent_name in agents_to_run:
            if agent_name not in self.agent_registry:
                return {
                    "status": "error",
                    "message": f"Agent {agent_name} not found"
                }

            agent = self.agent_registry[agent_name]
            result = agent.process(current_data)

            if result["status"] != "success":
                return result

            results.append(result)
            current_data = result.get("data", {})

        return {
            "status": "success",
            "data": {
                "steps": results,
                "final_result": current_data
            }
        }
```

---

## Performance Optimization

### Caching Responses

```python
from functools import lru_cache
from hashlib import md5

class CachingAgent(Agent):
    """Agent with response caching."""

    def __init__(self, llm_client):
        super().__init__(llm_client)
        self.cache = {}
        self.max_cache_size = 100

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process with caching."""
        # Generate cache key
        cache_key = self._get_cache_key(request)

        # Check cache
        if cache_key in self.cache:
            return {
                "status": "success",
                "data": self.cache[cache_key],
                "from_cache": True
            }

        # Process and cache
        result = self._process_impl(request)

        if result["status"] == "success":
            self._add_to_cache(cache_key, result["data"])

        return result

    def _get_cache_key(self, request: Dict[str, Any]) -> str:
        """Generate cache key from request."""
        key_str = str(sorted(request.items()))
        return md5(key_str.encode()).hexdigest()

    def _add_to_cache(self, key: str, value: Any) -> None:
        """Add to cache with size limit."""
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest item
            self.cache.pop(next(iter(self.cache)))

        self.cache[key] = value

    def _process_impl(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Actual implementation."""
        return {"status": "success", "data": {}}
```

### Batch Processing

```python
class BatchAgent(Agent):
    """Agent that processes multiple requests efficiently."""

    def process_batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple requests."""
        results = []

        for request in requests:
            result = self.process(request)
            results.append(result)

        return results

    def process_batch_async(self, requests: List[Dict[str, Any]]):
        """Process multiple requests in parallel."""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.process, req)
                for req in requests
            ]

            results = [f.result() for f in futures]
            return results
```

---

## Common Pitfalls

### ❌ Pitfall 1: Direct Database Access

```python
# Bad - Agent accessing database
class BadAgent(Agent):
    def process(self, request):
        # DON'T DO THIS - breaks reusability
        db.save_result(request)
        return {"status": "success"}

# Good - Use callbacks for persistence
class GoodAgent(Agent):
    def process(self, request):
        result = self._process(request)
        self.emit_event("result_ready", result)
        return {"status": "success", "data": result}
```

### ❌ Pitfall 2: Ignoring Error Cases

```python
# Bad - No error handling
class BadAgent(Agent):
    def process(self, request):
        code = request["code"]  # Will crash if missing
        return {"status": "success", "data": self.llm_client.chat(...)}

# Good - Handle all cases
class GoodAgent(Agent):
    def process(self, request):
        if "code" not in request:
            return {"status": "error", "message": "Missing code"}

        if not self.llm_client:
            return {"status": "success", "data": "stub response"}

        try:
            result = self.llm_client.chat(...)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
```

### ❌ Pitfall 3: Blocking Operations

```python
# Bad - Blocking operations
class BadAgent(Agent):
    def process(self, request):
        time.sleep(5)  # Don't block!
        return {"status": "success"}

# Good - Use async if needed
class GoodAgent(Agent):
    async def process_async(self, request):
        await asyncio.sleep(5)  # Better
        return {"status": "success"}
```

### ❌ Pitfall 4: No Type Hints

```python
# Bad - No types
class BadAgent(Agent):
    def process(self, request):
        return result

# Good - Clear types
class GoodAgent(Agent):
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success"}
```

### ❌ Pitfall 5: Tight Coupling

```python
# Bad - Depends on specific implementation
class BadAgent(Agent):
    def process(self, request):
        # Hard to test - depends on real LLM
        return self.llm_client.chat(...)

# Good - Handle both cases
class GoodAgent(Agent):
    def process(self, request):
        if self.llm_client:
            return self.llm_client.chat(...)
        else:
            return "stub response"
```

---

## Checklist for Custom Agents

Before shipping a custom agent:

- [ ] Inherits from Agent base class
- [ ] Implements `process(request)` method
- [ ] Has type hints on all methods
- [ ] Validates input in process method
- [ ] Returns standardized response format
- [ ] Handles errors gracefully
- [ ] Works with llm_client=None (stub mode)
- [ ] Emits events for learning system
- [ ] Has unit tests with >80% coverage
- [ ] Documented with docstrings
- [ ] Registered in APIOrchestrator
- [ ] Has API endpoint if needed
- [ ] Tested end-to-end in orchestrator

---

**Last Updated**: 2026-03-26
**Version**: 1.0.0
