# Socrates AI Ecosystem Architecture

## Overview

The Socrates AI ecosystem is a modular, composable architecture designed for building intelligent educational and development systems using the Socratic method with Claude AI. **`socrates-ai`** is the main wrapper package that orchestrates and integrates all components of the ecosystem.

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                     socrates-ai (v1.3.4)                           │
│              Main Wrapper / Orchestrator Package                    │
│          Integrates all libraries and frameworks below              │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┬─────────────────────┐
        │                  │                  │                     │
        ▼                  ▼                  ▼                     ▼
  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐
  │CORE LAYER   │  │FEATURE LAYER │  │INTEGRATION   │  │ socrates-nexus  │
  │             │  │              │  │LAYER         │  │(LLM Abstraction)│
  │- socratic-  │  │- socratic-   │  │              │  │                 │
  │  core       │  │  rag         │  │- socrates-ai-│  │Supports:        │
  │- socratic-  │  │- socratic-   │  │  langraph    │  │- Claude         │
  │  agents     │  │  learning    │  │- socrates-ai-│  │- GPT-4          │
  │- socratic-  │  │- socratic-   │  │  openclaw    │  │- Gemini         │
  │  security   │  │  analyzer    │  │              │  │- Ollama         │
  │             │  │- socratic-   │  │              │  │                 │
  │             │  │  conflict    │  │              │  │                 │
  │             │  │- socratic-   │  │              │  │                 │
  │             │  │  knowledge   │  │              │  │                 │
  │             │  │- socratic-   │  │              │  │                 │
  │             │  │  workflow    │  │              │  │                 │
  └─────────────┘  └──────────────┘  └──────────────┘  └─────────────────┘
        │                  │                  │                     │
        └──────────────────┼──────────────────┴─────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
  │socrates-cli │  │socrates-core-│  │  Socratic    │
  │(CLI Tool)   │  │api           │  │  System      │
  │             │  │(REST API)    │  │(Main App)    │
  └─────────────┘  └──────────────┘  └──────────────┘
```

## Package Layers

### 1. Core Foundation Layer (Required)

#### **socratic-core** (v0.1.1+)
- **Purpose**: Framework foundation providing configuration, events, exceptions, and utilities
- **Dependencies**: None (pure framework)
- **Exports**:
  - `SocratesConfig` - Application configuration
  - `EventEmitter`, `EventType` - Event-driven architecture (90+ event types)
  - `SocratesError` hierarchy - Structured exception handling
  - `LoggingConfig`, `PerformanceMonitor` - Observability
  - Utilities: ID generators, TTL cache, datetime helpers

#### **socratic-agents** (v0.1.0+)
- **Purpose**: Multi-agent orchestration with 19+ specialized agents
- **Key Agents**:
  - `ProjectManager` - Project coordination
  - `CodeGenerator` - Code generation
  - `SocraticCounselor` - Socratic guidance
  - `CodeAnalyzer` - Code analysis
  - `SkillGeneratorAgent` - Skill creation
  - And 14+ more specialized agents
- **Dependencies**: socratic-core, anthropic
- **Exports**: `AgentOrchestrator`, individual agent classes

#### **socratic-security** (v0.1.0+) [NEW]
- **Purpose**: Comprehensive security utilities across the ecosystem
- **Features**:
  - Prompt injection detection and sanitization
  - Input validation (XSS, SQL injection prevention)
  - Path traversal protection
  - Code execution sandboxing
  - Account lockout management
  - Multi-Factor Authentication (TOTP)
  - Token fingerprinting
  - Database encryption
  - Comprehensive audit logging
  - Password breach detection (HaveIBeenPwned integration)
- **Dependencies**: cryptography, requests, qrcode, bleach, pyotp, regex
- **Modules**:
  - `auth`: Lockout, MFA, breach checker
  - `input_validation`: XSS, SQL injection, path validation
  - `database`: Field-level encryption
  - `audit`: Event logging
  - `sandbox`: Code execution sandboxing
  - `filesystem`: Path validation
  - `prompt_injection`: Malicious prompt detection

### 2. Feature Libraries Layer (Optional, but Recommended)

These libraries extend the core functionality with specialized capabilities:

#### **socratic-rag** (v0.1.0+)
- **Purpose**: Retrieval-Augmented Generation for knowledge management
- **Providers**: ChromaDB, Qdrant, FAISS, Pinecone
- **Dependencies**: chromadb, sentence-transformers, socratic-core

#### **socratic-learning** (v0.1.1+)
- **Purpose**: Interaction tracking, pattern detection, and recommendations
- **Features**: Learning metrics, interaction logging, maturity calculations
- **Dependencies**: socratic-core

#### **socratic-analyzer** (v0.1.0+)
- **Purpose**: Production-grade code analysis with LLM-powered insights
- **Dependencies**: socratic-core, anthropic, socrates-nexus

#### **socratic-conflict** (v0.1.0+)
- **Purpose**: Multi-agent workflow conflict detection and resolution
- **Dependencies**: socratic-core, socratic-agents

#### **socratic-knowledge** (v0.1.0+)
- **Purpose**: Multi-tenant knowledge management with RBAC and versioning
- **Dependencies**: socratic-core, sqlalchemy

#### **socratic-workflow** (v0.1.1+)
- **Purpose**: Workflow orchestration with cost tracking and analytics
- **Dependencies**: socratic-core, socratic-agents (v0.1.3+)

### 3. LLM Abstraction Layer (Optional)

#### **socrates-nexus** (v0.1.0+)
- **Purpose**: Universal LLM client supporting multiple providers
- **Supported Providers**: Claude, GPT-4, Gemini, Ollama
- **Key Classes**: `LLMClient`, `AsyncLLMClient`, `LLMConfig`
- **Dependencies**: Provider-specific APIs
- **Note**: Optional for most use cases (socrates-ai provides Claude integration directly)

### 4. Framework Integration Layer (Optional)

These packages integrate Socrates components with external AI frameworks:

#### **socrates-ai-langraph** (v0.1.0+)
- **Purpose**: Multi-agent orchestration using LangGraph
- **Type**: Framework integration
- **Key Components**:
  - `StateGraph` based workflows with conditional routing
  - `CodeAnalysisAgent`, `CodeGenerationAgent`, `KnowledgeRetrievalAgent`
  - Event-driven state management
- **Dependencies**:
  - Required: socratic-core, langgraph
  - Optional: socratic-agents, socratic-rag
- **GitHub**: https://github.com/Nireus79/Socrates-ai-langraph
- **PyPI**: `socrates-ai-langraph`

#### **socrates-ai-openclaw** (v0.1.0+)
- **Purpose**: Socratic discovery skill implementation with OpenClaw framework
- **Type**: Framework skill
- **Key Features**:
  - Session-based discovery with adaptive questioning
  - ChromaDB vector store integration
  - Session persistence and resumption
  - Specification generation from sessions
- **Dependencies**:
  - Required: socratic-core, anthropic, chromadb
  - Optional: socratic-agents, socratic-rag
- **GitHub**: https://github.com/Nireus79/Socrates-ai-openclaw
- **PyPI**: `socrates-ai-openclaw`

### 5. Interface Layer (Optional)

#### **socrates-cli** (v0.1.0+)
- **Purpose**: Command-line interface for Socrates platform
- **Type**: Standalone CLI tool
- **Architecture**: API-first (communicates with socrates-core-api)
- **Commands**: project create/list, code generate, init, info
- **Dependencies**: socratic-core, click, colorama, httpx
- **GitHub**: Part of main Socrates repo

#### **socrates-core-api** (v0.1.0+)
- **Purpose**: REST API server exposing Socrates functionality
- **Type**: Web service
- **Architecture**: FastAPI-based with 25+ endpoints
- **Features**:
  - JWT-based authentication
  - MFA support (phase 2.2)
  - Rate limiting, metrics, security headers
  - Activity tracking, audit logging
- **Dependencies**: socratic-core, socrates-ai, fastapi, uvicorn, sqlalchemy, redis
- **GitHub**: Part of main Socrates repo

### 6. Application Layer

#### **Socratic System (socratic_system)**
- **Purpose**: Main orchestrator and example application
- **Type**: Full-featured platform combining all libraries
- **Components**:
  - Orchestration engine
  - Database management
  - Project coordination
  - Agent management
  - Event system
  - Configuration center
- **Location**: `socratic_system` module in socrates-ai package
- **Role**: Example of how to integrate all components

## Dependency Hierarchy

```
socrates-ai (Main Wrapper)
    ↓
┌─────────────────────────────────────────┐
│  CORE LAYER (Required)                  │
│  - socratic-core                        │
│  - socratic-agents                      │
│  - socratic-security                    │
│  - Direct anthropic integration         │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│  FEATURE LAYER (Optional)               │
│  - socratic-rag                         │
│  - socratic-learning                    │
│  - socratic-analyzer                    │
│  - socratic-conflict                    │
│  - socratic-knowledge                   │
│  - socratic-workflow                    │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│  LLM ABSTRACTION (Optional)             │
│  - socrates-nexus                       │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│  FRAMEWORK INTEGRATIONS (Optional)      │
│  - socrates-ai-langraph                 │
│  - socrates-ai-openclaw                 │
└────────────┬────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────┐
│  INTERFACES (Optional)                  │
│  - socrates-cli                         │
│  - socrates-core-api                    │
└─────────────────────────────────────────┘
```

## Installation Patterns

### Minimal Installation
```bash
pip install socrates-ai
# Includes: socratic-core, socratic-agents, socratic-security
# Provides: Basic orchestration with Claude AI
```

### With RAG Support
```bash
pip install socrates-ai[rag]
# Adds: socratic-rag (vector database and knowledge retrieval)
```

### Full Installation
```bash
pip install socrates-ai[full]
# Adds all feature libraries: rag, learning, analyzer, conflict, knowledge, workflow
# Plus: socrates-nexus, socrates-cli, socrates-core-api
```

### Framework-Specific
```bash
pip install socrates-ai-langraph
pip install socrates-ai-openclaw
```

## Data Flow Examples

### Project Creation Flow
```
CLI/API Request
    ↓
socrates-ai (socratic_system.Orchestrator)
    ↓
socratic-agents (ProjectManager agent)
    ↓
socratic-security (validation, audit logging)
    ↓
socrates-nexus / anthropic (LLM call to Claude)
    ↓
Response with generated project structure
```

### Code Generation with Analysis Flow
```
User Request (CLI/API)
    ↓
socrates-ai (Orchestrator)
    ↓
socratic-agents (CodeGenerator agent)
    ↓
socratic-security (prompt injection detection, sandboxing)
    ↓
socrates-nexus / anthropic (Claude generates code)
    ↓
socratic-analyzer (Optional: Code analysis)
    ↓
socratic-rag (Optional: Knowledge retrieval context)
    ↓
Response with code, analysis, and context
```

### Knowledge Management Flow
```
Document Upload
    ↓
socratic-knowledge (Store metadata)
    ↓
socratic-rag (Generate embeddings via sentence-transformers)
    ↓
socratic-rag (Store in ChromaDB)
    ↓
Future queries retrieve context from RAG
```

## Key Design Principles

1. **Modularity**: Each library is independently usable
   - Core libraries (`socratic-core`, `socratic-agents`) are always included
   - Feature libraries are optional and can be mixed-and-matched
   - Framework integrations are completely optional

2. **Composition**: Libraries combine additively for extended features
   - Install only what you need
   - No breaking changes when adding optional features

3. **Unidirectional Dependencies**: No circular dependencies
   - Core layer has no dependencies on feature or integration layers
   - Feature layers depend only on core and each other
   - Interfaces depend on core and optionally on features

4. **Framework Agnostic**: Core functionality works with any LLM provider
   - Default to Claude via `anthropic` library
   - Optional `socrates-nexus` for multi-provider support
   - Framework integrations (LangGraph, OpenClaw) are completely optional

5. **Security First**:
   - `socratic-security` integrated into core for all validation
   - Prompt injection protection on all LLM calls
   - Comprehensive audit logging throughout

6. **Extensibility**: Plugin architecture for custom agents and services

7. **Observability**: Comprehensive logging, metrics, and event system

## Configuration Management

### Environment Variables (Highest Priority)
```bash
ANTHROPIC_API_KEY=sk-...           # Claude API key
SOCRATES_DATA_DIR=/path/to/data    # Data storage location
CLAUDE_MODEL=claude-3-5-sonnet     # LLM model selection
DATABASE_URL=postgresql://...      # Database connection
REDIS_URL=redis://...              # Cache connection
```

### SocratesConfig
- Created from environment variables
- Used by orchestrator and all services
- Centralized configuration management

### Service-Specific Configuration
- RAGConfig, AnalyzerConfig, etc.
- Override defaults via environment or code
- Plugin configuration support

## Deployment Models

### Single-Process (Development)
```
Local Machine:
  - socrates-ai (orchestrator)
  - SQLite database
  - In-memory cache
  - Localhost API
```

### Distributed (Production)
```
API Server:              CLI Clients:
  - socrates-core-api      - socrates-cli
  - PostgreSQL database    - HTTP to API
  - Redis cache
  - socratic_system

External:
  - Vector DB (ChromaDB/Qdrant)
  - GitHub integration
```

### Kubernetes (Enterprise)
```
- Helm charts provided
- Docker multi-platform images
- ConfigMap for configuration
- Secrets for credentials
- StatefulSet for persistence
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.8+ (3.11+ recommended) |
| **Web Framework** | FastAPI, Uvicorn |
| **CLI Framework** | Click |
| **Database** | SQLite (dev), PostgreSQL (prod) |
| **Vector DB** | ChromaDB, Qdrant, FAISS, Pinecone |
| **LLM Provider** | Anthropic Claude (primary), OpenAI GPT-4, Google Gemini |
| **Caching** | Redis |
| **ORM** | SQLAlchemy |
| **Validation** | Pydantic |
| **Async** | asyncio, httpx |
| **Auth** | JWT, bcrypt, passlib |
| **Monitoring** | Prometheus, Grafana |
| **CI/CD** | GitHub Actions |
| **Container** | Docker, Kubernetes |

## Security Architecture

The ecosystem includes comprehensive security across all layers:

### Authentication & Authorization
- JWT-based token authentication
- Multi-Factor Authentication (TOTP)
- Account lockout after failed attempts
- Token fingerprinting (IP + User-Agent)
- Password breach detection (HaveIBeenPwned)
- Role-based access control (RBAC)

### Input Validation
- Comprehensive input sanitization (XSS, SQL injection)
- Path traversal protection
- Filename validation
- URL validation
- Email validation
- Username format validation

### Data Protection
- Field-level encryption (Fernet)
- Password hashing (bcrypt)
- CSRF protection
- Secure headers

### Code Safety
- Prompt injection detection
- Code execution sandboxing
- Static code analysis before execution

### Auditing & Compliance
- Comprehensive audit logging
- Event tracking for all operations
- Performance monitoring
- Metrics collection

## Development Workflow

### Working with Core Libraries
```bash
# Install with development dependencies
pip install -e socratic-core[dev]
pip install -e socratic-agents[dev]

# Run tests
pytest tests/

# Code quality
ruff check .
black --check .
mypy .
```

### Adding a New Feature Library
1. Create new library following the pattern
2. Depend on `socratic-core` (required)
3. Optionally depend on other feature libraries
4. Add to `socrates-ai` optional dependencies
5. Update this documentation

### Creating a Framework Integration
1. Create new repo: `socrates-ai-<framework>`
2. Depend on `socratic-core` + `socratic-agents`
3. Implement framework-specific adapters
4. Publish to PyPI with `socrates-ai-` prefix
5. Update integration documentation

## Future Roadmap

### Completed (Phase 1-6)
✅ Core framework (socratic-core)
✅ Multi-agent orchestration (socratic-agents)
✅ Comprehensive security (socratic-security)
✅ Feature libraries (RAG, learning, analyzer, etc.)
✅ LLM abstraction (socrates-nexus)
✅ Framework integrations (LangGraph, OpenClaw)
✅ Interface layers (CLI, API)

### In Progress
⏳ Kubernetes deployment templates
⏳ Advanced caching strategies
⏳ Distributed tracing integration
⏳ Plugin marketplace

### Future
⏳ GraphQL API alternative
⏳ Real-time collaboration WebSocket improvements
⏳ Mobile app integration
⏳ Voice interface support

## Community & Support

- **Repository**: https://github.com/Nireus79/Socrates
- **Issues**: https://github.com/Nireus79/Socrates/issues
- **Documentation**: https://github.com/Nireus79/Socrates/tree/main/docs
- **PyPI**: https://pypi.org/project/socrates-ai/

## License

All Socrates ecosystem packages are released under the MIT License.

---

**Last Updated**: March 2026
**Ecosystem Version**: v1.3.4 (socrates-ai)
**Status**: Production Ready
