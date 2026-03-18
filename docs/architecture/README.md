# Architecture Documentation

Complete architectural design for Socrates AI modular platform v2.0

## Documents in This Directory

### 1. [SOCRATES_AI_MODULAR_PLATFORM_ARCHITECTURE.md](SOCRATES_AI_MODULAR_PLATFORM_ARCHITECTURE.md)
**Complete system architecture design**
- 6 independent service modules
- Dependency graph and service relationships
- BaseService pattern specification
- ServiceOrchestrator design
- EventBus publish-subscribe system
- Deployment modes (single-process vs microservices)
- Data flow diagrams
- Skill generation integration

**Use this if**: You need to understand the overall system design

---

### 2. [SOCRATES_AI_ECOSYSTEM_INTEGRATION_PLAN.md](SOCRATES_AI_ECOSYSTEM_INTEGRATION_PLAN.md)
**Integration roadmap with 8 ecosystem libraries**
- socrates-nexus (LLM provider abstraction)
- socratic-agents (Agent framework)
- socratic-knowledge (Knowledge management)
- socratic-analyzer (Analysis pipeline)
- socratic-learning (Learning system)
- socratic-workflow (Workflow orchestration)
- socratic-conflict (Conflict resolution)
- socratic-rag (Retrieval-Augmented Generation)

**Use this if**: You want to understand how ecosystem libraries integrate

---

### 3. [MIGRATION_MAPPING.md](MIGRATION_MAPPING.md)
**File-by-file mapping of code reorganization**
- Current location → New location for all files
- Dependencies between modules
- Import path changes
- Validation checklists
- Rollback procedures
- Statistics on code movement

**Use this if**: You need to understand exactly where each piece of code moved

---

## Architecture Overview

### 6 Independent Services

```
┌─────────────────────────────────────────────────────┐
│                  API Layer (FastAPI)                 │
├─────────────────────────────────────────────────────┤
│                   ServiceOrchestrator                │
│                 (Central Coordination)               │
├──────────────┬──────────────┬──────────────┬────────┤
│   Agents     │  Learning    │  Knowledge   │Workflow│
│   Service    │  Service     │  Service     │Service │
│              │              │              │        │
│ • Execute    │ • Track      │ • Search     │• Build │
│   agents     │   learning   │   knowledge  │  DAGs │
│ • Manage     │ • Generate   │ • Manage     │• Cost  │
│   skills     │   skills     │   vectors    │  track │
└──────────────┴──────────────┴──────────────┴────────┘
│   Analytics  │             Foundation Service       │
│   Service    │  • LLM Service (Claude client)       │
│              │  • Database Service (SQLite/Vector)  │
│ • Metrics    │  • Connection Pool & Cache           │
│ • Insights   │  • Event Emitter                     │
└──────────────┴──────────────────────────────────────┘
```

### Service Dependencies

```
Foundation Service (No dependencies)
├── LLM Service
├── Database Service
├── Connection Pool
└── Event Emitter

Knowledge Service (depends on Foundation)
├── Vector DB
└── Knowledge Base

Learning Service (depends on Foundation)
├── Learning Engine
└── SkillGeneratorAgent

Agents Service (depends on Foundation + Learning)
├── Agent Base Class
└── 20 Agent Implementations

Workflow Service (depends on Foundation + Agents)
├── Workflow Builder
├── Workflow Optimizer
└── Cost Calculator

Analytics Service (depends on Foundation)
├── Metrics Calculator
└── Insights Generator
```

### Communication Patterns

1. **Direct Service Calls** (synchronous)
   ```python
   agent_service = orchestrator.get_service("agents")
   result = await agent_service.execute_agent(...)
   ```

2. **Event Bus** (asynchronous)
   ```python
   event_bus.publish("skill_generated", "learning", {...})
   # Subscribers notified automatically
   ```

3. **Foundation Services** (shared)
   ```python
   llm = foundation_service.get_llm_service()
   db = foundation_service.get_database_service()
   ```

## Deployment Modes

### Single-Process (Development)
- All services in one container
- Simple local development
- Docker Compose setup
- Low resource requirements

### Microservices (Production)
- Each service in separate container
- Kubernetes orchestration
- Auto-scaling with HPA
- Load balancing
- Health checks and auto-healing

## Skill Generation Flow

```
1. Agent executes task
   ↓
2. Learning module tracks interaction
   ↓
3. Interaction stored in database
   ↓
4. Learning service analyzes patterns
   ↓
5. If skill trigger met:
   a) Get maturity data from DB
   b) Get learning metrics
   c) Call SkillGeneratorAgent
   d) Receive new skills
   ↓
6. Skills stored in database
   ↓
7. Next agent execution:
   a) Check available skills
   b) Apply skills to agent
   c) Execute with enhanced capabilities
   ↓
8. Track skill effectiveness
   ↓
9. Skills improve over time
```

## Key Design Decisions

### 1. BaseService Pattern
- Abstract base class for all services
- Consistent lifecycle (initialize, shutdown, health_check)
- Standard interface for service coordination
- Easy to test and extend

### 2. ServiceOrchestrator
- Central coordinator for all services
- Manages startup/shutdown sequence
- Routes requests between services
- Health monitoring and recovery

### 3. EventBus
- Publish-subscribe system
- Loose coupling between services
- Asynchronous communication
- Event history tracking

### 4. Dependency Isolation
- Foundation layer has zero dependencies
- Other services depend only on Foundation
- No circular dependencies
- Clear dependency graph

### 5. Dual Deployment
- Single-process for development
- Microservices for production
- Same code, different deployment
- Easy transition from dev to prod

## Next Steps

1. **Phase 1**: Complete module restructuring (in progress)
2. **Phase 2**: Implement full service layer with orchestration
3. **Phase 3**: Integrate SkillGeneratorAgent for skill generation
4. **Phase 4**: Implement REST APIs and deploy to both modes
5. **Phase 5**: Release v2.0.0 to production

---

**Architecture Version**: 2.0
**Status**: Design Complete, Implementation in Progress
**Last Updated**: March 16, 2026
