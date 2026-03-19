# Socrates AI Ecosystem Architecture

## Overview

The Socrates ecosystem has been refactored into a modular, composable architecture where reusable libraries are the foundation, and Socrates serves as an example integration platform.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│              Socrates Nexus (LLM Foundation)                    │
│              (Universal LLM client for all providers)           │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  │ socratic-rag │   │ socratic-    │   │ socratic-    │
  │ (Knowledge   │   │ analyzer     │   │ agents       │
  │  Mgmt)       │   │ (Analysis)   │   │ (20+ agents) │
  └──────────────┘   └──────────────┘   └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────▼────────────────────┐
        │   socratic-knowledge, socratic-learning │
        │   socratic-workflow, socratic-conflict  │
        │   (Composite/advanced features)         │
        └────────────────────┬────────────────────┘
                             │
        ┌────────────────────▼────────────────────┐
        │                                         │
        │      Socratic Core Framework            │
        │      (Configuration, Events, Logging)   │
        │                                         │
        └────────────────────┬────────────────────┘
                ┌────────────┴────────────┐
                │                         │
         ▼──────────────┐          ▼──────────────┐
     ┌──────────────┐  │      ┌──────────────┐   │
     │ socrates-cli │  │      │ socrates-api │   │
     │ (CLI Tool)   │  │      │ (REST API)   │   │
     └──────────────┘  │      └──────────────┘   │
                ├──────┤              │
                │      │              │
                └──────┴──────┬───────┘
                             │
                      ▼──────────────┐
                   ┌─────────────────┘
                   │
            ▼──────────────┐
        ┌───────────────────┐
        │  Socrates (Main)  │
        │  - Orchestrator   │
        │  - Example app    │
        │  - UI/Dashboard   │
        └───────────────────┘
```

## Component Details

### Core Foundation: Socrates Nexus
- **Purpose**: Universal LLM client that supports multiple providers (Claude, GPT-4, Gemini, Ollama)
- **Location**: `/path/to/socrates-nexus` (separate repository)
- **Use**: All AI operations flow through Nexus for consistent LLM interaction
- **Key Classes**: `LLMClient`, `AsyncLLMClient`, `LLMConfig`

### Library Layer: Specialized Tools

#### socratic-rag
- **Purpose**: Retrieval-Augmented Generation with multiple vector stores
- **Providers**: ChromaDB, Qdrant, FAISS, Pinecone
- **Key Classes**: `RAGClient`, `AsyncRAGClient`, `RAGConfig`

#### socratic-agents
- **Purpose**: Multi-agent orchestration with 19+ specialized agents
- **Agents**: ProjectManager, CodeGenerator, SocraticCounselor, etc.
- **Key Classes**: `SocraticCounselor`, `CodeGenerator`, `AgentOrchestrator`, `SkillGeneratorAgent`

#### socratic-analyzer
- **Purpose**: Production-grade code analysis with LLM-powered insights
- **Key Classes**: `AnalyzerClient`, `AnalyzerConfig`
- **Note**: Requires Socrates Nexus (hard dependency)

#### socratic-knowledge
- **Purpose**: Multi-tenant knowledge management with RBAC and versioning
- **Key Classes**: `KnowledgeManager`, `Collection`, `Tenant`

#### socratic-learning
- **Purpose**: Interaction tracking, pattern detection, recommendations
- **Key Classes**: `InteractionLogger`, `RecommendationEngine`, `MaturityCalculator`

#### socratic-workflow
- **Purpose**: Workflow orchestration with cost tracking and analytics
- **Key Classes**: `Workflow`, `WorkflowEngine`, `CostTracker`, `MetricsCollector`

#### socratic-conflict
- **Purpose**: Multi-agent workflow conflict detection and resolution
- **Key Classes**: `ConflictDetector`, `ConflictResolver`, `ConsensusBuilder`

### Framework Layer: socratic-core
- **Purpose**: Core framework components used by CLI, API, and other tools
- **Components**:
  - **Configuration**: `SocratesConfig`, `ConfigBuilder`
  - **Exceptions**: `SocratesError` hierarchy (8 exception types)
  - **Events**: `EventEmitter`, `EventType` (90+ event types)
  - **Logging**: `LoggingConfig`, `PerformanceMonitor`, `JsonFormatter`
  - **Utilities**: ID generators, datetime helpers, TTL cache, etc.
- **Philosophy**: No dependencies on Nexus or other libraries - pure framework
- **Usage**: Imported by socrates-cli, socrates-api, and main Socrates

### Interface Layer

#### socrates-cli
- **Purpose**: Command-line interface to Socrates platform
- **Architecture**: API-first - communicates with socrates-api
- **Dependencies**:
  - Required: `socratic-core`, `click`, `colorama`, `httpx`
  - Optional: `socrates-ai` (for standalone mode)
- **Commands**: project create/list, code generate, init, info
- **Location**: `/socrates-cli`

#### socrates-api
- **Purpose**: REST API server exposing Socrates functionality
- **Architecture**: FastAPI-based with 25+ endpoints
- **Dependencies**:
  - Required: `socratic-core`, `socrates-ai`, `fastapi`, `uvicorn`
  - Optional: `socratic-analyzer`, `socratic-knowledge`
- **Authentication**: JWT-based token authentication
- **Middleware**: Rate limiting, metrics, security headers, activity tracking
- **Location**: `/socrates-api`

### Application Layer: Socrates (Main)
- **Purpose**: Full-featured platform combining all libraries
- **Components**:
  - `socratic_system`: Main library/orchestrator
  - `socrates-cli`: CLI interface
  - `socrates-api`: REST API server
  - UI/Dashboard (separate)
- **Dependencies**: All libraries (required)
- **Architecture**: Centralizes configuration, database, events, agents
- **Role**: Example application showing how to integrate all components

## Data Flow

### Project Creation Flow

```
CLI Request → socrates-api → socrates-ai (Orchestrator) → Nexus (LLM)
                 ↓                ↓
          Database          Agents Process
```

### Code Generation Flow

```
CLI → API → Orchestrator → CodeGenerator Agent → Nexus → Response
         ↓
      Analyzer (optional)
         ↓
      RAG (optional)
```

## Dependency Model

### Dependency Direction (One-Way Only)

```
Socrates (Main)
    ↓
socrates-cli + socrates-api
    ↓
socratic-core
    ↓
All other libraries (optional)
    ↓
socrates-nexus (foundation)
    ↓
External services (APIs, databases)
```

### No Circular Dependencies

- Each layer depends only on layers below it
- Plugins/libraries don't depend on main application
- Libraries are independently usable

## Integration Points

### CLI to API Communication
```python
client = httpx.Client(base_url="http://localhost:8000")
response = client.post("/projects", json={...})
```

### API to Orchestrator Integration
```python
from socratic_system.orchestration import AgentOrchestrator
orchestrator = AgentOrchestrator(config)
result = orchestrator.process_request("agent_type", {...})
```

### Service Initialization
```python
from socratic_core import SocratesConfig
from core.orchestrator import ServiceOrchestrator

config = SocratesConfig.from_env()
service_orchestrator = ServiceOrchestrator()
await service_orchestrator.start_all_services()
```

## Configuration Management

### Configuration Hierarchy

1. **Environment Variables** (highest priority)
   - `ANTHROPIC_API_KEY`, `SOCRATES_DATA_DIR`, `CLAUDE_MODEL`

2. **SocratesConfig** (application configuration)
   - Created from environment or dictionary
   - Used by orchestrator and services

3. **Service Configuration** (service-specific)
   - RAGConfig, AnalyzerConfig, etc.

## Event System

### Event Flow

```
Component → EventEmitter.emit(EventType.X, data)
    ↓
All registered listeners notified
    ↓
Sync and async listeners executed
```

### Event Types (90+)

- **Lifecycle**: AGENT_START, AGENT_COMPLETE, AGENT_ERROR
- **Project**: PROJECT_CREATED, PROJECT_SAVED, PROJECT_DELETED
- **Knowledge**: KNOWLEDGE_LOADED, DOCUMENT_IMPORTED
- **Code**: CODE_GENERATED, CODE_ANALYSIS_COMPLETE
- **System**: SYSTEM_INITIALIZED, TOKEN_USAGE
- **Learning**: LEARNING_METRICS_UPDATED

## Deployment Models

### Model 1: Monolithic (All-in-One)
```
Single Server:
  - Socrates Main
  - CLI (local)
  - API (port 8000)
  - Database
```

### Model 2: Distributed
```
API Server:         CLI Clients:
  - socrates-api      - socrates-cli
  - Database          - HTTP to API
  - Orchestrator

External:
  - Vector DB
  - Cache
```

### Model 3: Microservices
```
API Gateway
    ↓
├─ Projects Service
├─ Code Service
├─ Knowledge Service
└─ Learning Service

Each service:
  - Runs orchestrator
  - Connects to shared DB
```

## Technology Stack

- **Language**: Python 3.8+
- **Web Framework**: FastAPI
- **CLI Framework**: Click
- **Database**: SQLite (default), PostgreSQL (production)
- **Vector DB**: ChromaDB (default)
- **LLM Provider**: Anthropic Claude
- **Cache**: Redis (optional)
- **Async**: asyncio, httpx
- **Validation**: Pydantic
- **Serialization**: JSON, dataclasses
- **Monitoring**: Prometheus metrics

## Key Design Principles

1. **Modularity**: Each library is independently usable
2. **Composition**: Libraries combine for full features
3. **Decoupling**: Event-driven architecture prevents tight coupling
4. **Reusability**: Components designed for multiple use cases
5. **Extensibility**: Plugin architecture for custom agents/services
6. **Type Safety**: Pydantic models for all data structures
7. **Observability**: Comprehensive logging and metrics
8. **Scalability**: Async support, connection pooling, caching

## Migration Path

### From Monolith to Modular (Current Status)

1. ✅ Phase 1: Extract socratic-core (foundation)
2. ✅ Phase 2: Extract libraries (RAG, Agents, etc.)
3. ✅ Phase 3: Create socrates-cli and socrates-api
4. ⏳ Phase 4: Add optional advanced features
5. ⏳ Phase 5: Microservices decomposition (future)

## Future Improvements

1. **Database Abstraction**: Multiple database backends
2. **Message Queue**: Redis/RabbitMQ for async tasks
3. **Caching Layer**: Distributed caching for performance
4. **Authentication**: OAuth2, multi-user support
5. **Rate Limiting**: Advanced rate limiting strategies
6. **Observability**: Distributed tracing, APM integration
7. **Container Support**: Docker, Kubernetes manifests
8. **CLI Plugins**: Plugin system for custom commands
