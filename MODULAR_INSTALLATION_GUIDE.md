# Socrates Modular Installation Guide

## Overview

Socrates has been transformed from a monolith into a **modular ecosystem** where each library can be installed independently. This guide explains the new dependency structure and installation options.

## Architecture

```
┌─────────────────────────────────────────┐
│         Your Application                 │
│    (LangGraph, Openclaw, custom, etc.)   │
└──────────────────┬──────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│socratic- │ │socratic- │ │socratic- │
│  rag     │ │ agents   │ │analyzer  │
└──────────┘ └──────────┘ └──────────┘
    │              │              │
    └──────────────┼──────────────┘
                   │
         ┌─────────▼──────────┐
         │  socratic-core     │
         │  • Config          │
         │  • Events          │
         │  • Exceptions      │
         │  • Logging         │
         │  • Utilities       │
         └────────────────────┘
                   │
                   ▼
      ┌──────────────────────────┐
      │  socrates-nexus (LLM)    │
      │  (Optional, for Claude)  │
      └──────────────────────────┘
```

## Installation Options

### 1. **Core Framework Only** (Minimal)
```bash
pip install socratic-core
```
- **Size**: ~5 MB
- **Dependencies**: 3 (pydantic, colorama, python-dotenv)
- **Use case**: Building custom orchestrators, integrating with external frameworks

### 2. **CLI Tool**
```bash
pip install socratic-cli
```
- **Depends on**: socratic-core
- **Size**: ~10 MB
- **Use case**: Command-line interface for Socrates

### 3. **API Server**
```bash
pip install socratic-api
```
- **Depends on**: socratic-core, socrates-ai (main orchestrator)
- **Size**: ~50 MB
- **Use case**: REST API server

### 4. **Full Platform**
```bash
pip install socrates-ai[full]
```
- **Includes**: socratic-core + all libraries (rag, agents, analyzer, conflict, knowledge, learning, workflow, nexus)
- **Size**: ~200 MB
- **Use case**: Complete development environment

### 5. **Modular Installation** (Pick what you need)
```bash
# Core + RAG
pip install socratic-core socratic-rag

# Core + Agents
pip install socratic-core socratic-agents

# Core + RAG + Agents
pip install socratic-core socratic-rag socratic-agents

# Core + Multiple
pip install socratic-core socratic-rag socratic-agents socratic-analyzer
```

### 6. **Custom Bundle** (from pyproject.toml)
```bash
# Using main Socrates installation
pip install "socrates-ai[core]"           # Core only
pip install "socrates-ai[rag]"            # Core + RAG
pip install "socrates-ai[agents]"         # Core + Agents
pip install "socrates-ai[full]"           # Everything
```

## Development Installation

Install for local development:

```bash
# Install all packages in editable mode
pip install -e socratic-core
pip install -e socrates-cli
pip install -e socrates-api
pip install -e .              # Main Socrates orchestrator

# Install dev dependencies
pip install -e ".[dev]"
```

## Dependency Resolution

### Main Socrates (`socrates-ai`)
- **Required**: None (all libraries optional)
- **Optional**: socratic-core, socratic-rag, socratic-agents, etc.
- **Use case**: Orchestrator that coordinates all libraries

### socrates-cli
- **Required**: socratic-core, httpx, colorama, click
- **Optional**: socrates-ai (for standalone mode)
- **Size**: ~10 MB minimal install

### socrates-api
- **Required**: socratic-core, socrates-ai, fastapi, uvicorn
- **Optional**: socratic-analyzer, socratic-knowledge
- **Size**: ~50 MB

### socratic-core
- **Required**: pydantic, colorama, python-dotenv (3 deps!)
- **Optional**: socrates-nexus (for LLM integration)
- **Size**: ~5 MB
- **No framework dependencies** - completely framework-agnostic

## Installation Scenarios

### Scenario 1: Minimal CLI with Core Only
```bash
pip install socratic-core
# Then use core's API directly
from socratic_core import SocratesConfig, EventEmitter
config = SocratesConfig.from_env()
emitter = EventEmitter()
```

### Scenario 2: Build Custom RAG Pipeline
```bash
pip install socratic-core socratic-rag
# Your code using core config + RAG library
from socratic_core import SocratesConfig
from socratic_rag import RAGPipeline
```

### Scenario 3: REST API for Full Platform
```bash
pip install socrates-api
# Includes: socratic-core + all libraries via socrates-ai
uvicorn socrates_api.main:app
```

### Scenario 4: CLI with API Backend
```bash
pip install socrates-cli
# CLI automatically uses API if running
socrates project create --name myproject
```

### Scenario 5: Integrate with LangGraph
```bash
pip install socratic-core
pip install langgraph langchain

# Your code
from socratic_core import EventEmitter
from langgraph.graph import StateGraph

config = SocratesConfig.from_env()
emitter = EventEmitter()
# Build LangGraph with Socrates events
```

## Troubleshooting

### "Module not found: socratic_core"
```bash
# Make sure it's installed
pip install socratic-core
```

### "Module not found: socratic_rag"
```bash
# It's optional - install if needed
pip install socratic-rag
```

### "Cannot find package on PyPI"
```bash
# Local development - install with -e
pip install -e socratic-core
pip install -e socratic-rag
```

### Version conflicts
```bash
# Ensure compatible versions
pip install "socratic-core>=0.1.0" "socratic-rag>=0.1.0"
```

## Publishing to PyPI

When ready to publish:

```bash
# Build socratic-core
cd socratic-core
python -m build
twine upload dist/*

# Build socrates-cli
cd ../socrates-cli
python -m build
twine upload dist/*

# Build socrates-api
cd ../socrates-api
python -m build
twine upload dist/*

# Update main package to reference published versions
cd ..
pip install -e .
```

## Key Principles

1. **Minimal Core**: socratic-core has only 3 dependencies
2. **Optional Libraries**: All specialized libraries are optional
3. **Framework Agnostic**: No framework lock-in
4. **Backward Compatible**: Old code still works
5. **Progressive Adoption**: Start small, add libraries as needed

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| Core Size | 500 KB | 20 KB |
| Dependencies | 30+ | 3 (core) |
| Install Time | 5-10 min | 15-30 sec |
| Framework Lock-in | High (monolith) | None |
| Customization | Limited | Unlimited |

## Next Steps

1. **Choose your installation** based on your use case
2. **Import from core**: All framework features available via socratic-core
3. **Add libraries** as needed for specialized functionality
4. **Build your app** with any orchestration framework

For examples, see:
- `examples/langgraph_integration.py` - LangGraph + Socrates
- `examples/openclaw_integration.py` - Openclaw + Socrates
- `QUICKSTART.md` - 5-minute setup
