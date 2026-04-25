# EXTRACTION QUICK REFERENCE
## One-Page Execution Checklist

---

## FILE LOCATIONS (Source Files in Monolith)

```
C:\Users\themi\PycharmProjects\Socrates\socratic_system\
├── agents/                           (23 files) ──→ distributed to 5 libraries
├── clients/                          (2 files)  ──→ socratic-nexus
├── conflict_resolution/              (4 files)  ──→ socratic-conflict
├── core/                             (12 files) ──→ socratic-core (+ split to others)
├── database/                         (10 files) ──→ socratic-rag + socratic-knowledge
├── events/                           (2 files)  ──→ keep monolith import
├── exceptions/                       (2 files)  ──→ keep monolith import
├── models/                           (11 files) ──→ keep monolith import
├── orchestration/                    (2 files)  ──→ socratic-workflow + socratic-knowledge
├── config.py + config/               (2 files)  ──→ keep monolith import
└── utils/                            (partial)  ──→ distribute as needed
```

---

## LIBRARY EXTRACTION ORDER

### BATCH 1 (Start with these - no dependencies)
```
1. socratic-core          11 files from core/
2. socratic-nexus         2 files from clients/
3. socratic-conflict      4 files from conflict_resolution/
```

### BATCH 2 (After Batch 1 ready)
```
4. socratic-agents        6 files from agents/ + base.py
5. socratic-rag           5 files (database + agent)
6. socratic-workflow      6 files from core/ + orchestration/
```

### BATCH 3 (After Batch 2 ready)
```
7. socratic-knowledge     7 files (agents + orchestration + database)
8. socratic-analyzer      5 files from agents/
9. socratic-learning      4 files (agents + core)
10. socratic-docs         7+ files (agents + services + utils)
11. socratic-performance  5 files (core + ui)
12. socratic-maturity     3 files (core + ui)
```

---

## COPY COMMANDS (BATCH 1)

### socratic-core
```bash
mkdir socratic-core\socratic_core
copy socratic_system\core\*.py socratic-core\socratic_core\
# Creates: 12 files
```

### socratic-nexus
```bash
mkdir socratic-nexus\socratic_nexus
copy socratic_system\clients\*.py socratic-nexus\socratic_nexus\
# Creates: 2 files
```

### socratic-conflict
```bash
mkdir socratic-conflict\socratic_conflict
copy socratic_system\conflict_resolution\*.py socratic-conflict\socratic_conflict\
# Creates: 4 files
```

---

## COPY COMMANDS (BATCH 2)

### socratic-agents
```bash
mkdir socratic-agents\socratic_agents
copy socratic_system\agents\__init__.py socratic-agents\socratic_agents\
copy socratic_system\agents\base.py socratic-agents\socratic_agents\
copy socratic_system\agents\multi_llm_agent.py socratic-agents\socratic_agents\
copy socratic_system\agents\socratic_counselor.py socratic-agents\socratic_agents\
copy socratic_system\agents\note_manager.py socratic-agents\socratic_agents\
copy socratic_system\agents\quality_controller.py socratic-agents\socratic_agents\
# Creates: 6 files
```

### socratic-rag
```bash
mkdir socratic-rag\socratic_rag
copy socratic_system\database\vector_db.py socratic-rag\socratic_rag\
copy socratic_system\database\embedding_cache.py socratic-rag\socratic_rag\
copy socratic_system\database\connection_pool.py socratic-rag\socratic_rag\
copy socratic_system\agents\document_processor.py socratic-rag\socratic_rag\
copy socratic_system\agents\base.py socratic-rag\socratic_rag\
# Creates: 5 files
```

### socratic-workflow
```bash
mkdir socratic-workflow\socratic_workflow
copy socratic_system\core\workflow_builder.py socratic-workflow\socratic_workflow\
copy socratic_system\core\workflow_optimizer.py socratic-workflow\socratic_workflow\
copy socratic_system\core\workflow_path_finder.py socratic-workflow\socratic_workflow\
copy socratic_system\core\workflow_cost_calculator.py socratic-workflow\socratic_workflow\
copy socratic_system\core\workflow_risk_calculator.py socratic-workflow\socratic_workflow\
copy socratic_system\orchestration\orchestrator.py socratic-workflow\socratic_workflow\
# Creates: 6 files
```

---

## COPY COMMANDS (BATCH 3)

### socratic-knowledge
```bash
mkdir socratic-knowledge\socratic_knowledge
copy socratic_system\agents\knowledge_manager.py socratic-knowledge\socratic_knowledge\
copy socratic_system\agents\knowledge_analysis.py socratic-knowledge\socratic_knowledge\
copy socratic_system\orchestration\knowledge_base.py socratic-knowledge\socratic_knowledge\
copy socratic_system\database\vector_db.py socratic-knowledge\socratic_knowledge\
copy socratic_system\database\embedding_cache.py socratic-knowledge\socratic_knowledge\
copy socratic_system\database\search_cache.py socratic-knowledge\socratic_knowledge\
copy socratic_system\agents\base.py socratic-knowledge\socratic_knowledge\
# Creates: 7 files
```

### socratic-analyzer
```bash
mkdir socratic-analyzer\socratic_analyzer
copy socratic_system\agents\context_analyzer.py socratic-analyzer\socratic_analyzer\
copy socratic_system\agents\document_context_analyzer.py socratic-analyzer\socratic_analyzer\
copy socratic_system\agents\code_generator.py socratic-analyzer\socratic_analyzer\
copy socratic_system\agents\code_validation_agent.py socratic-analyzer\socratic_analyzer\
copy socratic_system\agents\base.py socratic-analyzer\socratic_analyzer\
# Creates: 5 files
```

### socratic-learning
```bash
mkdir socratic-learning\socratic_learning
copy socratic_system\agents\learning_agent.py socratic-learning\socratic_learning\
copy socratic_system\agents\user_manager.py socratic-learning\socratic_learning\
copy socratic_system\core\learning_engine.py socratic-learning\socratic_learning\
copy socratic_system\agents\base.py socratic-learning\socratic_learning\
# Creates: 4 files
```

### socratic-docs
```bash
mkdir socratic-docs\socratic_docs
copy socratic_system\agents\document_processor.py socratic-docs\socratic_docs\
copy socratic_system\agents\document_context_analyzer.py socratic-docs\socratic_docs\
copy socratic_system\services\document_understanding.py socratic-docs\socratic_docs\
copy socratic_system\utils\code_structure_analyzer.py socratic-docs\socratic_docs\
copy socratic_system\utils\code_extractor.py socratic-docs\socratic_docs\
copy socratic_system\agents\base.py socratic-docs\socratic_docs\
xcopy socratic_system\utils\extractors socratic-docs\socratic_docs\extractors\ /E /I /Y
# Creates: 7+ files
```

### socratic-performance
```bash
mkdir socratic-performance\socratic_performance
copy socratic_system\core\analytics_calculator.py socratic-performance\socratic_performance\
copy socratic_system\monitoring_metrics.py socratic-performance\socratic_performance\
copy socratic_system\ui\analytics_display.py socratic-performance\socratic_performance\
copy socratic_system\ui\maturity_display.py socratic-performance\socratic_performance\
copy socratic_system\core\insight_categorizer.py socratic-performance\socratic_performance\
# Creates: 5 files
```

### socratic-maturity
```bash
mkdir socratic-maturity\socratic_maturity
copy socratic_system\core\maturity_calculator.py socratic-maturity\socratic_maturity\
copy socratic_system\core\project_categories.py socratic-maturity\socratic_maturity\
copy socratic_system\ui\maturity_display.py socratic-maturity\socratic_maturity\
# Creates: 3 files
```

---

## KEY IMPORT REWRITES

### Always Rewrite (Intra-library)
```python
from socratic_system.core.X import Y
→ from .X import Y (if in socratic-core)

from socratic_system.agents.base import Agent
→ from .base import Agent (if in same library)
```

### Always Rewrite (Cross-library)
```python
from socratic_system.clients import ClaudeClient
→ from socratic_nexus import ClaudeClient
```

### Keep As-Is (Shared)
```python
from socratic_system.models import ...      # KEEP
from socratic_system.config import ...      # KEEP
from socratic_system.exceptions import ...  # KEEP
from socratic_system.events import ...      # KEEP
```

---

## POST-COPY VERIFICATION

### Step 1: Syntax Check
```bash
cd C:\Users\themi\PycharmProjects\Socrates
for /r socratic-core /F %%F in (*.py) do python -m py_compile "%%F"
# Repeat for each library
```

### Step 2: Import Test
```bash
python -c "import sys; sys.path.insert(0, '.'); from socratic_core import MaturityCalculator; print('OK')"
python -c "import sys; sys.path.insert(0, '.'); from socratic_nexus import ClaudeClient; print('OK')"
# ... etc for all 12
```

### Step 3: File Count Check
```
socratic-core:        12 files ✓
socratic-nexus:       2 files ✓
socratic-agents:      6 files ✓
socratic-conflict:    4 files ✓
socratic-knowledge:   7 files ✓
socratic-analyzer:    5 files ✓
socratic-learning:    4 files ✓
socratic-workflow:    6 files ✓
socratic-rag:         5 files ✓
socratic-docs:        7+ files ✓
socratic-performance: 5 files ✓
socratic-maturity:    3 files ✓
TOTAL:               59+ files
```

---

## CRITICAL SUCCESS CRITERIA

- [ ] All 12 library directories created
- [ ] All source files copied byte-for-byte
- [ ] No syntax errors in any library
- [ ] All import statements rewritten correctly
- [ ] All libraries can be imported: `from socratic_<lib> import ...`
- [ ] No circular dependencies detected
- [ ] File counts match expected values
- [ ] Each library has __init__.py and pyproject.toml
- [ ] Documentation updated
- [ ] Integration tests pass

---

## DEPENDENCY GRAPH

```
            Models, Config, Exceptions, Events
                    (from monolith)
                          ↑
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
   socratic-core   socratic-nexus  socratic-conflict
        ↑                 ↑
        │        ┌────────┼────────┐
        │        ↓        ↓        ↓
        └────  socratic-agents ──→ others
                  ↑
        ┌─────────┼──────────────────┐
        ↓         ↓                  ↓
    socratic-   socratic-        socratic-
    knowledge   analyzer          rag
        ↑         ↑                ↑
        └─────┬───┴────────────────┘
              ↓
        socratic-learning
        socratic-docs
        socratic-workflow
        socratic-performance
        socratic-maturity
```

---

## TIME ESTIMATES

| Phase | Libraries | Files | Time |
|-------|-----------|-------|------|
| Batch 1 | 3 | 18 | 15 min |
| Batch 2 | 3 | 17 | 20 min |
| Batch 3 | 6 | 27 | 30 min |
| Verification | All | - | 15 min |
| **TOTAL** | **12** | **62** | **80 min** |

---

## NEXT STEPS AFTER EXTRACTION

1. Create pyproject.toml for each library
2. Create __init__.py wrapper in each library root
3. Create README.md for each library
4. Update imports in all files
5. Run syntax checks
6. Run import tests
7. Run integration tests
8. Document API for each library
9. Set up CI/CD for each library
10. Publish to package registry (optional)

---

## EMERGENCY ROLLBACK

If extraction fails:
```bash
# Delete all extracted libraries
rm -r socratic-core socratic-nexus socratic-agents ...
# Monolith remains unchanged
git checkout .
```

---

## SUCCESS EXAMPLE OUTPUT

```
✓ socratic-core imported successfully
✓ socratic-nexus imported successfully
✓ socratic-agents imported successfully
✓ socratic-conflict imported successfully
✓ socratic-knowledge imported successfully
✓ socratic-analyzer imported successfully
✓ socratic-learning imported successfully
✓ socratic-workflow imported successfully
✓ socratic-rag imported successfully
✓ socratic-docs imported successfully
✓ socratic-performance imported successfully
✓ socratic-maturity imported successfully

12/12 libraries verified
62 total files extracted
Zero logic divergence
Ready for production
```

---

