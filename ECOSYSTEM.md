# Socrates AI - Complete Ecosystem & Architecture

> **Socrates is a production-ready, modular AI multi-agent orchestration platform.** Choose what you need: full platform, REST API, Python library, or individual components.

## Quick Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 SOCRATES AI ECOSYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Applications (REST API, CLI, React)          │  │
│  └───────────┬─────────────────────────────────────┬────┘  │
│              │                                       │       │
│  ┌───────────▼─────────────┐  ┌──────────────────────▼─┐    │
│  │  socrates-ai Package    │  │  Framework Integrations │   │
│  │  (37+ internal modules) │  │  (LangChain/LangGraph) │   │
│  └───────────┬─────────────┘  └──────────────────────┬─┘    │
│              │                                       │       │
│  ┌───────────▼──────────────────────────────────────▼─┐    │
│  │  8 Specialized socratic-* Libraries                │    │
│  │  (agents, knowledge, workflow, governance, etc.)   │    │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Data & Infrastructure                              │  │
│  │  (PostgreSQL, ChromaDB, Redis, Claude API)          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Value Proposition

Socrates AI enables organizations to:

✅ **Build intelligent agent networks** - Multi-agent orchestration with constitutional governance
✅ **Deploy production systems** - Kubernetes-ready, monitored, scalable from day one
✅ **Integrate with existing tools** - REST API, Python library, framework support (LangChain, LangGraph)
✅ **Make ethical decisions** - Constitutional AI governance built into every agent interaction
✅ **Manage complexity** - Modular architecture: use what you need, ignore the rest

---

## The Two-Layer Architecture

### Layer 1: Core Platform (socrates-ai)

A single unified PyPI package containing 37+ production-ready modules:

```bash
pip install socrates-ai
```

**Included Modules:**

| Category | Modules | Purpose |
|----------|---------|---------|
| **Orchestration** | orchestration, agents, events, services | Request routing, agent coordination, event-driven communication |
| **Knowledge** | knowledge, learning, maturity | RAG systems, user analytics, project progression |
| **Governance** | governance, reasoning, conflict | Constitutional AI, ethical deliberation, specification validation |
| **APIs** | api, api_adapter, adapters | Framework integrations (LangChain, LangGraph, OpenClaw) |
| **Storage** | database, models, repositories | PostgreSQL, SQLite, ChromaDB, vector search |
| **Security** | auth, security, monitoring_metrics | JWT, MFA, RBAC, compliance |
| **Workflow** | workflow, handlers, jobs | Background processing, task management, async operations |
| **Configuration** | config, di_container | Multi-method setup, dependency injection |
| **Utilities** | utils, parsers, docs, exceptions | Helpers, data extraction, error handling |

**37+ Modules = Complete Feature Set**

### Layer 2: Specialized Libraries

Eight independently-published `socratic-*` libraries providing extensible functionality. Each can be used independently or combined for maximum capability.

#### Core Library 1: socratic-morality
**Constitutional AI & Ethical Governance**

[![PyPI](https://img.shields.io/pypi/v/socratic-morality.svg)](https://pypi.org/project/socratic-morality/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-morality.svg)](https://pypi.org/project/socratic-morality/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-morality.svg?style=social)](https://github.com/Nireus79/Socratic-morality)

Use this library to add ethical decision-making to ANY agent system:

```python
from socratic_morality import EthicalGovernor, EthicalFramework
from socratic_morality.reasoning import KantianAnalyzer, UtilitarianAnalyzer

# Initialize governor with multiple ethical frameworks
governor = EthicalGovernor(
    frameworks=[
        KantianAnalyzer(),      # Deontological ethics
        UtilitarianAnalyzer(),  # Consequentialist ethics
    ]
)

# Evaluate agent decisions before execution
decision = {"action": "delete_data", "reason": "privacy"}
is_ethical = await governor.evaluate(decision)

if is_ethical:
    await execute_action(decision)
else:
    await log_ethical_violation(decision)
```

📖 [GitHub](https://github.com/Nireus79/Socratic-morality) | 📦 [PyPI](https://pypi.org/project/socratic-morality/) | Use cases: AI safety, compliance, policy enforcement

---

#### Core Library 2: socratic-agents
**14+ Specialized Agents for Multi-Agent Systems**

[![PyPI](https://img.shields.io/pypi/v/socratic-agents.svg)](https://pypi.org/project/socratic-agents/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-agents.svg)](https://pypi.org/project/socratic-agents/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-agents.svg?style=social)](https://github.com/Nireus79/Socratic-agents)

Drop-in agents for code review, conflict detection, knowledge management, and more:

```python
from socratic_agents import (
    CodeGeneratorAgent, QualityControllerAgent,
    ConflictDetectorAgent, KnowledgeManagerAgent
)

# Create specialized agents
code_gen = CodeGeneratorAgent()
quality_ctrl = QualityControllerAgent()

# Use in your workflow
spec = {"language": "python", "type": "api"}
code = await code_gen.generate(spec)
quality = await quality_ctrl.validate(code)

print(f"Code quality score: {quality.score}")
print(f"Suggestions: {quality.suggestions}")
```

**Agents included:**
- `CodeGeneratorAgent` - Synthesis from specifications
- `QualityControllerAgent` - Code review and quality assessment
- `ConflictDetectorAgent` - Specification validation
- `SocraticCounselorAgent` - Guided questioning
- Plus 10 more specialized agents

📖 [GitHub](https://github.com/Nireus79/Socratic-agents) | 📦 [PyPI](https://pypi.org/project/socratic-agents/) | Use cases: Code review, multi-agent orchestration, specialized tasks

---

#### Core Library 3: socratic-knowledge
**RAG & Semantic Search**

[![PyPI](https://img.shields.io/pypi/v/socratic-knowledge.svg)](https://pypi.org/project/socratic-knowledge/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-knowledge.svg)](https://pypi.org/project/socratic-knowledge/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-knowledge.svg?style=social)](https://github.com/Nireus79/Socratic-knowledge)

Build semantic search into your applications:

```python
from socratic_knowledge import KnowledgeBase, EmbeddingGenerator
from socratic_knowledge.retrieval import SemanticSearcher

# Initialize knowledge base
kb = KnowledgeBase(vector_db="chromadb")
embedder = EmbeddingGenerator(model="claude")
searcher = SemanticSearcher(kb)

# Add documents
await kb.add_document(
    content="Python best practices...",
    metadata={"type": "guide", "language": "python"}
)

# Search semantically
results = await searcher.search(
    query="How should I structure a Python project?",
    limit=3
)

for doc in results:
    print(f"Found: {doc.metadata}")
    print(f"Relevance: {doc.score}")
```

**Features:**
- Multi-document RAG
- Semantic similarity search
- Metadata filtering
- Batch document ingestion
- Embedding caching

📖 [GitHub](https://github.com/Nireus79/Socratic-knowledge) | 📦 [PyPI](https://pypi.org/project/socratic-knowledge/) | Use cases: Document Q&A, research synthesis, knowledge management

---

#### Core Library 4: socratic-nexus
**Inter-Component Communication**

[![PyPI](https://img.shields.io/pypi/v/socratic-nexus.svg)](https://pypi.org/project/socratic-nexus/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-nexus.svg)](https://pypi.org/project/socratic-nexus/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-nexus.svg?style=social)](https://github.com/Nireus79/Socratic-nexus)

Coordinate communication between independent services:

```python
from socratic_nexus import EventEmitter, EventBus

# Publish events
emitter = EventEmitter()

# Service A: Emit event
await emitter.publish("code_generated", {
    "project_id": "proj-123",
    "code": "...",
    "language": "python"
})

# Service B: Subscribe to events
@emitter.on("code_generated")
async def handle_code_generated(event):
    await validate_code(event.payload["code"])
    await notify_user(event.payload["project_id"])
```

**Features:**
- Pub/sub event system
- Async/await throughout
- Event filtering and routing
- Event history tracking
- Extensible event types

📖 [GitHub](https://github.com/Nireus79/Socratic-nexus) | 📦 [PyPI](https://pypi.org/project/socratic-nexus/) | Use cases: Microservices, real-time systems, event-driven architectures

---

#### Feature Library 1: socratic-conflict
**Conflict Detection & Resolution**

[![PyPI](https://img.shields.io/pypi/v/socratic-conflict.svg)](https://pypi.org/project/socratic-conflict/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-conflict.svg)](https://pypi.org/project/socratic-conflict/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-conflict.svg?style=social)](https://github.com/Nireus79/Socratic-conflict)

Validate specifications and detect contradictions:

```python
from socratic_conflict import ConflictDetector, ConflictType

detector = ConflictDetector()

# Check for conflicts
spec = {
    "goals": ["Real-time processing", "Minimal latency"],
    "constraints": ["$500/month budget", "Single machine"],
    "tech_stack": ["Kubernetes", "Raspberry Pi"]
}

conflicts = detector.detect(spec)

for conflict in conflicts:
    if conflict.type == ConflictType.GOAL_vs_CONSTRAINT:
        print(f"Conflict: {conflict.description}")
        print(f"Severity: {conflict.severity}")  # CRITICAL, HIGH, MEDIUM, LOW
```

📖 [GitHub](https://github.com/Nireus79/Socratic-conflict) | 📦 [PyPI](https://pypi.org/project/socratic-conflict/) | Use cases: Requirements validation, project planning, risk assessment

---

#### Feature Library 2: socratic-analyzer
**Analytics & Insight Categorization**

[![PyPI](https://img.shields.io/pypi/v/socratic-analyzer.svg)](https://pypi.org/project/socratic-analyzer/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-analyzer.svg)](https://pypi.org/project/socratic-analyzer/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-analyzer.svg?style=social)](https://github.com/Nireus79/Socratic-analyzer)

Analyze patterns and categorize insights from data:

```python
from socratic_analyzer import InsightAnalyzer, InsightCategory

analyzer = InsightAnalyzer()

# Analyze project data
insights = await analyzer.analyze({
    "project_name": "E-Commerce Platform",
    "phase": "implementation",
    "team_size": 5,
    "timeline": "3 months"
})

# Insights categorized by type
for insight in insights:
    print(f"{insight.category}: {insight.text}")
    print(f"Confidence: {insight.confidence}")
    if insight.recommendations:
        for rec in insight.recommendations:
            print(f"  → {rec}")
```

📖 [GitHub](https://github.com/Nireus79/Socratic-analyzer) | 📦 [PyPI](https://pypi.org/project/socratic-analyzer/) | Use cases: Project analytics, business intelligence, automated insights

---

#### Feature Library 3: socratic-maturity
**Project Maturity Scoring**

[![PyPI](https://img.shields.io/pypi/v/socratic-maturity.svg)](https://pypi.org/project/socratic-maturity/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-maturity.svg)](https://pypi.org/project/socratic-maturity/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-maturity.svg?style=social)](https://github.com/Nireus79/Socratic-maturity)

Track project readiness and progress:

```python
from socratic_maturity import MaturityCalculator

calculator = MaturityCalculator()

# Calculate maturity score
maturity = calculator.score({
    "requirements_completeness": 0.85,
    "architecture_defined": True,
    "testing_coverage": 0.72,
    "documentation_complete": True,
    "team_readiness": 0.90
})

print(f"Overall Maturity: {maturity.score}%")  # 0-100
print(f"Phase Readiness: {maturity.recommended_phase}")
print(f"Blockers: {maturity.blockers}")
```

📖 [GitHub](https://github.com/Nireus79/Socratic-maturity) | 📦 [PyPI](https://pypi.org/project/socratic-maturity/) | Use cases: Project management, phase progression, milestone tracking

---

#### Feature Library 4: socratic-learning
**User Learning Analytics**

[![PyPI](https://img.shields.io/pypi/v/socratic-learning.svg)](https://pypi.org/project/socratic-learning/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-learning.svg)](https://pypi.org/project/socratic-learning/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-learning.svg?style=social)](https://github.com/Nireus79/Socratic-learning)

Track how users interact and learn:

```python
from socratic_learning import LearningTracker, SkillLevel

tracker = LearningTracker()

# Track user interactions
await tracker.record_interaction(
    user_id="user-123",
    action="generated_code",
    topic="python",
    success=True
)

# Get learning progress
progress = tracker.get_progress("user-123", topic="python")
print(f"Skill Level: {progress.skill_level}")  # BEGINNER, INTERMEDIATE, EXPERT
print(f"Topics: {progress.mastered_topics}")
print(f"Next Recommended: {progress.next_topic}")
```

📖 [GitHub](https://github.com/Nireus79/Socratic-learning) | 📦 [PyPI](https://pypi.org/project/socratic-learning/) | Use cases: User profiling, personalization, learning paths

---

#### Feature Library 5: socratic-workflow
**Workflow Execution & Automation**

[![PyPI](https://img.shields.io/pypi/v/socratic-workflow.svg)](https://pypi.org/project/socratic-workflow/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-workflow.svg)](https://pypi.org/project/socratic-workflow/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-workflow.svg?style=social)](https://github.com/Nireus79/Socratic-workflow)

Define and execute multi-step workflows:

```python
from socratic_workflow import WorkflowEngine, Workflow, Step

# Define workflow
workflow = Workflow(
    name="Code Review Pipeline",
    steps=[
        Step(name="analyze", agent="code_analyzer"),
        Step(name="validate", agent="validator", depends_on="analyze"),
        Step(name="suggest", agent="suggester", depends_on="validate"),
    ]
)

# Execute
engine = WorkflowEngine()
result = await engine.execute(workflow, context={
    "code": "def hello(): pass"
})

print(f"Status: {result.status}")  # SUCCESS, PARTIAL, FAILED
for step in result.steps:
    print(f"  {step.name}: {step.output}")
```

📖 [GitHub](https://github.com/Nireus79/Socratic-workflow) | 📦 [PyPI](https://pypi.org/project/socratic-workflow/) | Use cases: Automation, orchestration, multi-step processes

---

#### Feature Library 6: socratic-performance
**Performance Profiling & Metrics**

[![PyPI](https://img.shields.io/pypi/v/socratic-performance.svg)](https://pypi.org/project/socratic-performance/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-performance.svg)](https://pypi.org/project/socratic-performance/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-performance.svg?style=social)](https://github.com/Nireus79/Socratic-performance)

Monitor and optimize system performance:

```python
from socratic_performance import PerformanceMonitor, MetricType

monitor = PerformanceMonitor()

# Track operation
with monitor.measure("code_generation"):
    result = await generate_code(spec)

# Get metrics
metrics = monitor.get_metrics()
print(f"Avg latency: {metrics.avg_latency}ms")
print(f"P95: {metrics.p95_latency}ms")
print(f"Throughput: {metrics.requests_per_sec}")

# Get recommendations
for recommendation in metrics.optimization_suggestions():
    print(f"Consider: {recommendation}")
```

📖 [GitHub](https://github.com/Nireus79/Socratic-performance) | 📦 [PyPI](https://pypi.org/project/socratic-performance/) | Use cases: Performance optimization, bottleneck detection, monitoring

---

#### Feature Library 7: socratic-docs
**Documentation Generation**

[![PyPI](https://img.shields.io/pypi/v/socratic-docs.svg)](https://pypi.org/project/socratic-docs/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-docs.svg)](https://pypi.org/project/socratic-docs/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-docs.svg?style=social)](https://github.com/Nireus79/Socratic-docs)

Auto-generate documentation from code and specs:

```python
from socratic_docs import DocumentationGenerator, DocFormat

generator = DocumentationGenerator()

# Generate from spec
docs = await generator.generate(
    spec={
        "project": "MyProject",
        "modules": [...],
        "endpoints": [...]
    },
    format=DocFormat.MARKDOWN
)

# Customize template
docs.set_template("api", "templates/api-custom.jinja2")
docs.generate_api_docs()
docs.generate_architecture_guide()

# Export
await docs.export(path="./docs", format="pdf")
```

📖 [GitHub](https://github.com/Nireus79/Socratic-docs) | 📦 [PyPI](https://pypi.org/project/socratic-docs/) | Use cases: API documentation, project guides, knowledge bases

---

#### Framework Integrations

Seamlessly integrate Socrates with your existing ecosystem:

```python
# LangChain integration
from socratic_system.api.adapters import create_socrates_tools
from langchain.agents import initialize_agent

tools = create_socrates_tools(
    agent_names=["code_generator", "conflict_detector"]
)
agent = initialize_agent(tools, your_llm, agent=AgentType.REACT)

# LangGraph integration
from socratic_system.api.adapters import create_socrates_nodes
from langgraph.graph import StateGraph

workflow = StateGraph(YourState)
nodes = create_socrates_nodes(agents=["code_generator", "quality_controller"])
for name, fn in nodes.items():
    workflow.add_node(name, fn)
```

📖 [Framework Integrations Guide](FRAMEWORK_INTEGRATIONS.md)

---

## Part A: Complete Module Reference

### A1. Agent Orchestration & Management

**`orchestration/`** - Central request routing and coordination
- `AgentOrchestrator` - Main hub routing requests to agents
- Agent initialization, lifecycle management
- Event emission for system-wide notification
- Service dependency management

**`agents/`** - 14+ specialized agents
- `ProjectManagerAgent` - Project creation and management
- `SocraticCounselorAgent` - Guided questioning
- `CodeGeneratorAgent` - Code synthesis from specs
- `ConflictDetectorAgent` - Specification conflict detection
- `QualityControllerAgent` - Code quality assessment
- `KnowledgeManagerAgent` - Knowledge base curation
- Plus 8 more specialized agents
- All from external `socratic-agents` library

**`events/`** - Event-driven communication
- `EventEmitter` - Publish/subscribe pattern
- 27+ event types (ProjectCreated, CodeGenerated, etc.)
- `JobQueue` for async job processing
- `ResultCache` for result tracking
- Fully async/await compatible

**`services/`** - Service-oriented business logic
- `ProjectService` - CRUD operations, phase management
- `CodeService` - Code generation and validation
- `KnowledgeService` - Knowledge base management
- `ConflictService` - Conflict detection and resolution
- `ValidationService` - Specification validation
- `LearningService` - User analytics
- `DocumentUnderstandingService` - Document processing
- And 2 more specialized services

### A2. Data Management

**`database/`** - Multi-backend persistence
- `ProjectDatabase` - SQL ORM with SQLite/PostgreSQL
- `VectorDatabase` - ChromaDB for semantic search
- Connection pooling, migrations, query profiling
- Automatic schema versioning

**`models/`** - Type-safe data schemas (dataclasses)
- `User` - User accounts, subscriptions, preferences
- `ProjectContext` - Complete project specification
- `KnowledgeEntry` - RAG documents with embeddings
- `TeamMemberRole` - Collaboration roles
- And 30+ additional models

**`repositories/`** - Data access abstraction
- Repository pattern for clean code/data separation
- Query optimization hints
- Transaction support

### A3. Knowledge & Learning

**`knowledge/`** - RAG (Retrieval-Augmented Generation)
- Semantic document search (ChromaDB)
- Embedding generation (Claude embeddings)
- Document chunking strategies
- Retrieved context injection into prompts
- From external `socratic-knowledge` library

**`learning/`** - User analytics & progression
- Learning effectiveness metrics
- User behavior tracking
- Skill development paths
- From external `socratic-learning` library

**`maturity/`** - Project maturity scoring
- Multi-factor maturity calculation
- Phase progression indicators
- Specification completeness assessment
- From external `socratic-maturity` library

### A4. Ethical Governance & Reasoning

**`governance/`** - Constitutional AI decision-making
- `EthicalGovernor` - Validates every agent action
- Governance checks integrated into orchestrator
- Decision logging and audit trails
- From external `socratic-morality` library

**`reasoning/`** - Multi-framework ethical analysis
- Kantian ethics analyzer
- Utilitarian consequence analyzer
- Virtue ethics evaluator
- Rights-based analysis
- Moral precedent search
- Stakeholder impact assessment

**`conflict/`** - Conflict detection & resolution
- Tech stack compatibility checking
- Goal vs. constraints analysis
- Requirement vs. specification validation
- From external `socratic-conflict` library

### A5. Security & Authentication

**`auth/`** - User authentication & authorization
- JWT token generation and validation
- Password hashing (bcrypt)
- Multi-factor authentication (TOTP)
- OAuth integration ready
- Session management

**`security/`** - Security hardening
- OWASP Top 10 protection
- CORS with restrictive defaults
- Rate limiting (5/min free, 100/min pro)
- Input validation and sanitization
- Encrypted database fields
- Security headers (HSTS, CSP, etc.)

### A6. APIs & Framework Integrations

**`api/`** - REST client and request handling
- Claude API integration
- Error handling and retries
- Token usage tracking
- Streaming response support

**`api_adapter/`** - Service adapter framework
- `BaseAdapter` - Base for custom adapters
- `ServiceAdapter` - Service registration
- `ServiceRegistry` - Available services catalog
- Async/sync support

**`api/adapters/`** - Framework integrations
- **LangChain**: Export Socrates agents as LangChain tools
- **LangGraph**: Create state machines with Socrates agents
- **OpenClaw**: Register agents with OpenClaw engine
- Custom adapter support

### A7. Workflow & Background Processing

**`workflow/`** - Workflow automation
- Workflow definition (YAML/Python)
- Conditional routing
- Parallel execution
- Result aggregation
- From external `socratic-workflow` library

**`handlers/`** - Event and background handlers
- Long-running operation support
- Event subscription patterns
- Background job processing
- Async/await throughout

**`jobs/`** - Background job management
- Job queue (Redis-backed)
- Job status tracking
- Result caching
- Retry logic with exponential backoff

### A8. Configuration & Initialization

**`config/`** - Multi-method configuration
- Environment variables
- Dict-based configuration
- Builder pattern (ConfigBuilder)
- Type validation
- 15+ configuration options

**`di_container/`** - Dependency injection
- Service lifecycle management
- Singleton pattern support
- Lazy initialization
- Circular dependency detection

### A9. Monitoring & Performance

**`performance/`** - Performance tracking
- Response time measurement
- Query execution profiling
- Optimization suggestions
- Agent call analytics

**`caching/`** - Result and query caching
- Analysis result caching
- Search query caching
- Embedding cache
- TTL-based expiration

**`monitoring_metrics/`** - Prometheus metrics
- Request counter
- Response latency histogram
- Error rate tracking
- Custom business metrics
- Grafana dashboard integration

### A10. Utilities & Infrastructure

**`utils/`** - Helper functions
- Data validation
- String processing
- Collection utilities
- Async helpers

**`parsers/`** - Data parsing
- Code extraction from specs
- Syntax validation
- Structure analysis
- Language-specific parsers

**`docs/`** - Documentation generation
- API documentation
- Code documentation
- README generation
- From external `socratic-docs` library

**`exceptions/`** - Custom error types
- `SocratesError` - Base exception
- `ValidationError` - Validation failures
- `DatabaseError` - Data persistence issues
- `AuthenticationError` - Auth failures
- `ProjectNotFoundError` - Missing resources
- And 3 more specific exceptions

**`migration/`** - Database migrations
- Alembic integration
- Schema versioning
- Rollback support
- Migration history

---

## Part B: Application Layer

### B1. REST API (socrates-api)

FastAPI backend with 31+ endpoints across 25+ routers:

**Authentication Routes**
- `POST /auth/register` - User registration
- `POST /auth/login` - JWT token generation
- `POST /auth/logout` - Token invalidation
- `POST /auth/refresh` - Token refresh
- `POST /auth/mfa/setup` - MFA configuration

**Project Routes**
- `GET/POST /projects` - List/create projects
- `GET/PUT/DELETE /projects/{id}` - Project CRUD
- `POST /projects/{id}/advance-phase` - Phase progression
- `GET/POST /projects/{id}/team-members` - Team management

**Chat Routes**
- `POST /projects/{id}/chat/sessions` - Create chat
- `POST /projects/{id}/chat/sessions/{sid}/message` - Send message
- `GET /projects/{id}/chat/sessions` - List chats
- `GET /projects/{id}/chat/sessions/{sid}/export` - Export chat

**Knowledge Routes**
- `GET/POST /projects/{id}/knowledge` - Knowledge CRUD
- `GET /projects/{id}/knowledge/search` - Semantic search
- Advanced knowledge operations

**Code Generation Routes**
- `POST /projects/{id}/generate-code` - Generate code
- `POST /projects/{id}/validate-code` - Validate generated code
- Language selection, syntax checking

**Analysis Routes**
- `GET /projects/{id}/analytics` - Project analytics
- `GET /projects/{id}/analytics/detail` - Detailed metrics
- Maturity scores, insights, recommendations

**Real-Time Routes**
- `WebSocket /projects/{id}/collaborate` - Real-time collaboration
- Presence tracking, cursor position sync
- Document synchronization

**GitHub Routes**
- `POST /github/auth` - GitHub OAuth flow
- `POST /github/repo/sync` - Sync repository
- `POST /github/pr/create` - Create pull request
- PR management, issue tracking

**System Routes**
- `GET /health` - Health check
- `GET /health/detailed` - Detailed health metrics
- `GET /metrics` - Prometheus metrics
- `GET /system/config` - Configuration info

**Database Health Routes**
- Database connection diagnostics
- Query performance metrics
- Index optimization suggestions

**Sponsorship Routes**
- GitHub Sponsors verification
- Tier information
- Sponsor management

**Subscription Routes**
- Tier management and verification
- Usage tracking
- Feature flag checking

**Middleware:**
- CORS with security headers
- Rate limiting (Redis-backed)
- JWT validation
- RBAC enforcement
- Request/response logging
- Error handling

### B2. Command-Line Interface (socrates-cli)

Interactive Click-based CLI:

```bash
socrates init                    # Initialize project
socrates project create          # Create new project
socrates project list            # List projects
socrates ask "question"          # Ask Socratic question
socrates generate-code           # Generate code
socrates knowledge add           # Add to knowledge base
socrates --help                  # Show all commands
```

Features:
- Interactive prompts
- Rich formatted output
- Progress indicators
- Error messages with suggestions
- Batch operation support

### B3. Web Frontend (React)

Modern React 19 + TypeScript application:

**Architecture:**
- Vite for fast builds
- TailwindCSS for styling
- Zustand for state management (14+ stores)
- React Query for data fetching
- TypeScript strict mode

**Key Components:**
- **Chat Interface** - Message display, input, conversation history
- **Project Management** - Create, edit, archive projects
- **Code Viewer** - Monaco Editor integration with syntax highlighting
- **Knowledge Base** - Search, add, organize knowledge
- **Analytics Dashboard** - Charts (Recharts), metrics, insights
- **Collaboration Panel** - Team members, roles, permissions
- **Settings** - LLM provider config, account settings

**Real-Time Features:**
- WebSocket integration with fallback polling
- Presence indicators
- Live cursor tracking
- Document synchronization
- Chat message streaming

**State Stores (Zustand):**
- `projectStore` - Current project, projects list
- `chatStore` - Chat sessions, messages, conversation state
- `authStore` - User info, authentication status
- `knowledgeStore` - Knowledge base entries, search results
- `collaborationStore` - Team members, active users
- `llmStore` - LLM provider configuration
- `analyticsStore` - Metrics, insights, performance data
- `subscriptionStore` - User tier, feature access
- `githubStore` - GitHub integration status
- Plus 5 more feature-specific stores

---

## Part C: Integration Patterns

### Pattern 1: Embedded Library Usage

```python
# Install from PyPI
pip install socrates-ai

# Use as a Python library
from socratic_system import AgentOrchestrator
from socratic_system.models import ProjectContext

# Initialize
orchestrator = AgentOrchestrator()

# Use agents directly
project = ProjectContext(name="My Project", description="...", goals=[...])
response = await orchestrator.handle_agent_request(
    agent_name="socratic_counselor",
    action="generate_questions",
    payload={"project": project}
)
```

### Pattern 2: REST API Server

```bash
# Start as server
socrates-api --port 8000

# Make HTTP requests
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer $TOKEN" \
  -d '{...}'
```

### Pattern 3: LangChain Integration

```python
from socratic_system.api.adapters.langchain_integration import create_socrates_tools
from langchain.agents import initialize_agent, AgentType

# Create tools from Socrates agents
tools = create_socrates_tools(agent_names=["code_generator", "conflict_detector"])

# Use with LangChain agent
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)
result = agent.run("Generate Python code for a REST API")
```

### Pattern 4: LangGraph Integration

```python
from socratic_system.api.adapters.langgraph_integration import create_socrates_nodes
from langgraph.graph import StateGraph

# Create workflow
workflow = StateGraph(SocratesState)
nodes = create_socrates_nodes(agents=["code_generator", "quality_controller"])

for name, fn in nodes.items():
    workflow.add_node(name, fn)

workflow.add_edge("code_generator", "quality_controller")
app = workflow.compile()

# Execute workflow
result = await app.ainvoke(state)
```

### Pattern 5: Docker Deployment

```bash
# Build and run with all services
docker-compose -f deployment/docker/docker-compose.yml up -d

# Services available at:
# - API: http://localhost:8000
# - Frontend: http://localhost:3000
# - API Docs: http://localhost:8000/docs
```

### Pattern 6: Kubernetes Deployment

```bash
# Deploy with Helm
helm install socrates ./helm \
  --namespace production \
  --set postgresql.auth.password=$(openssl rand -base64 32)

# Or with kubectl
kubectl apply -f kubernetes/
```

---

## Part D: Deployment Options

| Option | Best For | Complexity | Scaling |
|--------|----------|-----------|---------|
| **Docker Compose** | Development, single machine | Low | Single host |
| **Kubernetes** | Production, multi-cloud | High | Unlimited |
| **Serverless** | API-only, events | Medium | Auto |
| **Managed Services** (AWS/GCP) | Turnkey solution | Low | Auto |
| **Embedded Library** | Custom apps | Low | Application-level |

---

## Part E: Feature Comparison Matrix

| Feature | Community | Pro | Enterprise |
|---------|-----------|-----|-----------|
| **Core Platform** | ✓ | ✓ | ✓ |
| **Agents (14+)** | ✓ | ✓ | ✓ |
| **Knowledge (RAG)** | ✓ | ✓ | ✓ |
| **Governance** | ✓ | ✓ | ✓ |
| **REST API** | ✓ | ✓ | ✓ |
| **CLI Tool** | ✓ | ✓ | ✓ |
| **React UI** | ✓ | ✓ | ✓ |
| **PostgreSQL** | ✓ | ✓ | ✓ |
| **Projects** | 1 | 10 | Unlimited |
| **Team Members** | 1 | 5 | Unlimited |
| **Storage** | 5GB | 100GB | Unlimited |
| **API Rate Limit** | 5/min | 100/min | Unlimited |
| **GitHub Integration** | ✓ | ✓ | ✓ |
| **Kubernetes Support** | Limited | ✓ | ✓ |
| **Priority Support** | ✗ | ✓ | ✓ |
| **SLA** | None | 99.5% | 99.99% |

---

## Part F: Use Cases & Solutions

### Use Case 1: Intelligent Code Review System

**Components Used:**
- `socratic-agents` - CodeAnalyzer, QualityController
- `socratic-knowledge` - Documentation context
- `socratic-morality` - Ethical governance for suggestions
- REST API - Integration with GitHub

**Flow:**
1. PR submitted to GitHub
2. GitHub webhook triggers Socrates API
3. CodeAnalyzer reviews code against standards
4. QualityController scores quality
5. Suggestions sent back as PR comments

### Use Case 2: Research Synthesis Platform

**Components Used:**
- `socratic-knowledge` - RAG for paper retrieval
- `socratic-agents` - DocumentProcessor, KnowledgeManager
- React frontend - Visualization of insights
- REST API - Research API

**Flow:**
1. Upload research papers
2. Knowledge base indexes papers
3. Query synthesis system
4. Receive synthesized insights
5. Generate research report

### Use Case 3: Enterprise Knowledge Assistant

**Components Used:**
- All core components
- PostgreSQL for policies
- `socratic-morality` - Ethical guardrails
- React frontend - Employee interface
- REST API - Integration with HR systems

**Features:**
- Answer employee questions
- Enforce policy compliance
- Track learning patterns
- Suggest relevant documents

### Use Case 4: Embedded AI Agent (LangChain)

**Integration:**
- LangChain integration layer
- `socratic-agents` as tools
- Customer's LLM/RAG system

**Example:**
```python
from socratic_system.api.adapters import create_socrates_tools
tools = create_socrates_tools(agent_names=["conflict_detector"])
agent = initialize_agent(tools, your_llm, agent=AgentType.REACT)
```

---

## Part G: Technology Stack

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool (3-second cold start)
- **TailwindCSS** - Styling
- **Zustand** - State management
- **React Query** - Data fetching
- **Monaco Editor** - Code viewing/editing
- **Recharts** - Data visualization

### Backend
- **Python 3.11+** - Language
- **FastAPI** - Web framework (async)
- **PostgreSQL** - Primary database
- **SQLite** - Development database
- **ChromaDB** - Vector database (RAG)
- **Redis** - Caching and rate limiting
- **Alembic** - Database migrations
- **Pydantic** - Data validation

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Local orchestration
- **Kubernetes** - Production orchestration
- **Helm** - Kubernetes package management
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **GitHub Actions** - CI/CD

### AI/ML
- **Claude API** - LLM backend
- **LangChain** - Framework integration
- **LangGraph** - Workflow orchestration
- **OpenClaw** - Rule engine integration

---

## Part H: Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **API Latency** | < 100ms | P95 response time |
| **Knowledge Search** | < 500ms | Vector similarity search |
| **Code Generation** | 2-30s | Depends on complexity |
| **Concurrent Users** | 1000+ | Per deployment |
| **Requests/sec** | 500+ | Per instance |
| **Agent Throughput** | 100+ agents/sec | Local calls |
| **Database Connections** | 20 pool size | Configurable |
| **Memory per Instance** | 512MB - 2GB | Configurable |
| **Startup Time** | < 5s | Cold start |

---

## Part I: Ecosystem Summary

### What You Get
✅ 37+ production-ready modules
✅ 8 specialized libraries
✅ 3 application interfaces (API, CLI, Web)
✅ 3 framework integrations
✅ 14+ specialized agents
✅ Constitutional AI governance
✅ Real-time collaboration
✅ Complete observability

### Production Ready?
- ✅ Kubernetes manifests included
- ✅ Helm charts for easy deployment
- ✅ Prometheus metrics and Grafana dashboards
- ✅ Database migrations with Alembic
- ✅ Error handling and retries
- ✅ Security hardening (OWASP Top 10)
- ✅ Rate limiting and authentication
- ✅ Comprehensive logging and audit trails

### Enterprise Features?
- ✅ RBAC with 7 roles
- ✅ Multi-tenancy support
- ✅ Encryption at rest and in transit
- ✅ Compliance logging
- ✅ SLA monitoring
- ✅ High availability setup
- ✅ Backup and recovery

---

## Next Steps

1. **Start Locally**: `docker-compose up` (2 minutes)
2. **Explore Features**: Visit http://localhost:3000
3. **Read Architecture**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md)
4. **Deploy**: Follow [PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)
5. **Integrate**: See [FRAMEWORK_INTEGRATIONS.md](FRAMEWORK_INTEGRATIONS.md)

---

**Socrates AI: Intelligent agents for every scale.**
