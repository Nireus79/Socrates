# IMPORT REWRITING RULES & PATTERNS
## Complete Guide to Updating Imports During Extraction

---

## OVERVIEW

When extracting code from the monolith to libraries, imports must be rewritten to:
1. Keep logic byte-for-byte identical
2. Maintain correct module references
3. Avoid circular dependencies
4. Enable libraries to function independently

---

## RULE CATEGORIES

### Category A: Intra-Library Imports (REWRITE ALWAYS)

**Pattern 1: Agent imports within agents directory**
```python
# OLD (Monolith)
from socratic_system.agents.base import Agent
from socratic_system.agents.knowledge_manager import KnowledgeManagerAgent

# NEW (Library: socratic-agents)
from .base import Agent
from .knowledge_manager import KnowledgeManagerAgent
```

**When:** Both files are being extracted to the same library
**File Locations:**
- `socratic_system/agents/base.py` → `socratic-agents/socratic_agents/base.py`
- `socratic_system/agents/multi_llm_agent.py` → `socratic-agents/socratic_agents/multi_llm_agent.py`

**Pattern 2: Core module imports within core directory**
```python
# OLD
from socratic_system.core.maturity_calculator import MaturityCalculator
from socratic_system.core.workflow_builder import WorkflowBuilder

# NEW (Library: socratic-core)
from .maturity_calculator import MaturityCalculator
from .workflow_builder import WorkflowBuilder
```

**Pattern 3: Database imports within database directory (when extracted)**
```python
# OLD
from socratic_system.database.vector_db import VectorDatabase
from socratic_system.database.embedding_cache import EmbeddingCache

# NEW (Library: socratic-rag)
from .vector_db import VectorDatabase
from .embedding_cache import EmbeddingCache
```

---

### Category B: Cross-Library Imports (REWRITE CONDITIONALLY)

**Pattern 1: Import from socratic-nexus (ClaudeClient)**
```python
# OLD (Monolith)
from socratic_system.clients import ClaudeClient

# NEW (In any library that imports it)
from socratic_nexus import ClaudeClient
```

**When:** The importing library is NOT socratic-nexus
**Files affected:**
- `socratic_knowledge/knowledge_manager.py`
- `socratic_analyzer/context_analyzer.py`
- `socratic_docs/document_processor.py`
- `socratic_rag/document_processor.py`

**Pattern 2: Import from socratic-core**
```python
# OLD
from socratic_system.core.learning_engine import LearningEngine
from socratic_system.core.maturity_calculator import MaturityCalculator

# NEW (In library that uses core)
from socratic_core import LearningEngine, MaturityCalculator
# OR
from socratic_core.learning_engine import LearningEngine
```

**When:** Library depends on core functionality
**Affected Libraries:**
- socratic-learning (uses LearningEngine)
- socratic-workflow (uses WorkflowBuilder, WorkflowOptimizer)
- socratic-performance (uses AnalyticsCalculator)
- socratic-maturity (uses MaturityCalculator)

---

### Category C: Shared Imports (KEEP AS-IS OR DEPEND)

These modules should stay accessible from the monolith (or be made into separate libraries):

**Pattern 1: Models (KEEP MONOLITH IMPORT)**
```python
# KEEP (All libraries)
from socratic_system.models import (
    User,
    ProjectContext,
    KnowledgeEntry,
    ConflictInfo,
    MaturityEvent,
)
```

**Why:** Models are data contracts used by all 12 libraries. Creating circular dependencies if copied.
**Alternative:** Create `socratic-models` library and depend on it

**Pattern 2: Config (KEEP MONOLITH IMPORT)**
```python
# KEEP (All libraries)
from socratic_system.config import SocratesConfig

# KEEP (All libraries)
from socratic_system.config.constants import VALID_PROJECT_TYPES
```

**Why:** Central configuration needed by monolith and all libraries
**Can't:** Be duplicated without causing config divergence

**Pattern 3: Exceptions (KEEP OR COPY)**
```python
# Option A: Keep monolith import
from socratic_system.exceptions import APIError, ValidationError

# Option B: Copy to library (if independence needed)
from socratic_<libname>.exceptions import APIError
```

**Recommendation:** Keep monolith import for simplicity

**Pattern 4: Events (KEEP OR COPY)**
```python
# Option A: Keep monolith import
from socratic_system.events import EventEmitter, EventType

# Option B: Create socratic-events library
from socratic_events import EventEmitter, EventType
```

**Recommendation:** Keep monolith import

**Pattern 5: Utils (KEEP OR COPY SELECTIVELY)**
```python
# Keep utility imports that are small & self-contained
from socratic_system.utils.logger import get_logger
from socratic_system.utils.id_generator import generate_id

# Copy large utilities that are library-specific
# Example: socratic-docs copies extractors/
```

---

## LIBRARY-SPECIFIC IMPORT RULES

### socratic-core
**Source Directory:** `socratic_system/core/`

**Import Patterns:**
```python
# Intra-library (REWRITE)
from socratic_system.core.maturity_calculator import MaturityCalculator
→ from .maturity_calculator import MaturityCalculator

# Shared modules (KEEP)
from socratic_system.models import ProjectContext
→ from socratic_system.models import ProjectContext

from socratic_system.exceptions import ValidationError
→ from socratic_system.exceptions import ValidationError
```

**No cross-library imports** - It's foundational

---

### socratic-nexus
**Source Directory:** `socratic_system/clients/`

**Import Patterns:**
```python
# External (KEEP)
from anthropic import Anthropic, AsyncAnthropic

# Shared (KEEP)
from socratic_system.models import User
from socratic_system.exceptions import APIError

# No intra-library imports (only 2 files)
```

---

### socratic-agents
**Source Directory:** `socratic_system/agents/` (base only)

**Import Patterns:**
```python
# Intra-library
from socratic_system.agents.base import Agent
→ from .base import Agent

from socratic_system.agents.multi_llm_agent import MultiLLMAgent
→ from .multi_llm_agent import MultiLLMAgent

# Cross-library (socratic-nexus)
from socratic_system.clients import ClaudeClient
→ from socratic_nexus import ClaudeClient

# Shared (KEEP)
from socratic_system.models import User, ProjectContext
→ from socratic_system.models import User, ProjectContext

from socratic_system.events import EventEmitter
→ from socratic_system.events import EventEmitter
```

---

### socratic-knowledge
**Source Directories:**
- `socratic_system/agents/knowledge_*`
- `socratic_system/orchestration/knowledge_base.py`
- `socratic_system/database/vector_db.py`
- `socratic_system/database/embedding_cache.py`
- `socratic_system/database/search_cache.py`

**Import Patterns:**
```python
# Intra-library (agents → database modules)
from socratic_system.agents.base import Agent
→ from .base import Agent

from socratic_system.database.vector_db import VectorDatabase
→ from .vector_db import VectorDatabase

from socratic_system.orchestration.knowledge_base import KnowledgeBase
→ from .knowledge_base import KnowledgeBase

# Cross-library (socratic-nexus)
from socratic_system.clients import ClaudeClient
→ from socratic_nexus import ClaudeClient

# Cross-library (socratic-core) - If needed
# NO CHANGE - Use monolith import or depend on socratic-core

# Shared (KEEP)
from socratic_system.models import KnowledgeEntry
→ from socratic_system.models import KnowledgeEntry
```

---

### socratic-analyzer
**Source Files:** `socratic_system/agents/context_analyzer*`, `code_generator`, `code_validation_agent`

**Import Patterns:**
```python
# Intra-library (REWRITE)
from socratic_system.agents.base import Agent
→ from .base import Agent

# Cross-library
from socratic_system.clients import ClaudeClient
→ from socratic_nexus import ClaudeClient

from socratic_system.agents.code_generator import CodeGeneratorAgent
→ from .code_generator import CodeGeneratorAgent (if in same lib)

# Shared (KEEP)
from socratic_system.models import ProjectContext
→ from socratic_system.models import ProjectContext
```

---

### socratic-conflict
**Source Directory:** `socratic_system/conflict_resolution/`

**Import Patterns:**
```python
# Intra-library
from socratic_system.conflict_resolution.base import ConflictResolver
→ from .base import ConflictResolver

from socratic_system.conflict_resolution.checkers import ConflictChecker
→ from .checkers import ConflictChecker

# Shared (KEEP)
from socratic_system.models import ConflictInfo
→ from socratic_system.models import ConflictInfo
```

**No external cross-library dependencies**

---

### socratic-learning
**Source Files:** `agents/learning_agent`, `agents/user_manager`, `core/learning_engine`

**Import Patterns:**
```python
# Intra-library
from socratic_system.agents.base import Agent
→ from .base import Agent

from socratic_system.core.learning_engine import LearningEngine
→ from .learning_engine import LearningEngine

# Cross-library (socratic-nexus)
from socratic_system.clients import ClaudeClient
→ from socratic_nexus import ClaudeClient

# Shared (KEEP)
from socratic_system.models import UserBehaviorPattern, QuestionEffectiveness
→ from socratic_system.models import UserBehaviorPattern, QuestionEffectiveness
```

---

### socratic-workflow
**Source Files:** `core/workflow_*`, `orchestration/orchestrator`

**Import Patterns:**
```python
# Intra-library
from socratic_system.core.workflow_builder import WorkflowBuilder
→ from .workflow_builder import WorkflowBuilder

from socratic_system.core.workflow_optimizer import WorkflowOptimizer
→ from .workflow_optimizer import WorkflowOptimizer

from socratic_system.orchestration.orchestrator import Orchestrator
→ from .orchestrator import Orchestrator

# Shared (KEEP)
from socratic_system.models import ProjectContext
→ from socratic_system.models import ProjectContext
```

---

### socratic-rag
**Source Files:** `database/vector_db`, `database/embedding_cache`, `database/connection_pool`, `agents/document_processor`

**Import Patterns:**
```python
# Intra-library
from socratic_system.database.vector_db import VectorDatabase
→ from .vector_db import VectorDatabase

from socratic_system.database.embedding_cache import EmbeddingCache
→ from .embedding_cache import EmbeddingCache

from socratic_system.agents.base import Agent
→ from .base import Agent

# Cross-library (socratic-nexus)
from socratic_system.clients import ClaudeClient
→ from socratic_nexus import ClaudeClient

# Shared (KEEP)
from socratic_system.config import SocratesConfig
→ from socratic_system.config import SocratesConfig
```

---

### socratic-docs
**Source Files:** `agents/document_processor`, `agents/document_context_analyzer`, `services/document_understanding`, `utils/code_structure_analyzer`, `utils/code_extractor`, `utils/extractors/*`

**Import Patterns:**
```python
# Intra-library
from socratic_system.agents.base import Agent
→ from .base import Agent

from socratic_system.utils.code_extractor import CodeExtractor
→ from .code_extractor import CodeExtractor

from socratic_system.utils.extractors.python_extractor import PythonExtractor
→ from .extractors.python_extractor import PythonExtractor

# Cross-library
from socratic_system.clients import ClaudeClient
→ from socratic_nexus import ClaudeClient

# Shared (KEEP)
from socratic_system.models import ProjectContext
→ from socratic_system.models import ProjectContext
```

---

### socratic-performance
**Source Files:** `core/analytics_calculator`, `monitoring_metrics`, `ui/analytics_display`, `ui/maturity_display`, `core/insight_categorizer`

**Import Patterns:**
```python
# Intra-library
from socratic_system.core.analytics_calculator import AnalyticsCalculator
→ from .analytics_calculator import AnalyticsCalculator

from socratic_system.core.insight_categorizer import InsightCategorizer
→ from .insight_categorizer import InsightCategorizer

# Shared (KEEP)
from socratic_system.models import TokenUsage
→ from socratic_system.models import TokenUsage

from socratic_system.events import EventEmitter
→ from socratic_system.events import EventEmitter
```

---

### socratic-maturity
**Source Files:** `core/maturity_calculator`, `core/project_categories`, `ui/maturity_display`

**Import Patterns:**
```python
# Intra-library
from socratic_system.core.maturity_calculator import MaturityCalculator
→ from .maturity_calculator import MaturityCalculator

from socratic_system.core.project_categories import get_phase_categories
→ from .project_categories import get_phase_categories

# Shared (KEEP)
from socratic_system.models import PhaseMaturity, CategoryScore
→ from socratic_system.models import PhaseMaturity, CategoryScore
```

---

## AUTOMATED IMPORT REWRITING

Create script: `C:\Users\themi\PycharmProjects\Socrates\rewrite_imports.py`

```python
#!/usr/bin/env python3
"""Automated import rewriting for library extraction."""

import re
from pathlib import Path

# Define rewrite rules per library
REWRITE_RULES = {
    'socratic-core': [
        (r'from socratic_system\.core\.', 'from .'),
    ],
    'socratic-nexus': [
        # Minimal rewrites - mostly external imports
    ],
    'socratic-agents': [
        (r'from socratic_system\.agents\.', 'from .'),
        (r'from socratic_system\.clients import ClaudeClient',
         'from socratic_nexus import ClaudeClient'),
    ],
    'socratic-knowledge': [
        (r'from socratic_system\.agents\.', 'from .'),
        (r'from socratic_system\.database\.', 'from .'),
        (r'from socratic_system\.orchestration\.', 'from .'),
        (r'from socratic_system\.clients import ClaudeClient',
         'from socratic_nexus import ClaudeClient'),
    ],
    'socratic-conflict': [
        (r'from socratic_system\.conflict_resolution\.', 'from .'),
    ],
    'socratic-rag': [
        (r'from socratic_system\.database\.', 'from .'),
        (r'from socratic_system\.agents\.', 'from .'),
        (r'from socratic_system\.clients import ClaudeClient',
         'from socratic_nexus import ClaudeClient'),
    ],
    'socratic-workflow': [
        (r'from socratic_system\.core\.', 'from .'),
        (r'from socratic_system\.orchestration\.', 'from .'),
    ],
    'socratic-analyzer': [
        (r'from socratic_system\.agents\.', 'from .'),
        (r'from socratic_system\.clients import ClaudeClient',
         'from socratic_nexus import ClaudeClient'),
    ],
    'socratic-learning': [
        (r'from socratic_system\.agents\.', 'from .'),
        (r'from socratic_system\.clients import ClaudeClient',
         'from socratic_nexus import ClaudeClient'),
    ],
    'socratic-docs': [
        (r'from socratic_system\.agents\.', 'from .'),
        (r'from socratic_system\.utils\.', 'from .'),
        (r'from socratic_system\.services\.', 'from .'),
        (r'from socratic_system\.clients import ClaudeClient',
         'from socratic_nexus import ClaudeClient'),
    ],
    'socratic-performance': [
        (r'from socratic_system\.core\.', 'from .'),
        (r'from socratic_system\.ui\.', 'from .'),
    ],
    'socratic-maturity': [
        (r'from socratic_system\.core\.', 'from .'),
        (r'from socratic_system\.ui\.', 'from .'),
    ],
}

def rewrite_imports(file_path, library_name):
    """Rewrite imports in a single file."""
    content = file_path.read_text(encoding='utf-8')
    original = content

    if library_name in REWRITE_RULES:
        for pattern, replacement in REWRITE_RULES[library_name]:
            content = re.sub(pattern, replacement, content)

    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return True
    return False

def process_library(lib_dir):
    """Process all Python files in a library."""
    lib_name = lib_dir.name
    module_dir = lib_dir / lib_name.replace('-', '_')

    rewritten = 0
    for py_file in module_dir.glob('*.py'):
        if rewrite_imports(py_file, lib_name):
            rewritten += 1

    return rewritten

def main():
    """Process all libraries."""
    base_path = Path('C:\\Users\\themi\\PycharmProjects\\Socrates')
    libraries = [
        'socratic-core', 'socratic-nexus', 'socratic-agents', 'socratic-conflict',
        'socratic-knowledge', 'socratic-analyzer', 'socratic-learning', 'socratic-workflow',
        'socratic-rag', 'socratic-docs', 'socratic-performance', 'socratic-maturity'
    ]

    for lib_name in libraries:
        lib_dir = base_path / lib_name
        if lib_dir.exists():
            count = process_library(lib_dir)
            print(f'✓ {lib_name}: {count} files rewritten')
        else:
            print(f'✗ {lib_name}: directory not found')

if __name__ == '__main__':
    main()
```

**Usage:**
```bash
cd C:\Users\themi\PycharmProjects\Socrates
python rewrite_imports.py
```

---

## VERIFICATION CHECKLIST FOR EACH FILE

After rewriting imports, verify:

```python
# ✓ NO monolith imports remain for extracted modules
# ✗ from socratic_system.core.maturity_calculator import ...
# ✓ from .maturity_calculator import ...

# ✓ Cross-library imports use correct library names
# ✗ from socratic_system.clients import ClaudeClient
# ✓ from socratic_nexus import ClaudeClient

# ✓ Shared modules use monolith imports (or socratic-models if created)
# ✓ from socratic_system.models import User
# ✓ from socratic_system.config import SocratesConfig
# ✓ from socratic_system.exceptions import APIError

# ✓ No circular imports between libraries
# ✗ socratic-agents imports from socratic-knowledge imports from socratic-agents

# ✓ Relative imports are correct
# ✓ from .base import Agent
# ✗ from ..agents.base import Agent (if in same dir)
```

---

## COMMON MISTAKES & FIXES

### Mistake 1: Over-rewriting
**Wrong:**
```python
# Original
from socratic_system.models import User

# Over-rewritten
from .models import User  # models.py doesn't exist in library!
```

**Correct:**
```python
# Keep monolith import
from socratic_system.models import User
```

### Mistake 2: Under-rewriting
**Wrong:**
```python
# File is in socratic-agents, but still references monolith
from socratic_system.agents.base import Agent
```

**Correct:**
```python
# Use relative import
from .base import Agent
```

### Mistake 3: Cross-library import errors
**Wrong:**
```python
# socratic-knowledge tries to import from socratic-analyzer
from socratic_system.agents.context_analyzer import ContextAnalyzer
```

**Correct:**
```python
# Either:
# 1. Don't import (refactor code)
# 2. Depend on socratic-analyzer in pyproject.toml
# 3. Use monolith import during transition

from socratic_analyzer import ContextAnalyzer  # Requires dependency
```

---

## TRANSITION STRATEGY

### Phase 1: Keep All Monolith Imports (Minimal Changes)
- Copy all files as-is
- Only rewrite intra-library imports
- Libraries still depend heavily on monolith

### Phase 2: Rewrite Cross-Library Imports (Medium Changes)
- Libraries import from each other via module names
- e.g., `from socratic_nexus import ClaudeClient`
- Requires adding dependencies between libraries

### Phase 3: Extract Shared Modules (Full Independence)
- Create socratic-models, socratic-events libraries
- All libraries depend on shared libraries
- Zero monolith dependency (except config)

**Recommendation:** Start with Phase 1 for safety, migrate to Phase 2 as testing increases.

---

