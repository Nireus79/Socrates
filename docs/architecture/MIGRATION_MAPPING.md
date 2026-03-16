# Phase 1 Migration Mapping - Code Reorganization Guide

**Date**: March 16, 2026
**Phase**: Phase 1 - Module Restructuring
**Status**: Day 1 Complete - Ready for Days 2-5 execution
**Reference**: PHASE_1_IMPLEMENTATION_GUIDE.md

---

## Executive Summary

This document maps every file and module from the current monolithic `socratic_system/` structure to the new modular architecture. It ensures:
- ✅ No code is lost or duplicated
- ✅ All dependencies are resolved
- ✅ Import paths are correctly updated
- ✅ All 17 agents are moved intact
- ✅ All 16 original modules are reorganized

**Total Lines to Move**: ~50,000
**Total Files to Move**: ~200+
**Total Agents to Reorganize**: 17
**Original Modules**: 16

---

## Part A: Agent Migration (17 agents)

### Location: socratic_system/agents/ → modules/agents/agents/

| Agent Name | Current File | New Location | Dependencies | Priority |
|------------|-------------|--------------|--------------|----------|
| BaseAgent | base.py | modules/agents/base.py | None | P0 - First |
| AnalysisAgent | analysis_agent.py | modules/agents/agents/analysis_agent.py | utils, clients | P1 |
| ConflictAgent | conflict_agent.py | modules/agents/agents/conflict_agent.py | utils, database | P1 |
| DataAgent | data_agent.py | modules/agents/agents/data_agent.py | clients, database | P1 |
| DebugAgent | debug_agent.py | modules/agents/agents/debug_agent.py | clients | P1 |
| DesignAgent | design_agent.py | modules/agents/agents/design_agent.py | clients, utils | P1 |
| DocumentationAgent | documentation_agent.py | modules/agents/agents/documentation_agent.py | clients, utils | P1 |
| EngineAgent | engine_agent.py | modules/agents/agents/engine_agent.py | clients, database | P1 |
| FactCheckAgent | fact_check_agent.py | modules/agents/agents/fact_check_agent.py | clients, utils | P1 |
| ImplementationAgent | implementation_agent.py | modules/agents/agents/implementation_agent.py | clients, utils | P1 |
| ImprovedConflictAgent | improved_conflict_agent.py | modules/agents/agents/improved_conflict_agent.py | utils | P1 |
| InterfaceAgent | interface_agent.py | modules/agents/agents/interface_agent.py | clients | P1 |
| LearnersAnalysisAgent | learners_analysis_agent.py | modules/agents/agents/learners_analysis_agent.py | clients, database | P1 |
| NetworkAgent | network_agent.py | modules/agents/agents/network_agent.py | utils, database | P1 |
| PlanningAgent | planning_agent.py | modules/agents/agents/planning_agent.py | clients | P1 |
| ReviewAgent | review_agent.py | modules/agents/agents/review_agent.py | clients, utils | P1 |
| UserLearningAgent | user_learning_agent.py | modules/learning/user_learning_agent.py | database | P1 |

**Summary**:
- 16 agents → `modules/agents/agents/`
- 1 agent (UserLearningAgent) → `modules/learning/` (learning-specific)
- BaseAgent → `modules/agents/base.py` (shared base)

---

## Part B: Core Modules Migration

### 1. LEARNING MODULE
**Location**: socratic_system/core/ + socratic_system/agents/user_learning_agent.py
**New Location**: modules/learning/

| File | Current Path | New Path | Purpose |
|------|-------------|----------|---------|
| learning_engine.py | core/ | modules/learning/ | Core learning logic |
| user_learning_agent.py | agents/ | modules/learning/ | User-specific learning |
| learning_service.py | (NEW) | modules/learning/ | Service wrapper |
| skill_generator.py | (NEW) | modules/learning/ | SkillGeneratorAgent integration |
| __init__.py | (NEW) | modules/learning/ | Module exports |

**Dependencies**:
- ✓ database/project_db.py (Learning data storage)
- ✓ clients/claude_client.py (LLM calls for analysis)
- ✓ socratic-agents.SkillGeneratorAgent (ecosystem integration)

**Breakdown of learning_engine.py responsibilities**:
- Pattern detection in agent interactions
- Learning milestone calculation
- Recommendation generation
- Metrics tracking

---

### 2. FOUNDATION MODULE
**Location**: socratic_system/clients/ + socratic_system/database/
**New Location**: modules/foundation/

| File | Current Path | New Path | Purpose |
|------|-------------|----------|---------|
| claude_client.py | clients/ | modules/foundation/llm_service.py | LLM abstraction |
| project_db.py | database/ | modules/foundation/database_service.py | Database operations |
| connection_pool.py | database/ | modules/foundation/connection_pool.py | Connection pooling |
| redis_cache.py | database/ | modules/foundation/cache_service.py | Caching layer |
| foundation_service.py | (NEW) | modules/foundation/ | Service wrapper |
| __init__.py | (NEW) | modules/foundation/ | Module exports |

**Dependencies**:
- ✓ anthropic SDK (LLM calls)
- ✓ sqlite3 (database)
- ✓ chroma (embeddings/vector DB initially)
- ✓ redis (caching)

**Note**: LLM service will be wrapper around socrates-nexus (future integration)

---

### 3. KNOWLEDGE MODULE
**Location**: socratic_system/database/vector_db.py + socratic_system/orchestration/knowledge_base.py
**New Location**: modules/knowledge/

| File | Current Path | New Path | Purpose |
|------|-------------|----------|---------|
| vector_db.py | database/ | modules/knowledge/vector_db.py | Vector embeddings |
| knowledge_base.py | orchestration/ | modules/knowledge/knowledge_base.py | Knowledge management |
| knowledge_service.py | (NEW) | modules/knowledge/ | Service wrapper |
| __init__.py | (NEW) | modules/knowledge/ | Module exports |

**Dependencies**:
- ✓ chroma (vector DB)
- ✓ project_db.py (structured data)
- ✓ embeddings API (socrates-knowledge future)

**Breakdown**:
- Semantic search across knowledge base
- Document versioning
- RBAC for knowledge access
- RAG pipeline support (socratic-rag future)

---

### 4. WORKFLOW MODULE
**Location**: socratic_system/core/
**New Location**: modules/workflow/

| File | Current Path | New Path | Purpose |
|------|-------------|----------|---------|
| workflow_builder.py | core/ | modules/workflow/builder.py | Workflow construction |
| workflow_executor.py | core/ | modules/workflow/executor.py | Workflow execution |
| workflow_optimizer.py | core/ | modules/workflow/optimizer.py | Cost/performance optimization |
| workflow_service.py | (NEW) | modules/workflow/ | Service wrapper |
| __init__.py | (NEW) | modules/workflow/ | Module exports |

**Dependencies**:
- ✓ agents (workflow tasks are agent executions)
- ✓ database (state tracking)
- ✓ clients/claude_client.py (LLM for planning)

**Breakdown**:
- DAG-based workflow definition
- Conditional execution logic
- Cost tracking per step
- Optimization recommendations
- State persistence

---

### 5. ANALYTICS MODULE
**Location**: socratic_system/core/
**New Location**: modules/analytics/

| File | Current Path | New Path | Purpose |
|------|-------------|----------|---------|
| analytics_calculator.py | core/ | modules/analytics/calculator.py | Metrics computation |
| analytics_service.py | (NEW) | modules/analytics/ | Service wrapper |
| __init__.py | (NEW) | modules/analytics/ | Module exports |

**Dependencies**:
- ✓ database/project_db.py (historical data)

**Breakdown**:
- System performance metrics
- Agent effectiveness tracking
- Learning progress visualization
- Recommendation accuracy measurement
- User engagement analytics

---

### 6. AGENTS MODULE (Service Wrapper)
**Location**: socratic_system/agents/
**New Location**: modules/agents/

| File | Current Path | New Path | Purpose |
|------|-------------|----------|---------|
| base.py | agents/ | modules/agents/base.py | BaseAgent class |
| (all agents) | agents/*.py | modules/agents/agents/*.py | Individual agents |
| agents_service.py | (NEW) | modules/agents/ | Service wrapper |
| __init__.py | (NEW) | modules/agents/ | Module exports |

**Dependencies**:
- ✓ clients/claude_client.py (LLM calls)
- ✓ database/project_db.py (context storage)
- ✓ learning_engine.py (skill application)

**Breakdown**:
- Agent execution coordination
- Skill loading and application
- Interaction tracking
- Error handling and recovery

---

## Part C: Supporting Modules (Being Moved)

### Utilities (Shared across modules)
**Location**: socratic_system/utils/
**New Location**: modules/foundation/utils/ (for now)

| File | Purpose | Usage |
|------|---------|-------|
| decorators.py | Logging, timing, caching decorators | All modules |
| validators.py | Input validation | All modules |
| constants.py | System constants | All modules |
| helpers.py | Helper functions | Multiple modules |

**Note**: These will be reorganized as shared utilities during Phase 2

---

### Configuration
**Location**: socratic_system/config/ → config/
**New Location**: config/

| File | Purpose |
|------|---------|
| settings.py | Global configuration |
| environment.py | Environment-specific config |
| logging_config.py | Logging setup |

---

### Database Migrations
**Location**: socratic_system/database/migrations/
**New Location**: modules/foundation/migrations/

Database schema stays with Foundation module (closest parent)

---

## Part D: Tests Migration

### Current Structure
**Location**: tests/
**New Location**: tests/

```
tests/
├── unit/
│   ├── agents/
│   ├── learning/
│   ├── knowledge/
│   ├── workflow/
│   ├── analytics/
│   └── foundation/
├── integration/
│   ├── agents/
│   ├── learning/
│   └── workflow/
└── e2e/
    └── workflows/
```

**Test Files to Move**:
- test_*.py → tests/{unit,integration,e2e}/{module}/
- conftest.py → tests/conftest.py (shared fixtures)

**Total Tests**: 1000+

---

## Part E: Import Path Changes

### Pattern 1: System imports
**Before**:
```python
from socratic_system.agents.base import BaseAgent
from socratic_system.core.learning_engine import LearningEngine
from socratic_system.clients.claude_client import ClaudeClient
```

**After**:
```python
from modules.agents import BaseAgent
from modules.learning import LearningEngine
from modules.foundation import ClaudeClient
```

### Pattern 2: Relative imports within modules
**Before**:
```python
from socratic_system.utils.decorators import timing_decorator
```

**After**:
```python
from ..foundation.utils.decorators import timing_decorator  # Within agents module
from .utils.decorators import timing_decorator              # Within foundation module
```

### Pattern 3: Service imports (Phase 2+)
**After Phase 2**:
```python
from core.orchestrator import ServiceOrchestrator
agent_service = await orchestrator.get_service('agents')
```

---

## Part F: Dependency Graph

```
Foundation (Base layer)
├── LLM Service (claude_client)
├── Database Service (project_db, connection_pool)
├── Cache Service (redis_cache)
└── Utils (decorators, validators, helpers)
    ↓
Knowledge Module
├── Vector DB
├── Knowledge Base
└── Depends on: Foundation

    Learning Module
    ├── Learning Engine
    ├── Skill Generator (SkillGeneratorAgent)
    ├── User Learning Agent
    └── Depends on: Foundation

        Agents Module
        ├── 16 Agents + BaseAgent
        ├── Agents Service
        └── Depends on: Foundation, Learning

            Workflow Module
            ├── Builder, Executor, Optimizer
            ├── Workflow Service
            └── Depends on: Foundation, Agents

                Analytics Module
                ├── Calculator
                ├── Analytics Service
                └── Depends on: Foundation
```

**Key Rules**:
- ✅ Foundation has NO dependencies on other modules
- ✅ Knowledge depends ONLY on Foundation
- ✅ Learning depends ONLY on Foundation
- ✅ Agents depend on Foundation + Learning
- ✅ Workflow depends on Foundation + Agents
- ✅ Analytics depends ONLY on Foundation

---

## Part G: File-by-File Checklist

### Phase 1 Day 2: Directory Structure
- [ ] Create modules/{agents,learning,knowledge,workflow,analytics,foundation}/{agents,services,models}
- [ ] Create core/
- [ ] Create interfaces/{api,cli}
- [ ] Create config/
- [ ] Create tests/{unit,integration,e2e}/{module}
- [ ] Create all __init__.py files

### Phase 1 Day 3: Move Agent Code
- [ ] Copy socratic_system/agents/base.py → modules/agents/base.py
- [ ] Copy all socratic_system/agents/*.py → modules/agents/agents/
- [ ] Create modules/agents/service.py
- [ ] Create modules/agents/__init__.py
- [ ] Update imports in moved files

### Phase 1 Day 4: Move Remaining Code
- [ ] Move learning: socratic_system/core/learning_engine.py → modules/learning/
- [ ] Move learning: socratic_system/agents/user_learning_agent.py → modules/learning/
- [ ] Move foundation: clients/claude_client.py → modules/foundation/llm_service.py
- [ ] Move foundation: database/*.py → modules/foundation/
- [ ] Move knowledge: database/vector_db.py → modules/knowledge/
- [ ] Move knowledge: orchestration/knowledge_base.py → modules/knowledge/
- [ ] Move workflow: core/workflow_*.py → modules/workflow/
- [ ] Move analytics: core/analytics_calculator.py → modules/analytics/
- [ ] Create service.py for each module
- [ ] Create __init__.py for each module

### Phase 1 Day 5: Import Updates & Testing
- [ ] Run find/sed to update imports (with review)
- [ ] Test each module import individually
- [ ] Run full test suite: pytest tests/ -v
- [ ] Fix any remaining import errors
- [ ] Commit changes

---

## Part H: Known Issues & Resolutions

### Issue 1: Circular Imports
**Risk**: socratic_system has some circular dependencies
**Solution**: Use import reorganization to break cycles:
- Move shared code to Foundation
- Use service interfaces (Phase 2) for inter-module calls
- Use deferred imports where needed

### Issue 2: Config Files
**Risk**: Config references absolute paths to socratic_system/
**Solution**: Update config paths to use relative imports from project root

### Issue 3: Database Migrations
**Risk**: Migrations reference old table structures
**Solution**: Update migration paths but don't modify SQL (data compatible)

### Issue 4: Test Fixtures
**Risk**: Test fixtures have absolute imports
**Solution**: Update conftest.py and fixtures to use new import structure

---

## Part I: Validation Checklist

After each day of Phase 1, validate:

**After Day 2** (Directory Structure):
```bash
✓ mkdir created all directories
✓ __init__.py exists in all module directories
✓ tree command shows correct structure
```

**After Day 3** (Agent Code):
```bash
✓ python -c "from modules.agents import BaseAgent; print('OK')"
✓ python -c "from modules.agents.agents import AnalysisAgent; print('OK')"
✓ All 16 agent files present in modules/agents/agents/
```

**After Day 4** (Remaining Code):
```bash
✓ python -c "from modules.learning import LearningEngine; print('OK')"
✓ python -c "from modules.foundation import ClaudeClient; print('OK')"
✓ python -c "from modules.knowledge import VectorDB; print('OK')"
✓ python -c "from modules.workflow import WorkflowBuilder; print('OK')"
✓ python -c "from modules.analytics import AnalyticsCalculator; print('OK')"
✓ All service.py files created
```

**After Day 5** (Import Updates & Testing):
```bash
✓ pytest tests/ -v → 0 failures
✓ ruff check modules/ → 0 errors
✓ mypy modules/ --strict → 0 errors
✓ All 1000+ tests passing
✓ Code reorganized into modules
✓ No functional changes made
✓ Ready for Phase 2
```

---

## Part J: Rollback Procedure

If issues occur:

```bash
# Option 1: Rollback to tagged state
git reset --hard phase-1-start
git clean -fd

# Option 2: Restore from local backup
rm -rf socratic_system/
cp -r socratic_system.backup.phase1 socratic_system

# Option 3: Return to full monolith
git reset --hard backup/monolithic-v1.3.3
git clean -fd
```

---

## Summary

| Item | Count | Status |
|------|-------|--------|
| Total Agents | 17 | Ready to move |
| Total Files | 200+ | Mapped |
| Total Lines | 50,000 | Mapped |
| Modules | 6 | Designed |
| Core Infrastructure | 3 files | Designed (BaseService, Orchestrator, EventBus) |
| Tests | 1000+ | Ready to reorganize |
| Import Updates | ~300 | Planned |
| Rollback Points | 3 | Available |

**Phase 1 Objective**: Complete by end of Day 5
**Exit Criteria**: All tests passing, all imports working, no functional changes

---

**Document Status**: ✅ COMPLETE
**Date Created**: March 16, 2026
**Ready for**: Phase 1 Days 2-5 Execution
**Reference**: PHASE_1_IMPLEMENTATION_GUIDE.md
