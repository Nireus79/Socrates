# socratic-core API Reference

**Version:** 0.1.0
**Status:** Stable
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [Configuration](#configuration)
2. [Events](#events)
3. [Exceptions](#exceptions)
4. [Utilities](#utilities)
5. [Examples](#examples)

---

## Configuration

### SocratesConfig

Main configuration class for Socrates system.

#### Constructor

```python
SocratesConfig(
    api_key: str,
    data_dir: Optional[Path] = None,
    projects_db_path: Optional[Path] = None,
    vector_db_path: Optional[Path] = None,
    embedding_model: str = "claude-3-5-sonnet-20241022",
    claude_model: str = "claude-3-5-sonnet-20241022",
    log_level: str = "INFO",
    debug: bool = False,
    **kwargs: Any
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | str | Required | API key for LLM providers |
| `data_dir` | Path | ~/.socrates | Base directory for data |
| `projects_db_path` | Path | ~/.socrates/projects.db | Projects database |
| `vector_db_path` | Path | ~/.socrates/vector_db | Vector storage |
| `embedding_model` | str | claude-3-5-sonnet | Model for embeddings |
| `claude_model` | str | claude-3-5-sonnet | Claude model for LLM |
| `log_level` | str | INFO | Logging level |
| `debug` | bool | False | Enable debug mode |
| `**kwargs` | Any | None | Additional options |

#### Properties

```python
config.api_key              # API key (masked in to_dict())
config.data_dir             # Path to data directory
config.projects_db_path     # Path to projects database
config.vector_db_path       # Path to vector storage
config.embedding_model      # Embedding model name
config.claude_model         # Claude model name
config.log_level            # Current log level
config.debug                # Debug mode flag
config.extra                # Additional configuration
```

#### Methods

##### to_dict()

Convert configuration to dictionary (masks API key).

```python
config_dict = config.to_dict()
# Returns:
# {
#     "api_key": "***",
#     "data_dir": "/home/user/.socrates",
#     "projects_db_path": "/home/user/.socrates/projects.db",
#     "vector_db_path": "/home/user/.socrates/vector_db",
#     "embedding_model": "claude-3-5-sonnet-20241022",
#     "claude_model": "claude-3-5-sonnet-20241022",
#     "log_level": "INFO",
#     "debug": False
# }
```

##### from_dict(data)

Create config from dictionary.

```python
config_dict = {
    "api_key": "sk-...",
    "log_level": "DEBUG",
    "debug": True
}
config = SocratesConfig.from_dict(config_dict)
```

---

### ConfigBuilder

Fluent builder for constructing SocratesConfig.

#### Constructor

```python
ConfigBuilder(api_key: str)
```

#### Methods

All methods return `self` for chaining.

##### with_data_dir(path)

```python
builder.with_data_dir(Path("/custom/data"))
```

##### with_projects_db(path)

```python
builder.with_projects_db(Path("/custom/projects.db"))
```

##### with_vector_db(path)

```python
builder.with_vector_db(Path("/custom/vector_db"))
```

##### with_embedding_model(model)

```python
builder.with_embedding_model("text-embedding-3-large")
```

##### with_claude_model(model)

```python
builder.with_claude_model("claude-opus-4")
```

##### with_log_level(level)

```python
builder.with_log_level("DEBUG")
```

Supported levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

##### with_debug(flag)

```python
builder.with_debug(True)
```

##### with_option(key, value)

```python
builder.with_option("custom_key", "custom_value")
```

##### build()

```python
config = builder.build()
```

#### Example

```python
config = (ConfigBuilder("sk-...")
    .with_debug(True)
    .with_log_level("DEBUG")
    .with_embedding_model("text-embedding-3-large")
    .with_option("timeout", 30)
    .build())
```

---

## Events

### EventEmitter

Synchronous event emitter for local, in-process communication.

#### Constructor

```python
emitter = EventEmitter()
```

#### Methods

##### on(event_type, listener)

Subscribe to an event.

```python
def on_agent_started(data):
    print(f"Agent started: {data}")

emitter.on(EventType.AGENT_STARTED, on_agent_started)
```

##### once(event_type, listener)

Subscribe to an event only once.

```python
emitter.once(EventType.SYSTEM_STARTED, on_system_started)
# Listener will be called only once, then automatically unsubscribed
```

##### off(event_type, listener)

Unsubscribe from an event.

```python
emitter.off(EventType.AGENT_STARTED, on_agent_started)
```

##### emit(event_type, data)

Emit an event.

```python
emitter.emit(EventType.AGENT_COMPLETED, {
    "agent": "QualityController",
    "status": "success"
})
```

---

### EventBus

Asynchronous event bus for distributed communication.

#### Constructor

```python
bus = EventBus()
```

#### Methods

##### subscribe(event_type, handler)

Subscribe to an event (async).

```python
async def on_maturity_updated(event):
    print(f"Maturity: {event.data['score']}")

bus.subscribe(EventType.MATURITY_UPDATED, on_maturity_updated)
```

##### publish(event_type, source_service, data)

Publish an event (async).

```python
await bus.publish(
    EventType.MATURITY_UPDATED,
    "orchestrator",
    {"score": 0.75, "phase": "design"}
)
```

##### get_event_history(event_type)

Retrieve event history.

```python
history = bus.get_event_history(EventType.AGENT_COMPLETED)
# Returns list of events in reverse chronological order
```

---

### EventType

Enumeration of system event types.

#### System Events

```python
EventType.SYSTEM_STARTED          # System initialized
EventType.SYSTEM_INITIALIZED      # Ready to process
EventType.SYSTEM_STOPPED          # Shutdown
EventType.SYSTEM_ERROR            # System error occurred
```

#### Service Events

```python
EventType.SERVICE_INITIALIZED     # Service ready
EventType.SERVICE_STARTED         # Service starting
EventType.SERVICE_STOPPED         # Service stopping
EventType.SERVICE_ERROR           # Service error
```

#### Agent Events

```python
EventType.AGENT_STARTED           # Agent processing started
EventType.AGENT_COMPLETED         # Agent work completed
EventType.AGENT_FAILED            # Agent encountered error
EventType.AGENT_SKILL_UPDATED     # Agent skill changed
```

#### Learning Events

```python
EventType.LEARNING_STARTED        # Learning session started
EventType.LEARNING_COMPLETED      # Learning session ended
EventType.MATURITY_UPDATED        # Project maturity changed
EventType.SKILL_GENERATED         # New skill created
```

#### Workflow Events

```python
EventType.WORKFLOW_STARTED        # Workflow began
EventType.WORKFLOW_COMPLETED      # Workflow finished
EventType.WORKFLOW_FAILED         # Workflow error
```

#### Data Events

```python
EventType.DATA_CREATED            # Data created
EventType.DATA_UPDATED            # Data modified
EventType.DATA_DELETED            # Data removed
```

---

## Exceptions

### SocratesError (Base)

Base exception for all Socrates errors.

```python
try:
    # Some operation
    pass
except SocratesError as e:
    print(f"Error: {e}")
```

### ConfigurationError

Configuration is invalid or incomplete.

```python
raise ConfigurationError("API key not provided")
```

### DatabaseError

Database operation failed.

```python
raise DatabaseError("Failed to save project to database")
```

### ValidationError

Input validation failed.

```python
raise ValidationError("Project name cannot be empty")
```

### AuthenticationError

Authentication failed.

```python
raise AuthenticationError("Invalid API key")
```

### APIError

External API call failed.

```python
raise APIError("LLM API request failed")
```

### AgentError

Agent execution failed.

```python
raise AgentError("QualityController failed to analyze project")
```

### ProjectNotFoundError

Project not found in database.

```python
raise ProjectNotFoundError("Project 'proj_abc' not found")
```

### UserNotFoundError

User not found in database.

```python
raise UserNotFoundError("User 'john' not found")
```

---

## Utilities

### Datetime Serialization

#### serialize_datetime(dt)

Convert datetime to ISO 8601 string.

```python
from datetime import datetime
from socratic_core.utils import serialize_datetime

dt = datetime.now()
iso_string = serialize_datetime(dt)
# Returns: "2026-03-24T15:30:45.123456"
```

#### deserialize_datetime(iso_string)

Convert ISO 8601 string to datetime.

```python
from socratic_core.utils import deserialize_datetime

iso_string = "2026-03-24T15:30:45.123456"
dt = deserialize_datetime(iso_string)
# Returns: datetime(2026, 3, 24, 15, 30, 45, 123456)
```

**Supported Formats:**
- ISO 8601: `2026-03-24T15:30:45.123456`
- Legacy: `2026-03-24 15:30:45.123456`
- With timezone: `2026-03-24T15:30:45+05:00`

---

### ID Generators

#### ProjectIDGenerator

Generate unique project IDs.

```python
from socratic_core.utils import ProjectIDGenerator

# Without owner
project_id = ProjectIDGenerator.generate()
# Returns: "proj_a1b2c3d4"

# With owner
project_id = ProjectIDGenerator.generate("john")
# Returns: "proj_john_a1b2c3d4"
```

**Format:** `proj_{owner}_{uuid[:8]}`

#### UserIDGenerator

Generate unique user IDs.

```python
from socratic_core.utils import UserIDGenerator

user_id = UserIDGenerator.generate()
# Returns: "user_a1b2c3d4"
```

**Format:** `user_{uuid[:8]}`

---

### Caching

#### TTLCache

Time-limited cache with automatic expiration.

```python
from socratic_core.utils import TTLCache

cache = TTLCache(ttl_minutes=5)

# Store value
cache.set("key", "value")

# Retrieve value (returns (found, value))
found, value = cache.get("key")
if found:
    print(value)

# Clear cache
cache.clear()

# Remove expired entries
removed_count = cache.cleanup_expired()
```

#### cached (Decorator)

Decorator for caching function results with TTL.

```python
from socratic_core.utils import cached

@cached(ttl_minutes=5)
def expensive_operation(project_id):
    # This result will be cached for 5 minutes
    return analyze_project(project_id)

# Call the function
result = expensive_operation("proj_123")

# Same arguments - returns cached result
result = expensive_operation("proj_123")

# Different arguments - recalculates
result = expensive_operation("proj_456")

# Get cache statistics
stats = expensive_operation.cache_stats()
# Returns: {
#     "hits": 1,
#     "misses": 2,
#     "total_calls": 3,
#     "hit_rate": "33.3%",
#     "ttl_minutes": 5.0
# }

# Get cache info
info = expensive_operation.cache_info()
# Returns: "Cache: 2 entries, hit rate 33.3%, TTL 5 minutes"

# Clear cache
expensive_operation.cache_clear()
```

**Features:**
- Automatic TTL expiration
- Thread-safe operations
- Graceful handling of unhashable arguments
- Statistics tracking
- Memory-efficient (expired entries cleaned automatically)

---

## Examples

### Basic Setup

```python
from socratic_core import (
    SocratesConfig,
    ConfigBuilder,
    EventEmitter,
    EventType,
    SocratesError
)

# Create configuration
config = ConfigBuilder("sk-...").with_debug(True).build()

# Create event emitter
emitter = EventEmitter()

# Subscribe to events
def on_system_started(data):
    print("System ready!")

emitter.on(EventType.SYSTEM_STARTED, on_system_started)

# Emit event
emitter.emit(EventType.SYSTEM_STARTED, {"status": "ready"})
```

### Configuration Management

```python
from socratic_core import SocratesConfig, ConfigBuilder
from pathlib import Path

# Method 1: Direct instantiation
config = SocratesConfig(
    api_key="sk-...",
    debug=True,
    log_level="DEBUG"
)

# Method 2: Builder pattern
config = (ConfigBuilder("sk-...")
    .with_debug(True)
    .with_log_level("DEBUG")
    .with_embedding_model("text-embedding-3-large")
    .with_data_dir(Path("/opt/socrates/data"))
    .build())

# Method 3: From dictionary
config_dict = {
    "api_key": "sk-...",
    "debug": True,
    "log_level": "DEBUG"
}
config = SocratesConfig.from_dict(config_dict)

# Export configuration
exported = config.to_dict()
```

### Event-Driven Workflow

```python
from socratic_core import EventEmitter, EventType

emitter = EventEmitter()

# Subscribe to multiple events
def on_agent_started(data):
    print(f"Agent {data['agent']} started")

def on_agent_completed(data):
    print(f"Agent {data['agent']} completed: {data['result']}")

emitter.on(EventType.AGENT_STARTED, on_agent_started)
emitter.on(EventType.AGENT_COMPLETED, on_agent_completed)

# Emit events during workflow
emitter.emit(EventType.AGENT_STARTED, {"agent": "QualityController"})
# Process...
emitter.emit(EventType.AGENT_COMPLETED, {
    "agent": "QualityController",
    "result": "Code quality: 8.5/10"
})
```

### Caching Results

```python
from socratic_core.utils import cached
from datetime import datetime

@cached(ttl_minutes=10)
def get_project_maturity(project_id):
    # Expensive operation
    return calculate_maturity(project_id)

# First call - calculates
maturity1 = get_project_maturity("proj_123")

# Second call - cached
maturity2 = get_project_maturity("proj_123")

# Check cache performance
stats = get_project_maturity.cache_stats()
print(f"Hit rate: {stats['hit_rate']}")  # "50.0%"

# After 10 minutes, cache expires and recalculates
```

### Datetime Handling

```python
from socratic_core.utils import serialize_datetime, deserialize_datetime
from datetime import datetime

# Serialize
dt = datetime(2026, 3, 24, 15, 30, 45)
iso_string = serialize_datetime(dt)
print(iso_string)  # "2026-03-24T15:30:45"

# Store in database or send over network
# ...

# Deserialize
restored_dt = deserialize_datetime(iso_string)
print(restored_dt)  # datetime(2026, 3, 24, 15, 30, 45)

# Verify equality
assert dt.date() == restored_dt.date()
```

### Error Handling

```python
from socratic_core import (
    SocratesError,
    ConfigurationError,
    AgentError,
    DatabaseError
)

try:
    # Some operation
    if not api_key:
        raise ConfigurationError("API key required")

    if not project:
        raise DatabaseError("Project not found")

except ConfigurationError as e:
    print(f"Configuration error: {e}")
except AgentError as e:
    print(f"Agent failed: {e}")
except SocratesError as e:
    print(f"Socrates error: {e}")
```

---

## Best Practices

### Configuration

1. **Use ConfigBuilder for clarity**
   ```python
   # Good
   config = ConfigBuilder("key").with_debug(True).build()

   # OK
   config = SocratesConfig("key", debug=True)
   ```

2. **Load from environment**
   ```python
   import os
   config = ConfigBuilder(os.environ["SOCRATES_API_KEY"]).build()
   ```

3. **Validate configuration**
   ```python
   if not config.api_key:
       raise ConfigurationError("API key not configured")
   ```

### Events

1. **Use specific event types**
   ```python
   # Good
   emitter.emit(EventType.AGENT_COMPLETED, data)

   # Avoid
   emitter.emit("agent_completed", data)
   ```

2. **Include relevant data**
   ```python
   emitter.emit(EventType.AGENT_COMPLETED, {
       "agent": "QualityController",
       "project_id": "proj_123",
       "duration_ms": 1234,
       "result": {...}
   })
   ```

3. **Handle exceptions in listeners**
   ```python
   def listener(data):
       try:
           process(data)
       except Exception as e:
           logger.error(f"Listener error: {e}")
   ```

### Caching

1. **Set appropriate TTL**
   ```python
   @cached(ttl_minutes=5)  # Short-lived cache
   def get_user_projects(user_id):
       pass

   @cached(ttl_minutes=60)  # Longer cache
   def get_project_templates():
       pass
   ```

2. **Monitor cache performance**
   ```python
   stats = my_function.cache_stats()
   if float(stats["hit_rate"].strip("%")) < 30:
       # Consider increasing TTL
       pass
   ```

3. **Clear cache when data changes**
   ```python
   def update_project(project_id):
       update_in_db(project_id)
       get_project.cache_clear()  # Invalidate cache
   ```

---

## Migration Guide

### From Version 0.0.x to 0.1.0

**New in 0.1.0:**
- Added `socratic_core.utils` module
- Added `claude_model` to SocratesConfig
- Added `SYSTEM_INITIALIZED` event type

**Breaking Changes:** None

**Migration:**
```python
# Before: No utils module
# After: Import from socratic_core.utils
from socratic_core.utils import serialize_datetime, ProjectIDGenerator

# Before: No claude_model
# After: Add claude_model to config
config = SocratesConfig(
    api_key="...",
    claude_model="claude-3-5-sonnet-20241022"
)
```

---

## API Stability

✅ **Stable APIs** (Backward compatible):
- SocratesConfig
- ConfigBuilder
- EventEmitter
- EventBus
- EventType
- All Exceptions

✅ **Stable Utilities** (Backward compatible):
- serialize_datetime / deserialize_datetime
- ProjectIDGenerator
- UserIDGenerator
- TTLCache
- cached decorator

All APIs follow semantic versioning. Breaking changes only in major versions.

---

## Performance

### Configuration

- Initialization: <100ms
- to_dict(): <1ms
- from_dict(): <1ms

### Events

- emit(): <1ms
- on(): <1ms
- Event processing: Synchronous (no async overhead)

### Utilities

- serialize_datetime(): <1ms
- deserialize_datetime(): <1ms
- ID generation: <1ms
- Cache get(): <0.1ms (memory access)

---

## Support

For issues or questions:
- GitHub: https://github.com/anthropics/socratic-core
- Documentation: https://docs.socratic-ai.dev
- Email: support@socratic-ai.dev
