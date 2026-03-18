# socratic-core

Core framework for the Socrates AI ecosystem. Provides foundational components for configuration, events, logging, and exception handling with zero external dependencies.

## Overview

`socratic-core` is the lightweight foundation that powers all Socrates components. It provides:

- **Configuration System**: Type-safe configuration management via `SocratesConfig`
- **Event System**: Thread-safe, async-capable event emitter with 90+ built-in event types
- **Exception Hierarchy**: Structured error handling with 8 exception types
- **Logging Infrastructure**: JSON logging, performance monitoring, and metrics
- **Utilities**: ID generators, datetime helpers, TTL caching

## Installation

### Basic Installation
```bash
pip install socratic-core
```

### With Optional Dependencies
```bash
# For Socrates Nexus (LLM foundation)
pip install socratic-core[nexus]

# For agents support
pip install socratic-core[agents]

# Everything
pip install socratic-core[full]
```

## Quick Start

### Configuration
```python
from socratic_core import SocratesConfig

# Load from environment
config = SocratesConfig.from_env()

# Or build programmatically
config = (
    SocratesConfig()
    .with_api_key("your-key")
    .with_data_dir("/path/to/data")
    .with_model("claude-3-sonnet")
)
```

### Events
```python
from socratic_core import EventEmitter, EventType

emitter = EventEmitter()

# Listen for events
@emitter.on(EventType.PROJECT_CREATED)
def on_project_created(data):
    print(f"Project created: {data}")

# Emit events
emitter.emit(EventType.PROJECT_CREATED, {"project_id": "123"})

# Async support
@emitter.on_async(EventType.CODE_GENERATED)
async def on_code_generated(data):
    await process_code(data)

await emitter.emit_async(EventType.CODE_GENERATED, code_data)
```

### Logging
```python
from socratic_core.logging import initialize_logging, get_logger

# Initialize logging
initialize_logging(
    log_level="INFO",
    log_file="socrates.log",
    json_format=True
)

# Get logger
logger = get_logger(__name__)
logger.info("Application started", extra={"component": "startup"})
```

### Exceptions
```python
from socratic_core import (
    SocratesError,
    ConfigurationError,
    ValidationError,
    DatabaseError,
    AuthenticationError,
    ProjectNotFoundError,
)

try:
    # Some operation
    pass
except ConfigurationError as e:
    print(f"Configuration problem: {e}")
except ValidationError as e:
    print(f"Invalid input: {e}")
except SocratesError as e:
    print(f"Socrates error: {e}")
```

### Utilities
```python
from socratic_core.utils import (
    ProjectIDGenerator,
    UserIDGenerator,
    cached,
)

# Generate IDs
project_id = ProjectIDGenerator.generate()  # proj_xxxxx
user_id = UserIDGenerator.generate()        # user_xxxxx

# Cache with TTL
@cached(ttl=3600)  # Cache for 1 hour
def expensive_operation(param):
    return compute_something(param)
```

## Configuration Reference

### Environment Variables
```bash
# API Configuration
ANTHROPIC_API_KEY=your-api-key
CLAUDE_MODEL=claude-3-sonnet-20240229

# Data Storage
SOCRATES_DATA_DIR=/path/to/socrates/data
SOCRATES_DB_PATH=/path/to/database.db

# Logging
SOCRATES_LOG_LEVEL=INFO
SOCRATES_LOG_FILE=socrates.log
SOCRATES_LOG_JSON=false

# API Server
SOCRATES_API_URL=http://localhost:8000
SOCRATES_API_PORT=8000
```

### SocratesConfig Class
```python
config = SocratesConfig(
    # API Configuration
    api_key: str = "",                              # Anthropic API key
    model: str = "claude-3-sonnet-20240229",        # Claude model version

    # Data Paths
    data_dir: str = "./socrates_data",              # Data directory
    db_path: str = "./socrates_data/socrates.db",   # Database path

    # Logging
    log_level: str = "INFO",                        # Log level
    log_file: str = "socrates.log",                 # Log file path
    enable_json_logging: bool = False,              # JSON formatted logs

    # Service Configuration
    cache_enabled: bool = True,                     # Enable caching
    max_workers: int = 4,                           # Worker threads
)
```

## Event Types

### Lifecycle Events
- `AGENT_START` - Agent started processing
- `AGENT_COMPLETE` - Agent completed task
- `AGENT_ERROR` - Agent encountered error
- `SYSTEM_INITIALIZED` - System fully initialized
- `SYSTEM_SHUTDOWN` - System shutting down

### Project Events
- `PROJECT_CREATED` - New project created
- `PROJECT_SAVED` - Project saved
- `PROJECT_DELETED` - Project deleted
- `PROJECT_LOADED` - Project loaded

### Code Events
- `CODE_GENERATED` - Code generation complete
- `CODE_ANALYSIS_COMPLETE` - Code analysis done
- `CODE_REVIEW_STARTED` - Code review begun
- `CODE_REVIEW_COMPLETE` - Code review finished

### Knowledge Events
- `KNOWLEDGE_LOADED` - Knowledge loaded
- `DOCUMENT_IMPORTED` - Document imported
- `KNOWLEDGE_INDEXED` - Knowledge indexed

### System Events
- `TOKEN_USAGE` - Token usage tracked
- `ERROR_OCCURRED` - Error logged
- `WARNING_ISSUED` - Warning logged

See `socratic_core/events/event_types.py` for the complete list of 90+ event types.

## Exception Hierarchy

```
SocratesError (base)
├── ConfigurationError
├── ValidationError
├── DatabaseError
├── AuthenticationError
├── ProjectNotFoundError
├── UserNotFoundError
├── APIError
└── AgentError
```

## Architecture

```
socratic-core/
├── config/           # Configuration management
├── exceptions/       # Error hierarchy
├── events/           # Event system
├── logging/          # Logging infrastructure
└── utils/            # Utilities (IDs, caching, etc.)
```

## Dependencies

### Core Dependencies
- **pydantic** - Data validation
- **colorama** - Colored terminal output
- **python-dotenv** - Environment variable loading

### Optional Dependencies
- **socrates-nexus** - LLM client foundation
- **socratic-agents** - Agent framework

## Testing

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=socratic_core --cov-report=html
```

## Development

### Local Installation
```bash
git clone https://github.com/themsou/Socrates.git
cd Socrates/socratic-core
pip install -e ".[dev]"
```

### Build for Publishing
```bash
python -m build
twine upload dist/*
```

## Integration with Other Socrates Packages

`socratic-core` is designed to be the foundation for other packages:

```python
# In socratic-rag
from socratic_core import SocratesConfig, EventEmitter, get_logger

# In socratic-agents
from socratic_core import SocratesConfig, EventEmitter, ProjectIDGenerator

# In socrates-cli
from socratic_core import SocratesConfig

# In socrates-api
from socratic_core import SocratesConfig, EventEmitter
```

## Performance Characteristics

- **Import Time**: < 100ms
- **Memory Overhead**: < 2MB
- **Event Emission**: < 1ms per event
- **Configuration Load**: < 50ms

## License

MIT License - see [LICENSE](LICENSE) file for details

## Support

- **Issues**: [GitHub Issues](https://github.com/themsou/Socrates/issues)
- **Documentation**: See [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Migration**: See [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md)

## Contributing

We welcome contributions! Please see the main Socrates repository for contribution guidelines.
