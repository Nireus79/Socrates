# Socrates AI System Design & Architecture

## Table of Contents
1. [Design Goals](#design-goals)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Scalability Strategy](#scalability-strategy)
5. [Failure Handling](#failure-handling)
6. [Deployment Models](#deployment-models)
7. [Security Architecture](#security-architecture)
8. [Future Extensions](#future-extensions)

---

## Design Goals

### Primary Objectives
1. **Pedagogical Excellence**: Deliver Socratic tutoring at scale using AI
2. **Autonomy & Extensibility**: 14+ specialized agents, easily extensible
3. **Constitutional Governance**: All agent actions validated against constitutional principles
4. **Production Maturity**: Enterprise-grade reliability, monitoring, security
5. **User Control**: Support both platform-hosted and self-hosted deployments

### Architectural Principles
- **Separation of Concerns**: Each agent owns a specific domain
- **Event-Driven Coupling**: Agents communicate via events, not direct calls
- **Fail-Safe Design**: Circuit breakers, retries, graceful degradation
- **Data Durability**: Multiple storage backends (SQLite + ChromaDB)
- **Observable Systems**: Comprehensive metrics, health checks, audit logs

---

## System Architecture

### High-Level Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                          │
│  ┌──────────────────┬──────────────────┬──────────────────┐ │
│  │   Web UI         │   REST API       │    CLI           │ │
│  │ (React/Vite)     │   (FastAPI)      │   (Click)        │ │
│  └──────────────────┴──────────────────┴──────────────────┘ │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│               AgentOrchestrator (Hub)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Route requests to agents via AgentBus               │ │
│  │ • Manage databases (SQLite + ChromaDB)                │ │
│  │ • Load/initialize configuration                       │ │
│  │ • Emit system events                                  │ │
│  │ • Enforce constitutional governance                   │ │
│  │ • Track audit logs                                    │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                             │
┌───────▼─────────┐                    ┌─────────────▼──────┐
│   AgentBus      │                    │  EventEmitter      │
│ ┌─────────────┐ │                    │ ┌────────────────┐ │
│ │Circuit Break│ │                    │ │ Pub/Sub (27+  │ │
│ │Retry Logic  │ │                    │ │ event types)  │ │
│ │Governance   │ │                    │ │ Listeners     │ │
│ │Capability   │ │                    │ │ Thread-safe   │ │
│ │Checking     │ │                    │ └────────────────┘ │
│ └─────────────┘ │                    └────────────────────┘
└─────────────────┘
        │
┌───────┴─────────────────────────────────────────────┐
│                                                     │
│         14+ Specialized Agents                     │
│  ┌────────────────────────────────────────────────┐ │
│  │ • ProjectManager        • SocraticCounselor    │ │
│  │ • CodeGenerator         • ContextAnalyzer      │ │
│  │ • ConflictDetector      • SystemMonitor        │ │
│  │ • DocumentProcessor     • UserManager          │ │
│  │ • NoteManager           • KnowledgeManager     │ │
│  │ • CodeValidator         • MultiLLM             │ │
│  │ • QuestionQueue         • UserLearning         │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
        │
┌───────┴──────────────────────────────────────────┐
│                                                  │
│         Data Layer (Multi-Backend)              │
│  ┌────────────────┬──────────────┬────────────┐ │
│  │  SQLite        │  ChromaDB    │  Redis     │ │
│  │ (Relational)   │  (Vectors)   │  (Cache)   │ │
│  │                │              │            │ │
│  │ • Projects     │ • Embeddings │ • Sessions │ │
│  │ • Users        │ • Knowledge  │ • Rate     │ │
│  │ • Chats        │ • RAG Search │  limit     │ │
│  │ • Notes        │              │ • Presence │ │
│  │ • Audit logs   │              │            │ │
│  └────────────────┴──────────────┴────────────┘ │
└──────────────────────────────────────────────────┘
        │
        └─── Anthropic Claude API ───────┐
                                         │
                        ┌────────────────▼────────────┐
                        │    LLM Services            │
                        │ • Generation               │
                        │ • Embeddings (outsourced)  │
                        │ • Token tracking           │
                        └────────────────────────────┘
```

---

## Core Components

### 1. AgentOrchestrator
**Responsibility**: Central coordination hub
- Initializes all agents (14+ specialized instances)
- Manages orchestration lifecycle
- Maintains database connections (SQLite + ChromaDB)
- Loads configuration (SocratesConfig)
- Emits events to system
- Enforces constitutional governance
- Tracks audit logs

**Design Trade-offs**:
- ✅ Single source of truth for system state
- ✅ Easy to test (can mock orchestrator)
- ⚠️ Potential bottleneck (mitigated by event-driven design)
- ⚠️ Requires careful initialization order

### 2. AgentBus
**Responsibility**: Message routing with resilience
```
Request Flow:
1. Validate governance (constitutional check)
2. Check circuit breaker status
3. Route to agent handler
4. Track metrics (success/failure/timeout)
5. Return response (or error)
```

**Resilience Patterns**:
- **Circuit Breaker**: Opens after 5 failures, recovers after 60s
- **Retry Policy**: 3 retries, exponential backoff (0.1s → 5s)
- **Timeouts**: 30s default (configurable)
- **Metrics**: Track request counts, success rates, latency

**Design Trade-offs**:
- ✅ Prevents cascading failures
- ✅ Transparent request routing
- ⚠️ Circuit breaker state per agent (not global)
- ✅ Minimal latency overhead

### 3. Agents (14+ Specialized)
**Design**: Single Responsibility Principle
- Each agent owns one domain (projects, questions, code, etc.)
- Autonomous decision-making within constitutional constraints
- Stateless processing (state stored in databases)
- Event emission for system-wide notifications

**Key Agents**:
| Agent | Role | Key Methods |
|-------|------|------------|
| ProjectManager | Project lifecycle | create, load, save, archive, restore, delete |
| SocraticCounselor | Dialogue & tutoring | generate_question, process_response, advance_phase |
| CodeGenerator | Code production | generate_script, generate_documentation |
| ConflictDetector | Spec validation | detect conflicts (pluggable checkers) |
| KnowledgeManager | Knowledge curation | add, get, search knowledge entries |
| SystemMonitor | Health tracking | track tokens, check health, get stats |
| CodeValidator | Quality assurance | validate code, check correctness |

**Agent Registration**:
```python
# Auto-register during orchestrator init
agent = SpecializedAgent(orchestrator)
agent_bus.register(agent.name, agent.process)
```

### 4. EventEmitter
**Responsibility**: Loose coupling via pub/sub
- Thread-safe event dispatch
- 27+ event types (project, dialogue, code, knowledge, system)
- Synchronous emission (no async overhead for fast paths)
- Listener management (subscribe/unsubscribe)

**Design Trade-offs**:
- ✅ Components evolve independently
- ✅ Background processing via event listeners
- ⚠️ Event ordering not guaranteed across components
- ✅ Easy to test (can spy on events)

### 5. Multi-Database Strategy

#### SQLite (Relational Data)
**When to use**: Development, single-node, < 1M records
```sql
projects          -- Core project data
users             -- User accounts & auth
chat_sessions     -- Conversation containers
chat_messages     -- Actual dialogue
project_notes     -- Annotations
llm_usage         -- Token tracking
```

**Features**:
- WAL Mode: Better concurrent access
- Foreign Keys: Enforced integrity
- Query Profiler: Slow query detection
- Connection pooling: Concurrent access

#### ChromaDB (Vector Data)
**When to use**: Semantic search, RAG, knowledge base
```python
collection: "socratic_knowledge"
├─ Document: Knowledge entry text
├─ Embedding: 384-dim vector (all-MiniLM-L6-v2)
├─ Metadata: Category, difficulty, tags, project scope
└─ Search: O(log N) with HNSW index
```

**Features**:
- Persistent storage (local SQLite + embeddings)
- Lazy-loaded embedding model (1-3s savings on startup)
- EmbeddingCache (10k entries)
- SearchResultCache (300s TTL)

#### Redis (Optional Cache)
**When to use**: Distributed systems, high throughput
- Session caching
- Project metadata
- Search results
- Rate limit counters
- Presence tracking

**Fallback**: InMemoryCache if Redis unavailable

### 6. Configuration System (SocratesConfig)

**Design**: Multiple initialization paths
```python
# Path 1: From environment
config = SocratesConfig.from_env()

# Path 2: From dictionary
config = SocratesConfig.from_dict({...})

# Path 3: Builder pattern (fluent API)
config = ConfigBuilder(api_key) \
    .with_data_dir(Path(...)) \
    .with_model("claude-opus-4-5") \
    .build()
```

**Key Parameters**:
- API Key: Claude access (optional for server mode)
- Model: LLM to use
- Data Dir: Storage paths
- Encryption Key: Auto-generated if not provided
- Log Level: DEBUG/INFO/WARNING/ERROR
- Max Context: Token budget

**Design Trade-offs**:
- ✅ Flexible initialization
- ✅ Clear defaults
- ✅ Type-safe (dataclass)
- ⚠️ Post-init validation required

---

## Scalability Strategy

### Single-Node (Development)
```
FastAPI ↔ SQLite + ChromaDB ↔ Anthropic API
```
- All-in-one deployment
- Suitable for < 1000 active users
- No infrastructure overhead

### Multi-Node (Production)

#### Horizontal Scaling
```
Load Balancer
    ├─ API Instance 1
    ├─ API Instance 2
    └─ API Instance N

↓ (Shared)

PostgreSQL (managed, replicated)
Pinecone/Weaviate (vector search as service)
Redis Cluster (distributed cache)
```

#### Key Changes:
1. **Replace SQLite** → PostgreSQL
   - Alembic migrations
   - Connection pooling
   - Read replicas for scaling

2. **Replace ChromaDB** → Pinecone/Weaviate
   - Managed vector database
   - Built-in replication
   - Serverless scaling

3. **Add Redis Cluster**
   - Session replication
   - Distributed cache
   - Rate limit counters across nodes

#### Performance Scaling (Per Node)
- **API Instances**: Scale up to N instances
- **Connection Pool**: 5-20 connections per instance
- **Memory**: 2-4GB per instance (embedding model cached)
- **CPU**: 2-4 cores per instance

#### Load Testing Results
- **Single Node**: 100 req/s (concurrent)
- **Multi-Node (3x)**: 300+ req/s (linear scaling)
- **Bottleneck**: Claude API rate limits (not infra)

---

## Failure Handling

### Agent Failures

**Scenario 1: Agent Times Out (> 30s)**
```
Request → AgentBus → Agent (no response after 30s)
  ↓
Timeout triggered
  ↓
Return error to client
  ↓
Log for monitoring
  ↓
Circuit breaker increments failure count
```

**Scenario 2: Agent Crashes**
```
Request → AgentBus → Agent.process() raises Exception
  ↓
Exception caught in AgentBus
  ↓
Circuit breaker state: OPEN (after 5 failures)
  ↓
Subsequent requests rejected immediately
  ↓
After 60s: Try HALF_OPEN state
  ↓
If succeeds: Return to CLOSED
```

### Database Failures

**SQLite Unavailable**:
```
Database.load_project() → Connection error
  ↓
Logged with severity ERROR
  ↓
Return 503 Service Unavailable to client
  ↓
Auto-reconnection on next request
```

**ChromaDB Unavailable**:
```
KnowledgeManager searches but vector_db fails
  ↓
Fallback: Use keyword search in SQLite
  ↓
Degrade gracefully (no semantic search)
  ↓
Continue processing
```

### API Failures

**Rate Limit Hit**:
```
Request exceeds limit
  ↓
Return 429 Too Many Requests
  ↓
Include Retry-After header
  ↓
Client exponential backoff
```

**Claude API Fails**:
```
ClaudeClient.call() → 5xx error
  ↓
AgentBus retries (3 attempts, exp backoff)
  ↓
If persists: Return error response
  ↓
Metrics tracked (failure rate monitoring)
```

### Graceful Shutdown

**Orderly Shutdown Flow**:
```
1. Stop accepting new requests
2. Wait for in-flight requests (5-min timeout)
3. Cancel background tasks
4. Close database connections
5. Close vector database
6. Exit (0 = success, 1 = timeout)
```

---

## Deployment Models

### Model 1: Docker Compose (Development)
```yaml
services:
  api:
    build: Dockerfile.api
    ports: 8000:8000
    volumes: ./data:/app/data

  redis:
    image: redis:7-alpine
    ports: 6379:6379

  web:
    build: Dockerfile.reverse-proxy
    ports: 80:80
```

**Suitable for**: Dev teams, small deployments, self-hosted

### Model 2: Docker Hub (Pre-built Images)
```bash
docker run -e ANTHROPIC_API_KEY=... nireus79/socrates-api:latest
```

**Suitable for**: Quick deployments, consistent environments

### Model 3: Kubernetes (Production)
```yaml
Deployment:
  replicas: 3
  image: nireus79/socrates-api:latest
  env: ANTHROPIC_API_KEY, REDIS_URL, DATABASE_URL

Service:
  type: LoadBalancer
  port: 8000

ConfigMap:
  logging, rate limits, cache TTLs

Secrets:
  ANTHROPIC_API_KEY, database password, JWT secret
```

**Suitable for**: Enterprise, high availability, auto-scaling

---

## Security Architecture

### Authentication Flow
```
User → POST /auth/login (username, password)
  ↓
PasswordManager.verify(user.password_hash)
  ↓
Create JWT tokens:
  - access_token (15 min)
  - refresh_token (7 days)
  ↓
Return tokens to client
  ↓
Client stores tokens
  ↓
Subsequent requests include Authorization: Bearer {access_token}
```

### Encryption Strategy
```
Sensitive Data → Fernet (AES-128)
  ↓
Encrypted before storage
  ↓
Key managed by SOCRATES_ENCRYPTION_KEY
  ↓
Auto-generated if not provided
```

### Authorization (Zero-Trust)
```
Request → Extract JWT
  ↓
Validate signature & expiry
  ↓
Extract user_id from claims
  ↓
Check RBAC (role-based access control)
  ↓
Validate resource ownership
  ↓
Proceed or deny (401/403)
```

### Security Headers
```
Production:
  X-Frame-Options: DENY (prevent clickjacking)
  X-Content-Type-Options: nosniff (MIME sniffing)
  Strict-Transport-Security: 1 year (HTTPS only)
  Content-Security-Policy: restrictive (XSS prevention)

Development:
  Same but relaxed for testing
```

---

## Future Extensions

### 1. Real-time Collaboration
- WebSocket support (instead of polling)
- Operational transformation for concurrent editing
- Presence tracking (who's online)
- Live comments and annotations

### 2. Multi-LLM Support
- Anthropic Claude (current)
- OpenAI GPT-4 (fallback)
- Local models (Llama, Mistral)
- Cost optimization via model selection

### 3. Advanced Analytics
- Learning curve tracking per student
- Effectiveness metrics per question type
- Engagement funnels
- Cohort analysis

### 4. Custom Knowledge Integration
- Upload documents (PDF, DOCX, code repos)
- Git repository integration
- LMS integrations (Canvas, Blackboard)
- Slack/Teams notifications

### 5. Plugin Architecture
- Custom agents (user-defined domains)
- Custom conflict checkers
- Custom event listeners
- API v2 with plugin registration

### 6. Distributed Agents
- Run agents in separate services
- Cross-machine communication
- Scalable agent orchestration
- Resource allocation

### 7. Advanced Observability
- Distributed tracing (OpenTelemetry)
- Custom metrics dashboard
- Log aggregation (ELK, Datadog)
- Cost tracking per feature

---

## Summary

Socrates is built on a **modular, event-driven, production-ready architecture**:

1. **Modular**: 14+ agents, each with clear responsibilities
2. **Event-Driven**: Loose coupling via pub/sub, background processing
3. **Resilient**: Circuit breakers, retries, graceful degradation
4. **Observable**: Comprehensive metrics, health checks, audit logs
5. **Secure**: Encryption, JWT auth, zero-trust authorization
6. **Scalable**: Single-node to multi-node horizontal scaling
7. **Production-Ready**: Enterprise-grade error handling, logging, monitoring

The architecture supports both self-hosted deployments (Docker Compose) and enterprise deployments (Kubernetes + managed services) with minimal code changes.
