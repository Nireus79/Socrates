# DETAILED FILE MAPPING FOR ALL 12 LIBRARIES
## Complete Source → Target Mapping with Dependencies

---

## LIBRARY 1: socratic-core

### Source Location
`C:\Users\themi\PycharmProjects\Socrates\socratic_system\core\`

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-core\socratic_core\`

### Files to Extract (12)

| # | Source File | Target File | Size | Dependencies |
|---|-------------|------------|------|--------------|
| 1 | `__init__.py` | `__init__.py` | - | models, exceptions |
| 2 | `analytics_calculator.py` | `analytics_calculator.py` | ~3.5KB | models |
| 3 | `insight_categorizer.py` | `insight_categorizer.py` | ~2.1KB | models |
| 4 | `learning_engine.py` | `learning_engine.py` | ~4.2KB | models |
| 5 | `maturity_calculator.py` | `maturity_calculator.py` | ~5.8KB | models |
| 6 | `project_categories.py` | `project_categories.py` | ~3.9KB | config |
| 7 | `question_selector.py` | `question_selector.py` | ~2.8KB | models |
| 8 | `workflow_builder.py` | `workflow_builder.py` | ~4.5KB | models |
| 9 | `workflow_cost_calculator.py` | `workflow_cost_calculator.py` | ~3.2KB | models |
| 10 | `workflow_optimizer.py` | `workflow_optimizer.py` | ~4.1KB | models |
| 11 | `workflow_path_finder.py` | `workflow_path_finder.py` | ~3.6KB | models |
| 12 | `workflow_risk_calculator.py` | `workflow_risk_calculator.py` | ~3.1KB | models |

### Import Rewrites Needed
```python
# None - all imports are shared or already relative
# Just ensure models, exceptions, config are available
```

### Created Files (After Extraction)
- `socratic-core/__init__.py` (wrapper)
- `socratic-core/pyproject.toml`
- `socratic-core/README.md`

### Dependencies (External)
```
- anthropic>=0.25.0
- pydantic>=2.0.0
- numpy>=1.20.0
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models
- socratic_system.exceptions
- socratic_system.config
```

---

## LIBRARY 2: socratic-nexus

### Source Location
`C:\Users\themi\PycharmProjects\Socrates\socratic_system\clients\`

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-nexus\socratic_nexus\`

### Files to Extract (2)

| # | Source File | Target File | Size | Dependencies |
|---|-------------|------------|------|--------------|
| 1 | `__init__.py` | `__init__.py` | - | models |
| 2 | `claude_client.py` | `claude_client.py` | ~8.3KB | models, exceptions |

### Import Rewrites Needed
```python
# Minimal - external imports only
# from anthropic import Anthropic  [NO CHANGE]
# from socratic_system.models import ...  [KEEP]
# from socratic_system.exceptions import ...  [KEEP]
```

### Created Files (After Extraction)
- `socratic-nexus/__init__.py` (wrapper)
- `socratic-nexus/pyproject.toml`
- `socratic-nexus/README.md`

### Dependencies (External)
```
- anthropic>=0.25.0
- pydantic>=2.0.0
- python-dotenv>=1.0.0
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models
- socratic_system.exceptions
```

---

## LIBRARY 3: socratic-agents

### Source Location
`C:\Users\themi\PycharmProjects\Socrates\socratic_system\agents\` (selected files)

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-agents\socratic_agents\`

### Files to Extract (6)

| # | Source File | Target File | Size | Rewrites |
|---|-------------|------------|------|----------|
| 1 | `__init__.py` | `__init__.py` | - | ✓ Change imports to local |
| 2 | `base.py` | `base.py` | ~2.9KB | ✓ Update ClaudeClient import |
| 3 | `multi_llm_agent.py` | `multi_llm_agent.py` | ~5.1KB | ✓ Rewrite base import |
| 4 | `socratic_counselor.py` | `socratic_counselor.py` | ~3.8KB | ✓ Rewrite base import |
| 5 | `note_manager.py` | `note_manager.py` | ~2.6KB | ✓ Rewrite base import |
| 6 | `quality_controller.py` | `quality_controller.py` | ~3.2KB | ✓ Rewrite base import |

### Import Rewrites Needed
```python
# OLD                                          # NEW
from socratic_system.agents.base import Agent  → from .base import Agent
from socratic_system.clients import ClaudeClient → from socratic_nexus import ClaudeClient
```

### Created Files (After Extraction)
- `socratic-agents/__init__.py` (wrapper)
- `socratic-agents/pyproject.toml`
- `socratic-agents/README.md`

### Dependencies (External)
```
- anthropic>=0.25.0
- pydantic>=2.0.0
```

### Library Dependencies
```
- socratic-nexus
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models
- socratic_system.exceptions
- socratic_system.events
```

---

## LIBRARY 4: socratic-conflict

### Source Location
`C:\Users\themi\PycharmProjects\Socrates\socratic_system\conflict_resolution\`

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-conflict\socratic_conflict\`

### Files to Extract (4)

| # | Source File | Target File | Size | Rewrites |
|---|-------------|------------|------|----------|
| 1 | `__init__.py` | `__init__.py` | - | ✓ Change imports to local |
| 2 | `base.py` | `base.py` | ~3.1KB | - |
| 3 | `checkers.py` | `checkers.py` | ~4.2KB | ✓ Rewrite base import |
| 4 | `rules.py` | `rules.py` | ~3.7KB | ✓ Rewrite base import |

### Import Rewrites Needed
```python
from socratic_system.conflict_resolution.base import ConflictResolver → from .base import ConflictResolver
```

### Created Files (After Extraction)
- `socratic-conflict/__init__.py` (wrapper)
- `socratic-conflict/pyproject.toml`
- `socratic-conflict/README.md`

### Dependencies (External)
```
- pydantic>=2.0.0
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models (for ConflictInfo)
- socratic_system.exceptions
```

---

## LIBRARY 5: socratic-knowledge

### Source Locations
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\agents\knowledge_*.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\orchestration\knowledge_base.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\database\vector_db.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\database\embedding_cache.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\database\search_cache.py`

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-knowledge\socratic_knowledge\`

### Files to Extract (7)

| # | Source File | Target File | Type | Rewrites |
|---|-------------|------------|------|----------|
| 1 | `agents/base.py` | `base.py` | Agent | ✓ Update ClaudeClient |
| 2 | `agents/knowledge_manager.py` | `knowledge_manager.py` | Agent | ✓✓✓ Heavy |
| 3 | `agents/knowledge_analysis.py` | `knowledge_analysis.py` | Agent | ✓✓ Medium |
| 4 | `orchestration/knowledge_base.py` | `knowledge_base.py` | Service | ✓ Light |
| 5 | `database/vector_db.py` | `vector_db.py` | DB | ✓ Light |
| 6 | `database/embedding_cache.py` | `embedding_cache.py` | Cache | ✓ Light |
| 7 | `database/search_cache.py` | `search_cache.py` | Cache | ✓ Light |

### Import Rewrites Needed
```python
from socratic_system.agents.base import Agent                    → from .base import Agent
from socratic_system.agents.knowledge_manager import ...         → from .knowledge_manager import ...
from socratic_system.orchestration.knowledge_base import ...     → from .knowledge_base import ...
from socratic_system.database.vector_db import VectorDatabase    → from .vector_db import VectorDatabase
from socratic_system.database.embedding_cache import ...         → from .embedding_cache import ...
from socratic_system.database.search_cache import ...            → from .search_cache import ...
from socratic_system.clients import ClaudeClient                 → from socratic_nexus import ClaudeClient
```

### Created Files (After Extraction)
- `socratic-knowledge/__init__.py` (wrapper)
- `socratic-knowledge/pyproject.toml`
- `socratic-knowledge/README.md`

### Dependencies (External)
```
- anthropic>=0.25.0
- pydantic>=2.0.0
- numpy>=1.20.0
```

### Library Dependencies
```
- socratic-nexus
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models
- socratic_system.exceptions
- socratic_system.events
- socratic_system.config
```

---

## LIBRARY 6: socratic-analyzer

### Source Location
`C:\Users\themi\PycharmProjects\Socrates\socratic_system\agents\`

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-analyzer\socratic_analyzer\`

### Files to Extract (5)

| # | Source File | Target File | Size | Rewrites |
|---|-------------|------------|------|----------|
| 1 | `agents/base.py` | `base.py` | ~2.9KB | ✓ Update ClaudeClient |
| 2 | `agents/context_analyzer.py` | `context_analyzer.py` | ~4.6KB | ✓✓ Heavy |
| 3 | `agents/document_context_analyzer.py` | `document_context_analyzer.py` | ~3.9KB | ✓✓ Heavy |
| 4 | `agents/code_generator.py` | `code_generator.py` | ~5.2KB | ✓✓ Heavy |
| 5 | `agents/code_validation_agent.py` | `code_validation_agent.py` | ~4.1KB | ✓✓ Heavy |

### Import Rewrites Needed
```python
from socratic_system.agents.base import Agent                    → from .base import Agent
from socratic_system.agents.context_analyzer import ...          → from .context_analyzer import ...
from socratic_system.clients import ClaudeClient                 → from socratic_nexus import ClaudeClient
```

### Created Files (After Extraction)
- `socratic-analyzer/__init__.py` (wrapper)
- `socratic-analyzer/pyproject.toml`
- `socratic-analyzer/README.md`

### Dependencies (External)
```
- anthropic>=0.25.0
- pydantic>=2.0.0
```

### Library Dependencies
```
- socratic-nexus
- socratic-agents (for base)
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models
- socratic_system.exceptions
- socratic_system.events
```

---

## LIBRARY 7: socratic-learning

### Source Locations
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\agents\learning_agent.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\agents\user_manager.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\core\learning_engine.py`

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-learning\socratic_learning\`

### Files to Extract (4)

| # | Source File | Target File | Type | Rewrites |
|---|-------------|------------|------|----------|
| 1 | `agents/base.py` | `base.py` | Agent | ✓ Update ClaudeClient |
| 2 | `agents/learning_agent.py` | `learning_agent.py` | Agent | ✓✓ Heavy |
| 3 | `agents/user_manager.py` | `user_manager.py` | Agent | ✓✓ Heavy |
| 4 | `core/learning_engine.py` | `learning_engine.py` | Engine | ✓ Light |

### Import Rewrites Needed
```python
from socratic_system.agents.base import Agent                    → from .base import Agent
from socratic_system.core.learning_engine import LearningEngine  → from .learning_engine import LearningEngine
from socratic_system.clients import ClaudeClient                 → from socratic_nexus import ClaudeClient
```

### Created Files (After Extraction)
- `socratic-learning/__init__.py` (wrapper)
- `socratic-learning/pyproject.toml`
- `socratic-learning/README.md`

### Dependencies (External)
```
- anthropic>=0.25.0
- pydantic>=2.0.0
```

### Library Dependencies
```
- socratic-nexus
- socratic-agents (for base)
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models
- socratic_system.exceptions
- socratic_system.events
```

---

## LIBRARY 8: socratic-workflow

### Source Locations
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\core\workflow_*.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\orchestration\orchestrator.py`

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-workflow\socratic_workflow\`

### Files to Extract (6)

| # | Source File | Target File | Type | Rewrites |
|---|-------------|------------|------|----------|
| 1 | `core/workflow_builder.py` | `workflow_builder.py` | Core | ✓ Light |
| 2 | `core/workflow_optimizer.py` | `workflow_optimizer.py` | Core | ✓ Light |
| 3 | `core/workflow_path_finder.py` | `workflow_path_finder.py` | Core | ✓ Light |
| 4 | `core/workflow_cost_calculator.py` | `workflow_cost_calculator.py` | Core | ✓ Light |
| 5 | `core/workflow_risk_calculator.py` | `workflow_risk_calculator.py` | Core | ✓ Light |
| 6 | `orchestration/orchestrator.py` | `orchestrator.py` | Service | ✓✓ Medium |

### Import Rewrites Needed
```python
from socratic_system.core.workflow_builder import ...    → from .workflow_builder import ...
from socratic_system.orchestration.orchestrator import ... → from .orchestrator import ...
```

### Created Files (After Extraction)
- `socratic-workflow/__init__.py` (wrapper)
- `socratic-workflow/pyproject.toml`
- `socratic-workflow/README.md`

### Dependencies (External)
```
- pydantic>=2.0.0
- numpy>=1.20.0
```

### Library Dependencies
```
- socratic-core (optional, for shared code)
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models
- socratic_system.exceptions
- socratic_system.config
```

---

## LIBRARY 9: socratic-rag

### Source Locations
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\database\vector_db.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\database\embedding_cache.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\database\connection_pool.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\agents\document_processor.py`

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-rag\socratic_rag\`

### Files to Extract (5)

| # | Source File | Target File | Type | Rewrites |
|---|-------------|------------|------|----------|
| 1 | `agents/base.py` | `base.py` | Agent | ✓ Update ClaudeClient |
| 2 | `database/vector_db.py` | `vector_db.py` | DB | ✓ Light |
| 3 | `database/embedding_cache.py` | `embedding_cache.py` | Cache | ✓ Light |
| 4 | `database/connection_pool.py` | `connection_pool.py` | DB | ✓ Light |
| 5 | `agents/document_processor.py` | `document_processor.py` | Agent | ✓✓ Heavy |

### Import Rewrites Needed
```python
from socratic_system.agents.base import Agent                    → from .base import Agent
from socratic_system.database.vector_db import ...               → from .vector_db import ...
from socratic_system.database.embedding_cache import ...         → from .embedding_cache import ...
from socratic_system.database.connection_pool import ...         → from .connection_pool import ...
from socratic_system.clients import ClaudeClient                 → from socratic_nexus import ClaudeClient
```

### Created Files (After Extraction)
- `socratic-rag/__init__.py` (wrapper)
- `socratic-rag/pyproject.toml`
- `socratic-rag/README.md`

### Dependencies (External)
```
- anthropic>=0.25.0
- pydantic>=2.0.0
- numpy>=1.20.0
```

### Library Dependencies
```
- socratic-nexus
- socratic-agents (for base)
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models
- socratic_system.exceptions
- socratic_system.config
```

---

## LIBRARY 10: socratic-docs

### Source Locations
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\agents\document_*.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\services\document_understanding.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\utils\code_extractor.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\utils\code_structure_analyzer.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\utils\extractors\*` (all)

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-docs\socratic_docs\`

### Files to Extract (7+)

| # | Source File | Target File | Type | Rewrites |
|---|-------------|------------|------|----------|
| 1 | `agents/base.py` | `base.py` | Agent | ✓ Update ClaudeClient |
| 2 | `agents/document_processor.py` | `document_processor.py` | Agent | ✓✓ Heavy |
| 3 | `agents/document_context_analyzer.py` | `document_context_analyzer.py` | Agent | ✓✓ Heavy |
| 4 | `services/document_understanding.py` | `document_understanding.py` | Service | ✓✓ Medium |
| 5 | `utils/code_extractor.py` | `code_extractor.py` | Util | ✓ Light |
| 6 | `utils/code_structure_analyzer.py` | `code_structure_analyzer.py` | Util | ✓ Light |
| 7+ | `utils/extractors/*` | `extractors/` | Util | ✓ Light |

### Import Rewrites Needed
```python
from socratic_system.agents.base import Agent                    → from .base import Agent
from socratic_system.utils.code_extractor import ...             → from .code_extractor import ...
from socratic_system.utils.code_structure_analyzer import ...    → from .code_structure_analyzer import ...
from socratic_system.utils.extractors import ...                 → from .extractors import ...
from socratic_system.clients import ClaudeClient                 → from socratic_nexus import ClaudeClient
```

### Created Files (After Extraction)
- `socratic-docs/__init__.py` (wrapper)
- `socratic-docs/pyproject.toml`
- `socratic-docs/README.md`

### Dependencies (External)
```
- anthropic>=0.25.0
- pydantic>=2.0.0
```

### Library Dependencies
```
- socratic-nexus
- socratic-agents (for base)
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models
- socratic_system.exceptions
- socratic_system.events
```

---

## LIBRARY 11: socratic-performance

### Source Locations
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\core\analytics_calculator.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\core\insight_categorizer.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\monitoring_metrics.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\ui\analytics_display.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\ui\maturity_display.py`

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-performance\socratic_performance\`

### Files to Extract (5)

| # | Source File | Target File | Type | Rewrites |
|---|-------------|------------|------|----------|
| 1 | `core/analytics_calculator.py` | `analytics_calculator.py` | Core | ✓ Light |
| 2 | `core/insight_categorizer.py` | `insight_categorizer.py` | Core | ✓ Light |
| 3 | `monitoring_metrics.py` | `monitoring_metrics.py` | Metrics | ✓ Light |
| 4 | `ui/analytics_display.py` | `analytics_display.py` | UI | ✓ Light |
| 5 | `ui/maturity_display.py` | `maturity_display.py` | UI | ✓ Light |

### Import Rewrites Needed
```python
from socratic_system.core.analytics_calculator import ...    → from .analytics_calculator import ...
from socratic_system.core.insight_categorizer import ...     → from .insight_categorizer import ...
from socratic_system.ui.analytics_display import ...         → from .analytics_display import ...
from socratic_system.ui.maturity_display import ...          → from .maturity_display import ...
```

### Created Files (After Extraction)
- `socratic-performance/__init__.py` (wrapper)
- `socratic-performance/pyproject.toml`
- `socratic-performance/README.md`

### Dependencies (External)
```
- pydantic>=2.0.0
```

### Library Dependencies
```
- socratic-core (optional)
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models
- socratic_system.exceptions
- socratic_system.events
```

---

## LIBRARY 12: socratic-maturity

### Source Locations
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\core\maturity_calculator.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\core\project_categories.py`
- `C:\Users\themi\PycharmProjects\Socrates\socratic_system\ui\maturity_display.py`

### Target Location
`C:\Users\themi\PycharmProjects\Socrates\socratic-maturity\socratic_maturity\`

### Files to Extract (3)

| # | Source File | Target File | Type | Rewrites |
|---|-------------|------------|------|----------|
| 1 | `core/maturity_calculator.py` | `maturity_calculator.py` | Core | ✓ Light |
| 2 | `core/project_categories.py` | `project_categories.py` | Core | ✓ Light |
| 3 | `ui/maturity_display.py` | `maturity_display.py` | UI | ✓ Light |

### Import Rewrites Needed
```python
from socratic_system.core.maturity_calculator import ...    → from .maturity_calculator import ...
from socratic_system.core.project_categories import ...     → from .project_categories import ...
from socratic_system.ui.maturity_display import ...         → from .maturity_display import ...
```

### Created Files (After Extraction)
- `socratic-maturity/__init__.py` (wrapper)
- `socratic-maturity/pyproject.toml`
- `socratic-maturity/README.md`

### Dependencies (External)
```
- pydantic>=2.0.0
```

### Library Dependencies
```
- socratic-core (optional)
```

### Shared Dependencies (From Monolith)
```
- socratic_system.models
- socratic_system.exceptions
- socratic_system.events
```

---

## SUMMARY TABLE

| Library | Source | Files | Rewrite Complexity | Dependencies |
|---------|--------|-------|-------------------|--------------|
| socratic-core | core/ | 12 | None | models, exceptions, config |
| socratic-nexus | clients/ | 2 | None | models, exceptions |
| socratic-agents | agents/ | 6 | Light | nexus |
| socratic-conflict | conflict_resolution/ | 4 | Light | models, exceptions |
| socratic-knowledge | agents+orch+db | 7 | Heavy | nexus |
| socratic-analyzer | agents/ | 5 | Heavy | nexus, agents |
| socratic-learning | agents+core | 4 | Heavy | nexus, agents |
| socratic-workflow | core+orch | 6 | Light | - |
| socratic-rag | db+agents | 5 | Heavy | nexus, agents |
| socratic-docs | agents+utils+services | 7+ | Heavy | nexus, agents |
| socratic-performance | core+ui+monitoring | 5 | Light | - |
| socratic-maturity | core+ui | 3 | Light | - |
| **TOTAL** | **Monolith** | **62+** | **Mixed** | **See above** |

---

## REWRITE COMPLEXITY LEVELS

**None:** No import changes needed, files are self-contained
**Light:** 1-2 import patterns to rewrite
**Medium:** 3-5 import patterns to rewrite
**Heavy:** 6+ import patterns to rewrite, cross-library dependencies

---

