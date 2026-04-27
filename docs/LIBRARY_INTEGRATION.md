# Library Integration Architecture

## Overview

Socrates v1.3.3+ uses a modular architecture built on specialized libraries, replacing the previous monolithic implementation. This document explains how these libraries integrate into the Socrates system.

## Core Libraries

### 1. socratic-nexus (v0.4.0)
**Purpose:** Universal LLM client supporting Claude, GPT-4, Gemini, and Ollama

**Location in Socrates:** `socratic_system/clients/`

**Features:**
- Multi-provider LLM support
- Automatic retry and fallback mechanisms
- Token usage tracking
- Streaming support
- Async/await support with native async methods

**Usage:**
```python
from socratic_system.clients import GoogleClient, ClaudeClient, OpenAIClient
```

**Key Components:**
- GoogleClient: Gemini models (now using google-genai with native async)
- ClaudeClient: Claude models (via Anthropic API)
- OpenAIClient: GPT-4 and GPT-3.5 models
- OllamaClient: Local LLM hosting

### 2. socratic-maturity (v0.2.0)
**Purpose:** Project maturity assessment and phase categorization

**Location in Socrates:** `socratic_system/maturity/`

**Features:**
- 6 project type categories (software, business, creative, research, marketing, educational)
- Phase-based maturity scoring
- Threshold-based status determination
- Claude-powered intelligent categorization

**Usage:**
```python
from socratic_system.maturity import MaturityCalculator
calculator = MaturityCalculator(project_type="software")
```

**Bridge Pattern:** `socratic_system/maturity/__init__.py` re-exports library components

### 3. socratic-agents (v0.3.0+)
**Purpose:** Multi-agent orchestration and coordination

**Location in Socrates:** `socratic_system/agents/`

**Features:**
- Base Agent class and agent management
- Coordination mechanisms
- Event-driven architecture

**Key Agents in Socrates:**
- QualityControllerAgent
- ConflictDetectorAgent
- WorkflowBuilderAgent
- QuestionSelectorAgent
- AnalyticsAgent

### 4. socratic-rag (v0.1.0+)
**Purpose:** Retrieval-Augmented Generation for knowledge management

**Location in Socrates:** `socratic_system/knowledge/`

**Features:**
- Vector database integration
- Semantic search and retrieval
- Knowledge base management

### 5. socratic-learning (v0.1.0+)
**Purpose:** Learning progress tracking and adaptive learning

**Location in Socrates:** `socratic_system/learning/`

**Features:**
- Learning path management
- Progress tracking
- Adaptive recommendations

### 6. socratic-knowledge (v0.1.0+)
**Purpose:** Knowledge base and domain expertise

**Location in Socrates:** `socratic_system/knowledge/`

### 7. socratic-conflict (v0.1.0+)
**Purpose:** Conflict detection and resolution between project requirements

**Location in Socrates:** `socratic_system/conflict/`

**Features:**
- Goals conflict detection
- Technical stack compatibility checking
- Requirements conflict resolution
- Constraints validation

**Key Checkers:**
- GoalsConflictChecker
- TechStackConflictChecker
- RequirementsConflictChecker
- ConstraintsConflictChecker

### 8. socratic-workflow (v0.1.0+)
**Purpose:** Workflow analysis and optimization

**Location in Socrates:** `socratic_system/workflow/`

**Features:**
- Workflow path analysis
- Cost calculation
- Risk assessment
- Workflow optimization

### 9. socratic-performance (v0.1.0+)
**Purpose:** Performance monitoring and analytics

**Location in Socrates:** `socratic_system/performance/`

## Bridge Module Pattern

Socrates uses a "bridge module" pattern to integrate library functionality while maintaining a stable internal API.

### How It Works

Each library has a corresponding bridge module that:
1. **Re-exports** library classes and functions
2. **Provides compatibility** layer if needed
3. **Maintains API stability** for the rest of Socrates

### Bridge Modules

```
socratic_system/
├── clients/__init__.py           → imports from socratic_nexus
├── maturity/__init__.py          → imports from socratic_maturity
├── agents/                       → imports from socratic_agents
├── knowledge/__init__.py         → imports from socratic_knowledge
├── learning/__init__.py          → imports from socratic_learning
├── conflict/__init__.py          → imports from socratic_conflict
├── workflow/__init__.py          → imports from socratic_workflow
└── performance/__init__.py       → imports from socratic_performance
```

### Example Bridge Module

```python
# socratic_system/clients/__init__.py
from socratic_nexus.clients import (
    ClaudeClient,
    GoogleClient,
    OpenAIClient,
    OllamaClient,
)

__all__ = [
    "ClaudeClient",
    "GoogleClient",
    "OpenAIClient",
    "OllamaClient",
]
```

## Local Code (Not from Libraries)

The following modules are local implementations specific to Socrates and are NOT from libraries:

### Core Orchestration
- `socratic_system/core/workflow_optimizer.py` - Orchestrates workflow execution
- `socratic_system/core/analytics_calculator.py` - Calculates analytics
- `socratic_system/core/question_selector.py` - Selects Socratic questions
- `socratic_system/core/workflow_builder.py` - Builds execution workflows
- `socratic_system/core/project_categories.py` - Project type definitions

### Quality Control
- `socratic_system/quality/quality_controller.py` - Quality assessment
- Related modules for quality checking

### Models & Data
- `socratic_system/models/` - Data models specific to Socrates
- `socratic_system/config/` - Configuration management

## Integration Points

### LLM Client Selection

Socrates uses `socratic-nexus` clients for all LLM interactions:
```python
from socratic_system.clients import GoogleClient, ClaudeClient

# Create client with configuration
client = GoogleClient(api_key=api_key, orchestrator=self)

# Use standard interface
response = client.generate_response(prompt)
```

### Maturity Assessment

Integration with `socratic-maturity`:
```python
from socratic_system.maturity import MaturityCalculator

calculator = MaturityCalculator(
    project_type="software",
    claude_client=claude_client
)

score = calculator.calculate_phase_maturity(phase_data)
```

### Agent Coordination

Agents inherit from `socratic-agents` base classes:
```python
from socratic_system.agents import Agent

class CustomAgent(Agent):
    async def execute(self, context):
        # Agent implementation
        pass
```

### Conflict Detection

Using `socratic-conflict` checkers:
```python
from socratic_system.conflict import (
    GoalsConflictChecker,
    TechStackConflictChecker,
)

checker = GoalsConflictChecker()
conflicts = checker.detect(goals)
```

## Configuration

Libraries are configured through Socrates' main configuration system:

```python
# Configuration
config = {
    "google_model": "gemini-2.0-flash",
    "openai_model": "gpt-4",
    "claude_model": "claude-3-opus-20240229",
    "ollama_model": "llama2",
}
```

## Dependency Management

### Installation

All libraries are installed via `requirements.txt`:

```
socratic-nexus>=0.4.0
socratic-maturity>=0.2.0
socratic-agents>=0.3.0
socratic-rag>=0.1.0
socratic-learning>=0.1.0
socratic-knowledge>=0.1.0
socratic-conflict>=0.1.0
socratic-workflow>=0.1.0
socratic-performance>=0.1.0
```

### Version Management

Each library follows semantic versioning (MAJOR.MINOR.PATCH). Socrates specifies minimum versions but allows compatible patches.

## Migration from Monolithic Architecture

The following components were previously local implementations but are now provided by libraries:

| Component | Previous | Current |
|-----------|----------|---------|
| LLM Clients | `socratic_system/clients/` (local) | socratic-nexus library |
| Maturity Calculator | `socratic_system/core/maturity_calculator.py` | socratic-maturity library |
| Agents | Various local agents | socratic-agents library |
| Conflict Detection | `socratic_system/conflict_resolution/` (local) | socratic-conflict library |
| Workflow Analysis | Local implementations | socratic-workflow library |
| Learning Engine | Local implementation | socratic-learning library |
| Knowledge Base | Local implementation | socratic-rag library |

## Best Practices

### Importing from Libraries

✅ **DO:**
```python
# Import through bridge modules
from socratic_system.clients import GoogleClient
from socratic_system.maturity import MaturityCalculator
```

❌ **DON'T:**
```python
# Don't import directly from libraries
from socratic_nexus.clients import GoogleClient
from socratic_maturity import MaturityCalculator
```

### Adding New Functionality

If adding features that overlap with libraries:
1. Check if the library already has this functionality
2. Use the library implementation when possible
3. Only create local code for Socrates-specific logic
4. Keep local code in appropriate subdirectories

### Contributing to Libraries

If you find bugs or want features in libraries:
1. Check the library repository's issues
2. Open an issue or pull request in the library repo
3. Libraries are at: https://github.com/Nireus79/socratic-*

## Troubleshooting

### Library Import Errors

**Issue:** `ModuleNotFoundError: No module named 'socratic_nexus'`

**Solution:** Ensure libraries are installed:
```bash
pip install -r requirements.txt
```

### Version Conflicts

**Issue:** Library version incompatibility

**Solution:** Update requirements:
```bash
pip install --upgrade -r requirements.txt
```

### Bridge Module Issues

**Issue:** `ImportError` from bridge module

**Solution:** Verify the library is installed and the bridge module path is correct

## Architecture Diagram

```
Socrates Application
    ↓
┌───────────────────────────────────────┐
│     Bridge Modules                    │
│  (socratic_system/*/  __init__.py)    │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│     Socratic Libraries (PyPI)          │
├───────────────────────────────────────┤
│ • socratic-nexus (LLM clients)        │
│ • socratic-maturity (Assessment)      │
│ • socratic-agents (Orchestration)     │
│ • socratic-rag (Knowledge)            │
│ • socratic-learning (Adaptation)      │
│ • socratic-conflict (Detection)       │
│ • socratic-workflow (Execution)       │
│ • socratic-performance (Analytics)    │
└───────────────────────────────────────┘
```

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - Overall system architecture
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Development environment setup
- Library repositories on GitHub: https://github.com/Nireus79?q=socratic
