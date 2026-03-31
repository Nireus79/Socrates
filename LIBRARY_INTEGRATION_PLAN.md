# Socratic Libraries Integration Plan

**Status**: Ready for Implementation
**Date**: 2026-03-31
**Objective**: Integrate all 13 socratic-* libraries into Socrates backend

---

## Current State

### ✅ ADDED TO requirements.txt (Just Done)
All 13 libraries now in requirements.txt:
- socratic-core>=0.1.2
- socratic-security>=0.4.0
- socratic-learning>=0.1.3
- socratic-analyzer>=0.1.2
- socratic-rag>=0.1.1
- socratic-workflow>=0.1.2
- socratic-knowledge>=0.1.3
- socratic-conflict>=0.1.3
- socratic-agents>=0.2.3
- socratic-maturity>=0.1.0
- socratic-performance>=0.1.1
- socratic-docs>=0.1.1
- socrates-nexus>=0.3.1

### ❌ CODE INTEGRATION STATUS

**Try/Except Fallbacks** (Fail Silently When Libraries Missing):
- models_local.py (LearningIntegration, AnalyzerIntegration, KnowledgeManager, RAGIntegration, WorkflowIntegration)
- models.py (SecurityInputValidator)
- middleware/performance.py (QueryProfiler attempt)
- orchestrator.py (SocraticCounselor from agents)

**Not Used At All Yet**:
- socratic-conflict (ConflictDetector, ResolutionEngine)
- socratic-maturity (MaturityTracker)
- socratic-core (EventBus, BaseService, Orchestrator, SharedModels)
- socratic-docs (DocumentationGenerator)
- socrates-nexus (LLMClient - CRITICAL!)

---

## Integration Tasks by Priority

### PRIORITY 1: socrates-nexus (CRITICAL - Replace Custom LLM Handling)

**Current Issue**: Socrates using custom LLM client instead of production-grade socrates-nexus

**Files to Modify**:
- `orchestrator.py` - Replace LLM calls with socrates-nexus LLMClient
- `models_local.py` - Use socrates-nexus for all LLM operations
- Any direct LLM calls in routers

**Steps**:
1. Import LLMClient from socrates_nexus
2. Replace `self.llm_client` initialization with socrates_nexus.LLMClient
3. Update all LLM call patterns to use nexus client methods
4. Enable token tracking via socrates_nexus
5. Enable response caching via socrates_nexus
6. Test with multiple providers (Claude, GPT-4, Gemini)

**Expected Result**: Production-grade LLM handling with token tracking, caching, retry logic

---

### PRIORITY 2: Remove Try/Except Fallbacks & Force Library Usage

**Current Approach**: Libraries try to import but gracefully fail
**New Approach**: Libraries MUST work - fail fast if not available

**Files to Modify**:
- `models_local.py` - LearningIntegration, AnalyzerIntegration, KnowledgeManager, RAGIntegration, WorkflowIntegration
- `models.py` - SecurityInputValidator
- `middleware/performance.py` - QueryProfiler

**Steps for Each**:
1. Remove try/except ImportError blocks
2. Change from lazy import to eager import at module level
3. Remove `self.available` flag (libraries must be installed)
4. Ensure proper initialization
5. Update error handling to fail fast instead of gracefully degrade

**Example**:
```python
# OLD (try/except with fallback):
try:
    from socratic_learning import LearningEngine
    self.engine = LearningEngine()
    self.available = True
except ImportError:
    self.available = False

# NEW (proper import):
from socratic_learning import LearningEngine
self.engine = LearningEngine()
```

---

### PRIORITY 3: Integrate socratic-agents

**Current State**: orchestrator.py tries to import SocraticCounselor but fails
**Target**: Use all 19 agents from socratic-agents library

**Files to Modify**:
- `orchestrator.py` - Use agents from library, not custom implementations

**Steps**:
1. Import 19 agents from socratic_agents
2. Replace custom agent implementations with library agents
3. Update orchestrator to coordinate agents properly
4. Remove duplicate agent code

**Agents Available**:
- CodeGenerator, CodeValidator, CodeAnalyzer
- KnowledgeManager, ContextAnalyzer
- ProjectManager, ConflictResolver
- LearningTracker, PerformanceMonitor
- 9+ more specialized agents

**Expected Result**: 19 production-grade agents instead of custom stubs

---

### PRIORITY 4: Integrate socratic-conflict

**Current State**: Not used at all
**Target**: Use ConflictDetector and ResolutionEngine for spec conflicts

**Files to Modify**:
- `orchestrator.py` - Use conflict detection and resolution
- `routers/projects.py` - Better conflict handling

**Steps**:
1. Import ConflictDetector, ResolutionEngine from socratic_conflict
2. Add conflict detection on spec extraction
3. Implement 5 resolution strategies
4. Use consensus algorithms for multi-agent decisions
5. Track decision versioning and reversal

**Expected Result**: Production-grade conflict management instead of basic detection

---

### PRIORITY 5: Integrate socratic-maturity

**Current State**: Custom maturity calculation in orchestrator/analytics
**Target**: Use MaturityTracker from library

**Files to Modify**:
- `orchestrator.py` - Replace maturity calculation
- `analytics.py` - Use library instead of custom calc

**Steps**:
1. Import MaturityTracker from socratic_maturity
2. Replace custom phase calculation with library
3. Use library's smart phase averaging (never penalizes advancement)
4. Get phase estimation based on quality categories

**Expected Result**: Production-grade maturity tracking

---

### PRIORITY 6: Integrate socratic-performance

**Current State**: Try to import QueryProfiler in middleware, not working
**Target**: Use QueryProfiler decorator and TTLCache

**Files to Modify**:
- `middleware/performance.py` - Actually use QueryProfiler
- `database.py` - Add @profile decorator to slow queries
- Analytics and caching code - Use TTLCache

**Steps**:
1. Import QueryProfiler, TTLCache from socratic_performance
2. Add @profile decorator to database queries
3. Use @cached decorator for metrics calculations
4. Configure TTL values (default 5min)
5. Monitor profiler stats

**Expected Result**: Production-grade performance monitoring and caching

---

### PRIORITY 7: Integrate socratic-security

**Current State**: Try to import in models.py, fails
**Target**: Use all 4 components properly

**Files to Modify**:
- `models.py` - Use from library
- `orchestrator.py` - Use components for all inputs
- All endpoints - Apply security decorators

**Components**:
1. PromptInjectionDetector - already trying to use
2. PathTraversalValidator - for file operations
3. CodeSandbox - for code execution
4. InputValidator - for all user input

**Expected Result**: Enterprise-grade security from library

---

### PRIORITY 8: Integrate socratic-knowledge

**Current State**: Tries to import, fails
**Target**: Use KnowledgeManager from library

**Files to Modify**:
- `models_local.py` - KnowledgeManager class
- `routers/knowledge_management.py` - Use library instead

**Steps**:
1. Import KnowledgeManager from socratic_knowledge
2. Remove custom KnowledgeManager wrapper
3. Use library's multi-tenancy, RBAC, versioning, semantic search, audit logging
4. Leverage RAG-powered retrieval

**Expected Result**: Enterprise knowledge management system

---

### PRIORITY 9: Integrate socratic-rag

**Current State**: Tries to import, fails
**Target**: Use RAGClient from library

**Files to Modify**:
- `models_local.py` - RAGIntegration class
- `routers/rag.py` - Use library components

**Steps**:
1. Import RAGClient, DocumentStore, Retriever from socratic_rag
2. Remove custom RAG wrapper
3. Use library's multiple vector DB support (ChromaDB, Qdrant, FAISS, Pinecone)
4. Use library's chunking strategies (fixed, semantic, recursive)
5. Enable async operations

**Expected Result**: Production-grade RAG system with multiple vector DB support

---

### PRIORITY 10: Integrate socratic-workflow

**Current State**: Tries to import, fails
**Target**: Use WorkflowEngine from library

**Files to Modify**:
- `models_local.py` - WorkflowIntegration class
- `routers/workflow.py` - Use library

**Steps**:
1. Import WorkflowEngine from socratic_workflow
2. Remove custom WorkflowIntegration
3. Use library's dependency management, cost tracking, parallel execution
4. Use library's error recovery with exponential backoff
5. Enable state management for resilience

**Expected Result**: Production-grade workflow orchestration

---

### PRIORITY 11: Integrate socratic-learning

**Current State**: Tries to import, fails
**Target**: Use LearningEngine from library

**Files to Modify**:
- `models_local.py` - LearningIntegration class
- `routers/learning.py` - Use library

**Steps**:
1. Import LearningEngine, PatternDetector, MetricsCollector, RecommendationEngine from socratic_learning
2. Remove custom LearningIntegration
3. Use library's interaction tracking, pattern detection, performance monitoring
4. Use library's user feedback integration
5. Export fine-tuning data

**Expected Result**: Enterprise-grade continuous learning system

---

### PRIORITY 12: Integrate socratic-analyzer

**Current State**: Tries to import, fails
**Target**: Use CodeAnalyzer from library

**Files to Modify**:
- `models_local.py` - AnalyzerIntegration class
- `routers/analysis.py` - Use library

**Steps**:
1. Import CodeAnalyzer, MetricsCalculator, InsightGenerator, SecurityAnalyzer, PerformanceAnalyzer from socratic_analyzer
2. Remove custom AnalyzerIntegration
3. Use library's static analysis, complexity metrics, pattern detection, security scanning
4. Use library's quality scoring (0-100)

**Expected Result**: Production-grade code analysis with 0-100 quality scoring

---

### PRIORITY 13: Integrate socratic-core

**Current State**: Not used at all
**Target**: Use EventBus, BaseService, Orchestrator, SharedModels from library

**Files to Modify**:
- `orchestrator.py` - Use library Orchestrator
- Multiple routers - Use BaseService if needed
- `models_local.py` - Use SharedModels

**Steps**:
1. Import from socratic_core
2. Use EventBus for event-driven architecture
3. Leverage library's Orchestrator patterns
4. Use SharedModels for consistent data structures

**Expected Result**: Foundation services for entire system

---

### PRIORITY 14: Integrate socratic-docs (OPTIONAL)

**Current State**: Not used
**Target**: Use DocumentationGenerator for auto-docs

**Files to Modify**:
- New endpoint or CLI command

**Steps**:
1. Import DocumentationGenerator from socratic_docs
2. Create endpoint or CLI command to generate docs
3. Auto-generate README, API docs, architecture docs

**Expected Result**: Auto-generated documentation

---

## Installation Steps

```bash
# 1. Update dependencies
pip install -r requirements.txt

# 2. Verify all libraries installed
pip list | grep socratic

# 3. Run import tests
python -c "from socratic_core import *; from socratic_learning import *; from socratic_workflow import *"

# 4. Run backend
cd backend && python -m socrates_api.main
```

---

## Testing Each Integration

For each library integrated:

1. **Import Test**: Verify library imports without error
2. **Functional Test**: Test library methods work as expected
3. **Integration Test**: Test library works with rest of system
4. **E2E Test**: Test complete workflow using library

---

## Success Criteria

✅ All 13 libraries in requirements.txt
✅ All imports at module level (no try/except fallbacks)
✅ All `self.available` flags removed
✅ All custom implementations replaced with library code
✅ No graceful degradation - fail fast if libraries missing
✅ All 40+ endpoints using proper library components
✅ Complete test coverage for library integration
✅ Production-grade reliability from libraries

---

## Expected Impact

**Before**: Custom stubs, graceful fallback, limited features
**After**: Production-grade libraries, fail-fast design, full features

- Security: 4 components (injection, traversal, sandbox, validation)
- Learning: Continuous learning system with pattern detection
- Analysis: Code analysis with 0-100 quality scoring
- Conflict: Multi-strategy conflict resolution
- Maturity: Smart phase tracking that never penalizes advancement
- Performance: Query profiling and TTL caching
- Knowledge: Multi-tenant knowledge management with RAG
- RAG: Multiple vector DB support (ChromaDB, Qdrant, FAISS, Pinecone)
- Workflow: Cost tracking, parallel execution, error recovery
- Agents: 19 specialized agents instead of stubs
- Nexus: Production LLM client with token tracking and caching
- Core: Event bus and orchestrator patterns

---

## Next Action

Ready to implement Priority 1: **socrates-nexus integration**

This is critical because it affects all LLM operations throughout Socrates.
