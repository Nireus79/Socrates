# API & Data Models Documentation

Complete REST API specification and Pydantic data models for Socrates AI v2.0

## Documents in This Directory

### 1. [API_ROUTE_DESIGN.md](API_ROUTE_DESIGN.md)
**Complete REST API specification (40+ endpoints)**
- Agent execution endpoints
- Learning and skill generation endpoints
- Knowledge management endpoints
- Workflow orchestration endpoints
- Analytics endpoints
- System health endpoints
- Full request/response examples
- Error handling standards
- Rate limiting
- Pagination

**Use this if**: You're implementing API endpoints or calling the API

---

### 2. [DATA_MODELS_SPECIFICATION.md](DATA_MODELS_SPECIFICATION.md)
**Pydantic v2 data model specification (50+ models)**
- Shared models (Interaction, Skill, Metric, Recommendation)
- Base model classes with validation
- Enums for status and types
- Agent service models
- Learning service models
- Knowledge service models
- Workflow service models
- Analytics service models
- Foundation service models
- Validation rules and constraints
- Usage examples

**Use this if**: You need to understand data structures or implement models

---

### 3. [EXAMPLES.md](EXAMPLES.md)
**Practical usage examples and tutorials**
- Common API call patterns
- Workflow examples
- Skill generation walkthrough
- Error handling examples
- Data validation examples

**Use this if**: You want practical examples of using the API

---

## API Endpoint Categories

### Agents Service (6 endpoints)
```
POST   /api/v1/agents/{agent_name}/execute
GET    /api/v1/agents/{agent_name}/info
GET    /api/v1/agents/{agent_name}/skills
POST   /api/v1/agents/{agent_name}/apply-skill
GET    /api/v1/agents/list
GET    /api/v1/agents/history
```

### Learning Service (6 endpoints)
```
POST   /api/v1/learning/{agent_name}/track-interaction
POST   /api/v1/learning/{agent_name}/generate-skills
GET    /api/v1/learning/{agent_name}/recommendations
GET    /api/v1/learning/{agent_name}/metrics
POST   /api/v1/learning/{agent_name}/analyze-patterns
GET    /api/v1/learning/insights
```

### Knowledge Service (6 endpoints)
```
POST   /api/v1/knowledge/search
POST   /api/v1/knowledge/items
GET    /api/v1/knowledge/items/{item_id}
PUT    /api/v1/knowledge/items/{item_id}
DELETE /api/v1/knowledge/items/{item_id}
GET    /api/v1/knowledge/stats
```

### Workflow Service (6 endpoints)
```
POST   /api/v1/workflow/create
POST   /api/v1/workflow/{workflow_id}/execute
GET    /api/v1/workflow/{workflow_id}
GET    /api/v1/workflow/{workflow_id}/status
POST   /api/v1/workflow/{workflow_id}/optimize
GET    /api/v1/workflow/list
```

### Analytics Service (4 endpoints)
```
GET    /api/v1/analytics/system/metrics
GET    /api/v1/analytics/system/insights
GET    /api/v1/analytics/agents
GET    /api/v1/analytics/dashboard
```

### System Service (3 endpoints)
```
GET    /api/v1/system/health
GET    /api/v1/system/info
GET    /api/v1/system/status
```

## Data Model Categories

### Shared Models
```
Interaction    - Record of agent action
Skill          - Learned capability
Metric         - Performance measurement
Recommendation - Suggestion for improvement
```

### Enums
```
InteractionStatus  - started, in_progress, completed, failed, cancelled
SkillType          - analysis, design, implementation, testing, etc.
WorkflowStatus     - draft, ready, running, paused, completed, failed
```

### Service-Specific Models
```
Agent Service:
  - ExecutionRequest
  - ExecutionResult
  - AgentInfo
  - SkillInfo

Learning Service:
  - TrackingRequest
  - SkillGenerationRequest
  - GeneratedSkill
  - AgentMetrics

Knowledge Service:
  - SearchRequest
  - SearchResult
  - KnowledgeItem
  - KnowledgeStats

Workflow Service:
  - WorkflowTask
  - WorkflowExecution
  - TaskResult
  - Optimization

Analytics Service:
  - SystemMetrics
  - AgentMetricsEntry
  - Insight
  - DashboardData

Foundation Service:
  - LLMConfig
  - DatabaseConfig
  - SystemHealth
```

## Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {...},
  "timestamp": "2026-03-16T12:34:56Z"
}
```

### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "AGENT_NOT_FOUND",
    "message": "Agent does not exist",
    "details": {...}
  },
  "timestamp": "2026-03-16T12:34:56Z"
}
```

## Standards

### Rate Limiting
- 1000 requests per minute per IP
- Rate limit headers included in all responses
- 429 Too Many Requests when exceeded

### Pagination
- Default: 20 items per page
- Max: 100 items per page
- Includes `total`, `page`, `per_page` in response

### Authentication
- Bearer token in Authorization header
- JWT tokens for API access
- Scope-based permissions

### Validation
- All inputs validated against Pydantic models
- 400 Bad Request for validation errors
- Clear error messages in response

## Common Patterns

### Error Codes
```
200  OK - Request successful
201  Created - Resource created
400  Bad Request - Input validation failed
401  Unauthorized - Authentication required
403  Forbidden - Access denied
404  Not Found - Resource not found
429  Too Many Requests - Rate limit exceeded
500  Internal Server Error - Server error
```

## Version Compatibility

- Current API Version: v1
- All endpoints prefixed with `/api/v1/`
- Backward compatibility maintained across minor versions
- Breaking changes in major versions with migration guide

---

**API Version**: 1.0
**Status**: Specification Complete, Implementation in Progress
**Last Updated**: March 16, 2026
