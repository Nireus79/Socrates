# Socratic RAG Enhanced - System Architecture

**Version:** 7.4.0
**Last Updated:** October 2024
**Status:** Production Ready

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Layers](#architecture-layers)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Patterns](#design-patterns)
7. [Scalability Considerations](#scalability-considerations)

---

## System Overview

Socratic RAG Enhanced is an AI-powered educational platform that combines:
- **Socratic Questioning**: AI-guided questioning methodology for collaborative learning
- **RAG (Retrieval-Augmented Generation)**: Vector-based knowledge base for context-aware responses
- **Code Generation**: Automated code creation using Claude AI
- **Multi-Agent Orchestration**: Specialized agents for different domains

### Key Characteristics
- **Multi-user support** with role-based access control
- **Real-time updates** using polling and WebSocket-ready architecture
- **Modular design** with loose coupling and high cohesion
- **Error resilience** with fallback mechanisms
- **Production-ready** with comprehensive logging and monitoring

---

## Architecture Layers

### 1. Presentation Layer (Web UI)
**Location:** `web/`

- **Flask Web Framework**: Primary HTTP server
- **Jinja2 Templates**: Server-side template rendering
- **Bootstrap 5**: Responsive UI components
- **JavaScript**: Client-side interactivity

**Key Features:**
- Responsive design for all screen sizes
- Real-time progress tracking with AJAX polling
- Dark mode support
- Accessibility compliance (WCAG 2.1)

### 2. Application Layer
**Location:** `src/`

#### Request Handler (Flask Routes)
- Authentication & authorization checks
- Input validation and sanitization
- Business logic orchestration
- Response formatting

#### Agent System
- 9 specialized agents for different tasks
- Agent Orchestrator for routing
- Base Agent class for common functionality
- Service Container for dependency injection

### 3. Business Logic Layer
**Location:** `src/agents/` & `src/services/`

#### Agents (Core Processing Units)
1. **UserManagerAgent** - User authentication, profile management
2. **ProjectManagerAgent** - Project lifecycle management
3. **SocraticCounselorAgent** - Socratic questioning generation
4. **CodeGeneratorAgent** - Code generation with Claude AI
5. **ContextAnalyzerAgent** - Context analysis and conflict detection
6. **DocumentProcessorAgent** - PDF/DOCX/text processing
7. **ServicesAgent** - Git, IDE, export operations
8. **SystemMonitorAgent** - Health monitoring and analytics
9. **ArchitectureOptimizerAgent** - Architecture analysis and optimization (C6)

#### Services (External Integrations)
- **ClaudeService**: Anthropic Claude API integration
- **GitService**: Git operations and cloning
- **IDEService**: VSCode, PyCharm integration
- **VectorService**: ChromaDB vector database
- **DocumentService**: Document chunking and processing
- **DynamicProviderSelector**: Multi-LLM provider routing

### 4. Data Layer
**Location:** `src/database/`

#### Database Structure
- **SQLite** for persistence
- **Repository Pattern** for data access
- **Connection pooling** for performance
- **Transaction management** for data integrity

#### Core Models
- Users & Organizations
- Projects & Modules
- Sessions & Conversations
- Tasks & Specifications
- Generated Code & Files
- Repositories & Imports

### 5. Infrastructure Layer
**Location:** `src/core.py` & `config.yaml`

#### Service Container
```
ServiceContainer
├── SystemConfig (config.yaml + env vars)
├── SystemLogger (file rotation, levels)
├── EventSystem (pub/sub for async communication)
├── DatabaseManager (connection pooling)
└── Service Registry (all initialized services)
```

---

## Core Components

### Service Container Pattern
**Purpose:** Central dependency management

```python
# Initialize system
services = ServiceFactory.create_services('config.yaml')

# Access services
services.database_manager      # SQLite connection pool
services.event_system          # Event bus
services.logger               # Centralized logging
services.config               # Configuration
```

**Benefits:**
- Single source of truth for configuration
- Easy mocking for testing
- Graceful degradation when services fail
- Clear initialization order

### Agent Orchestrator
**Purpose:** Route requests to appropriate agents

```python
orchestrator = AgentOrchestrator(services)

# Direct routing by agent ID
result = orchestrator.route_request(
    agent_id='code_generator',
    action='generate_codebase',
    data={...}
)

# Capability-based routing
result = orchestrator.route_by_capability(
    capability='generate_questions',
    data={...}
)
```

**Features:**
- Health monitoring of agents
- Automatic fallback for failed agents
- Statistics collection
- Request validation

### Vector Database (ChromaDB)
**Purpose:** Semantic search for RAG context

```python
vector_service = VectorService()

# Add documents
vector_service.add_document(
    doc_id='repo_123_file_1_0',
    content='Python code snippet...',
    metadata={'language': 'python', 'file': 'app.py'},
    collection_name='repo_123'
)

# Search similar
results = vector_service.search(
    query='How to handle database connections?',
    collection_name='repo_123',
    k=5  # Top 5 results
)
```

### Dynamic Provider Selection
**Purpose:** Optimize LLM provider based on task complexity

```python
selector = DynamicProviderSelector()

# Analyze task complexity
analysis = selector.analyze_task({
    'task_type': 'code_generation',
    'requirements': 'Complex REST API',
    'context_size': 5000
})
# Result: COMPLEX (0.75 score) → Recommends Claude Opus

# Get optimal provider
provider = selector.select_provider(task_data)
```

**Complexity Factors:**
- Reasoning depth (0-0.3)
- Code complexity (0-0.25)
- Context requirement (0-0.2)
- Latency sensitivity (0-0.15)
- Domain specificity (0-0.1)

---

## Data Flow

### 1. User Interaction Flow
```
Browser Request
    ↓
Flask Route Handler
    ↓
Authentication Check
    ↓
Input Validation
    ↓
Agent Orchestrator
    ↓
Appropriate Agent
    ↓
Database/External Service
    ↓
Response Formatting
    ↓
JSON/HTML Response
    ↓
Browser Renders
```

### 2. Code Generation Flow
```
User submits generation request
    ↓
new_generation() creates generation record (pending)
    ↓
CodeGeneratorAgent.generate_codebase()
    ↓
Prepare technical specifications
    ↓
Call Claude API via ClaudeService
    ↓
Claude generates code structure
    ↓
Extract files from response
    ↓
Store each file in database
    ↓
Update generation status → completed
    ↓
Frontend polls progress (every 2s)
    ↓
Display results to user
```

### 3. RAG Query Flow
```
User asks question about code
    ↓
Extract query intent
    ↓
VectorService.search() in relevant repository
    ↓
Retrieve top K similar code chunks
    ↓
Combine as context
    ↓
Add to Claude prompt
    ↓
Claude generates contextual answer
    ↓
Return with citations
```

### 4. Repository Import Flow
```
User provides repository URL
    ↓
GitService.clone_repository()
    ↓
RepositoryAnalyzer analyzes codebase
    ↓
Extract: languages, frameworks, dependencies
    ↓
DocumentService chunks code files
    ↓
VectorService creates embeddings
    ↓
Store vectors in ChromaDB
    ↓
Store metadata in database
    ↓
Generate analysis report
```

---

## Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Flask 2.0+ | Web server & routing |
| Database | SQLite 3 | Data persistence |
| Vector DB | ChromaDB | Semantic search |
| AI Provider | Anthropic Claude | Code generation & analysis |
| Alternative AI | OpenAI GPT-4, Google Gemini | Multi-provider support |
| Local AI | Ollama | Cost-effective fallback |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| HTML/CSS | Bootstrap 5 | Responsive UI |
| JavaScript | Vanilla JS | Client-side logic |
| Code Highlighting | Prism.js | Syntax highlighting |
| Markdown | Marked.js | Markdown rendering |
| Icons | Bootstrap Icons | UI icons |

### DevOps
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Container | Docker | Standardized deployment |
| Language | Python 3.8+ | Primary language |
| Testing | pytest | Unit & integration tests |
| Logging | Python logging | Structured logging |

---

## Design Patterns

### 1. Repository Pattern
**Purpose:** Abstract data access logic

```python
# Database operations abstracted
users_repo = db.users
user = users_repo.get_by_id(user_id)
user = users_repo.update(user_id, {'name': 'John'})
```

**Benefits:**
- Testable with mock repositories
- Easy to swap storage backend
- Consistent CRUD interface

### 2. Factory Pattern
**Purpose:** Create service instances

```python
# ServiceFactory creates entire container
services = ServiceFactory.create_services('config.yaml')

# LLM provider factory
provider = get_llm_provider('claude', auto_detect=True)
```

### 3. Strategy Pattern
**Purpose:** Select algorithms based on conditions

```python
# Dynamic provider selection
selector = DynamicProviderSelector()
complexity = analyzer.analyze(task)
provider = selector.select_provider(task)
```

### 4. Observer Pattern
**Purpose:** Event-driven architecture

```python
# Subscribe to events
services.event_system.subscribe('code_generated', on_code_generated)

# Emit events
services.event_system.emit('code_generated', 'code_agent', data)
```

### 5. Decorator Pattern
**Purpose:** Add authentication/authorization

```python
@require_authentication
def protected_action(self, data):
    user = data['_authenticated_user']
    # ...

@require_project_access
def project_action(self, data):
    project = data['_project']
    # ...
```

---

## Scalability Considerations

### Current Capacity
- **Users:** 100-1000 concurrent
- **Repositories:** 1000+ imported
- **Generated Code:** 10,000+ projects
- **Vector Store:** 1M+ embeddings

### Scaling Strategies

#### Horizontal Scaling
```
Frontend
├── Load Balancer
├── Flask Instance 1
├── Flask Instance 2
├── Flask Instance 3
└── Shared Resources
    ├── PostgreSQL (replaces SQLite)
    ├── Redis (caching layer)
    └── ChromaDB Cluster
```

#### Database Optimization
- **From SQLite to PostgreSQL** - ACID compliance, concurrency
- **Connection pooling** - Reuse connections
- **Query optimization** - Indexes, query analysis
- **Read replicas** - Separate read/write

#### Caching Strategy
- **Redis cache** for frequently accessed data
- **Browser caching** for static assets
- **API response caching** with TTL
- **Vector cache** for common queries

#### Asynchronous Processing
- **Celery + RabbitMQ** for long-running tasks
- **Background jobs** for code generation
- **Webhook updates** for real-time notifications
- **Job queuing** with retry logic

#### AI Provider Optimization
- **Batch API calls** to reduce latency
- **Model caching** for repeated requests
- **Cost optimization** with token counting
- **Fallback routing** via DynamicProviderSelector

### Performance Metrics to Monitor
- API response time (target: <500ms)
- Code generation time (target: <2min)
- Vector search latency (target: <500ms)
- Database query time (target: <100ms)
- Cache hit ratio (target: >80%)

---

## Security Architecture

### Authentication
- Session-based auth with secure cookies
- CSRF protection on all state-changing operations
- Password hashing with werkzeug

### Authorization
- Project-level access control
- Role-based access (owner, collaborator, viewer)
- Data isolation per user

### Data Protection
- HTTPS only in production
- Input sanitization on all forms
- SQL injection prevention via parameterized queries
- XSS protection via template escaping

### API Security
- Rate limiting (50 req/60sec default)
- API key validation
- Request signing for sensitive operations
- Audit logging of sensitive actions

---

## Summary

Socratic RAG Enhanced uses a layered architecture with:
- **Clear separation of concerns** across 5 layers
- **Service container** for dependency management
- **Agent-based orchestration** for business logic
- **Repository pattern** for data access
- **Vector database** for semantic search
- **Multi-agent support** for flexible AI integration
- **Production-ready** error handling and monitoring

This design enables:
✅ Easy maintenance and testing
✅ Horizontal scalability
✅ Feature extensibility
✅ Graceful degradation
✅ Multi-provider AI support

For more details, see:
- User Guide: `docs/USER_GUIDE.md`
- API Documentation: `docs/API_DOCUMENTATION.md`
- Deployment Guide: `docs/DEPLOYMENT.md`
