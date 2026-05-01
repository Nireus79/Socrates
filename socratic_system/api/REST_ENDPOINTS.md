# Socrates REST API Endpoints

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

All endpoints support optional Bearer token authentication:

```
Authorization: Bearer your-api-key
```

---

## Agent Processing Endpoints

### POST /agents/{agent_name}/process

Process a request through a specific agent.

**Parameters:**
- `agent_name` (path): Agent name (e.g., "project_manager", "socratic_counselor")
- Request body: JSON object with agent-specific parameters

**Response:**
```json
{
    "status": "success",
    "data": { /* agent-specific response */ },
    "request_id": "uuid",
    "timestamp": "2026-05-01T12:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/agents/project_manager/process \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create",
    "name": "My Project",
    "description": "...",
    "user_id": "user_123"
  }'
```

---

## Agent Discovery Endpoints

### GET /agents/available

Get list of available agents and their capabilities.

**Response:**
```json
{
    "status": "success",
    "data": {
        "agents": [
            {
                "name": "project_manager",
                "capabilities": ["create", "load", "save", "list", "archive"],
                "status": "active",
                "version": "0.5.0"
            },
            {
                "name": "socratic_counselor",
                "capabilities": ["get_question", "process_response", "advance_phase"],
                "status": "active",
                "version": "0.5.0"
            }
            // ... more agents
        ]
    }
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/agents/available
```

### GET /agents/{agent_name}/schema

Get request/response schema for a specific agent.

**Response:**
```json
{
    "status": "success",
    "data": {
        "agent": "project_manager",
        "actions": {
            "create": {
                "description": "Create a new project",
                "parameters": {
                    "action": {
                        "type": "string",
                        "enum": ["create"],
                        "required": true
                    },
                    "name": {
                        "type": "string",
                        "description": "Project name",
                        "required": true
                    },
                    "description": {
                        "type": "string",
                        "description": "Project description",
                        "required": false
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User identifier",
                        "required": true
                    }
                }
            }
            // ... more actions
        }
    }
}
```

---

## Project Management Endpoints

### POST /agents/project_manager/process

All project operations go through the agent endpoint above.

**Available Actions:**

#### create
Create a new project.
```json
{
    "action": "create",
    "name": "Project Name",
    "description": "Optional description",
    "user_id": "user_123"
}
```

#### load
Load existing project.
```json
{
    "action": "load",
    "project_id": "proj_abc123",
    "user_id": "user_123"
}
```

#### save
Save project changes.
```json
{
    "action": "save",
    "project": { /* project object */ },
    "user_id": "user_123"
}
```

#### list
List all projects for a user.
```json
{
    "action": "list",
    "user_id": "user_123"
}
```

---

## Socratic Questioning Endpoints

### POST /agents/socratic_counselor/process

**Available Actions:**

#### get_question
Get a Socratic question.
```json
{
    "action": "get_question",
    "project_id": "proj_abc123",
    "phase": "discovery",
    "user_id": "user_123"
}
```

#### process_response
Process user's response to a question.
```json
{
    "action": "process_response",
    "project_id": "proj_abc123",
    "response": "User's answer text",
    "user_id": "user_123"
}
```

#### get_analysis
Get analysis results (polling).
```json
{
    "action": "get_analysis",
    "project_id": "proj_abc123",
    "user_id": "user_123"
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "ready": true,
        "maturity": 45.5,
        "conflicts": [],
        "insights": []
    }
}
```

#### advance_phase
Move to next phase.
```json
{
    "action": "advance_phase",
    "project_id": "proj_abc123",
    "user_id": "user_123"
}
```

---

## Code Generation Endpoints

### POST /agents/code_generator/process

**Available Actions:**

#### generate
Generate code/artifacts.
```json
{
    "action": "generate",
    "project_id": "proj_abc123",
    "language": "python",
    "user_id": "user_123"
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "files": [
            {
                "path": "src/main.py",
                "content": "...",
                "language": "python"
            }
        ]
    }
}
```

#### generate_documentation
Generate documentation.
```json
{
    "action": "generate_documentation",
    "project_id": "proj_abc123",
    "user_id": "user_123"
}
```

---

## Code Validation Endpoints

### POST /agents/code_validation/process

**Available Actions:**

#### validate
Validate code syntax/structure.
```json
{
    "action": "validate",
    "project_id": "proj_abc123",
    "code": "def hello(): pass",
    "language": "python",
    "user_id": "user_123"
}
```

#### run_tests
Run project tests.
```json
{
    "action": "run_tests",
    "project_id": "proj_abc123",
    "user_id": "user_123"
}
```

---

## Quality Control Endpoints

### POST /agents/quality_controller/process

**Available Actions:**

#### get_phase_maturity
Get quality/maturity metrics.
```json
{
    "action": "get_phase_maturity",
    "project_id": "proj_abc123",
    "user_id": "user_123"
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "overall_maturity": 62.5,
        "phase_maturity_scores": {
            "discovery": 85,
            "analysis": 60,
            "design": 45,
            "implementation": 30
        }
    }
}
```

#### calculate_maturity
Calculate/recalculate maturity.
```json
{
    "action": "calculate_maturity",
    "project_id": "proj_abc123",
    "user_id": "user_123"
}
```

---

## Conflict Detection Endpoints

### POST /agents/conflict_detector/process

**Available Actions:**

#### detect_conflicts
Detect conflicts in project.
```json
{
    "action": "detect_conflicts",
    "project_id": "proj_abc123",
    "user_id": "user_123"
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "conflicts": [
            {
                "type": "technical_stack",
                "description": "Conflict description",
                "severity": "high"
            }
        ]
    }
}
```

#### resolve_conflict
Resolve a specific conflict.
```json
{
    "action": "resolve_conflict",
    "project_id": "proj_abc123",
    "conflict_id": "conflict_xyz",
    "resolution": "Chosen resolution approach",
    "user_id": "user_123"
}
```

---

## Background Analysis Endpoints (Phase 3)

### GET /api/v1/background/status

Get status of background analysis jobs.

**Query Parameters:**
- `project_id` (optional): Filter by project

**Response:**
```json
{
    "status": "success",
    "data": {
        "pending": 1,
        "processing": 2,
        "completed": 3
    }
}
```

### GET /api/v1/background/quality

Get cached quality analysis results.

**Query Parameters:**
- `project_id` (required): Project to query

**Response:**
```json
{
    "status": "success",
    "data": {
        "status": "completed",
        "result": { /* quality metrics */ }
    }
}
```

### GET /api/v1/background/conflicts

Get cached conflict detection results.

**Query Parameters:**
- `project_id` (required): Project to query

### GET /api/v1/background/insights

Get cached insights analysis results.

**Query Parameters:**
- `project_id` (required): Project to query

---

## WebSocket Endpoints (Real-Time Updates)

### WS /ws/analysis/{project_id}

Subscribe to real-time analysis updates for a project.

**Connection Flow:**
1. Connect to WebSocket
2. Receive `{"type": "subscribed", "project_id": "..."}`
3. Receive updates as analyses complete:
   - `{"type": "quality.completed", "data": {...}}`
   - `{"type": "conflicts.completed", "data": {...}}`
   - `{"type": "insights.completed", "data": {...}}`

**Client Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analysis/proj_abc123');

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'quality.completed') {
        console.log('Quality analysis ready:', message.data);
    }
};

// Ping to keep connection alive
setInterval(() => ws.send('ping'), 30000);
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
    "status": "error",
    "message": "Human-readable error message",
    "error_code": "AGENT_TIMEOUT",
    "request_id": "uuid",
    "timestamp": "2026-05-01T12:00:00Z"
}
```

### Common Error Codes

- `INVALID_REQUEST`: Missing required parameters
- `INVALID_AGENT`: Unknown agent name
- `AGENT_TIMEOUT`: Agent request timed out
- `AGENT_ERROR`: Agent encountered an error
- `AUTHENTICATION_FAILED`: Invalid or missing auth token
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Server error

---

## Rate Limiting

- Default: 100 requests per minute per IP
- Headers included in response:
  - `X-RateLimit-Limit`: Rate limit threshold
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Unix timestamp of reset time

---

## Health Check

### GET /health

Check API health status.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2026-05-01T12:00:00Z",
    "agents_available": 17,
    "uptime_seconds": 3600
}
```

---

## Request/Response Examples

### Example 1: Create Project and Get Question

```bash
# Create project
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/agents/project_manager/process \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create",
    "name": "MyApp",
    "user_id": "user_123"
  }')

PROJECT_ID=$(echo $RESPONSE | jq -r '.data.project_id')

# Get question
curl -s -X POST http://localhost:8000/api/v1/agents/socratic_counselor/process \
  -H "Content-Type: application/json" \
  -d "{
    \"action\": \"get_question\",
    \"project_id\": \"$PROJECT_ID\",
    \"phase\": \"discovery\",
    \"user_id\": \"user_123\"
  }"
```

### Example 2: Process Response and Poll Results

```bash
# Process response
curl -s -X POST http://localhost:8000/api/v1/agents/socratic_counselor/process \
  -H "Content-Type: application/json" \
  -d "{
    \"action\": \"process_response\",
    \"project_id\": \"$PROJECT_ID\",
    \"response\": \"Our target is small businesses\",
    \"user_id\": \"user_123\"
  }"

# Poll for results
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/api/v1/agents/socratic_counselor/process \
    -H "Content-Type: application/json" \
    -d "{
      \"action\": \"get_analysis\",
      \"project_id\": \"$PROJECT_ID\",
      \"user_id\": \"user_123\"
    }"
  sleep 1
done
```

---

## Documentation

- [Client Library API](./CLIENT_API.md)
- [Architecture Overview](../ARCHITECTURE_ANALYSIS_LIBRARY_EXPORT.md)
- [AgentBus Internals](./AGENT_BUS.md)
