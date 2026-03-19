# Migration Guide: Updated Packages (March 19, 2026)

## Overview

We've created modern replacements for deprecated packages and published new integration libraries. This guide helps you migrate to the latest packages.

## Timeline

- **Status**: New packages released, old packages deprecated
- **Support**: Old packages will receive deprecation warnings but remain available
- **Recommendation**: Migrate to new packages within 6 months

---

## Package Migration Matrix

| Old Package | Status | Migration Path | New Package |
|---|---|---|---|
| **socrates-ai** (1.3.4) | ❌ Deprecated | Use modular libs | socratic-core + socratic-learning |
| **socrates-ai-openclaw** (1.0.0) | ❌ Broken/Deprecated | Use new skill | **socratic-openclaw-skill** (0.1.0) |
| *(NEW)* | ✅ NEW | LangGraph users | **socrates-ai-langraph** (0.1.0) |

---

## Option 1: Migrate from socrates-ai

### Current Setup (Deprecated)

```bash
pip install socrates-ai
```

```python
from socratic_system import SocratesConfig, EventEmitter
```

### New Setup (Recommended)

```bash
pip install socratic-core socratic-learning socratic-agents socratic-rag
```

```python
from socratic_core import SocratesConfig, EventEmitter
from socratic_learning import InteractionLogger
```

### Migration Steps

1. **Update dependencies in requirements.txt or pyproject.toml**

   ```toml
   # Before
   socrates-ai = ">=1.3.0"

   # After
   socratic-core = ">=0.1.1"
   socratic-learning = ">=0.1.1"
   socratic-agents = ">=0.1.0"  # if needed
   socratic-rag = ">=0.1.0"     # if needed
   ```

2. **Update imports**

   ```python
   # Before
   from socratic_system import SocratesConfig, EventEmitter

   # After
   from socratic_core import SocratesConfig, EventEmitter
   ```

3. **Test thoroughly**

   ```bash
   pytest tests/
   ```

### Backward Compatibility

The main `socrates-ai` package still works with old imports via re-exports:

```python
# ✅ Still works
from socratic_system import SocratesConfig

# ⭐ Recommended
from socratic_core import SocratesConfig
```

---

## Option 2: Migrate from socrates-ai-openclaw

### Current Setup (Broken)

```bash
# ❌ BROKEN - Depends on non-existent socrates-ai>=1.3.0
pip install socrates-ai-openclaw
```

```python
from socrates_openclaw import SocraticDiscoverySkill
```

### New Setup (Works!)

```bash
# ✅ NEW - Modern architecture
pip install socratic-openclaw-skill
```

```python
from socratic_openclaw_skill import SocraticDiscoverySkill
```

### Migration Steps

1. **Uninstall old package**

   ```bash
   pip uninstall socrates-ai-openclaw
   ```

2. **Install new package**

   ```bash
   pip install socratic-openclaw-skill
   ```

3. **Update imports**

   ```python
   # Before (broken)
   from socrates_openclaw import SocraticDiscoverySkill

   # After (works)
   from socratic_openclaw_skill import SocraticDiscoverySkill
   ```

4. **Test**

   ```bash
   pytest tests/
   ```

### Key Changes

- **Dependencies**: Now uses `socratic-core>=0.1.1` (working)
- **Configuration**: Renamed `SocratesOpenclawConfig` → `SocraticOpenclawConfig`
- **API**: Same interface, better implementation

---

## Option 3: Migrate to LangGraph Integration

### If You Use LangGraph

```bash
# Install new integration
pip install socrates-ai-langraph
```

### Basic Example

```python
from socrates_ai_langraph import create_socrates_langgraph_workflow, AgentState

# Create workflow
workflow = create_socrates_langgraph_workflow()
app = workflow.compile()

# Run
initial_state = AgentState(input="Your task")
result = app.invoke(initial_state)

print(result.messages)
print(result.results)
```

### With Optional Features

```bash
# Add agent support
pip install "socrates-ai-langraph[agents]"

# Add RAG support
pip install "socrates-ai-langraph[rag]"

# Everything
pip install "socrates-ai-langraph[full]"
```

---

## Compatibility Matrix

### Python Versions

| Package | Python 3.8 | Python 3.9 | Python 3.10 | Python 3.11 | Python 3.12 |
|---------|:---:|:---:|:---:|:---:|:---:|
| socratic-core | ✅ | ✅ | ✅ | ✅ | ✅ |
| socratic-learning | ✅ | ✅ | ✅ | ✅ | ✅ |
| socratic-openclaw-skill | ✅ | ✅ | ✅ | ✅ | ✅ |
| socrates-ai-langraph | ❌ | ✅ | ✅ | ✅ | ✅ |
| socrates-ai (old) | ✅ | ✅ | ✅ | ✅ | ✅ |

### Framework Support

| Package | LangGraph | OpenClaw | OpenAI | Anthropic |
|---------|:---:|:---:|:---:|:---:|
| socratic-core | ✅ | ✅ | ✅ | ✅ |
| socratic-openclaw-skill | ❌ | ✅ | ❌ | ✅ |
| socrates-ai-langraph | ✅ | ❌ | ❌ | ✅ |

---

## Installation Checklists

### For Core Development

```bash
# Minimal
pip install socratic-core

# Development
pip install socratic-core "socratic-core[dev]"

# With learning engine
pip install socratic-core socratic-learning

# Everything
pip install socratic-core socratic-learning socratic-agents socratic-rag
```

### For OpenClaw Users

```bash
# Old (broken, do NOT use)
# pip install socrates-ai-openclaw ❌

# New (modern, works)
pip install socratic-openclaw-skill ✅

# With development tools
pip install "socratic-openclaw-skill[dev]"
```

### For LangGraph Users

```bash
# Core
pip install socrates-ai-langraph

# With agents
pip install "socrates-ai-langraph[agents]"

# With RAG
pip install "socrates-ai-langraph[rag]"

# Everything
pip install "socrates-ai-langraph[full]"
```

---

## Testing After Migration

### Verify Installation

```bash
python -c "from socratic_core import SocratesConfig; print('✓ socratic-core works')"
python -c "from socratic_openclaw_skill import SocraticDiscoverySkill; print('✓ socratic-openclaw-skill works')"
python -c "from socrates_ai_langraph import create_socrates_langgraph_workflow; print('✓ socrates-ai-langraph works')"
```

### Run Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests
pytest tests/ -v --cov
```

### Import Tests

```bash
# Test old imports still work (backward compatibility)
python -c "from socratic_system import SocratesConfig; print('✓ Backward compat works')"

# Test new imports work
python -c "from socratic_core import SocratesConfig; print('✓ New imports work')"
```

---

## Version Mapping

| Component | Old Version | New Version | Status |
|-----------|---|---|---|
| socratic-core | N/A | 0.1.1 | ✅ Latest |
| socratic-learning | N/A | 0.1.1 | ✅ Latest |
| socrates-cli | N/A | 0.1.0 | ✅ Latest |
| socrates-core-api | N/A | 0.1.0 | ✅ Latest |
| socratic-openclaw-skill | N/A | 0.1.0 | ✅ New |
| socrates-ai-langraph | N/A | 0.1.0 | ✅ New |
| **socrates-ai** | 1.3.4 | 1.3.4 | ⚠️ Deprecated |
| **socrates-ai-openclaw** | 1.0.0 | 1.0.0 | ⚠️ Deprecated/Broken |

---

## Troubleshooting

### Import Error: No module named 'socratic_core'

```bash
# Solution
pip install socratic-core
```

### Import Error: No module named 'socratic_openclaw'

```bash
# Old package no longer supported
# Solution: Use new package
pip uninstall socrates-ai-openclaw
pip install socratic-openclaw-skill
```

### Dependency Conflict

```bash
# If you get: "socrates-ai requires socrates-ai>=1.3.0"
# This means socrates-ai-openclaw is still installed
# Solution:
pip uninstall socrates-ai-openclaw
pip install socratic-openclaw-skill
```

### LangGraph Import Error

```bash
# Error: No module named 'langgraph'
# Solution:
pip install langgraph
```

---

## Support

- **GitHub Issues**: [Report problems](https://github.com/Nireus79/Socrates/issues)
- **Discussions**: [Ask questions](https://github.com/Nireus79/Socrates/discussions)
- **Documentation**: [Detailed docs](https://github.com/Nireus79/Socrates/tree/main/docs)

---

## Summary

| Task | Action | Timeline |
|------|--------|----------|
| **Migrate from socrates-ai** | Use `socratic-core` + `socratic-learning` | Immediate |
| **Migrate from socrates-ai-openclaw** | Switch to `socratic-openclaw-skill` | Immediate |
| **Add LangGraph support** | Install `socrates-ai-langraph` | As needed |
| **Update imports** | Use new package imports | During migration |
| **Test thoroughly** | Run full test suite | Before production |
| **Update documentation** | Update READMEs and guides | Before release |

**All new packages are production-ready and recommended for immediate adoption.**

---

**Last Updated**: March 19, 2026
**Version**: 1.0
**Status**: Active
