# Socrates Modularization Implementation Plan

**Status:** In Progress (Phase 1 Starting)
**Date:** April 8, 2026
**Branch:** master (Monolithic-Socrates as reference)
**Target Completion:** 4 weeks

---

## Executive Summary

Transform the Socrates master branch from a hybrid/broken state into a fully functional modularized version by importing and integrating 12 published Socratic libraries while maintaining all workflows, pipelines, and interconnections from the Monolithic-Socrates reference implementation.

### Key Objectives

✅ **Completed (Task #6):**
- Updated all 7 library dependencies to latest PyPI versions
- Added debug_logs consistency across all 16 router endpoints with orchestrator calls
- Verified 25 routers without orchestrator calls (no changes needed)

🔄 **In Progress:**
- Phase 1: Orchestrator restructuring and agent integration
- Phase 2-5: Router fixes, cleanup, and testing

---

## The 12 Published Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| socratic-core | 0.2.0 | EventBus, ServiceOrchestrator, DatabaseClient |
| socratic-agents | 0.2.6 | 18 specialized agent implementations |
| socrates-nexus | 0.3.1 | Universal LLM client (Claude, GPT-4, Gemini, Ollama) |
| socratic-analyzer | 0.1.4 | Code analysis and testing framework |
| socratic-rag | 0.1.0 | Document processing and embeddings |
| socratic-knowledge | 0.1.5 | Enterprise knowledge management with RBAC |
| socratic-conflict | 0.1.2 | Conflict detection with 5 consensus algorithms |
| socratic-learning | 0.1.4 | Interaction tracking and pattern detection |
| socratic-workflow | 0.1.3 | Workflow orchestration |
| socratic-maturity | 0.1.1 | Maturity calculator |
| socratic-performance | 0.1.2 | Query profiling and caching |
| socratic-docs | 0.1.2 | Documentation generation |

---

## Implementation Phases

### Phase 1: Orchestrator Restructuring (Days 1-3)

**Objective:** Refactor central orchestrator to gather full context and coordinate multi-agent flows

**Key Tasks:**

1. **Add Context Gathering Infrastructure**
   - Create `_gather_question_context()` method
   - Include conversation_history, phase, recent messages, knowledge base chunks
   - Build document understanding context
   - Ensure all context passed to agents

2. **Replace Local Agents with Library Imports**
   - Remove dependencies on `socratic_system/agents/`
   - Import from published libraries:
     - SocraticCounselor, ContextAnalyzer from socratic-agents
     - CodeGenerator, ConflictDetector from respective libraries
     - All 18 agents with unified interface

3. **Initialize Agents with Wrapped LLMClient**
   - Apply LLMClientAdapter at initialization (one time only)
   - Initialize all agents with wrapped client
   - Use EventBus from socratic-core for coordination

4. **Add Multi-Agent Coordination Methods**
   - `_orchestrate_question_generation()` - Complete flow with ContextAnalyzer → SocraticCounselor
   - `_orchestrate_answer_processing()` - Answer → Specs → Conflict Detection → Maturity Update
   - Replicate monolithic patterns with library agents

**Critical Files:**
- `backend/src/socrates_api/orchestrator.py` (major refactor)

---

### Phase 2: Router Updates - Fix Context Passing (Days 4-6)

**Objective:** Ensure all routes pass conversation history and return debug_logs

**Priority 1 - Critical Dialogue Flow:**
- `backend/src/socrates_api/routers/projects_chat.py`
- `backend/src/socrates_api/routers/chat.py`
- `backend/src/socrates_api/routers/websocket.py`

**Priority 2 - Secondary Routes:**
- `backend/src/socrates_api/routers/nlu.py`
- `backend/src/socrates_api/routers/code_generation.py`
- `backend/src/socrates_api/routers/analytics.py`

**Priority 3 - Knowledge Routes:**
- `backend/src/socrates_api/routers/knowledge.py`
- `backend/src/socrates_api/routers/free_session.py`
- `backend/src/socrates_api/routers/projects.py`

**Fix Pattern for Each Route:**
```python
# Replace direct agent calls with orchestrator coordination
result = await orchestrator._orchestrate_question_generation(
    project_id=project.project_id,
    user_id=current_user.user_id
)

# Extract and return debug_logs in APIResponse
debug_logs = context.get("debug_logs", []) if context else []
return APIResponse(
    success=True,
    data={...},
    debug_logs=debug_logs  # ALWAYS INCLUDE
)
```

**Status:** 100% debug_logs coverage already implemented (Task #6 complete)

---

### Phase 3: Remove Local Implementations (Days 7-8)

**Objective:** Remove duplicate local agents after verifying library equivalents work

**Audit Plan:**
1. Verify library agent interfaces match usage
2. Update all imports across codebase
3. Run tests to verify functionality
4. Remove files from `socratic_system/agents/`

**Library Mapping:**
| Local Agent | Library Source | Keep/Remove |
|------------|----------------|-------------|
| socratic_counselor.py | socratic-agents | Remove |
| context_analyzer.py | socratic-agents | Remove |
| code_generator.py | socratic-agents | Remove |
| conflict_detector.py | socratic-conflict | Remove |
| quality_controller.py | socratic-maturity | Remove |
| learning_agent.py | socratic-learning | Remove |
| knowledge_manager.py | socratic-knowledge | Remove |
| document_processor.py | socratic-rag | Remove |
| code_validation_agent.py | socratic-analyzer | Remove |

---

### Phase 4: Integrate Missing Library Features (Days 9-10)

**Objective:** Enable advanced features from libraries

**1. Knowledge Base (socratic-rag)**
```python
from socratic_rag import VectorDatabase, DocumentEmbedder

self.vector_db = VectorDatabase(
    path="./data/vector_db",
    embedding_model="all-MiniLM-L6-v2"
)

async def search_similar_adaptive(self, query: str, strategy: str):
    if strategy == "snippet":
        return await self.vector_db.search(query, top_k=3)
    elif strategy == "full":
        return await self.vector_db.search(query, top_k=5)
```

**2. Workflow Engine (socratic-workflow)**
```python
from socratic_workflow import WorkflowEngine, Task

workflow = WorkflowEngine.create_workflow(
    name="socratic_dialogue",
    tasks=[
        Task(name="generate_question", agent="socratic_counselor"),
        Task(name="wait_for_answer", agent="input_handler"),
        Task(name="extract_specs", agent="context_analyzer"),
        Task(name="detect_conflicts", agent="conflict_detector"),
    ]
)
```

**3. Performance Monitoring (socratic-performance)**
```python
from socratic_performance import QueryProfiler

with QueryProfiler("question_generation"):
    result = await self._orchestrate_question_generation(...)

metrics = PerformanceMetrics.get_summary()
```

---

### Phase 5: Testing & Validation (Days 11-12)

**Objective:** Comprehensive testing and performance verification

**1. Unit Tests**
- Test context passing to agents
- Test debug_logs in API responses
- Test library agent integration
- Verify conversation history usage

**2. Integration Tests**
- Full dialogue flow (Question → Answer → Specs → Conflicts → Maturity)
- Context continuity across multiple questions
- Debug visibility in all endpoints
- Library integration correctness

**3. End-to-End Tests**
- Complete project workflow
- Multi-user conversations
- Conflict detection and resolution
- Maturity progression

**4. Performance Tests**
- Question generation < 3 seconds
- Answer processing < 2 seconds
- No memory leaks in context gathering
- Compare vs monolithic baseline

---

## Critical Files to Modify

### Orchestrator (Foundation)
- ✏️ `backend/src/socrates_api/orchestrator.py` (major refactor)

### Routers (Context + Debug Fixes)
- ✏️ `backend/src/socrates_api/routers/projects_chat.py` (critical)
- ✏️ `backend/src/socrates_api/routers/chat.py` (critical)
- ✏️ `backend/src/socrates_api/routers/websocket.py` (critical)
- ✏️ `backend/src/socrates_api/routers/nlu.py`
- ✏️ `backend/src/socrates_api/routers/code_generation.py`
- ✏️ `backend/src/socrates_api/routers/analytics.py`
- ✏️ `backend/src/socrates_api/routers/knowledge.py`
- ✏️ `backend/src/socrates_api/routers/free_session.py`
- ✏️ `backend/src/socrates_api/routers/projects.py`

### Dependencies
- ✅ `requirements.txt` (updated to latest library versions)
- ✅ `pyproject.toml` (updated to latest library versions)

### Cleanup (Phase 3)
- 🗑️ `socratic_system/agents/` (replace with library imports)
- 🗑️ `socratic_system/clients/claude_client.py` (replace with socrates_nexus)
- 🗑️ Local orchestrator implementations

---

## Key Technical Patterns

### 1. Context Gathering Pattern
```python
context = await self._gather_question_context(
    project_id=project_id,
    user_id=user_id
)
# context includes: project_context, phase, recent_messages,
# knowledge_base_chunks, conversation_history, user_role, etc.
```

### 2. Agent Call Pattern
```python
result = await self.agents["agent_name"].method(
    **context  # Pass ALL context including conversation_history
)
debug_logs = context.get("debug_logs", [])
```

### 3. Response Pattern
```python
return APIResponse(
    success=True,
    data=result,
    debug_logs=debug_logs  # ALWAYS INCLUDE
)
```

### 4. Multi-Agent Orchestration
```python
async def _orchestrate_X():
    # 1. Gather context
    context = await self._gather_question_context(...)

    # 2. Call Agent 1
    result1 = await self.agents["agent1"].method(**context)
    context["result1"] = result1

    # 3. Call Agent 2 with updated context
    result2 = await self.agents["agent2"].method(**context)

    # 4. Return coordinated result with debug_logs
    return {..., "debug_logs": context.get("debug_logs")}
```

---

## Success Criteria

### Functional Requirements
- ✅ All routes pass conversation_history to agents
- ✅ All API responses include debug_logs (Task #6 complete)
- ✅ LLMClientAdapter consistently applied (1 time at init)
- ✅ Single-question flow maintained (not batch)
- ✅ Conflict detection works end-to-end
- ✅ Maturity tracking works correctly
- ✅ Phase advancement works properly
- ✅ All agents use library implementations

### Quality Requirements
- Test coverage > 70%
- No direct agent access (all via orchestrator)
- No direct LLMClient calls (all via adapter)
- No duplicate implementations (library vs local)

### Performance Requirements
- Question generation < 3 seconds
- Answer processing < 2 seconds
- No regression vs monolithic baseline
- Memory usage stable over time

---

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|-------------------|
| Library interface mismatch | Keep LLMClientAdapter, add comprehensive tests |
| Breaking changes | Monolithic-Socrates branch remains as reference |
| Performance degradation | Use socratic-performance to profile and optimize |
| Missing library features | Implement feature flags, keep local until verified |

---

## Rollback Strategy

If critical issues arise:
1. Monolithic-Socrates branch remains untouched as fallback
2. Implement feature flags for new components
3. Can revert individual routes independently
4. Database migrations are backwards compatible

---

## Reference Documents

- **Monolithic Reference:** `Monolithic-Socrates` branch (frozen, working)
- **Analysis:** `MODULAR_ARCHITECTURE_ISSUES_ANALYSIS.md`
- **Previous Plan:** `MODULAR_SOCRATES_IMPLEMENTATION_PLAN.md` (7-phase reference)
- **Branch Policy:** `BRANCH_SEPARATION_POLICY.md`

---

## Completed Work Summary

### Task #6: Router Debug_Logs Consistency (100% Complete)

**Summary:**
- Verified all 34 routers in `backend/src/socrates_api/routers/`
- Identified 9 routers with orchestrator/agent calls
- Added debug_logs to all 16 endpoints with agent interactions
- Updated 7 library versions to latest PyPI releases

**Results:**
- 25 routers verified as safe (no orchestrator calls)
- 8 routers modified with debug_logs additions
- 7 git commits pushed with incremental changes
- 100% debug_logs coverage achieved

**Modified Routers:**
1. code_generation.py - 3 endpoints
2. websocket.py - 2 endpoints
3. nlu.py - 1 endpoint
4. projects.py - 5 endpoints
5. knowledge.py - 6 endpoints

---

## Next Steps

1. **Phase 1 Start:** Orchestrator restructuring
   - Begin context gathering infrastructure
   - Start library agent integration
   - Implement multi-agent coordination methods

2. **Continuous Integration:** Git push after each phase
   - Incremental commits with clear messages
   - Maintain working master branch
   - Easy rollback if issues arise

3. **Testing:** Start with unit tests for Phase 1
   - Test context gathering methods
   - Test agent initialization
   - Test LLMClientAdapter wrapping

---

**Last Updated:** April 8, 2026
**Status:** Phase 1 Ready to Start
**Contact:** Implementation via master branch
