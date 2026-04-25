# STEP-BY-STEP LIBRARY EXTRACTION GUIDE
## Line-by-Line Execution Instructions

---

## PHASE 0: SETUP (Do This First)

### Step 0.1: Create Directory Structure
```bash
cd C:\Users\themi\PycharmProjects\Socrates

# Create parent directories for all 12 libraries
mkdir socratic-core
mkdir socratic-nexus
mkdir socratic-agents
mkdir socratic-conflict
mkdir socratic-knowledge
mkdir socratic-analyzer
mkdir socratic-learning
mkdir socratic-workflow
mkdir socratic-rag
mkdir socratic-docs
mkdir socratic-performance
mkdir socratic-maturity

# Inside each, create the package directory
mkdir socratic-core\socratic_core
mkdir socratic-nexus\socratic_nexus
mkdir socratic-agents\socratic_agents
mkdir socratic-conflict\socratic_conflict
mkdir socratic-knowledge\socratic_knowledge
mkdir socratic-analyzer\socratic_analyzer
mkdir socratic-learning\socratic_learning
mkdir socratic-workflow\socratic_workflow
mkdir socratic-rag\socratic_rag
mkdir socratic-docs\socratic_docs
mkdir socratic-performance\socratic_performance
mkdir socratic-maturity\socratic_maturity
```

### Step 0.2: Create Base pyproject.toml Template
**File:** `C:\Users\themi\PycharmProjects\Socrates\LIBRARY_BASE_TEMPLATE.toml`

```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "socratic-<LIBNAME>"
version = "1.0.0"
description = "Modular <LIBNAME> library extracted from Socrates monolith"
readme = "README.md"
requires-python = ">=3.9"
authors = [
    {name = "Socrates Team", email = "team@socrates.ai"}
]
dependencies = [
    # Override per library
]

[project.urls]
Homepage = "https://github.com/your-org/socratic-<LIBNAME>"
Repository = "https://github.com/your-org/socratic-<LIBNAME>.git"

[tool.setuptools.packages.find]
where = ["."]
include = ["socratic_<LIBNAME>*"]
```

### Step 0.3: Verification Scripts
Create `C:\Users\themi\PycharmProjects\Socrates\verify_extraction.py`:

```python
#!/usr/bin/env python3
"""Verify library extractions are complete and correct."""

import os
import sys
from pathlib import Path

LIBRARIES = {
    'socratic-core': 12,
    'socratic-nexus': 2,
    'socratic-agents': 6,
    'socratic-conflict': 4,
    'socratic-knowledge': 7,
    'socratic-analyzer': 5,
    'socratic-learning': 4,
    'socratic-workflow': 6,
    'socratic-rag': 5,
    'socratic-docs': 7,
    'socratic-performance': 5,
    'socratic-maturity': 3,
}

def verify_library(lib_name, expected_count):
    """Verify a library has correct file count."""
    lib_dir = Path(lib_name) / lib_name.replace('-', '_')
    py_files = list(lib_dir.glob('*.py'))

    if len(py_files) >= expected_count:
        print(f"✓ {lib_name}: {len(py_files)} files (expected {expected_count})")
        return True
    else:
        print(f"✗ {lib_name}: {len(py_files)} files (expected {expected_count})")
        return False

def main():
    """Verify all libraries."""
    os.chdir('C:\\Users\\themi\\PycharmProjects\\Socrates')

    passed = sum(verify_library(lib, count) for lib, count in LIBRARIES.items())
    total = len(LIBRARIES)

    print(f"\n{passed}/{total} libraries verified")
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
```

---

## BATCH 1: EXTRACT CORE LIBRARIES (Parallel)

### Library 1.1: socratic-core

#### Step 1.1.1: Copy Core Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

# Copy all 12 files from core/
copy socratic_system\core\__init__.py socratic-core\socratic_core\
copy socratic_system\core\analytics_calculator.py socratic-core\socratic_core\
copy socratic_system\core\insight_categorizer.py socratic-core\socratic_core\
copy socratic_system\core\learning_engine.py socratic-core\socratic_core\
copy socratic_system\core\maturity_calculator.py socratic-core\socratic_core\
copy socratic_system\core\project_categories.py socratic-core\socratic_core\
copy socratic_system\core\question_selector.py socratic-core\socratic_core\
copy socratic_system\core\workflow_builder.py socratic-core\socratic_core\
copy socratic_system\core\workflow_cost_calculator.py socratic-core\socratic_core\
copy socratic_system\core\workflow_optimizer.py socratic-core\socratic_core\
copy socratic_system\core\workflow_path_finder.py socratic-core\socratic_core\
copy socratic_system\core\workflow_risk_calculator.py socratic-core\socratic_core\
```

#### Step 1.1.2: Verify Syntax
```bash
cd socratic-core
python -m py_compile socratic_core\*.py
# Should complete with no errors
```

#### Step 1.1.3: Create __init__.py (Wrapper)
**File:** `C:\Users\themi\PycharmProjects\Socrates\socratic-core\__init__.py`
```python
"""Socratic Core Module - Exported from monolith"""
from .socratic_core import *
```

#### Step 1.1.4: Create pyproject.toml
**File:** `C:\Users\themi\PycharmProjects\Socrates\socratic-core\pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "socratic-core"
version = "1.0.0"
description = "Core calculation module for Socrates"
requires-python = ">=3.9"
dependencies = [
    "anthropic>=0.25.0",
    "pydantic>=2.0.0",
    "numpy>=1.20.0",
]
```

#### Step 1.1.5: Test Import
```bash
cd C:\Users\themi\PycharmProjects\Socrates
python -c "import sys; sys.path.insert(0, '.'); from socratic_core import MaturityCalculator; print('✓ socratic-core imported')"
```

**Expected Output:**
```
✓ socratic-core imported
```

---

### Library 1.2: socratic-nexus

#### Step 1.2.1: Copy Client Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

copy socratic_system\clients\__init__.py socratic-nexus\socratic_nexus\
copy socratic_system\clients\claude_client.py socratic-nexus\socratic_nexus\
```

#### Step 1.2.2: Verify Syntax
```bash
cd socratic-nexus
python -m py_compile socratic_nexus\*.py
```

#### Step 1.2.3: Create pyproject.toml
**File:** `C:\Users\themi\PycharmProjects\Socrates\socratic-nexus\pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "socratic-nexus"
version = "1.0.0"
description = "Claude API client for Socrates"
requires-python = ">=3.9"
dependencies = [
    "anthropic>=0.25.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
]
```

#### Step 1.2.4: Test Import
```bash
cd C:\Users\themi\PycharmProjects\Socrates
python -c "import sys; sys.path.insert(0, '.'); from socratic_nexus import ClaudeClient; print('✓ socratic-nexus imported')"
```

---

### Library 1.3: socratic-conflict

#### Step 1.3.1: Copy Conflict Resolution Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

copy socratic_system\conflict_resolution\__init__.py socratic-conflict\socratic_conflict\
copy socratic_system\conflict_resolution\base.py socratic-conflict\socratic_conflict\
copy socratic_system\conflict_resolution\checkers.py socratic-conflict\socratic_conflict\
copy socratic_system\conflict_resolution\rules.py socratic-conflict\socratic_conflict\
```

#### Step 1.3.2: Verify & Test
```bash
cd socratic-conflict
python -m py_compile socratic_conflict\*.py

cd C:\Users\themi\PycharmProjects\Socrates
python -c "import sys; sys.path.insert(0, '.'); from socratic_conflict import *; print('✓ socratic-conflict imported')"
```

---

## BATCH 2: EXTRACT SECONDARY LIBRARIES (Parallel)

### Library 2.1: socratic-agents

#### Step 2.1.1: Copy Agent Base and Core Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

copy socratic_system\agents\__init__.py socratic-agents\socratic_agents\
copy socratic_system\agents\base.py socratic-agents\socratic_agents\
copy socratic_system\agents\multi_llm_agent.py socratic-agents\socratic_agents\
copy socratic_system\agents\socratic_counselor.py socratic-agents\socratic_agents\
copy socratic_system\agents\note_manager.py socratic-agents\socratic_agents\
copy socratic_system\agents\quality_controller.py socratic-agents\socratic_agents\
```

#### Step 2.1.2: Update __init__.py Imports
**File:** `C:\Users\themi\PycharmProjects\Socrates\socratic-agents\socratic_agents\__init__.py`

Read original:
```python
# Original has imports from socratic_system.agents
from .base import Agent
from .multi_llm_agent import MultiLLMAgent
# ... etc
```

Make sure it's all local imports (starting with `.`)

#### Step 2.1.3: Test Import
```bash
cd C:\Users\themi\PycharmProjects\Socrates
python -c "import sys; sys.path.insert(0, '.'); from socratic_agents import Agent; print('✓ socratic-agents imported')"
```

---

### Library 2.2: socratic-rag

#### Step 2.2.1: Copy Database and Document Processing Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

copy socratic_system\database\vector_db.py socratic-rag\socratic_rag\
copy socratic_system\database\embedding_cache.py socratic-rag\socratic_rag\
copy socratic_system\database\connection_pool.py socratic-rag\socratic_rag\
copy socratic_system\agents\document_processor.py socratic-rag\socratic_rag\
copy socratic_system\agents\base.py socratic-rag\socratic_rag\
```

#### Step 2.2.2: Update Imports in document_processor.py
**Location:** `C:\Users\themi\PycharmProjects\Socrates\socratic-rag\socratic_rag\document_processor.py`

Changes needed:
- `from socratic_system.agents.base import Agent` → `from .base import Agent`
- `from socratic_system.clients import ClaudeClient` → (import from socratic_nexus OR keep monolith)

#### Step 2.2.3: Test Import
```bash
python -c "from socratic_rag import VectorDatabase; print('✓ socratic-rag imported')"
```

---

### Library 2.3: socratic-workflow

#### Step 2.3.1: Copy Workflow Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

copy socratic_system\core\workflow_builder.py socratic-workflow\socratic_workflow\
copy socratic_system\core\workflow_optimizer.py socratic-workflow\socratic_workflow\
copy socratic_system\core\workflow_path_finder.py socratic-workflow\socratic_workflow\
copy socratic_system\core\workflow_cost_calculator.py socratic-workflow\socratic_workflow\
copy socratic_system\core\workflow_risk_calculator.py socratic-workflow\socratic_workflow\
copy socratic_system\orchestration\orchestrator.py socratic-workflow\socratic_workflow\
```

#### Step 2.3.2: Create __init__.py
```python
"""Workflow management module."""
from .workflow_builder import WorkflowBuilder
from .workflow_optimizer import WorkflowOptimizer
from .orchestrator import Orchestrator

__all__ = ["WorkflowBuilder", "WorkflowOptimizer", "Orchestrator"]
```

#### Step 2.3.3: Test Import
```bash
python -c "from socratic_workflow import WorkflowBuilder; print('✓ socratic-workflow imported')"
```

---

## BATCH 3: EXTRACT SPECIALIZED LIBRARIES (Parallel)

### Library 3.1: socratic-knowledge

#### Step 3.1.1: Copy Knowledge Management Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

copy socratic_system\agents\knowledge_manager.py socratic-knowledge\socratic_knowledge\
copy socratic_system\agents\knowledge_analysis.py socratic-knowledge\socratic_knowledge\
copy socratic_system\orchestration\knowledge_base.py socratic-knowledge\socratic_knowledge\
copy socratic_system\database\vector_db.py socratic-knowledge\socratic_knowledge\
copy socratic_system\database\embedding_cache.py socratic-knowledge\socratic_knowledge\
copy socratic_system\database\search_cache.py socratic-knowledge\socratic_knowledge\
copy socratic_system\agents\base.py socratic-knowledge\socratic_knowledge\
```

#### Step 3.1.2: Update Imports
All agent files:
- `from socratic_system.agents.base import Agent` → `from .base import Agent`
- `from socratic_system.database import VectorDatabase` → `from .vector_db import VectorDatabase`
- `from socratic_system.clients import ClaudeClient` → Keep or update based on setup

#### Step 3.1.3: Test Import
```bash
python -c "from socratic_knowledge import KnowledgeManagerAgent; print('✓ socratic-knowledge imported')"
```

---

### Library 3.2: socratic-analyzer

#### Step 3.2.1: Copy Context Analysis Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

copy socratic_system\agents\context_analyzer.py socratic-analyzer\socratic_analyzer\
copy socratic_system\agents\document_context_analyzer.py socratic-analyzer\socratic_analyzer\
copy socratic_system\agents\code_generator.py socratic-analyzer\socratic_analyzer\
copy socratic_system\agents\code_validation_agent.py socratic-analyzer\socratic_analyzer\
copy socratic_system\agents\base.py socratic-analyzer\socratic_analyzer\
```

#### Step 3.2.2: Create __init__.py
```python
"""Context analysis and code validation module."""
from .context_analyzer import ContextAnalyzerAgent
from .document_context_analyzer import DocumentContextAnalyzer
from .code_generator import CodeGeneratorAgent
from .code_validation_agent import CodeValidationAgent

__all__ = [
    "ContextAnalyzerAgent",
    "DocumentContextAnalyzer",
    "CodeGeneratorAgent",
    "CodeValidationAgent",
]
```

#### Step 3.2.3: Test Import
```bash
python -c "from socratic_analyzer import ContextAnalyzerAgent; print('✓ socratic-analyzer imported')"
```

---

### Library 3.3: socratic-learning

#### Step 3.3.1: Copy Learning Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

copy socratic_system\agents\learning_agent.py socratic-learning\socratic_learning\
copy socratic_system\agents\user_manager.py socratic-learning\socratic_learning\
copy socratic_system\core\learning_engine.py socratic-learning\socratic_learning\
copy socratic_system\agents\base.py socratic-learning\socratic_learning\
```

#### Step 3.3.2: Test Import
```bash
python -c "from socratic_learning import UserLearningAgent; print('✓ socratic-learning imported')"
```

---

### Library 3.4: socratic-docs

#### Step 3.4.1: Copy Document Processing Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

copy socratic_system\agents\document_processor.py socratic-docs\socratic_docs\
copy socratic_system\agents\document_context_analyzer.py socratic-docs\socratic_docs\
copy socratic_system\services\document_understanding.py socratic-docs\socratic_docs\
copy socratic_system\utils\code_structure_analyzer.py socratic-docs\socratic_docs\
copy socratic_system\utils\code_extractor.py socratic-docs\socratic_docs\
copy socratic_system\agents\base.py socratic-docs\socratic_docs\

# Copy extractors subdirectory
xcopy socratic_system\utils\extractors socratic-docs\socratic_docs\extractors\ /E /I /Y
```

#### Step 3.4.2: Test Import
```bash
python -c "from socratic_docs import DocumentProcessorAgent; print('✓ socratic-docs imported')"
```

---

### Library 3.5: socratic-performance

#### Step 3.5.1: Copy Analytics and Monitoring Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

copy socratic_system\core\analytics_calculator.py socratic-performance\socratic_performance\
copy socratic_system\monitoring_metrics.py socratic-performance\socratic_performance\
copy socratic_system\ui\analytics_display.py socratic-performance\socratic_performance\
copy socratic_system\ui\maturity_display.py socratic-performance\socratic_performance\
copy socratic_system\core\insight_categorizer.py socratic-performance\socratic_performance\
```

#### Step 3.5.2: Create __init__.py
```python
"""Performance monitoring and analytics module."""
from .analytics_calculator import AnalyticsCalculator
from .monitoring_metrics import TokenUsage
from .analytics_display import AnalyticsDisplay

__all__ = ["AnalyticsCalculator", "TokenUsage", "AnalyticsDisplay"]
```

#### Step 3.5.3: Test Import
```bash
python -c "from socratic_performance import AnalyticsCalculator; print('✓ socratic-performance imported')"
```

---

### Library 3.6: socratic-maturity

#### Step 3.6.1: Copy Maturity Calculation Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

copy socratic_system\core\maturity_calculator.py socratic-maturity\socratic_maturity\
copy socratic_system\core\project_categories.py socratic-maturity\socratic_maturity\
copy socratic_system\ui\maturity_display.py socratic-maturity\socratic_maturity\
```

#### Step 3.6.2: Create __init__.py
```python
"""Maturity calculation and tracking module."""
from .maturity_calculator import MaturityCalculator
from .project_categories import VALID_PROJECT_TYPES, get_phase_categories

__all__ = ["MaturityCalculator", "VALID_PROJECT_TYPES", "get_phase_categories"]
```

#### Step 3.6.3: Test Import
```bash
python -c "from socratic_maturity import MaturityCalculator; print('✓ socratic-maturity imported')"
```

---

## VERIFICATION PHASE

### Step V.1: Run File Count Verification
```bash
cd C:\Users\themi\PycharmProjects\Socrates
python verify_extraction.py
```

**Expected Output:**
```
✓ socratic-core: 12 files (expected 12)
✓ socratic-nexus: 2 files (expected 2)
✓ socratic-agents: 6 files (expected 6)
✓ socratic-conflict: 4 files (expected 4)
✓ socratic-knowledge: 7 files (expected 7)
✓ socratic-analyzer: 5 files (expected 5)
✓ socratic-learning: 4 files (expected 4)
✓ socratic-workflow: 6 files (expected 6)
✓ socratic-rag: 5 files (expected 5)
✓ socratic-docs: 7 files (expected 7)
✓ socratic-performance: 5 files (expected 5)
✓ socratic-maturity: 3 files (expected 3)

12/12 libraries verified
```

### Step V.2: Run All Import Tests
```bash
cd C:\Users\themi\PycharmProjects\Socrates

python -c "
import sys
sys.path.insert(0, '.')

libs = [
    'socratic_core', 'socratic_nexus', 'socratic_agents', 'socratic_conflict',
    'socratic_knowledge', 'socratic_analyzer', 'socratic_learning', 'socratic_workflow',
    'socratic_rag', 'socratic_docs', 'socratic_performance', 'socratic_maturity'
]

for lib in libs:
    try:
        __import__(lib)
        print(f'✓ {lib} imported successfully')
    except Exception as e:
        print(f'✗ {lib} failed: {e}')
"
```

### Step V.3: Syntax Check All Files
```bash
cd C:\Users\themi\PycharmProjects\Socrates

for lib in socratic-core socratic-nexus socratic-agents socratic-conflict socratic-knowledge socratic-analyzer socratic-learning socratic-workflow socratic-rag socratic-docs socratic-performance socratic-maturity; do
    echo "Checking $lib..."
    python -m py_compile "$lib"/"${lib//-/_}"/*.py || exit 1
done

echo "All libraries passed syntax check!"
```

---

## FINAL CHECKLIST

- [ ] All 12 libraries created
- [ ] All source files copied
- [ ] All __init__.py files created
- [ ] All pyproject.toml files created
- [ ] All imports updated correctly
- [ ] File count verification passed
- [ ] All libraries import successfully
- [ ] No syntax errors found
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] Ready for publication

---

## TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'socratic_system'"
**Solution:** The libraries still need monolith imports for shared modules.
**Fix:**
1. Keep shared imports: `from socratic_system.models import ...`
2. OR create a dependency: `socratic-models`

### Issue: "Circular import detected"
**Solution:** Review import order in __init__.py files.
**Fix:** Use explicit imports in __init__.py, delay imports in functions if needed.

### Issue: "File count mismatch"
**Solution:** Check if you missed files or copied extras.
**Fix:** `find socratic-<lib> -name "*.py" | wc -l`

### Issue: "Import path incorrect"
**Solution:** Review which imports should be local vs. external.
**Fix:** Use relative imports (`.`) for same-library, module imports for cross-library.

---

## TIME ESTIMATE

- Batch 1 (Core): 15-20 minutes
- Batch 2 (Secondary): 20-25 minutes
- Batch 3 (Specialized): 30-40 minutes
- Verification: 10-15 minutes
- **Total: ~90 minutes**

---

