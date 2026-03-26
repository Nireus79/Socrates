# Socrates API Backend

**Production-ready REST API for Socrates AI tutoring platform**

## Overview

The Socrates API is a FastAPI-based backend that provides REST endpoints for project management, Socratic questioning, knowledge management, and multi-agent orchestration. It serves as the core interface for the Socrates system, supporting both the CLI and web front-end.

## Architecture

### Directory Structure

```
backend/
├── src/
│   ├── socrates_api/
│   │   ├── __init__.py              # Package initialization
│   │   ├── main.py                  # FastAPI application setup
│   │   ├── orchestrator.py          # Agent orchestration
│   │   ├── database.py              # Local SQLite wrapper
│   │   ├── models.py                # Pydantic request/response models
│   │   ├── models_local.py          # Local data models
│   │   ├── testing_mode.py          # Testing utilities
│   │   ├── monitoring.py            # System monitoring
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py          # Module exports
│   │   │   └── id_generator.py      # Centralized ID generation utility
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── dependencies.py      # FastAPI dependency injection
│   │   │   ├── jwt_handler.py       # JWT token creation/validation
│   │   │   ├── password.py          # Password hashing utilities
│   │   │   └── project_access.py    # Project-based access control
│   │   │
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── rate_limit.py        # Rate limiting middleware
│   │   │   ├── security_headers.py  # HTTP security headers
│   │   │   ├── metrics.py           # Performance metrics collection
│   │   │   ├── audit.py             # Audit logging
│   │   │   ├── activity_tracker.py  # User activity tracking
│   │   │   ├── csrf.py              # CSRF protection
│   │   │   ├── performance.py       # Performance monitoring
│   │   │   └── subscription.py      # Subscription-based gating
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py          # Router imports and registration
│   │   │   ├── auth.py              # Authentication endpoints
│   │   │   ├── projects.py          # Project CRUD endpoints
│   │   │   ├── chat_sessions.py     # Chat session management
│   │   │   ├── free_session.py      # Free-form chat sessions
│   │   │   ├── knowledge.py         # Knowledge base endpoints
│   │   │   ├── collaboration.py     # Team collaboration endpoints
│   │   │   ├── code_generation.py   # Code generation endpoints
│   │   │   ├── learning.py          # Learning tracking endpoints
│   │   │   ├── skills.py            # Skill management endpoints
│   │   │   └── [14+ more routers]   # Domain-specific endpoints
│   │   │
│   │   ├── websocket/
│   │   │   ├── __init__.py
│   │   │   ├── connection_manager.py # WebSocket connection management
│   │   │   ├── message_handler.py    # WebSocket message routing
│   │   │   └── event_bridge.py       # Event system integration
│   │   │
│   │   ├── caching/
│   │   │   ├── __init__.py
│   │   │   └── redis_cache.py       # Redis caching with fallback
│   │   │
│   │   └── services/
│   │       └── report_generator.py  # Report generation utilities
│   │
│   └── tests/
│       └── test_id_generator.py     # ID generator tests
│
├── requirements.txt                  # Python dependencies
└── Dockerfile                        # Docker container definition
```

## Key Components

### ID Generator (`utils/id_generator.py`)

Centralized utility for generating prefixed, unique IDs across all entity types. Replaces the pattern from the monolithic system that was removed during the monorepo migration.

**Supported Entity Types** (11 total):
- `project()` → `proj_XXXXXXXXXXXX`
- `user()` → `user_XXXXXXXXXXXX`
- `session()` → `sess_XXXXXXXX` (8-char variant)
- `message()` → `msg_XXXXXXXXXXXX`
- `skill()` → `skill_XXXXXXXXXXXX`
- `note()` → `note_XXXXXXXXXXXX`
- `interaction()` → `int_XXXXXXXXXXXX`
- `document()` → `doc_XXXXXXXXXXXX`
- `token()` → `tok_XXXXXXXXXXXX`
- `activity()` → `act_XXXXXXXXXXXX`
- `invitation()` → `inv_XXXXXXXXXXXX`

**Design Benefits:**
- Single source of truth for ID generation across system
- Easy to change ID format globally
- Type-safe with proper documentation
- Fully tested (50+ test cases)
- Backward compatible with monolithic system pattern

### Authentication (`auth/`)

Provides JWT-based authentication with refresh tokens and password hashing.

**Key Features:**
- JWT token creation and validation
- Secure password hashing with salt
- FastAPI dependency injection for route protection
- Project-level access control (owner/editor/viewer roles)
- Optional multi-factor authentication (TOTP)

### Database (`database.py`)

Local SQLite wrapper for API-specific data (projects, users, sessions).

**Tables:**
- `users` - User accounts with credentials
- `projects` - Project metadata and ownership
- `refresh_tokens` - Token refresh tracking

**Important:** Database uses centralized `IDGenerator` for all ID creation, ensuring consistency across the system.

### Routers (`routers/`)

API endpoints organized by functional domain. Each router handles specific entity types:

- **Auth Router** - User registration, login, token refresh
- **Projects Router** - Project CRUD, listing, analytics
- **Chat Sessions** - Chat history and message management
- **Knowledge** - Document storage and retrieval
- **Collaboration** - Team management and invitations
- **Code Generation** - AI-powered code generation
- **Learning** - User skill and progress tracking

**Router Pattern:**
All routers follow consistent patterns:
1. Use `IDGenerator` for creating new entities
2. Implement authentication via FastAPI dependencies
3. Return standardized `APIResponse` wrapper
4. Log operations for audit trail
5. Validate inputs for security

### Middleware (`middleware/`)

Cross-cutting concerns applied to all requests:

- **Rate Limiting** - Prevent abuse with configurable limits
- **Security Headers** - HTTPS enforcement, XSS protection
- **Metrics** - Request/response metrics collection
- **Audit Logging** - Track all API activity
- **Activity Tracking** - User interaction history
- **CSRF Protection** - Cross-site request forgery prevention
- **Performance Monitoring** - Response time tracking

### WebSocket (`websocket/`)

Real-time communication for chat and collaborative features.

- **Connection Manager** - Manages active connections
- **Message Handler** - Routes WebSocket messages
- **Event Bridge** - Integrates with event system

## Getting Started

### Installation

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Running the Server

```bash
# Development with auto-reload
python -m socrates_api

# Production with gunicorn
gunicorn socrates_api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Configuration

Environment variables in `.env`:

```bash
# FastAPI
ENVIRONMENT=development
DEBUG=true

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=7

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Redis (optional)
REDIS_URL=redis://redis:6379
REDIS_FALLBACK_TO_MEMORY=true

# Database
DATABASE_URL=sqlite:///~/.socrates/api_projects.db

# Claude API
ANTHROPIC_API_KEY=your-api-key-here

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

All endpoints return standardized `APIResponse` format:

```json
{
  "success": true,
  "status": "success",
  "data": { "project_id": "proj_abc123" },
  "message": "Operation successful",
  "error_code": null,
  "timestamp": "2026-01-08T12:30:45Z"
}
```

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user

### Projects
- `GET /projects` - List user's projects
- `POST /projects` - Create new project
- `GET /projects/{project_id}` - Get project details
- `PUT /projects/{project_id}` - Update project
- `DELETE /projects/{project_id}` - Delete project
- `POST /projects/{project_id}/archive` - Archive project

### Chat
- `POST /chat-sessions` - Create chat session
- `GET /chat-sessions/{session_id}` - Get session
- `POST /chat-sessions/{session_id}/messages` - Send message
- `GET /chat-sessions/{session_id}/messages` - Get messages
- `DELETE /chat-sessions/{session_id}` - Delete session

### Knowledge Base
- `POST /knowledge/documents` - Upload document
- `GET /knowledge/documents` - List documents
- `GET /knowledge/search` - Search documents
- `DELETE /knowledge/documents/{doc_id}` - Delete document

### [See API documentation for complete endpoint list]

## Key Design Patterns

### 1. Dependency Injection

Uses FastAPI dependencies for clean separation of concerns:

```python
async def list_projects(
    current_user: str = Depends(get_current_user),
    db: LocalDatabase = Depends(get_database),
):
    # Implementation
```

### 2. Error Handling

Consistent error responses with machine-readable codes:

```python
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid project ID",
)
```

### 3. Authorization Model

Owner-based authorization (no global admins):
- Each project has an owner (creator)
- Only owner can manage project
- Collaborators can be invited with specific roles (owner/editor/viewer)
- Decentralized permission management

### 4. ID Generation

Centralized `IDGenerator` utility ensures:
- Consistent format across all entity types
- High entropy (UUID4-based, 48+ bits)
- Easy to change format globally
- Backward compatible with monolithic system

## Testing

```bash
# Run all tests
pytest backend/src/tests/

# Run with coverage
pytest --cov=socrates_api backend/src/tests/

# Run specific test file
pytest backend/src/tests/test_id_generator.py

# Run tests in verbose mode
pytest -v backend/src/tests/
```

## Monitoring and Metrics

The API exposes several monitoring endpoints:

- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /status` - System status
- `GET /config` - Configuration info (development only)

## Database Schema

### users table
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,                    -- user_XXXX
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    passcode_hash TEXT,
    subscription_tier TEXT DEFAULT 'free',
    subscription_status TEXT DEFAULT 'active',
    testing_mode INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT,
    metadata TEXT
);
```

### projects table
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,                    -- proj_XXXX
    owner TEXT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT,
    updated_at TEXT,
    phase TEXT DEFAULT 'discovery',
    is_archived INTEGER DEFAULT 0,
    metadata TEXT
);
```

## Performance Considerations

### Caching
- Redis for distributed caching (with in-memory fallback)
- Request/response caching for frequently accessed data
- Database query result caching

### Database
- Connection pooling for SQLite
- Indexed queries on frequently searched fields
- Lazy loading for large datasets

### API
- Async/await for concurrent request handling
- Request compression with gzip
- Pagination for large result sets

## Security

### Input Validation
- All user inputs validated against SQL injection and XSS
- Type validation via Pydantic models
- Request size limits

### Authentication
- JWT tokens with configurable expiration
- Secure password hashing with salt
- Token refresh mechanism

### CORS
- Configured for development (localhost)
- Restricted origins in production

### Rate Limiting
- Per-IP rate limits on sensitive endpoints
- Configurable limits per endpoint

## Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Check database exists and is readable
ls -la ~/.socrates/api_projects.db

# Reset database
rm ~/.socrates/api_projects.db
python -c "from socrates_api.database import get_database; db = get_database()"
```

**JWT token errors:**
```bash
# Verify JWT_SECRET_KEY is set
echo $JWT_SECRET_KEY

# Regenerate tokens
curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '...'
```

**Rate limiting issues:**
```bash
# Check Redis connection
redis-cli ping

# Or restart with in-memory fallback
export REDIS_FALLBACK_TO_MEMORY=true
```

## Deployment

### Docker

```bash
# Build image
docker build -f backend/Dockerfile -t socrates-api:latest .

# Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e JWT_SECRET_KEY=$JWT_SECRET_KEY \
  socrates-api:latest
```

### Production Considerations

1. Use production database (PostgreSQL recommended)
2. Enable HTTPS/TLS
3. Configure proper CORS origins
4. Set up monitoring and alerting
5. Implement API key authentication
6. Use separate Redis instance
7. Implement request logging
8. Set up error tracking (Sentry)

## Contributing

When adding new features:

1. **Use IDGenerator** for creating new entities - don't create inline ID generation
2. **Follow router patterns** - consistency across API
3. **Add proper authentication** - use FastAPI dependencies
4. **Return APIResponse** - standardize response format
5. **Log operations** - for audit trail
6. **Validate inputs** - use Pydantic models
7. **Write tests** - maintain test coverage
8. **Document endpoints** - add docstrings and OpenAPI descriptions

## License

See LICENSE file in root directory.

---

**Last Updated**: 2026-03-26
**Status**: Production Ready
**API Version**: 1.0.0
