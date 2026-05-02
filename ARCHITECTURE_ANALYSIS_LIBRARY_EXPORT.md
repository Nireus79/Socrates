# Socrates Agent Architecture Analysis & Library Export Strategy
# ARCHITECTURE_ANALYSIS_LIBRARY_EXPORT.md
## Executive Summary

The Socrates agent system exhibits **moderate-to-high coupling** (Risk Level: 6.5/10) that prevents direct library export without significant refactoring. The primary issue is that agents are directly instantiated and called through the `AgentOrchestrator`, creating Socrates-specific dependencies. This document proposes an **API-first architecture** where agents are accessed via REST/gRPC interfaces rather than direct instantiation, enabling them to be library-exported while maintaining full functionality.

**Recommended Solution: Expose Agents as Microservices through Orchestration Layer**

---

## 1. CURRENT ARCHITECTURE OVERVIEW

### 1.1 Agent Instantiation Pattern

```
AgentOrchestrator (Central Hub)
  ├── Lazy-loads 21 agents on first property access
  ├── Manages: Claude client, databases, event emitter, config
  └── Routes requests: orchestrator.process_request(agent_name, request)

Agent Lifecycle:
  1. Created lazily (first access)
  2. Stored in _agents_cache
  3. Receives orchestrator reference in __init__
  4. Calls to other agents via orchestrator.process_request()
```

### 1.2 Current Dependencies Chain

```
API/CLI Layer
    ↓
AgentOrchestrator (dependency hub)
    ├─→ ProjectDatabase (SQLite)
    ├─→ VectorDatabase (ChromaDB)
    ├─→ ClaudeClient (socratic_nexus)
    ├─→ EventEmitter (internal)
    ├─→ SocratesConfig (config)
    └─→ 21 Agents
        ├─→ Cross-agent calls via orchestrator
        ├─→ Direct database access
        ├─→ Direct Claude API calls
        ├─→ External libraries (socratic_*)
        └─→ File system access
```

### 1.3 Problem: Why Agents Can't Be Exported as Library

| Issue | Impact | Severity |
|-------|--------|----------|
| **Direct orchestrator coupling** | Each agent holds orchestrator reference; can't instantiate without orchestrator | CRITICAL |
| **Circular agent dependencies** | SocraticCounselor orchestrates 6+ agents synchronously | HIGH |
| **Database schema tightly coupled** | Agents directly call database methods; changes require updating all agents | HIGH |
| **Scattered business logic** | Auth handling, validation, insights extraction spread across agents | HIGH |
| **External service dependencies** | Claude API, vector DB, knowledge DB tightly integrated | HIGH |
| **File system access** | Project generation directly writes files via multiple agents | MEDIUM |
| **Event bus coupling** | Event types are hardcoded; agents register listeners directly | MEDIUM |

---

## 2. PROPOSED SOLUTION: API-FIRST AGENT ARCHITECTURE

### 2.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     External Consumers (Library Users)            │
│                                                                   │
│  - Python applications                                            │
│  - Other services                                                │
│  - CLI tools                                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Agent API     │
                    │  (REST/gRPC)    │
                    │                 │
                    │ Adapter Layer   │
                    │ - Request/      │
                    │   Response      │
                    │   Serialization │
                    │ - Error         │
                    │   Handling      │
                    │ - Schema        │
                    │   Validation    │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼────┐          ┌────▼─────┐        ┌────▼─────┐
    │ Service │          │ Messaging │        │ Service  │
    │ Bus     │          │ Bus       │        │ Locator  │
    │         │          │ (Sync)    │        │          │
    └───┬────┘          └────┬─────┘        └────┬─────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │   AgentOrchestrator (Refactored)    │
          │                                     │
          │  - Manages agent lifecycle          │
          │  - Handles cross-agent calls        │
          │  - Event distribution               │
          │  - Shared services (DB, Claude)     │
          └──────────────────┬──────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼────┐          ┌────▼─────┐        ┌────▼─────┐
    │ Agent 1 │          │ Agent 2   │        │ Agent N   │
    │         │          │           │        │           │
    │ • No    │          │ • No      │        │ • No      │
    │   orch. │          │   orch.   │        │   orch.   │
    │   ref.  │          │   ref.    │        │   ref.    │
    │ • DI    │          │ • DI      │        │ • DI      │
    │   only  │          │   only    │        │   only    │
    └────────┘          └───────────┘        └───────────┘
```

### 2.2 Detailed Architecture

#### Phase 1: Create Service Layer (Decoupling)

```python
# NEW: socratic_system/services/base.py
class Service:
    """Base class for all services - no orchestrator dependency"""
    def __init__(self, config: SocratesConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

# NEW: socratic_system/services/project_service.py
class ProjectService(Service):
    """Encapsulates all project-related operations"""
    def __init__(
        self,
        config: SocratesConfig,
        database: ProjectDatabase,
        claude_client: ClaudeClient,
        event_emitter: EventEmitter
    ):
        super().__init__(config)
        self.database = database
        self.claude_client = claude_client
        self.event_emitter = event_emitter

    def create_project(self, spec: ProjectCreateRequest) -> ProjectContext:
        """Create new project - business logic extracted from agent"""
        # Validation
        if not spec.name:
            raise ValueError("Project name required")

        # Extract initial specs using Claude
        specs = self.claude_client.extract_insights(...)

        # Create project object
        project = ProjectContext(
            project_id=generate_id(),
            name=spec.name,
            specs=specs,
            ...
        )

        # Persist
        self.database.save_project(project)

        # Emit event (decoupled)
        self.event_emitter.emit("project.created", {"project_id": project.project_id})

        return project

# NEW: socratic_system/services/quality_service.py
class QualityService(Service):
    """Quality control and maturity tracking"""
    def __init__(
        self,
        config: SocratesConfig,
        maturity_calculator: MaturityCalculator,
        workflow_optimizer: WorkflowOptimizer
    ):
        super().__init__(config)
        self.maturity_calc = maturity_calculator
        self.workflow_optimizer = workflow_optimizer

    def calculate_maturity(self, project: ProjectContext) -> MaturityResult:
        """Calculate phase maturity"""
        return self.maturity_calc.calculate_phase_maturity(...)

# NEW: socratic_system/services/knowledge_service.py
class KnowledgeService(Service):
    """Knowledge management and vector search"""
    def __init__(
        self,
        config: SocratesConfig,
        vector_db: VectorDatabase,
        project_db: ProjectDatabase
    ):
        super().__init__(config)
        self.vector_db = vector_db
        self.project_db = project_db

    def search_knowledge(self, query: str, project_id: str, top_k: int = 5):
        """Search knowledge base"""
        return self.vector_db.search_similar(query, top_k, project_id)

# NEW: socratic_system/services/insight_service.py
class InsightService(Service):
    """Extract and analyze insights"""
    def __init__(
        self,
        config: SocratesConfig,
        claude_client: ClaudeClient,
        context_analyzer: DocumentContextAnalyzer
    ):
        super().__init__(config)
        self.claude_client = claude_client
        self.context_analyzer = context_analyzer

    def extract_insights(self, context: str, project: ProjectContext) -> Insights:
        """Extract insights from context"""
        return self.claude_client.extract_insights(context, project, ...)
```

#### Phase 2: Create Agent Bus (Eliminate Direct Orchestrator Calls)

```python
# NEW: socratic_system/messaging/agent_bus.py
class AgentBus:
    """Message bus for agent-to-agent communication"""

    def __init__(self, event_emitter: EventEmitter):
        self.event_emitter = event_emitter
        self.request_queue = {}  # request_id -> Future
        self.response_listeners = defaultdict(list)

    async def send_request(
        self,
        target_agent: str,
        request: dict,
        timeout: float = 30.0,
        fire_and_forget: bool = False
    ) -> dict:
        """Send request to another agent (replaces orchestrator.process_request)"""
        request_id = generate_id()

        if fire_and_forget:
            self.event_emitter.emit(f"agent.{target_agent}.request", {
                "request_id": request_id,
                "payload": request
            })
            return {"request_id": request_id}

        # Request-response pattern
        future = asyncio.Future()
        self.request_queue[request_id] = future

        self.event_emitter.emit(f"agent.{target_agent}.request", {
            "request_id": request_id,
            "payload": request,
            "reply_to": "agent_bus"
        })

        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            raise AgentTimeoutError(f"{target_agent} timed out after {timeout}s")
        finally:
            del self.request_queue[request_id]

    def register_handler(self, agent_name: str, handler_func):
        """Register handler for agent responses"""
        self.event_emitter.on(f"agent.{agent_name}.response", handler_func)

# Refactored agent (simplified example)
class QualityControllerAgent(Agent):
    """Updated to use AgentBus instead of orchestrator calls"""

    def __init__(
        self,
        name: str,
        agent_bus: AgentBus,        # NEW: AgentBus instead of orchestrator
        maturity_service: QualityService,
        event_emitter: EventEmitter
    ):
        super().__init__(name)
        self.agent_bus = agent_bus
        self.maturity_service = maturity_service
        self.event_emitter = event_emitter

    async def process_async(self, request: dict) -> dict:
        # Old way: orchestrator.process_request("some_agent", {...})
        # New way: agent_bus.send_request("some_agent", {...})

        project = request["project"]

        # Calculate maturity
        maturity = self.maturity_service.calculate_maturity(project)

        # Emit event for interested listeners
        self.event_emitter.emit("quality.maturity_calculated", {
            "project_id": project.project_id,
            "maturity": maturity
        })

        return {
            "maturity_result": maturity,
            "project_id": project.project_id
        }
```

#### Phase 3: Create API Adapter Layer (Library Export)

```python
# NEW: socratic_system/api/adapters/agent_adapter.py
class AgentAdapter:
    """Converts REST/gRPC requests to agent format and vice versa"""

    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator

    async def handle_request(self, agent_name: str, request_data: dict) -> dict:
        """Handle external API request"""
        try:
            # Validate request schema
            schema = self.get_schema(agent_name)
            validated = schema.validate(request_data)

            # Route to agent
            response = await self.orchestrator.process_request_async(
                agent_name,
                validated
            )

            # Convert response
            return self.serialize_response(response)

        except ValidationError as e:
            return {"error": "invalid_request", "details": str(e)}
        except AgentError as e:
            return {"error": "agent_error", "details": str(e)}

# NEW: socratic_system/api/rest_handlers.py (FastAPI)
from fastapi import FastAPI, HTTPException
from socratic_system.api.adapters import AgentAdapter

app = FastAPI()

@app.post("/agents/{agent_name}/process")
async def process_agent_request(agent_name: str, request: dict):
    """REST endpoint for agent requests"""
    adapter = AgentAdapter(orchestrator)
    result = await adapter.handle_request(agent_name, request)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result

# NEW: socratic_system/api/grpc_handlers.py
class AgentServiceGRPC(agent_pb2_grpc.AgentServiceServicer):
    """gRPC service for agents"""

    def __init__(self, orchestrator: AgentOrchestrator):
        self.adapter = AgentAdapter(orchestrator)

    async def ProcessRequest(self, request, context):
        result = await self.adapter.handle_request(
            request.agent_name,
            request.payload
        )
        return agent_pb2.ProcessResponse(result=result)

# NEW: socratic_system/api/client.py (Library User Interface)
class SocratesAgentClient:
    """Library client for accessing agents"""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.http_client = httpx.AsyncClient()

    async def project_manager(self, request: dict) -> dict:
        """Call ProjectManager agent"""
        return await self._call_agent("project_manager", request)

    async def socratic_counselor(self, request: dict) -> dict:
        """Call SocraticCounselor agent"""
        return await self._call_agent("socratic_counselor", request)

    async def code_generator(self, request: dict) -> dict:
        """Call CodeGenerator agent"""
        return await self._call_agent("code_generator", request)

    async def _call_agent(self, agent_name: str, request: dict) -> dict:
        response = await self.http_client.post(
            f"{self.api_url}/agents/{agent_name}/process",
            json=request
        )
        response.raise_for_status()
        return response.json()

# Example library usage (AFTER refactoring)
async def main():
    # User of the library - NO DEPENDENCY on Socrates internals
    client = SocratesAgentClient("http://socrates-api.internal:8000")

    # Create project
    project = await client.project_manager({
        "action": "create",
        "name": "My Project",
        "description": "..."
    })

    # Ask question
    response = await client.socratic_counselor({
        "action": "get_question",
        "project_id": project["id"],
        "user_id": "user_123"
    })

    # Generate code
    code = await client.code_generator({
        "action": "generate",
        "project_id": project["id"],
        "language": "python"
    })
```

---

## 3. INTERCONNECTION MAP

### 3.1 Agent Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│ CORE ORCHESTRATION AGENTS                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ProjectManager                                                 │
│    ├──→ QualityController (maturity checks) [BLOCKING]         │
│    ├──→ CodeValidation (GitHub validation) [BLOCKING]          │
│    ├──→ Claude (extract_insights)                              │
│    └──→ Database (project persistence)                         │
│                                                                 │
│  SocraticCounselor (BOTTLENECK - 6 orchestrator calls)         │
│    ├──→ QualityController (post-response maturity)             │
│    ├──→ ConflictDetector (response validation)                 │
│    ├──→ DocumentProcessor (context analysis)                   │
│    ├──→ QuestionSelector (question generation)                 │
│    ├──→ WorkflowOptimizer (workflow decisions)                 │
│    ├──→ ContextAnalyzer (insight generation)                   │
│    ├──→ Claude (multiple calls)                                │
│    ├──→ VectorDatabase (context retrieval)                     │
│    └──→ Database (project updates, file tracking)              │
│                                                                 │
│  QualityController                                              │
│    ├──→ MaturityCalculator (socratic_maturity)                 │
│    ├──→ WorkflowOptimizer (socratic_workflow)                  │
│    └──→ Database (maturity scores)                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ KNOWLEDGE MANAGEMENT AGENTS                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  KnowledgeAnalysis                                              │
│    ├──→ SocraticCounselor (HARD COUPLING - direct property)    │
│    ├──→ VectorDatabase (document indexing)                     │
│    ├──→ Claude (insight analysis)                              │
│    └──→ Listens: KNOWLEDGE_SUGGESTION events                   │
│                                                                 │
│  KnowledgeManager                                               │
│    ├──→ VectorDatabase (add_knowledge, search)                 │
│    ├──→ Database (knowledge persistence)                       │
│    └──→ Listens: KNOWLEDGE_SUGGESTION events                   │
│                                                                 │
│  DocumentProcessor                                              │
│    ├──→ ContextAnalyzer (document analysis)                    │
│    ├──→ VectorDatabase (chunking, embedding)                   │
│    ├──→ Claude (artifact generation)                           │
│    └──→ FileSystem (artifact storage)                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ GENERATION & CODE AGENTS                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CodeGenerator                                                  │
│    ├──→ Claude (generate_artifact, generate_documentation)     │
│    ├──→ MultiFileCodeSplitter (project structure)              │
│    ├──→ ProjectStructureGenerator (folders/files)              │
│    ├──→ ArtifactSaver (file writing)                           │
│    └──→ Database (project files tracking)                      │
│                                                                 │
│  CodeValidationAgent                                            │
│    ├──→ GitRepositoryManager (GitHub operations)               │
│    ├──→ GitHub API (repo creation, PR operations)              │
│    └──→ Database (validation results)                          │
│                                                                 │
│  MultiLLMAgent                                                  │
│    ├──→ Claude (multiple models via config)                    │
│    ├──→ Database (LLM config storage)                          │
│    └──→ Credential management (per-user auth)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ UTILITY & MONITORING AGENTS                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  UserLearningAgent                                              │
│    ├──→ LearningEngine (socratic_learning)                     │
│    ├──→ Database (learning records)                            │
│    └──→ VectorDatabase (behavior patterns)                     │
│                                                                 │
│  ConflictDetector                                               │
│    ├──→ ConflictCheckers (4 parallel: TechStack, Requirements, │
│    │     Goals, Constraints) from socratic_conflict library    │
│    └──→ ThreadPoolExecutor (parallel execution)                │
│                                                                 │
│  ContextAnalyzer                                                │
│    ├──→ VectorDatabase (context search)                        │
│    ├──→ DocumentContextAnalyzer (document parsing)             │
│    └──→ Database (context caching)                             │
│                                                                 │
│  SystemMonitor                                                  │
│    ├──→ SubscriptionChecker (quota validation)                 │
│    ├──→ Database (usage tracking)                              │
│    └──→ EventEmitter (monitoring events)                       │
│                                                                 │
│  UserManager, NoteManager, ProjectFileLoader                   │
│    └──→ Database (CRUD operations)                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Service Dependencies (After Refactoring)

```
┌─────────────────────────────────────────────────────────────────┐
│ SHARED INFRASTRUCTURE                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  • SocratesConfig (configuration, defaults)                    │
│  • ProjectDatabase (SQLite, persistence layer)                 │
│  • VectorDatabase (ChromaDB, embeddings)                       │
│  • ClaudeClient (API wrapper, per-user auth)                   │
│  • EventEmitter (publish-subscribe, decoupling)                │
│  • Logger (observability)                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Each Service receives ONLY what it needs via DI:

┌─────────────────────────────────────────────────────────────────┐
│ SERVICE DEPENDENCIES (Dependency Injection)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ProjectService(config, database, claude, event_emitter)       │
│  QualityService(config, maturity_calc, workflow_opt)           │
│  KnowledgeService(config, vector_db, project_db)               │
│  InsightService(config, claude, context_analyzer)              │
│  CodeService(config, claude, code_splitter, artifact_saver)    │
│  ConflictService(config, conflict_checkers)                    │
│  ValidationService(config, github_manager)                     │
│  LearningService(config, learning_engine, vector_db)           │
│                                                                 │
│  Each service has EXPLICIT dependencies (no hidden coupling)   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. OPTIMIZATION SOLUTIONS

### 4.1 Problem: SocraticCounselor Bottleneck

**Current State:**
```
User Response → SocraticCounselor.process()
  ├─→ orchestrator.process_request("quality_controller", {...}) [WAIT 2s]
  ├─→ orchestrator.process_request("conflict_detector", {...}) [WAIT 1.5s]
  ├─→ orchestrator.process_request("document_processor", {...}) [WAIT 1.5s]
  ├─→ orchestrator.process_request("workflow_optimizer", {...}) [WAIT 1s]
  └─→ Return to user

Total latency: ~6s (sequential)
```

**Optimized State (Event-Driven Post-Processing):**
```
User Response → SocraticCounselor.process()
  ├─→ Store response in database
  ├─→ Emit "response.received" event
  │   ├─→ (Async) Quality metrics calculation
  │   ├─→ (Async) Conflict detection
  │   ├─→ (Async) Document processing
  │   └─→ (Async) Workflow optimization
  └─→ Return to user immediately

Total latency: ~100ms (non-blocking)
Results collected asynchronously and cached
```

**Implementation:**
```python
# OLD: Blocking orchestrator calls
async def _process_response(self, response: str, project: ProjectContext):
    quality = await self.orchestrator.process_request_async("quality_controller", {...})
    conflicts = await self.orchestrator.process_request_async("conflict_detector", {...})
    # ... blocking calls
    return {"response": response, "quality": quality, "conflicts": conflicts}

# NEW: Event-driven, non-blocking
async def _process_response(self, response: str, project: ProjectContext):
    # Store immediately
    self.database.save_response(response, project.project_id)

    # Emit events for background processing
    self.event_emitter.emit("response.received", {
        "project_id": project.project_id,
        "response": response,
        "timestamp": now()
    })

    # Return immediately
    return {
        "response": response,
        "status": "accepted",
        "analysis_pending": True  # Client polls for results
    }

# Background listeners
@self.event_emitter.on("response.received")
async def process_quality(data):
    quality = await self.quality_service.calculate_maturity(...)
    self.cache.set(f"quality:{data['project_id']}", quality)
    self.event_emitter.emit("quality.analyzed", data)

@self.event_emitter.on("response.received")
async def process_conflicts(data):
    conflicts = await self.conflict_service.detect(...)
    self.cache.set(f"conflicts:{data['project_id']}", conflicts)
    self.event_emitter.emit("conflicts.analyzed", data)
```

### 4.2 Problem: Direct Agent-to-Agent Coupling

**Current State:**
```python
# Direct orchestrator.process_request calls throughout SocraticCounselor
result = self.orchestrator.process_request("quality_controller", request)
# If quality_controller fails, entire workflow fails
```

**Optimized State (AgentBus with Resilience):**
```python
# Use agent bus with timeout and retry logic
try:
    result = await self.agent_bus.send_request(
        "quality_controller",
        request,
        timeout=5.0,
        fire_and_forget=False  # Request-response pattern
    )
except AgentTimeoutError:
    # Circuit breaker: don't retry if service down
    result = self.get_cached_result(project_id) or SAFE_DEFAULT
except AgentError:
    # Graceful degradation
    result = SAFE_DEFAULT
    self.event_emitter.emit("warning.quality_unavailable", {})
```

### 4.3 Problem: Database Schema Tightly Coupled to Agents

**Current State:**
```python
# Scattered across agents
self.database.save_project(project)
project = self.database.load_project(project_id)
self.database.save_knowledge_document(doc)
scores = self.database.get_category_scores(project_id)
# Each agent knows database schema
```

**Optimized State (Repository Pattern):**
```python
# Centralized repositories
project_repo.save(project)
project = project_repo.load(project_id)
knowledge_repo.save(doc)
scores = maturity_repo.get_scores(project_id)

# Single point of change for schema updates
# Agents depend on interface, not implementation
```

### 4.4 Problem: KnowledgeAnalysis Hard-Coupled to SocraticCounselor

**Current State:**
```python
class KnowledgeAnalysisAgent(Agent):
    def __init__(self, name, orchestrator):
        self.orchestrator = orchestrator
        # Direct property access - breaks if counselor not initialized
        self.counselor = self.orchestrator.counselor

    def process(self, request):
        # Hard dependency on counselor instance
        response = self.counselor.process(request)
```

**Optimized State (Event-Driven):**
```python
class KnowledgeAnalysisAgent(Agent):
    def __init__(self, name, agent_bus, event_emitter):
        self.agent_bus = agent_bus
        self.event_emitter = event_emitter
        # Register event listeners
        self.event_emitter.on("counselor.ready", self.on_counselor_ready)

    def process(self, request):
        # Send request via agent bus
        return await self.agent_bus.send_request("socratic_counselor", request)

    @self.event_emitter.on("response.analyzed")
    async def on_response_analyzed(self, data):
        # React to events, don't call directly
        insights = self.extract_insights(data)
        self.event_emitter.emit("insights.extracted", insights)
```

### 4.5 Problem: Scattered Claude API Client Usage

**Current State:**
```python
# Different patterns in different agents
class ProjectManager:
    async def create(self, spec):
        specs = self.orchestrator.claude_client.extract_insights(...)
        auth = get_user_auth(spec.user_id)  # Scattered logic
        return specs

class CodeGenerator:
    async def generate(self, project):
        artifact = self.orchestrator.claude_client.generate_artifact(...)
        auth = get_user_auth(project.owner_id)  # Duplicated logic
        return artifact
```

**Optimized State (Service Layer):**
```python
class InsightService:
    """Centralized insight extraction with auth handling"""
    def extract_insights(self, context, project, user_id):
        auth = self.auth_manager.get_user_auth(user_id)
        return self.claude_client.extract_insights(
            context,
            project,
            auth.method,  # oauth, api_key, or subscription_token
            user_id
        )

class CodeService:
    """Centralized code generation with auth handling"""
    def generate_artifact(self, project, user_id):
        auth = self.auth_manager.get_user_auth(user_id)
        return self.claude_client.generate_artifact(
            project,
            auth.method,
            user_id
        )

# In agents: just use the service
class ProjectManager:
    def __init__(self, insight_service):
        self.insight_service = insight_service

    async def create(self, spec):
        specs = self.insight_service.extract_insights(
            spec.description,
            project=None,  # Creating new project
            user_id=spec.user_id
        )
        return specs

class CodeGenerator:
    def __init__(self, code_service):
        self.code_service = code_service

    async def generate(self, project, user_id):
        artifact = self.code_service.generate_artifact(project, user_id)
        return artifact
```

---

## 5. MIGRATION ROADMAP

### Phase 1: Service Layer Creation (2-3 weeks)
- [ ] Create `socratic_system/services/` directory
- [ ] Extract business logic from agents into services
- [ ] Create: ProjectService, QualityService, KnowledgeService, InsightService, CodeService
- [ ] Implement Repository pattern for database access
- [ ] Add dependency injection container

### Phase 2: Agent Bus Implementation (1-2 weeks)
- [ ] Create AgentBus for message routing
- [ ] Replace orchestrator.process_request() calls with agent_bus.send_request()
- [ ] Add timeout/retry logic and circuit breakers
- [ ] Implement fire-and-forget vs request-response patterns

### Phase 3: Event-Driven Refactoring (2-3 weeks)
- [ ] Create event listeners for background processing
- [ ] Refactor SocraticCounselor to emit events instead of blocking
- [ ] Implement result caching for async operations
- [ ] Add polling/websocket endpoints for client result retrieval

### Phase 4: API Adapter Layer (1-2 weeks)
- [ ] Create REST endpoints (`/agents/{agent_name}/process`)
- [ ] Implement gRPC service definitions
- [ ] Build AgentAdapter for serialization/deserialization
- [ ] Add schema validation for all requests

### Phase 5: Library Export (1 week)
- [ ] Create `SocratesAgentClient` library client
- [ ] Document public API
- [ ] Create example implementations
- [ ] Update dependencies to optional/extras

### Phase 6: Testing & Validation (2-3 weeks)
- [ ] Write integration tests for refactored architecture
- [ ] Performance testing: latency improvements
- [ ] Load testing: parallel agent processing
- [ ] Backward compatibility testing

---

## 6. EXPECTED IMPROVEMENTS

### Performance
- SocraticCounselor response latency: 6s → 100ms (60x faster user-facing response)
- Background analysis: continues asynchronously
- Parallel processing: conflict detection, quality checks run concurrently

### Decoupling
- Agent hard dependencies: 3 critical → 0
- Database schema coupling: 10+ agents → Repository pattern (1 point of change)
- Agent instantiation: requires orchestrator → DI only
- Testability: mocking dependencies becomes straightforward

### Exportability
- Agents callable via REST/gRPC API
- No Socrates-specific imports required for library users
- Authentication abstracted through service layer
- Database persistence decoupled via repositories

---

## 7. BACKWARD COMPATIBILITY

The refactoring can be done incrementally without breaking existing code:

```python
# Phase 1-3: Both patterns coexist
class AgentOrchestrator:
    # Old interface (deprecated but working)
    async def process_request(self, agent_name, request):
        # Route through new agent bus internally
        return await self.agent_bus.send_request(agent_name, request)

    # Existing agents still work
    @property
    def counselor(self):
        return self._agents_cache.get("socratic_counselor")

# Phase 4: New API exposed alongside old
@app.post("/agents/{agent_name}/process")  # NEW
async def process_agent_request(agent_name, request):
    ...

@app.post("/process")  # OLD (still works, calls new endpoint)
async def legacy_process(request):
    agent_name = request.pop("agent_name")
    return await process_agent_request(agent_name, request)

# Phase 5: Library exports both patterns
client = SocratesAgentClient()  # NEW: REST-based
client.legacy.project_manager = orchestrator.project_manager  # OLD: Direct access
```

---

## 8. EXAMPLE: Library Usage After Refactoring

```python
# User's application (no Socrates internals dependency)
from socrates import SocratesAgentClient

async def build_project():
    client = SocratesAgentClient(
        api_url="http://socrates-api.company.internal:8000",
        auth_token="api_key_xxx"
    )

    # Create project
    project = await client.project_manager({
        "action": "create",
        "name": "E-Commerce Platform",
        "description": "Multi-tenant SaaS platform",
        "user_id": "user_123"
    })

    print(f"Project created: {project['id']}")

    # Start discovery phase
    question = await client.socratic_counselor({
        "action": "get_question",
        "project_id": project["id"],
        "phase": "discovery",
        "user_id": "user_123"
    })

    print(f"Question: {question['content']}")

    # User answers
    response = await client.socratic_counselor({
        "action": "process_response",
        "project_id": project["id"],
        "response": "We're targeting small businesses initially...",
        "user_id": "user_123"
    })

    print(f"Response accepted: {response['status']}")

    # Poll for analysis results (non-blocking)
    import asyncio
    for _ in range(10):  # Poll up to 10 times
        analysis = await client.socratic_counselor({
            "action": "get_analysis",
            "project_id": project["id"],
            "user_id": "user_123"
        })

        if analysis["ready"]:
            print(f"Quality score: {analysis['maturity']}")
            print(f"Conflicts detected: {len(analysis.get('conflicts', []))}")
            break

        await asyncio.sleep(1)

    # Generate code
    code = await client.code_generator({
        "action": "generate",
        "project_id": project["id"],
        "language": "python",
        "user_id": "user_123"
    })

    print(f"Generated {len(code['files'])} files")

    return project

# Run it
asyncio.run(build_project())
```

---

## 9. RISK ANALYSIS & MITIGATION

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **Breaking existing code during refactoring** | Medium | High | Maintain backward-compatible interfaces; deprecation period |
| **Performance regression** | Low | High | Benchmark before/after; profile async overhead |
| **Event ordering issues** | Medium | Medium | Add event ordering guarantees; idempotent handlers |
| **Distributed system complexity** | High | High | Start with single-process; add distribution later |
| **Message queue bottleneck** | Low | Medium | Use async queue; monitor throughput |
| **Database transaction issues** | Medium | High | Use DB transactions; test concurrent access |

---

## 10. CONCLUSION

The proposed **API-first architecture** with **service layer abstraction** and **agent bus messaging** provides:

1. **Clear separation of concerns** - Services handle business logic, agents handle orchestration
2. **Library exportability** - REST/gRPC API allows external library usage without Socrates coupling
3. **Performance improvements** - Non-blocking architectureremoves bottlenecks
4. **Testability** - DI makes mocking dependencies straightforward
5. **Scalability** - Event-driven async processing enables horizontal scaling

**Recommendation:** Begin with Phase 1 (Service Layer) as it provides immediate value and unblocks subsequent phases without breaking existing code.

