# Socrates System Architecture

**Comprehensive documentation of the Socrates AI system architecture**

## Executive Summary

Socrates is a multi-layered system for AI-guided collaborative project development. It combines:
- **Multi-agent orchestration** for specialized tasks
- **Knowledge management** with vector search (RAG)
- **REST API** for cross-platform access
- **Command-line interface** for developers
- **Persistent storage** for projects and learning

## System Layers

```
┌────────────────────────────────────────────────────────┐
│           Frontend (React SPA)                         │
│    - Project management UI                             │
│    - Chat interface                                    │
│    - Knowledge browser                                 │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│       FastAPI REST API (socrates-api)                  │
│  - Authentication & Authorization                     │
│  - Project CRUD operations                            │
│  - Chat session management                            │
│  - Knowledge base endpoints                           │
│  - WebSocket for real-time communication             │
│  - Agent orchestration gateway                        │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│    Business Logic & Orchestration Layer                │
│  - APIOrchestrator (coordinates agents)               │
│  - Database access (projects, users, sessions)        │
│  - Caching layer (Redis with fallback)                │
│  - Event system                                        │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│        Multi-Agent System (socratic-agents)            │
│                                                        │
│  Specialized Agents:                                  │
│  - CodeGenerator: Generates code with explanations    │
│  - CodeValidator: Validates code quality             │
│  - SocraticCounselor: Asks guiding questions          │
│  - ProjectManager: Manages project state              │
│  - LearningAgent: Tracks user learning patterns       │
│  - KnowledgeManager: Manages knowledge base           │
│  - DocumentProcessor: Indexes documents               │
│  - ContextAnalyzer: Understands project context       │
│  - ConflictDetector: Identifies design issues         │
│  - QualityController: Ensures code quality            │
│  - UserManager: Manages user interactions             │
│  - NoteManager: Manages project notes                 │
│  - SystemMonitor: Monitors system health              │
│  - SkillGeneratorAgent: Generates learning skills     │
│  - [And more specialized agents]                      │
│                                                        │
│  Orchestrators:                                       │
│  - SkillOrchestrator: Coordinates skill learning      │
│  - WorkflowOrchestrator: Manages workflows            │
│  - PureOrchestrator: Maturity-driven agent selection  │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│         AI & Knowledge Management Layer                │
│                                                        │
│  - Claude LLM (via Anthropic API)                    │
│  - ChromaDB (vector embeddings)                      │
│  - Semantic search                                    │
│  - RAG (Retrieval-Augmented Generation)              │
│  - Document indexing & versioning                     │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│        Data & Storage Layer                            │
│                                                        │
│  - SQLite (project metadata, users, sessions)        │
│  - Redis (caching, sessions)                         │
│  - ChromaDB (vector embeddings)                      │
│  - File system (documents, knowledge base)           │
└────────────────────────────────────────────────────────┘
```

## Core Concepts

### Projects

A **project** is the main organizing unit in Socrates. Each project:
- Has an owner (creator)
- Contains code, documentation, and knowledge
- Has a maturity level (tracks learning progress)
- Supports team collaboration
- Maintains learning history

**Project Lifecycle:**
1. **Creation** - Owner creates project
2. **Discovery** - Initial phase, team establishes requirements
3. **Development** - Main coding and implementation
4. **Refinement** - Quality improvement and optimization
5. **Completion** - Project finalized
6. **Archive** - Project stored for future reference

### Agents

**Agents** are specialized components that perform specific tasks:

- **CodeGenerator** - Writes code based on requirements
  - Takes: Requirements, context, code style
  - Returns: Generated code with explanations

- **SocraticCounselor** - Asks guiding questions
  - Takes: Project context, user questions
  - Returns: Thoughtful counter-questions

- **ConflictDetector** - Identifies design conflicts
  - Takes: Requirements, specifications
  - Returns: List of potential conflicts

- **LearningAgent** - Tracks learning progress
  - Takes: User interactions, skill exercises
  - Returns: Learning effectiveness scores

- **ProjectManager** - Manages project workflow
  - Takes: User actions, project state
  - Returns: Updated project state

**Agent Properties:**
- Independent: Can operate without other agents
- Specialized: Focused on specific domain
- Composable: Can be orchestrated together
- Testable: Can be unit tested
- Replaceable: Can be swapped with alternatives

### Knowledge Management

Knowledge in Socrates flows through:

1. **Document Upload** - User uploads files (code, docs, articles)
2. **Indexing** - Documents are indexed by ChromaDB
3. **Vector Embedding** - Text converted to vector embeddings
4. **Search** - User queries matched against embeddings
5. **RAG** - Retrieved documents augment LLM context
6. **Learning** - System learns from interactions

**Benefits:**
- Semantic search (finds concepts, not keywords)
- Context-aware responses
- Personalized learning
- Reduced hallucination from LLM

## ID Generation Strategy

### The Challenge

During the monorepo migration, the system lost its centralized ID generation utility. Code referenced `socratic_core.utils.ProjectIDGenerator` which no longer existed.

### The Solution

Created `backend/src/socrates_api/utils/id_generator.py` with:
- 11 entity types covered
- Consistent format: `{prefix}_{12-char-hex}`
- High entropy: UUID4-based (48+ bits per ID)
- Single source of truth for ID generation
- Backward compatible with monolithic pattern

### Benefits

1. **Consistency** - All IDs follow same format
2. **Debuggability** - Prefix indicates entity type in logs
3. **Flexibility** - Easy to change format globally
4. **Testability** - Can mock ID generation
5. **Future-proof** - Can switch to ULID, nanoid, etc. easily

### Usage Pattern

```python
from socrates_api.utils import IDGenerator

# Generate IDs for different entity types
project_id = IDGenerator.project()      # proj_abc123def456
user_id = IDGenerator.user()            # user_xyz789uiop12
session_id = IDGenerator.session()      # sess_ab12cd34
message_id = IDGenerator.message()      # msg_ef56gh78ij90
```

## Authentication & Authorization

### Authentication Flow

1. **User Registration**
   ```
   User → POST /auth/register → Create user in DB → Return tokens
   ```

2. **User Login**
   ```
   User → POST /auth/login → Verify credentials → Generate JWT → Return tokens
   ```

3. **Token Refresh**
   ```
   Client → POST /auth/refresh → Validate refresh token → Return new access token
   ```

4. **Protected Request**
   ```
   Client → GET /api/resource (with JWT) → Verify JWT → Return resource
   ```

### Authorization Model

Socrates uses **owner-based authorization** (no global admin role):

```
Project
├── Owner
│   └── Full control (edit, delete, invite, manage permissions)
├── Editors
│   └── Can edit and contribute
└── Viewers
    └── Can view only
```

**Benefits:**
- Decentralized (no bottleneck at admin)
- Scalable (easy to add collaborators)
- Clear ownership (always know who owns project)
- Flexible (easy to change roles)

## Request-Response Cycle

### Request Flow

```
1. Request arrives at API
   ├─ Middleware: Security headers, rate limiting
   ├─ Route matching: Find correct endpoint
   ├─ Authentication: Verify JWT token
   ├─ Validation: Pydantic model validation
   ├─ Authorization: Check project access
   └─ Handler: Execute business logic

2. Business Logic
   ├─ Database query/update
   ├─ Agent call (if needed)
   ├─ Cache update
   └─ Event emission

3. Response
   ├─ APIResponse wrapper
   ├─ Middleware: Metrics, logging
   └─ Return to client
```

### Response Format

All API endpoints return standardized format:

```json
{
  "success": true,
  "status": "success",
  "data": {
    "project_id": "proj_abc123",
    "name": "My Project",
    "created_at": "2026-03-26T10:30:00Z"
  },
  "message": "Project created successfully",
  "error_code": null,
  "timestamp": "2026-03-26T10:30:01Z"
}
```

## Caching Strategy

### Multi-Level Caching

1. **Application Cache** - In-memory caching for frequently accessed data
2. **Redis Cache** - Distributed cache across servers
3. **Database Cache** - Query result caching
4. **HTTP Cache** - Browser caching with appropriate headers

### Cache Invalidation

- Time-based: Expire after TTL
- Event-based: Invalidate on data change
- Manual: Admin can clear cache
- Pattern-based: Wildcard invalidation

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "status": "error",
  "data": null,
  "message": "Project not found",
  "error_code": "PROJECT_NOT_FOUND",
  "timestamp": "2026-03-26T10:30:01Z"
}
```

### Error Codes

- `AUTHENTICATION_FAILED` - JWT invalid/expired
- `AUTHORIZATION_FAILED` - User lacks permission
- `VALIDATION_ERROR` - Input validation failed
- `PROJECT_NOT_FOUND` - Project doesn't exist
- `USER_NOT_FOUND` - User doesn't exist
- `INTERNAL_SERVER_ERROR` - Unexpected error
- [And more...]

### Error Handling Pattern

```python
try:
    # Business logic
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User-friendly message"
    )
```

## Monitoring & Observability

### Logging

- **Application logs**: `INFO`, `WARNING`, `ERROR`, `DEBUG`
- **Access logs**: All HTTP requests
- **Audit logs**: User actions and permission changes
- **Error logs**: Exceptions and stack traces

### Metrics

- Request count and latency
- Error rate and types
- Database query time
- Cache hit/miss ratio
- Agent execution time

### Health Checks

- `GET /health` - Application status
- `GET /status` - Detailed system status
- `GET /metrics` - Prometheus metrics

## Security Considerations

### Input Validation

- All user input validated against SQL injection
- XSS protection for text fields
- Type validation via Pydantic
- Request size limits

### Authentication

- JWT tokens (HS256)
- Secure password hashing (bcrypt)
- Token expiration
- Refresh token rotation

### Authorization

- Project ownership verification
- Role-based access control
- Implicit deny principle

### Network Security

- HTTPS/TLS in production
- CORS restrictions
- Rate limiting
- API key authentication

## Deployment Architecture

### Development

```
┌─────────────────┐
│  Local Machine  │
├─────────────────┤
│ Python 3.12+    │
│ SQLite          │
│ (Redis optional)│
│ Claude API      │
└─────────────────┘
```

### Production

```
┌──────────────────────────────────────────────────┐
│           Load Balancer (nginx)                  │
└──────────────────────────────────────────────────┘
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
   ┌────────┬────────┬────────┐
   │ API #1 │ API #2 │ API #3 │  (FastAPI with Gunicorn)
   └────────┴────────┴────────┘
        │        │        │
        └────────┼────────┘
                 ▼
        ┌────────────────┐
        │  PostgreSQL    │  (Database)
        └────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
    ┌────────┐      ┌────────┐
    │ Redis  │      │ ChromaDB│  (Caching & Vectors)
    └────────┘      └────────┘
                         │
                         ▼
                  ┌────────────┐
                  │ Claude API │
                  └────────────┘
```

## Future Enhancements

### Short-term (Q1 2026)
- [ ] WebSocket authentication
- [ ] Real-time collaboration
- [ ] Document versioning
- [ ] User activity analytics

### Medium-term (Q2 2026)
- [ ] ULID-based ID generation
- [ ] GraphQL API
- [ ] Mobile application
- [ ] Plugin system

### Long-term (Q3+ 2026)
- [ ] On-premise deployment guide
- [ ] Enterprise authentication (LDAP/SAML)
- [ ] Multi-tenant support
- [ ] Custom agent creation

## Testing Strategy

### Unit Tests
- Individual functions and classes
- Mock external dependencies
- Test error cases

### Integration Tests
- API endpoint testing
- Database operations
- Agent interactions

### End-to-End Tests
- Full request-response cycle
- Multiple components working together
- Real database operations

### Performance Tests
- Load testing
- Latency measurements
- Memory usage

## Conclusion

Socrates provides a comprehensive architecture for AI-guided collaborative project development. The system is:

- **Modular** - Components can be developed and tested independently
- **Scalable** - Can handle multiple users and projects
- **Maintainable** - Clear separation of concerns
- **Extensible** - Easy to add new agents or features
- **Secure** - Multiple layers of security
- **Observable** - Comprehensive logging and metrics

---

**Last Updated**: 2026-03-26
**Version**: 1.0.0
**Status**: Stable
