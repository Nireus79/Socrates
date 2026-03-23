# Socrates Integration Layer Guide

## Overview

The integration layer in `socratic_system/orchestration/library_integrations.py` is the bridge between Socrates and its 16 published PyPI libraries. It provides a simple, unified interface to access all libraries through the orchestrator.

## Architecture

```
┌─────────────────────────────────────────┐
│     AgentOrchestrator                   │
│  (orchestrator.py)                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  SocraticLibraryManager                 │
│  (library_integrations.py)              │
│                                         │
│  ├── CoreIntegration                    │
│  ├── NexusIntegration                   │
│  ├── AgentsIntegration                  │
│  ├── RAGIntegration                     │
│  ├── SecurityIntegration                │
│  ├── LearningIntegration                │
│  ├── AnalyzerIntegration                │
│  ├── ConflictIntegration                │
│  ├── KnowledgeIntegration               │
│  ├── WorkflowIntegration                │
│  ├── DocsIntegration                    │
│  ├── PerformanceIntegration             │
│  ├── LangGraphIntegration               │
│  ├── SocraticOpenclawIntegration        │
│  ├── CLIIntegration                     │
│  └── APIIntegration                     │
└─────────────────────────────────────────┘
               │
       ┌───────┼───────┬───────┬───────┐
       ▼       ▼       ▼       ▼       ▼
┌──────────────────────────────────────┐
│  16 Published PyPI Libraries          │
│                                       │
│  Core:  socratic-core                 │
│         socrates-nexus                │
│                                       │
│  Libraries: socratic-rag              │
│            socratic-agents            │
│            socratic-security          │
│            socratic-learning          │
│            ... (10 more)              │
└──────────────────────────────────────┘
```

## How It Works

### 1. Each Integration Class

Each library has a corresponding integration class that:
- **Imports** the library gracefully (try/except)
- **Initializes** the library with proper configuration
- **Wraps** library methods with error handling
- **Returns** sensible defaults if library unavailable

Example:

```python
class LearningIntegration:
    def __init__(self, storage_path: str = "socrates_learning.db"):
        try:
            from socratic_learning import InteractionLogger, SQLiteLearningStore
            self.store = SQLiteLearningStore(storage_path)
            self.logger = InteractionLogger(self.store)
            self.enabled = True
        except ImportError:
            self.enabled = False
```

### 2. The Manager

`SocraticLibraryManager` centralizes all integrations:

```python
manager = SocraticLibraryManager(config)

# All 16 libraries accessible through manager
manager.core.emit_event(...)
manager.nexus.call_llm(...)
manager.rag.search(...)
manager.agents.execute_agent(...)
# ... etc
```

### 3. Graceful Degradation

If a library isn't installed, it doesn't crash the system:

```python
if manager.learning.enabled:
    manager.learning.log_interaction(...)
else:
    logger.debug("Learning not available")
```

## Usage Patterns

### Pattern 1: Direct Library Use

For simple operations, call library methods directly:

```python
from socratic_core import SocratesConfig
from socrates_nexus import LLMClient

config = SocratesConfig()
llm = LLMClient(config=config)
response = llm.call_llm("prompt")
```

### Pattern 2: Through Orchestrator

For integrated workflows, use the orchestrator:

```python
orchestrator = AgentOrchestrator(config)

# All libraries accessible through manager
library_status = orchestrator.library_manager.get_status()

# Use specific libraries
orchestrator.library_manager.nexus.call_llm(...)
orchestrator.library_manager.rag.search(...)
```

### Pattern 3: Check Before Using

Always check if library is enabled:

```python
manager = orchestrator.library_manager

if manager.learning.enabled:
    manager.learning.log_interaction(...)

if manager.performance.enabled:
    stats = manager.performance.get_profile_stats()
```

## Adding a New Library

If you publish a new library:

1. Create an integration class in `library_integrations.py`
2. Follow the same pattern (try/except, enabled flag, error handling)
3. Add it to `SocraticLibraryManager.__init__()`
4. Add status check in `get_status()`

Example template:

```python
class NewLibraryIntegration:
    """Integrate your-new-library"""

    def __init__(self, config: Any = None):
        self.enabled = False
        try:
            from your_new_library import Client
            self.client = Client(config)
            self.enabled = True
            logger.info("New library integration enabled")
        except ImportError:
            logger.warning("your-new-library not available")

    def do_something(self, input_data):
        if not self.enabled:
            return None
        try:
            return self.client.do_something(input_data)
        except Exception as e:
            logger.error(f"Failed: {e}")
            return None
```

## Key Design Principles

### 1. Simplicity Over Features
- Each integration does ONE thing
- No complex orchestration logic
- Pass-through to library methods

### 2. Graceful Degradation
- Missing library? System continues
- Method fails? Return safe default
- Always log errors for debugging

### 3. No Reinvention
- Integrations don't add logic
- They wrap and delegate
- Library owns the implementation

### 4. Backward Compatibility
- Old code using orchestrator still works
- New code can import libraries directly
- Both patterns supported

## Testing the Integration

### Quick Test

```bash
python -c "
from socratic_system.orchestration.library_integrations import SocraticLibraryManager
manager = SocraticLibraryManager({})
status = manager.get_status()
print(f'Enabled: {sum(1 for v in status.values() if v)}/16 libraries')
"
```

### Comprehensive Test

```bash
python VERIFY_FIXES.py
```

## Current Status

✅ **All 16 libraries integrated**
✅ **All 3 configuration fixes applied**
✅ **844 tests passing**
✅ **0 regressions**

## Fixes Applied

1. **SocratesConfig.knowledge_base_path** - Uses `getattr()` with fallback
2. **PerformanceMonitor initialization** - Passes logger argument
3. **RAG metadata document_id** - Removed incompatible parameter

## Troubleshooting

### Library not showing as enabled

Check logs:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
manager = SocraticLibraryManager({})
```

Look for `ImportError` or initialization errors.

### Method returning None

Check if enabled:
```python
if manager.learning.enabled:
    result = manager.learning.log_interaction(...)
else:
    print("Learning library not available")
```

### Performance issues

Use the performance integration:
```python
if manager.performance.enabled:
    manager.performance.start_profiling("operation")
    # ... do something
    manager.performance.stop_profiling("operation")
```

## Philosophy

**This integration layer is not a limitation—it's a feature.**

It allows Socrates to:
- Be a complete modular ecosystem
- Support both simple (single library) and complex (full platform) use cases
- Maintain backward compatibility
- Gracefully handle missing dependencies
- Provide a single unified interface

**Keep it simple. Keep it working. Keep it integrated.**
