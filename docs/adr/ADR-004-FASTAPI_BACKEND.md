# ADR-004: FastAPI Backend

**Date**: January 2026
**Status**: Accepted
**Deciders**: Architecture Team

## Context

Socrates AI needed a web API to support both web UI and programmatic integrations.

**Requirements**:
- Fast, modern REST API
- Built-in async support
- Automatic API documentation
- Type safety
- Easy deployment
- Lightweight for single-machine use

## Decision

We chose **FastAPI** as the backend framework because it:
- Modern async framework (built on Starlette)
- Automatic OpenAPI/Swagger documentation
- Type hints for validation
- Fast performance (comparable to Go/Node)
- Minimal dependencies
- Built-in CORS, authentication, etc.
- Easy to deploy (single executable with uvicorn)

## Architecture

```
Client (Web/CLI)
    ↓ HTTPS
FastAPI Server
    ├─ Authentication Middleware
    ├─ CORS Middleware
    ├─ Error Handler Middleware
    └─ Route Handlers
        ↓
AgentOrchestrator
    ├─ ProjectManager
    ├─ CodeGenerator
    └─ ... (other agents)
        ↓
Database / VectorDB
```

## API Endpoints

**Examples**:
```
POST   /projects           - Create project
GET    /projects          - List projects
GET    /projects/{id}     - Get project detail
DELETE /projects/{id}     - Delete project

POST   /projects/{id}/dialogue    - Ask question
GET    /projects/{id}/answers     - Get answers

POST   /projects/{id}/code        - Generate code
GET    /projects/{id}/code        - Get generated code

GET    /health            - System health
POST   /auth/login        - User login
POST   /auth/register     - Register user
```

## Advantages

✓ **Performance**: Fastest Python async framework
✓ **Developer Experience**: Great docs, easy to use
✓ **Automatic Documentation**: Interactive API docs at /docs
✓ **Type Safety**: Pydantic models for validation
✓ **Easy Deployment**: Single binary, minimal infrastructure
✓ **Async Native**: Full async/await support
✓ **Standards**: Follows REST and OpenAPI standards

## Disadvantages

✗ **Python Async**: Complexity of async error handling
✗ **Community Size**: Smaller than Flask/Django
✗ **Maturity**: Newer framework (some edge cases)
✗ **Learning Curve**: Async patterns require understanding

## Alternatives Considered

### 1. Flask
- Lightweight Python framework
- **Rejected**: No async support, slower performance

### 2. Django
- Full-featured framework
- **Rejected**: Too heavy, overkill for API-only use

### 3. Node.js/Express
- Popular, fast
- **Rejected**: Requires different ecosystem, language fragmentation

### 4. Go
- High performance
- **Rejected**: Language/ecosystem mismatch with Python core

## Consequences

- API is responsive and scalable
- Web UI has solid backend support
- External integrations easy to build
- Documentation automatically generated
- Async operations require careful design

## Implementation Details

**Basic Endpoint**:
```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/projects")
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    result = orchestrator.process_request('project_manager', {
        'action': 'create_project',
        'project_name': project_data.name,
        'owner': current_user.id
    })
    return result['project']
```

**Type Safety**:
```python
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    template: str = "blank"
```

**Error Handling**:
```python
from fastapi import HTTPException

@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    try:
        result = orchestrator.process_request('project_manager', {
            'action': 'get_project',
            'project_id': project_id
        })
        return result['project']
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
```

## API Design Principles

1. **RESTful URLs**: `/projects`, `/projects/{id}`, `/projects/{id}/code`
2. **Proper HTTP Verbs**: GET, POST, PUT, DELETE
3. **Status Codes**: 200, 201, 400, 404, 500
4. **Error Responses**: `{"detail": "error message"}`
5. **Async Operations**: Return Job ID for long operations
6. **Pagination**: Limit/offset for list endpoints
7. **Authentication**: Bearer token in Authorization header

## Deployment

**Local Development**:
```bash
uvicorn socrates_api.main:app --reload
```

**Production**:
```bash
uvicorn socrates_api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Docker**:
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "socrates_api.main:app", "--host", "0.0.0.0"]
```

## Monitoring & Observability

**Built-in Documentation**: http://localhost:8000/docs
**OpenAPI Schema**: http://localhost:8000/openapi.json
**Health Check**: http://localhost:8000/health

**Custom Logging**:
```python
import logging
logger = logging.getLogger(__name__)

@app.post("/projects")
async def create_project(...):
    logger.info(f"Creating project: {project_data.name}")
    ...
```

## Performance Characteristics

**Typical Response Times**:
- Get project: <10ms
- List projects: <50ms
- Generate question: 1-3 seconds
- Generate code: 10-30 seconds

**Throughput**:
- Requests per second: 100+ (varies by operation)
- Concurrent users: 50+ on single machine

## Security

**Authentication**: JWT tokens
**CORS**: Configured for frontend
**Rate Limiting**: Per-user rate limits
**Input Validation**: Pydantic models
**Error Messages**: Safe, non-leaking

## Future Considerations

**v1.4+**: GraphQL layer on top of REST
**v1.5+**: WebSocket support for real-time updates
**v2.0+**: Microservices with service mesh

## Related ADRs
- ADR-001: Multi-Agent Architecture
- ADR-003: Event-Driven Communication

---

**Decision**: ACCEPTED
**Implementation**: ✓ Complete
**Review Date**: Q2 2026
