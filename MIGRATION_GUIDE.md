# Migration Guide: Monolithic to Modular Architecture

## Overview

Socrates has been refactored from a monolithic structure to a modular, composable architecture. This guide helps you understand the changes and migrate your code.

## Key Changes

### Before (Monolithic)
```
socratic_system/
├── config.py           # Configuration
├── exceptions.py       # Exceptions
├── events.py          # Events
├── logging_config.py  # Logging
├── agents/            # All agents
├── models/            # All models
├── database/          # Database layer
└── ui/                # UI/CLI
```

### After (Modular)
```
socratic-core/                 # New framework library
├── config.py
├── exceptions.py
├── events.py
└── logging/

socratic-rag/                  # Separate library
socratic-agents/               # Separate library
socratic-analyzer/             # Separate library
socratic-knowledge/            # Separate library

socrates-cli/                  # CLI interface
socrates-api/                  # API server

socratic_system/               # Main platform (orchestrator)
```

## Import Changes

### Configuration

**Old:**
```python
from socratic_system.config import SocratesConfig, ConfigBuilder
```

**New:**
```python
from socratic_core import SocratesConfig, ConfigBuilder
```

> Note: `socratic_system` still re-exports these for backward compatibility

### Exceptions

**Old:**
```python
from socratic_system.exceptions import SocratesError, APIError
```

**New:**
```python
from socratic_core import SocratesError, APIError
```

### Events

**Old:**
```python
from socratic_system.events import EventEmitter, EventType
```

**New:**
```python
from socratic_core import EventEmitter, EventType
```

### Logging

**Old:**
```python
from socratic_system.logging_config import LoggingConfig
```

**New:**
```python
from socratic_core import LoggingConfig
```

### Learning Models

**Old:**
```python
from socratic_system.models.learning import QuestionEffectiveness
```

**New:**
```python
from modules.foundation.models.learning import QuestionEffectiveness
```

## Dependency Installation

### Option 1: Full Installation (All Features)
```bash
pip install socrates-ai
```
Installs: socratic-core, socratic-rag, socratic-agents, socratic-analyzer, socratic-knowledge, socratic-learning, socratic-workflow, socratic-conflict, and everything else.

### Option 2: Modular Installation

**Just Core Framework:**
```bash
pip install socratic-core
```

**Core + CLI:**
```bash
pip install socratic-core socrates-cli
```

**Core + API:**
```bash
pip install socratic-core socrates-api
```

**Core + Specific Libraries:**
```bash
pip install socratic-core socratic-rag socratic-agents
```

**Core with Optional Features:**
```bash
pip install socratic-core[nexus,agents,full]
```

## Usage Patterns

### Old Pattern: Direct Orchestrator

```python
from socratic_system import create_orchestrator, SocratesConfig

config = SocratesConfig.from_env()
orchestrator = create_orchestrator(config)
result = orchestrator.process_request('project_manager', {...})
```

### New Pattern: API-Based (Recommended for CLI/External)

```python
import httpx
from socratic_core import SocratesConfig

config = SocratesConfig.from_env()
api_url = "http://localhost:8000"

async with httpx.AsyncClient(base_url=api_url) as client:
    response = await client.post("/projects", json={...})
    result = response.json()
```

### Still Supported: Direct Orchestrator

```python
from socratic_system import create_orchestrator, SocratesConfig

# This still works - backward compatibility maintained
config = SocratesConfig.from_env()
orchestrator = create_orchestrator(config)
```

## Architecture Upgrade Path

### Phase 1: No Changes Required
Your existing code continues to work. `socratic_system` re-exports all components.

```python
# Old imports still work
from socratic_system import SocratesConfig, EventType, SocratesError
```

### Phase 2: Update Imports (Optional)
Move to the new import locations over time:

```python
# New imports
from socratic_core import SocratesConfig, EventType, SocratesError
```

### Phase 3: Use New Interfaces
Adopt new CLI and API interfaces:

```bash
# Instead of direct Python imports, use CLI
socrates project create --name "My Project" --owner "me"

# Or use API
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "owner": "me"}'
```

## Configuration Changes

### Environment Variables (No Changes)
All existing environment variables still work:
- `ANTHROPIC_API_KEY`
- `SOCRATES_DATA_DIR`
- `CLAUDE_MODEL`
- `SOCRATES_LOG_LEVEL`
- `SOCRATES_LOG_FILE`

### New Environment Variables

**For API:**
```bash
SOCRATES_API_URL=http://localhost:8000
SOCRATES_API_PORT=8000
```

**For CLI:**
```bash
SOCRATES_API_URL=http://localhost:8000  # API to connect to
```

## Database Changes

### No Changes
The database schema remains the same. Your existing SQLite databases are compatible.

### Migration Path
1. No migration needed for existing databases
2. New installations use the same schema
3. All models work with both old and new code

## Event System Changes

### No API Changes
The event system API is identical:

```python
# Old code still works
orchestrator.event_emitter.on(EventType.PROJECT_CREATED, callback)
orchestrator.event_emitter.emit(EventType.CODE_GENERATED, data)

# New async support available
await orchestrator.event_emitter.emit_async(EventType.PROJECT_CREATED, data)
```

## Testing Changes

### Old Test Pattern
```python
def test_project_creation():
    config = SocratesConfig(api_key="test")
    orchestrator = create_orchestrator(config)
    result = orchestrator.process_request('project_manager', {...})
    assert result['status'] == 'success'
```

### New Test Pattern (API)
```python
import httpx
import pytest

@pytest.mark.asyncio
async def test_project_creation():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post("/projects", json={...})
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'success'
```

## Troubleshooting

### Import Error: No module 'socratic_core'

**Solution:**
```bash
pip install socratic-core
```

Or install full package:
```bash
pip install socrates-ai
```

### API Connection Error: "Connection refused"

**Solution:** Make sure the API server is running:
```bash
socrates-api
```

Or set the correct API URL:
```bash
export SOCRATES_API_URL=http://your-server:8000
```

### Old Imports Still Work but Show Warnings

**Note:** This is normal and intentional. Old imports are still supported for backward compatibility. You can migrate at your own pace.

## CLI Changes

### Old Usage (If Using Direct Python)
```python
from socratic_system import create_orchestrator

config = SocratesConfig.from_env()
orchestrator = create_orchestrator(config)
# Use programmatically
```

### New Usage (Recommended)
```bash
# Start API server
socrates-api &

# Use CLI commands
socrates project create --name "My Project" --owner "me"
socrates project list
socrates code generate --project-id "proj_xyz"
```

## API Changes

### REST Endpoints Now Available
```bash
# Projects
POST   /projects              # Create project
GET    /projects              # List projects
GET    /projects/{id}         # Get project
PUT    /projects/{id}         # Update project
DELETE /projects/{id}         # Delete project

# Code
POST   /projects/{id}/code/generate  # Generate code
GET    /projects/{id}/code           # Get generated code

# System
GET    /health                # Health check
GET    /info                  # System info
GET    /metrics               # Prometheus metrics
```

## Performance Considerations

### API-Based Approach
- ✅ Better for distributed systems
- ✅ Reduced memory per process
- ⚠️ Network latency between CLI and API

### Direct Orchestrator
- ✅ Lower latency
- ✅ No network overhead
- ⚠️ Higher memory usage

Choose based on your deployment model.

## Backward Compatibility

### What Still Works
- All `socratic_system` imports (via re-exports)
- All existing code using `create_orchestrator()`
- All database schemas
- All configuration options
- All events and logging

### What Changed
- Internal structure (you shouldn't access this)
- Learning models location (use new import path)
- CLI/API are now separate (but compatible)

## Support Matrix

| Component | Old Import | New Import | Status |
|-----------|-----------|-----------|--------|
| SocratesConfig | socratic_system | socratic_core | ✅ Both work |
| ConfigBuilder | socratic_system | socratic_core | ✅ Both work |
| EventEmitter | socratic_system | socratic_core | ✅ Both work |
| EventType | socratic_system | socratic_core | ✅ Both work |
| SocratesError | socratic_system | socratic_core | ✅ Both work |
| LoggingConfig | socratic_system | socratic_core | ✅ Both work |
| QuestionEffectiveness | socratic_system.models.learning | modules.foundation.models.learning | ⚠️ New location |
| Agents | socratic_system.agents | socratic-agents | ✅ Both work |
| RAG | socratic_system | socratic-rag | ✅ Both work |

## Timeline

- **Now**: Both old and new imports work (backward compatible)
- **v2.0** (future): Old imports may be deprecated with warnings
- **v3.0** (future): Old imports removed

Take your time migrating - backward compatibility is maintained.

## Getting Help

- **Documentation**: See `ARCHITECTURE.md` for full system overview
- **CLI Help**: `socrates --help`
- **API Docs**: `http://localhost:8000/docs` (when server running)
- **Issues**: https://github.com/themsou/Socrates/issues
