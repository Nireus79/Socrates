# Socrates Architecture Analysis & Restructuring Plan

**Date**: March 26, 2026
**Status**: APPROVED FOR IMPLEMENTATION
**Vision**: Reusable PyPI developer tools + Socrates as the best example implementation

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Root Causes Identified](#root-causes-identified)
4. [Target Architecture](#target-architecture)
5. [PyPI Library Tier Structure](#pypi-library-tier-structure)
6. [Agent Architecture Deep Dive](#agent-architecture-deep-dive)
7. [Separation of Concerns](#separation-of-concerns)
8. [Implementation Strategy](#implementation-strategy)

---

## EXECUTIVE SUMMARY

### The Problem

Socrates underwent a transition from **monolithic → modular architecture** (moving code from PyPI to local), but the transition was incomplete:

1. **FastAPI dependency injection broken** - 6 instances of direct calls to `Depends()` objects
2. **Conflicting package definitions** - pyproject.toml lists packages that don't exist locally
3. **Database type mismatch** - multiple incompatible database implementations
4. **Orchestrator integration incomplete** - missing method signatures from PyPI refactoring
5. **Architecture unclear** - mixture of local code, PyPI imports, and stub implementations

### The Solution

**Clear Separation of Concerns**:

- **PyPI Tier 1** (Universal Tools): Reusable agent implementations + orchestration framework
- **PyPI Tier 2-3** (Domain Tools): Specialized libraries for analytics, security, RAG, etc.
- **Local Tier** (Socrates Implementation): Infrastructure (REST, CLI) + orchestration logic + business domain

### The Outcome

- ✅ Socrates becomes a **working, maintainable application**
- ✅ PyPI libraries become **genuine developer tools** others can use
- ✅ Clear **architectural boundaries** eliminate confusion
- ✅ **Reusable orchestration framework** for building agent-based systems

---

## CURRENT STATE ANALYSIS

### Codebase Structure

```
Socrates/ (Monorepo)
├── backend/src/socrates_api/          ← REST API Server (LOCAL)
│   ├── routers/                       (35+ FastAPI routers)
│   ├── orchestrator.py                (APIOrchestrator - tries to use PyPI)
│   ├── database.py                    (LocalDatabase - SQLite)
│   ├── auth/                          (Authentication & dependency injection)
│   ├── middleware/                    (HTTP middleware)
│   └── models_local.py                (Stub models - NOT CONNECTED)
│
├── cli/src/socrates_cli/              ← CLI Tool (LOCAL)
│   └── cli.py                         (Click-based commands)
│
├── socratic_system/                   ← Core Business Logic
│   ├── orchestration/                 (Imports PyPI agents & tools)
│   ├── models/                        (Data models)
│   ├── database/                      (Knowledge, projects, vector DB)
│   ├── core/                          (Business logic - maturity, questions, etc.)
│   └── ui/commands/                   (CLI commands)
│
├── socrates-frontend/                 ← React Frontend
│   └── src/api/                       (TypeScript API client)
│
├── pyproject.toml                     ← Dependencies
└── socrates.py                        ← Entry point
```

### Dependencies in pyproject.toml

**Tier 1 - PyPI Packages (Core)**:
- `socrates-nexus>=0.3.0` (LLM client)
- `socratic-core>=0.1.1` (Foundation)
- `socratic-agents>=0.1.2` (Agent implementations) ⚠️

**Tier 2-3 - PyPI Packages (Supporting)**:
- `socratic-security==0.4.0` (Security utilities)
- `socratic-rag>=0.1.0` (Knowledge retrieval)
- `socratic-learning>=0.1.1` (Analytics)
- `socratic-knowledge>=0.1.2` (Knowledge management)
- `socratic-workflow>=0.1.1` (Workflow orchestration)
- `socratic-analyzer>=0.1.1` (Code analysis)
- `socratic-conflict>=0.1.2` (Conflict detection)
- `socratic-docs>=0.1.1` (Documentation generation)
- `socratic-performance>=0.1.1` (Performance monitoring)

**Framework Dependencies**:
- `fastapi>=0.100.0` (REST API)
- `uvicorn[standard]>=0.23.0` (ASGI server)
- `pydantic>=2.0.0` (Data validation)
- `sqlalchemy>=2.0.0` (ORM)
- `redis>=5.0.0` (Caching)
- Plus infrastructure libraries

### Import Analysis

**What's actually imported from PyPI**:

```python
# From socratic-core
from socratic_core import SocratesConfig, EventEmitter, ConfigBuilder, ProjectIDGenerator

# From socrates-nexus
from socrates_nexus import LLMClient, AsyncLLMClient

# From socratic-agents
from socratic_agents import (
    CodeGenerator, CodeValidator, QualityController,
    LearningAgent, SocraticCounselor, ProjectManager,
    SkillGeneratorAgent, ... (14+ agents)
)

# From supporting libraries
from socratic_security import PathValidator, PromptInjectionDetector
from socratic_rag import RAGClient, RAGConfig
from socratic_learning import InteractionLogger, AnalyticsCalculator
# ... etc
```

### Installed vs Referenced

```
socrates-core-api>=0.5.6  ← Listed in pyproject.toml but NOT installed
socrates-cli>=0.1.0       ← Listed in pyproject.toml but NOT installed

Actually installed:
- socratic-agents v0.2.1
- socratic-core v0.1.1
- socrates-nexus v0.3.0
- (9 other socratic-* packages)
```

**Implication**: The code was moved from PyPI packages to local, but dependencies weren't updated.

---

## ROOT CAUSES IDENTIFIED

### 1. INCOMPLETE REFACTORING: FastAPI Dependency Injection ⚠️ CRITICAL

**Location**: 6 instances across 4 routers

```python
# WRONG - calling dependency directly
user_object = await get_current_user_object(current_user)

# CORRECT - declare as parameter
async def create_project(
    current_user: str = Depends(get_current_user),
    user_object: User = Depends(get_current_user_object),  # ← RIGHT HERE
):
```

**Files Affected**:
- `backend/src/socrates_api/routers/projects.py:264`
- `backend/src/socrates_api/routers/analytics.py:89, 483, 592`
- `backend/src/socrates_api/routers/code_generation.py:660`
- `backend/src/socrates_api/routers/github.py:150`

**Why It Breaks**:
- FastAPI doesn't inject dependencies when called directly
- Instead, the `Depends()` object itself is passed
- Calling `.load_user()` on a `Depends` object fails

### 2. DATABASE TYPE MISMATCH ⚠️ HIGH

**Conflict**:
- `get_database()` returns `LocalDatabase` (actual impl)
- Routers expect `ProjectDatabase` type (stub impl)
- `ProjectDatabase` class has empty implementations with `return None`

**Files Involved**:
- `backend/src/socrates_api/database.py` - `LocalDatabase` (working)
- `backend/src/socrates_api/models_local.py` - `ProjectDatabase` (stub, not used)

**Impact**:
- Type checker confusion
- IDE doesn't recognize methods
- Potential runtime errors if code assumes stub methods

### 3. CONFLICTING PACKAGE DEFINITIONS ⚠️ CRITICAL

**What pyproject.toml says**:
```toml
socrates-core-api>=0.5.6
socrates-cli>=0.1.0
```

**What's actually there**:
- Code in `backend/src/socrates_api/` (local)
- Code in `cli/src/socrates_cli/` (local)
- No PyPI imports trying to use `socrates-core-api` or `socrates-cli`

**But**:
- Package still listed in dependencies (confusing)
- If someone runs `pip install -e .`, different package might resolve first
- Creates circular dependency risk

### 4. INCOMPLETE ORCHESTRATOR INTEGRATION ⚠️ MEDIUM

**Error Seen**:
```
AttributeError: 'APIOrchestrator' object has no attribute 'process_request'
```

**Cause**:
- `APIOrchestrator` was supposed to be a wrapper around agents
- It's trying to call methods that don't exist
- Orchestrator definition in PyPI may have changed
- Local implementation doesn't match expected interface

### 5. AGENT INTERCONNECTION LOGIC UNKNOWN ⚠️ MEDIUM

**Before Investigation**: Unclear which agents are reusable vs. Socrates-specific

**After Investigation**: **Clear separation found**:
- **Agents** (algorithm implementations) = REUSABLE
- **PureOrchestrator** (coordination logic) = REUSABLE
- **Maturity System** (phase gating) = SOCRATES-SPECIFIC
- **APIOrchestrator** (REST adapter) = INFRASTRUCTURE

---

## TARGET ARCHITECTURE

### Tier 1: PyPI - Universal Developer Tools (Reusable)

```
Agents (Pure Algorithm Implementations)
├── CodeGenerator (code from prompts)
├── CodeValidator (validates code)
├── QualityController (code quality + maturity integration point)
├── LearningAgent (interaction tracking + personalization)
├── SocraticCounselor (Socratic questioning pedagogy)
├── ProjectManager (project operations)
├── ContextAnalyzer (document/code analysis)
├── DocumentProcessor (document processing)
├── NoteManager (note management)
├── KnowledgeManager (knowledge storage/retrieval)
├── UserManager (user operations)
├── AgentConflictDetector (multi-agent conflict detection)
└── MultiLLMAgent (multi-LLM orchestration)

Orchestration Framework
├── PureOrchestrator
│   ├── Request routing to agents
│   ├── Phase-based gating (customizable)
│   ├── Workflow execution
│   ├── Event emission (callback-based)
│   └── Feedback recording (callback-based)
│
└── WorkflowOrchestrator
    ├── Workflow planning
    ├── Step execution
    ├── Dependency resolution
    └── Error handling strategies

Supporting Libraries (Already on PyPI)
├── socrates-nexus (LLM client)
├── socratic-core (foundation)
├── socratic-security (security utils)
├── socratic-rag (knowledge retrieval)
├── socratic-learning (analytics)
├── socratic-knowledge (knowledge management)
├── socratic-workflow (task orchestration)
├── socratic-analyzer (code analysis)
├── socratic-conflict (conflict resolution)
├── socratic-performance (monitoring)
└── socratic-docs (documentation generation)
```

### Tier 2: Local - Socrates Implementation (Infrastructure + Domain)

```
REST API (Infrastructure)
├── APIOrchestrator (agent instantiation + REST adapter)
├── Routers (35+ FastAPI endpoints)
├── Auth (JWT, password, MFA)
├── Middleware (rate limiting, CORS, security headers)
├── Database (LocalDatabase - SQLite for API layer)
└── Models (REST request/response schemas)

CLI (Infrastructure)
├── Commands (Click-based CLI)
├── Auth (CLI-specific auth)
└── Output formatting

Socrates Orchestration Logic (Domain-Specific)
├── Maturity System
│   ├── MaturityCalculator (phase-based maturity scoring)
│   ├── Phase detection (0-100% mapping to phases)
│   ├── Quality thresholds (phase-specific gating)
│   └── Weak category identification
│
├── Orchestration Integration
│   ├── SocraticLibraryManager (imports PyPI agents + tools)
│   ├── Callback implementations (maturity updates, skill generation)
│   └── Feedback loop implementation
│
└── Workflow Integration
    ├── Socratic-specific workflows
    ├── Project-based workflows
    └── Learning path orchestration

Socrates Business Logic (Domain)
├── Project Management
│   ├── Project creation/update/delete
│   ├── Project phases (discovery, analysis, design, implementation)
│   └── Project metadata
│
├── User/Learning System
│   ├── User profiles
│   ├── Learning velocity
│   ├── Skill effectiveness tracking
│   └── Personalization rules
│
├── Knowledge Management
│   ├── Knowledge base operations
│   ├── Vector search (via socratic-rag)
│   ├── Knowledge versioning (via socratic-knowledge)
│   └── Document processing
│
├── Skill System
│   ├── Skill generation (weak area targeting)
│   ├── Skill application to agents
│   ├── Skill effectiveness tracking
│   └── Personalized skill adaptation
│
└── Database Persistence
    ├── Projects & users (LocalDatabase)
    ├── Knowledge (vector DB via socratic-rag)
    ├── Interactions (learning tracking)
    └── Metrics (analytics)
```

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    Developer's Project                       │
│          (Building any multi-agent system)                   │
└──────────────────────┬───────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼──────┐  ┌────▼────────┐  ┌─▼──────────────┐
   │ PyPI Tier │  │  PyPI Tier  │  │  PyPI Tier 2-3 │
   │  (Agents) │  │ (Orchestr.) │  │  (Supporting)  │
   │           │  │             │  │                │
   │ - 13+ pure│  │ - PureOrch. │  │ - Security     │
   │   agents  │  │ - Workflows │  │ - RAG          │
   │           │  │ - Events    │  │ - Learning     │
   └────┬──────┘  └────┬────────┘  │ - Knowledge    │
        │              │           │ - Analyzer     │
        │              │           │ - Conflict     │
        │              │           │ - Workflow     │
        │              │           │ - Performance  │
        │              │           │ - Docs         │
        │              │           └────────────────┘
        │              │
        └──────────────┼──────────────┐
                       │              │
              ┌────────▼──────────────▼────────────┐
              │                                    │
              │  Socrates (Example Implementation) │
              │                                    │
              ├────────────────────────────────────┤
              │ Infrastructure (Local)             │
              │ - REST API / Routers               │
              │ - CLI Commands                     │
              │ - HTTP Auth / Middleware           │
              ├────────────────────────────────────┤
              │ Orchestration (Local)              │
              │ - Maturity System                  │
              │ - Phase Gating                     │
              │ - SocraticLibraryManager           │
              │ - Callbacks & Feedback Loops       │
              ├────────────────────────────────────┤
              │ Domain Logic (Local)               │
              │ - Project Management               │
              │ - User/Learning System             │
              │ - Knowledge Base                   │
              │ - Skill System                     │
              │ - Database (LocalDatabase)         │
              └────────────────────────────────────┘
```

---

## PYPI LIBRARY TIER STRUCTURE

### Tier 1: Agent Implementations & Orchestration Framework

**Library**: `socratic-agents`

**Current Status**: v0.2.1 on PyPI (probably needs updates)

**Should Contain**:

```
socratic_agents/
├── agents/
│   ├── base.py (BaseAgent abstract class)
│   ├── code_generator.py
│   ├── code_validator.py
│   ├── quality_controller.py
│   ├── learning_agent.py
│   ├── socratic_counselor.py
│   ├── project_manager.py
│   ├── context_analyzer.py
│   ├── document_processor.py
│   ├── note_manager.py
│   ├── knowledge_manager.py
│   ├── user_manager.py
│   ├── agent_conflict_detector.py
│   ├── multi_llm_agent.py
│   ├── skill_generator.py
│   └── __init__.py
│
├── orchestration/
│   ├── orchestrator.py (PureOrchestrator - reusable framework)
│   ├── workflow_orchestrator.py (WorkflowOrchestrator)
│   ├── models.py (Request/Response/Event models)
│   └── __init__.py
│
├── skill_generation/
│   ├── skill_generator.py
│   ├── skill_applier.py
│   └── __init__.py
│
└── __init__.py
```

**Key Requirements**:
- ✅ All agents use dependency injection
- ✅ No database access in agents
- ✅ No REST/HTTP knowledge in agents
- ✅ PureOrchestrator takes callbacks, not direct services
- ✅ Event-driven (callbacks), not side effects
- ✅ Can work with ANY maturity calculation system

**Testing**: 2,300+ tests (per user confirmation)

### Tier 2: Supporting Libraries (Already on PyPI)

| Library | Version | Purpose | Reusability |
|---------|---------|---------|-------------|
| socrates-nexus | 0.3.0 | Multi-provider LLM client | Universal |
| socratic-core | 0.1.1 | Config, events, utilities | Universal |
| socratic-security | 0.4.0 | Security, input validation | Universal |
| socratic-rag | 0.1.0 | Vector search, RAG | Domain (knowledge systems) |
| socratic-learning | 0.1.1 | Analytics, maturity calc | Domain (learning systems) |
| socratic-knowledge | 0.1.2 | Knowledge management | Domain (knowledge systems) |
| socratic-workflow | 0.1.1 | Task orchestration | Domain (workflow systems) |
| socratic-analyzer | 0.1.1 | Code analysis | Domain (dev tools) |
| socratic-conflict | 0.1.2 | Conflict detection | Domain (multi-agent systems) |
| socratic-performance | 0.1.1 | Performance monitoring | Domain (monitoring) |
| socratic-docs | 0.1.1 | Auto-documentation | Domain (dev tools) |

**Status**: All appear correctly implemented

**Update Needed**: Verify they work with new agent framework if socratic-agents is updated

### Tier 3: Infrastructure (Local Only)

**Backend API**:
- REST server (FastAPI + Uvicorn)
- Authentication & Authorization
- Database persistence (SQLite locally, can add PostgreSQL)
- HTTP middleware

**CLI**:
- Command-line interface (Click)
- CLI-specific commands

**Frontend**:
- React application
- TypeScript client library

**Note**: These are infrastructure layers - they call PyPI libraries, they're not called by them

---

## AGENT ARCHITECTURE DEEP DIVE

### Agent Pattern (BaseAgent)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """All agents inherit from this interface"""

    def __init__(self, name: str, llm_client: Optional[Any] = None):
        self.name = name
        self.llm_client = llm_client  # Optional - graceful degradation if not available

    @abstractmethod
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request and return a response.

        Args:
            request: Dict with agent-specific fields

        Returns:
            Dict with response data (agent-specific)
        """
        pass

    async def process_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Async wrapper - default implementation calls process()"""
        return self.process(request)
```

### Agent Independence Characteristics

**Every agent is independent**:
- ✅ Can be instantiated without other agents
- ✅ Has a `process()` method that returns a complete response
- ✅ No direct calls to other agents
- ✅ No side effects (logging, database writes) - returns results only
- ✅ Optional LLM client (can work without)
- ✅ Graceful degradation on missing dependencies

### Example: CodeGenerator

```python
class CodeGenerator(BaseAgent):
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input:
            {
                "prompt": str,
                "language": str,
                "context": Optional[str]
            }

        Output:
            {
                "status": "success" | "error",
                "code": str,
                "language": str,
                "explanation": str
            }
        """
        prompt = request.get("prompt", "")
        language = request.get("language", "python")

        if not self.llm_client:
            return {
                "status": "error",
                "code": "",
                "explanation": "LLM client not available"
            }

        # Call LLM
        response = self.llm_client.create_message(...)

        return {
            "status": "success",
            "code": extracted_code,
            "language": language,
            "explanation": explanation
        }
```

### Example: LearningAgent (More Complex)

```python
class LearningAgent(BaseAgent):
    def __init__(self, name: str = "learning_agent"):
        super().__init__(name)
        self.interactions = []
        self.skill_effectiveness_history = {}
        self.user_profile = {
            "learning_velocity": 1.0,
            "engagement_level": 0.5,
            "difficulty_preference": "medium"
        }
        self.personalization_rules = {}

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        action = request.get("action", "")

        if action == "record_interaction":
            return self._record_interaction(request)
        elif action == "analyze_patterns":
            return self._analyze_patterns(request)
        elif action == "personalize_skills":
            return self._personalize_skills(request)
        elif action == "track_skill_feedback":
            return self._track_skill_feedback(request)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _record_interaction(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Record a user interaction"""
        interaction = {
            "timestamp": datetime.utcnow(),
            "user_id": request.get("user_id"),
            "action": request.get("action_type"),
            "duration": request.get("duration", 0),
            "success": request.get("success", False)
        }
        self.interactions.append(interaction)

        return {
            "status": "success",
            "interaction_recorded": True,
            "total_interactions": len(self.interactions)
        }

    def _personalize_skills(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize skill difficulty and priority"""
        skills = request.get("skills", [])
        user_profile = request.get("user_profile", self.user_profile)

        # Adjust skills based on profile
        personalized = []
        for skill in skills:
            adjusted = self._adjust_skill(skill, user_profile)
            personalized.append(adjusted)

        return {
            "status": "success",
            "personalized_skills": personalized,
            "profile_used": user_profile
        }
```

### How Agents Interconnect (Via Orchestration, Not Direct Calls)

**Important**: Agents don't call each other. Instead, the orchestrator coordinates them:

```
User Makes Request
    ↓
Router extracts data
    ↓
Router calls APIOrchestrator.execute_request()
    ↓
APIOrchestrator calls PureOrchestrator.execute_request()
    ↓
PureOrchestrator checks gating (maturity, phase)
    ↓
PureOrchestrator calls agent.process(request_data)
    ↓
Agent returns response
    ↓
PureOrchestrator emits event: AGENT_EXECUTED
    ↓
Event handler (in Socrates, not in PyPI) receives callback
    ↓
Callback: Record effectiveness, update learning profile,
         detect weak areas, generate new skills
    ↓
LearningAgent state updated (next request will use updated profile)
    ↓
Response returned to user
```

**Key insight**: Agents don't need to know about each other. The **orchestration layer** (local to Socrates) handles the coordination through callbacks and event emission.

### Orchestrator Framework (PureOrchestrator)

```python
class AgentRequest:
    agent_name: str
    action: str
    data: Dict[str, Any]
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None

class CoordinationEvent(Enum):
    WORKFLOW_STARTED = "workflow_started"
    PHASE_GATING_CHECK = "phase_gating_check"
    PHASE_GATE_PASSED = "phase_gate_passed"
    PHASE_GATE_FAILED = "phase_gate_failed"
    AGENT_EXECUTED = "agent_executed"
    FEEDBACK_RECORDED = "feedback_recorded"
    WORKFLOW_COMPLETED = "workflow_completed"

class PureOrchestrator:
    """Framework for orchestrating agents - reusable in ANY system"""

    def __init__(
        self,
        agents: Dict[str, Any],
        get_maturity: Callable[[str, str], float],  # (user_id, phase) -> score
        get_learning_effectiveness: Callable[[str], float],
        on_event: Optional[Callable[[CoordinationEvent, Dict], None]] = None
    ):
        self.agents = agents
        self.get_maturity = get_maturity
        self.on_event = on_event

    def execute_request(
        self,
        request: AgentRequest,
        current_maturity: Optional[float] = None,
        current_phase: Optional[str] = None,
    ) -> AgentResponse:
        """
        Execute agent request with optional phase gating.

        1. Emit WORKFLOW_STARTED
        2. Check phase gating (if gating function provided)
        3. Execute agent if passed
        4. Emit events
        5. Return response
        """
```

**Key Design Principles**:
- Takes **agents as dependencies** - doesn't create them
- Takes **callback functions** - doesn't do I/O itself
- Takes **maturity getter** - doesn't fetch from database
- Event-driven - emits events, others handle side effects
- **Pure coordination logic** - no database, no HTTP, no file I/O

---

## SEPARATION OF CONCERNS

### What Each Layer Does

#### PyPI Libraries (Do Computation)

```
socratic-agents/
├── Agents: Pure algorithm implementations
│   └── Input → Process → Output
│
└── Orchestration Framework: Routing + Workflow logic
    └── Route requests → Execute agents → Emit events

No I/O, No side effects, No database access
```

#### Socrates REST API (Infrastructure - Translates HTTP to Agent Calls)

```
backend/src/socrates_api/
├── Routers: HTTP endpoints
│   └── Parse HTTP → Call orchestrator → Format response
│
├── APIOrchestrator: Adapter between REST and PyPI
│   └── Instantiate agents → Call PureOrchestrator → Handle results
│
├── Database: Local SQLite for API layer
│   └── Persist projects, users, sessions
│
└── Auth/Middleware: HTTP-specific
    └── JWT validation, rate limiting, CORS, etc.
```

#### Socrates Core System (Domain Logic - Ties It All Together)

```
socratic_system/
├── Maturity System: Domain-specific gating logic
│   └── Calculate maturity → Determine phase → Set gating
│
├── Orchestration Integration: Wires PyPI tools to Socrates
│   └── Creates agents → Sets up callbacks → Calls PureOrchestrator
│
├── Business Logic: Socrates-specific workflows
│   └── Project management, skill generation, learning paths
│
└── Database Layer: Knowledge, projects, learning data
    └── Persistent storage via multiple backends
```

### Request Flow (Complete)

```
HTTP Request
└── POST /projects
    └── FastAPI Router (code_generation.py)
        ├── Extract: user, project, requirements
        ├── Authenticate: JWT token → user_id
        ├── Call: APIOrchestrator.execute_request(
        │   agent="code_generator",
        │   action="generate_artifact",
        │   data={...}
        └── )
            └── APIOrchestrator
                ├── Get current user & project
                ├── Get maturity score for user+project
                ├── Get current phase from maturity
                ├── Call: PureOrchestrator.execute_request(...)
                │   └── PureOrchestrator (from PyPI)
                │       ├── Emit: PHASE_GATING_CHECK
                │       ├── Get phase gates for agent
                │       ├── Check: is user mature enough for this phase?
                │       ├── If gated: return gated response
                │       ├── If passed: Emit PHASE_GATE_PASSED
                │       ├── Call: agent.process(request_data)
                │       │   └── CodeGenerator (from PyPI)
                │       │       ├── Use LLM to generate code
                │       │       └── Return {code, explanation, ...}
                │       ├── Emit: AGENT_EXECUTED
                │       └── Return response
                │
                ├── Get response from PureOrchestrator
                ├── Record execution in database
                ├── Update learning profile (callback handling)
                ├── Check if weak areas detected
                ├── Trigger skill generation if needed
                ├── Update maturity score
                └── Return APIResponse to router
                    └── Router formats HTTP response
                        └── HTTP 200 + Generated Code

Total Layers: 5
- HTTP (router)
- Infrastructure (APIOrchestrator)
- Framework (PureOrchestrator from PyPI)
- Algorithm (Agent from PyPI)
- Domain (orchestration integration, database, business logic)
```

### Responsibility Matrix

| Responsibility | PyPI | Local |
|---|---|---|
| Agent algorithm implementation | ✅ | ❌ |
| Request routing to agents | ✅ | ❌ |
| Event emission | ✅ | ❌ |
| Agent instantiation | ❌ | ✅ (in APIOrchestrator) |
| Maturity calculation | ❌ | ✅ (domain-specific) |
| Phase gating callback | ❌ | ✅ (Socrates-specific logic) |
| Event handling (side effects) | ❌ | ✅ (database updates, learning profile changes) |
| HTTP routing | ❌ | ✅ |
| Database persistence | ❌ | ✅ |
| Authentication | ❌ | ✅ |
| CLI commands | ❌ | ✅ |
| Business workflows | ❌ | ✅ |

---

## IMPLEMENTATION STRATEGY

### Phase-Based Approach

**Phase 1**: Update PyPI libraries (if needed) ← START HERE
**Phase 2**: Fix Socrates local code
**Phase 3**: Integration testing
**Phase 4**: Documentation

### Success Criteria

- ✅ All PyPI libraries contain clean, reusable code
- ✅ PureOrchestrator properly documented for use by others
- ✅ Socrates starts without errors
- ✅ Project creation succeeds
- ✅ Agents execute through proper orchestration
- ✅ Maturity system gates appropriately
- ✅ Learning profiles update correctly
- ✅ Skills are generated for weak areas

### Key Decisions Made

✅ **Agents stay on PyPI** - They're pure algorithm implementations
✅ **Orchestration framework stays on PyPI** - It's reusable for any system
✅ **Maturity system moves to local** - It's Socrates-specific gating logic
✅ **REST API moves to local** - It's infrastructure
✅ **CLI moves to local** - It's infrastructure
✅ **Supporting libraries stay on PyPI** - They're tools

### Dependencies for Task Execution

```
Phase 1: Update PyPI
├── Verify socratic-agents exports properly (PureOrchestrator, all agents)
├── Verify PureOrchestrator signature matches Socrates usage
├── Verify no agents have database access
└── Update if needed

Phase 2: Fix Socrates
├── Remove database type mismatch (ProjectDatabase stub)
├── Fix 6 FastAPI dependency injection calls
├── Update APIOrchestrator to properly use PureOrchestrator
├── Implement SocraticLibraryManager (imports + wires PyPI libraries)
├── Verify maturity system is correctly separated
└── Verify orchestration callbacks work

Phase 3: Integration
├── End-to-end project creation
├── Agent execution tests
├── Maturity gating validation
├── Learning profile updates
└── Skill generation

Phase 4: Documentation
├── ARCHITECTURE.md (this file)
├── DEVELOPER_GUIDE.md (how to use PyPI libraries)
├── API_ENDPOINTS.md (Socrates REST API)
└── Inline code documentation
```

---

## NEXT STEPS

### Immediate Actions

1. **Verify PyPI Library Status** (1-2 hours)
   - Check if socratic-agents has PureOrchestrator + agents
   - Check if all dependencies are correct
   - Check if any agents have database access
   - Check if event system is callback-based

2. **Create Task List** (this document, next section)
   - Phase 1 tasks: Library updates
   - Phase 2 tasks: Socrates fixes
   - Phase 3 tasks: Integration
   - Phase 4 tasks: Documentation

3. **Execute Phase 1** (Library updates)
   - Update PyPI libraries if needed
   - Tag releases appropriately
   - Update requirements in pyproject.toml

4. **Execute Phase 2** (Socrates fixes)
   - Fix dependency injection
   - Clean up database layer
   - Implement orchestration integration

5. **Validate Phase 3** (Integration testing)
   - Run end-to-end flows
   - Validate all systems work together

6. **Complete Phase 4** (Documentation)
   - Update README files
   - Create developer guides
   - Document architecture

---

**Status**: Analysis complete. Ready for implementation.
**Confidence**: High (thorough investigation completed)
**Risk**: Low (clear separation of concerns identified)
**Estimated Timeline**: 2-3 weeks for full implementation
