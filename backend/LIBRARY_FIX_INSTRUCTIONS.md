# Library Fix Instructions

**Status**: Detailed fix instructions for each library
**Target**: Get all 21 integration tests passing
**Effort**: ~2-3 hours per library

---

## Library 1: socratic_analyzer

### Current State
- **File**: `socratic_analyzer/client.py` (broken)
- **Symptom**: `ModuleNotFoundError: No module named 'socratic_analyzer.analyzers'`
- **Cause**: Imports from non-existent subpackage

### The Broken Import Chain
```
socratic_analyzer/__init__.py (line 7)
  ↓ imports
socratic_analyzer/async_client.py (line 6)
  ↓ imports
socratic_analyzer/client.py (line 5)
  ↓ tries to import
socratic_analyzer.analyzers.complexity ❌ DOESN'T EXIST
```

### Exact Lines That Need Fixing

**File**: `socratic_analyzer/client.py`

```python
# CURRENT (BROKEN) - Lines 5-13:
from socratic_analyzer.analyzers.complexity import ComplexityAnalyzer
from socratic_analyzer.analyzers.imports import ImportAnalyzer
from socratic_analyzer.analyzers.metrics import MetricsAnalyzer
from socratic_analyzer.analyzers.patterns import PatternAnalyzer
from socratic_analyzer.analyzers.performance import PerformanceAnalyzer
from socratic_analyzer.analyzers.smells import CodeSmellDetector
from socratic_analyzer.analyzers.static import StaticAnalyzer
from socratic_analyzer.models import Analysis, AnalyzerConfig, CodeIssue
from socratic_analyzer.utils.quality_scorer import QualityScorer
```

### Fix Option A: Create the Missing Subpackage Structure

Create the following files:

**`socratic_analyzer/analyzers/__init__.py`**
```python
"""Analyzer submodule."""

from .complexity import ComplexityAnalyzer
from .imports import ImportAnalyzer
from .metrics import MetricsAnalyzer
from .patterns import PatternAnalyzer
from .performance import PerformanceAnalyzer
from .smells import CodeSmellDetector
from .static import StaticAnalyzer

__all__ = [
    "ComplexityAnalyzer",
    "ImportAnalyzer",
    "MetricsAnalyzer",
    "PatternAnalyzer",
    "PerformanceAnalyzer",
    "CodeSmellDetector",
    "StaticAnalyzer",
]
```

Then create each analyzer file:
- `socratic_analyzer/analyzers/complexity.py` - ComplexityAnalyzer class
- `socratic_analyzer/analyzers/imports.py` - ImportAnalyzer class
- `socratic_analyzer/analyzers/metrics.py` - MetricsAnalyzer class
- `socratic_analyzer/analyzers/patterns.py` - PatternAnalyzer class
- `socratic_analyzer/analyzers/performance.py` - PerformanceAnalyzer class
- `socratic_analyzer/analyzers/smells.py` - CodeSmellDetector class
- `socratic_analyzer/analyzers/static.py` - StaticAnalyzer class

### Fix Option B: Fix the Import Path (Simpler)

If the analyzer classes exist elsewhere or in a different structure, update `client.py` to import from the correct location.

**Example if analyzers are in a different module**:
```python
# FIXED VERSION - Import from actual location
from socratic_analyzer.analyzer import CodeAnalyzer
from socratic_analyzer.metrics import MetricsCalculator
from socratic_analyzer.insights import InsightGenerator
# ... etc
```

### Fix Option C: Create Missing Utils Module

If QualityScorer doesn't exist:

**`socratic_analyzer/utils/quality_scorer.py`**
```python
"""Quality scoring module."""

class QualityScorer:
    """Scores code quality based on analysis results."""

    def calculate_score(self, analysis_result):
        """Calculate quality score from analysis."""
        # Implementation
        pass
```

### How to Verify the Fix

Once fixed, this should work:
```bash
python -c "from socratic_analyzer import AnalyzerClient; print('✅ Import successful')"
```

---

## Library 2: socratic_rag

### Current State
- **File**: `socratic_rag/client.py` (broken)
- **Symptom**: `ModuleNotFoundError: No module named 'socratic_rag.chunking'`
- **Cause**: Imports from non-existent subpackage

### The Broken Import Chain
```
socratic_rag/__init__.py
  ↓ imports
socratic_rag/async_client.py
  ↓ imports
socratic_rag/client.py (line 5)
  ↓ tries to import
socratic_rag.chunking.base ❌ DOESN'T EXIST
```

### Exact Lines That Need Fixing

**File**: `socratic_rag/client.py` (line 5)

```python
# CURRENT (BROKEN):
from .chunking.base import BaseChunker

# NEED TO FIX THIS
```

### Fix Option A: Create the Missing Chunking Subpackage

Create the following files:

**`socratic_rag/chunking/__init__.py`**
```python
"""Chunking strategies for document splitting."""

from .base import BaseChunker
from .strategies import SemanticChunker, FixedChunker, RecursiveChunker

__all__ = [
    "BaseChunker",
    "SemanticChunker",
    "FixedChunker",
    "RecursiveChunker",
]
```

**`socratic_rag/chunking/base.py`**
```python
"""Base chunker interface."""

from abc import ABC, abstractmethod

class BaseChunker(ABC):
    """Base class for document chunking strategies."""

    @abstractmethod
    def chunk(self, text: str, chunk_size: int = 512) -> list:
        """Split text into chunks."""
        pass
```

**`socratic_rag/chunking/strategies.py`**
```python
"""Chunking strategy implementations."""

from .base import BaseChunker

class SemanticChunker(BaseChunker):
    """Chunks text by semantic meaning."""
    def chunk(self, text: str, chunk_size: int = 512) -> list:
        # Implementation
        pass

class FixedChunker(BaseChunker):
    """Chunks text into fixed-size pieces."""
    def chunk(self, text: str, chunk_size: int = 512) -> list:
        # Implementation
        pass

class RecursiveChunker(BaseChunker):
    """Recursively chunks text."""
    def chunk(self, text: str, chunk_size: int = 512) -> list:
        # Implementation
        pass
```

### Fix Option B: Fix the Import Path

If chunking is implemented elsewhere:

```python
# Update socratic_rag/client.py to import from correct location
# Example:
from socratic_rag.strategies import BaseChunker
# or
from socratic_rag.splitting import BaseChunker
```

### How to Verify the Fix

Once fixed:
```bash
python -c "from socratic_rag import RAGClient; print('✅ Import successful')"
```

---

## Library 3: socratic_learning

### Current State
- **Class Missing**: `PatternDetector`
- **Symptom**: `ImportError: cannot import name 'PatternDetector' from 'socratic_learning'`
- **Cause**: Class doesn't exist in library exports

### What Socrates Needs
**File**: `backend/src/socrates_api/models_local.py` (line 290)

```python
from socratic_learning import (
    LearningEngine,           # ✅ Check if exists
    PatternDetector,          # ❌ MISSING - NEED TO ADD
    MetricsCollector,         # ✅ Check if exists
    RecommendationEngine,     # ✅ Check if exists
    UserFeedback,             # ✅ Check if exists
    FineTuningDataExporter,   # ✅ Check if exists
)
```

### Fix: Add PatternDetector to socratic_learning

**File**: `socratic_learning/__init__.py`

Add to imports and exports:

```python
# Current __init__.py needs to have:
from .pattern_detection import PatternDetector  # ADD THIS

# And in __all__:
__all__ = [
    # ... existing exports ...
    "PatternDetector",  # ADD THIS
]
```

**Create File**: `socratic_learning/pattern_detection.py`

```python
"""Pattern detection module."""

class PatternDetector:
    """Detects learning patterns in user interactions."""

    def __init__(self):
        """Initialize pattern detector."""
        pass

    def detect_patterns(self, interactions):
        """Detect patterns in user learning interactions."""
        return {
            "patterns": [],
            "insights": [],
        }

    def analyze_sequence(self, sequence):
        """Analyze learning sequence."""
        return {"sequence_type": "unknown"}
```

### Alternative Fix: Check if PatternDetector Exists Under Different Name

Search the library for similar classes:
```bash
grep -r "class Pattern" socratic_learning/
grep -r "class Detection" socratic_learning/
grep -r "Pattern" socratic_learning/__init__.py
```

If found under different name, either:
1. Add an alias in `__init__.py`: `PatternDetector = ExistingClass`
2. Create a wrapper class that uses the existing implementation

### How to Verify the Fix

Once fixed:
```bash
python -c "from socratic_learning import PatternDetector; print('✅ Import successful')"
```

---

## Library 4: socratic_knowledge

### Current State
- **Class Missing**: `KnowledgeBase`
- **Symptom**: `ImportError: cannot import name 'KnowledgeBase' from 'socratic_knowledge'`
- **Cause**: Class doesn't exist; library has `KnowledgeItem` instead

### What Socrates Needs
**File**: `backend/src/socrates_api/models_local.py` (line 877)

```python
from socratic_knowledge import (
    KnowledgeBase,       # ❌ MISSING - NEED TO ADD
    DocumentStore,       # ✅ Check if exists
    SearchEngine,        # ✅ Check if exists
    RBACManager,         # ✅ Check if exists
    VersionControl,      # ✅ Check if exists
    SemanticSearch,      # ✅ Check if exists
    AuditLogger,         # ✅ Check if exists
)
```

### Fix: Add KnowledgeBase to socratic_knowledge

**File**: `socratic_knowledge/__init__.py`

Add to imports and exports:

```python
# Current __init__.py needs to have:
from .knowledge_base import KnowledgeBase  # ADD THIS

# And in __all__:
__all__ = [
    # ... existing exports ...
    "KnowledgeBase",  # ADD THIS
]
```

**Create File**: `socratic_knowledge/knowledge_base.py`

```python
"""Knowledge base management module."""

class KnowledgeBase:
    """Main knowledge base management system."""

    def __init__(self):
        """Initialize knowledge base."""
        self.documents = []
        self.metadata = {}

    def add_document(self, doc):
        """Add document to knowledge base."""
        self.documents.append(doc)
        return doc

    def search(self, query):
        """Search knowledge base."""
        return []

    def get_document(self, doc_id):
        """Get document by ID."""
        return None
```

### Alternative Fix: Use KnowledgeItem Instead

If `KnowledgeItem` is the main class and you want to use it:

1. In `socratic_knowledge/__init__.py`, create an alias:
```python
from .knowledge_item import KnowledgeItem as KnowledgeBase

__all__ = [
    "KnowledgeBase",  # Alias for KnowledgeItem
    # ... other exports ...
]
```

2. Or update Socrates to use `KnowledgeItem` instead of `KnowledgeBase`:
```python
# In models_local.py, change:
from socratic_knowledge import (
    KnowledgeItem as KnowledgeBase,  # Use alias
    # ... rest ...
)
```

### How to Verify the Fix

Once fixed:
```bash
python -c "from socratic_knowledge import KnowledgeBase; print('✅ Import successful')"
```

---

## Verification Checklist

After making all fixes, run this to verify each library:

### Test Script: `verify_libraries.py`

```python
#!/usr/bin/env python3
"""Verify all libraries import correctly."""

libraries = [
    ("socratic_analyzer", ["AnalyzerClient", "AsyncAnalyzerClient"]),
    ("socratic_rag", ["RAGClient"]),
    ("socratic_learning", ["LearningEngine", "PatternDetector"]),
    ("socratic_knowledge", ["KnowledgeBase"]),
]

print("Verifying library imports...\n")

failed = []
for lib_name, classes in libraries:
    try:
        lib = __import__(lib_name)
        print(f"✅ {lib_name} imports successfully")

        for cls in classes:
            try:
                getattr(lib, cls)
                print(f"   ✅ {cls} available")
            except AttributeError:
                print(f"   ❌ {cls} NOT FOUND")
                failed.append(f"{lib_name}.{cls}")
    except Exception as e:
        print(f"❌ {lib_name} import FAILED: {e}")
        failed.append(lib_name)
    print()

if failed:
    print(f"❌ FAILED: {len(failed)} issues found:")
    for f in failed:
        print(f"  - {f}")
else:
    print("✅ ALL LIBRARIES VERIFIED SUCCESSFULLY")
```

Run it:
```bash
cd backend/src
python ../../../verify_libraries.py
```

---

## Integration Test Verification

After fixing libraries, run integration tests:

```bash
cd backend/src
python -m pytest tests/integration/test_integration_core.py -v

# Expected output:
# ======================== 21 passed in X.XXs ========================
```

---

## Summary of Changes

| Library | Action | Files to Create/Modify | Complexity |
|---------|--------|----------------------|------------|
| socratic_analyzer | Create analyzers/ subpackage OR fix client.py imports | 7 new files OR 1 file edit | Medium |
| socratic_rag | Create chunking/ subpackage OR fix client.py imports | 2-3 new files OR 1 file edit | Medium |
| socratic_learning | Add PatternDetector class | 2 file edits | Low |
| socratic_knowledge | Add KnowledgeBase class | 2 file edits | Low |

**Total effort**: 2-3 hours per library maximum

---

## Success Criteria

✅ All imports work without errors
✅ All 21 integration tests pass
✅ No ModuleNotFoundError
✅ No ImportError
✅ Socrates uses only library-exported APIs

