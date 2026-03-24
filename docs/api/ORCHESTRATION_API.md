# Orchestration API Reference

**Version:** 2.0
**Status:** Stable
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [AgentOrchestrator](#agentor chestrator)
2. [OrchestratorService](#orchestratorservice)
3. [ServiceOrchestrator](#serviceorchestrator)
4. [Request/Response Models](#request-response-models)
5. [Examples](#examples)
6. [Best Practices](#best-practices)

---

## AgentOrchestrator

Central coordinator for agent-based processing. Manages agent lifecycle, request routing, and event distribution.

### Constructor

```python
from socratic_system.orchestration import AgentOrchestrator
from socratic_core import SocratesConfig

# Method 1: With API key string (legacy)
orchestrator = AgentOrchestrator("sk-...")

# Method 2: With SocratesConfig (recommended)
config = SocratesConfig(
    api_key="sk-...",
    debug=True,
    log_level="DEBUG"
)
orchestrator = AgentOrchestrator(config)
```

### Methods

#### process_request(request)

Process a request by routing to appropriate agent.

**Signature:**
```python
result = orchestrator.process_request(request: Dict[str, Any]) -> Dict[str, Any]
```

**Parameters:**
```python
request = {
    "agent": "agent_name",           # Required: agent identifier
    "action": "action_name",         # Required: what to do
    "project_id": "proj_123",        # Optional: project context
    "user_id": "user_456",           # Optional: user context
    "parameters": {...},             # Optional: agent-specific params
    "context": {...}                 # Optional: execution context
}
```

**Returns:**
```python
{
    "status": "success" | "error" | "partial",
    "agent": "agent_name",
    "result": {...},                 # Agent-specific result
    "metadata": {
        "duration_ms": 1234,
        "timestamp": "2026-03-24T...",
        "events": [...]
    },
    "error": "error message if status=error"
}
```

**Example:**
```python
result = orchestrator.process_request({
    "agent": "QualityController",
    "action": "analyze",
    "project_id": "proj_123",
    "parameters": {
        "depth": "thorough",
        "include_metrics": True
    }
})

if result["status"] == "success":
    print(f"Quality Score: {result['result']['quality_score']}")
else:
    print(f"Error: {result['error']}")
```

#### on_event(event_type, callback)

Subscribe to an event.

**Signature:**
```python
orchestrator.on_event(
    event_type: EventType,
    callback: Callable[[Dict[str, Any]], None]
) -> None
```

**Example:**
```python
def on_agent_completed(event):
    print(f"Agent {event['agent']} completed in {event['duration_ms']}ms")

orchestrator.on_event(EventType.AGENT_COMPLETED, on_agent_completed)
```

#### emit_event(event_type, data)

Emit an event to subscribers.

**Signature:**
```python
orchestrator.emit_event(
    event_type: EventType,
    data: Dict[str, Any]
) -> None
```

**Example:**
```python
orchestrator.emit_event(EventType.CUSTOM_EVENT, {
    "message": "Custom operation completed",
    "timestamp": datetime.now()
})
```

### Properties

#### config

Access the orchestrator's configuration.

```python
api_key = orchestrator.config.api_key
log_level = orchestrator.config.log_level
debug = orchestrator.config.debug
```

#### database

Access the database layer.

```python
project = orchestrator.database.load_project("proj_123")
user = orchestrator.database.load_user("user_456")
```

#### knowledge_base

Access the knowledge base.

```python
docs = orchestrator.knowledge_base.search("machine learning", top_k=5)
```

#### agents

Access registered agents (read-only).

```python
registered_agents = orchestrator.agents
agent_names = list(registered_agents.keys())
```

---

## OrchestratorService

Singleton service managing user-scoped orchestrator instances.

### Usage

```python
from socratic_system.services import OrchestratorService

# Get orchestrator for a user
orchestrator = OrchestratorService.get_orchestrator("user_123")

# Use orchestrator
result = orchestrator.process_request({...})

# Service automatically manages lifetime
# - Creates on demand
# - Caches for performance
# - Cleans up after TTL
```

### Features

- **Per-User Instances:** One orchestrator per user
- **Automatic Caching:** Reuses instances within TTL
- **Resource Management:** Cleans up expired instances
- **Thread-Safe:** Safe for concurrent access
- **Lazy Initialization:** Creates only when needed

### Methods

#### get_orchestrator(user_id)

Get or create orchestrator for user.

**Signature:**
```python
orchestrator = OrchestratorService.get_orchestrator(
    user_id: str
) -> AgentOrchestrator
```

**Example:**
```python
orchestrator = OrchestratorService.get_orchestrator("user_123")
result = orchestrator.process_request({...})

# Later, for same user
orchestrator2 = OrchestratorService.get_orchestrator("user_123")
# Returns cached instance (same object as orchestrator)
assert orchestrator is orchestrator2
```

#### clear_user(user_id)

Clear orchestrator for a user (force refresh).

**Signature:**
```python
OrchestratorService.clear_user(user_id: str) -> None
```

**Example:**
```python
# Force new orchestrator creation
OrchestratorService.clear_user("user_123")
```

#### clear_all()

Clear all cached orchestrators.

**Signature:**
```python
OrchestratorService.clear_all() -> None
```

---

## ServiceOrchestrator

High-level orchestrator managing multiple services (used internally).

### Architecture

```
ServiceOrchestrator
├── Agent Services
├── Data Services
├── Knowledge Services
└── User Services
```

### Typical Usage

Usually accessed through AgentOrchestrator. Direct usage is advanced.

```python
from socratic_core.orchestrator import ServiceOrchestrator

orchestrator = ServiceOrchestrator(config)

# Initialize all services
await orchestrator.initialize()

# Use services
await orchestrator.process_workflow(...)

# Shutdown
await orchestrator.shutdown()
```

---

## Request/Response Models

### Agent Request

```python
{
    # Required fields
    "agent": "QualityController",           # Agent name
    "action": "analyze",                    # Action to perform

    # Optional context fields
    "project_id": "proj_123",               # Project identifier
    "user_id": "user_456",                  # User identifier
    "session_id": "sess_789",               # Session identifier

    # Agent-specific parameters
    "parameters": {
        "depth": "thorough",                # Analysis depth
        "include_metrics": True,            # Include metrics
        "focus_areas": ["code_quality"]     # Focus areas
    },

    # Execution context
    "context": {
        "project_data": {...},              # Project context
        "user_preferences": {...},          # User preferences
        "previous_results": {...}           # Previous results
    }
}
```

### Agent Response

```python
{
    # Status
    "status": "success",                    # success/error/partial

    # Identification
    "agent": "QualityController",
    "request_id": "req_abc123",
    "timestamp": "2026-03-24T15:30:45Z",

    # Result
    "result": {
        # Agent-specific results
        "quality_score": 8.5,
        "issues": [...],
        "recommendations": [...]
    },

    # Metadata
    "metadata": {
        "duration_ms": 1234,
        "tokens_used": 5000,
        "cached": False,
        "version": "1.0"
    },

    # Error (if status != success)
    "error": "Agent error message",
    "error_code": "AGENT_ERROR_CODE"
}
```

### Event Data

```python
{
    # Event identification
    "event_type": "AGENT_COMPLETED",
    "timestamp": "2026-03-24T15:30:45Z",
    "event_id": "evt_def456",

    # Context
    "agent": "QualityController",
    "project_id": "proj_123",
    "user_id": "user_456",

    # Details (event-specific)
    "status": "success",
    "result": {...},
    "duration_ms": 1234
}
```

---

## Examples

### Basic Agent Processing

```python
from socratic_system.orchestration import AgentOrchestrator
from socratic_core import SocratesConfig

# Create orchestrator
config = SocratesConfig(api_key="sk-...")
orchestrator = AgentOrchestrator(config)

# Process request
result = orchestrator.process_request({
    "agent": "QualityController",
    "action": "analyze",
    "project_id": "proj_123"
})

# Handle result
if result["status"] == "success":
    score = result["result"]["quality_score"]
    print(f"Quality: {score}/10")
else:
    print(f"Error: {result['error']}")
```

### Event-Driven Processing

```python
from socratic_core import EventType

def on_agent_completed(event):
    print(f"Agent: {event['agent']}")
    print(f"Duration: {event['duration_ms']}ms")
    print(f"Status: {event['status']}")

orchestrator.on_event(EventType.AGENT_COMPLETED, on_agent_completed)

# Process request (events will be emitted)
result = orchestrator.process_request({
    "agent": "SkillGenerator",
    "action": "generate",
    "project_id": "proj_123"
})
```

### User-Scoped Orchestration

```python
from socratic_system.services import OrchestratorService

# Get orchestrator for current user
current_user = "user_123"
orchestrator = OrchestratorService.get_orchestrator(current_user)

# Process request (same orchestrator instance for user)
result = orchestrator.process_request({
    "agent": "QualityController",
    "action": "analyze",
    "project_id": "proj_123"
})

# Later, for same user (reuses cached instance)
orchestrator2 = OrchestratorService.get_orchestrator(current_user)
result2 = orchestrator2.process_request({
    "agent": "SkillGenerator",
    "action": "generate",
    "project_id": "proj_456"
})

# Both use same orchestrator
assert orchestrator is orchestrator2
```

### Multi-Agent Workflow

```python
# Sequential agents
orchestrator = OrchestratorService.get_orchestrator(user_id)

# Step 1: Analyze code quality
quality_result = orchestrator.process_request({
    "agent": "QualityController",
    "action": "analyze",
    "project_id": project_id
})

if quality_result["status"] != "success":
    print("Quality analysis failed")
    exit(1)

# Step 2: Generate skills for weak areas
skill_result = orchestrator.process_request({
    "agent": "SkillGenerator",
    "action": "generate",
    "project_id": project_id,
    "parameters": {
        "focus": quality_result["result"]["weak_areas"]
    }
})

# Step 3: Generate code
code_result = orchestrator.process_request({
    "agent": "CodeGenerator",
    "action": "generate",
    "project_id": project_id,
    "parameters": {
        "skills": skill_result["result"]["skills"]
    }
})

print(f"Generated code:\n{code_result['result']['code']}")
```

### Error Handling

```python
from socratic_core import AgentError

try:
    result = orchestrator.process_request({
        "agent": "QualityController",
        "action": "analyze",
        "project_id": project_id
    })

    if result["status"] == "error":
        raise AgentError(result["error"])

    return result["result"]

except AgentError as e:
    print(f"Agent error: {e}")
    # Retry with different parameters
    return retry_with_fallback()
except Exception as e:
    print(f"Unexpected error: {e}")
    raise
```

### Event Monitoring

```python
from socratic_core import EventType

# Track all agent operations
operations = []

def track_operation(event):
    operations.append({
        "agent": event["agent"],
        "duration": event["duration_ms"],
        "status": event["status"]
    })

orchestrator.on_event(EventType.AGENT_STARTED, track_operation)
orchestrator.on_event(EventType.AGENT_COMPLETED, track_operation)
orchestrator.on_event(EventType.AGENT_FAILED, track_operation)

# Process requests
orchestrator.process_request({...})
orchestrator.process_request({...})
orchestrator.process_request({...})

# Analyze operations
total_time = sum(op["duration"] for op in operations)
success_rate = len([op for op in operations if op["status"] == "success"]) / len(operations)

print(f"Total time: {total_time}ms")
print(f"Success rate: {success_rate:.1%}")
```

---

## Best Practices

### 1. Use OrchestratorService for User Sessions

```python
# Good: Per-user orchestrator
orchestrator = OrchestratorService.get_orchestrator(user_id)

# Avoid: Creating new orchestrator per request
orchestrator = AgentOrchestrator(config)  # Wasteful
```

### 2. Handle Errors Appropriately

```python
# Good: Check status and handle errors
result = orchestrator.process_request(...)
if result["status"] == "error":
    handle_error(result["error"])

# Avoid: Ignoring errors
result = orchestrator.process_request(...)
use_result(result["result"])  # May fail if error
```

### 3. Include Relevant Context

```python
# Good: Provide context for agent
result = orchestrator.process_request({
    "agent": "QualityController",
    "action": "analyze",
    "project_id": project_id,
    "user_id": user_id,
    "context": {
        "project_data": project_data,
        "user_preferences": preferences
    }
})

# Avoid: Minimal information
result = orchestrator.process_request({
    "agent": "QualityController",
    "action": "analyze"
})
```

### 4. Monitor Performance

```python
# Good: Track metrics
start = time.time()
result = orchestrator.process_request(...)
duration = (time.time() - start) * 1000

print(f"Duration: {duration}ms")
print(f"Tokens: {result['metadata']['tokens_used']}")

# Use event system
def on_complete(event):
    log_metrics(event["duration_ms"], event["agent"])

orchestrator.on_event(EventType.AGENT_COMPLETED, on_complete)
```

### 5. Structure Complex Workflows

```python
# Good: Workflow function
def analyze_and_generate_skills(project_id, user_id):
    orchestrator = OrchestratorService.get_orchestrator(user_id)

    # Analyze
    quality = orchestrator.process_request({
        "agent": "QualityController",
        "action": "analyze",
        "project_id": project_id
    })

    if quality["status"] != "success":
        return {"status": "error", "phase": "analysis"}

    # Generate skills
    skills = orchestrator.process_request({
        "agent": "SkillGenerator",
        "action": "generate",
        "project_id": project_id,
        "parameters": {
            "focus": quality["result"]["weak_areas"]
        }
    })

    return {
        "status": "success",
        "quality": quality["result"],
        "skills": skills["result"]
    }

# Use workflow
result = analyze_and_generate_skills("proj_123", "user_456")
```

---

## Performance Considerations

### Request Processing

- **Agent selection:** <1ms
- **Agent execution:** 1-10s (depends on agent)
- **Response formatting:** <10ms
- **Total overhead:** <50ms

### Caching

- **Orchestrator caching:** 5-minute default TTL
- **Result caching:** Per-agent (varies)
- **Memory per instance:** 50-100MB

### Scaling

- **Concurrent users:** 100+ (single instance)
- **Agent parallelism:** 10-20 (database limited)
- **Request queue:** Unbounded (consider limits)

---

## Troubleshooting

### Agent Not Found

```python
# Error: Agent 'CustomAgent' not found
# Solution: Check agent name and registration
print(orchestrator.agents.keys())  # List available agents
```

### Memory Issues

```python
# Issue: Memory growing with user sessions
# Solution: Clear inactive sessions
OrchestratorService.clear_user("user_123")
```

### Slow Performance

```python
# Issue: Requests taking too long
# Solution: Check event listeners
for callback in event_callbacks:
    if callback.duration > threshold:
        optimize_callback(callback)
```

---

## API Evolution

### Version History

- **2.0** (Current): Modularized architecture with libraries
- **1.0**: Monolithic orchestrator

### Backward Compatibility

✅ Constructor accepts both string and SocratesConfig
✅ All public methods stable
✅ Event types compatible

---

## Related Documentation

- [Architecture Overview](../ARCHITECTURE.md)
- [socratic-core API](./SOCRATIC_CORE_API.md)
- [Configuration Guide](../guides/CONFIGURATION_GUIDE.md)
- [Agent Development](../guides/ADD_NEW_AGENT.md)
