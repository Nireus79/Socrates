# Action Plan: Library Updates Required

**Prepared For**: Library Owner/Developer
**Date**: 2026-03-31
**Urgency**: HIGH - Required to unblock 14 integration tests
**Estimated Effort**: 1.5-2 hours total

---

## Summary

Four socratic-* libraries have structural issues preventing proper imports. This document tells you **exactly what to fix** in each library.

---

## Quick Overview

### 4 Libraries, 4 Issues

| # | Library | Issue | Fix Type | Time |
|---|---------|-------|----------|------|
| 1 | socratic_analyzer | Missing subpackage | Structural | 30min |
| 2 | socratic_rag | Missing subpackage | Structural | 30min |
| 3 | socratic_learning | Missing class | Functional | 15min |
| 4 | socratic_knowledge | Missing class | Functional | 15min |

---

## Library 1: socratic_analyzer

### What's Wrong
The library tries to import from a subpackage that doesn't exist.

### Exact Error
```
ModuleNotFoundError: No module named 'socratic_analyzer.analyzers'
```

### Where the Error Occurs
File: `socratic_analyzer/client.py`, Lines 5-13

```python
# THIS FAILS:
from socratic_analyzer.analyzers.complexity import ComplexityAnalyzer
from socratic_analyzer.analyzers.imports import ImportAnalyzer
from socratic_analyzer.analyzers.metrics import MetricsAnalyzer
from socratic_analyzer.analyzers.patterns import PatternAnalyzer
from socratic_analyzer.analyzers.performance import PerformanceAnalyzer
from socratic_analyzer.analyzers.smells import CodeSmellDetector
from socratic_analyzer.analyzers.static import StaticAnalyzer
```

### Your Options

#### Option A: Create the Missing Subpackage (Recommended if these classes don't exist elsewhere)
Create the `analyzers/` directory with 7 analyzer classes:

```
socratic_analyzer/
├── analyzers/
│   ├── __init__.py
│   ├── complexity.py      (ComplexityAnalyzer class)
│   ├── imports.py         (ImportAnalyzer class)
│   ├── metrics.py         (MetricsAnalyzer class)
│   ├── patterns.py        (PatternAnalyzer class)
│   ├── performance.py     (PerformanceAnalyzer class)
│   ├── smells.py          (CodeSmellDetector class)
│   └── static.py          (StaticAnalyzer class)
```

#### Option B: Fix the Import Path (If classes are elsewhere)
If these analyzer classes exist in different locations, update `client.py`:

```python
# Example - update to correct import path:
from socratic_analyzer.analyzer import CodeAnalyzer as ComplexityAnalyzer
from socratic_analyzer.metrics import MetricsCalculator as MetricsAnalyzer
# ... etc
```

#### Option C: Re-export from __init__.py (If classes need restructuring)
If the classes are in other modules, make them available through __init__.py:

```python
# In socratic_analyzer/__init__.py, add:
from .analyzer import CodeAnalyzer
from .metrics import MetricsCalculator
from .insights import InsightGenerator
# ... etc and add to __all__
```

### Verification Command
```bash
python -c "from socratic_analyzer import AnalyzerClient; print('✅ Works!')"
```

---

## Library 2: socratic_rag

### What's Wrong
The library tries to import from a subpackage that doesn't exist.

### Exact Error
```
ModuleNotFoundError: No module named 'socratic_rag.chunking'
```

### Where the Error Occurs
File: `socratic_rag/client.py`, Line 5

```python
# THIS FAILS:
from .chunking.base import BaseChunker
```

### Your Options

#### Option A: Create the Missing Subpackage (Recommended)
Create the `chunking/` directory with base chunker class:

```
socratic_rag/
├── chunking/
│   ├── __init__.py
│   ├── base.py        (BaseChunker class)
│   └── strategies.py  (SemanticChunker, FixedChunker, RecursiveChunker)
```

#### Option B: Fix the Import Path
If chunking is implemented elsewhere:

```python
# In socratic_rag/client.py, change to correct import:
from socratic_rag.strategies import BaseChunker
# or
from socratic_rag.splitting import BaseChunker
```

#### Option C: Implement Chunking Differently
If chunking is now handled internally, remove or update the import.

### Verification Command
```bash
python -c "from socratic_rag import RAGClient; print('✅ Works!')"
```

---

## Library 3: socratic_learning

### What's Wrong
A class that Socrates imports doesn't exist in the library.

### Exact Error
```
ImportError: cannot import name 'PatternDetector' from 'socratic_learning'
```

### What Socrates Needs to Import
```python
from socratic_learning import (
    LearningEngine,           # ✅ Already exists
    PatternDetector,          # ❌ MISSING - NEED TO ADD
    MetricsCollector,         # ✅ Already exists
    RecommendationEngine,     # ✅ Already exists
    UserFeedback,             # ✅ Already exists
    FineTuningDataExporter,   # ✅ Already exists
)
```

### Your Options

#### Option A: Create PatternDetector Class (Recommended)
Create a new `pattern_detection.py` file with the class:

```python
# In socratic_learning/pattern_detection.py:
class PatternDetector:
    """Detects patterns in learning interactions."""
    def detect_patterns(self, interactions):
        pass
    def analyze_sequence(self, sequence):
        pass
```

Then export from `__init__.py`:
```python
from .pattern_detection import PatternDetector

__all__ = [
    # ... existing exports ...
    "PatternDetector",
]
```

#### Option B: Rename/Alias Existing Class
If pattern detection exists under a different name:

```python
# In socratic_learning/__init__.py:
from .existing_module import ExistingPatternClass as PatternDetector
```

### Verification Command
```bash
python -c "from socratic_learning import PatternDetector; print('✅ Works!')"
```

---

## Library 4: socratic_knowledge

### What's Wrong
A class that Socrates imports doesn't exist in the library.

### Exact Error
```
ImportError: cannot import name 'KnowledgeBase' from 'socratic_knowledge'
```

### What Socrates Needs to Import
```python
from socratic_knowledge import (
    KnowledgeBase,       # ❌ MISSING - NEED TO ADD
    DocumentStore,       # ✅ Already exists
    SearchEngine,        # ✅ Already exists
    RBACManager,         # ✅ Already exists
    VersionControl,      # ✅ Already exists
    SemanticSearch,      # ✅ Already exists
    AuditLogger,         # ✅ Already exists
)
```

### Your Options

#### Option A: Create KnowledgeBase Class (Recommended)
Create a new `knowledge_base.py` file with the class:

```python
# In socratic_knowledge/knowledge_base.py:
class KnowledgeBase:
    """Main knowledge base management system."""
    def add_document(self, doc):
        pass
    def search(self, query):
        pass
    def get_document(self, doc_id):
        pass
```

Then export from `__init__.py`:
```python
from .knowledge_base import KnowledgeBase

__all__ = [
    # ... existing exports ...
    "KnowledgeBase",
]
```

#### Option B: Alias Existing Class
If you want to use `KnowledgeItem` as the base:

```python
# In socratic_knowledge/__init__.py:
from .knowledge_item import KnowledgeItem as KnowledgeBase

__all__ = [
    # ... existing exports ...
    "KnowledgeBase",  # Alias for KnowledgeItem
]
```

### Verification Command
```bash
python -c "from socratic_knowledge import KnowledgeBase; print('✅ Works!')"
```

---

## Testing the Fixes

### Individual Library Tests
```bash
# Test each library separately
python -c "from socratic_analyzer import AnalyzerClient; print('✅ socratic_analyzer')"
python -c "from socratic_rag import RAGClient; print('✅ socratic_rag')"
python -c "from socratic_learning import PatternDetector; print('✅ socratic_learning')"
python -c "from socratic_knowledge import KnowledgeBase; print('✅ socratic_knowledge')"
```

### Full Integration Test Suite
```bash
cd backend/src
python -m pytest tests/integration/test_integration_core.py -v

# Expected when all libraries are fixed:
# ======================== 21 passed in X.XXs ========================
```

---

## Implementation Checklist

### socratic_analyzer
- [ ] Decide on fix approach (A, B, or C)
- [ ] Implement fix
- [ ] Verify import works: `python -c "from socratic_analyzer import AnalyzerClient"`
- [ ] Run test: `python -m pytest tests/integration/test_integration_core.py::TestLibrarySingletonIntegration::test_analyzer_singleton_initialized_once`

### socratic_rag
- [ ] Decide on fix approach (A, B, or C)
- [ ] Implement fix
- [ ] Verify import works: `python -c "from socratic_rag import RAGClient"`
- [ ] Run test: `python -m pytest tests/integration/test_integration_core.py::TestLibrarySingletonIntegration::test_rag_singleton_initialized_once`

### socratic_learning
- [ ] Decide on fix approach (A or B)
- [ ] Implement fix
- [ ] Verify import works: `python -c "from socratic_learning import PatternDetector"`
- [ ] Run test: `python -m pytest tests/integration/test_integration_core.py::TestLibrarySingletonIntegration::test_learning_singleton_initialized_once`

### socratic_knowledge
- [ ] Decide on fix approach (A or B)
- [ ] Implement fix
- [ ] Verify import works: `python -c "from socratic_knowledge import KnowledgeBase"`
- [ ] Run test: `python -m pytest tests/integration/test_integration_core.py::TestLibrarySingletonIntegration::test_knowledge_singleton_initialized_once`

### Final Verification
- [ ] Run full test suite: `python -m pytest tests/integration/test_integration_core.py -v`
- [ ] Verify all 21 tests pass
- [ ] Update PyPI packages with new versions

---

## Priority

**HIGH** - These fixes unblock:
- ✅ 6 singleton initialization tests
- ✅ 4 library component verification tests
- ✅ 2 performance optimization tests
- ✅ 1 integration flow test

**Total**: 14 tests waiting for these library fixes

---

## Communication

When you've fixed the libraries:
1. Update package versions on PyPI
2. Let me know the new versions
3. I'll run `pip install --upgrade socratic-*` and re-test

Expected timeline: ~2 hours from fix to verification

---

## Support

### Questions During Implementation?

For **socratic_analyzer** issues:
- Check: `socratic_analyzer/client.py` and see what analyzers it expects
- Option: Check `socratic_analyzer/analyzer.py` to see what CodeAnalyzer provides
- Solution: Either create the subpackage OR rename imports

For **socratic_rag** issues:
- Check: `socratic_rag/client.py` and see what chunking functionality it needs
- Solution: Either create `chunking/` subpackage OR move chunking elsewhere

For **socratic_learning** issues:
- Create: Simple class that detects learning patterns
- Export: Make it available in `__init__.py`

For **socratic_knowledge** issues:
- Create: Main knowledge base management class
- OR Alias: Use `KnowledgeItem` if that's the core

---

## Expected Outcome

After all fixes:
```bash
$ pip install --upgrade socratic-analyzer socratic-rag socratic-learning socratic-knowledge

$ cd backend/src

$ python -m pytest tests/integration/test_integration_core.py -v

======================== 21 passed in 1.50s ========================

✅ All tests passing
✅ Socrates fully integrated with all 4 libraries
✅ Ready for production
```

---

## Next Steps

1. **Choose fix approach for each library** (A, B, or C)
2. **Implement the fixes** in your library source repositories
3. **Update PyPI packages** with new versions
4. **Let me know** when updates are available
5. **I'll verify** all tests pass

---

**Document Version**: 1.0
**Created**: 2026-03-31
**Status**: Ready for Implementation
**Questions?**: Review LIBRARY_FIX_INSTRUCTIONS.md for detailed examples
