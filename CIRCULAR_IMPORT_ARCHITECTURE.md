# Circular Import Avoidance Architecture - Discovery Document

## How Current Architecture Avoids Circular Imports

The Socrates agent system uses **4 patterns** to avoid circular imports while maintaining agent interconnectivity:

### Pattern 1: Service Locator via Orchestrator Lazy-Loading

**Location:** `socratic_system/orchestration/orchestrator.py` (lines 150+)

Each agent is accessed through an orchestrator property that lazily instantiates it:

```python
@property
def socratic_counselor(self) -> SocraticCounselorAgent:
    """Lazy-load socratic counselor agent"""
    if "socratic_counselor" not in self._agents_cache:
        from socratic_system.agents import SocraticCounselorAgent
        self._agents_cache["socratic_counselor"] = SocraticCounselorAgent(self)
    return self._agents_cache["socratic_counselor"]
```

**Why it avoids circular imports:**
- Agents are NOT imported at orchestrator module level
- Import happens on first property access
- By that time, all other agents are already registered in orchestrator
- No agent needs to import another agent directly

**Initialization order:**
```
1. Orchestrator.__init__()
2. Agent A accesses: orchestrator.agent_b property
3. Agent B is created with orchestrator reference
4. Agent A and B can now communicate via orchestrator
```

### Pattern 2: Process Request Routing (Message Passing)

**Location:** `socratic_system/orchestration/orchestrator.py` (line 466)

Agents communicate via string-based routing, not direct imports:

```python
# In SocraticCounselor (agents/socratic_counselor.py, line 574)
quality_result = safe_orchestrator_call(
    self.orchestrator,
    "quality_controller",  # ← String reference, not import
    {"action": "get_phase_maturity", "project": project}
)
```

**Routing implementation:**
```python
# orchestrator.process_request() maps string names to agents
agents = {
    "quality_controller": self.quality_controller,
    "conflict_detector": self.conflict_detector,
    "document_agent": self.document_processor,
    ...
}
agent = agents.get(agent_name)
result = agent.process(request)
```

**Why it avoids circular imports:**
- Agent A doesn't import Agent B
- Only names are passed as strings
- Orchestrator resolves names at runtime
- No compile-time dependency between agents

**Helper:** `socratic_system/utils/orchestrator_helper.py`
- `safe_orchestrator_call()` wraps all agent calls
- Validates responses
- Handles errors consistently

### Pattern 3: TYPE_CHECKING for Type Hints

**Location:** Throughout all agent files

Type hints don't cause imports at runtime:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from socratic_system.orchestration import AgentOrchestrator

class SocraticCounselorAgent(Agent):
    def __init__(self, orchestrator: "AgentOrchestrator") -> None:
        super().__init__("SocraticCounselor", orchestrator)
        self.orchestrator = orchestrator
```

**Why it works:**
- `TYPE_CHECKING` is False at runtime, so imports don't execute
- Type checkers (mypy) see the type hints
- No circular import at runtime
- Full type safety for development

### Pattern 4: Event-Driven Decoupling

**Location:** `socratic_system/agents/knowledge_analysis.py` (line 45)

Hard dependencies use events instead of direct calls:

```python
# Instead of: counselor = orchestrator.socratic_counselor
# KnowledgeAnalysisAgent listens for events:

self.orchestrator.event_emitter.on(
    EventType.DOCUMENT_IMPORTED, 
    self._handle_document_imported
)
```

**Why it works:**
- No direct agent-to-agent reference needed
- Decoupled through event system
- Sender doesn't need to know about listeners
- Prevents hard coupling

---

## Current Agent Interconnection Map

```
ORCHESTRATOR (AgentOrchestrator)
    ↑ Holds single instance
    |
    +─→ project_manager (ProjectManagerAgent)
    |   ├─→ calls: quality_controller (via process_request)
    |   ├─→ calls: code_validation_agent
    |   └─→ uses: orchestrator.database
    |
    +─→ socratic_counselor (SocraticCounselorAgent)
    |   ├─→ calls: quality_controller
    |   ├─→ calls: conflict_detector
    |   ├─→ calls: document_processor
    |   ├─→ calls: context_analyzer
    |   ├─→ uses: orchestrator.vector_db
    |   └─→ uses: orchestrator.database
    |
    +─→ quality_controller (QualityControllerAgent)
    |   └─→ uses: orchestrator.database
    |
    +─→ conflict_detector (ConflictDetectorAgent)
    |   └─→ no agent calls, only services
    |
    +─→ knowledge_analysis (KnowledgeAnalysisAgent)
    |   ├─→ listens: DOCUMENT_IMPORTED event
    |   ├─→ calls: socratic_counselor (via process_request)
    |   └─→ calls: question_queue
    |
    +─→ [13 other agents]
    |
    └─→ Shared Resources:
        ├─→ database (ProjectDatabase)
        ├─→ vector_db (VectorDatabase)
        ├─→ claude_client (ClaudeClient)
        └─→ event_emitter (EventEmitter)
```

---

## Key Insights for Phase 1 Refactoring

### Must Preserve During Service Extraction:
1. **Lazy-loading pattern** - Services shouldn't all instantiate at once
2. **Service locator** - Agents still route through orchestrator
3. **String-based routing** - Agents call `safe_orchestrator_call()` with service names
4. **Event-driven fallback** - Keep event listeners for loose coupling

### Refactoring Strategy:
```
Phase 1: Extract Services (While keeping agents as routers)
├─→ Create: socratic_system/services/base_service.py
├─→ Create: socratic_system/services/project_service.py
├─→ Create: socratic_system/services/quality_service.py
├─→ Create: socratic_system/services/insight_service.py
├─→ Create: socratic_system/repositories/ (repository pattern)
└─→ Refactor: Agents call services instead of databases

Phase 2: Agent Bus (Replace orchestrator calls)
├─→ Create: socratic_system/messaging/agent_bus.py
├─→ Refactor: Agent calls use agent_bus.send_request() instead of orchestrator
└─→ Add: Timeout, retry, circuit breaker logic

Phase 3: Event-Driven (Remove blocking calls)
├─→ Convert: SocraticCounselor to emit events instead of waiting
├─→ Add: Background listeners for async processing
└─→ Add: Polling endpoints for result retrieval
```

---

## Files Referenced

- **Orchestrator:** `socratic_system/orchestration/orchestrator.py`
- **Agent Base:** `socratic_system/agents/base.py`
- **Helper:** `socratic_system/utils/orchestrator_helper.py`
- **Example Agent:** `socratic_system/agents/socratic_counselor.py`
- **Event Coupling:** `socratic_system/agents/knowledge_analysis.py`
- **Events:** `socratic_system/events.py`

---

## Summary

The system avoids circular imports through:
1. **Lazy instantiation** (no import at module level)
2. **Service locator pattern** (orchestrator routes by string name)
3. **TYPE_CHECKING imports** (no runtime execution)
4. **Event-driven architecture** (for hard dependencies)

Phase 1 must preserve these patterns while extracting business logic into services.
