# COMPREHENSIVE MODULAR LIBRARY EXTRACTION PLAN
## Socrates Monolith -> 12 Modular Libraries

---

## EXECUTIVE SUMMARY

This plan extracts the Socrates monolith (`socratic_system/`) into 12 byte-for-byte identical modular libraries. Each library will contain exact copies of code from the monolith with minimal modifications to imports and dependencies.

**Total Python Files in Monolith:** 148 files
**Target: Zero Logic Divergence** - All extracted code must be functionally identical to source.

---

## PHASE 0: PREREQUISITES & SETUP

### Base Infrastructure (Extract First)

**MUST-HAVE SHARED ACROSS ALL 12 LIBRARIES:**

1. **socratic_system/exceptions/** (2 files)
   - Path: `C:\Users\themi\PycharmProjects\Socrates\socratic_system\exceptions\`
   - Files: `__init__.py`, `errors.py`
   - Status: Copy to each library OR keep monolith import
   - Recommendation: **Copy to each** (only ~50 lines, enables independence)

2. **socratic_system/models/** (11 files)
   - Path: `C:\Users\themi\PycharmProjects\Socrates\socratic_system\models\`
   - Files: user.py, project.py, knowledge.py, learning.py, maturity.py, conflict.py, note.py, monitoring.py, role.py, llm_provider.py, __init__.py
   - Status: Required by all 12 libraries
   - Recommendation: **Create separate socratic-models library** OR embed in socratic-core

3. **socratic_system/events/** (2 files)
   - Path: `C:\Users\themi\PycharmProjects\Socrates\socratic_system\events\`
   - Files: `event_emitter.py`, `event_types.py`
   - Status: Used by agents, core, performance
   - Recommendation: **Copy to core OR create socratic-events**

4. **socratic_system/config.py** (1 file)
   - Path: `C:\Users\themi\PycharmProjects\Socrates\socratic_system\config.py`
   - Used by: Almost all modules
   - Recommendation: **Keep monolith import** (provides central config)

5. **socratic_system/config/constants.py** (1 file)
   - Path: `C:\Users\themi\PycharmProjects\Socrates\socratic_system\config\constants.py`
   - Used by: Multiple libraries
   - Recommendation: **Keep monolith import**

---

## EXTRACTION DEPENDENCY TREE

```
LEVEL 0 (Base - No library dependencies):
├── exceptions/                    → Copy to each
├── models/                        → Copy or socratic-models
├── events/                        → Copy or socratic-events
└── config.py + constants.py       → Keep monolith import

LEVEL 1 (Single-module libraries):
├── socratic-nexus (clients/)
└── socratic-core (core/)

LEVEL 2 (Depends on Level 0-1):
├── socratic-rag (database/)
├── socratic-agents (agents base)
└── socratic-knowledge (agents/knowledge + orchestration/)

LEVEL 3 (Depends on Level 0-2):
├── socratic-analyzer (agents/context)
├── socratic-learning (agents/learning)
├── socratic-conflict (conflict_resolution/)
├── socratic-workflow (core/workflow)
├── socratic-docs (document processing)
├── socratic-performance (analytics)
└── socratic-maturity (maturity calculation)
```

---

## THE 12 LIBRARIES: DETAILED MAPPING

### Library 1: socratic-core
**Source Monolith:** `C:\Users\themi\PycharmProjects\Socrates\socratic_system\core\`
**Target Library:** `socratic-core/socratic_core/`
**Files:** 11 core modules
**Priority:** EXTRACT FIRST (Level 1)

**Files to Copy:**
```
1. C:\...\socratic_system\core\__init__.py                    → socratic_core/__init__.py
2. C:\...\socratic_system\core\analytics_calculator.py        → socratic_core/analytics_calculator.py
3. C:\...\socratic_system\core\insight_categorizer.py         → socratic_core/insight_categorizer.py
4. C:\...\socratic_system\core\learning_engine.py             → socratic_core/learning_engine.py
5. C:\...\socratic_system\core\maturity_calculator.py          → socratic_core/maturity_calculator.py
6. C:\...\socratic_system\core\project_categories.py           → socratic_core/project_categories.py
7. C:\...\socratic_system\core\question_selector.py            → socratic_core/question_selector.py
8. C:\...\socratic_system\core\workflow_builder.py             → socratic_core/workflow_builder.py
9. C:\...\socratic_system\core\workflow_cost_calculator.py     → socratic_core/workflow_cost_calculator.py
10. C:\...\socratic_system\core\workflow_optimizer.py          → socratic_core/workflow_optimizer.py
11. C:\...\socratic_system\core\workflow_path_finder.py        → socratic_core/workflow_path_finder.py
12. C:\...\socratic_system\core\workflow_risk_calculator.py    → socratic_core/workflow_risk_calculator.py
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-core/socratic_core`
2. Copy all files: `cp -r socratic_system/core/*.py socratic-core/socratic_core/`
3. Update imports in each file:
   - Keep: `from socratic_system.models import ...` (shared)
   - Keep: `from socratic_system.config import ...` (shared)
   - Keep: `from socratic_system.exceptions import ...` (or copy)
   - Keep: `from socratic_system.events import ...` (or copy)
4. Create `socratic-core/__init__.py`:
   ```python
   from .socratic_core import *
   ```
5. Create `socratic-core/pyproject.toml`:
   ```toml
   [project]
   name = "socratic-core"
   version = "1.0.0"
   dependencies = [
       "anthropic>=0.25.0",
       "pydantic>=2.0.0",
       "numpy>=1.20.0",
   ]
   ```

**Verification:**
- [ ] File count: 12 files
- [ ] Run: `python -c "from socratic_core import MaturityCalculator"`
- [ ] No syntax errors: `python -m py_compile socratic_core/*.py`
- [ ] Imports resolve

**Dependencies:** None (Level 1)

---

### Library 2: socratic-nexus
**Source Monolith:** `C:\Users\themi\PycharmProjects\Socrates\socratic_system\clients\`
**Target Library:** `socratic-nexus/socratic_nexus/`
**Files:** 2 files
**Priority:** EXTRACT FIRST (Level 1)

**Files to Copy:**
```
1. C:\...\socratic_system\clients\__init__.py         → socratic_nexus/__init__.py
2. C:\...\socratic_system\clients\claude_client.py    → socratic_nexus/claude_client.py
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-nexus/socratic_nexus`
2. Copy files exactly
3. Update imports:
   - Keep external: `from anthropic import ...`
   - Keep shared: `from socratic_system.models import ...`
   - Keep shared: `from socratic_system.exceptions import ...`
4. Create `socratic-nexus/pyproject.toml`

**Verification:**
- [ ] File count: 2 files
- [ ] Run: `python -c "from socratic_nexus import ClaudeClient"`
- [ ] Instantiation works with mock API key

**Dependencies:** None (Level 1)

---

### Library 3: socratic-agents
**Source Monolith:** `C:\Users\themi\PycharmProjects\Socrates\socratic_system\agents\`
**Target Library:** `socratic-agents/socratic_agents/`
**Files:** 6 core files (others go to specialized libraries)
**Priority:** EXTRACT 2ND (Level 2)

**Files to Copy:**
```
1. C:\...\socratic_system\agents\__init__.py                 → socratic_agents/__init__.py
2. C:\...\socratic_system\agents\base.py                     → socratic_agents/base.py
3. C:\...\socratic_system\agents\multi_llm_agent.py          → socratic_agents/multi_llm_agent.py
4. C:\...\socratic_system\agents\socratic_counselor.py       → socratic_agents/socratic_counselor.py
5. C:\...\socratic_system\agents\note_manager.py             → socratic_agents/note_manager.py
6. C:\...\socratic_system\agents\quality_controller.py       → socratic_agents/quality_controller.py
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-agents/socratic_agents`
2. Copy 6 files
3. Update base.py to:
   - Keep imports from socratic_system
   - Import ClaudeClient from socratic_nexus if needed
4. Create __init__.py

**Verification:**
- [ ] File count: 6
- [ ] Run: `python -c "from socratic_agents import Agent"`
- [ ] Can instantiate base Agent

**Dependencies:** socratic-nexus

---

### Library 4: socratic-knowledge
**Source Monolith:**
- `C:\...\socratic_system\agents\knowledge_manager.py`
- `C:\...\socratic_system\agents\knowledge_analysis.py`
- `C:\...\socratic_system\orchestration\knowledge_base.py`
- `C:\...\socratic_system\database\vector_db.py`
- `C:\...\socratic_system\database\embedding_cache.py`
- `C:\...\socratic_system\database\search_cache.py`

**Target Library:** `socratic-knowledge/socratic_knowledge/`
**Files:** 6 files
**Priority:** EXTRACT 3RD (Level 3)

**Files to Copy:**
```
1. C:\...\socratic_system\agents\knowledge_manager.py        → socratic_knowledge/knowledge_manager.py
2. C:\...\socratic_system\agents\knowledge_analysis.py       → socratic_knowledge/knowledge_analysis.py
3. C:\...\socratic_system\orchestration\knowledge_base.py    → socratic_knowledge/knowledge_base.py
4. C:\...\socratic_system\database\vector_db.py              → socratic_knowledge/vector_db.py
5. C:\...\socratic_system\database\embedding_cache.py        → socratic_knowledge/embedding_cache.py
6. C:\...\socratic_system\database\search_cache.py           → socratic_knowledge/search_cache.py
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-knowledge/socratic_knowledge`
2. Copy all 6 files
3. Copy base agent: `cp socratic_system/agents/base.py socratic-knowledge/socratic_knowledge/`
4. Update imports:
   - `from socratic_system.agents.base` → `from .base import Agent`
   - `from socratic_system.database` → local imports
   - `from socratic_system.clients` → `from socratic_nexus import ClaudeClient`
5. Create __init__.py with exports

**Verification:**
- [ ] File count: 7 (6 + base.py)
- [ ] Run: `python -c "from socratic_knowledge import KnowledgeManagerAgent"`
- [ ] Vector DB initializes
- [ ] Embedding cache works

**Dependencies:** socratic-nexus, socratic-core (optional)

---

### Library 5: socratic-analyzer
**Source Monolith:** `C:\...\socratic_system\agents\`
**Target Library:** `socratic-analyzer/socratic_analyzer/`
**Files:** 4 files
**Priority:** EXTRACT 3RD (Level 3)

**Files to Copy:**
```
1. C:\...\socratic_system\agents\context_analyzer.py           → socratic_analyzer/context_analyzer.py
2. C:\...\socratic_system\agents\document_context_analyzer.py  → socratic_analyzer/document_context_analyzer.py
3. C:\...\socratic_system\agents\code_generator.py             → socratic_analyzer/code_generator.py
4. C:\...\socratic_system\agents\code_validation_agent.py      → socratic_analyzer/code_validation_agent.py
5. (ALSO COPY) base.py                                          → socratic_analyzer/base.py
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-analyzer/socratic_analyzer`
2. Copy all 5 files
3. Update imports for local base.py
4. Update imports for socratic_nexus

**Verification:**
- [ ] File count: 5
- [ ] Run: `python -c "from socratic_analyzer import ContextAnalyzerAgent"`
- [ ] Agent instantiation works

**Dependencies:** socratic-agents (for base)

---

### Library 6: socratic-conflict
**Source Monolith:** `C:\Users\themi\PycharmProjects\Socrates\socratic_system\conflict_resolution\`
**Target Library:** `socratic-conflict/socratic_conflict/`
**Files:** 4 files
**Priority:** EXTRACT 2ND (Level 2)

**Files to Copy:**
```
1. C:\...\socratic_system\conflict_resolution\__init__.py    → socratic_conflict/__init__.py
2. C:\...\socratic_system\conflict_resolution\base.py        → socratic_conflict/base.py
3. C:\...\socratic_system\conflict_resolution\checkers.py    → socratic_conflict/checkers.py
4. C:\...\socratic_system\conflict_resolution\rules.py       → socratic_conflict/rules.py
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-conflict/socratic_conflict`
2. Copy all 4 files
3. Update imports (fairly self-contained)
4. Create __init__.py

**Verification:**
- [ ] File count: 4
- [ ] Run: `python -c "from socratic_conflict import *"`
- [ ] Conflict checkers work

**Dependencies:** None (Level 2)

---

### Library 7: socratic-workflow
**Source Monolith:** `C:\...\socratic_system\core\` (workflow_* files) + `orchestration/`
**Target Library:** `socratic-workflow/socratic_workflow/`
**Files:** 6 files
**Priority:** EXTRACT 2ND (Level 2)

**Files to Copy:**
```
1. C:\...\socratic_system\core\workflow_builder.py            → socratic_workflow/workflow_builder.py
2. C:\...\socratic_system\core\workflow_optimizer.py          → socratic_workflow/workflow_optimizer.py
3. C:\...\socratic_system\core\workflow_path_finder.py        → socratic_workflow/workflow_path_finder.py
4. C:\...\socratic_system\core\workflow_cost_calculator.py    → socratic_workflow/workflow_cost_calculator.py
5. C:\...\socratic_system\core\workflow_risk_calculator.py    → socratic_workflow/workflow_risk_calculator.py
6. C:\...\socratic_system\orchestration\orchestrator.py       → socratic_workflow/orchestrator.py
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-workflow/socratic_workflow`
2. Copy 6 files
3. Update imports (mostly local)

**Verification:**
- [ ] File count: 6
- [ ] Run: `python -c "from socratic_workflow import WorkflowBuilder"`
- [ ] Workflow building works

**Dependencies:** socratic-core

---

### Library 8: socratic-rag
**Source Monolith:** `C:\...\socratic_system\database\`
**Target Library:** `socratic-rag/socratic_rag/`
**Files:** 4 files + base.py
**Priority:** EXTRACT 2ND (Level 2)

**Files to Copy:**
```
1. C:\...\socratic_system\database\vector_db.py              → socratic_rag/vector_db.py
2. C:\...\socratic_system\database\embedding_cache.py        → socratic_rag/embedding_cache.py
3. C:\...\socratic_system\database\connection_pool.py        → socratic_rag/connection_pool.py
4. C:\...\socratic_system\agents\document_processor.py       → socratic_rag/document_processor.py
5. C:\...\socratic_system\agents\base.py                     → socratic_rag/base.py
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-rag/socratic_rag`
2. Copy all 5 files
3. Update imports

**Verification:**
- [ ] File count: 5
- [ ] Run: `python -c "from socratic_rag import VectorDatabase"`
- [ ] Database initializes

**Dependencies:** socratic-nexus

---

### Library 9: socratic-learning
**Source Monolith:** `agents/learning_agent.py`, `agents/user_manager.py`, `core/learning_engine.py`
**Target Library:** `socratic-learning/socratic_learning/`
**Files:** 3 files + base.py
**Priority:** EXTRACT 3RD (Level 3)

**Files to Copy:**
```
1. C:\...\socratic_system\agents\learning_agent.py         → socratic_learning/learning_agent.py
2. C:\...\socratic_system\agents\user_manager.py           → socratic_learning/user_manager.py
3. C:\...\socratic_system\core\learning_engine.py          → socratic_learning/learning_engine.py
4. C:\...\socratic_system\agents\base.py                   → socratic_learning/base.py
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-learning/socratic_learning`
2. Copy 4 files
3. Update imports

**Verification:**
- [ ] File count: 4
- [ ] Run: `python -c "from socratic_learning import UserLearningAgent"`

**Dependencies:** socratic-core, socratic-agents

---

### Library 10: socratic-docs
**Source Monolith:** Document processing modules
**Target Library:** `socratic-docs/socratic_docs/`
**Files:** 5+ files
**Priority:** EXTRACT 3RD (Level 3)

**Files to Copy:**
```
1. C:\...\socratic_system\agents\document_processor.py        → socratic_docs/document_processor.py
2. C:\...\socratic_system\agents\document_context_analyzer.py → socratic_docs/document_context_analyzer.py
3. C:\...\socratic_system\services\document_understanding.py  → socratic_docs/document_understanding.py
4. C:\...\socratic_system\utils\code_structure_analyzer.py    → socratic_docs/code_structure_analyzer.py
5. C:\...\socratic_system\utils\code_extractor.py             → socratic_docs/code_extractor.py
6. C:\...\socratic_system\agents\base.py                      → socratic_docs/base.py
7. C:\...\socratic_system\utils\extractors\*                  → socratic_docs/extractors/
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-docs/socratic_docs`
2. Copy all files
3. Copy utils/extractors directory entirely

**Verification:**
- [ ] Run: `python -c "from socratic_docs import DocumentProcessorAgent"`

**Dependencies:** socratic-agents, socratic-nexus

---

### Library 11: socratic-performance
**Source Monolith:** Analytics and monitoring
**Target Library:** `socratic-performance/socratic_performance/`
**Files:** 5 files
**Priority:** EXTRACT 3RD (Level 3)

**Files to Copy:**
```
1. C:\...\socratic_system\core\analytics_calculator.py        → socratic_performance/analytics_calculator.py
2. C:\...\socratic_system\monitoring_metrics.py               → socratic_performance/monitoring_metrics.py
3. C:\...\socratic_system\ui\analytics_display.py             → socratic_performance/analytics_display.py
4. C:\...\socratic_system\ui\maturity_display.py              → socratic_performance/maturity_display.py
5. C:\...\socratic_system\core\insight_categorizer.py         → socratic_performance/insight_categorizer.py
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-performance/socratic_performance`
2. Copy 5 files

**Verification:**
- [ ] Run: `python -c "from socratic_performance import AnalyticsCalculator"`

**Dependencies:** socratic-core

---

### Library 12: socratic-maturity
**Source Monolith:** Maturity calculation
**Target Library:** `socratic-maturity/socratic_maturity/`
**Files:** 3 files
**Priority:** EXTRACT 3RD (Level 3)

**Files to Copy:**
```
1. C:\...\socratic_system\core\maturity_calculator.py         → socratic_maturity/maturity_calculator.py
2. C:\...\socratic_system\core\project_categories.py          → socratic_maturity/project_categories.py
3. C:\...\socratic_system\ui\maturity_display.py              → socratic_maturity/maturity_display.py
```

**Extraction Steps:**
1. Create directory: `mkdir -p socratic-maturity/socratic_maturity`
2. Copy 3 files

**Verification:**
- [ ] Run: `python -c "from socratic_maturity import MaturityCalculator"`

**Dependencies:** socratic-core

---

## EXECUTION SEQUENCE

### BATCH 1 (Parallel - No Dependencies)
**Time: ~1 hour**
- [ ] socratic-core (11 files)
- [ ] socratic-nexus (2 files)
- [ ] socratic-conflict (4 files)

### BATCH 2 (Parallel - After Batch 1)
**Time: ~1 hour**
- [ ] socratic-agents (6 files)
- [ ] socratic-rag (5 files)
- [ ] socratic-workflow (6 files)

### BATCH 3 (Parallel - After Batch 2)
**Time: ~2 hours**
- [ ] socratic-knowledge (7 files)
- [ ] socratic-analyzer (5 files)
- [ ] socratic-learning (4 files)
- [ ] socratic-docs (7+ files)
- [ ] socratic-performance (5 files)
- [ ] socratic-maturity (3 files)

---

## VERIFICATION STRATEGY

### For Each Library:

1. **Syntax Check:**
   ```bash
   python -m py_compile socratic_<lib>/*.py
   ```

2. **Import Check:**
   ```bash
   python -c "from socratic_<lib> import *"
   ```

3. **Logic Preservation:**
   - Compare file counts
   - Verify no functions/classes removed
   - Spot-check critical logic

4. **Integration Check:**
   ```bash
   python test_all_libraries.py
   ```

---

## SUCCESS CRITERIA

✓ All 12 libraries extracted
✓ 59+ total files copied
✓ Zero logic divergence verified
✓ All imports resolve
✓ No circular dependencies
✓ Each library standalone-testable
✓ Integration tests pass
✓ Monolith and extracted libraries behave identically

