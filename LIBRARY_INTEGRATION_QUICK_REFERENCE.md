# 12 Modular Libraries: Quick Integration Reference

## TL;DR: Can They Replace Built-in Agents?

| Library | Safe Import | Replace Agent | Use as Utility | Critical Issue |
|---------|---|---|---|---|
| **socratic_analyzer** | ✅ | ⚠️ Need adapter | ✅ | Different API signatures |
| **socratic_knowledge** | ✅ | ❌ | ✅ | Own database, no events |
| **socratic_learning** | ✅ | ⚠️ Need adapter | ✅ | No async, own DB |
| **socratic_rag** | ✅ | ❌ | ✅ | Own ChromaDB instance |
| **socratic_conflict** | ✅ | ⚠️ Need adapter | ✅ | Not an Agent subclass |
| **socratic_workflow** | ✅ | ❌ | ✅ | Not agent-like |
| **socratic_nexus** | ✅ | ⚠️ Can wrap | ✅✅ | NO ISSUES - SAFEST |
| **socratic_docs** | ✅ | ❌ | ✅ | Docs only, not agents |
| **socratic_performance** | ✅ | ❌ | ✅ | Utility only |
| **socratic_core** | ⚠️ | ❌ | ⚠️ | DUPLICATION RISK |
| **socratic_agents** | ⚠️ | ? | ⚠️ | Editable install (unstable) |
| **socrates_maturity** | ✅ | N/A | ✅ | Already integrated |

---

## Critical Problems Summary

### Problem 1: Different Method Signatures ❌

```python
# MONOLITH AGENT (what orchestrator expects)
agent.process(request: Dict) -> Dict

# LIBRARY CLIENTS (what libraries provide)
analyzer.analyze(code: str) -> Analysis
llm_client.message(prompt: str) -> ChatResponse
rag_client.retrieve(query: str) -> List[Document]
```

**Fix**: Create adapter that translates.

### Problem 2: No Event Emission ❌

```python
# MONOLITH: Events are fired
self.emit_event(EventType.CODE_GENERATED, {...})
# ↓ UI listens and updates

# LIBRARIES: Silent execution
analyzer.analyze(code)  # No event fired!
# ↓ UI doesn't know anything happened
```

**Fix**: Wrapper must emit events after library calls.

### Problem 3: Database Isolation ❌

```python
# MONOLITH uses one database
orchestrator.database = DatabaseSingleton.get_instance()
orchestrator.vector_db = VectorDatabase(...)

# LIBRARIES create own databases
rag_client = RAGClient()  # ← Creates own ChromaDB!
learning_engine = LearningEngine()  # ← Creates own SQLite!

# Result: Multiple DB connections instead of unified layer
```

**Fix**: Pass orchestrator's database to libraries.

### Problem 4: No Orchestrator Context ❌

```python
# MONOLITH AGENT has access to
self.orchestrator.project_manager
self.orchestrator.vector_db
self.orchestrator.database
self.orchestrator.event_emitter

# LIBRARY CLIENT has access to
None - completely isolated!

# Example: Library can't check project constraints
# Example: Library can't access knowledge base
# Example: Library can't notify other agents
```

**Fix**: Pass orchestrator reference to libraries.

### Problem 5: Initialization Incompatibility ❌

```python
# MONOLITH: Simple init from orchestrator
agent = SocraticCounselorAgent(orchestrator)

# LIBRARIES: Complex init with dependencies
client = LLMClient(provider="anthropic", api_key="...", model="...")
client = AnalyzerClient(config=AnalyzerConfig(...), llm_client=...)
client = RAGClient(embeddings=Embeddings(...), vector_store=...)

# None can be initialized with just orchestrator
```

**Fix**: Provide factory methods or adapt init.

---

## Safe Integration Patterns

### Pattern A: Use Libraries as Internal Utilities (✅ SAFE)

```python
# In agent class
from socratic_nexus import AsyncLLMClient

class SocraticCounselorAgent(Agent):
    def __init__(self, name: str, orchestrator):
        super().__init__(name, orchestrator)
        # Initialize library as utility
        self.llm = AsyncLLMClient(
            provider="anthropic",
            api_key=orchestrator.config.api_key,
            model=orchestrator.config.claude_model
        )

    def process(self, request: Dict) -> Dict:
        try:
            # Use library internally
            response = self.llm.message(request['prompt'])

            # Return in monolith format
            return {
                'status': 'success',
                'response': response.content,
                'tokens': response.usage.total_tokens
            }
        except Exception as e:
            # Emit error event
            self.emit_event(EventType.AGENT_ERROR, {'error': str(e)})
            return {'status': 'error', 'error': str(e)}
```

**Pros**: ✅ Works immediately, no changes to libraries
**Cons**: ❌ Code duplication if multiple agents use same library

### Pattern B: Create Agent Adapter Wrapper (⚠️ MODERATE)

```python
# New file: socratic_system/agents/analyzer_adapter.py
from socratic_analyzer import AnalyzerClient
from socratic_system.agents.base import Agent

class AnalyzerAgentAdapter(Agent):
    """Wraps socratic_analyzer as a monolith Agent"""

    def __init__(self, name: str, orchestrator):
        super().__init__(name, orchestrator)
        self.analyzer = AnalyzerClient(
            config=AnalyzerConfig(llm_client=...)
        )

    def process(self, request: Dict) -> Dict:
        try:
            # Translate monolith request → library format
            code = request.get('code', '')
            language = request.get('language', 'python')

            # Call library
            analysis = self.analyzer.analyze(code, language=language)

            # Emit monolith event
            self.emit_event(EventType.CODE_ANALYSIS_COMPLETE, {
                'issues_count': len(analysis.issues),
                'complexity': analysis.code_metrics.get('cyclomatic_complexity', 0)
            })

            # Translate library response → monolith format
            return {
                'status': 'success',
                'data': {
                    'issues': [dict(issue) for issue in analysis.issues],
                    'metrics': analysis.code_metrics
                }
            }
        except Exception as e:
            self.emit_event(EventType.AGENT_ERROR, {'error': str(e)})
            return {'status': 'error', 'error': str(e)}

# In orchestrator.py
@property
def context_analyzer(self) -> Agent:
    if "context_analyzer" not in self._agents_cache:
        from socratic_system.agents.analyzer_adapter import AnalyzerAgentAdapter
        self._agents_cache["context_analyzer"] = AnalyzerAgentAdapter(self)
    return self._agents_cache["context_analyzer"]
```

**Pros**: ✅ Full integration, proper event emission
**Cons**: ❌ Requires per-library wrapper code

### Pattern C: Configuration-Based Switching (✅ BEST)

```python
# In config
class SocratesConfig:
    # New: Specify which libraries to use
    agent_providers: Dict[str, str] = {
        'context_analyzer': 'library:socratic_analyzer',  # Use library
        'code_generator': 'built_in',                     # Use monolith
        'socratic_counselor': 'library:socratic_nexus',   # Use library
    }

# In orchestrator
def _create_agent(self, agent_name: str, agent_class: str):
    provider = self.config.agent_providers.get(agent_name, 'built_in')

    if provider.startswith('library:'):
        library_name = provider.split(':')[1]
        return self._create_library_adapter(agent_name, library_name)
    else:
        # Use built-in agent class
        return agent_class(agent_name, self)

@property
def context_analyzer(self) -> Agent:
    if "context_analyzer" not in self._agents_cache:
        self._agents_cache["context_analyzer"] = self._create_agent(
            'context_analyzer',
            ContextAnalyzerAgent
        )
    return self._agents_cache["context_analyzer"]
```

**Pros**: ✅ Flexible, can enable per-agent, easy to test
**Cons**: ⚠️ Requires config structure changes

---

## Per-Library Integration Guide

### 1. socratic_nexus ✅✅✅ RECOMMENDED

**Status**: SAFEST library, HIGHEST quality
**Recommended Use**: Replace ClaudeClient directly

```python
# Current code (monolith)
from socratic_system.clients import ClaudeClient
self.claude_client = ClaudeClient(self.config.api_key, self)

# Can be replaced with (library)
from socratic_nexus import AsyncLLMClient
self.llm_client = AsyncLLMClient(
    provider="anthropic",
    api_key=self.config.api_key,
    model=self.config.claude_model
)

# Benefits:
# ✅ Multi-provider support (Claude, GPT-4, Gemini)
# ✅ Better error handling
# ✅ Cost tracking built-in
# ✅ Async native
# ✅ Vision support
```

**Action**: Can use NOW - no adapters needed

### 2. socratic_analyzer ✅ GOOD

**Status**: Good library, different API
**Recommended Use**: Use as utility in agents

```python
from socratic_analyzer import AnalyzerClient

analyzer = AnalyzerClient(config=...)
analysis = analyzer.analyze(code)

# Use results inside agents
# Don't try to make it an Agent subclass (incompatible)
```

**Action**: Use internally via Pattern A (utility)

### 3. socratic_rag ✅ GOOD

**Status**: Solid library, isolated database
**Recommended Use**: Enhance vector search

**Problem**: Creates own ChromaDB instance
**Solution**: Share orchestrator's vector_db

```python
# Don't do this (creates duplicate DB):
rag_client = RAGClient(embeddings=..., vector_store=ChromaDB())

# Do this instead:
from socratic_rag import RAGClient
rag_client = RAGClient(
    embeddings=self.config.embeddings,
    vector_store=self.vector_db.chroma  # Share orchestrator's DB!
)
```

**Action**: Use with shared database connection

### 4. socratic_learning ✅ GOOD

**Status**: Good library, lacks async
**Recommended Use**: Learning analytics

**Problem**: No async support, own database
**Solution**: Keep isolated or migrate to unified DB later

```python
from socratic_learning import LearningEngine

learning_engine = LearningEngine(
    storage=self.database,  # Share if possible
    config=...
)
```

**Action**: Use as utility, add async wrapper if needed

### 5. socratic_conflict ✅ GOOD

**Status**: Good library, could be agent
**Recommended Use**: Multi-agent arbitration

**Problem**: Not an Agent subclass
**Solution**: Wrap in adapter if replacing ConflictDetectorAgent

```python
from socratic_conflict import ConflictDetector

# As utility (✅ easier)
detector = ConflictDetector()
resolution = detector.resolve(proposals)

# As agent replacement (⚠️ needs adapter)
class ConflictDetectorAgentAdapter(Agent):
    def __init__(self, orchestrator):
        super().__init__("conflict_detector", orchestrator)
        self.detector = ConflictDetector()

    def process(self, request):
        proposals = request.get('proposals', [])
        resolution = self.detector.resolve(proposals)
        self.emit_event(EventType.CONFLICT_RESOLVED, ...)
        return {'status': 'success', 'resolution': ...}
```

**Action**: Use as utility first, wrap only if needed

### 6. socratic_workflow ✅ GOOD

**Status**: Good library, not agent-like
**Recommended Use**: Task pipeline orchestration

```python
from socratic_workflow import WorkflowEngine

workflow = WorkflowEngine()
workflow.add_task(Task(...))
result = workflow.execute()
```

**Action**: Use for complex workflows above agent level

### 7. socratic_knowledge ✅ GOOD

**Status**: Good library, own database
**Recommended Use**: Knowledge metadata layer

```python
from socratic_knowledge import KnowledgeManager

# Metadata management on top of vector_db
knowledge_mgr = KnowledgeManager(storage_path=...)
collection = knowledge_mgr.create_collection("project_a")
```

**Action**: Use independently, don't replace KnowledgeEntry

### 8. socratic_performance ✅ GOOD

**Status**: Good utility library
**Recommended Use**: Caching and profiling

```python
from socratic_performance import TTLCache, cached

# Memoize expensive operations
@cached(ttl_seconds=3600)
def expensive_analysis(code: str):
    return analyzer.analyze(code)

# Profile queries
profiler = QueryProfiler()
with profiler.profile("vector_search"):
    results = vector_db.search(query)
```

**Action**: Use directly, good for optimization

### 9. socratic_docs ✅ GOOD

**Status**: Documentation utility
**Recommended Use**: Auto-generate API docs

```python
from socratic_docs import APIDocumentationGenerator

generator = APIDocumentationGenerator()
docs = generator.generate_from_openapi(schema)
```

**Action**: Use for docs only, no integration needed

### 10. socratic_core ⚠️ CAUTION

**Status**: REVIEW BEFORE USE
**Issue**: Potential duplication with monolith

**Concern**: May have:
- Duplicate SocratesConfig
- Duplicate AgentOrchestrator
- Duplicate EventBus
- Duplicate database utilities

**Action**: AUDIT FIRST - check what it exports and what monolith already has

### 11. socratic_agents ⚠️ UNCLEAR

**Status**: Editable install (unstable)
**Issue**: Points to temp directory, unclear purpose

**Action**: CLARIFY PURPOSE - determine if it's meant to replace monolith agents

### 12. socrates_maturity ✅ ALREADY USED

**Status**: Already integrated in monolith
**Use**: Maturity calculations for agents

**Action**: No changes needed, already working

---

## Implementation Checklist

To safely integrate libraries into orchestrator:

### Phase 1: Utility Integration (SAFE NOW) ✅

- [ ] Add `socratic_nexus` as LLM provider wrapper
- [ ] Add `socratic_analyzer` for code analysis
- [ ] Add `socratic_rag` for enhanced vector search
- [ ] Add `socratic_performance` for caching

```python
# In orchestrator.__init__
from socratic_nexus import AsyncLLMClient
from socratic_analyzer import AnalyzerClient
from socratic_rag import RAGClient
from socratic_performance import TTLCache

self.llm_provider = AsyncLLMClient(...)
self.code_analyzer = AnalyzerClient(...)
self.rag_search = RAGClient(...)
self.cache = TTLCache()
```

### Phase 2: Agent Adapter Integration (MODERATE) ⚠️

- [ ] Create adapter for `socratic_analyzer` → ContextAnalyzerAgent
- [ ] Create adapter for `socratic_nexus` → Socratic Counselor
- [ ] Create adapter for `socratic_conflict` → ConflictDetectorAgent
- [ ] Test each adapter independently

### Phase 3: Database Unification (HARD) ❌

- [ ] Make libraries accept orchestrator's database
- [ ] Consolidate multiple DB connections
- [ ] Migrate library data to monolith DB schema
- [ ] Add transaction management across libraries

### Phase 4: Event System Integration (HARD) ❌

- [ ] Add event emission to library wrappers
- [ ] Standardize event types
- [ ] Test UI responsiveness
- [ ] Add event logging/tracking

---

## What Actually Works Right Now (NO CHANGES NEEDED)

```python
# These imports work perfectly
from socratic_nexus import AsyncLLMClient, LLMClient
from socratic_analyzer import AnalyzerClient
from socratic_rag import RAGClient
from socratic_knowledge import KnowledgeManager
from socratic_learning import LearningEngine
from socratic_conflict import ConflictDetector
from socratic_workflow import WorkflowEngine
from socratic_docs import DocumentationGenerator
from socratic_performance import TTLCache

# Use them as utilities in agents immediately
# No breaking changes to monolith
# No database conflicts
# No event system conflicts
```

---

## Summary: The Honest Answer

**Can libraries replace built-in agent implementations?**

❌ **No, not directly.** But...

✅ **They can be used as utilities inside agents.**

✅ **They can be wrapped with adapters.**

⚠️ **Some are better than others** (nexus is excellent).

❌ **Core issues that need fixing**: database isolation, event system decoupling, API signature mismatch.

**Recommendation**: Use libraries as utilities first (Phase 1), avoid replacing agents directly without proper integration work (Phase 2-4).

**Best immediate action**: Replace `ClaudeClient` with `socratic_nexus.AsyncLLMClient` - it's an improvement with zero breaking changes.
